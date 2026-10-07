from datetime import datetime, timezone
import enum
from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
from backend.app.database.base import Base


class CameraStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class Camera(Base):
    __tablename__ = "cameras"

    camera_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    camera_name = Column(String(255), nullable=False, index=True)
    location = Column(String(255), nullable=False)
    stream_url = Column(String(1024), nullable=False)
    status = Column(Enum(CameraStatus, name="camera_status_enum", native_enum=False), default=CameraStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    zones = relationship("Zone", back_populates="camera", cascade="all, delete-orphan")
    entities = relationship("TrackedEntity", back_populates="camera", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="camera", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Camera(camera_id={self.camera_id}, name='{self.camera_name}', status='{self.status}')>"
