import cv2
import numpy as np
from typing import List, Dict, Any, Tuple, Optional

class ZoneManager:
    """Manages Polygon Zones and Entry/Exit Line Crossing detection."""

    def __init__(self, camera_id: str):
        self.camera_id = camera_id
        self.zones: List[Dict[str, Any]] = [] # [{'id': str, 'name': str, 'polygon': np.ndarray}]
        self.entry_line: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None
        self.track_positions: Dict[int, List[Tuple[int, int]]] = {} # track_id -> history of centers

        # Set default line near bottom of camera frame if unconfigured
        self.set_entry_line((100, 620), (1180, 620))

    def add_zone(self, zone_id: str, name: str, polygon_coords: List[List[int]], zone_type: str = "polygon"):
        pts = np.array(polygon_coords, dtype=np.int32)
        self.zones.append({
            'id': zone_id,
            'name': name,
            'polygon': pts,
            'zone_type': zone_type
        })

    def set_entry_line(self, p1: Tuple[int, int], p2: Tuple[int, int]):
        self.entry_line = (p1, p2)

    def check_zone_containment(self, center: Tuple[int, int]) -> Optional[Dict[str, Any]]:
        """Returns the zone dict if the center point (cx, cy) is inside any defined polygon zone."""
        for zone in self.zones:
            if zone['zone_type'] == "polygon" and len(zone['polygon']) >= 3:
                dist = cv2.pointPolygonTest(zone['polygon'], (float(center[0]), float(center[1])), False)
                if dist >= 0:
                    return zone
        return None

    def update_track_positions(self, track_id: int, center: Tuple[int, int]) -> Tuple[bool, bool]:
        """
        Updates center position history for line crossing detection.
        Returns: (is_entry, is_exit)
        """
        if track_id not in self.track_positions:
            self.track_positions[track_id] = []

        self.track_positions[track_id].append(center)
        # Keep last 10 points
        if len(self.track_positions[track_id]) > 10:
            self.track_positions[track_id].pop(0)

        is_entry = False
        is_exit = False

        if self.entry_line is not None and len(self.track_positions[track_id]) >= 2:
            p1, p2 = self.entry_line
            prev_pt = self.track_positions[track_id][-2]
            curr_pt = self.track_positions[track_id][-1]

            # Vector cross product side test
            def side(line_p1, line_p2, pt):
                return (line_p2[0] - line_p1[0]) * (pt[1] - line_p1[1]) - (line_p2[1] - line_p1[1]) * (pt[0] - line_p1[0])

            prev_side = side(p1, p2, prev_pt)
            curr_side = side(p1, p2, curr_pt)

            # Check if line was crossed in current frame
            if prev_side < 0 and curr_side >= 0:
                is_entry = True
            elif prev_side > 0 and curr_side <= 0:
                is_exit = True

        return is_entry, is_exit

    def draw_zones(self, frame: np.ndarray) -> np.ndarray:
        """Draws zone polygons and entry line overlays on the video frame."""
        for zone in self.zones:
            pts = zone['polygon']
            if len(pts) >= 3:
                # Semi-transparent overlay polygon fill
                overlay = frame.copy()
                cv2.fillPoly(overlay, [pts], (255, 140, 0)) # Cyan/Blue-Orange
                cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)
                cv2.polylines(frame, [pts], True, (255, 165, 0), 2)

                # Label zone name
                M = cv2.moments(pts)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    cv2.putText(frame, zone['name'], (cX - 40, cY), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Draw Entry / Exit Line
        if self.entry_line:
            p1, p2 = self.entry_line
            cv2.line(frame, p1, p2, (0, 255, 255), 3) # Bright yellow
            cv2.putText(frame, "ENTRY / EXIT LINE", (p1[0] + 10, p1[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

        return frame
