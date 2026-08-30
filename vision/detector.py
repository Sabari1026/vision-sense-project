import os
import cv2
import threading
import numpy as np
from typing import List, Dict, Any, Tuple

class YOLODetector:
    """High-Performance YOLOv11 Person Detector wrapping Ultralytics with CPU/GPU optimization."""

    def __init__(self, model_name: str = "yolo11n.pt", confidence_threshold: float = 0.35, use_gpu: bool = True, imgsz: int = 480):
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.use_gpu = use_gpu
        self.imgsz = imgsz
        self.model = None
        self.person_class_id = 0  # COCO class 0 is 'person'
        self.is_ready = False
        self.lock = threading.Lock()

        self._load_model()

    def _load_model(self):
        try:
            from ultralytics import YOLO
            import torch

            # Optimize PyTorch CPU threading
            if hasattr(torch, "set_num_threads"):
                torch.set_num_threads(max(1, min(os.cpu_count() or 4, 6)))

            device = 'cuda' if (self.use_gpu and torch.cuda.is_available()) else 'cpu'
            print(f"[YOLODetector] Loading YOLOv11 model '{self.model_name}' on device '{device}'...")

            self.model = YOLO(self.model_name)
            self.model.to(device)
            self.is_ready = True
            print(f"[YOLODetector] YOLOv11 model loaded successfully!")
        except Exception as e:
            print(f"[YOLODetector] Warning: Could not load Ultralytics YOLO model ({e}). Using fallback detector.")
            self.model = None
            self.is_ready = False

    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Run object detection on a BGR OpenCV frame.
        Returns list of dicts: [{'bbox': (x1, y1, x2, y2), 'confidence': float, 'class_id': int, 'center': (cx, cy)}]
        """
        if frame is None:
            return []

        detections = []

        if self.is_ready and self.model is not None:
            try:
                with self.lock:
                    results = self.model.predict(
                        source=frame,
                        conf=self.confidence_threshold,
                        classes=[self.person_class_id],
                        imgsz=self.imgsz,
                        verbose=False
                    )

                if results and len(results) > 0:
                    boxes = results[0].boxes
                    if boxes is not None:
                        for box in boxes:
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                            conf = float(box.conf[0].cpu().numpy())
                            cls_id = int(box.cls[0].cpu().numpy())

                            cx = int((x1 + x2) / 2)
                            cy = int((y1 + y2) / 2)

                            detections.append({
                                'bbox': (int(x1), int(y1), int(x2), int(y2)),
                                'confidence': round(conf, 3),
                                'class_id': cls_id,
                                'center': (cx, cy)
                            })
                return detections
            except Exception as e:
                print(f"[YOLODetector] Prediction error: {e}")

        # Fallback Detector if YOLO is unavailable
        return self._fallback_detect(frame)

    def _fallback_detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Contour/Color-based fallback detector."""
        detections = []
        try:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, np.array([0, 20, 20]), np.array([180, 255, 255]))
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if 1500 < area < 40000:
                    x, y, w, h = cv2.boundingRect(cnt)
                    if 1.2 <= (h / max(w, 1)) <= 4.0:
                        cx = x + w // 2
                        cy = y + h // 2
                        detections.append({
                            'bbox': (x, y, x + w, y + h),
                            'confidence': 0.75,
                            'class_id': 0,
                            'center': (cx, cy)
                        })
        except Exception:
            pass
        return detections
