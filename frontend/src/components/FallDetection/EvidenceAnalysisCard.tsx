import React from 'react';
import { AlertOctagon, CheckCircle2, RefreshCcw, ShieldCheck, Clock, User, Eye, ArrowRight, Flame, Users, ShieldAlert } from 'lucide-react';
import { Incident } from '../../types';
import { EvidenceChecklist } from './EvidenceChecklist';

interface EvidenceAnalysisCardProps {
  incident: Incident;
  onSeekToTimestamp?: (seconds: number) => void;
}

export const EvidenceAnalysisCard: React.FC<EvidenceAnalysisCardProps> = ({
  incident,
  onSeekToTimestamp,
}) => {
  const isConfirmed = incident.status === 'CONFIRMED';
  const isRetracted = incident.status === 'RETRACTED';
  const et = (incident.event_type || 'fall').toLowerCase();

  const eventTypeLabel = {
    fall: 'FALL',
    intrusion: 'RESTRICTED ZONE',
    fight: 'FIGHTING',
    crowd: 'OVERCROWDING',
  }[et] || et.toUpperCase();

  const getEventTitle = () => {
    if (isConfirmed) {
      if (et === 'intrusion') return 'CONFIRMED RESTRICTED-ZONE INTRUSION';
      if (et === 'fight') return 'CONFIRMED FIGHTING / AGGRESSIVE ACTIVITY';
      if (et === 'crowd') return 'CONFIRMED OVERCROWDING SURGE';
      return 'CONFIRMED FALL DETECTED';
    }
    if (isRetracted) {
      if (et === 'intrusion') return 'ZONE INTRUSION RETRACTED (Exited Perimeter)';
      if (et === 'fight') return 'FIGHT RETRACTED (Subjects Disengaged)';
      if (et === 'crowd') return 'OVERCROWDING RETRACTED (Crowd Dispersed)';
      return 'FALL RETRACTED (Recovery Verified)';
    }
    if (et === 'intrusion') return 'VERIFYING ZONE DWELL TIME';
    if (et === 'fight') return 'VERIFYING INTERACTION DYNAMICS';
    if (et === 'crowd') return 'VERIFYING CROWD DENSITY';
    return 'VERIFYING FALL KINEMATICS';
  };

  const getEventDescription = () => {
    if (isConfirmed) {
      if (et === 'intrusion') return 'Polygonal boundary crossed and sustained dwell verification satisfied.';
      if (et === 'fight') return 'Interpersonal proximity, high kinetic energy, and sustained altercation verified.';
      if (et === 'crowd') return 'Headcount exceeded configured capacity continuously across observation window.';
      return 'Multi-frame kinematic evidence and ground persistence satisfied.';
    }
    if (isRetracted) {
      if (et === 'intrusion') return 'Tracked entity departed restricted zone boundary prior to confirmation.';
      if (et === 'fight') return 'Subjects separated naturally; kinetic energy returned to baseline.';
      if (et === 'crowd') return 'Pedestrian headcount naturally dropped below threshold capacity.';
      return 'Subject resumed upright standing posture during verification window.';
    }
    return 'Multi-frame evidence reasoning active across observation window.';
  };

  const getOverlayLabel = () => {
    if (et === 'fight') return 'Aggressive Altercation & Kinematics Overlay';
    if (et === 'intrusion') return 'Virtual Polygonal Security Perimeter HUD';
    if (et === 'crowd') return 'Spatial Density & Headcount Census HUD';
    return 'Pose Skeleton Overlay';
  };

  const getEventIcon = () => {
    if (isRetracted) return <RefreshCcw className="w-6 h-6 stroke-[2.5]" />;
    if (!isConfirmed) return <ShieldCheck className="w-6 h-6 stroke-[2.5]" />;
    if (et === 'fight') return <Flame className="w-6 h-6 stroke-[2.5]" />;
    if (et === 'crowd') return <Users className="w-6 h-6 stroke-[2.5]" />;
    if (et === 'intrusion') return <AlertOctagon className="w-6 h-6 stroke-[2.5]" />;
    return <ShieldAlert className="w-6 h-6 stroke-[2.5]" />;
  };

  const supportedEvidenceCount = incident.evidence_items?.filter(e => e.status === 'SUPPORTED').length || 0;

  return (
    <div className="glass-panel p-6 rounded-2xl border-slate-800 space-y-6">
      {/* Header Status Banner */}
      <div
        className={`p-4 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
          isConfirmed
            ? et === 'fight'
              ? 'bg-orange-950/30 border-orange-500/50 shadow-lg shadow-orange-950/20'
              : et === 'crowd'
              ? 'bg-sky-950/30 border-sky-500/50 shadow-lg shadow-sky-950/20'
              : et === 'intrusion'
              ? 'bg-amber-950/30 border-amber-500/50 shadow-lg shadow-amber-950/20'
              : 'bg-rose-950/30 border-rose-500/50 shadow-lg shadow-rose-950/20'
            : isRetracted
            ? 'bg-amber-950/30 border-amber-500/50 shadow-lg shadow-amber-950/20'
            : 'bg-emerald-950/30 border-emerald-500/50'
        }`}
      >
        <div className="flex items-center space-x-3">
          <div
            className={`p-2.5 rounded-xl ${
              isConfirmed
                ? et === 'fight'
                  ? 'bg-orange-500 text-slate-950'
                  : et === 'crowd'
                  ? 'bg-sky-500 text-slate-950'
                  : et === 'intrusion'
                  ? 'bg-amber-500 text-slate-950'
                  : 'bg-rose-500 text-slate-950'
                : isRetracted
                ? 'bg-amber-500 text-slate-950'
                : 'bg-emerald-500 text-slate-950'
            }`}
          >
            {getEventIcon()}
          </div>

          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span
                className={`px-2 py-0.5 rounded text-[10px] font-mono font-extrabold uppercase tracking-wide ${
                  et === 'intrusion'
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                    : et === 'fight'
                    ? 'bg-orange-500/20 text-orange-300 border border-orange-500/40'
                    : et === 'crowd'
                    ? 'bg-sky-500/20 text-sky-300 border border-sky-500/40'
                    : 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                }`}
              >
                {eventTypeLabel}
              </span>
              <span className="text-base font-extrabold tracking-tight text-white">
                {getEventTitle()}
              </span>
              <span
                className={`px-2 py-0.5 rounded text-[11px] font-mono font-bold uppercase ${
                  isConfirmed
                    ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                    : isRetracted
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                    : 'bg-teal-500/20 text-teal-300 border border-teal-500/30'
                }`}
              >
                {incident.status}
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-1">
              {getEventDescription()}
            </p>
          </div>
        </div>

        {/* Telemetry Pills */}
        <div className="flex items-center space-x-2">
          {onSeekToTimestamp && (
            <button
              onClick={() => onSeekToTimestamp(incident.timestamp_sec)}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-teal-300 text-xs font-mono transition"
            >
              <Clock className="w-3.5 h-3.5 text-teal-400" />
              <span>Seek {incident.timestamp_formatted}</span>
              <ArrowRight className="w-3 h-3 text-slate-400" />
            </button>
          )}
        </div>
      </div>

      {/* Alert Decision Banner (Evidence-Complete Alerting) */}
      <div
        className={`p-3.5 rounded-xl border flex items-center justify-between text-xs ${
          incident.should_alert
            ? 'bg-rose-950/40 border-rose-500/60 text-rose-200'
            : 'bg-slate-900/60 border-slate-800 text-slate-400'
        }`}
      >
        <div className="flex items-center space-x-2.5">
          {incident.should_alert ? (
            <AlertOctagon className="w-4 h-4 text-rose-400 flex-shrink-0 animate-pulse" />
          ) : (
            <ShieldCheck className="w-4 h-4 text-teal-400 flex-shrink-0" />
          )}
          <div>
            <span className="font-semibold text-white">
              {incident.should_alert
                ? `🔔 Alert Dispatched (Alert #${incident.alert_id || 'ACTIVE'}): `
                : '🛡️ Alert Status: '}
            </span>
            <span>
              {incident.should_alert
                ? incident.alert_message || `Critical ${eventTypeLabel} incident confirmed with complete 5-point evidence.`
                : `No alert dispatched. System requires CONFIRMED status with complete evidence (Current: ${incident.status}).`}
            </span>
          </div>
        </div>
        <span
          className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold flex-shrink-0 ${
            incident.should_alert
              ? 'bg-rose-900/60 text-rose-300 border border-rose-700/60'
              : 'bg-slate-800 text-slate-300 border border-slate-700'
          }`}
        >
          {incident.should_alert ? 'POSTGRESQL ALERT CREATED' : 'ALERT SUPPRESSED'}
        </span>
      </div>

      {/* Grid: Incident Metadata + Evidence Image */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Metrics & Evidence Checklist */}
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
              <p className="text-[11px] text-slate-400 uppercase font-semibold">
                {et === 'crowd'
                  ? 'Monitored Region'
                  : et === 'fight'
                  ? 'Participants'
                  : et === 'intrusion'
                  ? 'Intruder Track'
                  : 'Person Track ID'}
              </p>
              <p className="text-lg font-mono font-bold text-white mt-0.5 truncate">
                {et === 'crowd'
                  ? 'Sector Area'
                  : incident.participant_ids && incident.participant_ids.length > 0
                  ? incident.participant_ids.map(id => `#${id}`).join(', ')
                  : incident.track_id
                  ? `#${incident.track_id}`
                  : `#${incident.entity_id || '1'}`}
              </p>
            </div>

            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
              <p className="text-[11px] text-slate-400 uppercase font-semibold">Evidence Score</p>
              <p className="text-lg font-mono font-bold text-teal-400 mt-0.5">
                {incident.confidence.toFixed(2)}
              </p>
            </div>

            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
              <p className="text-[11px] text-slate-400 uppercase font-semibold">Completeness</p>
              <p className="text-sm font-mono font-bold text-slate-200 mt-1">
                {incident.is_evidence_complete ? (
                  <span className="text-emerald-400">COMPLETE ({supportedEvidenceCount}/5)</span>
                ) : (
                  <span className="text-amber-400">{supportedEvidenceCount}/5 SUPPORTED</span>
                )}
              </p>
            </div>
          </div>

            {/* 3-State Evidence Checklist */}
            {incident.evidence_items && incident.evidence_items.length > 0 && (
              <EvidenceChecklist evidenceItems={incident.evidence_items} />
            )}

            {/* Temporal Evolution Trace */}
            {incident.temporal_trace && incident.temporal_trace.length > 0 && (
              <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <h5 className="text-[11px] font-semibold uppercase text-slate-400 font-mono">
                    Temporal Evidence Lifecycle Trace
                  </h5>
                  <span className="text-[10px] font-mono text-teal-400">
                    {incident.temporal_trace.length} Snapshots
                  </span>
                </div>
                <div className="flex flex-wrap items-center gap-1.5 text-[11px] font-mono">
                  {incident.temporal_trace.map((snap, sIdx) => (
                    <div
                      key={sIdx}
                      className={`px-2 py-1 rounded border flex items-center space-x-1.5 ${
                        snap.state === 'CONFIRMED'
                          ? 'bg-rose-950/50 border-rose-800/60 text-rose-300'
                          : snap.state === 'VERIFYING'
                          ? 'bg-teal-950/50 border-teal-800/60 text-teal-300'
                          : snap.state === 'CANDIDATE'
                          ? 'bg-amber-950/50 border-amber-800/60 text-amber-300'
                          : 'bg-slate-900 border-slate-800 text-slate-400'
                      }`}
                    >
                      <span>F{snap.frame_idx}</span>
                      <span className="text-[9px] font-bold uppercase">({snap.state})</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right: Annotated Evidence Image Frame */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
                <Eye className="w-4 h-4 text-teal-400" />
                <span>Annotated Evidence Frame Snapshot</span>
              </h4>
              <span className="text-[10px] font-mono text-slate-400">{getOverlayLabel()}</span>
            </div>

            <div className="rounded-xl overflow-hidden border border-slate-800 bg-slate-950 aspect-video flex items-center justify-center relative shadow-inner">
              {(incident.evidence_frame_url || incident.evidence_image_url) ? (
                <img
                  src={incident.evidence_frame_url || incident.evidence_image_url || ''}
                  alt="Safety Event Evidence Frame Snapshot Overlay"
                  className="w-full h-full object-contain bg-slate-950"
                />
              ) : (
                <div className="text-center p-6 text-slate-500 text-xs font-mono">
                  No visual evidence snapshot generated
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };
