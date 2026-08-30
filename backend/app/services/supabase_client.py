import os
import time
import sqlite3
import json
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

class DatabaseService:
    """Unified Database Service connecting to Supabase with local SQLite fallback."""

    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        self.use_supabase = False
        self.client = None

        self._init_db()

    def _init_db(self):
        if self.supabase_url and "demo-vision-sense" not in self.supabase_url:
            try:
                from supabase import create_client
                self.client = create_client(self.supabase_url, self.supabase_key)
                self.use_supabase = True
                print("[DatabaseService] Connected to live Supabase PostgreSQL.")
                return
            except Exception as e:
                print(f"[DatabaseService] Could not connect to Supabase ({e}). Initializing SQLite fallback.")

        # Fallback Local SQLite DB
        self.use_supabase = False
        self.sqlite_path = os.path.join(os.path.dirname(__file__), "..", "..", "local_visionsense.db")
        self._init_sqlite()
        print("[DatabaseService] Running in Local SQLite Database fallback mode.")

    def _init_sqlite(self):
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()

        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS cameras (
            id TEXT PRIMARY KEY,
            name TEXT,
            location TEXT,
            source_type TEXT,
            source_path TEXT,
            status TEXT,
            resolution TEXT,
            fps INTEGER,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS camera_zones (
            id TEXT PRIMARY KEY,
            camera_id TEXT,
            name TEXT,
            zone_type TEXT,
            polygon TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS visitor_sessions (
            id TEXT PRIMARY KEY,
            camera_id TEXT,
            anonymous_track_id INTEGER,
            entry_time REAL,
            exit_time REAL,
            dwell_seconds INTEGER,
            age_group TEXT,
            age_confidence REAL,
            entry_zone TEXT,
            exit_zone TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS detection_events (
            id TEXT PRIMARY KEY,
            camera_id TEXT,
            track_id INTEGER,
            timestamp REAL,
            center_x INTEGER,
            center_y INTEGER,
            bbox_x INTEGER,
            bbox_y INTEGER,
            bbox_width INTEGER,
            bbox_height INTEGER,
            confidence REAL,
            zone_id TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS zone_visits (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            camera_id TEXT,
            zone_id TEXT,
            entered_at REAL,
            exited_at REAL,
            duration_seconds INTEGER,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS heatmap_points (
            id TEXT PRIMARY KEY,
            camera_id TEXT,
            timestamp REAL,
            x INTEGER,
            y INTEGER,
            weight REAL,
            zone_id TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS analytics_snapshots (
            id TEXT PRIMARY KEY,
            camera_id TEXT,
            timestamp REAL,
            people_count INTEGER,
            entries INTEGER,
            exits INTEGER,
            occupancy INTEGER,
            average_dwell_seconds REAL,
            total_visitors INTEGER,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY,
            report_type TEXT,
            start_date TEXT,
            end_date TEXT,
            report_data TEXT,
            created_at TEXT
        );
        """)
        conn.commit()

        # Insert default cameras into SQLite if empty
        cursor.execute("SELECT COUNT(*) FROM cameras")
        if cursor.fetchone()[0] == 0:
            cursor.executescript("""
            INSERT INTO cameras (id, name, location, source_type, source_path, status, resolution, fps, created_at) VALUES
            ('11111111-1111-1111-1111-111111111111', 'Camera 01 - USA Retail Store #2', 'Main Entrance & Retail Floor', 'file', 'videos/vidssave.com E43A inside the Retail store in USA #2 1080P.mp4', 'LIVE', '1920x1080', 30, datetime('now')),
            ('22222222-2222-2222-2222-222222222222', 'Camera 02 - HD CCTV Retail Store', 'Clothing & Display Aisles', 'file', 'videos/vidssave.com HD CCTV Camera video 3MP 4MP iProx CCTV HDCCTVCameras.net retail store 720p.mp4', 'LIVE', '1270x720', 13, datetime('now')),
            ('33333333-3333-3333-3333-333333333333', 'Camera 03 - Electronics Hub', 'Electronics Section', 'file', 'videos/camera3.mp4', 'LIVE', '1280x720', 25, datetime('now')),
            ('44444444-4444-4444-4444-444444444444', 'Camera 04 - Checkout Counters', 'Billing Area', 'file', 'videos/camera4.mp4', 'LIVE', '1280x720', 25, datetime('now'));

            INSERT INTO camera_zones (id, camera_id, name, zone_type, polygon, created_at) VALUES
            ('a1111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111', 'Zone A - Entrance Door', 'polygon', '[[100, 100], [400, 100], [400, 400], [100, 400]]', datetime('now')),
            ('a2222222-2222-2222-2222-222222222222', '22222222-2222-2222-2222-222222222222', 'Zone B - Apparel Racks', 'polygon', '[[200, 150], [600, 150], [600, 500], [200, 500]]', datetime('now')),
            ('a3333333-3333-3333-3333-333333333333', '33333333-3333-3333-3333-333333333333', 'Zone C - Electronics Display', 'polygon', '[[150, 200], [550, 200], [550, 600], [150, 600]]', datetime('now')),
            ('a4444444-4444-4444-4444-444444444444', '44444444-4444-4444-4444-444444444444', 'Zone D - Billing Desk', 'polygon', '[[300, 100], [700, 100], [700, 400], [300, 400]]', datetime('now'));
            """)
            conn.commit()
        conn.close()

    def upsert_camera(self, camera: Dict[str, Any]):
        if self.use_supabase and self.client:
            try:
                self.client.table('cameras').upsert(camera).execute()
                return
            except Exception as e:
                print(f"[DatabaseService] Supabase camera upsert error: {e}")

        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO cameras (id, name, location, source_type, source_path, status, resolution, fps, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            location=excluded.location,
            source_type=excluded.source_type,
            source_path=excluded.source_path,
            status=excluded.status,
            resolution=excluded.resolution,
            fps=excluded.fps
        """, (
            camera.get('id'),
            camera.get('name'),
            camera.get('location', 'Store Floor'),
            camera.get('source_type', 'file'),
            camera.get('source_path'),
            camera.get('status', 'LIVE'),
            camera.get('resolution', '1280x720'),
            camera.get('fps', 25)
        ))
        conn.commit()
        conn.close()

    def get_cameras(self) -> List[Dict[str, Any]]:
        if self.use_supabase and self.client:
            res = self.client.table('cameras').select('*').execute()
            return res.data or []

        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cameras")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def get_zones(self, camera_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if self.use_supabase and self.client:
            query = self.client.table('camera_zones').select('*')
            if camera_id:
                query = query.eq('camera_id', camera_id)
            res = query.execute()
            return res.data or []

        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if camera_id:
            cursor.execute("SELECT * FROM camera_zones WHERE camera_id = ?", (camera_id,))
        else:
            cursor.execute("SELECT * FROM camera_zones")
        rows = []
        for r in cursor.fetchall():
            row_dict = dict(r)
            if isinstance(row_dict.get('polygon'), str):
                try:
                    row_dict['polygon'] = json.loads(row_dict['polygon'])
                except:
                    pass
            rows.append(row_dict)
        conn.close()
        return rows

    def save_visitor_sessions(self, sessions: List[Dict[str, Any]]):
        if not sessions:
            return

        if self.use_supabase and self.client:
            try:
                self.client.table('visitor_sessions').insert(sessions).execute()
                return
            except Exception as e:
                print(f"[DatabaseService] Supabase insert error: {e}")

        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        import uuid
        for s in sessions:
            cursor.execute("""
            INSERT INTO visitor_sessions (id, camera_id, anonymous_track_id, entry_time, exit_time, dwell_seconds, age_group, age_confidence, entry_zone, exit_zone, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                s.get('id', str(uuid.uuid4())),
                s.get('camera_id'),
                s.get('anonymous_track_id'),
                s.get('entry_time'),
                s.get('exit_time'),
                s.get('dwell_seconds'),
                s.get('age_group', 'Unknown'),
                s.get('age_confidence', 0.0),
                s.get('entry_zone'),
                s.get('exit_zone')
            ))
        conn.commit()
        conn.close()

    def get_visitor_sessions(self, limit: int = 100, camera_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if self.use_supabase and self.client:
            query = self.client.table('visitor_sessions').select('*').order('created_at', desc=True)
            if camera_id:
                query = query.eq('camera_id', camera_id)
            res = query.limit(limit).execute()
            return res.data or []

        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if camera_id:
            cursor.execute("SELECT * FROM visitor_sessions WHERE camera_id = ? ORDER BY created_at DESC LIMIT ?", (camera_id, limit))
        else:
            cursor.execute("SELECT * FROM visitor_sessions ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def save_detection_events(self, events: List[Dict[str, Any]]):
        if not events:
            return

        if self.use_supabase and self.client:
            try:
                # Batch insert in chunks of 100
                for i in range(0, len(events), 100):
                    self.client.table('detection_events').insert(events[i:i+100]).execute()
                return
            except Exception as e:
                print(f"[DatabaseService] Supabase detection_events insert error: {e}")

        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        import uuid
        for ev in events:
            cursor.execute("""
            INSERT INTO detection_events (id, camera_id, track_id, timestamp, center_x, center_y, bbox_x, bbox_y, bbox_width, bbox_height, confidence, zone_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                ev.get('id', str(uuid.uuid4())),
                ev.get('camera_id'),
                ev.get('track_id'),
                ev.get('timestamp'),
                ev.get('center_x'),
                ev.get('center_y'),
                ev.get('bbox_x'),
                ev.get('bbox_y'),
                ev.get('bbox_width'),
                ev.get('bbox_height'),
                ev.get('confidence'),
                ev.get('zone_id')
            ))
        conn.commit()
        conn.close()

    def get_detection_events(self, limit: int = 100, camera_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if self.use_supabase and self.client:
            query = self.client.table('detection_events').select('*').order('created_at', desc=True)
            if camera_id:
                query = query.eq('camera_id', camera_id)
            res = query.limit(limit).execute()
            return res.data or []

        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if camera_id:
            cursor.execute("SELECT * FROM detection_events WHERE camera_id = ? ORDER BY created_at DESC LIMIT ?", (camera_id, limit))
        else:
            cursor.execute("SELECT * FROM detection_events ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def save_heatmap_points(self, points: List[Dict[str, Any]]):
        if not points:
            return

        if self.use_supabase and self.client:
            try:
                for i in range(0, len(points), 100):
                    self.client.table('heatmap_points').insert(points[i:i+100]).execute()
                return
            except Exception as e:
                pass

        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        import uuid
        for p in points:
            cursor.execute("""
            INSERT INTO heatmap_points (id, camera_id, timestamp, x, y, weight, zone_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                p.get('id', str(uuid.uuid4())),
                p.get('camera_id'),
                p.get('timestamp'),
                p.get('x'),
                p.get('y'),
                p.get('weight', 1.0),
                p.get('zone_id')
            ))
        conn.commit()
        conn.close()

    def get_heatmap_points(self, limit: int = 2000, camera_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if self.use_supabase and self.client:
            query = self.client.table('heatmap_points').select('*').order('created_at', desc=True)
            if camera_id:
                query = query.eq('camera_id', camera_id)
            res = query.limit(limit).execute()
            return res.data or []

        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if camera_id:
            cursor.execute("SELECT * FROM heatmap_points WHERE camera_id = ? ORDER BY created_at DESC LIMIT ?", (camera_id, limit))
        else:
            cursor.execute("SELECT * FROM heatmap_points ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def save_analytics_snapshots(self, snapshots: List[Dict[str, Any]]):
        if not snapshots:
            return

        if self.use_supabase and self.client:
            try:
                self.client.table('analytics_snapshots').insert(snapshots).execute()
                return
            except Exception as e:
                pass

        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        import uuid
        for s in snapshots:
            cursor.execute("""
            INSERT INTO analytics_snapshots (id, camera_id, timestamp, people_count, entries, exits, occupancy, average_dwell_seconds, total_visitors, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                s.get('id', str(uuid.uuid4())),
                s.get('camera_id'),
                s.get('timestamp'),
                s.get('people_count'),
                s.get('entries'),
                s.get('exits'),
                s.get('occupancy'),
                s.get('average_dwell_seconds'),
                s.get('total_visitors')
            ))
        conn.commit()
        conn.close()

    def save_zone_visits(self, zone_visits: List[Dict[str, Any]]):
        if not zone_visits:
            return

        if self.use_supabase and self.client:
            try:
                self.client.table('zone_visits').insert(zone_visits).execute()
                return
            except Exception as e:
                pass

        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        import uuid
        for zv in zone_visits:
            cursor.execute("""
            INSERT INTO zone_visits (id, session_id, camera_id, zone_id, entered_at, exited_at, duration_seconds, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                zv.get('id', str(uuid.uuid4())),
                zv.get('session_id'),
                zv.get('camera_id'),
                zv.get('zone_id'),
                zv.get('entered_at'),
                zv.get('exited_at'),
                zv.get('duration_seconds')
            ))
        conn.commit()
        conn.close()

db_service = DatabaseService()

