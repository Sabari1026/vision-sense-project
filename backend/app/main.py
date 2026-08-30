import os
import sys

# Bootstrap Python sys.path so 'backend' and 'app' modules resolve on any cloud host
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
    from backend.app.api.analytics import router as analytics_router
    from backend.app.api.heatmaps import router as heatmaps_router
    from backend.app.api.reports import router as reports_router
    from backend.app.api.system import router as system_router
    from backend.app.api.ws import router as ws_router
    from backend.app.services.camera_manager import camera_manager
except ModuleNotFoundError:
    from app.api.cameras import router as cameras_router
    from app.api.analytics import router as analytics_router
    from app.api.heatmaps import router as heatmaps_router
    from app.api.reports import router as reports_router
    from app.api.system import router as system_router
    from app.api.ws import router as ws_router
    from app.services.camera_manager import camera_manager

app = FastAPI(
    title="VisionSense AI CCTV Retail Analytics API",
    description="Backend API powering VisionSense real-time computer vision monitoring, tracking, occupancy, dwell time, and heatmaps.",
    version="1.0.0"
)

# Enable CORS for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(cameras_router)
app.include_router(analytics_router)
app.include_router(heatmaps_router)
app.include_router(reports_router)
app.include_router(system_router)
app.include_router(ws_router)

# Mount videos static directory
videos_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "videos"))
os.makedirs(videos_dir, exist_ok=True)
app.mount("/videos", StaticFiles(directory=videos_dir), name="videos")

@app.on_event("startup")
def on_startup():
    print("==================================================================")
    print(" VisionSense AI CCTV Retail Analytics Platform Engine Initialized ")
    print("==================================================================")
    import torch
    import gc
    try:
        torch.set_num_threads(2)
        torch.set_grad_enabled(False)
    except Exception:
        pass
    gc.collect()
    # Auto start camera workers in Demo Mode
    camera_manager.start_all()

@app.on_event("shutdown")
def on_shutdown():
    print("Stopping VisionSense camera workers...")
    camera_manager.stop_all()

@app.get("/")
def root():
    return {
        "title": "VisionSense AI CCTV API",
        "status": "Online",
        "docs": "/docs",
        "health": "/api/system/health"
    }
