import os
import shutil
from fastapi import APIRouter, HTTPException, UploadFile, File, Response
from typing import List, Dict, Any
try:
    from backend.app.services.camera_manager import camera_manager
    from backend.app.services.supabase_client import db_service
except ModuleNotFoundError:
    from app.services.camera_manager import camera_manager
    from app.services.supabase_client import db_service

router = APIRouter(prefix="/api/cameras", tags=["Cameras"])

@router.get("", response_model=List[Dict[str, Any]])
def list_cameras():
    """Get all configured cameras and their real-time operational status."""
    return camera_manager.get_all_stats()

@router.post("/{camera_id}/start")
def start_camera_feed(camera_id: str):
    """Start Vision worker for a specific CCTV camera."""
    success = camera_manager.start_camera(camera_id)
    if not success:
        raise HTTPException(status_code=400, detail="Could not start camera processing.")
    return {"status": "success", "camera_id": camera_id, "state": "LIVE"}

@router.post("/{camera_id}/stop")
def stop_camera_feed(camera_id: str):
    """Stop Vision worker for a specific camera."""
    camera_manager.stop_camera(camera_id)
    return {"status": "success", "camera_id": camera_id, "state": "STOPPED"}

@router.get("/{camera_id}/frame")
def get_camera_frame(camera_id: str):
    """Retrieve the latest annotated camera frame as JPEG image binary."""
    jpeg_bytes = camera_manager.get_latest_frame_jpeg(camera_id)
    if jpeg_bytes is None:
        # Return a black placeholder image if frame is not ready
        import cv2
        import numpy as np
        img = np.zeros((360, 640, 3), dtype=np.uint8)
        cv2.putText(img, "STREAM OFFLINE / INITIALIZING", (80, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 200), 2)
        _, jpeg = cv2.imencode('.jpg', img)
        return Response(content=jpeg.tobytes(), media_type="image/jpeg")

    return Response(content=jpeg_bytes, media_type="image/jpeg")

from fastapi.responses import StreamingResponse
import time

def generate_mjpeg_stream(camera_id: str):
    while True:
        jpeg_bytes = camera_manager.get_latest_frame_jpeg(camera_id)
        if jpeg_bytes:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n')
        time.sleep(0.033) # Smooth ~30 FPS stream pushing

@router.get("/{camera_id}/stream")
def stream_camera_feed(camera_id: str):
    """Stream live CCTV video as continuous smooth MJPEG multipart binary stream."""
    return StreamingResponse(
        generate_mjpeg_stream(camera_id),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.get("/{camera_id}/zones")
def get_camera_zones(camera_id: str):
    """Retrieve polygon zones for a camera."""
    return db_service.get_zones(camera_id)

@router.post("/upload")
async def upload_video(file: UploadFile = File(...), camera_id: str = "11111111-1111-1111-1111-111111111111"):
    """Upload a custom CCTV video file to /videos directory."""
    if not file.filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
        raise HTTPException(status_code=400, detail="Unsupported video format.")

    videos_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "videos"))
    os.makedirs(videos_dir, exist_ok=True)
    target_path = os.path.join(videos_dir, file.filename)

    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"status": "success", "filename": file.filename, "path": target_path}
