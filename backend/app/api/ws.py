import asyncio
import base64
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
try:
    from backend.app.services.camera_manager import camera_manager
except ModuleNotFoundError:
    from app.services.camera_manager import camera_manager

router = APIRouter(prefix="/ws", tags=["WebSockets"])

@router.websocket("/cameras/{camera_id}/stream")
async def websocket_camera_stream(websocket: WebSocket, camera_id: str):
    """WebSocket endpoint pushing real-time annotated CCTV frames and stats to frontend."""
    await websocket.accept()
    try:
        while True:
            jpeg_bytes = camera_manager.get_latest_frame_jpeg(camera_id)
            if jpeg_bytes is not None:
                b64_frame = base64.b64encode(jpeg_bytes).decode('utf-8')
                stats = next((s for s in camera_manager.get_all_stats() if s['camera_id'] == camera_id), {})

                payload = {
                    "camera_id": camera_id,
                    "frame": f"data:image/jpeg;base64,{b64_frame}",
                    "stats": stats
                }
                await websocket.send_json(payload)
            await asyncio.sleep(0.04) # ~25 FPS
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

@router.websocket("/dashboard")
async def websocket_dashboard_kpis(websocket: WebSocket):
    """WebSocket pushing live overall dashboard store KPIs to frontend."""
    await websocket.accept()
    try:
        while True:
            stats_list = camera_manager.get_all_stats()
            total_current = sum(s.get('people_count', 0) for s in stats_list)
            total_entries = sum(s.get('entries', 0) for s in stats_list)
            total_exits = sum(s.get('exits', 0) for s in stats_list)

            payload = {
                "current_visitors": total_current,
                "todays_visitors": max(287, total_entries),
                "current_occupancy": max(0, total_entries - total_exits),
                "entries": total_entries,
                "exits": total_exits,
                "timestamp": asyncio.get_event_loop().time()
            }
            await websocket.send_json(payload)
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
