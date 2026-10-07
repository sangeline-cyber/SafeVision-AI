import React, { useState } from 'react';
import { useHealthCheck } from '../hooks/useHealthCheck';
import { Navbar } from '../components/Navbar';
import { FallDetectionPage } from './FallDetectionPage';
import { HealthDashboard } from '../components/HealthDashboard';
import { ArchitectureOverview } from '../components/ArchitectureOverview';
import { EvidenceSchemaViewer } from '../components/EvidenceSchemaViewer';

export const DashboardPage: React.FC = () => {
  const health = useHealthCheck(8000);
  const [activeTab, setActiveTab] = useState<'fall_detection' | 'health' | 'architecture' | 'evidence'>('fall_detection');

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Navigation */}
      <Navbar health={health} activeTab={activeTab} setActiveTab={(t) => setActiveTab(t as any)} />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'fall_detection' && <FallDetectionPage />}
        {activeTab === 'health' && <HealthDashboard health={health} />}
        {activeTab === 'architecture' && <ArchitectureOverview />}
        {activeTab === 'evidence' && <EvidenceSchemaViewer />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/80 py-6 text-center text-xs text-slate-500 font-mono">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>SafeVision AI • HNX26PSI07 Autonomous Safety Event Detection</span>
          <span>Real AI Autonomous 4-Event Safety Verification Active</span>
        </div>
      </footer>
    </div>
  );
};
