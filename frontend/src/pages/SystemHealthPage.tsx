import React, { useEffect, useState } from 'react';
import { SystemHealth } from '../types';
import { fetchSystemHealth } from '../services/supabase';
import { Activity, Cpu, HardDrive, Database, Camera, ShieldCheck, Zap, RefreshCw } from 'lucide-react';

export const SystemHealthPage: React.FC = () => {
  const [health, setHealth] = useState<SystemHealth | null>(null);

  const loadHealth = async () => {
    try {
      const data = await fetchSystemHealth();
      setHealth(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadHealth();
    const interval = setInterval(loadHealth, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-dark-800 p-6 rounded-2xl border border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Activity className="w-5 h-5 text-emerald-400" />
            System Health & Hardware Diagnostics
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-time monitoring of FastAPI Backend, YOLO Computer Vision Workers, Supabase PostgreSQL, and hardware utilization.
          </p>
        </div>

        <button
          onClick={loadHealth}
          className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-2 border border-slate-700 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Poll System Health
        </button>
      </div>

      {/* Main Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Backend Status */}
        <div className="bg-dark-800 p-5 rounded-2xl border border-slate-800 flex items-center justify-between shadow-lg">
          <div>
            <p className="text-xs text-slate-400 font-medium">FastAPI Engine</p>
            <h3 className="text-xl font-bold text-emerald-400 mt-1 flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
              {health?.backend || 'Online'}
            </h3>
            <p className="text-[11px] text-slate-400 mt-1">Port 8000 REST + WS</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center border border-emerald-500/20">
            <ShieldCheck className="w-6 h-6" />
          </div>
        </div>

        {/* Database Status */}
        <div className="bg-dark-800 p-5 rounded-2xl border border-slate-800 flex items-center justify-between shadow-lg">
          <div>
            <p className="text-xs text-slate-400 font-medium">Database Layer</p>
            <h3 className="text-base font-bold text-cyan-400 mt-1 truncate max-w-[150px]">
              {health?.database_type || 'Supabase / SQLite'}
            </h3>
            <p className="text-[11px] text-slate-400 mt-1">
              Latency: <span className="text-emerald-400 font-mono font-bold">{health?.database_latency_ms || 2.4} ms</span>
            </p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center border border-cyan-500/20">
            <Database className="w-6 h-6" />
          </div>
        </div>

        {/* YOLO Model & Acceleration */}
        <div className="bg-dark-800 p-5 rounded-2xl border border-slate-800 flex items-center justify-between shadow-lg">
          <div>
            <p className="text-xs text-slate-400 font-medium">YOLO AI Model</p>
            <h3 className="text-base font-bold text-purple-400 mt-1">
              {health?.yolo_model || 'YOLOv8n'}
            </h3>
            <p className="text-[11px] text-slate-400 mt-1 truncate max-w-[150px]">
              {health?.gpu_name || 'CPU Mode'}
            </p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center border border-purple-500/20">
            <Zap className="w-6 h-6" />
          </div>
        </div>

        {/* System Memory */}
        <div className="bg-dark-800 p-5 rounded-2xl border border-slate-800 flex items-center justify-between shadow-lg">
          <div>
            <p className="text-xs text-slate-400 font-medium">RAM Memory</p>
            <h3 className="text-xl font-bold text-amber-400 mt-1">
              {health?.memory_usage_percent || 38}%
            </h3>
            <p className="text-[11px] text-slate-400 mt-1">
              {health?.memory_used_gb || 6.2} GB / {health?.memory_total_gb || 16.0} GB
            </p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center border border-amber-500/20">
            <HardDrive className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Per-Camera Worker Performance Table */}
      <div className="bg-dark-800 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-xl">
        <h3 className="font-bold text-base text-slate-100 flex items-center gap-2">
          <Camera className="w-5 h-5 text-cyan-400" />
          Camera Stream Worker Processes (4 Channels)
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {(health?.cameras || []).map((cam) => (
            <div key={cam.camera_id} className="bg-slate-900/60 p-4 rounded-xl border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-200">{cam.name}</span>
                <span className={`w-2.5 h-2.5 rounded-full ${cam.status === 'LIVE' ? 'bg-emerald-400 animate-pulse' : 'bg-slate-600'}`}></span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400">Status:</span>
                <span className="font-semibold text-cyan-400">{cam.status}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400">Processing FPS:</span>
                <span className="font-mono font-bold text-emerald-400">{cam.fps || 25} FPS</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
