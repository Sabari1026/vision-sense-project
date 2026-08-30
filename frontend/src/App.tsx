import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { DashboardLayout } from './layouts/DashboardLayout';
import { Login } from './pages/Login';
import { DashboardHome } from './pages/DashboardHome';
import { LiveMonitoring } from './pages/LiveMonitoring';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { HeatmapsPage } from './pages/HeatmapsPage';
import { VisitorsPage } from './pages/VisitorsPage';
import { ReportsPage } from './pages/ReportsPage';
import { ZoneEditorPage } from './pages/ZoneEditorPage';
import { VideoManagerPage } from './pages/VideoManagerPage';
import { SystemHealthPage } from './pages/SystemHealthPage';

const MainApp: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('videos');

  if (!user) {
    return <Login />;
  }

  const renderTabContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <DashboardHome />;
      case 'live':
        return <LiveMonitoring />;
      case 'analytics':
        return <AnalyticsPage />;
      case 'heatmaps':
        return <HeatmapsPage />;
      case 'visitors':
        return <VisitorsPage />;
      case 'reports':
        return <ReportsPage />;
      case 'zones':
        return <ZoneEditorPage />;
      case 'videos':
        return <VideoManagerPage />;
      case 'health':
        return <SystemHealthPage />;
      default:
        return <DashboardHome />;
    }
  };

  return (
    <DashboardLayout activeTab={activeTab} setActiveTab={setActiveTab}>
      {renderTabContent()}
    </DashboardLayout>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
};

export default App;
