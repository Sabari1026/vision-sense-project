import React, { useState, useEffect } from 'react';
import { Flame, Filter, Eye, Layers, Camera, Info } from 'lucide-react';
import { fetchCameras, API_BASE_URL } from '../services/supabase';
import { CameraStats } from '../types';

export const HeatmapsPage: React.FC = () => {
  const [cameras, setCameras] = useState<CameraStats[]>([]);
  const [selectedCam, setSelectedCam] = useState<string>('');
  const [heatmapMode, setHeatmapMode] = useState<'traffic' | 'dwell' | 'occupancy'>('traffic');

  useEffect(() => {
    fetchCameras().then((data) => {
      setCameras(data);
      if (data.length > 0 && !selectedCam) {
        setSelectedCam(data[0].camera_id);
      }
    }).catch(console.error);
  }, []);

  const activeCamera = cameras.find((c) => c.camera_id === selectedCam) || cameras[0];

  return (
    <div className="space-y-6">
      {/* Top Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-dark-800 p-4 rounded-xl border border-slate-800">
        <div className="flex items-center gap-2">
          <Flame className="w-5 h-5 text-amber-400" />
          <h2 className="font-bold text-base text-slate-100">Customer Movement Heatmap Engine</h2>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Mode Selector */}
          <div className="flex bg-slate-900 p-1 rounded-lg border border-slate-700">
            {(['traffic', 'dwell', 'occupancy'] as const).map((m) => (
              <button
                key={m}
                onClick={() => setHeatmapMode(m)}
                className={`px-3 py-1 text-xs capitalize rounded font-semibold transition ${
                  heatmapMode === m ? 'bg-amber-500 text-white shadow-md' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {m}
              </button>
            ))}
          </div>

          <select
            value={selectedCam}
            onChange={(e) => setSelectedCam(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
          >
            {cameras.map((c) => (
              <option key={c.camera_id} value={c.camera_id}>
                {c.camera_name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Heatmap Main Frame Display */}
      <div className="bg-dark-800 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">
              {heatmapMode.toUpperCase()} HEATMAP OVERLAY ({activeCamera?.camera_name || 'LIVE'})
            </span>
            <span className="text-xs text-slate-400">
              Visitors: {activeCamera?.total_visitors || 0} | Active Density
            </span>
          </div>

          {/* Color Scale Legend */}
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span>Low Traffic</span>
            <div className="w-32 h-3 rounded-full bg-gradient-to-r from-blue-600 via-green-500 via-yellow-400 to-red-600"></div>
            <span>High Dwell Traffic</span>
          </div>
        </div>

        {/* Heatmap Frame Container */}
        <div className="w-full h-[520px] bg-black rounded-xl overflow-hidden relative flex items-center justify-center border border-slate-800">
          {selectedCam ? (
            <img
              src={`${API_BASE_URL}/heatmap/${selectedCam}/stream`}
              alt="Customer Movement Heatmap"
              className="w-full h-full object-contain"
            />
          ) : (
            <div className="text-slate-400 text-sm font-semibold">INITIALIZING HEATMAP STREAM...</div>
          )}

          {/* Legend Banner Overlay */}
          <div className="absolute top-4 left-4 bg-dark-900/80 backdrop-blur p-3 rounded-xl border border-slate-700 max-w-xs space-y-1">
            <p className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
              <Info className="w-4 h-4 text-amber-400" />
              Thermal Trajectory Density
            </p>
            <p className="text-[11px] text-slate-400">
              Red & warm areas accumulate customer dwell & movement density. Green/blue areas represent passage paths.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
