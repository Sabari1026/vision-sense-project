import time
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

class CameraStreamProcessor:
    """Master Multi-Threaded Processor for single CCTV Camera Feed."""

    def __init__(self, camera_id: str, camera_name: str, source_path: str, config: Dict[str, Any], loop: bool = True):
        self.camera_id = camera_id
        self.camera_name = camera_name
        self.source_path = source_path
        self.config = config

        self.source: CameraSource = FileCameraSource(source_path, name=camera_name, loop=loop)
        self.detector = YOLODetector(
            model_name=config.get('YOLO_MODEL', 'yolov8n.pt'),
            confidence_threshold=config.get('vision', {}).get('confidence', 0.45),
            use_gpu=config.get('USE_GPU', True)
        )
        self.tracker = PersonTracker(tracker_type=config.get('vision', {}).get('tracker', 'bytetrack'))
        self.zone_manager = ZoneManager(camera_id)
        self.dwell_manager = DwellTimeManager(
            camera_id,
            lost_timeout_seconds=config.get('vision', {}).get('lost_timeout_seconds', 5.0)
        )
        self.heatmap = HeatmapGenerator()
        # Pre-populate stored database points into heatmap generator
        try:
            from backend.app.services.supabase_client import db_service
            stored_points = db_service.get_heatmap_points(limit=3000, camera_id=camera_id)
            for p in stored_points:
                self.heatmap.add_point((p['x'], p['y']), weight=p.get('weight', 1.0))
        except Exception as e:
            pass

        self.age_estimator = AgeEstimator(enabled=config.get('age_estimation', {}).get('enabled', True))

        self.is_running = False
        self.fps = 0.0
        self.current_people_count = 0
        self.total_entries = 0
        self.total_exits = 0
        self.total_visitors_count = 0

        self.latest_frame: Optional[np.ndarray] = None
        self.latest_annotated_frame: Optional[np.ndarray] = None

        # Data Buffers & Caches
        self.buffered_events: List[Dict[str, Any]] = []
        self.buffered_heatmap_points: List[Dict[str, Any]] = []
        self.track_age_cache: Dict[int, Tuple[str, float]] = {}
        self.frame_counter = 0
        self.cached_tracked_objects: List[Dict[str, Any]] = []
        self.last_flush_time = time.time()
        self.last_snapshot_time = time.time()
        self.last_event_sample_time = time.time()

    def initialize(self) -> bool:
        return self.source.open()

    def process_next_frame(self, enable_heatmap_overlay: bool = False) -> Tuple[bool, Optional[np.ndarray], Dict[str, Any]]:
        start_time = time.time()

        ret, frame = self.source.read_frame()
        if not ret or frame is None:
            return False, None, {}

        self.latest_frame = frame.copy()
        self.frame_counter += 1

        # 1 & 2. Detection & Multi-Object Tracking (Interleaved for 30 FPS smooth live stream)
        if getattr(self.source, 'loop', True) and self.frame_counter % 2 == 0 and len(self.cached_tracked_objects) > 0:
            tracked_objects = self.cached_tracked_objects
        else:
            detections = self.detector.detect(frame)
            tracked_objects = self.tracker.update(detections, model_instance=self.detector.model, frame=frame)
            self.cached_tracked_objects = tracked_objects

        current_timestamp = time.time()
        self.current_people_count = len(tracked_objects)

        annotated_frame = frame.copy()

        # 3. Draw Zones and Entry/Exit Line
        annotated_frame = self.zone_manager.draw_zones(annotated_frame)

        active_track_ids = set()

        for obj in tracked_objects:
            track_id = obj['track_id']
            active_track_ids.add(track_id)
            bbox = obj['bbox']
            conf = obj['confidence']
            center = obj['center']

            x1, y1, x2, y2 = bbox

            # Zone containment check
            zone_info = self.zone_manager.check_zone_containment(center)
            zone_id = zone_info['id'] if zone_info else None
            zone_name = zone_info['name'] if zone_info else "General Area"

            # Line crossing check
            is_entry, is_exit = self.zone_manager.update_track_positions(track_id, center)
            if is_entry:
                self.total_entries += 1
            if is_exit:
                self.total_exits += 1

            # Estimate Age (Cached per track_id for high performance)
            if track_id not in self.track_age_cache:
                person_crop = frame[max(0, y1):min(frame.shape[0], y2), max(0, x1):min(frame.shape[1], x2)]
                age_group, age_conf = self.age_estimator.estimate_age(person_crop)
                self.track_age_cache[track_id] = (age_group, age_conf)
            else:
                age_group, age_conf = self.track_age_cache[track_id]

            # Update Dwell Time & Session
            session = self.dwell_manager.update_track(track_id, current_timestamp, zone_info, age_group, age_conf)

            # Accumulate Heatmap Point
            self.heatmap.add_point(center, weight=1.0)
            if current_timestamp - self.last_event_sample_time >= self.config.get('analytics', {}).get('heatmap_sampling_seconds', 1.0):
                self.buffered_heatmap_points.append({
                    'camera_id': self.camera_id,
                    'timestamp': current_timestamp,
                    'x': center[0],
                    'y': center[1],
                    'weight': 1.0,
                    'zone_id': zone_id
                })

            # Draw Bounding Box & Label
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 120), 2)

            label = f"Person #{track_id} ({int(conf*100)}%)"
            sub_label = f"Dwell: {session['dwell_seconds']}s | {zone_name}"

            cv2.rectangle(annotated_frame, (x1, y1 - 40), (x1 + max(len(label), len(sub_label))*9, y1), (0, 180, 80), -1)
            cv2.putText(annotated_frame, label, (x1 + 5, y1 - 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(annotated_frame, sub_label, (x1 + 5, y1 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (240, 240, 240), 1)

            # Buffer sample detection event periodically (every 1-2 sec)
            if current_timestamp - self.last_event_sample_time >= 1.5:
                self.buffered_events.append({
                    'camera_id': self.camera_id,
                    'track_id': track_id,
                    'timestamp': current_timestamp,
                    'center_x': center[0],
                    'center_y': center[1],
                    'bbox_x': x1,
                    'bbox_y': y1,
                    'bbox_width': x2 - x1,
                    'bbox_height': y2 - y1,
                    'confidence': conf,
                    'zone_id': zone_id
                })

        if current_timestamp - self.last_event_sample_time >= 1.5:
            self.last_event_sample_time = current_timestamp

        # 4. Cleanup lost sessions
        closed_sessions = self.dwell_manager.cleanup_lost_tracks(current_timestamp)
        self.total_visitors_count += len(closed_sessions)

        # 5. Apply Heatmap overlay if requested
        if enable_heatmap_overlay:
            annotated_frame = self.heatmap.generate_overlay(annotated_frame, alpha=0.45)

        # 6. Calculate FPS and stats overlay
        processing_time = time.time() - start_time
        self.fps = round(1.0 / max(processing_time, 0.001), 1)

        # Draw HUD stats
        cv2.rectangle(annotated_frame, (10, 10), (360, 110), (20, 25, 35), -1)
        cv2.rectangle(annotated_frame, (10, 10), (360, 110), (0, 255, 200), 1)
        cv2.putText(annotated_frame, f"CAM: {self.camera_name}", (20, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 200), 2)
        cv2.putText(annotated_frame, f"People Count: {self.current_people_count} | FPS: {self.fps}", (20, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(annotated_frame, f"Entries: {self.total_entries} | Exits: {self.total_exits}", (20, 78), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(annotated_frame, f"Avg Dwell: {self.dwell_manager.get_average_dwell_seconds()}s", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        self.latest_annotated_frame = annotated_frame

        stats = {
            'camera_id': self.camera_id,
            'camera_name': self.camera_name,
            'fps': self.fps,
            'people_count': self.current_people_count,
            'entries': self.total_entries,
            'exits': self.total_exits,
            'occupancy': max(0, self.total_entries - self.total_exits),
            'avg_dwell_seconds': self.dwell_manager.get_average_dwell_seconds(),
            'total_visitors': self.total_visitors_count
        }

        return True, annotated_frame, stats

    def get_closed_sessions_to_flush(self) -> List[Dict[str, Any]]:
        return self.dwell_manager.pop_closed_sessions()

    def get_closed_zone_visits_to_flush(self) -> List[Dict[str, Any]]:
        return self.dwell_manager.pop_closed_zone_visits()

    def finalize(self, final_timestamp: Optional[float] = None) -> Dict[str, Any]:
        """Force-close all active sessions at EOF and return all remaining buffered database records."""
        if final_timestamp is None:
            final_timestamp = time.time()
        
        closed = self.dwell_manager.force_close_all(final_timestamp)
        self.total_visitors_count += len(closed)

        all_closed_sessions = self.get_closed_sessions_to_flush()
        all_zone_visits = self.get_closed_zone_visits_to_flush()
        buffered_events = self.buffered_events.copy()
        self.buffered_events.clear()

        heatmap_pts = self.buffered_heatmap_points.copy()
        self.buffered_heatmap_points.clear()

        return {
            'visitor_sessions': all_closed_sessions,
            'zone_visits': all_zone_visits,
            'detection_events': buffered_events,
            'heatmap_points': heatmap_pts,
            'total_visitors': self.total_visitors_count
        }

    def stop(self):
        self.is_running = False
        self.source.release()
