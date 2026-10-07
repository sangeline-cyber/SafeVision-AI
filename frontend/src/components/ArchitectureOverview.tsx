import React from 'react';
import { Layers, Cpu } from 'lucide-react';

export const ArchitectureOverview: React.FC = () => {
  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="glass-panel p-6 rounded-2xl border-slate-800 bg-gradient-to-r from-slate-900/90 to-slate-900/40">
        <div className="max-w-3xl">
          <span className="px-3 py-1 rounded-full text-xs font-semibold bg-teal-500/10 text-teal-400 border border-teal-500/20">
            HNX26PSI07 Problem Statement Alignment
          </span>
          <h2 className="text-2xl font-bold text-white mt-3">
            Autonomous Vision & Safety Behaviour Understanding Architecture
          </h2>
          <p className="text-sm text-slate-300 mt-2 leading-relaxed">
            SafeVision AI replaces generic, noisy "weird behaviour detection" with a deterministic, evidence-grounded safety monitoring pipeline. Normal activities (standing, sitting, bending, talking, phone usage) are contextualized and separated from genuine safety hazards.
          </p>
        </div>
      </div>

      {/* 5 Core Differentiating Pillars */}
      <div>
        <h3 className="text-lg font-bold text-white mb-4 flex items-center space-x-2">
          <Layers className="w-5 h-5 text-teal-400" />
          <span>The 5 Core Differentiating Engineering Features</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {/* Pillar 1 */}
          <div className="glass-panel p-5 rounded-xl border-slate-800 space-y-3">
            <div className="w-9 h-9 rounded-lg bg-teal-500/10 text-teal-400 flex items-center justify-center font-bold text-sm">
              01
            </div>
            <h4 className="font-bold text-white text-base">Event-Specific Evidence Schema</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Every safety incident type requires a distinct set of multi-frame sensory evidence (e.g., fall requires upright-to-ground transition, velocity, ground persistence, and recovery check).
            </p>
          </div>

          {/* Pillar 2 */}
          <div className="glass-panel p-5 rounded-xl border-slate-800 space-y-3">
            <div className="w-9 h-9 rounded-lg bg-cyan-500/10 text-cyan-400 flex items-center justify-center font-bold text-sm">
              02
            </div>
            <h4 className="font-bold text-white text-base">Three-State Evidence Reasoning</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Evidence uses ternary logic: <span className="text-emerald-400 font-semibold">SUPPORTED</span>, <span className="text-rose-400 font-semibold">CONTRADICTED</span>, and <span className="text-amber-400 font-semibold">UNKNOWN</span>. Partial occlusions produce <code className="text-amber-300">UNKNOWN</code>, never assumed false.
            </p>
          </div>

          {/* Pillar 3 */}
          <div className="glass-panel p-5 rounded-xl border-slate-800 space-y-3">
            <div className="w-9 h-9 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center font-bold text-sm">
              03
            </div>
            <h4 className="font-bold text-white text-base">Reversible Incident Reasoning</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Incidents transition across a reversible lifecycle: <span className="text-amber-300 font-mono">CANDIDATE</span> → <span className="text-cyan-300 font-mono">VERIFYING</span> → <span className="text-emerald-300 font-mono">CONFIRMED</span> or <span className="text-rose-300 font-mono">RETRACTED</span> if person resumes normal posture.
            </p>
          </div>

          {/* Pillar 4 */}
          <div className="glass-panel p-5 rounded-xl border-slate-800 space-y-3">
            <div className="w-9 h-9 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center font-bold text-sm">
              04
            </div>
            <h4 className="font-bold text-white text-base">Evidence-Complete Alerting</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Alerts trigger strictly when all required evidence items meet confidence and duration thresholds. Premature triggers on single ambiguous frames are strictly prohibited.
            </p>
          </div>

          {/* Pillar 5 */}
          <div className="glass-panel p-5 rounded-xl border-slate-800 space-y-3 md:col-span-2 lg:col-span-2">
            <div className="w-9 h-9 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center font-bold text-sm">
              05
            </div>
            <h4 className="font-bold text-white text-base">Temporal Multi-Frame Lifecycle</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Maintains rolling temporal buffers across multi-frame sequences. Bending over momentarily is differentiated from a sustained fall through continuous temporal velocity tracking.
            </p>
          </div>
        </div>
      </div>

      {/* Pipeline Sequence Diagram */}
      <div className="glass-panel p-6 rounded-2xl border-slate-800 space-y-6">
        <h3 className="text-lg font-bold text-white flex items-center space-x-2">
          <Cpu className="w-5 h-5 text-teal-400" />
          <span>Multi-Stage Autonomous Vision Pipeline</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 relative">
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-col justify-between">
            <div>
              <span className="text-[11px] font-mono text-teal-400 uppercase font-bold">Stage 1</span>
              <h5 className="font-bold text-white text-sm mt-1">Detection</h5>
              <p className="text-[11px] text-slate-400 mt-1">YOLOv8 / YOLOv11 Person & Object BBoxes</p>
            </div>
            <div className="mt-3 text-[10px] text-slate-500 font-mono">Interfaces Defined</div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-col justify-between">
            <div>
              <span className="text-[11px] font-mono text-teal-400 uppercase font-bold">Stage 2</span>
              <h5 className="font-bold text-white text-sm mt-1">ByteTrack Tracking</h5>
              <p className="text-[11px] text-slate-400 mt-1">Continuous ID Association & Velocity Vectors</p>
            </div>
            <div className="mt-3 text-[10px] text-slate-500 font-mono">Interfaces Defined</div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-col justify-between">
            <div>
              <span className="text-[11px] font-mono text-teal-400 uppercase font-bold">Stage 3</span>
              <h5 className="font-bold text-white text-sm mt-1">Pose & Action</h5>
              <p className="text-[11px] text-slate-400 mt-1">Keypoints (Hips, Head, Knees) & Optical Flow</p>
            </div>
            <div className="mt-3 text-[10px] text-slate-500 font-mono">Interfaces Defined</div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-col justify-between">
            <div>
              <span className="text-[11px] font-mono text-teal-400 uppercase font-bold">Stage 4</span>
              <h5 className="font-bold text-white text-sm mt-1">Evidence Reasoner</h5>
              <p className="text-[11px] text-slate-400 mt-1">3-State Logic & Reversible Verification</p>
            </div>
            <div className="mt-3 text-[10px] text-teal-400 font-mono">Core Differentiator</div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-col justify-between">
            <div>
              <span className="text-[11px] font-mono text-teal-400 uppercase font-bold">Stage 5</span>
              <h5 className="font-bold text-white text-sm mt-1">Alerting & DB</h5>
              <p className="text-[11px] text-slate-400 mt-1">PostgreSQL Event Logging & Notifications</p>
            </div>
            <div className="mt-3 text-[10px] text-emerald-400 font-mono">Foundation Active</div>
          </div>
        </div>
      </div>
    </div>
  );
};
