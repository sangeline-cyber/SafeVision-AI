from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class TrackedEntityBase(BaseModel):
    camera_id: int
    track_id: int


class TrackedEntityCreate(TrackedEntityBase):
    pass


class TrackedEntityRead(TrackedEntityBase):
    entity_id: int
    first_seen: datetime
    last_seen: datetime

    model_config = ConfigDict(from_attributes=True)
