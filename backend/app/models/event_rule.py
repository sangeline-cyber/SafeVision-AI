import enum
from sqlalchemy import Column, Integer, String, Float, JSON, Enum
from backend.app.database.base import Base
from backend.app.models.incident import EventType


class EventRule(Base):
    __tablename__ = "event_rules"

    rule_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_type = Column(
        Enum(EventType, name="event_rule_type_enum", native_enum=False),
        nullable=False,
        unique=True,
        index=True
    )
    required_evidence = Column(JSON, nullable=False)  # Schema of required evidence items and weights
    threshold = Column(Float, default=0.75, nullable=False)  # Confidence threshold required for confirmation
    verification_duration = Column(Float, default=3.0, nullable=False)  # Duration in seconds for temporal verification

    def __repr__(self):
        return (
            f"<EventRule(id={self.rule_id}, type='{self.event_type}', "
            f"threshold={self.threshold}, verification_duration={self.verification_duration}s)>"
        )
