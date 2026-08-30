import React, { useEffect, useState } from 'react';
import { CameraStats } from '../types';
import { fetchCameras, startCamera, stopCamera } from '../services/supabase';
import {
  Play,
  Pause,
  Square,
  Maximize2,
  Minimize2,
  Flame,
  Layers,
  Settings,
  AlertCircle,
  Activity,
  User,
  Clock
} from 'lucide-react';

export const LiveMonitoring: React.FC = () => {
  const [cameras, setCameras] = useState<CameraStats[]>([]);
  const [fullscreenCam, setFullscreenCam] = useState<string | null>(null);
  const [showHeatmap, setShowHeatmap] = useState<Record<string, boolean>>({});
  const [frameRates, setFrameRates] = useState<Record<string, number>>({});

  const loadCameras = async () => {
    try {
      const data = await fetchCameras();
      setCameras(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadCameras();
    const interval = setInterval(loadCameras, 2000);
    return () => clearInterval(interval);
  }, []);

  const toggleStartStop = async (camId: string, currentStatus: string) => {
    if (currentStatus === 'LIVE') {
      await stopCamera(camId);
    } else {
      await startCamera(camId);
    }
    loadCameras();
  };

  const toggleHeatmap = (camId: string) => {
    setShowHeatmap(prev => ({ ...prev, [camId]: !prev[camId] }));
  };

  return (
    <div className="space-y-4">
      {/* Top Controls Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-dark-800 p-4 rounded-xl border border-slate-800">
        <div>
          <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-ping"></span>
            2×2 Real-Time CCTV Monitoring Grid
          </h2>
          <p className="text-xs text-slate-400">YOLO Person Detection, Persistent ByteTrack, Zone Analytics & Live Heatmaps</p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setFullscreenCam(null)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition ${
              fullscreenCam === null ? 'bg-cyan-500 text-white border-cyan-400' : 'bg-slate-800 text-slate-400 border-slate-700'
            }`}
          >
            2×2 Grid View
          </button>
        </div>
      </div>

      {/* 2×2 CCTV Grid Container */}
      <div className={`grid gap-4 ${fullscreenCam ? 'grid-cols-1' : 'grid-cols-1 lg:grid-cols-2'}`}>
        {cameras.map((cam, idx) => {
          if (fullscreenCam && fullscreenCam !== cam.camera_id) return null;

          const isLive = cam.status === 'LIVE';
          const isHeatmapActive = showHeatmap[cam.camera_id] || false;

          // Compute live MJPEG continuous stream URL from backend
          const streamUrl = isHeatmapActive
            ? `/api/heatmap/${cam.camera_id}/stream`
            : `/api/cameras/${cam.camera_id}/stream`;

          return (
            <div
              key={cam.camera_id}
              className={`bg-dark-800 border border-slate-800 rounded-2xl overflow-hidden flex flex-col shadow-xl transition-all ${
                fullscreenCam === cam.camera_id ? 'h-[75vh]' : 'h-[380px]'
              }`}
            >
              {/* Card Header */}
              <div className="bg-dark-800 px-4 py-2.5 border-b border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <span className={`w-2.5 h-2.5 rounded-full ${isLive ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`}></span>
                  <h3 className="font-bold text-sm text-slate-100">{cam.camera_name}</h3>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-slate-900 text-slate-400 font-mono">
                    {cam.fps || 25} FPS
                  </span>
                </div>

                <div className="flex items-center gap-1.5">
                  <button
                    onClick={() => toggleHeatmap(cam.camera_id)}
                    title="Toggle Thermal Movement Heatmap"
                    className={`p-1.5 rounded-lg text-xs font-semibold flex items-center gap-1 border transition ${
                      isHeatmapActive ? 'bg-amber-500/20 text-amber-400 border-amber-500/40' : 'bg-slate-900 text-slate-400 border-slate-700'
                    }`}
                  >
                    <Flame className="w-3.5 h-3.5" />
                    Heatmap
                  </button>

                  <button
                    onClick={() => toggleStartStop(cam.camera_id, cam.status)}
                    title={isLive ? "Pause Processing" : "Start Processing"}
                    className="p-1.5 rounded-lg bg-slate-900 text-slate-300 hover:text-white border border-slate-700 transition"
                  >
                    {isLive ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5 text-emerald-400" />}
                  </button>

                  <button
                    onClick={() => setFullscreenCam(fullscreenCam === cam.camera_id ? null : cam.camera_id)}
                    title="Toggle Fullscreen"
                    className="p-1.5 rounded-lg bg-slate-900 text-slate-300 hover:text-white border border-slate-700 transition"
                  >
                    {fullscreenCam === cam.camera_id ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              {/* Video Stream Frame View */}
              <div className="flex-1 bg-black relative overflow-hidden flex items-center justify-center">
                {isLive ? (
                  <img
                    src={streamUrl}
                    alt={cam.camera_name}
                    className="w-full h-full object-contain"
                    onError={(e) => {
                      // fallback if image fetch fails momentarily
                    }}
                  />
                ) : (
                  <div className="text-center p-6 space-y-2">
                    <AlertCircle className="w-10 h-10 text-slate-600 mx-auto" />
                    <p className="text-sm font-semibold text-slate-400">CAMERA STREAM PAUSED / STOPPED</p>
                    <button
                      onClick={() => startCamera(cam.camera_id)}
                      className="px-3 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-white text-xs font-bold"
                    >
                      Start Camera Processing
                    </button>
                  </div>
                )}

                {/* Overlaid OSD Live Stats Pill */}
                <div className="absolute bottom-3 left-3 bg-dark-900/80 backdrop-blur px-3 py-1.5 rounded-xl border border-slate-700/80 flex items-center gap-3 text-xs">
                  <div className="flex items-center gap-1 text-cyan-400 font-bold">
                    <User className="w-3.5 h-3.5" />
                    <span>People: {cam.people_count || 0}</span>
                  </div>
                  <div className="flex items-center gap-1 text-emerald-400 font-medium">
                    <span>In: {cam.entries || 0}</span>
                  </div>
                  <div className="flex items-center gap-1 text-rose-400 font-medium">
                    <span>Out: {cam.exits || 0}</span>
                  </div>
                  <div className="flex items-center gap-1 text-amber-400 font-medium">
                    <Clock className="w-3.5 h-3.5" />
                    <span>Dwell: {cam.avg_dwell_seconds || 0}s</span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
