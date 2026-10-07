from datetime import datetime, timezone
import enum
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from backend.app.database.base import Base


class IncidentStatus(str, enum.Enum):
    CANDIDATE = "CANDIDATE"
    VERIFYING = "VERIFYING"
    CONFIRMED = "CONFIRMED"
    RETRACTED = "RETRACTED"


class EventType(str, enum.Enum):
    FALL = "fall"
    INTRUSION = "intrusion"
    FIGHT = "fight"
    CROWD = "crowd"


class IncidentRiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Incident(Base):
    __tablename__ = "incidents"

    incident_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    camera_id = Column(Integer, ForeignKey("cameras.camera_id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(Enum(EventType, name="event_type_enum", native_enum=False), nullable=False, index=True)
    entity_id = Column(Integer, ForeignKey("tracked_entities.entity_id", ondelete="SET NULL"), nullable=True, index=True)
    start_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    status = Column(
        Enum(IncidentStatus, name="incident_status_enum", native_enum=False),
        default=IncidentStatus.CANDIDATE,
        nullable=False,
        index=True
    )
    confidence = Column(Float, default=0.0, nullable=False)
    risk_level = Column(
        Enum(IncidentRiskLevel, name="incident_risk_level_enum", native_enum=False),
        default=IncidentRiskLevel.MEDIUM,
        nullable=False
    )

    # Relationships
    camera = relationship("Camera", back_populates="incidents")
    entity = relationship("TrackedEntity", back_populates="incidents")
    evidence_items = relationship("Evidence", back_populates="incident", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="incident", cascade="all, delete-orphan")

    def __repr__(self):
        return (
            f"<Incident(id={self.incident_id}, type='{self.event_type}', "
            f"status='{self.status}', confidence={self.confidence:.2f})>"
        )
