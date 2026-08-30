import numpy as np
import math
from typing import List, Dict, Any, Tuple

class CentroidTracker:
    """Fallback Centroid & IoU Persistent Multi-Object Tracker for stable track ID assignment."""

    def __init__(self, max_disappeared: int = 15, max_distance: int = 100):
        self.next_object_id = 101 # Start track IDs at 101
        self.objects: Dict[int, Tuple[int, int]] = {} # id -> center (cx, cy)
        self.bboxes: Dict[int, Tuple[int, int, int, int]] = {} # id -> (x1, y1, x2, y2)
        self.confidences: Dict[int, float] = {}
        self.disappeared: Dict[int, int] = {}
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance

    def register(self, center: Tuple[int, int], bbox: Tuple[int, int, int, int], conf: float) -> int:
        object_id = self.next_object_id
        self.objects[object_id] = center
        self.bboxes[object_id] = bbox
        self.confidences[object_id] = conf
        self.disappeared[object_id] = 0
        self.next_object_id += 1
        return object_id

    def deregister(self, object_id: int):
        del self.objects[object_id]
        del self.bboxes[object_id]
        del self.confidences[object_id]
        del self.disappeared[object_id]

    def update(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if len(detections) == 0:
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
            return []

        input_centers = [det['center'] for det in detections]
        input_bboxes = [det['bbox'] for det in detections]
        input_confs = [det['confidence'] for det in detections]

        if len(self.objects) == 0:
            tracked_results = []
            for i in range(len(input_centers)):
                obj_id = self.register(input_centers[i], input_bboxes[i], input_confs[i])
                det = detections[i].copy()
                det['track_id'] = obj_id
                tracked_results.append(det)
            return tracked_results

        object_ids = list(self.objects.keys())
        object_centers = list(self.objects.values())

        # Compute Euclidean distance matrix between existing objects and new input detections
        D = np.zeros((len(object_centers), len(input_centers)), dtype=np.float32)
        for i in range(len(object_centers)):
            for j in range(len(input_centers)):
                D[i, j] = math.hypot(object_centers[i][0] - input_centers[j][0],
                                     object_centers[i][1] - input_centers[j][1])

        rows = D.min(axis=1).argsort()
        cols = D.argmin(axis=1)[rows]

        used_rows = set()
        used_cols = set()

        tracked_results = []

        for (row, col) in zip(rows, cols):
            if row in used_rows or col in used_cols:
                continue

            if D[row, col] > self.max_distance:
                continue

            object_id = object_ids[row]
            self.objects[object_id] = input_centers[col]
            self.bboxes[object_id] = input_bboxes[col]
            self.confidences[object_id] = input_confs[col]
            self.disappeared[object_id] = 0

            used_rows.add(row)
            used_cols.add(col)

            det = detections[col].copy()
            det['track_id'] = object_id
            tracked_results.append(det)

        unused_rows = set(range(0, D.shape[0])).difference(used_rows)
        unused_cols = set(range(0, D.shape[1])).difference(used_cols)

        for row in unused_rows:
            object_id = object_ids[row]
            self.disappeared[object_id] += 1
            if self.disappeared[object_id] > self.max_disappeared:
                self.deregister(object_id)

        for col in unused_cols:
            obj_id = self.register(input_centers[col], input_bboxes[col], input_confs[col])
            det = detections[col].copy()
            det['track_id'] = obj_id
            tracked_results.append(det)

        return tracked_results

class PersonTracker:
    """Wrapper supporting ByteTrack/BoT-SORT tracking with fallback centroid tracker and EMA trajectory smoothing."""

    def __init__(self, tracker_type: str = "bytetrack", smoothing_alpha: float = 0.65):
        self.tracker_type = tracker_type
        self.centroid_tracker = CentroidTracker()
        self.smoothing_alpha = smoothing_alpha
        self.track_history: Dict[int, Tuple[float, float, float, float]] = {}

    def smooth_bbox(self, track_id: int, new_bbox: Tuple[int, int, int, int]) -> Tuple[int, int, int, int]:
        """Applies Exponential Moving Average (EMA) filtering for smooth, jitter-free bounding box trajectory."""
        if track_id in self.track_history:
            px1, py1, px2, py2 = self.track_history[track_id]
            a = self.smoothing_alpha
            sx1 = a * new_bbox[0] + (1.0 - a) * px1
            sy1 = a * new_bbox[1] + (1.0 - a) * py1
            sx2 = a * new_bbox[2] + (1.0 - a) * px2
            sy2 = a * new_bbox[3] + (1.0 - a) * py2
            self.track_history[track_id] = (sx1, sy1, sx2, sy2)
            return (int(round(sx1)), int(round(sy1)), int(round(sx2)), int(round(sy2)))
        else:
            self.track_history[track_id] = (float(new_bbox[0]), float(new_bbox[1]), float(new_bbox[2]), float(new_bbox[3]))
            return new_bbox

    def update(self, detections: List[Dict[str, Any]], model_instance=None, frame=None) -> List[Dict[str, Any]]:
        """
        Track detections across consecutive frames.
        If model_instance supports `model.track(frame, persist=True)`, use ByteTrack/BoT-SORT, otherwise fall back to CentroidTracker.
        """
        tracked_output = []

        if model_instance is not None and frame is not None:
            try:
                results = model_instance.track(frame, persist=True, verbose=False, tracker=f"{self.tracker_type}.yaml")
                for r in results:
                    boxes = r.boxes
                    if boxes is not None and boxes.id is not None:
                        for box, track_id in zip(boxes, boxes.id):
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                            conf = float(box.conf[0].cpu().numpy())
                            tid = int(track_id.cpu().numpy())

                            # Apply EMA bounding box trajectory smoothing
                            sm_bbox = self.smooth_bbox(tid, (x1, y1, x2, y2))
                            cx = int((sm_bbox[0] + sm_bbox[2]) / 2)
                            cy = int((sm_bbox[1] + sm_bbox[3]) / 2)

                            tracked_output.append({
                                'bbox': sm_bbox,
                                'confidence': round(conf, 3),
                                'class_id': 0,
                                'center': (cx, cy),
                                'track_id': tid
                            })
                if len(tracked_output) > 0:
                    return tracked_output
            except Exception as e:
                pass

        # Fallback to CentroidTracker
        raw_tracked = self.centroid_tracker.update(detections)
        for obj in raw_tracked:
            sm_bbox = self.smooth_bbox(obj['track_id'], obj['bbox'])
            obj['bbox'] = sm_bbox
            obj['center'] = (int((sm_bbox[0] + sm_bbox[2]) / 2), int((sm_bbox[1] + sm_bbox[3]) / 2))
            tracked_output.append(obj)

        return tracked_output
