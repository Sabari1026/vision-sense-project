import time
import cv2
import numpy as np
from fastapi import APIRouter, Response, HTTPException
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List, Optional

try:
    from backend.app.services.camera_manager import camera_manager
except ModuleNotFoundError:
    from app.services.camera_manager import camera_manager

router = APIRouter(prefix="/api/heatmap", tags=["Heatmaps"])

def build_combined_heatmap_frame() -> np.ndarray:
    """Combines 4 camera heatmap frames into a unified 2x2 showroom layout."""
    frames = []
    for cam_id, proc in camera_manager.processors.items():
        if proc.latest_frame is not None:
            hm_frame = proc.heatmap.generate_overlay(proc.latest_frame.copy(), alpha=0.6)
            hm_resized = cv2.resize(hm_frame, (640, 360))
        else:
            hm_resized = np.zeros((360, 640, 3), dtype=np.uint8)
            cv2.putText(hm_resized, f"CAM {proc.camera_name}", (40, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 220, 255), 2)
        frames.append(hm_resized)

    while len(frames) < 4:
        dummy = np.zeros((360, 640, 3), dtype=np.uint8)
        frames.append(dummy)

    row1 = np.hstack([frames[0], frames[1]])
    row2 = np.hstack([frames[2], frames[3]])
    combined = np.vstack([row1, row2])
    return combined

@router.get("/combined")
def get_combined_store_heatmap():
    """Retrieve unified 2x2 store thermal movement heatmap snapshot."""
    combined = build_combined_heatmap_frame()
    ret, jpeg = cv2.imencode('.jpg', combined, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    if ret:
        return Response(content=jpeg.tobytes(), media_type="image/jpeg")
    raise HTTPException(status_code=500, detail="Could not encode combined heatmap.")

def generate_combined_heatmap_stream():
    while True:
        combined = build_combined_heatmap_frame()
        ret, jpeg = cv2.imencode('.jpg', combined, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
        if ret:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
        time.sleep(0.05)

@router.get("/combined/stream")
def stream_combined_store_heatmap():
    """Stream live unified 2x2 showroom thermal heatmap."""
    return StreamingResponse(
        generate_combined_heatmap_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.get("/{camera_id}")
def get_camera_heatmap(camera_id: str):
    """Retrieve thermal movement heatmap image overlay for a specific camera feed."""
    if camera_id in camera_manager.processors:
        proc = camera_manager.processors[camera_id]
        if proc.latest_frame is not None:
            heatmap_frame = proc.heatmap.generate_overlay(proc.latest_frame.copy(), alpha=0.6)
            ret, jpeg = cv2.imencode('.jpg', heatmap_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
            if ret:
                return Response(content=jpeg.tobytes(), media_type="image/jpeg")

    img = np.zeros((360, 640, 3), dtype=np.uint8)
    cv2.putText(img, "HEATMAP INITIALIZING", (120, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
    _, jpeg = cv2.imencode('.jpg', img)
    return Response(content=jpeg.tobytes(), media_type="image/jpeg")

def generate_heatmap_mjpeg_stream(camera_id: str):
    while True:
        if camera_id in camera_manager.processors:
            proc = camera_manager.processors[camera_id]
            if proc.latest_frame is not None:
                heatmap_frame = proc.heatmap.generate_overlay(proc.latest_frame.copy(), alpha=0.6)
                ret, jpeg = cv2.imencode('.jpg', heatmap_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
                if ret:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
        time.sleep(0.033)

@router.get("/{camera_id}/stream")
def stream_camera_heatmap(camera_id: str):
    """Stream live CCTV thermal movement heatmap as smooth continuous MJPEG multipart stream."""
    return StreamingResponse(
        generate_heatmap_mjpeg_stream(camera_id),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
