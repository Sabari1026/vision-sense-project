import pytest
import numpy as np
from vision.heatmap import HeatmapGenerator

def test_heatmap_point_accumulation():
    hm = HeatmapGenerator(width=640, height=360)
    assert np.max(hm.grid) == 0.0

    # Add points
    hm.add_point((320, 180), weight=1.0)
    hm.add_point((320, 180), weight=1.0)
    
    assert np.max(hm.grid) > 0.0

def test_heatmap_overlay_blending():
    hm = HeatmapGenerator(width=640, height=360)
    hm.add_point((320, 180), weight=2.0)
    
    dummy_frame = np.ones((360, 640, 3), dtype=np.uint8) * 100
    blended = hm.generate_overlay(dummy_frame, alpha=0.5)
    assert blended is not None
    assert blended.shape == (360, 640, 3)
