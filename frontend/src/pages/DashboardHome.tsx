import React, { useEffect, useState } from 'react';
import { AnalyticsOverview, BusinessInsight } from '../types';
import { fetchAnalyticsOverview, fetchHourlyAnalytics, fetchBusinessInsights } from '../services/supabase';
import {
  Users,
  UserCheck,
  Clock,
  LogIn,
  LogOut,
  TrendingUp,
  Award,
  Sparkles,
  ArrowUpRight,
  RefreshCw
} from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export const DashboardHome: React.FC = () => {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [hourlyData, setHourlyData] = useState<any[]>([]);
  const [insights, setInsights] = useState<BusinessInsight[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const [ov, hr, ins] = await Promise.all([
        fetchAnalyticsOverview(),
        fetchHourlyAnalytics(),
        fetchBusinessInsights()
      ]);
      setOverview(ov);
      setHourlyData(hr);
      setInsights(ins);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-dark-800 to-slate-900 p-6 rounded-2xl border border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            Store Overview & Real-Time Intelligence
            <Sparkles className="w-5 h-5 text-amber-400" />
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Live multi-camera YOLO tracking, visitor dwell analytics, and automated zone insights.
          </p>
        </div>
        <button
          onClick={loadData}
          className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-2 border border-slate-700 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh Stats
        </button>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* 1. Current Visitors */}
        <div className="bg-dark-800 p-5 rounded-2xl border border-slate-800 flex items-center justify-between shadow-lg">
          <div>
            <p className="text-xs font-medium text-slate-400">Current Visitors</p>
            <h3 className="text-3xl font-extrabold text-cyan-400 mt-1">
              {overview?.current_visitors ?? 0}
            </h3>
            <p className="text-[11px] text-emerald-400 flex items-center gap-1 mt-1 font-medium">
              <ArrowUpRight className="w-3 h-3" /> Live Detection
            </p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center border border-cyan-500/20">
            <Users className="w-6 h-6" />
          </div>
        </div>

        {/* 2. Today's Visitors */}
        <div className="bg-dark-800 p-5 rounded-2xl border border-slate-800 flex items-center justify-between shadow-lg">
          <div>
            <p className="text-xs font-medium text-slate-400">Today's Total Visitors</p>
            <h3 className="text-3xl font-extrabold text-blue-400 mt-1">
              {overview?.todays_visitors ?? 0}
            </h3>
            <p className="text-[11px] text-slate-400 mt-1">Cumulative Sessions</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-blue-500/10 text-blue-400 flex items-center justify-center border border-blue-500/20">
            <UserCheck className="w-6 h-6" />
          </div>
        </div>

        {/* 3. Current Occupancy */}
        <div className="bg-dark-800 p-5 rounded-2xl border border-slate-800 flex items-center justify-between shadow-lg">
          <div>
            <p className="text-xs font-medium text-slate-400">Current Occupancy</p>
            <h3 className="text-3xl font-extrabold text-emerald-400 mt-1">
              {overview?.current_occupancy ?? 0}
            </h3>
            <p className="text-[11px] text-slate-400 mt-1">Entries minus Exits</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center border border-emerald-500/20">
            <TrendingUp className="w-6 h-6" />
          </div>
        </div>

        {/* 4. Average Dwell Time */}
        <div className="bg-dark-800 p-5 rounded-2xl border border-slate-800 flex items-center justify-between shadow-lg">
          <div>
            <p className="text-xs font-medium text-slate-400">Average Dwell Time</p>
            <h3 className="text-3xl font-extrabold text-amber-400 mt-1">
              {overview?.average_dwell_formatted ?? '0m 0s'}
            </h3>
            <p className="text-[11px] text-slate-400 mt-1">Stay Duration</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center border border-amber-500/20">
            <Clock className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Secondary KPI Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-dark-800 p-4 rounded-xl border border-slate-800 flex items-center gap-3">
          <LogIn className="w-5 h-5 text-emerald-400" />
          <div>
            <p className="text-[11px] text-slate-400">Total Entries</p>
            <p className="text-lg font-bold text-slate-100">{overview?.entries ?? 0}</p>
          </div>
        </div>

        <div className="bg-dark-800 p-4 rounded-xl border border-slate-800 flex items-center gap-3">
          <LogOut className="w-5 h-5 text-rose-400" />
          <div>
            <p className="text-[11px] text-slate-400">Total Exits</p>
            <p className="text-lg font-bold text-slate-100">{overview?.exits ?? 0}</p>
          </div>
        </div>

        <div className="bg-dark-800 p-4 rounded-xl border border-slate-800 flex items-center gap-3">
          <TrendingUp className="w-5 h-5 text-purple-400" />
          <div>
            <p className="text-[11px] text-slate-400">Peak Occupancy</p>
            <p className="text-lg font-bold text-slate-100">{overview?.peak_occupancy ?? 0}</p>
          </div>
        </div>

        <div className="bg-dark-800 p-4 rounded-xl border border-slate-800 flex items-center gap-3">
          <Award className="w-5 h-5 text-amber-400" />
          <div>
            <p className="text-[11px] text-slate-400">Top Visited Zone</p>
            <p className="text-sm font-bold text-slate-100 truncate">{overview?.most_visited_zone ?? 'N/A'}</p>
          </div>
        </div>
      </div>

      {/* Chart & Insights Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Hourly Traffic Chart */}
        <div className="lg:col-span-2 bg-dark-800 p-6 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-base text-slate-100">Hourly Foot Traffic Trend</h3>
            <span className="text-xs text-slate-400">Today's Traffic</span>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={hourlyData}>
                <defs>
                  <linearGradient id="colorVisitors" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0099ff" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#0099ff" stopOpacity={0.0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
                <XAxis dataKey="hour" stroke="#9CA3AF" fontSize={11} />
                <YAxis stroke="#9CA3AF" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '8px' }}
                  labelStyle={{ color: '#9CA3AF' }}
                />
                <Area type="monotone" dataKey="visitors" stroke="#0099ff" strokeWidth={3} fillOpacity={1} fill="url(#colorVisitors)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* AI Business Insights Panel */}
        <div className="bg-dark-800 p-6 rounded-2xl border border-slate-800 flex flex-col justify-between">
          <div>
            <h3 className="font-bold text-base text-slate-100 flex items-center gap-2 mb-4">
              <Sparkles className="w-5 h-5 text-amber-400" />
              Automated Business Insights
            </h3>

            <div className="space-y-3">
              {insights.map((ins) => (
                <div key={ins.id} className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-bold text-slate-200">{ins.title}</p>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 font-semibold border border-cyan-500/20">
                      {ins.impact}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">{ins.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
