from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from backend.app.models.incident import IncidentStatus, IncidentRiskLevel
from backend.app.models.evidence import EvidenceStatus


class EvidenceItemResponse(BaseModel):
    evidence_type: str
    description: str
    status: EvidenceStatus
    confidence: float
    timestamp_sec: float


class IncidentDetectionResponse(BaseModel):
    incident_id: Optional[int] = None
    event_type: str = "FALL"
    track_id: Optional[int] = None
    participant_ids: Optional[List[int]] = None
    timestamp_sec: float
    timestamp_formatted: str
    status: IncidentStatus
    confidence: float = Field(..., description="Fall Evidence Score calculated from multi-frame evidence")
    risk_level: IncidentRiskLevel
    evidence_frame_url: Optional[str] = None
    evidence_image_url: Optional[str] = None
    evidence_items: List[EvidenceItemResponse] = []
    is_evidence_complete: bool = False
    should_alert: bool = False
    alert_id: Optional[int] = None
    alert_message: Optional[str] = None
    temporal_trace: List[Dict[str, Any]] = []


class VideoUploadResponse(BaseModel):
    video_id: str
    filename: str
    file_size_bytes: int
    duration_sec: Optional[float] = None
    fps: Optional[float] = None
    total_frames: Optional[int] = None
    video_url: str
    uploaded_at: datetime


class VideoProcessingStatusResponse(BaseModel):
    video_id: str
    status: str  # "pending", "processing", "completed", "failed"
    progress_percent: float
    processed_frames: int
    total_frames: int
    fps: float
    elapsed_time_sec: float
    incidents_count: int
    error: Optional[str] = None


class VideoAnalysisResultResponse(BaseModel):
    video_id: str
    filename: str
    total_frames: int
    fps: float
    duration_sec: float
    processed_at: datetime
    incidents: List[IncidentDetectionResponse] = []
    summary: Dict[str, Any] = {}
