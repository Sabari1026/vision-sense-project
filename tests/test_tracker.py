import pytest
from vision.tracker import ByteTracker, PersonTracker, compute_iou

def test_compute_iou():
    box1 = (100, 100, 200, 200)
    box2 = (100, 100, 200, 200)
    assert compute_iou(box1, box2) == 1.0

    box3 = (300, 300, 400, 400)
    assert compute_iou(box1, box3) == 0.0

    box4 = (150, 100, 250, 200) # 50% overlap
    iou = compute_iou(box1, box4)
    assert 0.3 < iou < 0.4

def test_bytetrack_association():
    tracker = ByteTracker(track_thresh=0.35, match_thresh=0.25, max_lost_frames=30)
    
    # Frame 1: Detection of person
    dets_frame1 = [
        {'bbox': (100, 100, 180, 300), 'confidence': 0.85, 'class_id': 0, 'center': (140, 200)}
    ]
    tracks1 = tracker.update(dets_frame1)
    assert len(tracks1) == 1
    t1_id = tracks1[0]['track_id']
    assert t1_id == 101

    # Frame 2: Slight movement (high confidence)
    dets_frame2 = [
        {'bbox': (105, 102, 185, 302), 'confidence': 0.88, 'class_id': 0, 'center': (145, 202)}
    ]
    tracks2 = tracker.update(dets_frame2)
    assert len(tracks2) == 1
    assert tracks2[0]['track_id'] == t1_id # Preserves identical Track ID

    # Frame 3: Occlusion / low-confidence detection (Stage 2 association)
    dets_frame3 = [
        {'bbox': (110, 105, 190, 305), 'confidence': 0.20, 'class_id': 0, 'center': (150, 205)}
    ]
    tracks3 = tracker.update(dets_frame3)
    assert len(tracks3) == 1
    assert tracks3[0]['track_id'] == t1_id # Recovered via Stage 2

def test_person_tracker_wrapper():
    pt = PersonTracker()
    dets = [
        {'bbox': (200, 200, 280, 400), 'confidence': 0.90, 'class_id': 0, 'center': (240, 300)},
        {'bbox': (400, 200, 480, 400), 'confidence': 0.92, 'class_id': 0, 'center': (440, 300)}
    ]
    tracks = pt.update(dets)
    assert len(tracks) == 2
    assert tracks[0]['track_id'] != tracks[1]['track_id']
