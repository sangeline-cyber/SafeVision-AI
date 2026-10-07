import React, { useState, useRef } from 'react';
import { UploadCloud, FileVideo, AlertCircle, Play, CheckCircle2, Loader2 } from 'lucide-react';

interface VideoUploaderProps {
  onUploadAndAnalyze: (file: File) => Promise<void>;
  isProcessing: boolean;
  uploadProgress: number;
}

const ALLOWED_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv', '.webm'];
const MAX_SIZE_MB = 500;

export const VideoUploader: React.FC<VideoUploaderProps> = ({
  onUploadAndAnalyze,
  isProcessing,
  uploadProgress,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateAndSetFile = (file: File) => {
    setValidationError(null);
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setValidationError(`Unsupported file format '${ext}'. Please select MP4, AVI, MOV, or WebM.`);
      setSelectedFile(null);
      return;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setValidationError(`File exceeds maximum allowed size of ${MAX_SIZE_MB}MB.`);
      setSelectedFile(null);
      return;
    }
    setSelectedFile(file);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleSubmit = async () => {
    if (!selectedFile || isProcessing) return;
    await onUploadAndAnalyze(selectedFile);
  };

  return (
    <div className="glass-panel p-6 rounded-2xl border-slate-800 space-y-5">
      <div>
        <h3 className="text-lg font-bold text-white flex items-center space-x-2">
          <FileVideo className="w-5 h-5 text-teal-400" />
          <span>Upload Video for Multi-Event Safety Analysis</span>
        </h3>
        <p className="text-xs text-slate-400 mt-1">
          Upload real surveillance or test video footage. The AI pipeline evaluates YOLO Pose estimation and multi-frame Kleene temporal evidence across Fall, Fight, Crowd, and Restricted-Zone events.
        </p>
      </div>

      {/* Drag & Drop Box */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
          dragActive
            ? 'border-teal-400 bg-teal-950/30'
            : selectedFile
            ? 'border-teal-500/50 bg-slate-900/60'
            : 'border-slate-700/80 hover:border-slate-500 bg-slate-950/40'
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ALLOWED_EXTENSIONS.join(',')}
          onChange={handleChange}
          className="hidden"
          disabled={isProcessing}
        />

        <div className="flex flex-col items-center justify-center space-y-3">
          <div className="p-3.5 rounded-full bg-slate-900 border border-slate-800 text-teal-400">
            <UploadCloud className="w-7 h-7" />
          </div>

          <div>
            <p className="text-sm font-semibold text-slate-200">
              {selectedFile ? selectedFile.name : 'Click to select or drag & drop surveillance video'}
            </p>
            <p className="text-xs text-slate-500 mt-1 font-mono">
              MP4, AVI, MOV, MKV, WebM (Max 500MB)
            </p>
          </div>
        </div>
      </div>

      {/* Selected File Details */}
      {selectedFile && (
        <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900/90 border border-slate-800 text-xs">
          <div className="flex items-center space-x-2.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <div>
              <p className="font-semibold text-slate-200">{selectedFile.name}</p>
              <p className="text-slate-400 font-mono">{(selectedFile.size / (1024 * 1024)).toFixed(2)} MB</p>
            </div>
          </div>

          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setSelectedFile(null);
            }}
            disabled={isProcessing}
            className="text-slate-400 hover:text-rose-400 transition"
          >
            Change
          </button>
        </div>
      )}

      {/* Error Message */}
      {validationError && (
        <div className="flex items-center space-x-2 p-3 rounded-xl bg-rose-950/40 border border-rose-800/60 text-xs text-rose-300">
          <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-400" />
          <span>{validationError}</span>
        </div>
      )}

      {/* Upload & Analyze Action Button */}
      <button
        onClick={handleSubmit}
        disabled={!selectedFile || isProcessing}
        className={`w-full py-3 px-4 rounded-xl font-bold text-sm flex items-center justify-center space-x-2 transition-all shadow-lg ${
          !selectedFile || isProcessing
            ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700/50'
            : 'bg-gradient-to-r from-teal-500 to-cyan-500 text-slate-950 hover:from-teal-400 hover:to-cyan-400 shadow-teal-500/20'
        }`}
      >
        {isProcessing ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Processing Perception Pipeline... ({uploadProgress}%)</span>
          </>
        ) : (
          <>
            <Play className="w-4 h-4 fill-current" />
            <span>Upload & Run Safety Event Analysis</span>
          </>
        )}
      </button>
    </div>
  );
};
