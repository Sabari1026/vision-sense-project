import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Camera, Lock, Mail, Shield, CheckCircle2 } from 'lucide-react';
import { UserRole } from '../types';

export const Login: React.FC = () => {
  const { login } = useAuth();
  const [email, setEmail] = useState('admin@visionsense.ai');
  const [password, setPassword] = useState('password123');
  const [selectedRole, setSelectedRole] = useState<UserRole>('admin');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    login(email, selectedRole);
  };

  return (
    <div className="min-h-screen bg-dark-900 flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background Accent Gradients */}
      <div className="absolute -top-40 -left-40 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl"></div>
      <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl"></div>

      <div className="w-full max-w-md bg-dark-800/90 border border-slate-800 rounded-2xl p-8 shadow-2xl backdrop-blur-xl relative z-10">
        {/* Brand Header */}
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center text-white mx-auto mb-4 shadow-lg shadow-cyan-500/30">
            <Camera className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-wide">VisionSense</h1>
          <p className="text-sm text-slate-400 mt-1">AI CCTV Retail Analytics Platform</p>
        </div>

        {/* Quick Demo Role Selector */}
        <div className="mb-6 bg-slate-900/60 p-3 rounded-xl border border-slate-800">
          <label className="block text-xs font-semibold text-slate-400 mb-2">Select Demo Authentication Role:</label>
          <div className="grid grid-cols-3 gap-2">
            {(['admin', 'manager', 'viewer'] as UserRole[]).map((r) => (
              <button
                key={r}
                type="button"
                onClick={() => {
                  setSelectedRole(r);
                  setEmail(`${r}@visionsense.ai`);
                }}
                className={`py-2 px-3 rounded-lg text-xs capitalize font-bold border transition ${
                  selectedRole === r
                    ? 'bg-cyan-500 text-white border-cyan-400 shadow-md shadow-cyan-500/20'
                    : 'bg-slate-800 text-slate-400 border-slate-700 hover:bg-slate-700'
                }`}
              >
                {r}
              </button>
            ))}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Email Address</label>
            <div className="relative">
              <Mail className="w-5 h-5 text-slate-500 absolute left-3 top-2.5" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
                placeholder="name@company.com"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Password</label>
            <div className="relative">
              <Lock className="w-5 h-5 text-slate-500 absolute left-3 top-2.5" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
                placeholder="••••••••"
              />
            </div>
          </div>

          <button
            type="submit"
            className="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-semibold text-sm shadow-lg shadow-cyan-500/25 hover:from-cyan-400 hover:to-blue-500 transition-all flex items-center justify-center gap-2"
          >
            <Shield className="w-4 h-4" />
            Sign In to VisionSense Dashboard
          </button>
        </form>

        <div className="mt-6 text-center text-xs text-slate-500">
          Powered by Supabase Auth & Ultralytics YOLO Real-Time Engine
        </div>
      </div>
    </div>
  );
};
