import os
import sys
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from vision.processor import CameraStreamProcessor

def test_pipeline():
    print("==========================================================")
    print(" Running VisionSense End-to-End Pipeline Verification Test ")
    print("==========================================================")

    # Step 1: Ensure sample videos exist
    videos_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "videos"))
    os.makedirs(videos_dir, exist_ok=True)
    video_path = os.path.join(videos_dir, "camera1.mp4")

    if not os.path.exists(video_path):
        print("Generating synthetic demo CCTV video for testing...")
        from scripts.generate_sample_videos import create_cctv_video
        create_cctv_video(video_path, "CAM-01 TEST")

    # Step 2: Initialize Stream Processor
    config = {
        'YOLO_MODEL': 'yolov8n.pt',
        'USE_GPU': False,
        'vision': {'confidence': 0.35, 'tracker': 'bytetrack', 'lost_timeout_seconds': 5}
    }

    processor = CameraStreamProcessor(
        camera_id="11111111-1111-1111-1111-111111111111",
        camera_name="Test Camera 01",
        source_path=video_path,
        config=config
    )

    opened = processor.initialize()
    assert opened, "Failed to open video source!"
    print("Video source initialized successfully.")

    # Step 3: Process 30 Frames
    print("Processing 30 consecutive frames...")
    for frame_idx in range(30):
        success, frame, stats = processor.process_next_frame(enable_heatmap_overlay=True)
        assert success, f"Frame processing failed at frame {frame_idx}"
        assert frame is not None, "Annotated frame was None"
        print(f"  Frame {frame_idx + 1:02d}/30 | FPS: {stats['fps']} | People: {stats['people_count']} | Entries: {stats['entries']} | Dwell: {stats['avg_dwell_seconds']}s")

    processor.stop()
    print("==========================================================")
    print(" SUCCESS: VisionSense Computer Vision Pipeline Test Passed ")
    print("==========================================================")

if __name__ == "__main__":
    test_pipeline()
