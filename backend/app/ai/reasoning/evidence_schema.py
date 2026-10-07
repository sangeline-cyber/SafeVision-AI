"""
SafeVision AI - Event-Specific Evidence Schema & 3-State Logic

Defines the 5 mandatory evidence categories for Fall incidents:
1. DOWNWARD_MOVEMENT
2. POSTURE_TRANSITION
3. LOW_OR_HORIZONTAL_POSTURE
4. REMAINS_DOWN
5. TEMPORAL_CONSISTENCY

And the 3-state Kleene logic:
- SUPPORTED
- CONTRADICTED
- UNKNOWN
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from backend.app.models.incident import IncidentStatus, IncidentRiskLevel


class EvidenceState(str, Enum):
    """
    Three-state evidence evaluation.
    Preserves strict separation: SUPPORTED != CONTRADICTED != UNKNOWN.
    UNKNOWN is never assumed to be FALSE.
    """
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    UNKNOWN = "UNKNOWN"


class FallEvidenceCategory(str, Enum):
    """
    The 5 mandatory evidence categories specified for Fall Incident Reasoning.
    """
    DOWNWARD_MOVEMENT = "DOWNWARD_MOVEMENT"
    POSTURE_TRANSITION = "POSTURE_TRANSITION"
    LOW_OR_HORIZONTAL_POSTURE = "LOW_OR_HORIZONTAL_POSTURE"
    REMAINS_DOWN = "REMAINS_DOWN"
    TEMPORAL_CONSISTENCY = "TEMPORAL_CONSISTENCY"


class IntrusionEvidenceCategory(str, Enum):
    """
    The 5 mandatory evidence categories for Restricted-Zone Intrusion.
    """
    ZONE_BOUNDARY_PROXIMITY = "ZONE_BOUNDARY_PROXIMITY"
    POLYGON_INTERSECTION = "POLYGON_INTERSECTION"
    ZONE_DWELL_TIME = "ZONE_DWELL_TIME"
    TEMPORAL_PERSISTENCE = "TEMPORAL_PERSISTENCE"
    ACTIVE_SCHEDULE_RESTRICTION = "ACTIVE_SCHEDULE_RESTRICTION"


class FightEvidenceCategory(str, Enum):
    """
    The 5 mandatory evidence categories for Fighting / Aggressive Activity.
    """
    MULTI_PERSON_PROXIMITY = "MULTI_PERSON_PROXIMITY"
    MUTUAL_INTERACTION_DYNAMICS = "MUTUAL_INTERACTION_DYNAMICS"
    HIGH_KINETIC_MOTION = "HIGH_KINETIC_MOTION"
    SUSTAINED_ENGAGEMENT = "SUSTAINED_ENGAGEMENT"
    TEMPORAL_CONSISTENCY = "TEMPORAL_CONSISTENCY"


class CrowdEvidenceCategory(str, Enum):
    """
    The 5 mandatory evidence categories for Overcrowding.
    """
    HEADCOUNT_THRESHOLD_EXCEEDED = "HEADCOUNT_THRESHOLD_EXCEEDED"
    SPATIAL_DENSITY_CONCENTRATION = "SPATIAL_DENSITY_CONCENTRATION"
    SUSTAINED_CROWD_PRESENCE = "SUSTAINED_CROWD_PRESENCE"
    INFLOW_RATE_ACCUMULATION = "INFLOW_RATE_ACCUMULATION"
    TEMPORAL_CONSISTENCY = "TEMPORAL_CONSISTENCY"


@dataclass
class EvidenceItem:
    """
    Individual evidence observation evaluated from video kinematics and posture tracking.
    """
    evidence_type: str
    state: EvidenceState
    timestamp_sec: float
    frame_idx: int
    confidence: float
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_type": self.evidence_type,
            "state": self.state.value,
            "timestamp_sec": round(self.timestamp_sec, 2),
            "frame_idx": self.frame_idx,
            "confidence": round(self.confidence, 3),
            "description": self.description,
            "metadata": self.metadata
        }


@dataclass
class TemporalFrameSnapshot:
    """
    Snapshot of evidence state evolution at a given frame.
    Demonstrates temporal progression (e.g. Frame 100 -> Frame 120 -> Frame 150).
    """
    frame_idx: int
    timestamp_sec: float
    evidence_states: Dict[str, str]  # category -> SUPPORTED | CONTRADICTED | UNKNOWN
    incident_status: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frame_idx": self.frame_idx,
            "timestamp_sec": round(self.timestamp_sec, 2),
            "evidence_states": self.evidence_states,
            "incident_status": self.incident_status
        }


@dataclass
class FallReasoningEvaluation:
    """
    Complete output of the Evidence Reasoning Layer for a tracked person at a specific frame.
    """
    track_id: int
    frame_idx: int
    timestamp_sec: float
    incident_status: IncidentStatus
    evidence_score: float
    is_evidence_complete: bool
    should_alert: bool
    evidence_items: List[EvidenceItem]
    temporal_evolution: List[TemporalFrameSnapshot] = field(default_factory=list)
    alert_message: Optional[str] = None
    risk_level: IncidentRiskLevel = IncidentRiskLevel.HIGH


@dataclass
class IntrusionReasoningEvaluation:
    """
    Complete output of the Evidence Reasoning Layer for a restricted zone intrusion.
    """
    track_id: int
    zone_id: int
    zone_name: str
    frame_idx: int
    timestamp_sec: float
    incident_status: IncidentStatus
    evidence_score: float
    is_evidence_complete: bool
    should_alert: bool
    evidence_items: List[EvidenceItem]
    dwell_frames: int = 0
    temporal_evolution: List[TemporalFrameSnapshot] = field(default_factory=list)
    alert_message: Optional[str] = None
    risk_level: IncidentRiskLevel = IncidentRiskLevel.HIGH


@dataclass
class FightReasoningEvaluation:
    """
    Complete output of the Evidence Reasoning Layer for fighting / aggressive interaction.
    """
    involved_track_ids: List[int]
    frame_idx: int
    timestamp_sec: float
    incident_status: IncidentStatus
    evidence_score: float
    is_evidence_complete: bool
    should_alert: bool
    evidence_items: List[EvidenceItem]
    interaction_distance: float = 0.0
    temporal_evolution: List[TemporalFrameSnapshot] = field(default_factory=list)
    alert_message: Optional[str] = None
    risk_level: IncidentRiskLevel = IncidentRiskLevel.CRITICAL


@dataclass
class CrowdReasoningEvaluation:
    """
    Complete output of the Evidence Reasoning Layer for overcrowding.
    """
    region_name: str
    current_count: int
    threshold: int
    frame_idx: int
    timestamp_sec: float
    incident_status: IncidentStatus
    evidence_score: float
    is_evidence_complete: bool
    should_alert: bool
    evidence_items: List[EvidenceItem]
    dwell_frames: int = 0
    temporal_evolution: List[TemporalFrameSnapshot] = field(default_factory=list)
    alert_message: Optional[str] = None
    risk_level: IncidentRiskLevel = IncidentRiskLevel.MEDIUM

