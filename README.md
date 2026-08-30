# VisionSense: AI CCTV Retail Analytics System

VisionSense is an enterprise-grade AI-powered CCTV retail analytics platform that converts standard CCTV or video streams into actionable operational intelligence.

The system uses **YOLO + OpenCV** for person detection, **ByteTrack / BoT-SORT** for persistent multi-object tracking, calculates occupancy and stay duration (dwell time), counts line-crossings for store entries and exits, evaluates polygon zone popularity, generates movement heatmaps, and persists structured metrics to **Supabase PostgreSQL**.

---

## 🚀 Core Features

- **2×2 CCTV Real-Time Monitoring Grid**: Live grid streaming 4 camera channels simultaneously with bounding box overlays, track IDs (`Person #101`), confidence %, movement trails, and zone boundaries.
- **Persistent Multi-Object Tracking**: Retains visitor tracking IDs across frames so visitors are counted once per visit instead of re-counted on every frame.
- **Entry & Exit Line Crossing**: Calculates real-time occupancy (`Current Occupancy = Total Entries - Total Exits`).
- **Polygon Zone Analytics**: Canvas-based interactive zone drawer for custom store areas (Entrance, Apparel, Electronics, Billing Desk).
- **Thermal Movement Heatmaps**: Accumulates 2D trajectory density overlays (Low to High traffic) over CCTV camera frames.
- **CV Age Group Estimation**: Automated computer-vision classification into `Child`, `Young Adult`, `Adult`, and `Senior` brackets with disclaimers.
- **Privacy-Conscious Architecture**: Tracks anonymous session IDs (`#101`, `#102`) only. **No face recognition** or facial embeddings are stored.
- **Supabase PostgreSQL Integration**: Fully connected database schema with RLS security policies, time-series snapshots, and fallback local database.
- **Automated Analytics & Reporting**: Interactive Recharts, daily/weekly/monthly report generator with CSV and JSON exports.
- **System Health Diagnostics**: Monitors CPU %, RAM Memory %, GPU acceleration, camera worker FPS, and database latency.

---

## 🏗️ Architecture

```
 ┌────────────────────────────────────────────────────────────────────────┐
 │                              REACT FRONTEND                            │
 │  - 2x2 CCTV Monitoring Grid (WebSocket / MJPEG live feed streaming)    │
 │  - Real-time Dashboard KPIs, Interactive Recharts & Heatmap Overlays   │
 │  - Visual Polygon Zone Editor (Canvas-based)                           │
 │  - Supabase Auth Integration & Role-based Routing (Admin/Manager/Viewer)│
 └───────────────────▲────────────────────────────────┬───────────────────┘
                     │ REST & WebSocket               │ Supabase Client / Auth
                     ▼                                ▼
 ┌───────────────────────────────────────┐  ┌─────────────────────────────┐
 │            FASTAPI BACKEND            │  │          SUPABASE           │
 │  - Camera Worker Process Manager      │  │  - Auth (Profiles & Roles)  │
 │  - Video Source Manager & Uploads     │  │  - PostgreSQL Database      │
 │  - Aggregated REST APIs & Health      │  │  - RLS Security Policies    │
 └───────────────────▲───────────────────┘  │  - Realtime Engine          │
                     │ Frame Stream /           └──────────────▲──────────────┘
                     │ In-memory Buffer                        │ Batch Flushes
 ┌───────────────────┴─────────────────────────────────────────┴──────────────┐
 │                        VISION ENGINE (PYTHON CV)                           │
 │  - VideoCapture (File / Future RTSP abstraction)                           │
 │  - YOLO Detection (`person` class) + Persistent ByteTrack / BoT-SORT      │
 │  - Entry/Exit Line-Crossing Math & Visitor Session Manager                 │
 │  - Polygon Zone Containment (`cv2.pointPolygonTest`)                       │
 │  - Heatmap Accumulator Array & OpenCV Color Map Overlay                    │
 │  - Optional CV Age Group Estimator & Buffer DB Flusher                     │
 └────────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Tech Stack

- **Computer Vision & Backend**: Python 3.10+, OpenCV, Ultralytics YOLO (v8 / v11), ByteTrack / BoT-SORT, NumPy, Pandas, FastAPI, Uvicorn, PyTorch, PyYAML, WebSockets.
- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, Lucide Icons, Recharts, Supabase JS SDK.
- **Database & Auth**: Supabase PostgreSQL, Row Level Security (RLS), Local SQLite fallback.

---

## 🛠️ Quick Start & Installation

### 1. Clone & Setup Environment

```bash
git clone https://github.com/your-org/vision-sense.git
cd "vision sense project"
```

### 2. Python Backend Setup

```bash
# Create virtual environment (optional)
python -m venv venv
venv\Scripts\activate   # On Windows

# Install Python requirements
pip install -r backend/requirements.txt
```

### 3. Generate Synthetic CCTV Demo Videos

If you don't have video files ready in `/videos`, run our synthetic generator to create 4 high-definition retail CCTV MP4 files:

```bash
python scripts/generate_sample_videos.py
```

This creates:
- `videos/camera1.mp4` (Main Entrance)
- `videos/camera2.mp4` (Apparel Racks)
- `videos/camera3.mp4` (Electronics Hub)
- `videos/camera4.mp4` (Checkout Counters)

### 4. Database Setup (Supabase)

1. Open your Supabase Project Dashboard.
2. Go to **SQL Editor** and run `supabase/schema.sql` to create all required tables, indexes, and RLS policies.
3. Run `supabase/seed.sql` to populate default cameras and zones.
4. Copy credentials to `.env`:

```env
SUPABASE_URL=https://your-supabase-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
```

*(Note: If Supabase credentials are left as placeholders, VisionSense automatically operates in local SQLite mode for seamless offline development.)*

---

## 🚀 Running the System

### Start FastAPI Backend Engine

```bash
python -m uvicorn backend.app.main:app --reload --port 8000
```
Backend API docs will be available at: `http://localhost:8000/docs`

### Start React Frontend Dashboard

```bash
cd frontend
npm install
npm run dev
```
Open your browser at: `http://localhost:3000`

---

## 🐳 Docker Deployment

To run VisionSense using Docker Compose:

```bash
docker-compose up --build
```

---

## 🔒 Privacy Disclaimer

VisionSense operates strictly on anonymous computer-vision tracking for retail operational analytics. It does not perform facial recognition or store facial biometric embeddings. Temporary track IDs (`#101`, `#102`) exist only within active analytics sessions. Age categories are automated estimates. Use in accordance with local privacy laws.
