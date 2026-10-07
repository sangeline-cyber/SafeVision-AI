import React, { useRef, useImperativeHandle, forwardRef } from 'react';
import { Play, Pause, Clock, AlertTriangle, Film } from 'lucide-react';
import { Incident } from '../../types';

export interface VideoPlayerRef {
  seekTo: (seconds: number) => void;
}

interface VideoPlayerPreviewProps {
  videoUrl: string;
  filename: string;
  incidents: Incident[];
}

export const VideoPlayerPreview = forwardRef<VideoPlayerRef, VideoPlayerPreviewProps>(
  ({ videoUrl, filename, incidents }, ref) => {
    const videoRef = useRef<HTMLVideoElement>(null);

    useImperativeHandle(ref, () => ({
      seekTo: (seconds: number) => {
        if (videoRef.current) {
          videoRef.current.currentTime = seconds;
          videoRef.current.play();
        }
      },
    }));

    return (
      <div className="glass-panel p-6 rounded-2xl border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Film className="w-5 h-5 text-teal-400" />
            <h3 className="text-lg font-bold text-white">Video Playback Preview</h3>
          </div>
          <span className="text-xs font-mono text-slate-400 bg-slate-900 px-3 py-1 rounded-full border border-slate-800">
            {filename}
          </span>
        </div>

        {/* Video Player */}
        <div className="rounded-xl overflow-hidden bg-slate-950 border border-slate-800 aspect-video relative shadow-2xl">
          <video
            ref={videoRef}
            src={videoUrl}
            controls
            className="w-full h-full object-contain"
            playsInline
          />
        </div>

        {/* Interactive Incident Seek Markers */}
        {incidents.length > 0 && (
          <div className="space-y-2 pt-2">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Jump to Detected Incident Timestamps:
            </p>
            <div className="flex flex-wrap gap-2">
              {incidents.map((inc, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    if (videoRef.current) {
                      videoRef.current.currentTime = inc.timestamp_sec;
                      videoRef.current.play();
                    }
                  }}
                  className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-mono transition border ${
                    inc.status === 'CONFIRMED'
                      ? 'bg-rose-950/40 hover:bg-rose-900/60 border-rose-700/60 text-rose-300'
                      : inc.status === 'RETRACTED'
                      ? 'bg-amber-950/40 hover:bg-amber-900/60 border-amber-700/60 text-amber-300'
                      : 'bg-teal-950/40 hover:bg-teal-900/60 border-teal-700/60 text-teal-300'
                  }`}
                >
                  <Clock className="w-3.5 h-3.5" />
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-900/90 font-bold text-white uppercase border border-slate-700">
                    {inc.event_type || 'FALL'}
                  </span>
                  <span>
                    {inc.event_type?.toUpperCase() === 'CROWD'
                      ? `Surge at ${inc.timestamp_formatted}`
                      : inc.event_type?.toUpperCase() === 'FIGHT'
                      ? `Fight at ${inc.timestamp_formatted}`
                      : inc.event_type?.toUpperCase() === 'INTRUSION'
                      ? `Intrusion at ${inc.timestamp_formatted}`
                      : `Track #${inc.track_id || '1'} at ${inc.timestamp_formatted}`}
                  </span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-900/80 font-bold">
                    {inc.status}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }
);
