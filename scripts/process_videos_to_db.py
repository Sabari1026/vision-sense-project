import os
import sys
import time
import cv2
import uuid
from typing import Dict, Any, List

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from vision.processor import CameraStreamProcessor
from backend.app.services.supabase_client import db_service

def log(msg=""):
    print(msg, flush=True)

def process_all_videos():
    log("==================================================================")
    log(" VisionSense Video Batch Processing & Database Persistence System ")
    log("==================================================================")

    videos_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "videos"))
    if not os.path.exists(videos_dir):
        print(f"Error: Videos directory not found at {videos_dir}")
        return

    mp4_files = sorted([f for f in os.listdir(videos_dir) if f.endswith('.mp4')])
    if not mp4_files:
        print(f"No MP4 video files found in {videos_dir}")
        return

    log(f"Found {len(mp4_files)} video file(s) in '{videos_dir}':")
    for idx, fname in enumerate(mp4_files, 1):
        log(f"  {idx}. {fname}")
    log("------------------------------------------------------------------")

    # Use yolo11n.pt for ultra-fast, high-accuracy CPU processing
    yolo_model = "yolo11n.pt"
    frame_stride = 2 # Process every 2nd frame for 2x speedup while maintaining track continuity
    log(f"Using Detection Model: {yolo_model} (Frame Stride: {frame_stride})")

    summary_results = []

    for idx, fname in enumerate(mp4_files, 1):
        video_path = os.path.join(videos_dir, fname)
        cam_id = f"{idx}{idx}{idx}{idx}{idx}{idx}{idx}{idx}-{idx}{idx}{idx}{idx}-{idx}{idx}{idx}{idx}-{idx}{idx}{idx}{idx}-{idx}{idx}{idx}{idx}{idx}{idx}{idx}{idx}{idx}{idx}{idx}{idx}"
        
        if "USA #2" in fname:
            cam_name = "Camera 01 - USA Retail Store #2"
            location = "Main Entrance & Floor"
        elif "HDCCTVCameras" in fname or "HD CCTV" in fname:
            cam_name = "Camera 02 - HD CCTV Retail Store"
            location = "Clothing & Display Aisles"
        else:
            cam_name = f"Camera 0{idx} - {os.path.splitext(fname)[0][:20]}"
            location = f"Location 0{idx}"

        # Get video metadata
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        resolution_str = f"{w}x{h}"
        cap.release()

        log(f"\n[Processing {idx}/{len(mp4_files)}] {cam_name}")
        log(f"  File: {fname}")
        log(f"  Resolution: {resolution_str} | FPS: {fps:.2f} | Total Frames: {total_frames}")

        # Register camera in DB
        camera_record = {
            "id": cam_id,
            "name": cam_name,
            "location": location,
            "source_type": "file",
            "source_path": os.path.join("videos", fname),
            "status": "PROCESSED",
            "resolution": resolution_str,
            "fps": int(fps)
        }
        db_service.upsert_camera(camera_record)

        # Configure processor
        config = {
            'YOLO_MODEL': yolo_model,
            'USE_GPU': False,
            'vision': {
                'confidence': 0.35,
                'tracker': 'bytetrack',
                'lost_timeout_seconds': 5.0
            },
            'analytics': {
                'heatmap_sampling_seconds': 1.0
            },
            'age_estimation': {
                'enabled': True
            }
        }

        processor = CameraStreamProcessor(
            camera_id=cam_id,
            camera_name=cam_name,
            source_path=video_path,
            config=config,
            loop=False
        )

        if not processor.initialize():
            log(f"  Error: Could not open video file: {video_path}")
            continue

        frame_count = 0
        processed_count = 0
        start_time = time.time()
        video_start_timestamp = time.time()

        snapshots_to_save = []

        log("  Processing frames & detecting people...")
        while True:
            # Handle frame stride
            for _ in range(frame_stride - 1):
                processor.source.cap.grab() if processor.source.cap else None
                frame_count += 1

            success, frame, stats = processor.process_next_frame(enable_heatmap_overlay=False)
            if not success:
                break
            
            frame_count += 1
            processed_count += 1
            current_sec = video_start_timestamp + (frame_count / fps)

            # Record periodic snapshot every ~5 seconds of video
            if processed_count % int(max(1, (fps / frame_stride) * 5)) == 0:
                snapshots_to_save.append({
                    "id": str(uuid.uuid4()),
                    "camera_id": cam_id,
                    "timestamp": current_sec,
                    "people_count": stats['people_count'],
                    "entries": stats['entries'],
                    "exits": stats['exits'],
                    "occupancy": stats['occupancy'],
                    "average_dwell_seconds": stats['avg_dwell_seconds'],
                    "total_visitors": stats['total_visitors']
                })

            if processed_count % 20 == 0 or frame_count >= total_frames:
                pct = min(100.0, (frame_count / total_frames) * 100) if total_frames > 0 else 0
                log(f"    Frame {frame_count}/{total_frames} ({pct:.1f}%) | Active People: {stats['people_count']} | Entries: {stats['entries']} | Exits: {stats['exits']} | Total Visitors: {stats['total_visitors']}")

        final_video_time = video_start_timestamp + (frame_count / fps)
        final_data = processor.finalize(final_video_time)
        processor.stop()

        elapsed = time.time() - start_time
        proc_fps = frame_count / max(elapsed, 0.001)

        # Flush all collected analytics to Database
        sessions = final_data['visitor_sessions']
        events = final_data['detection_events']
        heatmaps = final_data['heatmap_points']
        zone_visits = final_data['zone_visits']
        total_visitors = final_data['total_visitors']

        db_service.save_visitor_sessions(sessions)
        db_service.save_detection_events(events)
        db_service.save_heatmap_points(heatmaps)
        db_service.save_zone_visits(zone_visits)
        if snapshots_to_save:
            db_service.save_analytics_snapshots(snapshots_to_save)

        log(f"  Completed processing in {elapsed:.2f}s ({proc_fps:.1f} FPS processing speed)")
        log(f"  --> DB Records Saved for {cam_name}:")
        log(f"      - Visitor Sessions: {len(sessions)}")
        log(f"      - Frame Detection Events: {len(events)}")
        log(f"      - Heatmap Density Points: {len(heatmaps)}")
        log(f"      - Zone Visits: {len(zone_visits)}")
        log(f"      - Analytics Snapshots: {len(snapshots_to_save)}")

        summary_results.append({
            "camera_name": cam_name,
            "video_file": fname,
            "frames_processed": frame_count,
            "total_visitors": total_visitors,
            "sessions_saved": len(sessions),
            "detection_events_saved": len(events),
            "heatmap_points_saved": len(heatmaps),
            "avg_dwell_seconds": round(sum(s.get('dwell_seconds', 0) for s in sessions) / max(1, len(sessions)), 1)
        })

    log("\n==================================================================")
    log(" SUMMARY OF PERSON DETECTION & DATABASE PERSISTENCE ")
    log("==================================================================")
    for res in summary_results:
        log(f"Camera: {res['camera_name']}")
        log(f"  Video File:            {res['video_file']}")
        log(f"  Frames Processed:      {res['frames_processed']}")
        log(f"  Total People Detected: {res['total_visitors']}")
        log(f"  Average Dwell Time:    {res['avg_dwell_seconds']} seconds")
        log(f"  DB Visitor Sessions:   {res['sessions_saved']}")
        log(f"  DB Detection Events:   {res['detection_events_saved']}")
        log(f"  DB Heatmap Points:     {res['heatmap_points_saved']}")
        log("------------------------------------------------------------------")

if __name__ == "__main__":
    process_all_videos()
