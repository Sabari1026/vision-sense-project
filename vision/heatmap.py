import cv2
import numpy as np
from typing import List, Tuple, Dict, Any, Optional

class HeatmapGenerator:
    """Customer Movement Heatmap Generator accumulating 2D trajectory positions."""

    def __init__(self, width: int = 1280, height: int = 720, decay_factor: float = 0.999):
        self.width = width
        self.height = height
        self.decay_factor = decay_factor
        self.grid = np.zeros((height, width), dtype=np.float32)
        self.points_buffer: List[Tuple[int, int]] = []

    def _ensure_dimensions(self, h: int, w: int):
        if self.grid is None or self.grid.shape != (h, w):
            if self.grid is not None and self.grid.size > 0:
                self.grid = cv2.resize(self.grid, (w, h))
            else:
                self.grid = np.zeros((h, w), dtype=np.float32)
            self.height = h
            self.width = w

    def add_point(self, center: Tuple[int, int], weight: float = 1.0, radius: int = 30):
        cx, cy = int(center[0]), int(center[1])
        if self.width <= 0 or self.height <= 0:
            return

        cx = max(0, min(self.width - 1, cx))
        cy = max(0, min(self.height - 1, cy))

        self.points_buffer.append((cx, cy))

        # Accumulate Gaussian blob around center point
        y_indices, x_indices = np.ogrid[-radius:radius+1, -radius:radius+1]
        mask = x_indices**2 + y_indices**2 <= radius**2
        gaussian_blob = np.exp(-(x_indices**2 + y_indices**2) / (2 * (radius / 2)**2)) * mask * weight

        x_min, x_max = max(0, cx - radius), min(self.width, cx + radius + 1)
        y_min, y_max = max(0, cy - radius), min(self.height, cy + radius + 1)

        g_x_min = max(0, radius - cx)
        g_x_max = radius + (x_max - cx)
        g_y_min = max(0, radius - cy)
        g_y_max = radius + (y_max - cy)

        self.grid[y_min:y_max, x_min:x_max] += gaussian_blob[g_y_min:g_y_max, g_x_min:g_x_max]

    def generate_overlay(self, frame: np.ndarray, alpha: float = 0.55) -> np.ndarray:
        """Blends current density heatmap onto camera frame."""
        if frame is None:
            return frame

        h, w = frame.shape[:2]
        self._ensure_dimensions(h, w)

        # Apply subtle decay to avoid static saturation over hours
        self.grid *= self.decay_factor

        # Normalize grid to 0-255 uint8
        max_val = np.max(self.grid)
        if max_val > 0:
            norm_grid = np.uint8(255 * (self.grid / max_val))
        else:
            norm_grid = np.zeros((h, w), dtype=np.uint8)

        # Gaussian blur for smooth thermal gradient blobs
        norm_grid = cv2.GaussianBlur(norm_grid, (15, 15), 0)

        # Apply Jet Color Map (blue = low, red = high traffic)
        color_map = cv2.applyColorMap(norm_grid, cv2.COLORMAP_JET)

        # Zero out background (where density is low) to preserve underlying camera view
        mask = norm_grid < 10
        color_map[mask] = [0, 0, 0]

        if color_map.shape[:2] != (h, w):
            color_map = cv2.resize(color_map, (w, h))

        # Blend with original frame
        blended = cv2.addWeighted(frame, 1.0 - alpha, color_map, alpha, 0)
        return blended

    def get_points_and_clear(self) -> List[Tuple[int, int]]:
        pts = self.points_buffer.copy()
        self.points_buffer.clear()
        return pts
