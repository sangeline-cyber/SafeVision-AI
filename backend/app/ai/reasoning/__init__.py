"""
SafeVision AI - Evidence Reasoning Layer
Package initialization.
"""

from backend.app.ai.reasoning.evidence_schema import (
    EvidenceState,
    FallEvidenceCategory,
    IntrusionEvidenceCategory,
    FightEvidenceCategory,
    CrowdEvidenceCategory,
    EvidenceItem,
    TemporalFrameSnapshot,
    FallReasoningEvaluation,
    IntrusionReasoningEvaluation,
    FightReasoningEvaluation,
    CrowdReasoningEvaluation,
)
from backend.app.ai.reasoning.zone_intrusion_reasoner import ZoneIntrusionReasoner, RestrictedZoneConfig
from backend.app.ai.reasoning.fighting_reasoner import FightIncidentReasoner, FightReasonerConfig
from backend.app.ai.reasoning.overcrowding_reasoner import OvercrowdingReasoner, CrowdRegionConfig

__all__ = [
    "EvidenceState",
    "FallEvidenceCategory",
    "IntrusionEvidenceCategory",
    "FightEvidenceCategory",
    "CrowdEvidenceCategory",
    "EvidenceItem",
    "TemporalFrameSnapshot",
    "FallReasoningEvaluation",
    "IntrusionReasoningEvaluation",
    "FightReasoningEvaluation",
    "CrowdReasoningEvaluation",
    "ZoneIntrusionReasoner",
    "RestrictedZoneConfig",
    "FightIncidentReasoner",
    "FightReasonerConfig",
    "OvercrowdingReasoner",
    "CrowdRegionConfig",
]
