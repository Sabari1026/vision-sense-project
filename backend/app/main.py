import os
import sys

# Bootstrap Python sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

try:
    from backend.app.api.cameras import router as cameras_router
    from backend.app.api.tracking import router as tracking_router
    from backend.app.api.events import router as events_router
    from backend.app.api.zones import router as zones_router
    from backend.app.api.analytics import router as analytics_router
    from backend.app.api.heatmaps import router as heatmaps_router
    from backend.app.api.reports import router as reports_router
    from backend.app.api.system import router as system_router
    from backend.app.api.ws import router as ws_router
    from backend.app.services.camera_manager import camera_manager
except ModuleNotFoundError:
    from app.api.cameras import router as cameras_router
    from app.api.tracking import router as tracking_router
    from app.api.events import router as events_router
    from app.api.zones import router as zones_router
    from app.api.analytics import router as analytics_router
    from app.api.heatmaps import router as heatmaps_router
    from app.api.reports import router as reports_router
    from app.api.system import router as system_router
    from app.api.ws import router as ws_router
    from app.services.camera_manager import camera_manager

app = FastAPI(
    title="VisionSense AI CCTV Retail Analytics Platform",
    description="Production-ready 4-Camera CCTV Person Detection, ByteTrack Multi-Object Tracking, Dwell Time, Zone Analytics, and Heatmaps API.",
    version="2.0.0"
)

# Enable CORS for React Dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register REST & WebSocket API Routers
app.include_router(cameras_router)
app.include_router(tracking_router)
app.include_router(events_router)
app.include_router(zones_router)
app.include_router(analytics_router)
app.include_router(heatmaps_router)
app.include_router(reports_router)
app.include_router(system_router)
app.include_router(ws_router)

# Static files for local video streaming
videos_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "videos"))
os.makedirs(videos_dir, exist_ok=True)
app.mount("/videos", StaticFiles(directory=videos_dir), name="videos")

@app.on_event("startup")
def on_startup():
    print("==================================================================")
    print(" VisionSense AI CCTV Retail Analytics Engine (4-Camera) Initialized ")
    print("==================================================================")
    camera_manager.start_all()

@app.on_event("shutdown")
def on_shutdown():
    print("Stopping VisionSense camera workers...")
    camera_manager.stop_all()

@app.get("/")
def root():
    return {
        "title": "VisionSense AI CCTV Retail Analytics API",
        "status": "Online",
        "cameras_active": 4,
        "docs": "/docs",
        "health": "/api/system/health"
    }
