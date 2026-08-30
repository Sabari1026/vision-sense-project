import time
import queue
import threading
import cv2
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

from vision.source import CameraSource, FileCameraSource
from vision.detector import YOLODetector
from vision.tracker import PersonTracker
from vision.zone_manager import ZoneManager
from vision.dwell_time import DwellTimeManager
from vision.heatmap import HeatmapGenerator
from vision.age_estimator import AgeEstimator
from vision.reid import PersonReID

class CameraStreamProcessor:
    """
    Decoupled High-Precision CCTV Stream Processor with Real-Time Motion Interpolation,
    Aspect-Ratio Invariant Temporal Smoothing, and ByteTrack State Management.
    """

    def __init__(self, camera_id: str, camera_name: str, source_path: str, config: Dict[str, Any],
                 loop: bool = True, shared_detector: Optional[YOLODetector] = None, shared_reid: Optional[PersonReID] = None):
        self.camera_id = camera_id
        self.camera_name = camera_name
        self.source_path = source_path
        self.config = config
        self.loop = loop
        self.reid = shared_reid

        self.source: CameraSource = FileCameraSource(source_path, name=camera_name, loop=loop)
        if shared_detector is not None:
            self.detector = shared_detector
        else:
            self.detector = YOLODetector(
                model_name=config.get('YOLO_MODEL', 'yolo11n.pt'),
                confidence_threshold=config.get('vision', {}).get('confidence', 0.25),
                use_gpu=config.get('USE_GPU', True),
                imgsz=config.get('vision', {}).get('imgsz', 512)
            )

        # Dedicated ByteTracker per camera stream with Kalman filtering and temporal smoothing
        smoothing_alpha = float(config.get('vision', {}).get('smoothing_alpha', config.get('BBOX_SMOOTHING_ALPHA', 0.65)))
        enable_kalman = bool(config.get('vision', {}).get('enable_kalman', config.get('ENABLE_KALMAN', True)))
        min_confirmation_frames = int(config.get('vision', {}).get('min_confirmation_frames', config.get('MIN_TRACK_CONFIRMATION_FRAMES', 2)))

        self.tracker = PersonTracker(
            tracker_type='bytetrack',
            smoothing_alpha=smoothing_alpha,
            enable_kalman=enable_kalman,
            min_confirmation_frames=min_confirmation_frames,
            camera_id=camera_id
        )

        self.zone_manager = ZoneManager(camera_id)
        self.dwell_manager = DwellTimeManager(
            camera_id,
            lost_timeout_seconds=config.get('vision', {}).get('lost_timeout_seconds', 5.0)
        )
        self.heatmap = HeatmapGenerator()

        try:
            from backend.app.services.supabase_client import db_service
            stored_points = db_service.get_heatmap_points(limit=2000, camera_id=camera_id)
            for p in stored_points:
                self.heatmap.add_point((p['x'], p['y']), weight=p.get('weight', 1.0))
        except Exception:
            pass

        self.age_estimator = AgeEstimator(enabled=config.get('age_estimation', {}).get('enabled', True))

        self.is_running = False
        self.target_fps = float(config.get('cameras', {}).get('default_fps', 25.0))
        self.current_fps = self.target_fps
        self.people_count = 0
        self.total_entries = 0
        self.total_exits = 0
        self.total_visitors_count = 0

        self.latest_frame: Optional[np.ndarray] = None
        self.latest_annotated_frame: Optional[np.ndarray] = None
        self.latest_jpeg_bytes: Optional[bytes] = None

        # Threading & Decoupled Inference Queue
        self.ai_queue: queue.Queue = queue.Queue(maxsize=1)
        self.tracked_objects: List[Dict[str, Any]] = []
        self.last_ai_update_time = time.time()
        self.tracks_lock = threading.Lock()
        self.stream_thread: Optional[threading.Thread] = None
        self.ai_thread: Optional[threading.Thread] = None

        # Buffers & Caches
        self.buffered_events: List[Dict[str, Any]] = []
        self.buffered_heatmap_points: List[Dict[str, Any]] = []
        self.track_age_cache: Dict[int, Tuple[str, float]] = {}
        self.track_global_id_cache: Dict[int, Optional[str]] = {}
        self.last_event_sample_time = time.time()
        self.fps_frame_count = 0
        self.fps_calc_time = time.time()

    def initialize(self) -> bool:
        return self.source.open()

    def start(self):
        if self.is_running:
            return

        if not self.source.is_opened:
            if not self.initialize():
                return

        self.is_running = True

        # Thread 1: Video Stream & Rendering Engine (25-30 FPS)
        self.stream_thread = threading.Thread(target=self._stream_loop, daemon=True)
        self.stream_thread.start()

        # Thread 2: YOLOv11 + ByteTrack AI Worker (Async)
        self.ai_thread = threading.Thread(target=self._ai_worker_loop, daemon=True)
        self.ai_thread.start()

    def stop(self):
        self.is_running = False
        if self.source:
            self.source.release()

    def _stream_loop(self):
        frame_interval = 1.0 / self.target_fps

        while self.is_running:
            t_start = time.time()

            ret, frame = self.source.read_frame()
            if not ret or frame is None:
                time.sleep(0.01)
                continue

            self.latest_frame = frame
            current_timestamp = time.time()

            # Submit frame to AI worker if queue is free
            if self.ai_queue.empty():
                try:
                    self.ai_queue.put_nowait((frame.copy(), current_timestamp))
                except queue.Full:
                    pass

            annotated_frame = frame.copy()
            h, w = frame.shape[:2]

            # Draw Zone polygons & counting lines
            annotated_frame = self.zone_manager.draw_zones(annotated_frame)

            # Draw active ByteTrack tracks with motion interpolation
            with self.tracks_lock:
                active_tracks = self.tracked_objects.copy()
                ai_time = self.last_ai_update_time

            self.people_count = len([t for t in active_tracks if t.get('state') != 'TEMPORARILY_LOST'])
            dt_ai = min(0.35, max(0.0, current_timestamp - ai_time))

            for obj in active_tracks:
                track_id = obj['track_id']
                raw_bbox = obj['bbox']
                conf = obj.get('confidence', 0.85)
                history = obj.get('history', [])
                zone_name = obj.get('zone_name', 'General Area')
                dwell = obj.get('dwell', 0)
                global_id = obj.get('global_id')
                state = obj.get('state', 'ACTIVE')
                vx = obj.get('vx', 0.0)
                vy = obj.get('vy', 0.0)

                # Smooth velocity interpolation
                shift_x = int(round(vx * dt_ai * 16.0))
                shift_y = int(round(vy * dt_ai * 16.0))

                x1 = max(0, min(w - 10, raw_bbox[0] + shift_x))
                y1 = max(0, min(h - 20, raw_bbox[1] + shift_y))
                x2 = max(x1 + 10, min(w, raw_bbox[2] + shift_x))
                y2 = max(y1 + 20, min(h, raw_bbox[3] + shift_y))

                # Draw motion trail
                if len(history) > 1:
                    for i in range(1, len(history)):
                        alpha_trail = float(i) / len(history)
                        color_val = int(255 * alpha_trail)
                        cv2.line(annotated_frame, history[i-1], history[i], (0, color_val, 255), 2, cv2.LINE_AA)

                # Select theme color based on track state
                if state == "TEMPORARILY_LOST":
                    box_color = (0, 165, 255)  # Orange for predicted occlusion recovery
                elif state == "RECOVERED":
                    box_color = (255, 200, 0)  # Cyan for recovered track
                else:
                    box_color = (0, 255, 120)  # Emerald green for active track

                # Draw Smooth Bounding Box
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), box_color, 2, cv2.LINE_AA)

                # Corner accent markers
                corner_len = min(16, min((x2 - x1) // 3, (y2 - y1) // 3))
                if corner_len > 4:
                    cv2.line(annotated_frame, (x1, y1), (x1 + corner_len, y1), (255, 255, 255), 3)
                    cv2.line(annotated_frame, (x1, y1), (x1, y1 + corner_len), (255, 255, 255), 3)
                    cv2.line(annotated_frame, (x2, y2), (x2 - corner_len, y2), (255, 255, 255), 3)
                    cv2.line(annotated_frame, (x2, y2), (x2, y2 - corner_len), (255, 255, 255), 3)

                # Construct HUD Label attached to bounding box header
                if global_id:
                    label = f"ID: {track_id} [Global: {global_id}] ({int(conf * 100)}%)"
                else:
                    label = f"ID: {track_id} ({int(conf * 100)}%)"

                if state == "TEMPORARILY_LOST":
                    sub_label = f"Dwell: {dwell}s | {zone_name} (Predicting...)"
                else:
                    sub_label = f"Dwell: {dwell}s | {zone_name}"

                box_width = max(len(label), len(sub_label)) * 8 + 12
                cv2.rectangle(annotated_frame, (x1, max(0, y1 - 38)), (x1 + box_width, y1), (15, 23, 42), -1)
                cv2.rectangle(annotated_frame, (x1, max(0, y1 - 38)), (x1 + box_width, y1), box_color, 1)
                cv2.putText(annotated_frame, label, (x1 + 6, max(12, y1 - 22)), cv2.FONT_HERSHEY_SIMPLEX, 0.42, box_color, 1, cv2.LINE_AA)
                cv2.putText(annotated_frame, sub_label, (x1 + 6, max(24, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (220, 225, 230), 1, cv2.LINE_AA)

            # Calculate Rolling Playback FPS
            self.fps_frame_count += 1
            fps_elapsed = current_timestamp - self.fps_calc_time
            if fps_elapsed >= 1.0:
                self.current_fps = round(self.fps_frame_count / fps_elapsed, 1)
                self.fps_frame_count = 0
                self.fps_calc_time = current_timestamp

            # Render Camera HUD Banner
            cv2.rectangle(annotated_frame, (10, 10), (380, 105), (15, 23, 42), -1)
            cv2.rectangle(annotated_frame, (10, 10), (380, 105), (0, 255, 200), 1)
            cv2.putText(annotated_frame, f"CAM: {self.camera_name}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 255, 200), 1, cv2.LINE_AA)
            cv2.putText(annotated_frame, f"Occupancy: {max(0, self.total_entries - self.total_exits)} | People Live: {self.people_count}", (20, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(annotated_frame, f"Entries: {self.total_entries} | Exits: {self.total_exits} | FPS: {self.current_fps}", (20, 74), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(annotated_frame, f"Avg Dwell: {self.dwell_manager.get_average_dwell_seconds()}s | Total: {self.total_visitors_count}", (20, 94), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 220, 255), 1, cv2.LINE_AA)

            self.latest_annotated_frame = annotated_frame

            # Pre-encode JPEG binary in worker thread for instant zero-copy streaming
            ret_jpg, jpeg_buf = cv2.imencode('.jpg', annotated_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if ret_jpg:
                self.latest_jpeg_bytes = jpeg_buf.tobytes()

            t_elapsed = time.time() - t_start
            sleep_sec = max(0.001, frame_interval - t_elapsed)
            time.sleep(sleep_sec)

    def _ai_worker_loop(self):
        while self.is_running:
            try:
                frame, timestamp = self.ai_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            try:
                # 1. YOLOv11 Person Detection
                detections = self.detector.detect(frame)

                # 2. ByteTrack Multi-Object Tracking with Kalman Filtering & Temporal Smoothing
                tracks = self.tracker.update(detections)

                # 3. Process Zones, Line-Crossing, Dwell Time, Age, Re-ID
                augmented_tracks = []
                for obj in tracks:
                    track_id = obj['track_id']
                    bbox = obj['bbox']
                    conf = obj['confidence']
                    center = obj['center']
                    footprint = obj.get('footprint', (center[0], bbox[3]))
                    x1, y1, x2, y2 = bbox

                    # Extract crop for Age & optional Re-ID
                    crop = frame[max(0, y1):min(frame.shape[0], y2), max(0, x1):min(frame.shape[1], x2)]

                    # Optional Re-ID matching
                    global_id = None
                    if self.reid is not None and self.reid.enabled:
                        global_id = self.reid.match_or_register(self.camera_id, track_id, crop, timestamp)
                        self.track_global_id_cache[track_id] = global_id

                    # Zone containment (based on ground footprint)
                    zone_info = self.zone_manager.check_zone_containment(footprint)
                    zone_id = zone_info['id'] if zone_info else None
                    zone_name = zone_info['name'] if zone_info else "General Area"

                    # Entry / Exit line crossing (based on ground footprint)
                    is_entry, is_exit = self.zone_manager.update_track_positions(track_id, footprint)
                    if is_entry:
                        self.total_entries += 1
                    if is_exit:
                        self.total_exits += 1

                    # Age estimation (cached)
                    if track_id not in self.track_age_cache:
                        age_group, age_conf = self.age_estimator.estimate_age(crop)
                        self.track_age_cache[track_id] = (age_group, age_conf)
                    else:
                        age_group, age_conf = self.track_age_cache[track_id]

                    # Dwell session update
                    session = self.dwell_manager.update_track(track_id, timestamp, zone_info, age_group, age_conf)

                    # Heatmap accumulation
                    self.heatmap.add_point(center, weight=1.0)
                    if timestamp - self.last_event_sample_time >= 1.0:
                        self.buffered_heatmap_points.append({
                            'camera_id': self.camera_id,
                            'timestamp': timestamp,
                            'x': center[0],
                            'y': center[1],
                            'weight': 1.0,
                            'zone_id': zone_id
                        })

                    obj['zone_name'] = zone_name
                    obj['dwell'] = session.get('dwell_seconds', 0)
                    obj['global_id'] = global_id
                    augmented_tracks.append(obj)

                # 4. Clean up lost sessions
                closed = self.dwell_manager.cleanup_lost_tracks(timestamp)
                self.total_visitors_count += len(closed)

                if timestamp - self.last_event_sample_time >= 1.0:
                    self.last_event_sample_time = timestamp

                with self.tracks_lock:
                    self.tracked_objects = augmented_tracks
                    self.last_ai_update_time = timestamp

            except Exception:
                pass

    def get_active_tracks_json(self) -> List[Dict[str, Any]]:
        with self.tracks_lock:
            return [
                {
                    'track_id': t['track_id'],
                    'global_person_id': t.get('global_id'),
                    'bbox': list(t['bbox']),
                    'center': list(t['center']),
                    'confidence': t.get('confidence', 0.85),
                    'zone': t.get('zone_name', 'General Area'),
                    'dwell_seconds': t.get('dwell', 0),
                    'state': t.get('state', 'ACTIVE')
                }
                for t in self.tracked_objects
            ]

    def get_stats(self) -> Dict[str, Any]:
        return {
            'camera_id': self.camera_id,
            'camera_name': self.camera_name,
            'fps': self.current_fps,
            'people_count': self.people_count,
            'entries': self.total_entries,
            'exits': self.total_exits,
            'occupancy': max(0, self.total_entries - self.total_exits),
            'avg_dwell_seconds': self.dwell_manager.get_average_dwell_seconds(),
            'total_visitors': self.total_visitors_count
        }

    def get_closed_sessions_to_flush(self) -> List[Dict[str, Any]]:
        raw_sessions = self.dwell_manager.pop_closed_sessions()
        sanitized = []
        for s in raw_sessions:
            t_id = s.get('anonymous_track_id')
            sanitized.append({
                'camera_id': s.get('camera_id'),
                'anonymous_track_id': t_id,
                'global_person_id': self.track_global_id_cache.get(t_id),
                'entry_time': s.get('entry_time'),
                'exit_time': s.get('exit_time'),
                'dwell_seconds': s.get('dwell_seconds', 0),
                'age_group': s.get('age_group', 'Unknown'),
                'age_confidence': s.get('age_confidence', 0.0),
                'entry_zone': s.get('entry_zone', 'General Area'),
                'exit_zone': s.get('exit_zone', 'General Area')
            })
        return sanitized

    def get_closed_zone_visits_to_flush(self) -> List[Dict[str, Any]]:
        return self.dwell_manager.pop_closed_zone_visits()
