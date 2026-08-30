import cv2
import time
import numpy as np
from typing import List, Dict, Any, Tuple, Optional

def ccw(A: Tuple[int, int], B: Tuple[int, int], C: Tuple[int, int]) -> bool:
    """Checks if three points are listed in counter-clockwise order."""
    return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

def line_intersect(A: Tuple[int, int], B: Tuple[int, int], C: Tuple[int, int], D: Tuple[int, int]) -> bool:
    """Returns True if line segment AB intersects line segment CD."""
    return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)

class ZoneManager:
    """
    Manages Interactive Polygon Zones, Ground Footprint Containment,
    and Bidirectional Virtual Entry/Exit Line Crossings with Debounce Filtering.
    """

    def __init__(self, camera_id: str):
        self.camera_id = camera_id
        self.zones: List[Dict[str, Any]] = []
        self.entry_line: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None
        self.exit_line: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None
        
        # Tracking history for line crossing: track_id -> list of footprint points
        self.track_positions: Dict[int, List[Tuple[int, int]]] = {}
        # Debounce: track_id -> timestamp of last crossing
        self.last_crossing_time: Dict[int, float] = {}

        # Default virtual line across lower third of frame
        self.set_entry_line((80, 580), (1200, 580))
        self._load_zones_from_db()

    def _load_zones_from_db(self):
        try:
            from backend.app.services.supabase_client import db_service
            db_zones = db_service.get_zones(self.camera_id)
            for z in db_zones:
                poly = z.get('polygon')
                if poly and len(poly) >= 3:
                    self.add_zone(
                        zone_id=z.get('id', z.get('zone_id', 'zone-1')),
                        name=z.get('name', 'Zone'),
                        polygon_coords=poly
                    )
        except Exception:
            pass

    def add_zone(self, zone_id: str, name: str, polygon_coords: List[List[int]], zone_type: str = "polygon"):
        pts = np.array(polygon_coords, dtype=np.int32)
        # Avoid duplicates
        self.zones = [z for z in self.zones if z['id'] != zone_id]
        self.zones.append({
            'id': zone_id,
            'name': name,
            'polygon': pts,
            'zone_type': zone_type
        })

    def set_entry_line(self, p1: Tuple[int, int], p2: Tuple[int, int]):
        self.entry_line = (p1, p2)

    def set_exit_line(self, p1: Tuple[int, int], p2: Tuple[int, int]):
        self.exit_line = (p1, p2)

    def check_zone_containment(self, footprint: Tuple[int, int]) -> Optional[Dict[str, Any]]:
        """
        Determines which polygon zone contains the person's ground footprint (cx, y2).
        Returns the zone dict or None.
        """
        for zone in self.zones:
            if zone['zone_type'] == "polygon" and len(zone['polygon']) >= 3:
                dist = cv2.pointPolygonTest(zone['polygon'], (float(footprint[0]), float(footprint[1])), False)
                if dist >= 0:
                    return zone
        return None

    def update_track_positions(self, track_id: int, footprint: Tuple[int, int]) -> Tuple[bool, bool]:
        """
        Tests whether the person's trajectory crossed configured entry or exit lines.
        Includes 2.0 second debounce per track ID to prevent duplicate counts.
        Returns: (is_entry, is_exit)
        """
        if track_id not in self.track_positions:
            self.track_positions[track_id] = []

        self.track_positions[track_id].append(footprint)
        if len(self.track_positions[track_id]) > 15:
            self.track_positions[track_id].pop(0)

        is_entry = False
        is_exit = False
        now = time.time()

        if len(self.track_positions[track_id]) >= 2:
            prev_pt = self.track_positions[track_id][-2]
            curr_pt = self.track_positions[track_id][-1]

            # Test Entry Line
            if self.entry_line:
                lp1, lp2 = self.entry_line
                if line_intersect(prev_pt, curr_pt, lp1, lp2):
                    # Check debounce
                    last_cross = self.last_crossing_time.get(track_id, 0.0)
                    if now - last_cross > 2.0:
                        # Vector direction determines entry vs exit
                        # Cross product of line vector and movement vector
                        line_vec = (lp2[0] - lp1[0], lp2[1] - lp1[1])
                        move_vec = (curr_pt[0] - prev_pt[0], curr_pt[1] - prev_pt[1])
                        cross = line_vec[0] * move_vec[1] - line_vec[1] * move_vec[0]
                        
                        if cross > 0:
                            is_entry = True
                        else:
                            is_exit = True
                        self.last_crossing_time[track_id] = now

        return is_entry, is_exit

    def draw_zones(self, frame: np.ndarray) -> np.ndarray:
        """Draws glowing zones and entry/exit virtual lines on frame."""
        h, w = frame.shape[:2]
        
        # Draw Polygon Zones
        for zone in self.zones:
            pts = zone['polygon']
            if len(pts) >= 3:
                # Scale coordinates if frame dimensions differ
                overlay = frame.copy()
                cv2.fillPoly(overlay, [pts], (240, 160, 20))
                cv2.addWeighted(overlay, 0.25, frame, 0.75, 0, frame)
                cv2.polylines(frame, [pts], True, (255, 180, 0), 2, cv2.LINE_AA)

                # Label zone name
                M = cv2.moments(pts)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    cv2.rectangle(frame, (cX - 45, cY - 14), (cX + 45, cY + 8), (15, 23, 42), -1)
                    cv2.putText(frame, zone['name'], (cX - 40, cY), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 220, 255), 1, cv2.LINE_AA)

        # Draw Entry / Exit Line
        if self.entry_line:
            p1, p2 = self.entry_line
            cv2.line(frame, p1, p2, (0, 255, 255), 3, cv2.LINE_AA)
            cv2.rectangle(frame, (p1[0] + 5, p1[1] - 22), (p1[0] + 165, p1[1] - 4), (15, 23, 42), -1)
            cv2.putText(frame, "ENTRY / EXIT LINE", (p1[0] + 10, p1[1] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA)

        return frame
