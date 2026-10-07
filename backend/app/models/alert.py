from datetime import datetime, timezone
import enum
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from backend.app.database.base import Base


class AlertSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Alert(Base):
    __tablename__ = "alerts"

    alert_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    incident_id = Column(Integer, ForeignKey("incidents.incident_id", ondelete="CASCADE"), nullable=False, index=True)
    severity = Column(
        Enum(AlertSeverity, name="alert_severity_enum", native_enum=False),
        default=AlertSeverity.HIGH,
        nullable=False,
        index=True
    )
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    acknowledged = Column(Boolean, default=False, nullable=False, index=True)

    # Relationships
    incident = relationship("Incident", back_populates="alerts")

    def __repr__(self):
        return (
            f"<Alert(id={self.alert_id}, incident_id={self.incident_id}, "
            f"severity='{self.severity}', acknowledged={self.acknowledged})>"
        )
