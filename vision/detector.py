import os
import cv2
import numpy as np
from typing import List, Dict, Any, Tuple

class YOLODetector:
    """YOLO Person Detector wrapping Ultralytics YOLO with CPU/GPU auto-detection."""

    def __init__(self, model_name: str = "yolo11n.pt", confidence_threshold: float = 0.45, use_gpu: bool = True):
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.use_gpu = use_gpu
        self.model = None
        self.person_class_id = 0 # COCO class 0 is 'person'
        self.is_ready = False

        self._load_model()

    def _load_model(self):
        try:
            from ultralytics import YOLO
            import torch

            device = 'cuda' if (self.use_gpu and torch.cuda.is_available()) else 'cpu'
            print(f"[YOLODetector] Loading YOLO model '{self.model_name}' on device '{device}'...")

            self.model = YOLO(self.model_name)
            self.model.to(device)
            self.is_ready = True
            print(f"[YOLODetector] Model loaded successfully!")
        except Exception as e:
            print(f"[YOLODetector] Warning: Could not load Ultralytics YOLO model ({e}). Using OpenCV fallback detector.")
            self.model = None
            self.is_ready = False

    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Run object detection on an BGR OpenCV frame.
        Returns list of dicts: [{'bbox': (x1, y1, x2, y2), 'confidence': float, 'class_id': int, 'center': (cx, cy)}]
        """
        if frame is None:
            return []

        detections = []

        if self.is_ready and self.model is not None:
            try:
                # Perform inference with class 0 (person) filter and standard 640 input resolution
                results = self.model.predict(
                    source=frame,
                    conf=self.confidence_threshold,
                    classes=[self.person_class_id],
                    imgsz=640,
                    verbose=False
                )

                for r in results:
                    boxes = r.boxes
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
                print(f"[YOLODetector] Error during prediction: {e}")

        # Fallback Detector if YOLO is unavailable or frame is synthetic
        return self._fallback_detect(frame)

    def _fallback_detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Contour/Color-based fallback detector for synthetic demo frames or when YOLO is loading."""
        detections = []
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # Look for torso/human figure color ranges in synthetic video
        mask = cv2.inRange(hsv, np.array([0, 20, 20]), np.array([180, 255, 255]))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 1500 < area < 40000:
                x, y, w, h = cv2.boundingRect(cnt)
                # Check aspect ratio typical for humans (height > width)
                if 1.2 <= (h / max(w, 1)) <= 4.0:
                    cx = x + w // 2
                    cy = y + h // 2
                    detections.append({
                        'bbox': (x, y, x + w, y + h),
                        'confidence': 0.85,
                        'class_id': 0,
                        'center': (cx, cy)
                    })
        return detections
