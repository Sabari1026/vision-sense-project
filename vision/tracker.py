import math
import time
import numpy as np
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

class KalmanBoxTracker:
    """
    Lightweight 8-state Kalman Filter for bounding box tracking:
    State: [x_center, y_center, width, height, vx, vy, vw, vh]
    """

    def __init__(self, bbox: Tuple[int, int, int, int]):
        x1, y1, x2, y2 = bbox
        w = max(1.0, float(x2 - x1))
        h = max(1.0, float(y2 - y1))
        cx = float(x1 + x2) / 2.0
        cy = float(y1 + y2) / 2.0

        # State vector [cx, cy, w, h, vx, vy, vw, vh]
        self.x = np.array([cx, cy, w, h, 0.0, 0.0, 0.0, 0.0], dtype=np.float32)

        # State transition matrix F
        self.F = np.eye(8, dtype=np.float32)
        for i in range(4):
            self.F[i, i + 4] = 1.0  # pos += vel * dt

        # Measurement matrix H
        self.H = np.zeros((4, 8), dtype=np.float32)
        for i in range(4):
            self.H[i, i] = 1.0

        # Covariance matrix P
        self.P = np.diag([10.0, 10.0, 10.0, 10.0, 100.0, 100.0, 100.0, 100.0]).astype(np.float32)

        # Process noise covariance Q
        self.Q = np.diag([1.0, 1.0, 1.0, 1.0, 0.05, 0.05, 0.05, 0.05]).astype(np.float32)

        # Measurement noise covariance R
        self.R = np.diag([2.0, 2.0, 4.0, 4.0]).astype(np.float32)

    def predict(self) -> Tuple[int, int, int, int]:
        """Advances state by one time step and returns predicted bbox."""
        self.x = np.dot(self.F, self.x)
        self.P = np.dot(np.dot(self.F, self.P), self.F.T) + self.Q

        cx, cy, w, h = self.x[0], self.x[1], max(10.0, self.x[2]), max(20.0, self.x[3])
        return (int(round(cx - w / 2.0)), int(round(cy - h / 2.0)),
                int(round(cx + w / 2.0)), int(round(cy + h / 2.0)))

    def update(self, bbox: Tuple[int, int, int, int]):
        """Updates Kalman state with new observed detection box."""
        x1, y1, x2, y2 = bbox
        w = max(1.0, float(x2 - x1))
        h = max(1.0, float(y2 - y1))
        cx = float(x1 + x2) / 2.0
        cy = float(y1 + y2) / 2.0

        z = np.array([cx, cy, w, h], dtype=np.float32)
        y = z - np.dot(self.H, self.x)  # Measurement residual
        S = np.dot(np.dot(self.H, self.P), self.H.T) + self.R
        K = np.dot(np.dot(self.P, self.H.T), np.linalg.inv(S))  # Kalman gain

        self.x = self.x + np.dot(K, y)
        I = np.eye(8, dtype=np.float32)
        self.P = np.dot(I - np.dot(K, self.H), self.P)

    def get_state(self) -> Tuple[Tuple[int, int, int, int], float, float]:
        cx, cy, w, h = self.x[0], self.x[1], max(10.0, self.x[2]), max(20.0, self.x[3])
        vx, vy = float(self.x[4]), float(self.x[5])
        box = (int(round(cx - w / 2.0)), int(round(cy - h / 2.0)),
               int(round(cx + w / 2.0)), int(round(cy + h / 2.0)))
        return box, vx, vy

class TrackState:
    """
    Complete Track State Object maintaining full track lifecycle,
    temporal center/dimension smoothing, and trajectory history.
    """

    def __init__(self, track_id: int, bbox: Tuple[int, int, int, int], conf: float, camera_id: str = "camera_1",
                 enable_kalman: bool = True, smoothing_alpha: float = 0.65):
        self.track_id = track_id
        self.camera_id = camera_id
        self.conf = conf
        self.state = "NEW"  # NEW -> CONFIRMED -> ACTIVE -> TEMPORARILY_LOST -> RECOVERED -> EXITED
        
        self.first_seen = time.time()
        self.last_seen = time.time()
        self.hits = 1
        self.time_since_update = 0
        self.age = 1

        self.enable_kalman = enable_kalman
        self.smoothing_alpha = smoothing_alpha

        # Raw detection coords
        self.raw_bbox = bbox
        self.raw_center = (int((bbox[0] + bbox[2]) / 2), int((bbox[1] + bbox[3]) / 2))

        # Smoothed coords (Center + Width + Height representation for aspect-ratio stability)
        self.smoothed_cx = float(self.raw_center[0])
        self.smoothed_cy = float(self.raw_center[1])
        self.smoothed_w = float(bbox[2] - bbox[0])
        self.smoothed_h = float(bbox[3] - bbox[1])
        self.smoothed_bbox = bbox
        self.smoothed_center = self.raw_center

        self.velocity_x = 0.0
        self.velocity_y = 0.0

        self.kalman = KalmanBoxTracker(bbox) if enable_kalman else None
        
        # Trajectory history of ground footprints (cx, y2)
        self.trajectory: List[Tuple[int, int]] = [(self.raw_center[0], bbox[3])]
        
        self.current_zone: Optional[str] = None
        self.zone_entry_time: Optional[float] = None
        self.total_dwell_seconds: float = 0.0

    def predict(self) -> Tuple[int, int, int, int]:
        """Predicts position for next frame using Kalman filter or linear velocity."""
        self.age += 1
        if self.time_since_update > 0:
            if self.state == "ACTIVE":
                self.state = "TEMPORARILY_LOST"

        if self.enable_kalman and self.kalman is not None:
            pred_box = self.kalman.predict()
            self.smoothed_bbox = pred_box
            self.smoothed_center = (int((pred_box[0] + pred_box[2]) / 2), int((pred_box[1] + pred_box[3]) / 2))
            self.smoothed_cx, self.smoothed_cy = float(self.smoothed_center[0]), float(self.smoothed_center[1])
            self.smoothed_w = float(pred_box[2] - pred_box[0])
            self.smoothed_h = float(pred_box[3] - pred_box[1])
        else:
            # Constant velocity prediction
            self.smoothed_cx += self.velocity_x
            self.smoothed_cy += self.velocity_y
            half_w = self.smoothed_w / 2.0
            half_h = self.smoothed_h / 2.0
            self.smoothed_bbox = (
                int(round(self.smoothed_cx - half_w)),
                int(round(self.smoothed_cy - half_h)),
                int(round(self.smoothed_cx + half_w)),
                int(round(self.smoothed_cy + half_h))
            )
            self.smoothed_center = (int(round(self.smoothed_cx)), int(round(self.smoothed_cy)))

        self.time_since_update += 1
        return self.smoothed_bbox

    def update(self, new_bbox: Tuple[int, int, int, int], conf: float, min_confirmation_frames: int = 2):
        """
        Updates track state with newly associated YOLO detection.
        Applies displacement jump prevention and temporal smoothing.
        """
        self.last_seen = time.time()
        self.raw_bbox = new_bbox
        self.conf = conf
        raw_cx = float(new_bbox[0] + new_bbox[2]) / 2.0
        raw_cy = float(new_bbox[1] + new_bbox[3]) / 2.0
        raw_w = float(new_bbox[2] - new_bbox[0])
        raw_h = float(new_bbox[3] - new_bbox[1])
        self.raw_center = (int(round(raw_cx)), int(round(raw_cy)))

        # Update Kalman Filter
        if self.enable_kalman and self.kalman is not None:
            self.kalman.update(new_bbox)
            k_box, kvx, kvy = self.kalman.get_state()
            self.velocity_x = 0.7 * self.velocity_x + 0.3 * kvx
            self.velocity_y = 0.7 * self.velocity_y + 0.3 * kvy

        # Anti-Jumping Check: Test Euclidean displacement against adaptive threshold
        dt = max(1, self.time_since_update)
        displacement = math.hypot(raw_cx - self.smoothed_cx, raw_cy - self.smoothed_cy)
        max_allowed_disp = max(70.0, 1.4 * raw_h)

        if displacement > max_allowed_disp:
            # Suspicious jump: clamp movement toward new detection rather than teleporting
            scale = max_allowed_disp / displacement
            target_cx = self.smoothed_cx + (raw_cx - self.smoothed_cx) * scale
            target_cy = self.smoothed_cy + (raw_cy - self.smoothed_cy) * scale
        else:
            target_cx = raw_cx
            target_cy = raw_cy
            # Instantaneous velocity update
            calc_vx = (raw_cx - self.smoothed_cx) / float(dt)
            calc_vy = (raw_cy - self.smoothed_cy) / float(dt)
            self.velocity_x = 0.65 * self.velocity_x + 0.35 * calc_vx
            self.velocity_y = 0.65 * self.velocity_y + 0.35 * calc_vy

        # Temporal Exponential Moving Average (EMA) Smoothing for Center + Dimensions
        alpha = self.smoothing_alpha
        self.smoothed_cx = alpha * target_cx + (1.0 - alpha) * self.smoothed_cx
        self.smoothed_cy = alpha * target_cy + (1.0 - alpha) * self.smoothed_cy
        self.smoothed_w = alpha * raw_w + (1.0 - alpha) * self.smoothed_w
        self.smoothed_h = alpha * raw_h + (1.0 - alpha) * self.smoothed_h

        # Reconstruct smoothed bounding box
        half_w = self.smoothed_w / 2.0
        half_h = self.smoothed_h / 2.0
        self.smoothed_bbox = (
            int(round(self.smoothed_cx - half_w)),
            int(round(self.smoothed_cy - half_h)),
            int(round(self.smoothed_cx + half_w)),
            int(round(self.smoothed_cy + half_h))
        )
        self.smoothed_center = (int(round(self.smoothed_cx)), int(round(self.smoothed_cy)))

        # Update Lifecycle State
        self.hits += 1
        if self.state == "TEMPORARILY_LOST":
            self.state = "RECOVERED"
        elif self.hits >= min_confirmation_frames:
            self.state = "ACTIVE"
        else:
            self.state = "CONFIRMED"

        self.time_since_update = 0

        # Update ground footprint trajectory
        footprint = (self.smoothed_center[0], self.smoothed_bbox[3])
        self.trajectory.append(footprint)
        if len(self.trajectory) > 50:
            self.trajectory.pop(0)

class ByteTracker:
    """
    Enterprise-Grade ByteTrack Multi-Object Tracker with:
    - Two-Stage High/Low Confidence Association
    - Kalman Filter State Estimation
    - Temporal Bounding Box & Center Smoothing
    - Anti-Jumping Displacement Validation
    - Full Track Lifecycle Management (NEW -> CONFIRMED -> ACTIVE -> TEMPORARILY_LOST -> RECOVERED -> EXITED)
    """

    def __init__(self, track_thresh: float = 0.28, match_thresh: float = 0.22, max_lost_frames: int = 50,
                 smoothing_alpha: float = 0.65, enable_kalman: bool = True, min_confirmation_frames: int = 2,
                 camera_id: str = "camera_1"):
        self.track_thresh = track_thresh
        self.match_thresh = match_thresh
        self.max_lost_frames = max_lost_frames
        self.smoothing_alpha = smoothing_alpha
        self.enable_kalman = enable_kalman
        self.min_confirmation_frames = min_confirmation_frames
        self.camera_id = camera_id

        self.tracked_stracks: List[TrackState] = []
        self.lost_stracks: List[TrackState] = []
        self.next_id = 101

    def update(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Executes ByteTrack two-stage data association and updates smoothed track states.
        """
        # Step 1: Predict positions for all tracked and lost tracks
        for track in self.tracked_stracks:
            track.predict()
        for track in self.lost_stracks:
            track.predict()

        # Step 2: Split detections into High-Score and Low-Score pools
        high_dets = []
        low_dets = []
        for det in detections:
            conf = det['confidence']
            if conf >= self.track_thresh:
                high_dets.append(det)
            elif conf >= 0.10:
                low_dets.append(det)

        # Step 3: First Association (High-Confidence detections with Tracked + Lost pools)
        track_pool = [t for t in self.tracked_stracks if t.state in ("NEW", "CONFIRMED", "ACTIVE", "RECOVERED")] + self.lost_stracks
        matched_1, unmatched_tracks_1, unmatched_dets_1 = self._associate(track_pool, high_dets, self.match_thresh)

        for track, det in matched_1:
            track.update(det['bbox'], det['confidence'], self.min_confirmation_frames)
            if track in self.lost_stracks:
                self.lost_stracks.remove(track)
                if track not in self.tracked_stracks:
                    self.tracked_stracks.append(track)

        # Step 4: Second Association (Unmatched tracks with Low-Confidence detections to recover occluded persons)
        remaining_tracked = [t for t in unmatched_tracks_1 if t.state in ("ACTIVE", "RECOVERED", "CONFIRMED")]
        matched_2, unmatched_tracks_2, _ = self._associate(remaining_tracked, low_dets, self.match_thresh * 0.70)

        for track, det in matched_2:
            track.update(det['bbox'], det['confidence'], self.min_confirmation_frames)

        # Step 5: Handle unmatched tracks (transition to TEMPORARILY_LOST or EXITED)
        for track in unmatched_tracks_2:
            if track.state in ("ACTIVE", "RECOVERED", "CONFIRMED"):
                track.state = "TEMPORARILY_LOST"
                if track in self.tracked_stracks:
                    self.tracked_stracks.remove(track)
                if track not in self.lost_stracks:
                    self.lost_stracks.append(track)

        # Purge tracks exceeding max lost frames
        for track in list(self.lost_stracks):
            if track.time_since_update > self.max_lost_frames:
                track.state = "EXITED"
                self.lost_stracks.remove(track)

        # Step 6: Initialize new tracks from unmatched high-confidence detections
        for det in unmatched_dets_1:
            if det['confidence'] >= self.track_thresh:
                new_track = TrackState(
                    track_id=self.next_id,
                    bbox=det['bbox'],
                    conf=det['confidence'],
                    camera_id=self.camera_id,
                    enable_kalman=self.enable_kalman,
                    smoothing_alpha=self.smoothing_alpha
                )
                self.next_id += 1
                self.tracked_stracks.append(new_track)

        # Format stabilized output for rendering and analytics
        results = []
        # Return all active tracks + confirmed tracks + temporarily lost tracks (for graceful occlusion rendering)
        render_pool = self.tracked_stracks + [t for t in self.lost_stracks if t.time_since_update <= 12]
        
        for track in render_pool:
            # Only render tracks that have reached confirmation threshold or are temporarily lost active tracks
            if track.hits >= self.min_confirmation_frames or track.state in ("ACTIVE", "TEMPORARILY_LOST", "RECOVERED"):
                results.append({
                    'track_id': track.track_id,
                    'bbox': track.smoothed_bbox,  # Smooth bounding box for display
                    'raw_bbox': track.raw_bbox,   # Raw YOLO box
                    'center': track.smoothed_center,
                    'footprint': (track.smoothed_center[0], track.smoothed_bbox[3]),
                    'confidence': round(track.conf, 3),
                    'class_id': 0,
                    'vx': round(track.velocity_x, 2),
                    'vy': round(track.velocity_y, 2),
                    'history': track.trajectory.copy(),
                    'state': track.state,
                    'time_since_update': track.time_since_update
                })

        return results

    def _associate(self, tracks: List[TrackState], detections: List[Dict[str, Any]], match_thresh: float):
        if len(tracks) == 0 or len(detections) == 0:
            return [], tracks.copy(), detections.copy()

        cost_matrix = np.zeros((len(tracks), len(detections)), dtype=np.float32)
        for i, t in enumerate(tracks):
            for j, d in enumerate(detections):
                # Calculate IoU against predicted smoothed bbox
                cost_matrix[i, j] = compute_iou(t.smoothed_bbox, d['bbox'])

        matched = []
        unmatched_tracks = set(range(len(tracks)))
        unmatched_dets = set(range(len(detections)))

        while len(unmatched_tracks) > 0 and len(unmatched_dets) > 0:
            max_idx = np.unravel_index(np.argmax(cost_matrix), cost_matrix.shape)
            i, j = max_idx[0], max_idx[1]
            best_iou = cost_matrix[i, j]

            if best_iou < match_thresh:
                break

            matched.append((tracks[i], detections[j]))
            unmatched_tracks.remove(i)
            unmatched_dets.remove(j)
            cost_matrix[i, :] = -1.0
            cost_matrix[:, j] = -1.0

        return matched, [tracks[i] for i in unmatched_tracks], [detections[j] for j in unmatched_dets]

class PersonTracker:
    """Unified Person Tracker Wrapper instantiated per Camera."""

    def __init__(self, tracker_type: str = "bytetrack", smoothing_alpha: float = 0.65,
                 enable_kalman: bool = True, min_confirmation_frames: int = 2, camera_id: str = "camera_1"):
        self.tracker_type = tracker_type
        self.byte_tracker = ByteTracker(
            track_thresh=0.25,
            match_thresh=0.20,
            max_lost_frames=50,
            smoothing_alpha=smoothing_alpha,
            enable_kalman=enable_kalman,
            min_confirmation_frames=min_confirmation_frames,
            camera_id=camera_id
        )

    def update(self, detections: List[Dict[str, Any]], model_instance=None, frame=None) -> List[Dict[str, Any]]:
        return self.byte_tracker.update(detections)
