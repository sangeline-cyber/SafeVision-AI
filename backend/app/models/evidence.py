from datetime import datetime, timezone
import enum
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from backend.app.database.base import Base


class EvidenceStatus(str, enum.Enum):
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    UNKNOWN = "UNKNOWN"


class Evidence(Base):
    __tablename__ = "evidence"

    evidence_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    incident_id = Column(Integer, ForeignKey("incidents.incident_id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_type = Column(String(100), nullable=False, index=True)  # e.g., 'downward_movement', 'boundary_crossing'
    description = Column(Text, nullable=False)
    status = Column(
        Enum(EvidenceStatus, name="evidence_status_enum", native_enum=False),
        default=EvidenceStatus.UNKNOWN,
        nullable=False,
        index=True
    )
    confidence = Column(Float, default=0.0, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    incident = relationship("Incident", back_populates="evidence_items")

    def __repr__(self):
        return (
            f"<Evidence(id={self.evidence_id}, incident_id={self.incident_id}, "
            f"type='{self.evidence_type}', status='{self.status}', conf={self.confidence:.2f})>"
        )
