from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from backend.app.models.camera import CameraStatus


class CameraBase(BaseModel):
    camera_name: str
    location: str
    stream_url: str
    status: CameraStatus = CameraStatus.ACTIVE


class CameraCreate(CameraBase):
    pass


class CameraUpdate(BaseModel):
    camera_name: Optional[str] = None
    location: Optional[str] = None
    stream_url: Optional[str] = None
    status: Optional[CameraStatus] = None


class CameraRead(CameraBase):
    camera_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
