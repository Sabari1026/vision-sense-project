import time
from typing import Dict, Any, List, Optional, Tuple

class DwellTimeManager:
    """Tracks visitor stay durations, zone visits, and manages active session timeouts."""

    def __init__(self, camera_id: str, lost_timeout_seconds: float = 5.0):
        self.camera_id = camera_id
        self.lost_timeout_seconds = lost_timeout_seconds
        
        # Active sessions: track_id -> session dict
        self.active_sessions: Dict[int, Dict[str, Any]] = {}
        # Completed sessions ready for DB insert: list of closed session dicts
        self.closed_sessions: List[Dict[str, Any]] = []
        # Active zone visits: (track_id, zone_id) -> start_time
        self.active_zone_visits: Dict[Tuple[int, str], float] = {}
        # Closed zone visits ready for DB insert
        self.closed_zone_visits: List[Dict[str, Any]] = []

    def update_track(self, track_id: int, current_timestamp: float, zone_info: Optional[Dict[str, Any]] = None, age_group: str = "Unknown", age_conf: float = 0.0) -> Dict[str, Any]:
        """Updates timestamp for a track ID and returns active session data."""
        if track_id not in self.active_sessions:
            # Create new visitor session
            session = {
                'camera_id': self.camera_id,
                'anonymous_track_id': track_id,
                'entry_time': current_timestamp,
                'last_seen': current_timestamp,
                'exit_time': None,
                'dwell_seconds': 0,
                'age_group': age_group,
                'age_confidence': age_conf,
                'entry_zone': zone_info['name'] if zone_info else "General Area",
                'exit_zone': None,
                'current_zone': zone_info['name'] if zone_info else None
            }
            self.active_sessions[track_id] = session
        else:
            session = self.active_sessions[track_id]
            session['last_seen'] = current_timestamp
            session['dwell_seconds'] = int(current_timestamp - session['entry_time'])
            if zone_info:
                session['current_zone'] = zone_info['name']

        # Handle Zone Visit Tracking
        if zone_info:
            zone_id = zone_info['id']
            key = (track_id, zone_id)
            if key not in self.active_zone_visits:
                self.active_zone_visits[key] = current_timestamp

        return self.active_sessions[track_id]

    def cleanup_lost_tracks(self, current_timestamp: float) -> List[Dict[str, Any]]:
        """Closes sessions for tracks missing longer than lost_timeout_seconds."""
        recently_closed = []

        for track_id, session in list(self.active_sessions.items()):
            time_since_seen = current_timestamp - session['last_seen']
            if time_since_seen > self.lost_timeout_seconds:
                # Close session
                session['exit_time'] = session['last_seen']
                session['dwell_seconds'] = max(1, int(session['exit_time'] - session['entry_time']))
                session['exit_zone'] = session.get('current_zone') or "General Area"

                self.closed_sessions.append(session)
                recently_closed.append(session)
                del self.active_sessions[track_id]

                # Close active zone visits for this track
                for (t_id, z_id), start_time in list(self.active_zone_visits.items()):
                    if t_id == track_id:
                        dur = max(1, int(session['exit_time'] - start_time))
                        self.closed_zone_visits.append({
                            'track_id': t_id,
                            'camera_id': self.camera_id,
                            'zone_id': z_id,
                            'entered_at': start_time,
                            'exited_at': session['exit_time'],
                            'duration_seconds': dur
                        })
                        del self.active_zone_visits[(t_id, z_id)]

        return recently_closed

    def force_close_all(self, current_timestamp: float) -> List[Dict[str, Any]]:
        """Force closes all currently active sessions upon EOF/completion."""
        recently_closed = []
        for track_id, session in list(self.active_sessions.items()):
            session['exit_time'] = session['last_seen']
            session['dwell_seconds'] = max(1, int(session['exit_time'] - session['entry_time']))
            session['exit_zone'] = session.get('current_zone') or "General Area"

            self.closed_sessions.append(session)
            recently_closed.append(session)
            del self.active_sessions[track_id]

            for (t_id, z_id), start_time in list(self.active_zone_visits.items()):
                if t_id == track_id:
                    dur = max(1, int(session['exit_time'] - start_time))
                    self.closed_zone_visits.append({
                        'track_id': t_id,
                        'camera_id': self.camera_id,
                        'zone_id': z_id,
                        'entered_at': start_time,
                        'exited_at': session['exit_time'],
                        'duration_seconds': dur
                    })
                    del self.active_zone_visits[(t_id, z_id)]

        return recently_closed

    def get_average_dwell_seconds(self) -> float:
        total_dwell = sum(s['dwell_seconds'] for s in self.active_sessions.values())
        count = len(self.active_sessions)
        return round(total_dwell / count, 1) if count > 0 else 0.0

    def pop_closed_sessions(self) -> List[Dict[str, Any]]:
        sessions = self.closed_sessions.copy()
        self.closed_sessions.clear()
        return sessions

    def pop_closed_zone_visits(self) -> List[Dict[str, Any]]:
        visits = self.closed_zone_visits.copy()
        self.closed_zone_visits.clear()
        return visits
