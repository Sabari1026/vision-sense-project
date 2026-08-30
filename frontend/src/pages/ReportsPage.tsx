import React, { useState, useEffect } from 'react';
import { FileText, Download, Printer, Sparkles, RefreshCw, Activity } from 'lucide-react';

export const ReportsPage: React.FC = () => {
  const [reportType, setReportType] = useState<'daily' | 'weekly' | 'monthly'>('daily');
  const [reportData, setReportData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchReportData = async () => {
    try {
      const res = await fetch(`/api/reports/generate?report_type=${reportType}&format=json`);
      if (res.ok) {
        const data = await res.json();
        setReportData(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReportData();
    const interval = setInterval(fetchReportData, 2500);
    return () => clearInterval(interval);
  }, [reportType]);

  const downloadReport = (format: 'json' | 'csv') => {
    window.open(`/api/reports/generate?report_type=${reportType}&format=${format}`, '_blank');
  };

  const exec = reportData?.executive_summary;
  const cameraPerf = reportData?.camera_performance || [];
  const insights = reportData?.key_insights || [];

  return (
    <div className="space-y-6">
      {/* Top Controls Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-dark-800 p-4 rounded-xl border border-slate-800">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-cyan-400" />
          <h2 className="font-bold text-base text-slate-100">Automated Retail Analytics Reports</h2>
          <span className="flex items-center gap-1 text-[11px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 ml-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
            LIVE DB SYNC
          </span>
        </div>

        <div className="flex items-center gap-3">
          {/* Report Frequency Switcher */}
          <div className="flex bg-slate-900 p-1 rounded-lg border border-slate-700">
            {(['daily', 'weekly', 'monthly'] as const).map((t) => (
              <button
                key={t}
                onClick={() => setReportType(t)}
                className={`px-3 py-1 text-xs capitalize rounded font-semibold transition ${
                  reportType === t ? 'bg-cyan-500 text-white shadow-md' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {t}
              </button>
            ))}
          </div>

          <button
            onClick={() => downloadReport('csv')}
            className="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold flex items-center gap-1.5 shadow-md"
          >
            <Download className="w-3.5 h-3.5" />
            Export CSV
          </button>

          <button
            onClick={() => downloadReport('json')}
            className="px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold flex items-center gap-1.5 shadow-md"
          >
            <Download className="w-3.5 h-3.5" />
            Export JSON
          </button>

          <button
            onClick={() => window.print()}
            className="px-3.5 py-1.5 rounded-lg bg-slate-700 hover:bg-slate-600 text-white text-xs font-bold flex items-center gap-1.5"
          >
            <Printer className="w-3.5 h-3.5" />
            Print Report
          </button>
        </div>
      </div>

      {/* Printable Report Document Card */}
      <div className="bg-dark-800 border border-slate-800 rounded-2xl p-8 space-y-8 shadow-2xl max-w-4xl mx-auto text-slate-200">
        {/* Document Header */}
        <div className="border-b border-slate-800 pb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-100 tracking-tight flex items-center gap-2">
              VISION SENSE
              <span className="text-xs px-2.5 py-1 rounded bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                LIVE UPDATING
              </span>
            </h1>
            <p className="text-sm text-cyan-400 font-semibold uppercase mt-0.5">
              {reportType} Retail CCTV Analytics Report
            </p>
          </div>
          <div className="text-right text-xs text-slate-400 font-mono space-y-1">
            <p>Generated: {reportData?.generated_at || 'Loading...'}</p>
            <p>Period: {reportData?.period || 'Live'}</p>
          </div>
        </div>

        {/* Section 1: Executive Summary */}
        <div className="space-y-4">
          <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider text-cyan-400 border-b border-slate-800 pb-2">
            1. Live Executive Summary
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
              <p className="text-xs text-slate-400">Total Visitors</p>
              <p className="text-2xl font-extrabold text-white mt-1">
                {exec?.total_visitors ?? 0}
              </p>
            </div>
            <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
              <p className="text-xs text-slate-400">Average Dwell Time</p>
              <p className="text-2xl font-extrabold text-amber-400 mt-1">
                {exec?.average_dwell_time ?? '0s'}
              </p>
            </div>
            <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
              <p className="text-xs text-slate-400">Current Occupancy</p>
              <p className="text-2xl font-extrabold text-emerald-400 mt-1">
                {exec?.current_occupancy ?? 0}
              </p>
            </div>
            <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
              <p className="text-xs text-slate-400">Top Visited Location</p>
              <p className="text-sm font-extrabold text-cyan-400 mt-1 truncate">
                {exec?.top_performing_camera ?? 'N/A'}
              </p>
            </div>
          </div>
        </div>

        {/* Section 2: Zone & Camera Performance */}
        <div className="space-y-4">
          <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider text-cyan-400 border-b border-slate-800 pb-2">
            2. Camera & Location Performance Metrics
          </h3>
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900 text-slate-400 font-semibold border-b border-slate-800">
              <tr>
                <th className="p-3">Camera Location</th>
                <th className="p-3">Total Visitors</th>
                <th className="p-3">Entries</th>
                <th className="p-3">Average Dwell</th>
                <th className="p-3">Popularity Index</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {cameraPerf.map((c: any) => (
                <tr key={c.camera_id}>
                  <td className="p-3 font-medium text-slate-100">{c.camera_name}</td>
                  <td className="p-3 font-bold text-white">{c.total_visitors}</td>
                  <td className="p-3 text-emerald-400 font-semibold">{c.entries}</td>
                  <td className="p-3 text-amber-400 font-semibold">{c.avg_dwell_time}</td>
                  <td className="p-3 font-bold text-cyan-400">{c.popularity}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Section 3: Data-Driven AI Insights */}
        <div className="space-y-4">
          <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider text-cyan-400 border-b border-slate-800 pb-2">
            3. Automated Business & Merchandise Insights
          </h3>
          <ul className="space-y-2.5 text-xs text-slate-300">
            {insights.map((insight: string, idx: number) => (
              <li key={idx} className="flex items-start gap-2 bg-slate-900/40 p-3 rounded-lg border border-slate-800">
                <Sparkles className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                <span>{insight}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};
