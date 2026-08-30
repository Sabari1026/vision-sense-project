import pytest
import numpy as np
from vision.reid import PersonReID

def test_reid_feature_extraction():
    reid = PersonReID(enabled=True)
    # Synthetic person crop (128x64 BGR)
    crop = np.random.randint(0, 255, (128, 64, 3), dtype=np.uint8)
    embedding = reid.extract_embedding(crop)
    assert embedding is not None
    assert isinstance(embedding, np.ndarray)
    assert len(embedding) > 0
    # Embedding must be L2-normalized
    norm = np.linalg.norm(embedding)
    assert pytest.approx(norm, 0.01) == 1.0

def test_reid_cross_camera_matching():
    reid = PersonReID(enabled=True, similarity_threshold=0.70)
    crop1 = np.ones((128, 64, 3), dtype=np.uint8) * 150 # Gray person
    
    # Register in Camera 1
    gid1 = reid.match_or_register("camera_1", local_track_id=101, person_crop=crop1)
    assert gid1 is not None
    assert gid1.startswith("G-")

    # Exact same person seen in Camera 2
    crop2 = crop1.copy()
    gid2 = reid.match_or_register("camera_2", local_track_id=202, person_crop=crop2)
    assert gid2 == gid1 # Correctly matches cross-camera identity!
