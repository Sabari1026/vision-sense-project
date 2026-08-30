export type UserRole = 'admin' | 'manager' | 'viewer';

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
}

export interface CameraStats {
  camera_id: string;
  camera_name: string;
  status: 'LIVE' | 'PROCESSING' | 'PAUSED' | 'STOPPED' | 'ERROR' | 'NO SOURCE';
  fps: number;
  people_count: number;
  entries: number;
  exits: number;
  occupancy: number;
  avg_dwell_seconds: number;
  total_visitors: number;
}

export interface CameraZone {
  id: string;
  camera_id: string;
  name: string;
  zone_type: 'polygon' | 'line';
  polygon: number[][]; // [[x, y], ...]
}

export interface AnalyticsOverview {
  current_visitors: number;
  todays_visitors: number;
  current_occupancy: number;
  average_dwell_seconds: number;
  average_dwell_formatted: string;
  entries: number;
  exits: number;
  peak_occupancy: number;
  most_visited_zone: string;
}

export interface VisitorRecord {
  id: string;
  track_id: string;
  camera: string;
  entry_time: string;
  exit_time: string;
  dwell_duration: string;
  age_group: string;
  entry_zone: string;
  exit_zone: string;
}

export interface BusinessInsight {
  id: number;
  title: string;
  description: string;
  impact: string;
  type: 'opportunity' | 'trend' | 'positive' | 'info';
}

export interface SystemHealth {
  status: string;
  backend: string;
  database: string;
  database_type: string;
  database_latency_ms: number;
  yolo_model: string;
  gpu_available: boolean;
  gpu_name: string;
  cpu_usage_percent: number;
  memory_usage_percent: number;
  memory_used_gb: number;
  memory_total_gb: number;
  cameras: {
    camera_id: string;
    name: string;
    status: string;
    fps: number;
  }[];
}
