import React from 'react';
import { CheckCircle2, XCircle, HelpCircle } from 'lucide-react';
import { EvidenceItem } from '../../types';

interface EvidenceChecklistProps {
  evidenceItems: EvidenceItem[];
}

export const EvidenceChecklist: React.FC<EvidenceChecklistProps> = ({ evidenceItems }) => {
  return (
    <div className="space-y-3">
      <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center justify-between">
        <span>Evidence Checklist (5-Category Reasoning)</span>
        <span className="font-mono text-[10px] text-teal-400">Ternary Kleene Logic</span>
      </h4>

      <div className="space-y-2">
        {evidenceItems.map((item, idx) => {
          const isSupported = item.status === 'SUPPORTED';
          const isContradicted = item.status === 'CONTRADICTED';
          const isUnknown = item.status === 'UNKNOWN';

          const categoryNames: Record<string, string> = {
            // Fall Evidence Categories
            DOWNWARD_MOVEMENT: 'Downward Movement',
            POSTURE_TRANSITION: 'Posture Transition',
            LOW_OR_HORIZONTAL_POSTURE: 'Low/Horizontal Posture',
            REMAINS_DOWN: 'Remains Down',
            TEMPORAL_CONSISTENCY: 'Temporal Consistency',
            rapid_downward_velocity: 'Downward Movement',
            posture_transition_collapse: 'Posture Transition',
            ground_level_orientation: 'Low/Horizontal Posture',
            sustained_ground_persistence: 'Remains Down',
            recovery_absence: 'Recovery Absence (Temporal)',
            // Restricted-Zone Intrusion Categories
            ZONE_BOUNDARY_PROXIMITY: 'Zone Boundary Proximity',
            POLYGON_INTERSECTION: 'Polygon Intersection',
            ZONE_DWELL_TIME: 'Zone Dwell Time',
            TEMPORAL_PERSISTENCE: 'Temporal Persistence',
            ACTIVE_SCHEDULE_RESTRICTION: 'Active Schedule Restriction',
            // Fighting / Altercation Categories
            MULTI_PERSON_PROXIMITY: 'Multi-Person Proximity',
            MUTUAL_INTERACTION_DYNAMICS: 'Mutual Interaction Dynamics',
            HIGH_KINETIC_MOTION: 'High Kinetic Motion',
            SUSTAINED_ENGAGEMENT: 'Sustained Engagement',
            // Overcrowding Categories
            HEADCOUNT_THRESHOLD_EXCEEDED: 'Headcount Threshold Exceeded',
            SPATIAL_DENSITY_CONCENTRATION: 'Spatial Density Concentration',
            SUSTAINED_CROWD_PRESENCE: 'Sustained Crowd Presence',
            INFLOW_RATE_ACCUMULATION: 'Inflow Rate Accumulation',
          };
          const displayName = categoryNames[item.evidence_type] || item.evidence_type.replace(/_/g, ' ');

          return (
            <div
              key={idx}
              className={`p-3 rounded-xl border transition-all text-xs ${
                isSupported
                  ? 'bg-emerald-950/20 border-emerald-800/40 text-emerald-200'
                  : isContradicted
                  ? 'bg-rose-950/20 border-rose-800/40 text-rose-200'
                  : 'bg-amber-950/20 border-amber-800/40 text-amber-200'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-start space-x-2.5">
                  {isSupported && <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />}
                  {isContradicted && <XCircle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />}
                  {isUnknown && <HelpCircle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />}

                  <div>
                    <p className="font-semibold text-slate-100 flex items-center space-x-1.5">
                      <span>{displayName}</span>
                      <span className="text-slate-500 font-mono text-[10px]">―</span>
                      <span
                        className={`text-[11px] font-mono font-bold ${
                          isSupported
                            ? 'text-emerald-400'
                            : isContradicted
                            ? 'text-rose-400'
                            : 'text-amber-400'
                        }`}
                      >
                        {item.status}
                      </span>
                    </p>
                    <p className="text-[11px] text-slate-300 mt-0.5 leading-relaxed">
                      {item.description}
                    </p>
                  </div>
                </div>

                <div className="flex flex-col items-end flex-shrink-0">
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                      isSupported
                        ? 'bg-emerald-900/60 text-emerald-300 border border-emerald-700/50'
                        : isContradicted
                        ? 'bg-rose-900/60 text-rose-300 border border-rose-700/50'
                        : 'bg-amber-900/60 text-amber-300 border border-amber-700/50'
                    }`}
                  >
                    {item.status}
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono mt-1">
                    Conf: {(item.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
