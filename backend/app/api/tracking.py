from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
import time

try:
    from backend.app.services.camera_manager import camera_manager
except ModuleNotFoundError:
    from app.services.camera_manager import camera_manager

router = APIRouter(prefix="/api/tracking", tags=["Tracking"])

@router.get("/live")
def get_all_live_tracks():
    """Returns active ByteTrack person tracks and bounding boxes across all 4 cameras."""
    all_tracks = {}
    total_count = 0
    
    for cam_id, proc in camera_manager.processors.items():
        tracks = proc.get_active_tracks_json()
        all_tracks[cam_id] = {
            "camera_id": cam_id,
            "camera_name": proc.camera_name,
            "status": "LIVE" if proc.is_running else "STOPPED",
            "people_count": len(tracks),
            "tracks": tracks
        }
        total_count += len(tracks)

    return {
        "timestamp": time.time(),
        "total_people_detected": total_count,
        "cameras": all_tracks
    }

@router.get("/{camera_id}")
def get_camera_live_tracks(camera_id: str):
    """Returns real-time ByteTrack person tracks for a specific camera channel."""
    if camera_id not in camera_manager.processors:
        raise HTTPException(status_code=404, detail="Camera not found.")

    proc = camera_manager.processors[camera_id]
    tracks = proc.get_active_tracks_json()

    return {
        "camera_id": camera_id,
        "camera_name": proc.camera_name,
        "timestamp": time.time(),
        "people_count": len(tracks),
        "tracks": tracks
    }
