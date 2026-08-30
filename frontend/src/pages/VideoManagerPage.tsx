import React, { useState } from 'react';
import { Upload, Film, Play, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';
import { startCamera, stopCamera, API_BASE_URL } from '../services/supabase';

export const VideoManagerPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedCam, setSelectedCam] = useState('11111111-1111-1111-1111-111111111111');
  const [uploading, setUploading] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');

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
        setStatusMsg(`Successfully uploaded "${data.filename}"! Restarting camera stream...`);
        await startCamera(selectedCam);
      } else {
        setStatusMsg(`Upload failed: ${data.detail}`);
      }
    } catch (err: any) {
      setStatusMsg(`Error: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-dark-800 p-6 rounded-2xl border border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Film className="w-5 h-5 text-cyan-400" />
            CCTV Video Stream & Demo File Manager
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Upload custom MP4, AVI, or MOV CCTV feeds to simulate live cameras or trigger automated Demo Mode.
          </p>
        </div>
      </div>

      {statusMsg && (
        <div className="bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 px-4 py-3 rounded-xl text-xs flex items-center gap-2 font-medium">
          <CheckCircle2 className="w-4 h-4" />
          {statusMsg}
        </div>
      )}

      {/* Upload Form Card */}
      <div className="bg-dark-800 border border-slate-800 rounded-2xl p-6 space-y-6 shadow-xl max-w-2xl">
        <h3 className="font-bold text-base text-slate-100 flex items-center gap-2">
          <Upload className="w-5 h-5 text-cyan-400" />
          Upload Video to Camera Channel
        </h3>

        <form onSubmit={handleUpload} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Target Camera Channel</label>
            <select
              value={selectedCam}
              onChange={(e) => setSelectedCam(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-cyan-500"
            >
              <option value="11111111-1111-1111-1111-111111111111">Camera 01 - Main Entrance (camera1.mp4)</option>
              <option value="22222222-2222-2222-2222-222222222222">Camera 02 - Apparel Section (camera2.mp4)</option>
              <option value="33333333-3333-3333-3333-333333333333">Camera 03 - Electronics Hub (camera3.mp4)</option>
              <option value="44444444-4444-4444-4444-444444444444">Camera 04 - Checkout Counters (camera4.mp4)</option>
            </select>
          </div>

          {/* Drag & Drop File Select */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Select Video File (.mp4, .avi, .mov, .mkv)</label>
            <input
              type="file"
              accept="video/*"
              required
              onChange={(e) => setSelectedFile(e.target.files ? e.target.files[0] : null)}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-xs text-slate-300 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-cyan-500 file:text-white hover:file:bg-cyan-400"
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
            {uploading ? "Uploading & Processing..." : "Upload & Replace Camera Feed"}
          </button>
        </form>
      </div>
    </div>
  );
};
