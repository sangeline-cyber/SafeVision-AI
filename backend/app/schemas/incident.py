from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from backend.app.models.incident import IncidentStatus, EventType, IncidentRiskLevel


class IncidentBase(BaseModel):
    camera_id: int
    event_type: EventType
    entity_id: Optional[int] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    risk_level: IncidentRiskLevel = IncidentRiskLevel.MEDIUM
    status: IncidentStatus = IncidentStatus.CANDIDATE


class IncidentCreate(IncidentBase):
    start_time: Optional[datetime] = None


class IncidentUpdate(BaseModel):
    status: Optional[IncidentStatus] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    risk_level: Optional[IncidentRiskLevel] = None
    end_time: Optional[datetime] = None


class IncidentRead(IncidentBase):
    incident_id: int
    start_time: datetime
    end_time: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
