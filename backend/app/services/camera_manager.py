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
    """Manager controlling concurrent high-speed processors for 4 CCTV Cameras."""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.processors: Dict[str, CameraStreamProcessor] = {}
        self.is_running: Dict[str, bool] = {}
        self.lock = threading.Lock()

        from vision.detector import YOLODetector
        self.shared_detector = YOLODetector(
            model_name=self.config.get('YOLO_MODEL', 'yolo11n.pt'),
            confidence_threshold=self.config.get('vision', {}).get('confidence', 0.25),
            use_gpu=self.config.get('USE_GPU', True),
            imgsz=self.config.get('vision', {}).get('imgsz', 512)
        )

        self._discover_and_setup_cameras()
        self._start_db_sync_thread()
        # Auto-start all 4 cameras
        self.start_all()

    def _load_config(self) -> Dict[str, Any]:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                print(f"[CameraManager] Error loading config ({e}): using defaults.")
        return {'vision': {'confidence': 0.35, 'tracker': 'bytetrack', 'lost_timeout_seconds': 5}}

    def _discover_and_setup_cameras(self):
        videos_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "videos"))
        os.makedirs(videos_dir, exist_ok=True)

        camera_configs = [
            {"file": "camera1.mp4", "name": "CAM-01 Main Entrance & Entry Line"},
            {"file": "camera2.mp4", "name": "CAM-02 Apparel & Fashion Department"},
            {"file": "camera3.mp4", "name": "CAM-03 Electronics & Showcase Hub"},
            {"file": "camera4.mp4", "name": "CAM-04 Checkout Desks & POS"}
        ]

        for idx, cfg in enumerate(camera_configs, start=1):
            cam_id = f"{idx}{idx}{idx}{idx}{idx}{idx}{idx}{idx}-{idx}{idx}{idx}{idx}-{idx}{idx}{idx}{idx}-{idx}{idx}{idx}{idx}-{idx}{idx}{idx}{idx}{idx}{idx}{idx}{idx}{idx}{idx}{idx}{idx}"
            video_file = os.path.join(videos_dir, cfg["file"])
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

    def start_camera(self, camera_id: str) -> bool:
        with self.lock:
            if camera_id not in self.processors:
                return False

            processor = self.processors[camera_id]
            processor.start()
            self.is_running[camera_id] = True
            print(f"[CameraManager] Started background processing worker for Camera {camera_id}.")
            return True

    def stop_camera(self, camera_id: str):
        with self.lock:
            if camera_id in self.processors:
                self.processors[camera_id].stop()
                self.is_running[camera_id] = False
                print(f"[CameraManager] Stopped camera worker {camera_id}.")

    def start_all(self):
        for cam_id in list(self.processors.keys()):
            self.start_camera(cam_id)

    def stop_all(self):
        for cam_id in list(self.processors.keys()):
            self.stop_camera(cam_id)

    def _start_db_sync_thread(self):
        def db_sync_worker():
            while True:
                time.sleep(5.0)
                for cam_id, proc in list(self.processors.items()):
                    if proc.is_running:
                        try:
                            closed_sessions = proc.get_closed_sessions_to_flush()
                            if closed_sessions:
                                db_service.save_visitor_sessions(closed_sessions)

                            pts = proc.buffered_heatmap_points.copy()
                            proc.buffered_heatmap_points.clear()
                            if pts:
                                db_service.save_heatmap_points(pts)
                        except Exception:
                            pass

        t = threading.Thread(target=db_sync_worker, daemon=True)
        t.start()

    def get_latest_frame_jpeg(self, camera_id: str) -> Optional[bytes]:
        if camera_id in self.processors:
            proc = self.processors[camera_id]
            if proc.latest_jpeg_bytes is not None:
                return proc.latest_jpeg_bytes
            elif proc.latest_annotated_frame is not None:
                ret, jpeg = cv2.imencode('.jpg', proc.latest_annotated_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                if ret:
                    return jpeg.tobytes()
        return None

    def get_all_stats(self) -> List[Dict[str, Any]]:
        stats_list = []
        for cam_id, proc in self.processors.items():
            st = proc.get_stats()
            st['status'] = 'LIVE' if proc.is_running else 'STOPPED'
            stats_list.append(st)
        return stats_list

camera_manager = MultiCameraManager()
