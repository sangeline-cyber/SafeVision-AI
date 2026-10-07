from typing import List, Any, Optional
from pydantic import BaseModel, ConfigDict
from backend.app.models.zone import ZoneType, RiskLevel


class ZoneBase(BaseModel):
    zone_name: str
    zone_type: ZoneType = ZoneType.RESTRICTED
    polygon_coordinates: Any  # List of coordinates [[x1, y1], [x2, y2], ...]
    risk_level: RiskLevel = RiskLevel.HIGH


class ZoneCreate(ZoneBase):
    camera_id: int


class ZoneUpdate(BaseModel):
    zone_name: Optional[str] = None
    zone_type: Optional[ZoneType] = None
    polygon_coordinates: Optional[Any] = None
    risk_level: Optional[RiskLevel] = None


class ZoneRead(ZoneBase):
    zone_id: int
    camera_id: int

    model_config = ConfigDict(from_attributes=True)
