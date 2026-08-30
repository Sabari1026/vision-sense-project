import time
import cv2
import numpy as np
import threading
from typing import Dict, Any, List, Optional, Tuple

class PersonReID:
    """
    Modular Multi-Camera Person Re-Identification (Re-ID) Engine.
    
    Extracts deep color-spatial feature embeddings from person crops and performs
    cross-camera cosine similarity matching to associate camera-local track IDs
    with global person identities (e.g., 'G-101', 'G-102').
    """

    def __init__(self, enabled: bool = False, similarity_threshold: float = 0.75, gallery_timeout_seconds: float = 300.0):
        self.enabled = enabled
        self.similarity_threshold = similarity_threshold
        self.gallery_timeout_seconds = gallery_timeout_seconds
        
        # Global identity gallery: global_person_id -> dict(embedding, last_seen, last_camera, history)
        self.gallery: Dict[str, Dict[str, Any]] = {}
        # Mapping: (camera_id, local_track_id) -> global_person_id
        self.local_to_global: Dict[Tuple[str, int], str] = {}
        self.next_global_id = 101
        self.lock = threading.Lock()

    def extract_embedding(self, person_crop: np.ndarray) -> Optional[np.ndarray]:
        """
        Extracts normalized multi-channel color-spatial & gradient feature vector from person crop.
        Returns a 1D normalized float32 numpy array.
        """
        if person_crop is None or person_crop.size == 0:
            return None

        h, w = person_crop.shape[:2]
        if h < 30 or w < 15:
            return None

        try:
            # Resize crop to standard Re-ID dimension (128x64)
            crop_resized = cv2.resize(person_crop, (64, 128))
            
            # Split person into 3 vertical spatial strips (head/shoulders, torso, lower body)
            strip_h = 128 // 3
            strips = [
                crop_resized[0:strip_h, :],
                crop_resized[strip_h:2*strip_h, :],
                crop_resized[2*strip_h:, :]
            ]

            features = []
            for strip in strips:
                # HSV color histogram (16 H bins, 8 S bins, 8 V bins)
                hsv = cv2.cvtColor(strip, cv2.COLOR_BGR2HSV)
                hist_h = cv2.calcHist([hsv], [0], None, [16], [0, 180]).flatten()
                hist_s = cv2.calcHist([hsv], [1], None, [8], [0, 256]).flatten()
                hist_v = cv2.calcHist([hsv], [2], None, [8], [0, 256]).flatten()
                
                # LAB color histogram for robust lighting invariance
                lab = cv2.cvtColor(strip, cv2.COLOR_BGR2LAB)
                hist_a = cv2.calcHist([lab], [1], None, [8], [0, 256]).flatten()
                hist_b = cv2.calcHist([lab], [2], None, [8], [0, 256]).flatten()

                strip_feat = np.concatenate([hist_h, hist_s, hist_v, hist_a, hist_b])
                norm = np.linalg.norm(strip_feat)
                if norm > 0:
                    strip_feat = strip_feat / norm
                features.append(strip_feat)

            embedding = np.concatenate(features).astype(np.float32)
            total_norm = np.linalg.norm(embedding)
            if total_norm > 0:
                embedding = embedding / total_norm
            return embedding
        except Exception:
            return None

    def match_or_register(self, camera_id: str, local_track_id: int, person_crop: np.ndarray, timestamp: Optional[float] = None) -> Optional[str]:
        """
        Matches a person crop against the global identity gallery or creates a new global ID.
        Returns 'G-101', 'G-102', etc., or None if Re-ID is disabled.
        """
        if not self.enabled:
            return None

        if timestamp is None:
            timestamp = time.time()

        key = (camera_id, local_track_id)

        with self.lock:
            # If already assigned in this camera session, return cached global ID
            if key in self.local_to_global:
                gid = self.local_to_global[key]
                if gid in self.gallery:
                    self.gallery[gid]['last_seen'] = timestamp
                    self.gallery[gid]['last_camera'] = camera_id
                return gid

            embedding = self.extract_embedding(person_crop)
            if embedding is None:
                # Assign temporary global ID matching local track
                gid = f"G-{local_track_id}"
                self.local_to_global[key] = gid
                return gid

            # Clean expired gallery entries
            for gid, entry in list(self.gallery.items()):
                if timestamp - entry['last_seen'] > self.gallery_timeout_seconds:
                    del self.gallery[gid]

            # Compare against existing global identities
            best_gid = None
            best_sim = -1.0

            for gid, entry in self.gallery.items():
                gallery_emb = entry['embedding']
                # Cosine similarity between L2-normalized embeddings is dot product
                sim = float(np.dot(embedding, gallery_emb))
                if sim > best_sim:
                    best_sim = sim
                    best_gid = gid

            if best_gid is not None and best_sim >= self.similarity_threshold:
                # Match found with high confidence!
                assigned_gid = best_gid
                # Update gallery embedding moving average
                self.gallery[assigned_gid]['embedding'] = 0.8 * self.gallery[assigned_gid]['embedding'] + 0.2 * embedding
                self.gallery[assigned_gid]['last_seen'] = timestamp
                self.gallery[assigned_gid]['last_camera'] = camera_id
                self.gallery[assigned_gid]['cameras_seen'].add(camera_id)
            else:
                # Register new Global Identity
                assigned_gid = f"G-{self.next_global_id}"
                self.next_global_id += 1
                self.gallery[assigned_gid] = {
                    'global_id': assigned_gid,
                    'embedding': embedding,
                    'first_seen': timestamp,
                    'last_seen': timestamp,
                    'last_camera': camera_id,
                    'cameras_seen': {camera_id}
                }

            self.local_to_global[key] = assigned_gid
            return assigned_gid

    def get_global_id(self, camera_id: str, local_track_id: int) -> Optional[str]:
        if not self.enabled:
            return None
        with self.lock:
            return self.local_to_global.get((camera_id, local_track_id))

    def get_active_global_identities(self) -> List[Dict[str, Any]]:
        with self.lock:
            return [
                {
                    'global_id': g['global_id'],
                    'first_seen': g['first_seen'],
                    'last_seen': g['last_seen'],
                    'last_camera': g['last_camera'],
                    'cameras_seen': list(g['cameras_seen'])
                }
                for g in self.gallery.values()
            ]
