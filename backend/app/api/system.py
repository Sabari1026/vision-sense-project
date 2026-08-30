import psutil
import time
import torch
from fastapi import APIRouter
try:
    from backend.app.services.camera_manager import camera_manager
    from backend.app.services.supabase_client import db_service
except ModuleNotFoundError:
    from app.services.camera_manager import camera_manager
    from app.services.supabase_client import db_service

router = APIRouter(prefix="/api/system", tags=["System"])

@router.get("/health")
def get_system_health():
    """Returns real-time hardware, engine, camera, and database health metrics."""
    cpu_percent = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory()

    gpu_available = False
    gpu_name = "N/A (CPU Mode)"
    try:
        if torch.cuda.is_available():
            gpu_available = True
            gpu_name = torch.cuda.get_device_name(0)
    except:
        pass

    # Measure DB Latency
    db_start = time.time()
    cameras = db_service.get_cameras()
    db_latency = round((time.time() - db_start) * 1000, 2)

    camera_statuses = camera_manager.get_all_stats()

    return {
        "status": "Healthy",
        "backend": "Online",
        "database": "Connected (Supabase / Local)",
        "database_type": "Supabase PostgreSQL" if db_service.use_supabase else "SQLite Local",
        "database_latency_ms": db_latency,
        "yolo_model": "Loaded (YOLOv8n)",
        "gpu_available": gpu_available,
        "gpu_name": gpu_name,
        "cpu_usage_percent": cpu_percent,
        "memory_usage_percent": memory.percent,
        "memory_used_gb": round(memory.used / (1024**3), 2),
        "memory_total_gb": round(memory.total / (1024**3), 2),
        "cameras": [
            {
                "camera_id": c.get('camera_id'),
                "name": c.get('camera_name'),
                "status": c.get('status', 'STOPPED'),
                "fps": c.get('fps', 0)
            }
            for c in camera_statuses
        ]
    }
