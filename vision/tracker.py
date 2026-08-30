import numpy as np
import math
import time
from typing import List, Dict, Any, Tuple, Optional

def compute_iou(box1: Tuple[int, int, int, int], box2: Tuple[int, int, int, int]) -> float:
    """Computes Intersection over Union (IoU) between two bounding boxes (x1, y1, x2, y2)."""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    inter_area = max(0, x2 - x1) * max(0, y2 - y1)
    if inter_area <= 0:
        return 0.0

    area1 = max(0, box1[2] - box1[0]) * max(0, box1[3] - box1[1])
    area2 = max(0, box2[2] - box2[0]) * max(0, box2[3] - box2[1])
    union_area = area1 + area2 - inter_area
    if union_area <= 0:
        return 0.0

    return float(inter_area / union_area)

class STrack:
    """Single Track object maintaining ByteTrack track state, Kalman velocity, and history."""

    def __init__(self, track_id: int, bbox: Tuple[int, int, int, int], conf: float, class_id: int = 0):
        self.track_id = track_id
        self.bbox = bbox  # (x1, y1, x2, y2)
        self.conf = conf
        self.class_id = class_id
        self.state = "TRACKED"  # "TRACKED", "LOST", "REMOVED"
        self.time_since_update = 0
        self.hits = 1
        self.history: List[Tuple[int, int]] = []
        
        # Velocity estimation for smooth trajectory prediction
        self.vx = 0.0
        self.vy = 0.0
        self.center = (int((bbox[0] + bbox[2]) / 2), int((bbox[1] + bbox[3]) / 2))
        self.footprint = (self.center[0], bbox[3])
        self.history.append(self.footprint)

    def predict(self):
        """Predict next bounding box position based on current velocity."""
        if self.time_since_update > 0:
            x1, y1, x2, y2 = self.bbox
            w = x2 - x1
            h = y2 - y1
            cx = self.center[0] + int(self.vx * min(self.time_since_update, 4))
            cy = self.center[1] + int(self.vy * min(self.time_since_update, 4))
            self.bbox = (cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2)
            self.center = (cx, cy)
            self.footprint = (cx, self.bbox[3])
        self.time_since_update += 1

    def update(self, new_bbox: Tuple[int, int, int, int], conf: float, smoothing_alpha: float = 0.70):
        """Update track with new matched detection box applying EMA smoothing."""
        new_cx = (new_bbox[0] + new_bbox[2]) / 2.0
        new_cy = (new_bbox[1] + new_bbox[3]) / 2.0
        dt = max(1, self.time_since_update)
        
        # Velocity moving average
        calc_vx = (new_cx - self.center[0]) / float(dt)
        calc_vy = (new_cy - self.center[1]) / float(dt)
        self.vx = 0.6 * self.vx + 0.4 * calc_vx
        self.vy = 0.6 * self.vy + 0.4 * calc_vy

        # Apply Exponential Moving Average (EMA) coordinate smoothing
        a = smoothing_alpha
        sx1 = int(round(a * new_bbox[0] + (1.0 - a) * self.bbox[0]))
        sy1 = int(round(a * new_bbox[1] + (1.0 - a) * self.bbox[1]))
        sx2 = int(round(a * new_bbox[2] + (1.0 - a) * self.bbox[2]))
        sy2 = int(round(a * new_bbox[3] + (1.0 - a) * self.bbox[3]))

        self.bbox = (sx1, sy1, sx2, sy2)
        self.center = (int((sx1 + sx2) / 2), int((sy1 + sy2) / 2))
        self.footprint = (self.center[0], sy2)
        self.conf = conf
        self.state = "TRACKED"
        self.time_since_update = 0
        self.hits += 1
        
        self.history.append(self.footprint)
        if len(self.history) > 30:
            self.history.pop(0)

    def mark_lost(self):
        self.state = "LOST"

    def mark_removed(self):
        self.state = "REMOVED"

class ByteTracker:
    """
    High-Performance ByteTrack: Multi-Object Tracking with Two-Stage Association.
    """

    def __init__(self, track_thresh: float = 0.35, match_thresh: float = 0.25, max_lost_frames: int = 40, smoothing_alpha: float = 0.70):
        self.track_thresh = track_thresh
        self.match_thresh = match_thresh
        self.max_lost_frames = max_lost_frames
        self.smoothing_alpha = smoothing_alpha

        self.tracked_stracks: List[STrack] = []
        self.lost_stracks: List[STrack] = []
        self.next_id = 101  # Person IDs start at #101

    def update(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Step 1: Predict positions of all existing active and lost tracks
        for strack in self.tracked_stracks:
            strack.predict()
        for strack in self.lost_stracks:
            strack.predict()

        # Step 2: Separate detections into High-Score and Low-Score pools
        high_dets = []
        low_dets = []
        for det in detections:
            conf = det['confidence']
            if conf >= self.track_thresh:
                high_dets.append(det)
            elif conf >= 0.12:
                low_dets.append(det)

        # Step 3: First Association - High score detections with active tracked tracks
        active_tracks = [t for t in self.tracked_stracks if t.state == "TRACKED"]
        track_pool = active_tracks + self.lost_stracks
        matched_tracks_1, unmatched_tracks_1, unmatched_dets_1 = self._associate(track_pool, high_dets, self.match_thresh)

        for track, det in matched_tracks_1:
            track.update(det['bbox'], det['confidence'], self.smoothing_alpha)
            if track in self.lost_stracks:
                self.lost_stracks.remove(track)
                self.tracked_stracks.append(track)

        # Step 4: Second Association - Unmatched tracks with Low-score detections (recovers occluded visitors)
        remaining_tracked = [t for t in unmatched_tracks_1 if t.state == "TRACKED"]
        matched_tracks_2, unmatched_tracks_2, _ = self._associate(remaining_tracked, low_dets, self.match_thresh * 0.75)

        for track, det in matched_tracks_2:
            track.update(det['bbox'], det['confidence'], self.smoothing_alpha)

        # Step 5: Mark unmatched tracks as lost or removed
        for track in unmatched_tracks_2:
            if track.state == "TRACKED":
                track.mark_lost()
                if track in self.tracked_stracks:
                    self.tracked_stracks.remove(track)
                self.lost_stracks.append(track)

        # Clean up expired lost tracks
        for track in list(self.lost_stracks):
            if track.time_since_update > self.max_lost_frames:
                track.mark_removed()
                self.lost_stracks.remove(track)

        # Step 6: Initiate new tracks from unmatched high-confidence detections
        for det in unmatched_dets_1:
            if det['confidence'] >= self.track_thresh:
                new_track = STrack(
                    track_id=self.next_id,
                    bbox=det['bbox'],
                    conf=det['confidence'],
                    class_id=det.get('class_id', 0)
                )
                self.next_id += 1
                self.tracked_stracks.append(new_track)

        # Format output
        results = []
        for track in self.tracked_stracks:
            if track.state == "TRACKED":
                results.append({
                    'bbox': track.bbox,
                    'confidence': round(track.conf, 3),
                    'class_id': track.class_id,
                    'center': track.center,
                    'footprint': track.footprint,
                    'track_id': track.track_id,
                    'vx': round(track.vx, 2),
                    'vy': round(track.vy, 2),
                    'history': track.history.copy()
                })

        return results

    def _associate(self, tracks: List[STrack], detections: List[Dict[str, Any]], match_thresh: float) -> Tuple[List[Tuple[STrack, Dict[str, Any]]], List[STrack], List[Dict[str, Any]]]:
        if len(tracks) == 0 or len(detections) == 0:
            return [], tracks.copy(), detections.copy()

        cost_matrix = np.zeros((len(tracks), len(detections)), dtype=np.float32)
        for i, t in enumerate(tracks):
            for j, d in enumerate(detections):
                cost_matrix[i, j] = compute_iou(t.bbox, d['bbox'])

        matched_tracks = []
        unmatched_tracks = set(range(len(tracks)))
        unmatched_dets = set(range(len(detections)))

        while len(unmatched_tracks) > 0 and len(unmatched_dets) > 0:
            max_idx = np.unravel_index(np.argmax(cost_matrix), cost_matrix.shape)
            i, j = max_idx[0], max_idx[1]
            best_iou = cost_matrix[i, j]

            if best_iou < match_thresh:
                break

            matched_tracks.append((tracks[i], detections[j]))
            unmatched_tracks.remove(i)
            unmatched_dets.remove(j)
            cost_matrix[i, :] = -1.0
            cost_matrix[:, j] = -1.0

        return matched_tracks, [tracks[i] for i in unmatched_tracks], [detections[j] for j in unmatched_dets]

class PersonTracker:
    """Unified Tracker Wrapper providing ByteTrack multi-object tracking."""

    def __init__(self, tracker_type: str = "bytetrack", smoothing_alpha: float = 0.70):
        self.tracker_type = tracker_type
        self.byte_tracker = ByteTracker(
            track_thresh=0.28,
            match_thresh=0.22,
            max_lost_frames=45,
            smoothing_alpha=smoothing_alpha
        )

    def update(self, detections: List[Dict[str, Any]], model_instance=None, frame=None) -> List[Dict[str, Any]]:
        return self.byte_tracker.update(detections)
