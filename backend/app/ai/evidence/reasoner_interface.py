"""
SafeVision AI - Evidence Reasoning Engine Interface

STATUS: NOT IMPLEMENTED YET
Core reasoning engine implementing 3-State Evidence Evaluation and Reversible Incident Lifecycles.

Features:
1. Event-Specific Evidence Schemas (Fall, Intrusion, Fight, Crowd)
2. 3-State Evidence Reasoning (SUPPORTED, CONTRADICTED, UNKNOWN)
3. Reversible Incident Reasoning (CANDIDATE -> VERIFYING -> CONFIRMED / RETRACTED)
4. Evidence-Complete Alerting
5. Multi-frame Temporal Evidence Lifecycle
"""

from abc import abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.app.ai.base import BaseAIModule, EvidenceObservation, TrackedObject
from backend.app.models.incident import IncidentStatus, EventType


class IEvidenceReasoner(BaseAIModule):
    """
    Interface for the deterministic, rule-and-evidence-based safety reasoning engine.
    (Non-LLM decision engine).
    """

    @abstractmethod
    def evaluate_fall_evidence(
        self,
        entity: TrackedObject,
        temporal_window_sec: float
    ) -> List[EvidenceObservation]:
        """
        Evaluates 7-point fall evidence schema:
        1. Person detected
        2. Previously upright
        3. Downward movement velocity
        4. Posture transition
        5. Ground-level horizontal posture
        6. Persistence duration
        7. Recovery check (supports retraction if person stands back up)
        """
        raise NotImplementedError("NOT IMPLEMENTED YET: Fall evidence evaluation engine scheduled for Phase 2.")

    @abstractmethod
    def evaluate_intrusion_evidence(
        self,
        entity: TrackedObject,
        zone_polygon: List[Dict[str, float]],
        zone_type: str
    ) -> List[EvidenceObservation]:
        """
        Evaluates intrusion evidence schema:
        1. Person detected
        2. Restricted-zone boundary crossing
        3. Direction of crossing (inward vs outward)
        4. Duration inside restricted boundary
        5. Zone context & authorization schedule
        """
        raise NotImplementedError("NOT IMPLEMENTED YET: Intrusion evidence evaluation engine scheduled for Phase 2.")

    @abstractmethod
    def evaluate_fight_evidence(
        self,
        entities: List[TrackedObject],
        interaction_energy: float
    ) -> List[EvidenceObservation]:
        """
        Evaluates fight evidence schema:
        1. Multiple persons detected in close proximity
        2. Interpersonal interaction
        3. High-energy violent motion / rapid velocity changes
        4. Spatio-temporal persistence
        """
        raise NotImplementedError("NOT IMPLEMENTED YET: Fight evidence evaluation engine scheduled for Phase 2.")

    @abstractmethod
    def evaluate_crowd_evidence(
        self,
        entities: List[TrackedObject],
        zone_area: float
    ) -> List[EvidenceObservation]:
        """
        Evaluates overcrowding evidence schema:
        1. Total person count
        2. Spatial density (persons / m^2)
        3. Spatial concentration cluster
        4. Temporal growth / accumulation rate
        """
        raise NotImplementedError("NOT IMPLEMENTED YET: Crowd evidence evaluation engine scheduled for Phase 2.")

    @abstractmethod
    def resolve_incident_lifecycle(
        self,
        event_type: EventType,
        current_status: IncidentStatus,
        evidence_list: List[EvidenceObservation]
    ) -> IncidentStatus:
        """
        Determines state transition (CANDIDATE -> VERIFYING -> CONFIRMED / RETRACTED)
        based on evidence completeness and satisfaction of event-specific rules.
        """
        raise NotImplementedError("NOT IMPLEMENTED YET: Incident lifecycle resolver scheduled for Phase 2.")
