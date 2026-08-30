import os
import time
import threading
import cv2
import yaml
from typing import Dict, Any, List, Optional
from vision.processor import CameraStreamProcessor
try:
    from backend.app.services.supabase_client import db_service
except ModuleNotFoundError:
    from app.services.supabase_client import db_service

class MultiCameraManager:
    """Manager controlling concurrent background processors for 4 CCTV Cameras."""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.processors: Dict[str, CameraStreamProcessor] = {}
        self.threads: Dict[str, threading.Thread] = {}
        self.is_running: Dict[str, bool] = {}
        self.camera_stats: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()

        from vision.detector import YOLODetector
        self.shared_detector = YOLODetector(
            model_name=self.config.get('YOLO_MODEL', 'yolo11n.pt'),
            confidence_threshold=self.config.get('vision', {}).get('confidence', 0.45),
            use_gpu=self.config.get('USE_GPU', False)
        )

        self._discover_and_setup_cameras()

    def _load_config(self) -> Dict[str, Any]:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                print(f"[CameraManager] Error loading config ({e}): using defaults.")
        return {'vision': {'confidence': 0.45, 'tracker': 'bytetrack', 'lost_timeout_seconds': 5}}

    def _discover_and_setup_cameras(self):
        videos_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "videos"))
        os.makedirs(videos_dir, exist_ok=True)

        mp4_files = sorted([os.path.join(videos_dir, f) for f in os.listdir(videos_dir) if f.endswith('.mp4')])

        camera_configs = [
            {"file": "camera1.mp4", "name": "CAM-01 Main Entrance & Entry Line"},
            {"file": "camera2.mp4", "name": "CAM-02 Apparel & Fashion Department"},
            {"file": "camera3.mp4", "name": "CAM-03 Electronics & Showcase Hub"},
            {"file": "camera4.mp4", "name": "CAM-04 Checkout Desks & POS"}
        ]

        for idx, cfg in enumerate(camera_configs, start=1):
            cam_id = f"{idx}{idx}{idx}{idx}{idx}{idx}{idx}{idx}-{idx}{idx}{idx}{idx}-{idx}{idx}{idx}{idx}-{idx}{idx}{idx}{idx}-{idx}{idx}{idx}{idx}{idx}{idx}{idx}{idx}{idx}{idx}{idx}{idx}"
            video_file = os.path.join(videos_dir, cfg["file"])
            if not os.path.exists(video_file):
                # Fallback to any mp4 in videos directory
                video_file = mp4_files[idx - 1] if idx <= len(mp4_files) else (mp4_files[0] if mp4_files else "")
            cam_name = cfg["name"]

            processor = CameraStreamProcessor(
                camera_id=cam_id,
                camera_name=cam_name,
                source_path=video_file,
                config=self.config,
                shared_detector=self.shared_detector
            )
            self.processors[cam_id] = processor
            self.is_running[cam_id] = False
            self.camera_stats[cam_id] = {
                'camera_id': cam_id,
                'camera_name': cam_name,
                'status': 'STOPPED' if not os.path.exists(video_file) else 'LIVE',
                'fps': 0,
                'people_count': 0,
                'entries': 0,
                'exits': 0,
                'occupancy': 0,
                'avg_dwell_seconds': 0.0,
                'total_visitors': 0
            }

    def start_camera(self, camera_id: str) -> bool:
        with self.lock:
            if camera_id not in self.processors:
                return False

            if self.is_running.get(camera_id, False):
                return True # Already running

            processor = self.processors[camera_id]
            if not processor.initialize():
                self.camera_stats[camera_id]['status'] = 'ERROR'
                print(f"[CameraManager] Failed to start camera {camera_id}: Video source unopened.")
                return False

            self.is_running[camera_id] = True
            self.camera_stats[camera_id]['status'] = 'LIVE'

            t = threading.Thread(target=self._worker_loop, args=(camera_id,), daemon=True)
            self.threads[camera_id] = t
            t.start()
            print(f"[CameraManager] Started background processing worker for Camera {camera_id}.")
            return True

    def stop_camera(self, camera_id: str):
        with self.lock:
            if camera_id in self.is_running:
                self.is_running[camera_id] = False
                if camera_id in self.processors:
                    self.processors[camera_id].stop()
                self.camera_stats[camera_id]['status'] = 'STOPPED'
                print(f"[CameraManager] Stopped camera worker {camera_id}.")

    def start_all(self):
        for cam_id in list(self.processors.keys()):
            self.start_camera(cam_id)

    def stop_all(self):
        for cam_id in list(self.processors.keys()):
            self.stop_camera(cam_id)

    def _worker_loop(self, camera_id: str):
        processor = self.processors[camera_id]

        last_db_flush = time.time()

        while self.is_running.get(camera_id, False):
            t_start = time.time()
            try:
                success, frame, stats = processor.process_next_frame()
                if not success:
                    time.sleep(0.02)
                    continue

                with self.lock:
                    self.camera_stats[camera_id].update(stats)
                    self.camera_stats[camera_id]['status'] = 'LIVE'

                # Periodically flush closed sessions and heatmap points to database
                now = time.time()
                if now - last_db_flush >= 5.0:
                    last_db_flush = now
                    closed_sessions = processor.get_closed_sessions_to_flush()
                    if closed_sessions:
                        db_service.save_visitor_sessions(closed_sessions)

                    points = processor.buffered_heatmap_points.copy()
                    processor.buffered_heatmap_points.clear()
                    if points:
                        db_service.save_heatmap_points(points)

                # Adaptive frame sleep timing locked to target 30.0 FPS
                t_elapsed = time.time() - t_start
                sleep_duration = max(0.001, (1.0 / 30.0) - t_elapsed)
                time.sleep(sleep_duration)
            except Exception as e:
                print(f"[CameraManager] Error in worker for camera {camera_id}: {e}")
                self.camera_stats[camera_id]['status'] = 'ERROR'
                time.sleep(0.5)

    def get_latest_frame_jpeg(self, camera_id: str, quality: int = 75) -> Optional[bytes]:
        if camera_id in self.processors:
            proc = self.processors[camera_id]
            frame = proc.latest_annotated_frame if proc.latest_annotated_frame is not None else proc.latest_frame
            if frame is not None:
                ret, jpeg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
                if ret:
                    return jpeg.tobytes()
        return None

    def get_all_stats(self) -> List[Dict[str, Any]]:
        with self.lock:
            return list(self.camera_stats.values())

camera_manager = MultiCameraManager()
