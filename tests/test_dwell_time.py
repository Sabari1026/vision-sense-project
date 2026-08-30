import pytest
import time
from vision.dwell_time import DwellTimeManager

def test_dwell_time_tracking():
    dtm = DwellTimeManager(camera_id="cam-dwell-test", lost_timeout_seconds=2.0)
    
    t0 = time.time()
    session = dtm.update_track(101, t0, zone_info={"id": "z1", "name": "Entrance"}, age_group="Adult", age_conf=0.88)
    assert session['anonymous_track_id'] == 101
    assert session['dwell_seconds'] == 0

    # Simulate 5 seconds dwell
    t1 = t0 + 5.0
    session_updated = dtm.update_track(101, t1, zone_info={"id": "z1", "name": "Entrance"})
    assert session_updated['dwell_seconds'] == 5

    # Simulate person lost longer than timeout (3 seconds later)
    t2 = t1 + 3.0
    closed = dtm.cleanup_lost_tracks(t2)
    assert len(closed) == 1
    assert closed[0]['anonymous_track_id'] == 101
    assert closed[0]['dwell_seconds'] == 5
