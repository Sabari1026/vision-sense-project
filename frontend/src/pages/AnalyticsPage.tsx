import React, { useEffect, useState } from 'react';
import {
  fetchHourlyAnalytics,
  fetchDailyAnalytics,
  fetchDwellAnalytics,
  fetchAgeAnalytics,
  fetchZoneAnalytics
} from '../services/supabase';
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { Calendar, Filter, AlertTriangle, Layers, Clock, Users, MapPin } from 'lucide-react';

const COLORS = ['#0099ff', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444'];

export const AnalyticsPage: React.FC = () => {
  const [hourly, setHourly] = useState<any[]>([]);
  const [daily, setDaily] = useState<any[]>([]);
  const [dwell, setDwell] = useState<any[]>([]);
  const [ageData, setAgeData] = useState<any>(null);
  const [zones, setZones] = useState<any[]>([]);

  const [selectedDate, setSelectedDate] = useState('Today');
  const [selectedCamera, setSelectedCamera] = useState('All Cameras');

  useEffect(() => {
    Promise.all([
      fetchHourlyAnalytics(),
      fetchDailyAnalytics(),
      fetchDwellAnalytics(),
      fetchAgeAnalytics(),
      fetchZoneAnalytics()
    ]).then(([hr, dy, dw, ag, zn]) => {
      setHourly(hr);
      setDaily(dy);
      setDwell(dw);
      setAgeData(ag);
      setZones(zn);
    });
  }, [selectedDate, selectedCamera]);

  return (
    <div className="space-y-6">
      {/* Global Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-dark-800 p-4 rounded-xl border border-slate-800">
        <div className="flex items-center gap-2">
          <Filter className="w-5 h-5 text-cyan-400" />
          <h2 className="font-bold text-base text-slate-100">Analytics Filtering</h2>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div>
            <label className="block text-[10px] text-slate-400 uppercase font-bold mb-1">Timeframe</label>
            <select
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
            >
              <option>Today</option>
              <option>Yesterday</option>
              <option>Last 7 Days</option>
              <option>Last 30 Days</option>
            </select>
          </div>

          <div>
            <label className="block text-[10px] text-slate-400 uppercase font-bold mb-1">Camera Filter</label>
            <select
              value={selectedCamera}
              onChange={(e) => setSelectedCamera(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
            >
              <option>All Cameras</option>
              <option>Camera 01 - Main Entrance</option>
              <option>Camera 02 - Apparel Section</option>
              <option>Camera 03 - Electronics Hub</option>
              <option>Camera 04 - Checkout Counters</option>
            </select>
          </div>
        </div>
      </div>

      {/* 2×2 Chart Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1: Visitors by Hour */}
        <div className="bg-dark-800 p-5 rounded-2xl border border-slate-800 space-y-3">
          <h3 className="font-bold text-sm text-slate-100 flex items-center gap-2">
            <Clock className="w-4 h-4 text-cyan-400" />
            Visitors by Hour
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={hourly}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
                <XAxis dataKey="hour" stroke="#9CA3AF" fontSize={11} />
                <YAxis stroke="#9CA3AF" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#374151' }} />
                <Line type="monotone" dataKey="visitors" stroke="#0099ff" strokeWidth={3} dot={{ fill: '#0099ff' }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Daily Visitor Trends */}
        <div className="bg-dark-800 p-5 rounded-2xl border border-slate-800 space-y-3">
          <h3 className="font-bold text-sm text-slate-100 flex items-center gap-2">
            <Users className="w-4 h-4 text-emerald-400" />
            Daily Visitor Trends (7 Days)
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={daily}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
                <XAxis dataKey="day" stroke="#9CA3AF" fontSize={11} />
                <YAxis stroke="#9CA3AF" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#374151' }} />
                <Bar dataKey="visitors" fill="#10b981" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 3: Dwell Time Distribution */}
        <div className="bg-dark-800 p-5 rounded-2xl border border-slate-800 space-y-3">
          <h3 className="font-bold text-sm text-slate-100 flex items-center gap-2">
            <Clock className="w-4 h-4 text-amber-400" />
            Dwell Duration Brackets
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dwell}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
                <XAxis dataKey="bracket" stroke="#9CA3AF" fontSize={11} />
                <YAxis stroke="#9CA3AF" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#374151' }} />
                <Bar dataKey="count" fill="#f59e0b" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 4: Age Group Distribution with Disclaimer */}
        <div className="bg-dark-800 p-5 rounded-2xl border border-slate-800 flex flex-col justify-between space-y-3">
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-bold text-sm text-slate-100 flex items-center gap-2">
                <Users className="w-4 h-4 text-purple-400" />
                Estimated Age Group Breakdown
              </h3>
            </div>
            <p className="text-[11px] text-amber-400/90 flex items-center gap-1.5 font-medium bg-amber-500/10 p-2 rounded-lg border border-amber-500/20 mb-3">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              {ageData?.disclaimer || "Age categories are computer-vision estimates and may be inaccurate."}
            </p>

            <div className="h-52">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={ageData?.distribution || []}
                    dataKey="count"
                    nameKey="age_group"
                    cx="50%"
                    cy="50%"
                    outerRadius={75}
                    innerRadius={45}
                    paddingAngle={4}
                  >
                    {(ageData?.distribution || []).map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#374151' }} />
                  <Legend wrapperStyle={{ fontSize: '11px', color: '#9CA3AF' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
