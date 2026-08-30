-- VisionSense Database Seed Data

-- Clear existing seed data safely
TRUNCATE TABLE public.camera_zones CASCADE;
TRUNCATE TABLE public.cameras CASCADE;

-- Insert 4 Default Cameras
INSERT INTO public.cameras (id, name, location, source_type, source_path, status, resolution, fps) VALUES
('11111111-1111-1111-1111-111111111111', 'Camera 01 - Main Entrance', 'Main Entrance', 'file', 'videos/camera1.mp4', 'LIVE', '1280x720', 25),
('22222222-2222-2222-2222-222222222222', 'Camera 02 - Clothing Section', 'Clothing Section', 'file', 'videos/camera2.mp4', 'LIVE', '1280x720', 25),
('33333333-3333-3333-3333-333333333333', 'Camera 03 - Electronics Hub', 'Electronics Section', 'file', 'videos/camera3.mp4', 'LIVE', '1280x720', 25),
('44444444-4444-4444-4444-444444444444', 'Camera 04 - Checkout Counters', 'Billing Area', 'file', 'videos/camera4.mp4', 'LIVE', '1280x720', 25);

-- Insert Default Zones for Cameras
INSERT INTO public.camera_zones (id, camera_id, name, zone_type, polygon) VALUES
('a1111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111', 'Zone A - Entrance Door', 'polygon', '[[100, 100], [400, 100], [400, 400], [100, 400]]'),
('a2222222-2222-2222-2222-222222222222', '22222222-2222-2222-2222-222222222222', 'Zone B - Apparel Racks', 'polygon', '[[200, 150], [600, 150], [600, 500], [200, 500]]'),
('a3333333-3333-3333-3333-333333333333', '33333333-3333-3333-3333-333333333333', 'Zone C - Electronics Display', 'polygon', '[[150, 200], [550, 200], [550, 600], [150, 600]]'),
('a4444444-4444-4444-4444-444444444444', '44444444-4444-4444-4444-444444444444', 'Zone D - Billing Desk', 'polygon', '[[300, 100], [700, 100], [700, 400], [300, 400]]');
