from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from backend.app.models.evidence import EvidenceStatus


class EvidenceBase(BaseModel):
    incident_id: int
    evidence_type: str
    description: str
    status: EvidenceStatus = EvidenceStatus.UNKNOWN
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class EvidenceCreate(EvidenceBase):
    timestamp: Optional[datetime] = None


class EvidenceUpdate(BaseModel):
    status: Optional[EvidenceStatus] = None
    description: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class EvidenceRead(EvidenceBase):
    evidence_id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
