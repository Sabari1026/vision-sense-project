import pytest
from vision.zone_manager import ZoneManager, line_intersect

def test_line_segment_intersection():
    # Crossing lines
    A, B = (0, 0), (10, 10)
    C, D = (0, 10), (10, 0)
    assert line_intersect(A, B, C, D) is True

    # Parallel non-intersecting lines
    E, F = (0, 0), (10, 0)
    G, H = (0, 5), (10, 5)
    assert line_intersect(E, F, G, H) is False

def test_entry_exit_line_crossing():
    zm = ZoneManager(camera_id="cam-test")
    zm.set_entry_line((100, 300), (500, 300))

    # Person walking downward crossing the line (from (300, 280) to (300, 320))
    entry1, exit1 = zm.update_track_positions(101, (300, 280))
    assert entry1 is False and exit1 is False

    entry2, exit2 = zm.update_track_positions(101, (300, 320))
    assert (entry2 is True or exit2 is True)

    # Debounce test: immediate consecutive crossing should be debounced
    entry3, exit3 = zm.update_track_positions(101, (300, 315))
    assert entry3 is False and exit3 is False
