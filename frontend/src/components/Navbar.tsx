import React from 'react';
import { ShieldCheck, Activity, Database, RefreshCw, Cpu, Video, ShieldAlert } from 'lucide-react';
import { HealthState } from '../hooks/useHealthCheck';

interface NavbarProps {
  health: HealthState;
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ health, activeTab, setActiveTab }) => {
  const isBackendOk = health.backend.data?.status === 'ok';
  const isDbOk = health.database.data?.connected === true;

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand & Problem Statement Badge */}
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-gradient-to-tr from-teal-500 to-cyan-400 text-slate-950 shadow-lg shadow-teal-500/20">
              <ShieldCheck className="w-6 h-6 stroke-[2.5]" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-xl tracking-tight text-white">SafeVision</span>
                <span className="text-teal-400 font-extrabold text-xl">AI</span>
                <span className="px-2 py-0.5 text-xs font-semibold rounded bg-teal-950/80 text-teal-300 border border-teal-800/50">
                  HNX26PSI07
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">
                Context-Aware Autonomous Safety & Evidence Verification
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="hidden md:flex items-center space-x-1">
            <button
              onClick={() => setActiveTab('fall_detection')}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-all flex items-center space-x-2 ${
                activeTab === 'fall_detection'
                  ? 'bg-rose-500/10 text-rose-300 border border-rose-500/30 font-bold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
              }`}
            >
              <Video className="w-4 h-4 text-rose-400" />
              <span>Safety Event Detection (Real AI)</span>
            </button>

            <button
              onClick={() => setActiveTab('health')}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-all flex items-center space-x-2 ${
                activeTab === 'health'
                  ? 'bg-teal-500/10 text-teal-300 border border-teal-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
              }`}
            >
              <Activity className="w-4 h-4" />
              <span>System Health</span>
            </button>

            <button
              onClick={() => setActiveTab('architecture')}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-all flex items-center space-x-2 ${
                activeTab === 'architecture'
                  ? 'bg-teal-500/10 text-teal-300 border border-teal-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
              }`}
            >
              <Cpu className="w-4 h-4" />
              <span>Architecture</span>
            </button>

            <button
              onClick={() => setActiveTab('evidence')}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-all flex items-center space-x-2 ${
                activeTab === 'evidence'
                  ? 'bg-teal-500/10 text-teal-300 border border-teal-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
              }`}
            >
              <ShieldAlert className="w-4 h-4" />
              <span>Evidence Schema</span>
            </button>
          </nav>

          {/* Live Telemetry Status Pills & Refresh */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-slate-900/90 border border-slate-800 text-xs">
              <span
                className={`w-2 h-2 rounded-full ${
                  isBackendOk ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'
                }`}
              />
              <span className="text-slate-300 font-mono text-[11px]">
                API: {isBackendOk ? `${health.backend.latencyMs}ms` : 'Offline'}
              </span>
            </div>

            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-slate-900/90 border border-slate-800 text-xs">
              <Database className="w-3 h-3 text-slate-400" />
              <span
                className={`w-2 h-2 rounded-full ${
                  isDbOk ? 'bg-emerald-400' : 'bg-amber-400'
                }`}
              />
              <span className="text-slate-300 font-mono text-[11px]">
                DB: {isDbOk ? 'Active' : 'Standby'}
              </span>
            </div>

            <button
              onClick={() => health.refresh()}
              disabled={health.backend.loading}
              className="p-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white transition disabled:opacity-50"
              title="Refresh System Health Status"
            >
              <RefreshCw
                className={`w-4 h-4 ${health.backend.loading ? 'animate-spin text-teal-400' : ''}`}
              />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
