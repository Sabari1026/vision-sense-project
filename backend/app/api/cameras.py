import os
import shutil
import time
import uuid
import cv2
import numpy as np
from fastapi import APIRouter, HTTPException, UploadFile, File, Response, Body
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional

try:
    from backend.app.services.camera_manager import camera_manager
    from backend.app.services.supabase_client import db_service
    from vision.processor import CameraStreamProcessor
except ModuleNotFoundError:
    from app.services.camera_manager import camera_manager
    from app.services.supabase_client import db_service
    from vision.processor import CameraStreamProcessor

router = APIRouter(prefix="/api/cameras", tags=["Cameras"])

@router.get("", response_model=List[Dict[str, Any]])
def list_cameras():
    """Get all configured cameras and their real-time operational status and metrics."""
    return camera_manager.get_all_stats()

@router.get("/{camera_id}")
def get_camera(camera_id: str):
    """Retrieve details and operational status for a single camera."""
    stats = next((s for s in camera_manager.get_all_stats() if s['camera_id'] == camera_id), None)
    if not stats:
        raise HTTPException(status_code=404, detail="Camera not found.")
    return stats

@router.get("/{camera_id}/status")
def get_camera_status(camera_id: str):
    """Retrieve online status, FPS, and person count for a single camera."""
    if camera_id not in camera_manager.processors:
        raise HTTPException(status_code=404, detail="Camera not found.")
    proc = camera_manager.processors[camera_id]
    return {
        "camera_id": camera_id,
        "name": proc.camera_name,
        "status": "ONLINE" if proc.is_running else "OFFLINE",
        "fps": proc.current_fps,
        "people_count": proc.people_count,
        "source": proc.source_path
    }

@router.post("")
def add_camera(payload: Dict[str, Any] = Body(...)):
    """Add a new camera source (RTSP, Webcam index 0/1/2, or MP4 video file)."""
    cam_id = payload.get('id', str(uuid.uuid4()))
    name = payload.get('name', 'New Camera')
    source = payload.get('source') or payload.get('source_path', '')
    location = payload.get('location', 'Store Floor')

    if not source:
        raise HTTPException(status_code=400, detail="Camera source is required.")

    # Save to Supabase / SQLite
    db_service.upsert_camera({
        'id': cam_id,
        'name': name,
        'location': location,
        'source_path': source,
        'status': 'LIVE'
    })

    # Instantiate Processor
    proc = CameraStreamProcessor(
        camera_id=cam_id,
        camera_name=name,
        source_path=source,
        config=camera_manager.config,
        shared_detector=camera_manager.shared_detector,
        shared_reid=camera_manager.shared_reid
    )
    camera_manager.processors[cam_id] = proc
    camera_manager.start_camera(cam_id)

    return {"status": "success", "camera_id": cam_id, "name": name}

@router.put("/{camera_id}")
def update_camera(camera_id: str, payload: Dict[str, Any] = Body(...)):
    """Update camera configuration (Name, Source, Location)."""
    if camera_id not in camera_manager.processors:
        raise HTTPException(status_code=404, detail="Camera not found.")

    name = payload.get('name')
    source = payload.get('source') or payload.get('source_path')
    location = payload.get('location')

    proc = camera_manager.processors[camera_id]
    if name:
        proc.camera_name = name
    if source and source != proc.source_path:
        proc.stop()
        proc.source_path = source
        from vision.source import FileCameraSource, RTSPCameraSource, WebCameraSource
        if str(source).isdigit():
            proc.source = WebCameraSource(int(source), name=proc.camera_name)
        elif str(source).startswith('rtsp://'):
            proc.source = RTSPCameraSource(str(source), name=proc.camera_name)
        else:
            proc.source = FileCameraSource(str(source), name=proc.camera_name, loop=True)
        proc.start()

    db_service.upsert_camera({
        'id': camera_id,
        'name': proc.camera_name,
        'source_path': proc.source_path,
        'location': location or 'Store Floor',
        'status': 'LIVE' if proc.is_running else 'STOPPED'
    })

    return {"status": "success", "camera_id": camera_id}

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
    """Retrieve the latest annotated camera frame as JPEG binary snapshot."""
    jpeg_bytes = camera_manager.get_latest_frame_jpeg(camera_id)
    if jpeg_bytes is None:
        img = np.zeros((360, 640, 3), dtype=np.uint8)
        cv2.putText(img, "CAMERA OFFLINE / CONNECTING", (70, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 220, 255), 2)
        _, jpeg = cv2.imencode('.jpg', img)
        return Response(content=jpeg.tobytes(), media_type="image/jpeg")

    return Response(content=jpeg_bytes, media_type="image/jpeg")

def generate_mjpeg_stream(camera_id: str):
    while True:
        jpeg_bytes = camera_manager.get_latest_frame_jpeg(camera_id)
        if jpeg_bytes:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n')
        time.sleep(0.033)

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
    """Upload a custom CCTV video file to data/videos and videos directories."""
    if not file.filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
        raise HTTPException(status_code=400, detail="Unsupported video format.")

    videos_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "videos"))
    data_videos_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "videos"))
    os.makedirs(videos_dir, exist_ok=True)
    os.makedirs(data_videos_dir, exist_ok=True)

    target_path = os.path.join(videos_dir, file.filename)
    target_data_path = os.path.join(data_videos_dir, file.filename)

    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    shutil.copyfile(target_path, target_data_path)

    # If camera exists, switch to uploaded video
    if camera_id in camera_manager.processors:
        proc = camera_manager.processors[camera_id]
        proc.stop()
        proc.source_path = target_path
        from vision.source import FileCameraSource
        proc.source = FileCameraSource(target_path, name=proc.camera_name, loop=True)
        proc.start()

    return {"status": "success", "filename": file.filename, "path": target_path}
