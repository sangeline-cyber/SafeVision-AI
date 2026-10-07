import enum
from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from backend.app.database.base import Base


class ZoneType(str, enum.Enum):
    RESTRICTED = "restricted"
    HAZARD = "hazard"
    MONITORED = "monitored"
    ENTRY_EXIT = "entry_exit"
    CROWD_WATCH = "crowd_watch"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Zone(Base):
    __tablename__ = "zones"

    zone_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    camera_id = Column(Integer, ForeignKey("cameras.camera_id", ondelete="CASCADE"), nullable=False, index=True)
    zone_name = Column(String(255), nullable=False)
    zone_type = Column(Enum(ZoneType, name="zone_type_enum", native_enum=False), default=ZoneType.RESTRICTED, nullable=False)
    polygon_coordinates = Column(JSON, nullable=False)  # e.g., [{"x": 100, "y": 200}, ...] or [[100,200], ...]
    risk_level = Column(Enum(RiskLevel, name="zone_risk_level_enum", native_enum=False), default=RiskLevel.HIGH, nullable=False)

    # Relationships
    camera = relationship("Camera", back_populates="zones")

    def __repr__(self):
        return f"<Zone(zone_id={self.zone_id}, name='{self.zone_name}', type='{self.zone_type}', risk='{self.risk_level}')>"
