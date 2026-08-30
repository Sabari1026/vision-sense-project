import React, { useEffect, useState } from 'react';
import { VisitorRecord } from '../types';
import { fetchVisitorSessions } from '../services/supabase';
import { Search, Download, Users, Filter, ArrowUpDown } from 'lucide-react';

export const VisitorsPage: React.FC = () => {
  const [visitors, setVisitors] = useState<VisitorRecord[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedAge, setSelectedAge] = useState('All');

  useEffect(() => {
    fetchVisitorSessions().then(setVisitors);
  }, []);

  const filteredVisitors = visitors.filter((v) => {
    const matchesSearch =
      v.track_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.camera.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.entry_zone.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesAge = selectedAge === 'All' || v.age_group === selectedAge;
    return matchesSearch && matchesAge;
  });

  const exportCSV = () => {
    const headers = ["Visitor ID", "Track ID", "Camera", "Entry Time", "Exit Time", "Dwell Duration", "Age Group", "Entry Zone"];
    const rows = filteredVisitors.map(v => [v.id, v.track_id, v.camera, v.entry_time, v.exit_time, v.dwell_duration, v.age_group, v.entry_zone]);

    let csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `visionsense_visitor_logs_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-dark-800 p-4 rounded-xl border border-slate-800">
        <div className="flex items-center gap-2">
          <Users className="w-5 h-5 text-cyan-400" />
          <h2 className="font-bold text-base text-slate-100">Anonymous Visitor Sessions Log</h2>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Search Input */}
          <div className="relative">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search Visitor ID or Zone..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-cyan-500 w-48 sm:w-64"
            />
          </div>

          <select
            value={selectedAge}
            onChange={(e) => setSelectedAge(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            <option value="All">All Age Groups</option>
            <option value="Child">Child</option>
            <option value="Young Adult">Young Adult</option>
            <option value="Adult">Adult</option>
            <option value="Senior">Senior</option>
          </select>

          <button
            onClick={exportCSV}
            className="px-3.5 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-white text-xs font-bold flex items-center gap-1.5 shadow-md shadow-cyan-500/20"
          >
            <Download className="w-3.5 h-3.5" />
            Export CSV
          </button>
        </div>
      </div>

      {/* Visitor Table Container */}
      <div className="bg-dark-800 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 text-slate-400 uppercase font-semibold border-b border-slate-800">
              <tr>
                <th className="p-4">Track ID</th>
                <th className="p-4">Camera Source</th>
                <th className="p-4">Entry Time</th>
                <th className="p-4">Exit Time</th>
                <th className="p-4">Dwell Time</th>
                <th className="p-4">Age Estimate</th>
                <th className="p-4">Entry Zone</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-200">
              {filteredVisitors.length > 0 ? (
                filteredVisitors.map((row) => (
                  <tr key={row.id} className="hover:bg-slate-800/50 transition">
                    <td className="p-4 font-mono font-bold text-cyan-400">{row.track_id}</td>
                    <td className="p-4 font-medium">{row.camera}</td>
                    <td className="p-4 text-slate-300 font-mono">{row.entry_time}</td>
                    <td className="p-4 text-slate-300 font-mono">{row.exit_time}</td>
                    <td className="p-4 font-semibold text-amber-400">{row.dwell_duration}</td>
                    <td className="p-4">
                      <span className="px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 font-medium border border-purple-500/20">
                        {row.age_group}
                      </span>
                    </td>
                    <td className="p-4 text-slate-300">{row.entry_zone}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-500">
                    No visitor session records found matching filter criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
