from typing import Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from backend.app.models.incident import EventType


class EventRuleBase(BaseModel):
    event_type: EventType
    required_evidence: Any
    threshold: float = Field(default=0.75, ge=0.0, le=1.0)
    verification_duration: float = Field(default=3.0, ge=0.1)


class EventRuleCreate(EventRuleBase):
    pass


class EventRuleUpdate(BaseModel):
    required_evidence: Optional[Any] = None
    threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    verification_duration: Optional[float] = Field(default=None, ge=0.1)


class EventRuleRead(EventRuleBase):
    rule_id: int

    model_config = ConfigDict(from_attributes=True)
