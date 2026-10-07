export interface HealthResponse {
  status: string;
  service: string;
  version?: string;
  timestamp?: string;
}

export interface DatabaseHealthResponse {
  status: 'connected' | 'unreachable' | 'error';
  database: string;
  connected: boolean;
  server?: string;
  database_name?: string;
  error?: string;
  details?: string;
  ping?: boolean;
}

export type EvidenceStatus = 'SUPPORTED' | 'CONTRADICTED' | 'UNKNOWN';

export type IncidentStatus = 'CANDIDATE' | 'VERIFYING' | 'CONFIRMED' | 'RETRACTED';

export type EventType = 'fall' | 'intrusion' | 'fight' | 'crowd' | 'FALL' | 'INTRUSION' | 'FIGHT' | 'CROWD';

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

export interface EvidenceItem {
  evidence_id?: number;
  incident_id?: number;
  evidence_type: string;
  description: string;
  status: EvidenceStatus;
  confidence: number;
  timestamp?: string;
  timestamp_sec?: number;
}

export interface TemporalSnapshot {
  frame_idx: number;
  timestamp_sec: number;
  state: IncidentStatus;
  evidence_states: Record<string, EvidenceStatus>;
  active_evidence_score: number;
}

export interface Incident {
  incident_id?: number;
  camera_id?: number;
  event_type: EventType;
  entity_id?: number | null;
  track_id?: number | null;
  participant_ids?: number[];
  start_time?: string;
  end_time?: string | null;
  timestamp_sec: number;
  timestamp_formatted: string;
  status: IncidentStatus;
  confidence: number;
  risk_level: RiskLevel;
  evidence_frame_url?: string | null;
  evidence_image_url?: string | null;
  evidence_items?: EvidenceItem[];
  is_evidence_complete?: boolean;
  should_alert?: boolean;
  alert_id?: number | null;
  alert_message?: string | null;
  temporal_trace?: TemporalSnapshot[];
}

export interface VideoUploadResult {
  video_id: string;
  filename: string;
  file_size_bytes: number;
  video_url: string;
  uploaded_at: string;
}

export interface VideoProcessingStatus {
  video_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress_percent: number;
  processed_frames: number;
  total_frames: number;
  fps: number;
  elapsed_time_sec: number;
  incidents_count: number;
  error?: string | null;
}

export interface VideoAnalysisResult {
  video_id: string;
  filename: string;
  total_frames: number;
  fps: number;
  duration_sec: number;
  processed_at: string;
  incidents: Incident[];
  summary: {
    total_incidents: number;
    confirmed_falls: number;
    confirmed_intrusions?: number;
    confirmed_fights?: number;
    confirmed_crowd?: number;
    retracted_events: number;
    processing_time_sec: number;
    model: string;
    reasoning_engine: string;
  };
}
