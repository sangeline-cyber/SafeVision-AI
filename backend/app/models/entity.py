from datetime import datetime, timezone
from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from backend.app.database.base import Base


class TrackedEntity(Base):
    __tablename__ = "tracked_entities"

    entity_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    camera_id = Column(Integer, ForeignKey("cameras.camera_id", ondelete="CASCADE"), nullable=False, index=True)
    track_id = Column(Integer, nullable=False, index=True)  # ByteTrack ID
    first_seen = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_seen = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    camera = relationship("Camera", back_populates="entities")
    incidents = relationship("Incident", back_populates="entity")

    def __repr__(self):
        return f"<TrackedEntity(entity_id={self.entity_id}, camera_id={self.camera_id}, track_id={self.track_id})>"
