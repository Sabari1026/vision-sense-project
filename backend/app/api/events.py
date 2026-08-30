from fastapi import APIRouter, Query
from typing import List, Dict, Any, Optional
import time

try:
    from backend.app.services.supabase_client import db_service
    from backend.app.services.camera_manager import camera_manager
except ModuleNotFoundError:
    from app.services.supabase_client import db_service
    from app.services.camera_manager import camera_manager

router = APIRouter(prefix="/api/events", tags=["Events"])

@router.get("")
def list_recent_events(limit: int = Query(50, ge=1, le=200), camera_id: Optional[str] = None):
    """Retrieve chronological log of recent store visitor events (Entries, Exits, Dwell)."""
    sessions = db_service.get_visitor_sessions(limit=limit, camera_id=camera_id)
    events = []
    
    for s in sessions:
        # Generate Entry event
        if s.get('entry_time'):
            events.append({
                "id": f"{s['id']}-entry",
                "camera_id": s.get('camera_id'),
                "track_id": s.get('anonymous_track_id'),
                "global_person_id": s.get('global_person_id'),
                "event_type": "ENTRY",
                "timestamp": s.get('entry_time'),
                "zone": s.get('entry_zone', 'Entrance'),
                "age_group": s.get('age_group', 'Unknown')
            })
        
        # Generate Exit event if session ended
        if s.get('exit_time'):
            events.append({
                "id": f"{s['id']}-exit",
                "camera_id": s.get('camera_id'),
                "track_id": s.get('anonymous_track_id'),
                "global_person_id": s.get('global_person_id'),
                "event_type": "EXIT",
                "timestamp": s.get('exit_time'),
                "dwell_seconds": s.get('dwell_seconds', 0),
                "zone": s.get('exit_zone', 'Checkout Area')
            })

    # Sort descending by timestamp
    events.sort(key=lambda x: x.get('timestamp') or 0, reverse=True)
    return events[:limit]

@router.get("/entries")
def list_entry_events(limit: int = Query(50, ge=1, le=200)):
    """Retrieve filtered list of visitor entry events."""
    all_events = list_recent_events(limit=limit * 2)
    return [e for e in all_events if e['event_type'] == 'ENTRY'][:limit]

@router.get("/exits")
def list_exit_events(limit: int = Query(50, ge=1, le=200)):
    """Retrieve filtered list of visitor exit events."""
    all_events = list_recent_events(limit=limit * 2)
    return [e for e in all_events if e['event_type'] == 'EXIT'][:limit]
