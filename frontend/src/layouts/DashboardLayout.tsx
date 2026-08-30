import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { UserRole } from '../types';
import {
  LayoutDashboard,
  Video,
  BarChart3,
  Flame,
  Users,
  FileText,
  MapPin,
  Upload,
  Activity,
  LogOut,
  Shield,
  Moon,
  Sun,
  Camera
} from 'lucide-react';

interface DashboardLayoutProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  children: React.ReactNode;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({ activeTab, setActiveTab, children }) => {
  const { user, role, setRole, logout } = useAuth();
  const [darkMode, setDarkMode] = useState(true);

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, roles: ['admin', 'manager', 'viewer'] },
    { id: 'live', label: 'Live Monitoring', icon: Video, roles: ['admin', 'manager', 'viewer'], badge: '2×2 Grid' },
    { id: 'analytics', label: 'Analytics', icon: BarChart3, roles: ['admin', 'manager', 'viewer'] },
    { id: 'heatmaps', label: 'Heatmaps', icon: Flame, roles: ['admin', 'manager', 'viewer'] },
    { id: 'visitors', label: 'Visitor Logs', icon: Users, roles: ['admin', 'manager', 'viewer'] },
    { id: 'reports', label: 'Reports', icon: FileText, roles: ['admin', 'manager', 'viewer'] },
    { id: 'zones', label: 'Zone Editor', icon: MapPin, roles: ['admin', 'manager'] },
    { id: 'videos', label: 'Video Manager', icon: Upload, roles: ['admin', 'manager'] },
    { id: 'health', label: 'System Health', icon: Activity, roles: ['admin', 'manager', 'viewer'] },
  ];

  const toggleTheme = () => {
    setDarkMode(!darkMode);
    document.documentElement.classList.toggle('dark');
  };

  return (
    <div className={`min-h-screen flex ${darkMode ? 'bg-dark-900 text-slate-100' : 'bg-slate-50 text-slate-900'}`}>
      {/* Sidebar */}
      <aside className="w-64 border-r border-slate-800 bg-dark-800 flex flex-col justify-between p-4 sticky top-0 h-screen z-30">
        <div>
          {/* Brand Header */}
          <div className="flex items-center gap-3 px-3 py-4 mb-6 border-b border-slate-800">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center text-white shadow-lg shadow-cyan-500/30">
              <Camera className="w-6 h-6" />
            </div>
            <div>
              <h1 className="font-bold text-lg text-white tracking-wide flex items-center gap-1.5">
                Vision<span className="text-cyan-400">Sense</span>
              </h1>
              <p className="text-xs text-slate-400 font-medium">AI CCTV Retail Analytics</p>
            </div>
          </div>

          {/* Navigation Items */}
          <nav className="space-y-1">
            {navItems.map((item) => {
              if (!item.roles.includes(role)) return null;
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-cyan-500/10 text-cyan-400 border-l-4 border-cyan-400 font-semibold'
                      : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={`w-5 h-5 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/30">
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* User Profile & Role Switcher */}
        <div className="pt-4 border-t border-slate-800 space-y-3">
          <div className="px-3 py-2 rounded-lg bg-slate-900/60 border border-slate-800">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs text-slate-400 font-medium">Current Role:</span>
              <span className="text-xs uppercase font-bold px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
                {role}
              </span>
            </div>

            {/* Quick Demo Role Switcher */}
            <div className="grid grid-cols-3 gap-1">
              {(['admin', 'manager', 'viewer'] as UserRole[]).map((r) => (
                <button
                  key={r}
                  onClick={() => setRole(r)}
                  className={`text-[10px] capitalize py-1 rounded font-medium transition ${
                    role === r ? 'bg-cyan-500 text-white font-bold' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-between px-2">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-xs font-bold text-slate-200">
                {user?.full_name?.charAt(0) || 'U'}
              </div>
              <div className="truncate w-28">
                <p className="text-xs font-semibold text-slate-200 truncate">{user?.full_name}</p>
                <p className="text-[10px] text-slate-400 truncate">{user?.email}</p>
              </div>
            </div>

            <button
              onClick={logout}
              title="Logout"
              className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded-lg transition"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Navbar */}
        <header className="h-16 border-b border-slate-800 bg-dark-800/80 backdrop-blur px-6 flex items-center justify-between sticky top-0 z-20">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-bold text-slate-100 capitalize">{activeTab.replace('-', ' ')}</h2>
            <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1.5 font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              4 CAMERAS ONLINE
            </span>
          </div>

          <div className="flex items-center gap-4">
            <button
              onClick={toggleTheme}
              className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition"
              title="Toggle Dark/Light Mode"
            >
              {darkMode ? <Sun className="w-5 h-5 text-amber-400" /> : <Moon className="w-5 h-5 text-slate-600" />}
            </button>

            <div className="text-xs text-right hidden sm:block">
              <p className="text-slate-400 font-medium">System Time (Local)</p>
              <p className="text-slate-200 font-mono font-bold">2026-08-30 12:33</p>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-6 flex-1 overflow-y-auto">
          {children}

          {/* Privacy & Legal Disclaimer */}
          <footer className="mt-12 pt-6 border-t border-slate-800 text-center text-xs text-slate-500 max-w-4xl mx-auto space-y-1">
            <p className="font-semibold text-slate-400">VisionSense AI Privacy Disclaimer</p>
            <p>
              VisionSense uses anonymous computer-vision tracking for retail operational analytics. It does not identify individuals by name or store facial recognition embeddings. Age categories are automated estimates and may be subject to minor variance.
            </p>
          </footer>
        </main>
      </div>
    </div>
  );
};
