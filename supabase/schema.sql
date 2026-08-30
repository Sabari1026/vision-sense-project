-- VisionSense Supabase PostgreSQL Database Schema
-- Run this migration script in the Supabase SQL Editor.

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Profiles Table
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL CHECK (role IN ('admin', 'manager', 'viewer')) DEFAULT 'viewer',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Cameras Table
CREATE TABLE IF NOT EXISTS public.cameras (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    location TEXT NOT NULL,
    source_type TEXT NOT NULL DEFAULT 'file',
    source_path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'STOPPED', -- LIVE, PROCESSING, PAUSED, STOPPED, ERROR, NO SOURCE
    resolution TEXT DEFAULT '1280x720',
    fps INTEGER DEFAULT 25,
    created_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Camera Zones Table
CREATE TABLE IF NOT EXISTS public.camera_zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_id UUID NOT NULL REFERENCES public.cameras(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    zone_type TEXT NOT NULL DEFAULT 'polygon', -- polygon, line
    polygon JSONB NOT NULL, -- list of [x, y] coordinates
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. Visitor Sessions Table
CREATE TABLE IF NOT EXISTS public.visitor_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_id UUID NOT NULL REFERENCES public.cameras(id) ON DELETE CASCADE,
    anonymous_track_id INTEGER NOT NULL,
    entry_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    exit_time TIMESTAMPTZ,
    dwell_seconds INTEGER DEFAULT 0,
    age_group TEXT DEFAULT 'Unknown', -- Child, Young Adult, Adult, Senior, Unknown
    age_confidence FLOAT DEFAULT 0.0,
    entry_zone TEXT,
    exit_zone TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5. Detection Events Table (Sampled 1-2 sec per track)
CREATE TABLE IF NOT EXISTS public.detection_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_id UUID NOT NULL REFERENCES public.cameras(id) ON DELETE CASCADE,
    session_id UUID REFERENCES public.visitor_sessions(id) ON DELETE CASCADE,
    track_id INTEGER NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    center_x INTEGER NOT NULL,
    center_y INTEGER NOT NULL,
    bbox_x INTEGER NOT NULL,
    bbox_y INTEGER NOT NULL,
    bbox_width INTEGER NOT NULL,
    bbox_height INTEGER NOT NULL,
    confidence FLOAT NOT NULL,
    zone_id UUID REFERENCES public.camera_zones(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6. Zone Visits Table
CREATE TABLE IF NOT EXISTS public.zone_visits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES public.visitor_sessions(id) ON DELETE CASCADE,
    camera_id UUID NOT NULL REFERENCES public.cameras(id) ON DELETE CASCADE,
    zone_id UUID NOT NULL REFERENCES public.camera_zones(id) ON DELETE CASCADE,
    entered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    exited_at TIMESTAMPTZ,
    duration_seconds INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 7. Analytics Snapshots Table (Aggregated periodically)
CREATE TABLE IF NOT EXISTS public.analytics_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_id UUID NOT NULL REFERENCES public.cameras(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    people_count INTEGER DEFAULT 0,
    entries INTEGER DEFAULT 0,
    exits INTEGER DEFAULT 0,
    occupancy INTEGER DEFAULT 0,
    average_dwell_seconds FLOAT DEFAULT 0.0,
    total_visitors INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 8. Heatmap Points Table
CREATE TABLE IF NOT EXISTS public.heatmap_points (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_id UUID NOT NULL REFERENCES public.cameras(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    x INTEGER NOT NULL,
    y INTEGER NOT NULL,
    weight FLOAT DEFAULT 1.0,
    zone_id UUID REFERENCES public.camera_zones(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 9. Reports Table
CREATE TABLE IF NOT EXISTS public.reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    report_type TEXT NOT NULL, -- daily, weekly, monthly
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    report_data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for maximum query performance
CREATE INDEX IF NOT EXISTS idx_detection_camera_time ON public.detection_events(camera_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_sessions_camera ON public.visitor_sessions(camera_id);
CREATE INDEX IF NOT EXISTS idx_sessions_entry_time ON public.visitor_sessions(entry_time);
CREATE INDEX IF NOT EXISTS idx_heatmap_camera_time ON public.heatmap_points(camera_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_snapshots_camera_time ON public.analytics_snapshots(camera_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_zone_visits_session ON public.zone_visits(session_id);

-- Enable Row Level Security (RLS) on all tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cameras ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.camera_zones ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.visitor_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.detection_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.zone_visits ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analytics_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.heatmap_points ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;

-- RLS Policies for authenticated users to read data
CREATE POLICY "Allow public read on cameras" ON public.cameras FOR SELECT USING (true);
CREATE POLICY "Allow public read on camera_zones" ON public.camera_zones FOR SELECT USING (true);
CREATE POLICY "Allow public read on visitor_sessions" ON public.visitor_sessions FOR SELECT USING (true);
CREATE POLICY "Allow public read on detection_events" ON public.detection_events FOR SELECT USING (true);
CREATE POLICY "Allow public read on zone_visits" ON public.zone_visits FOR SELECT USING (true);
CREATE POLICY "Allow public read on analytics_snapshots" ON public.analytics_snapshots FOR SELECT USING (true);
CREATE POLICY "Allow public read on heatmap_points" ON public.heatmap_points FOR SELECT USING (true);
CREATE POLICY "Allow public read on reports" ON public.reports FOR SELECT USING (true);
CREATE POLICY "Allow users to view own profile" ON public.profiles FOR SELECT USING (true);

-- Allow authenticated service role or backend worker to write/insert analytics data
CREATE POLICY "Allow insert/update/delete for authenticated service" ON public.cameras FOR ALL USING (true);
CREATE POLICY "Allow insert/update/delete for camera_zones" ON public.camera_zones FOR ALL USING (true);
CREATE POLICY "Allow insert/update/delete for visitor_sessions" ON public.visitor_sessions FOR ALL USING (true);
CREATE POLICY "Allow insert/update/delete for detection_events" ON public.detection_events FOR ALL USING (true);
CREATE POLICY "Allow insert/update/delete for zone_visits" ON public.zone_visits FOR ALL USING (true);
CREATE POLICY "Allow insert/update/delete for analytics_snapshots" ON public.analytics_snapshots FOR ALL USING (true);
CREATE POLICY "Allow insert/update/delete for heatmap_points" ON public.heatmap_points FOR ALL USING (true);
CREATE POLICY "Allow insert/update/delete for reports" ON public.reports FOR ALL USING (true);
