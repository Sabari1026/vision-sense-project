from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any, Optional
import uuid
import json

try:
    from backend.app.services.supabase_client import db_service
    from backend.app.services.camera_manager import camera_manager
except ModuleNotFoundError:
    from app.services.supabase_client import db_service
    from app.services.camera_manager import camera_manager

router = APIRouter(prefix="/api/zones", tags=["Zones"])

@router.get("")
def list_zones(camera_id: Optional[str] = None):
    """List all configured polygon zones, optionally filtered by camera."""
    return db_service.get_zones(camera_id=camera_id)

@router.post("")
def create_zone(payload: Dict[str, Any] = Body(...)):
    """Create a new polygon zone for a camera and register it in live vision processors."""
    zone_id = payload.get('id', str(uuid.uuid4()))
    camera_id = payload.get('camera_id')
    name = payload.get('name', 'Custom Zone')
    polygon = payload.get('polygon', [])
    zone_type = payload.get('zone_type', 'polygon')

    if not camera_id or len(polygon) < 3:
        raise HTTPException(status_code=400, detail="Invalid polygon: minimum 3 points required.")

    # Save to Database
    if db_service.use_supabase and db_service.client:
        try:
            db_service.client.table('camera_zones').insert({
                'id': zone_id,
                'camera_id': camera_id,
                'name': name,
                'zone_type': zone_type,
                'polygon': polygon
            }).execute()
        except Exception as e:
            pass

    # Save to local SQLite
    import sqlite3
    try:
        conn = sqlite3.connect(db_service.sqlite_path)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO camera_zones (id, camera_id, name, zone_type, polygon, created_at)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, (zone_id, camera_id, name, zone_type, json.dumps(polygon)))
        conn.commit()
        conn.close()
    except Exception:
        pass

    # Update active Camera Processor
    if camera_id in camera_manager.processors:
        proc = camera_manager.processors[camera_id]
        proc.zone_manager.add_zone(zone_id, name, polygon, zone_type)

    return {"status": "success", "zone_id": zone_id, "name": name}

@router.put("/{zone_id}")
def update_zone(zone_id: str, payload: Dict[str, Any] = Body(...)):
    """Update name or coordinates of an existing polygon zone."""
    name = payload.get('name')
    polygon = payload.get('polygon')
    camera_id = payload.get('camera_id')

    if db_service.use_supabase and db_service.client:
        try:
            update_data = {}
            if name: update_data['name'] = name
            if polygon: update_data['polygon'] = polygon
            db_service.client.table('camera_zones').update(update_data).eq('id', zone_id).execute()
        except Exception:
            pass

    import sqlite3
    try:
        conn = sqlite3.connect(db_service.sqlite_path)
        cursor = conn.cursor()
        if name and polygon:
            cursor.execute("UPDATE camera_zones SET name = ?, polygon = ? WHERE id = ?", (name, json.dumps(polygon), zone_id))
        elif name:
            cursor.execute("UPDATE camera_zones SET name = ? WHERE id = ?", (name, zone_id))
        elif polygon:
            cursor.execute("UPDATE camera_zones SET polygon = ? WHERE id = ?", (json.dumps(polygon), zone_id))
        conn.commit()
        conn.close()
    except Exception:
        pass

    if camera_id and camera_id in camera_manager.processors:
        proc = camera_manager.processors[camera_id]
        if polygon and name:
            proc.zone_manager.add_zone(zone_id, name, polygon)

    return {"status": "success", "zone_id": zone_id}

@router.delete("/{zone_id}")
def delete_zone(zone_id: str):
    """Delete a polygon zone."""
    if db_service.use_supabase and db_service.client:
        try:
            db_service.client.table('camera_zones').delete().eq('id', zone_id).execute()
        except Exception:
            pass

    import sqlite3
    try:
        conn = sqlite3.connect(db_service.sqlite_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM camera_zones WHERE id = ?", (zone_id,))
        conn.commit()
        conn.close()
    except Exception:
        pass

    # Remove from active processors
    for proc in camera_manager.processors.values():
        proc.zone_manager.zones = [z for z in proc.zone_manager.zones if z['id'] != zone_id]

    return {"status": "success", "deleted_zone_id": zone_id}
