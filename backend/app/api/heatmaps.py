from fastapi import APIRouter, Response, HTTPException
from typing import Dict, Any, List
try:
    from backend.app.services.camera_manager import camera_manager
except ModuleNotFoundError:
    from app.services.camera_manager import camera_manager

router = APIRouter(prefix="/api/heatmap", tags=["Heatmaps"])

@router.get("/{camera_id}")
def get_camera_heatmap(camera_id: str, overlay: bool = True):
    """Retrieve thermal movement heatmap image overlay for a camera feed."""
    if camera_id in camera_manager.processors:
        proc = camera_manager.processors[camera_id]
        if proc.latest_frame is not None:
            # Generate heatmap overlay on latest frame
            heatmap_frame = proc.heatmap.generate_overlay(proc.latest_frame.copy(), alpha=0.6)
            import cv2
            ret, jpeg = cv2.imencode('.jpg', heatmap_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
            if ret:
                return Response(content=jpeg.tobytes(), media_type="image/jpeg")

    # Placeholder fallback
    import cv2
    import numpy as np
    img = np.zeros((360, 640, 3), dtype=np.uint8)
    cv2.putText(img, "HEATMAP INITIALIZING", (120, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
    _, jpeg = cv2.imencode('.jpg', img)
    return Response(content=jpeg.tobytes(), media_type="image/jpeg")

from fastapi.responses import StreamingResponse
import time

def generate_heatmap_mjpeg_stream(camera_id: str):
    import cv2
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
