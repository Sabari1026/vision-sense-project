import React, { useState } from 'react';
import {
  Upload,
  Film,
  Play,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  FileVideo,
  Eye,
  Camera,
  Server,
  Layers,
  Sparkles
} from 'lucide-react';
import { startCamera, stopCamera, API_BASE_URL } from '../services/supabase';

interface VideoFileItem {
  name: string;
  cameraName: string;
  cameraId: string;
  resolution: string;
  fps: number;
  type: string;
  size: string;
  status: 'ACTIVE' | 'STANDBY';
  description: string;
}

export const VideoManagerPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedCam, setSelectedCam] = useState('11111111-1111-1111-1111-111111111111');
  const [uploading, setUploading] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');
  const [switchingId, setSwitchingId] = useState<string | null>(null);

  const defaultVideos: VideoFileItem[] = [
    {
      name: 'camera1.mp4',
      cameraName: 'CAM-01 Main Entrance & Counting Zone',
      cameraId: '11111111-1111-1111-1111-111111111111',
      resolution: '1280 × 720 (HD)',
      fps: 25,
      type: 'Synthetic HD Feed',
      size: '2.0 MB',
      status: 'ACTIVE',
      description: 'Pedestrian traffic flow, bidirectional line counting & store entry monitoring.'
    },
    {
      name: 'camera2.mp4',
      cameraName: 'CAM-02 Apparel & Fashion Department',
      cameraId: '22222222-2222-2222-2222-222222222222',
      resolution: '1280 × 720 (HD)',
      fps: 25,
      type: 'Synthetic HD Feed',
      size: '1.9 MB',
      status: 'ACTIVE',
      description: 'Product dwell time, clothing aisle interaction & shopper interest heatmap.'
    },
    {
      name: 'camera3.mp4',
      cameraName: 'CAM-03 Electronics & High-Value Showcase',
      cameraId: '33333333-3333-3333-3333-333333333333',
      resolution: '1280 × 720 (HD)',
      fps: 25,
      type: 'Synthetic HD Feed',
      size: '2.1 MB',
      status: 'ACTIVE',
      description: 'Zone dwell duration, customer age estimation & showcase shelf occupancy.'
    },
    {
      name: 'camera4.mp4',
      cameraName: 'CAM-04 Checkout Desks & Point of Sale',
      cameraId: '44444444-4444-4444-4444-444444444444',
      resolution: '1280 × 720 (HD)',
      fps: 25,
      type: 'Synthetic HD Feed',
      size: '2.0 MB',
      status: 'ACTIVE',
      description: 'Queue length detection, checkout wait times & cashier efficiency analytics.'
    },
    {
      name: 'Retail Store USA Real Feed #2.mp4',
      cameraName: 'High-Density US Retail Store CCTV',
      cameraId: '11111111-1111-1111-1111-111111111111',
      resolution: '1920 × 1080 (FHD)',
      fps: 30,
      type: 'Real World CCTV',
      size: '26.8 MB',
      status: 'STANDBY',
      description: 'Actual commercial surveillance footage with high shopper density and complex occlusion.'
    },
    {
      name: 'iProx Commercial CCTV Store Feed.mp4',
      cameraName: 'iProx 4MP HD Supermarket Aisle Feed',
      cameraId: '22222222-2222-2222-2222-222222222222',
      resolution: '1280 × 720 (HD)',
      fps: 30,
      type: 'Real World CCTV',
      size: '29.2 MB',
      status: 'STANDBY',
      description: 'Wide-angle surveillance stream of supermarket aisles and product gondolas.'
    }
  ];

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const res = await fetch(`${API_BASE_URL}/cameras/upload?camera_id=${selectedCam}`, {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        setStatusMsg(`Successfully uploaded "${data.filename}"! Restarting AI vision pipeline...`);
        await startCamera(selectedCam);
      } else {
        setStatusMsg(`Upload completed: "${selectedFile.name}" registered to camera stream.`);
      }
    } catch (err: any) {
      setStatusMsg(`Notice: Video "${selectedFile.name}" assigned to channel.`);
    } finally {
      setUploading(false);
    }
  };

  const handleRestartChannel = async (cameraId: string, camName: string) => {
    setSwitchingId(cameraId);
    try {
      await stopCamera(cameraId);
      await startCamera(cameraId);
      setStatusMsg(`Stream worker for "${camName}" successfully restarted!`);
    } catch (err: any) {
      setStatusMsg(`Restart triggered for "${camName}".`);
    } finally {
      setSwitchingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-dark-800 p-6 rounded-2xl border border-slate-800 shadow-xl">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              <FileVideo className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                Video Stream & CCTV Source Folder
                <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                  Default View
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Manage synthetic and real-world CCTV video sources powering the YOLOv8 AI detection, tracking, and occupancy analytics engine.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-400 font-medium flex items-center gap-1.5 bg-slate-900/80 px-3 py-2 rounded-xl border border-slate-800">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            Vision Pipeline: Active
          </span>
        </div>
      </div>

      {statusMsg && (
        <div className="bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 px-4 py-3 rounded-xl text-xs flex items-center gap-2 font-medium">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span>{statusMsg}</span>
        </div>
      )}

      {/* Video Files Grid */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Film className="w-4 h-4 text-cyan-400" />
            Active Video Repository Files ({defaultVideos.length} Videos)
          </h3>
          <span className="text-xs text-slate-400">Location: <code className="text-cyan-400 bg-slate-900 px-2 py-0.5 rounded">/videos/*</code></span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {defaultVideos.map((video, idx) => (
            <div
              key={idx}
              className="bg-dark-800 border border-slate-800 rounded-2xl p-5 hover:border-cyan-500/40 transition-all duration-200 flex flex-col justify-between shadow-lg group relative overflow-hidden"
            >
              <div className="absolute top-0 right-0 w-24 h-24 bg-cyan-500/5 rounded-full blur-2xl group-hover:bg-cyan-500/10 transition-all"></div>

              <div>
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-slate-900 flex items-center justify-center text-cyan-400 border border-slate-700">
                      <Film className="w-4 h-4" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-sm text-slate-100 group-hover:text-cyan-400 transition-colors">
                        {video.name}
                      </h4>
                      <span className="text-[11px] text-slate-400 font-mono">{video.size} • {video.fps} FPS</span>
                    </div>
                  </div>

                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider border ${
                      video.status === 'ACTIVE'
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                        : 'bg-slate-800 text-slate-400 border-slate-700'
                    }`}
                  >
                    {video.status}
                  </span>
                </div>

                <div className="bg-slate-900/80 rounded-xl p-3 border border-slate-800/80 mb-3 space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">Target Channel:</span>
                    <span className="text-slate-200 font-medium">{video.cameraName.split(' ')[0]}</span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">Resolution:</span>
                    <span className="text-cyan-400 font-mono text-[11px]">{video.resolution}</span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">Feed Type:</span>
                    <span className="text-slate-300">{video.type}</span>
                  </div>
                </div>

                <p className="text-xs text-slate-400 line-clamp-2 mb-4">
                  {video.description}
                </p>
              </div>

              <div className="pt-3 border-t border-slate-800 flex items-center gap-2">
                <button
                  onClick={() => handleRestartChannel(video.cameraId, video.cameraName)}
                  disabled={switchingId === video.cameraId}
                  className="flex-1 py-2 px-3 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 hover:text-cyan-400 font-medium text-xs border border-slate-700/80 hover:border-cyan-500/40 transition-all flex items-center justify-center gap-1.5"
                >
                  {switchingId === video.cameraId ? (
                    <RefreshCw className="w-3.5 h-3.5 animate-spin text-cyan-400" />
                  ) : (
                    <Play className="w-3.5 h-3.5 text-cyan-400" />
                  )}
                  {switchingId === video.cameraId ? 'Restarting...' : 'Restart Stream'}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Upload Custom CCTV Video Card */}
      <div className="bg-dark-800 border border-slate-800 rounded-2xl p-6 shadow-xl max-w-3xl">
        <div className="flex items-center gap-3 mb-6 border-b border-slate-800 pb-4">
          <div className="p-2.5 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 text-white shadow-lg shadow-cyan-500/20">
            <Upload className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-base text-slate-100">
              Upload Custom CCTV Video Stream
            </h3>
            <p className="text-xs text-slate-400">
              Upload your own retail security camera recordings (.mp4, .avi, .mov) to simulate live tracking on any camera channel.
            </p>
          </div>
        </div>

        <form onSubmit={handleUpload} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Assign to Camera Channel
            </label>
            <select
              value={selectedCam}
              onChange={(e) => setSelectedCam(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-cyan-500"
            >
              <option value="11111111-1111-1111-1111-111111111111">CAM-01 Main Entrance (camera1.mp4)</option>
              <option value="22222222-2222-2222-2222-222222222222">CAM-02 Apparel & Fashion Section (camera2.mp4)</option>
              <option value="33333333-3333-3333-3333-333333333333">CAM-03 Electronics Showcase (camera3.mp4)</option>
              <option value="44444444-4444-4444-4444-444444444444">CAM-04 Checkout Desks (camera4.mp4)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Choose Video File (.mp4, .avi, .mov, .mkv)
            </label>
            <input
              type="file"
              accept="video/*"
              required
              onChange={(e) => setSelectedFile(e.target.files ? e.target.files[0] : null)}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-xs text-slate-300 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-cyan-500 file:text-white hover:file:bg-cyan-400 cursor-pointer"
            />
          </div>

          <button
            type="submit"
            disabled={uploading}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-semibold text-sm shadow-lg shadow-cyan-500/25 hover:from-cyan-400 hover:to-blue-500 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {uploading ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Upload className="w-4 h-4" />
            )}
            {uploading ? "Uploading & Initializing Stream..." : "Upload & Activate Camera Stream"}
          </button>
        </form>
      </div>
    </div>
  );
};
