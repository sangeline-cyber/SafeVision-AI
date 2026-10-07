import React, { useState } from 'react';
import { Shield, AlertOctagon, Flame, Users, CheckCircle, XCircle, HelpCircle } from 'lucide-react';
import { EventType } from '../types';

interface EventSchemaDetail {
  id: EventType;
  title: string;
  icon: React.ReactNode;
  risk: string;
  description: string;
  evidenceItems: {
    name: string;
    requirement: string;
    role: string;
  }[];
  normalContrast: string;
  retractionTrigger: string;
}

const SCHEMAS: EventSchemaDetail[] = [
  {
    id: 'fall',
    title: 'Fall / Person Down',
    icon: <Shield className="w-5 h-5 text-rose-400" />,
    risk: 'Critical',
    description: 'Autonomous detection of falls while distinguishing benign bending, sitting, or tying shoes.',
    evidenceItems: [
      { name: '1. DOWNWARD_MOVEMENT', requirement: 'Center-of-mass downward velocity exceeding kinematic descent threshold', role: 'Kinematic Dynamic' },
      { name: '2. POSTURE_TRANSITION', requirement: 'Torso angle rotation exceeding angular transition threshold (> 45°)', role: 'Pose Geometry' },
      { name: '3. LOW_OR_HORIZONTAL_POSTURE', requirement: 'Prone orientation (W/H aspect ratio > 1.2) and low bounding box height', role: 'Ground Confirmation' },
      { name: '4. REMAINS_DOWN', requirement: 'Entity remains stationary on ground across persistence window (no recovery)', role: 'Temporal Persistence' },
      { name: '5. TEMPORAL_CONSISTENCY', requirement: 'Coherent sequence verified across consecutive multi-frame timeline', role: 'Verification Rule' },
    ],
    normalContrast: 'Sitting on a chair or bending to tie a shoelace maintains controlled downward velocity and does not satisfy the sudden posture collapse criteria.',
    retractionTrigger: 'If person rises back to upright standing posture during the VERIFYING window, status switches to RETRACTED.',
  },
  {
    id: 'intrusion',
    title: 'Restricted-Zone Intrusion',
    icon: <AlertOctagon className="w-5 h-5 text-amber-400" />,
    risk: 'High',
    description: 'Detection of unauthorized entry across virtual polygonal security perimeter zones.',
    evidenceItems: [
      { name: 'Entity Identification', requirement: 'Persistent tracked entity ID from ByteTrack', role: 'Tracking ID' },
      { name: 'Boundary Crossing', requirement: 'Foot/centroid vector crossing polygon edge', role: 'Spatial Geometry' },
      { name: 'Crossing Direction', requirement: 'Inward normal vector into restricted sector', role: 'Vector Heading' },
      { name: 'Duration in Zone', requirement: 'Time elapsed inside perimeter exceeds dwell threshold', role: 'Temporal Dwell' },
      { name: 'Zone Context & Schedule', requirement: 'Active security schedule and zone risk classification', role: 'Context Filter' },
    ],
    normalContrast: 'Walking along the exterior boundary without crossing does not trigger candidate status.',
    retractionTrigger: 'Immediate reversal / accidental step back across perimeter within 1 second marks incident as RETRACTED.',
  },
  {
    id: 'fight',
    title: 'Fighting / Aggressive Activity',
    icon: <Flame className="w-5 h-5 text-orange-400" />,
    risk: 'Critical',
    description: 'Detection of violent physical altercations differentiated from benign social interactions.',
    evidenceItems: [
      { name: 'Multiple Entities', requirement: 'At least 2 tracked individuals in proximity (< 1.5m)', role: 'Multi-Entity' },
      { name: 'Interpersonal Interaction', requirement: 'Overlapping bounding boxes or high interaction graph score', role: 'Spatial Relation' },
      { name: 'High-Energy Motion', requirement: 'Rapid acceleration and high kinetic optical flow energy', role: 'Kinetic Metric' },
      { name: 'Temporal Persistence', requirement: 'Violent agitation sustained over window (> 2.0s)', role: 'Temporal Verification' },
    ],
    normalContrast: 'People hugging, greeting, or casually walking together maintain low kinetic acceleration variance.',
    retractionTrigger: 'Isolated brief sudden movement without continuation retracts back to normal.',
  },
  {
    id: 'crowd',
    title: 'Crowd / Overcrowding',
    icon: <Users className="w-5 h-5 text-cyan-400" />,
    risk: 'Medium',
    description: 'Detection of dangerous crowd density surge and bottleneck congestion.',
    evidenceItems: [
      { name: 'Head/Person Count', requirement: 'Number of unique entities detected in defined zone', role: 'Entity Density' },
      { name: 'Spatial Concentration', requirement: 'Cluster density (persons / square meter)', role: 'Density Metric' },
      { name: 'Temporal Growth Rate', requirement: 'Positive rate of inflow exceeding safety threshold', role: 'Flow Dynamic' },
      { name: 'Bottleneck Dwell Time', requirement: 'Reduced mean velocity inside congested zone', role: 'Congestion Metric' },
    ],
    normalContrast: 'Normal transit queue moving at standard pace without accumulation does not trigger warning.',
    retractionTrigger: 'Crowd dispersing naturally drops density below threshold and marks incident resolved.',
  },
];

export const EvidenceSchemaViewer: React.FC = () => {
  const [selectedSchema, setSelectedSchema] = useState<EventType>('fall');
  const current = SCHEMAS.find((s) => s.id === selectedSchema) || SCHEMAS[0];

  return (
    <div className="space-y-6">
      {/* Event Selector Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {SCHEMAS.map((schema) => {
          const isSelected = schema.id === selectedSchema;
          return (
            <button
              key={schema.id}
              onClick={() => setSelectedSchema(schema.id)}
              className={`text-left p-4 rounded-xl border transition-all ${
                isSelected
                  ? 'bg-teal-950/30 border-teal-500/60 shadow-lg shadow-teal-500/10'
                  : 'glass-panel border-slate-800 hover:border-slate-700 opacity-80 hover:opacity-100'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                  {schema.icon}
                </div>
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-400">
                  {schema.risk}
                </span>
              </div>
              <h4 className="font-bold text-white text-sm">{schema.title}</h4>
              <p className="text-xs text-slate-400 mt-1 line-clamp-2">{schema.description}</p>
            </button>
          );
        })}
      </div>

      {/* Detailed Schema Card */}
      <div className="glass-panel p-6 rounded-2xl border-slate-800 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-xl font-bold text-white">{current.title} Evidence Schema</h3>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-teal-500/20 text-teal-300 border border-teal-500/30">
                Phase 2 Blueprint
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">{current.description}</p>
          </div>

          <div className="flex items-center space-x-2 text-xs font-mono">
            <span className="flex items-center space-x-1 text-emerald-400 bg-emerald-950/40 px-2 py-1 rounded border border-emerald-800/40">
              <CheckCircle className="w-3.5 h-3.5" />
              <span>SUPPORTED</span>
            </span>
            <span className="flex items-center space-x-1 text-rose-400 bg-rose-950/40 px-2 py-1 rounded border border-rose-800/40">
              <XCircle className="w-3.5 h-3.5" />
              <span>CONTRADICTED</span>
            </span>
            <span className="flex items-center space-x-1 text-amber-400 bg-amber-950/40 px-2 py-1 rounded border border-amber-800/40">
              <HelpCircle className="w-3.5 h-3.5" />
              <span>UNKNOWN</span>
            </span>
          </div>
        </div>

        {/* Evidence Requirements Checklist */}
        <div>
          <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
            Multi-Frame Required Evidence Items:
          </h4>

          <div className="space-y-2.5">
            {current.evidenceItems.map((item, idx) => (
              <div
                key={idx}
                className="flex items-start justify-between p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 text-sm"
              >
                <div className="flex items-start space-x-3">
                  <span className="w-6 h-6 rounded-full bg-slate-900 border border-slate-700 text-teal-400 font-mono text-xs flex items-center justify-center font-bold flex-shrink-0 mt-0.5">
                    {idx + 1}
                  </span>
                  <div>
                    <p className="font-semibold text-slate-200">{item.name}</p>
                    <p className="text-xs text-slate-400 mt-0.5">{item.requirement}</p>
                  </div>
                </div>
                <span className="text-[11px] font-mono text-slate-400 bg-slate-900 px-2.5 py-1 rounded border border-slate-800">
                  {item.role}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Normal Contrast & Retraction Trigger */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
          <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800/60">
            <h5 className="text-xs font-bold uppercase text-teal-400 font-mono mb-1">
              Normal Activity Contrast (No False Anomaly)
            </h5>
            <p className="text-xs text-slate-300 leading-relaxed">{current.normalContrast}</p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800/60">
            <h5 className="text-xs font-bold uppercase text-amber-400 font-mono mb-1">
              Reversible Lifecycle Retraction Rule
            </h5>
            <p className="text-xs text-slate-300 leading-relaxed">{current.retractionTrigger}</p>
          </div>
        </div>
      </div>
    </div>
  );
};
