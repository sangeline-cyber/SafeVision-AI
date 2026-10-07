import React, { useState, useRef } from 'react';
import { Shield, CheckCircle2, AlertTriangle, RefreshCw, Cpu, Activity, Info } from 'lucide-react';
import { videoApi } from '../services/api';
import { VideoAnalysisResult, VideoUploadResult } from '../types';
import { VideoUploader } from '../components/FallDetection/VideoUploader';
import { VideoPlayerPreview, VideoPlayerRef } from '../components/FallDetection/VideoPlayerPreview';
import { EvidenceAnalysisCard } from '../components/FallDetection/EvidenceAnalysisCard';

export const FallDetectionPage: React.FC = () => {
  const [uploadedVideo, setUploadedVideo] = useState<VideoUploadResult | null>(null);
  const [analysisResult, setAnalysisResult] = useState<VideoAnalysisResult | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingStatusText, setProcessingStatusText] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const playerRef = useRef<VideoPlayerRef>(null);

  const [filterEventType, setFilterEventType] = useState<string>('ALL');

  const handleUploadAndAnalyze = async (file: File) => {
    setIsProcessing(true);
    setErrorMessage(null);
    setAnalysisResult(null);
    setUploadedVideo(null); // Clear previous video player and state immediately
    setFilterEventType('ALL');
    setUploadProgress(0);
    setProcessingStatusText('Uploading surveillance video to server...');

    try {
      // 1. Upload Video
      const uploadRes = await videoApi.uploadVideo(file, (percent) => {
        setUploadProgress(percent);
        setProcessingStatusText(`Uploading video... ${percent}%`);
      });
      setUploadedVideo(uploadRes);

      // 2. Process Video with real YOLO Pose and Evidence Reasoning
      setProcessingStatusText('Running real YOLO Pose inference & 3-state temporal verification...');
      const result = await videoApi.processVideo(uploadRes.video_id);
      setAnalysisResult(result);
    } catch (err: any) {
      console.error('Video processing error:', err);
      const detail = err.response?.data?.detail || err.message || 'Failed to process video';
      setErrorMessage(detail);
    } finally {
      setIsProcessing(false);
      setProcessingStatusText('');
    }
  };

  const handleSeek = (seconds: number) => {
    playerRef.current?.seekTo(seconds);
  };

  const incidentsToDisplay = analysisResult?.incidents.filter((inc) => {
    if (filterEventType === 'ALL') return true;
    return (inc.event_type || 'FALL').toUpperCase() === filterEventType;
  }) || [];

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="glass-panel p-6 rounded-2xl border-slate-800 bg-gradient-to-r from-slate-900/90 via-slate-900/60 to-rose-950/20">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/30 flex items-center space-x-1.5">
                <Shield className="w-3.5 h-3.5" />
                <span>Multi-Event Real AI Safety Suite Active</span>
              </span>
              <span className="text-xs font-mono text-slate-400">4-Event Autonomous Perception & Evidence Engine</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              Autonomous Safety Event Detection & Evidence Verification
            </h1>
            <p className="text-slate-300 text-sm max-w-3xl leading-relaxed">
              Upload surveillance footage to run real-time perception across all 4 core safety events: Fall Detection, Restricted-Zone Intrusion, Fighting/Aggressive Altercations, and Overcrowding. Evaluated using multi-frame 3-state temporal Kleene evidence reasoning.
            </p>
          </div>

          <div className="flex items-center space-x-3 bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
            <div className="text-right">
              <p className="text-[11px] text-slate-400 uppercase font-semibold">AI Model</p>
              <p className="text-sm font-mono font-bold text-teal-400">YOLO Pose</p>
            </div>
            <div className="h-8 w-px bg-slate-800" />
            <div className="text-right">
              <p className="text-[11px] text-slate-400 uppercase font-semibold">Logic Engine</p>
              <p className="text-sm font-mono font-bold text-slate-200">3-State Kleene</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid: Upload & Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Uploader */}
        <div className="lg:col-span-5 space-y-6">
          <VideoUploader
            onUploadAndAnalyze={handleUploadAndAnalyze}
            isProcessing={isProcessing}
            uploadProgress={uploadProgress}
          />

          {/* Processing Status Banner */}
          {isProcessing && (
            <div className="glass-panel p-5 rounded-2xl border-teal-500/40 bg-teal-950/20 space-y-3">
              <div className="flex items-center space-x-2 text-teal-300 text-sm font-bold">
                <RefreshCw className="w-4 h-4 animate-spin text-teal-400" />
                <span>Video Analysis In Progress</span>
              </div>
              <p className="text-xs text-slate-300">{processingStatusText}</p>
              <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800">
                <div
                  className="bg-teal-400 h-2 transition-all duration-300 animate-pulse"
                  style={{ width: `${uploadProgress || 65}%` }}
                />
              </div>
            </div>
          )}

          {/* Error Banner */}
          {errorMessage && (
            <div className="glass-panel p-5 rounded-2xl border-rose-500/40 bg-rose-950/20 text-xs text-rose-300 space-y-2">
              <div className="flex items-center space-x-2 text-rose-400 font-bold">
                <AlertTriangle className="w-4 h-4" />
                <span>Processing Error</span>
              </div>
              <p>{errorMessage}</p>
            </div>
          )}
        </div>

        {/* Right Column: Video Playback & Summary */}
        <div className="lg:col-span-7 space-y-6">
          {uploadedVideo ? (
            <VideoPlayerPreview
              ref={playerRef}
              videoUrl={uploadedVideo.video_url}
              filename={uploadedVideo.filename}
              incidents={analysisResult?.incidents || []}
            />
          ) : (
            <div className="glass-panel p-12 rounded-2xl border-slate-800 text-center space-y-3 flex flex-col items-center justify-center min-h-[300px]">
              <div className="p-4 rounded-full bg-slate-900/80 border border-slate-800 text-slate-500">
                <Cpu className="w-8 h-8" />
              </div>
              <h3 className="text-base font-bold text-slate-300">No Video Loaded</h3>
              <p className="text-xs text-slate-500 max-w-sm">
                Upload a video on the left to start live multi-event safety verification.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Results Section */}
      {analysisResult && (
        <div className="space-y-6">
          {/* Summary Stat Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800">
              <p className="text-[10px] uppercase font-bold text-slate-400">Total Incidents</p>
              <p className="text-2xl font-mono font-bold text-white mt-0.5">
                {analysisResult.summary.total_incidents}
              </p>
            </div>
            <div className="p-3.5 rounded-xl bg-rose-950/20 border border-rose-900/40">
              <p className="text-[10px] uppercase font-bold text-rose-400">Falls</p>
              <p className="text-2xl font-mono font-bold text-rose-200 mt-0.5">
                {analysisResult.summary.confirmed_falls || 0}
              </p>
            </div>
            <div className="p-3.5 rounded-xl bg-orange-950/20 border border-orange-900/40">
              <p className="text-[10px] uppercase font-bold text-orange-400">Fights</p>
              <p className="text-2xl font-mono font-bold text-orange-200 mt-0.5">
                {analysisResult.summary.confirmed_fights || 0}
              </p>
            </div>
            <div className="p-3.5 rounded-xl bg-amber-950/20 border border-amber-900/40">
              <p className="text-[10px] uppercase font-bold text-amber-400">Intrusions</p>
              <p className="text-2xl font-mono font-bold text-amber-200 mt-0.5">
                {analysisResult.summary.confirmed_intrusions || 0}
              </p>
            </div>
            <div className="p-3.5 rounded-xl bg-sky-950/20 border border-sky-900/40">
              <p className="text-[10px] uppercase font-bold text-sky-400">Crowd Surges</p>
              <p className="text-2xl font-mono font-bold text-sky-200 mt-0.5">
                {analysisResult.summary.confirmed_crowd || 0}
              </p>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center space-x-2">
                <Activity className="w-5 h-5 text-teal-400" />
                <span>AI Video Analysis Results</span>
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Processed {analysisResult.total_frames} frames ({analysisResult.duration_sec}s) at {analysisResult.fps.toFixed(1)} FPS in {analysisResult.summary.processing_time_sec}s
              </p>
            </div>

            {/* Event Filter Pills */}
            <div className="flex items-center space-x-1.5 bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
              {(['ALL', 'FALL', 'FIGHT', 'INTRUSION', 'CROWD'] as const).map((filter) => (
                <button
                  key={filter}
                  onClick={() => setFilterEventType(filter)}
                  className={`px-3 py-1 rounded-lg font-mono font-semibold transition ${
                    filterEventType === filter
                      ? 'bg-teal-500 text-slate-950'
                      : 'text-slate-400 hover:text-white hover:bg-slate-900'
                  }`}
                >
                  {filter}
                </button>
              ))}
            </div>
          </div>

          {/* When Incidents Detected */}
          {incidentsToDisplay.length > 0 ? (
            <div className="space-y-6">
              {incidentsToDisplay.map((incident, idx) => (
                <EvidenceAnalysisCard
                  key={idx}
                  incident={incident}
                  onSeekToTimestamp={handleSeek}
                />
              ))}
            </div>
          ) : (
            /* When No Incident Detected */
            <div className="glass-panel p-8 rounded-2xl border-emerald-500/40 bg-emerald-950/20 space-y-3">
              <div className="flex items-center space-x-3">
                <div className="p-3 rounded-xl bg-emerald-500 text-slate-950">
                  <CheckCircle2 className="w-6 h-6 stroke-[2.5]" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-emerald-300">
                    🟢 NO {filterEventType !== 'ALL' ? filterEventType : 'SAFETY'} INCIDENTS DETECTED
                  </h3>
                  <p className="text-xs text-slate-300 mt-0.5">
                    No safety-critical events matching this category satisfied multi-frame evidence criteria during the observation window.
                  </p>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 font-mono text-xs text-slate-400 flex items-center justify-between">
                <span>Displaying 0 incidents ({analysisResult.incidents.length} total detected)</span>
                <span>All evidence criteria evaluated.</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
