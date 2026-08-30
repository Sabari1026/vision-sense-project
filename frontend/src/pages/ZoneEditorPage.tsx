import React, { useState, useRef, useEffect } from 'react';
import { MapPin, Save, Trash2, Plus, RefreshCw, CheckCircle } from 'lucide-react';
import { CameraZone } from '../types';
import { API_BASE_URL } from '../services/supabase';

export const ZoneEditorPage: React.FC = () => {
  const [selectedCam, setSelectedCam] = useState('11111111-1111-1111-1111-111111111111');
  const [zoneName, setZoneName] = useState('New Custom Zone');
  const [points, setPoints] = useState<number[][]>([]);
  const [savedZones, setSavedZones] = useState<CameraZone[]>([
    {
      id: 'a1111111',
      camera_id: '11111111-1111-1111-1111-111111111111',
      name: 'Zone A - Entrance Door',
      zone_type: 'polygon',
      polygon: [[100, 100], [400, 100], [400, 400], [100, 400]]
    }
  ]);
  const [message, setMessage] = useState('');

  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const imageSrc = `${API_BASE_URL}/cameras/${selectedCam}/frame?t=${Date.now()}`;

  useEffect(() => {
    drawCanvas();
  }, [points, selectedCam, savedZones]);

  const drawCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new Image();
    img.src = imageSrc;
    img.onload = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

      // Draw existing saved zones for this camera
      savedZones.forEach((z) => {
        if (z.polygon && z.polygon.length >= 3) {
          ctx.beginPath();
          ctx.moveTo(z.polygon[0][0], z.polygon[0][1]);
          z.polygon.forEach(pt => ctx.lineTo(pt[0], pt[1]));
          ctx.closePath();
          ctx.fillStyle = 'rgba(0, 153, 255, 0.25)';
          ctx.fill();
          ctx.strokeStyle = '#0099ff';
          ctx.lineWidth = 2;
          ctx.stroke();

          // Label
          ctx.fillStyle = '#ffffff';
          ctx.font = 'bold 12px Inter, sans-serif';
          ctx.fillText(z.name, z.polygon[0][0] + 10, z.polygon[0][1] + 20);
        }
      });

      // Draw current active drawing polygon
      if (points.length > 0) {
        ctx.beginPath();
        ctx.moveTo(points[0][0], points[0][1]);
        points.forEach(pt => ctx.lineTo(pt[0], pt[1]));
        if (points.length >= 3) ctx.closePath();

        ctx.fillStyle = 'rgba(16, 185, 129, 0.35)';
        ctx.fill();
        ctx.strokeStyle = '#10b981';
        ctx.lineWidth = 3;
        ctx.stroke();

        // Draw point vertices
        points.forEach(([x, y]) => {
          ctx.beginPath();
          ctx.arc(x, y, 6, 0, 2 * Math.PI);
          ctx.fillStyle = '#10b981';
          ctx.fill();
          ctx.strokeStyle = '#ffffff';
          ctx.lineWidth = 2;
          ctx.stroke();
        });
      }
    };
  };

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = Math.round((e.clientX - rect.left) * (canvas.width / rect.width));
    const y = Math.round((e.clientY - rect.top) * (canvas.height / rect.height));

    setPoints(prev => [...prev, [x, y]]);
  };

  const clearCurrent = () => {
    setPoints([]);
  };

  const saveZone = () => {
    if (points.length < 3) {
      alert("A polygon zone requires at least 3 points. Click on the camera canvas to add points.");
      return;
    }

    const newZone: CameraZone = {
      id: `z-${Date.now()}`,
      camera_id: selectedCam,
      name: zoneName,
      zone_type: 'polygon',
      polygon: points
    };

    setSavedZones(prev => [...prev, newZone]);
    setPoints([]);
    setMessage(`Zone "${zoneName}" saved successfully!`);
    setTimeout(() => setMessage(''), 3000);
  };

  return (
    <div className="space-y-6">
      {/* Controls Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-dark-800 p-4 rounded-xl border border-slate-800">
        <div className="flex items-center gap-2">
          <MapPin className="w-5 h-5 text-cyan-400" />
          <h2 className="font-bold text-base text-slate-100">Visual Camera Polygon Zone Drawer</h2>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <select
            value={selectedCam}
            onChange={(e) => {
              setSelectedCam(e.target.value);
              setPoints([]);
            }}
            className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            <option value="11111111-1111-1111-1111-111111111111">Camera 01 - Main Entrance</option>
            <option value="22222222-2222-2222-2222-222222222222">Camera 02 - Apparel Section</option>
            <option value="33333333-3333-3333-3333-333333333333">Camera 03 - Electronics Hub</option>
            <option value="44444444-4444-4444-4444-444444444444">Camera 04 - Checkout Counters</option>
          </select>

          <input
            type="text"
            value={zoneName}
            onChange={(e) => setZoneName(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-cyan-500 w-44"
            placeholder="Zone Name"
          />

          <button
            onClick={clearCurrent}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold flex items-center gap-1 border border-slate-700"
          >
            <Trash2 className="w-3.5 h-3.5 text-rose-400" />
            Clear Current Points ({points.length})
          </button>

          <button
            onClick={saveZone}
            className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold flex items-center gap-1.5 shadow-md shadow-emerald-500/20"
          >
            <Save className="w-3.5 h-3.5" />
            Save Zone Polygon
          </button>
        </div>
      </div>

      {message && (
        <div className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 px-4 py-2.5 rounded-xl text-xs flex items-center gap-2 font-medium">
          <CheckCircle className="w-4 h-4" />
          {message}
        </div>
      )}

      {/* Canvas Drawing Area */}
      <div className="bg-dark-800 border border-slate-800 rounded-2xl p-6 space-y-3 shadow-xl">
        <div className="flex items-center justify-between">
          <p className="text-xs text-slate-400">
            Click points directly on the camera canvas below to draw custom polygon boundaries. At least 3 points required.
          </p>
          <span className="text-xs font-mono font-semibold text-emerald-400">Points Placed: {points.length}</span>
        </div>

        <div className="w-full flex justify-center bg-black rounded-xl p-2 border border-slate-800 overflow-hidden">
          <canvas
            ref={canvasRef}
            width={1280}
            height={720}
            onClick={handleCanvasClick}
            className="w-full max-w-5xl h-auto cursor-crosshair rounded-lg border border-slate-800 shadow-lg"
          />
        </div>
      </div>
    </div>
  );
};
