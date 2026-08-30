import os
import time
import sqlite3
import json
import uuid
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
        self.sqlite_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "local_visionsense.db"))

        self._init_sqlite()
        self._init_supabase()

    def _init_supabase(self):
        if self.supabase_url and "demo-vision-sense" not in self.supabase_url:
            try:
                from supabase import create_client
                self.client = create_client(self.supabase_url, self.supabase_key)
                self.use_supabase = True
                print("[DatabaseService] Connected to live Supabase PostgreSQL.")
                return
            except Exception as e:
                print(f"[DatabaseService] Could not connect to Supabase ({e}). Using SQLite mode.")
                self.use_supabase = False

    def _init_sqlite(self):
        try:
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
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[DatabaseService] SQLite init warning: {e}")

    def save_visitor_sessions(self, sessions: List[Dict[str, Any]]):
        if not sessions:
            return

        sanitized_sessions = []
        for s in sessions:
            sanitized_sessions.append({
                'id': s.get('id', str(uuid.uuid4())),
                'camera_id': s.get('camera_id'),
                'anonymous_track_id': s.get('anonymous_track_id'),
                'entry_time': s.get('entry_time'),
                'exit_time': s.get('exit_time'),
                'dwell_seconds': s.get('dwell_seconds', 0),
                'age_group': s.get('age_group', 'Unknown'),
                'age_confidence': s.get('age_confidence', 0.0),
                'entry_zone': s.get('entry_zone', 'General Area'),
                'exit_zone': s.get('exit_zone', 'General Area')
            })

        if self.use_supabase and self.client:
            try:
                self.client.table('visitor_sessions').insert(sanitized_sessions).execute()
                return
            except Exception as e:
                pass

        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            for s in sanitized_sessions:
                cursor.execute("""
                INSERT INTO visitor_sessions (id, camera_id, anonymous_track_id, entry_time, exit_time, dwell_seconds, age_group, age_confidence, entry_zone, exit_zone, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """, (
                    s['id'],
                    s['camera_id'],
                    s['anonymous_track_id'],
                    s['entry_time'],
                    s['exit_time'],
                    s['dwell_seconds'],
                    s['age_group'],
                    s['age_confidence'],
                    s['entry_zone'],
                    s['exit_zone']
                ))
            conn.commit()
            conn.close()
        except Exception:
            pass

    def get_visitor_sessions(self, limit: int = 100, camera_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if self.use_supabase and self.client:
            try:
                query = self.client.table('visitor_sessions').select('*').order('created_at', desc=True)
                if camera_id:
                    query = query.eq('camera_id', camera_id)
                res = query.limit(limit).execute()
                return res.data or []
            except Exception:
                pass

        try:
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
        except Exception:
            return []

    def save_heatmap_points(self, points: List[Dict[str, Any]]):
        if not points:
            return

        sanitized_pts = []
        for p in points:
            sanitized_pts.append({
                'id': p.get('id', str(uuid.uuid4())),
                'camera_id': p.get('camera_id'),
                'timestamp': p.get('timestamp'),
                'x': int(p.get('x', 0)),
                'y': int(p.get('y', 0)),
                'weight': float(p.get('weight', 1.0)),
                'zone_id': p.get('zone_id')
            })

        if self.use_supabase and self.client:
            try:
                for i in range(0, len(sanitized_pts), 100):
                    self.client.table('heatmap_points').insert(sanitized_pts[i:i+100]).execute()
                return
            except Exception:
                pass

        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            for p in sanitized_pts:
                cursor.execute("""
                INSERT INTO heatmap_points (id, camera_id, timestamp, x, y, weight, zone_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """, (
                    p['id'],
                    p['camera_id'],
                    p['timestamp'],
                    p['x'],
                    p['y'],
                    p['weight'],
                    p['zone_id']
                ))
            conn.commit()
            conn.close()
        except Exception:
            pass

    def get_heatmap_points(self, limit: int = 2000, camera_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if self.use_supabase and self.client:
            try:
                query = self.client.table('heatmap_points').select('*').order('created_at', desc=True)
                if camera_id:
                    query = query.eq('camera_id', camera_id)
                res = query.limit(limit).execute()
                return res.data or []
            except Exception:
                pass

        try:
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
        except Exception:
            return []

    def get_zones(self, camera_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if self.use_supabase and self.client:
            try:
                query = self.client.table('camera_zones').select('*')
                if camera_id:
                    query = query.eq('camera_id', camera_id)
                res = query.execute()
                return res.data or []
            except Exception:
                pass

        try:
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
                    except Exception:
                        pass
                rows.append(row_dict)
            conn.close()
            return rows
        except Exception:
            return []

    def get_cameras(self) -> List[Dict[str, Any]]:
        if self.use_supabase and self.client:
            try:
                res = self.client.table('cameras').select('*').execute()
                return res.data or []
            except Exception:
                pass

        try:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cameras")
            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()
            return rows
        except Exception:
            return []

    def upsert_camera(self, camera: Dict[str, Any]):
        if self.use_supabase and self.client:
            try:
                self.client.table('cameras').upsert(camera).execute()
                return
            except Exception:
                pass

        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO cameras (id, name, location, source_path, status, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                location=excluded.location,
                source_path=excluded.source_path,
                status=excluded.status
            """, (
                camera.get('id', str(uuid.uuid4())),
                camera.get('name', 'Camera'),
                camera.get('location', 'Store'),
                camera.get('source_path', ''),
                camera.get('status', 'LIVE')
            ))
            conn.commit()
            conn.close()
        except Exception:
            pass

db_service = DatabaseService()
