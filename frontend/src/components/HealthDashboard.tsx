import React from 'react';
import { Activity, Database, CheckCircle2, AlertTriangle, XCircle, Clock, Server, Terminal, ShieldAlert } from 'lucide-react';
import { HealthState } from '../hooks/useHealthCheck';

interface HealthDashboardProps {
  health: HealthState;
}

export const HealthDashboard: React.FC<HealthDashboardProps> = ({ health }) => {
  const isBackendOk = health.backend.data?.status === 'ok';
  const isDbConnected = health.database.data?.connected === true;

  return (
    <div className="space-y-6">
      {/* Top Banner: Verification & Problem Scope */}
      <div className="glass-panel p-6 rounded-2xl relative overflow-hidden bg-gradient-to-r from-slate-900/90 via-slate-900/60 to-teal-950/20 border-slate-800">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-teal-500/20 text-teal-300 border border-teal-500/30">
                Phase 1: Project Foundation Active
              </span>
              <span className="text-xs text-slate-400 font-mono">
                {health.lastChecked ? `Last Ping: ${health.lastChecked.toLocaleTimeString()}` : 'Connecting...'}
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              SafeVision AI System Health & Connectivity
            </h1>
            <p className="text-slate-300 text-sm max-w-3xl leading-relaxed">
              Real-time telemetry and health endpoint monitoring for the Autonomous Safety Event Detection and Evidence Verification System.
            </p>
          </div>

          <div className="flex items-center space-x-3 bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
            <div className="text-right">
              <p className="text-[11px] text-slate-400 uppercase font-semibold">Backend Latency</p>
              <p className="text-lg font-mono font-bold text-teal-400">{health.backend.latencyMs} ms</p>
            </div>
            <div className="h-8 w-px bg-slate-800" />
            <div className="text-right">
              <p className="text-[11px] text-slate-400 uppercase font-semibold">DB Engine</p>
              <p className="text-sm font-mono font-bold text-slate-200">PostgreSQL</p>
            </div>
          </div>
        </div>
      </div>

      {/* Cards Grid: Backend Health & Database Health */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Card 1: Backend Health (GET /api/health) */}
        <div className="glass-panel p-6 rounded-2xl border-slate-800 space-y-4">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-3">
              <div className={`p-3 rounded-xl ${isBackendOk ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'}`}>
                <Server className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">Backend API Server</h3>
                <p className="text-xs text-slate-400 font-mono">GET /api/health</p>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              {isBackendOk ? (
                <span className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-xs font-semibold">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>ONLINE & HEALTHY</span>
                </span>
              ) : (
                <span className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/30 text-xs font-semibold">
                  <XCircle className="w-3.5 h-3.5" />
                  <span>DISCONNECTED</span>
                </span>
              )}
            </div>
          </div>

          <p className="text-sm text-slate-300">
            FastAPI application handling REST endpoints, CORS policies, global error handling, and evidence schemas.
          </p>

          {/* Raw JSON inspection block */}
          <div className="bg-slate-950/80 rounded-xl p-4 border border-slate-800/80 font-mono text-xs">
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800 text-slate-400">
              <span className="flex items-center space-x-1.5">
                <Terminal className="w-3.5 h-3.5 text-teal-400" />
                <span>Actual API Response Payload</span>
              </span>
              <span>HTTP {isBackendOk ? '200 OK' : 'ERROR'}</span>
            </div>
            <pre className="text-emerald-400 overflow-x-auto">
              {health.backend.data
                ? JSON.stringify(health.backend.data, null, 2)
                : JSON.stringify({ error: health.backend.error || 'Pending response...' }, null, 2)}
            </pre>
          </div>
        </div>

        {/* Card 2: PostgreSQL Database Health (GET /api/health/database) */}
        <div className="glass-panel p-6 rounded-2xl border-slate-800 space-y-4">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-3">
              <div className={`p-3 rounded-xl ${isDbConnected ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'}`}>
                <Database className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">PostgreSQL Database</h3>
                <p className="text-xs text-slate-400 font-mono">GET /api/health/database</p>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              {isDbConnected ? (
                <span className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-xs font-semibold">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>CONNECTED</span>
                </span>
              ) : (
                <span className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/30 text-xs font-semibold">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  <span>STANDBY / PENDING POSTGRES</span>
                </span>
              )}
            </div>
          </div>

          <p className="text-sm text-slate-300">
            {isDbConnected
              ? `Connected to ${health.database.data?.database_name || 'safevision_db'} on ${health.database.data?.server || 'localhost'}. Live ping succeeded.`
              : 'PostgreSQL connection test executed live via SQLAlchemy engine pool. Connect container/service to sync.'}
          </p>

          {/* Raw DB JSON inspection block */}
          <div className="bg-slate-950/80 rounded-xl p-4 border border-slate-800/80 font-mono text-xs">
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800 text-slate-400">
              <span className="flex items-center space-x-1.5">
                <Terminal className="w-3.5 h-3.5 text-teal-400" />
                <span>Live Database Query Response</span>
              </span>
              <span>{isDbConnected ? 'HTTP 200 OK' : 'HTTP 503 STANDBY'}</span>
            </div>
            <pre className={isDbConnected ? 'text-emerald-400 overflow-x-auto' : 'text-amber-400 overflow-x-auto'}>
              {health.database.data
                ? JSON.stringify(health.database.data, null, 2)
                : JSON.stringify({ error: health.database.error || 'Testing database...' }, null, 2)}
            </pre>
          </div>
        </div>
      </div>

      {/* Database Schema Summary Table */}
      <div className="glass-panel p-6 rounded-2xl border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-white">Database Relational Schema Models</h3>
            <p className="text-xs text-slate-400">
              SQLAlchemy & Alembic Migration Definitions (0001_initial_schema)
            </p>
          </div>
          <span className="px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs font-mono text-teal-400">
            8 Tables Initialized
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-900/80 text-xs uppercase font-semibold text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Table Name</th>
                <th className="py-3 px-4">Primary Key</th>
                <th className="py-3 px-4">Key Foreign Keys / Indexes</th>
                <th className="py-3 px-4">Core Lifecycle / Status Attributes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
              <tr className="hover:bg-slate-900/40">
                <td className="py-3 px-4 font-bold text-teal-300">users</td>
                <td className="py-3 px-4 text-slate-400">user_id (PK)</td>
                <td className="py-3 px-4 text-slate-400">email (Unique Index)</td>
                <td className="py-3 px-4 text-slate-300">role (admin, operator, analyst, viewer)</td>
              </tr>
              <tr className="hover:bg-slate-900/40">
                <td className="py-3 px-4 font-bold text-teal-300">cameras</td>
                <td className="py-3 px-4 text-slate-400">camera_id (PK)</td>
                <td className="py-3 px-4 text-slate-400">camera_name (Index)</td>
                <td className="py-3 px-4 text-slate-300">status (active, inactive, error, maintenance)</td>
              </tr>
              <tr className="hover:bg-slate-900/40">
                <td className="py-3 px-4 font-bold text-teal-300">zones</td>
                <td className="py-3 px-4 text-slate-400">zone_id (PK)</td>
                <td className="py-3 px-4 text-slate-400">camera_id (FK, Index)</td>
                <td className="py-3 px-4 text-slate-300">zone_type (restricted, hazard, monitored, etc.)</td>
              </tr>
              <tr className="hover:bg-slate-900/40">
                <td className="py-3 px-4 font-bold text-teal-300">tracked_entities</td>
                <td className="py-3 px-4 text-slate-400">entity_id (PK)</td>
                <td className="py-3 px-4 text-slate-400">camera_id (FK), track_id (Index)</td>
                <td className="py-3 px-4 text-slate-300">first_seen, last_seen</td>
              </tr>
              <tr className="hover:bg-slate-900/40 bg-teal-950/10">
                <td className="py-3 px-4 font-bold text-teal-300">incidents</td>
                <td className="py-3 px-4 text-slate-400">incident_id (PK)</td>
                <td className="py-3 px-4 text-slate-400">camera_id (FK), entity_id (FK)</td>
                <td className="py-3 px-4 text-amber-300 font-bold">CANDIDATE → VERIFYING → CONFIRMED / RETRACTED</td>
              </tr>
              <tr className="hover:bg-slate-900/40 bg-teal-950/10">
                <td className="py-3 px-4 font-bold text-teal-300">evidence</td>
                <td className="py-3 px-4 text-slate-400">evidence_id (PK)</td>
                <td className="py-3 px-4 text-slate-400">incident_id (FK, Index)</td>
                <td className="py-3 px-4 text-teal-300 font-bold">SUPPORTED | CONTRADICTED | UNKNOWN</td>
              </tr>
              <tr className="hover:bg-slate-900/40">
                <td className="py-3 px-4 font-bold text-teal-300">alerts</td>
                <td className="py-3 px-4 text-slate-400">alert_id (PK)</td>
                <td className="py-3 px-4 text-slate-400">incident_id (FK)</td>
                <td className="py-3 px-4 text-slate-300">severity (low, medium, high, critical), acknowledged</td>
              </tr>
              <tr className="hover:bg-slate-900/40">
                <td className="py-3 px-4 font-bold text-teal-300">event_rules</td>
                <td className="py-3 px-4 text-slate-400">rule_id (PK)</td>
                <td className="py-3 px-4 text-slate-400">event_type (Unique)</td>
                <td className="py-3 px-4 text-slate-300">required_evidence, threshold, verification_duration</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
