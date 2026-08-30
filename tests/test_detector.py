import pytest
import numpy as np
from vision.detector import YOLODetector

def test_detector_initialization():
    detector = YOLODetector(model_name="yolo11n.pt", confidence_threshold=0.25, use_gpu=False, imgsz=480)
    assert detector is not None
    assert detector.person_class_id == 0

def test_detector_inference_on_synthetic_frame():
    detector = YOLODetector(model_name="yolo11n.pt", confidence_threshold=0.25, use_gpu=False, imgsz=480)
    # Create synthetic test frame (720x1280 BGR)
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    detections = detector.detect(frame)
    assert isinstance(detections, list)

def test_detector_empty_frame():
    detector = YOLODetector(model_name="yolo11n.pt")
    detections = detector.detect(None)
    assert detections == []
