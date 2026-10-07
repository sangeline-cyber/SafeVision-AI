from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from backend.app.models.alert import AlertSeverity


class AlertBase(BaseModel):
    incident_id: int
    severity: AlertSeverity = AlertSeverity.HIGH
    message: str
    acknowledged: bool = False


class AlertCreate(AlertBase):
    pass


class AlertUpdate(BaseModel):
    acknowledged: Optional[bool] = None
    severity: Optional[AlertSeverity] = None
    message: Optional[str] = None


class AlertRead(AlertBase):
    alert_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
