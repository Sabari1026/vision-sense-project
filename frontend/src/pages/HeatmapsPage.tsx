import React, { useState, useEffect } from 'react';
import { Flame, Filter, Eye, Layers, Camera, Info, Download, Calendar, Sparkles } from 'lucide-react';
import { fetchCameras, API_BASE_URL } from '../services/supabase';
import { CameraStats } from '../types';

export const HeatmapsPage: React.FC = () => {
  const [cameras, setCameras] = useState<CameraStats[]>([]);
  const [selectedCam, setSelectedCam] = useState<string>('combined');
  const [timeRange, setTimeRange] = useState<'session' | 'today' | '7days' | '30days'>('today');

  useEffect(() => {
    fetchCameras().then((data) => {
      setCameras(data);
    }).catch(console.error);
  }, []);

  const isCombined = selectedCam === 'combined';
  const activeCamera = cameras.find((c) => c.camera_id === selectedCam);

  const streamSrc = isCombined
    ? `${API_BASE_URL}/heatmap/combined/stream`
    : `${API_BASE_URL}/heatmap/${selectedCam}/stream`;

  return (
    <div className="space-y-6">
      {/* Top Controls Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-dark-800 p-5 rounded-2xl border border-slate-800 shadow-xl">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center border border-amber-500/20">
            <Flame className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-bold text-base text-slate-100 flex items-center gap-2">
              Customer Movement & Thermal Heatmap Engine
              <Sparkles className="w-4 h-4 text-amber-400" />
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Accumulated 2D pedestrian trajectory density overlays over CCTV camera views.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Time Range Filter */}
          <div className="flex bg-slate-900 p-1 rounded-xl border border-slate-800 text-xs">
            {[
              { id: 'session', label: 'Live Session' },
              { id: 'today', label: 'Today' },
              { id: '7days', label: 'Last 7 Days' },
              { id: '30days', label: 'Last 30 Days' }
            ].map((t) => (
              <button
                key={t.id}
                onClick={() => setTimeRange(t.id as any)}
                className={`px-3 py-1.5 rounded-lg font-semibold transition ${
                  timeRange === t.id ? 'bg-amber-500 text-white shadow-md' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* Camera Selector Dropdown */}
          <select
            value={selectedCam}
            onChange={(e) => setSelectedCam(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-xl px-4 py-2 text-xs text-slate-200 focus:outline-none focus:border-amber-500 font-semibold"
          >
            <option value="combined">🏬 Combined Store 2×2 Heatmap</option>
            {cameras.map((c) => (
              <option key={c.camera_id} value={c.camera_id}>
                📹 {c.camera_name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Heatmap Display Viewport */}
      <div className="bg-dark-800 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">
              {isCombined ? 'COMBINED 2×2 STORE SHOWROOM HEATMAP' : `${activeCamera?.camera_name || 'CAMERA'} THERMAL OVERLAY`}
            </span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-amber-500/10 text-amber-400 font-semibold border border-amber-500/20">
              Live Density Accumulation
            </span>
          </div>

          {/* Color Scale Legend */}
          <div className="flex items-center gap-2.5 text-xs text-slate-400">
            <span>Low Traffic</span>
            <div className="w-36 h-3 rounded-full bg-gradient-to-r from-blue-600 via-cyan-400 via-emerald-400 via-amber-400 to-rose-600 shadow-inner"></div>
            <span>High Dwell Traffic</span>
          </div>
        </div>

        {/* Heatmap Frame Container */}
        <div className="w-full h-[560px] bg-black rounded-2xl overflow-hidden relative flex items-center justify-center border border-slate-800 shadow-2xl">
          <img
            key={streamSrc}
            src={streamSrc}
            alt="Customer Movement Heatmap"
            className="w-full h-full object-contain select-none"
          />

          {/* Info Badge */}
          <div className="absolute top-4 left-4 bg-dark-900/90 backdrop-blur-md p-3.5 rounded-xl border border-slate-700/80 max-w-sm space-y-1.5 shadow-xl">
            <p className="text-xs font-bold text-slate-200 flex items-center gap-2">
              <Info className="w-4 h-4 text-amber-400" />
              Thermal Density Analytics ({timeRange.toUpperCase()})
            </p>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Warm red & orange zones highlight high shopper interaction and dwell clusters. Cool blue paths indicate swift walkthrough corridors.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
