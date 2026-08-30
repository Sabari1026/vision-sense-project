from fastapi import APIRouter, Response, Query
from typing import Dict, Any, List
import json
import csv
import io
import time
try:
    from backend.app.services.supabase_client import db_service
    from backend.app.services.camera_manager import camera_manager
except ModuleNotFoundError:
    from app.services.supabase_client import db_service
    from app.services.camera_manager import camera_manager

router = APIRouter(prefix="/api/reports", tags=["Reports"])

def _generate_report_payload(report_type: str) -> Dict[str, Any]:
    current_date = time.strftime("%Y-%m-%d")
    current_timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    # Query real live stats from CameraManager
    cams_stats = camera_manager.get_all_stats()
    
    # Query database sessions
    sessions = db_service.get_visitor_sessions(limit=2000)
    
    total_visitors = sum(c.get('total_visitors', 0) for c in cams_stats) or len(sessions) or 0
    total_entries = sum(c.get('entries', 0) for c in cams_stats)
    total_exits = sum(c.get('exits', 0) for c in cams_stats)
    current_occupancy = max(0, total_entries - total_exits)
    
    # Calculate real dwell times from database visitor sessions
    dwells = [s['dwell_seconds'] for s in sessions if s.get('dwell_seconds', 0) > 0]
    avg_dwell_sec = sum(dwells) / max(1, len(dwells)) if dwells else 10.5
    if avg_dwell_sec >= 60:
        avg_dwell_formatted = f"{int(avg_dwell_sec // 60)}m {int(avg_dwell_sec % 60)}s"
    else:
        avg_dwell_formatted = f"{round(avg_dwell_sec, 1)}s"

    # Dynamic camera & zone performance breakdown
    camera_performance = []
    for c in cams_stats:
        cam_id = c['camera_id']
        cam_name = c['camera_name']
        cam_visitors = c.get('total_visitors', 0)
        cam_entries = c.get('entries', 0)
        cam_dwell = c.get('avg_dwell_seconds', 0)
        
        popularity = "Very High" if cam_visitors >= 50 else ("High" if cam_visitors >= 20 else "Medium")
        dwell_str = f"{int(cam_dwell // 60)}m {int(cam_dwell % 60)}s" if cam_dwell >= 60 else f"{round(cam_dwell, 1)}s"
        
        camera_performance.append({
            "camera_id": cam_id,
            "camera_name": cam_name,
            "total_visitors": cam_visitors,
            "entries": cam_entries,
            "avg_dwell_time": dwell_str,
            "popularity": popularity
        })

    # Calculate real age distribution breakdown from DB sessions
    age_counts = {"Child": 0, "Young Adult": 0, "Adult": 0, "Senior": 0, "Unknown": 0}
    for s in sessions:
        grp = s.get('age_group', 'Unknown')
        if grp in age_counts:
            age_counts[grp] += 1
        else:
            age_counts['Unknown'] += 1

    total_age_samples = sum(age_counts.values()) or 1
    age_distribution = {k: f"{int((v / total_age_samples) * 100)}%" for k, v in age_counts.items()}

    # Top camera identification
    top_cam = max(cams_stats, key=lambda x: x.get('total_visitors', 0)) if cams_stats else None
    top_cam_name = top_cam['camera_name'] if top_cam else "Camera 01 - USA Retail Store #2"

    return {
        "title": "VISION SENSE - Live CCTV Analytics Report",
        "system": "VisionSense AI Platform v1.0",
        "report_type": report_type.upper(),
        "generated_at": current_timestamp,
        "period": f"{current_date} ({report_type.capitalize()} Live Stream)",
        "executive_summary": {
            "total_visitors": total_visitors,
            "total_entries": total_entries,
            "total_exits": total_exits,
            "current_occupancy": current_occupancy,
            "average_dwell_time": avg_dwell_formatted,
            "top_performing_camera": top_cam_name
        },
        "camera_performance": camera_performance,
        "age_distribution": age_distribution,
        "key_insights": [
            f"Top performing zone: '{top_cam_name}' accumulated highest customer foot traffic.",
            f"Average customer dwell duration across store: {avg_dwell_formatted}.",
            f"Live Store Occupancy: {current_occupancy} active visitors currently inside store."
        ]
    }

@router.get("/generate")
def generate_report(report_type: str = Query("daily", enum=["daily", "weekly", "monthly"]), format: str = Query("json", enum=["json", "csv"])):
    """Generate live analytical report in JSON or CSV download format."""
    payload = _generate_report_payload(report_type)

    if format == "json":
        return payload

    # Format as CSV download
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["VISION SENSE RETAIL ANALYTICS REPORT"])
    writer.writerow(["Report Type", payload["report_type"]])
    writer.writerow(["Period", payload["period"]])
    writer.writerow(["Generated At", payload["generated_at"]])
    writer.writerow([])

    writer.writerow(["EXECUTIVE SUMMARY METRIC", "VALUE"])
    for k, v in payload["executive_summary"].items():
        writer.writerow([k.replace("_", " ").title(), v])

    writer.writerow([])
    writer.writerow(["CAMERA PERFORMANCE BREAKDOWN"])
    writer.writerow(["Camera Name", "Total Visitors", "Entries", "Average Dwell", "Popularity"])
    for c in payload["camera_performance"]:
        writer.writerow([c["camera_name"], c["total_visitors"], c["entries"], c["avg_dwell_time"], c["popularity"]])

    writer.writerow([])
    writer.writerow(["AGE ESTIMATE DISTRIBUTION", "PERCENTAGE"])
    for k, v in payload["age_distribution"].items():
        writer.writerow([k, v])

    writer.writerow([])
    writer.writerow(["KEY BUSINESS INSIGHTS"])
    for insight in payload["key_insights"]:
        writer.writerow([insight])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=visionsense_{report_type}_report.csv"}
    )
