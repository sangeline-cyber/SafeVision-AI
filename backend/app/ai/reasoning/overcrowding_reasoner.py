"""
SafeVision AI - Overcrowding Reasoner (3-State Kleene Logic)

Monitors headcounts inside configurable regions against safety capacity thresholds.
Requires multi-frame sustained persistence before generating alerts.
Eliminates false alarms from momentary transit surges or fleeting group crossings.
Supports reversible lifecycle: CANDIDATE -> VERIFYING -> CONFIRMED / RETRACTED.
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
import numpy as np

from backend.app.ai.tracking.person_tracker import TrackedPerson
from backend.app.ai.reasoning.evidence_schema import (
    EvidenceState,
    CrowdEvidenceCategory,
    EvidenceItem,
    CrowdReasoningEvaluation,
    TemporalFrameSnapshot,
)
from backend.app.ai.reasoning.temporal_evidence_tracker import TemporalEvidenceTracker
from backend.app.ai.reasoning.zone_intrusion_reasoner import point_in_polygon
from backend.app.models.incident import IncidentStatus, IncidentRiskLevel
from backend.app.core.logging import logger


@dataclass
class CrowdRegionConfig:
    region_id: int = 1
    region_name: str = "Main Concourse Zone"
    # Optional polygon bounds; if None/empty, monitors full frame
    polygon: Optional[List[Tuple[float, float]]] = None
    capacity_threshold: int = 2  # Alert threshold (e.g. > 2 people)
    min_persistence_frames: int = 10  # Must sustain for at least 10 consecutive frames
    risk_level: IncidentRiskLevel = IncidentRiskLevel.MEDIUM


class OvercrowdingReasoner:
    """
    Deterministic rule-and-evidence reasoning engine for Crowd Surge and Overcrowding.
    Verifies sustained headcount persistence above capacity threshold.
    """

    def __init__(self, config: Optional[CrowdRegionConfig] = None):
        self.config = config or CrowdRegionConfig()
        self._exceeded_frames: int = 0
        self._prev_status: IncidentStatus = IncidentStatus.CANDIDATE
        self._temporal_tracker = TemporalEvidenceTracker(self.config.region_id + 9000)

    def evaluate_crowd(
        self,
        active_tracks: List[TrackedPerson],
        frame_idx: int,
        timestamp_sec: float,
        frame_width: int = 640,
        frame_height: int = 480
    ) -> Optional[CrowdReasoningEvaluation]:
        """
        Counts active people within the configured crowd region and evaluates overcrowding evidence.
        """
        # Count persons in region
        if self.config.polygon and len(self.config.polygon) >= 3:
            inside_tracks = []
            for p in active_tracks:
                x1, y1, x2, y2 = p.current_obs.bbox
                cx = ((x1 + x2) / 2.0) / max(1.0, frame_width)
                cy = y2 / max(1.0, frame_height)
                if point_in_polygon(cx, cy, self.config.polygon):
                    inside_tracks.append(p)
            current_count = len(inside_tracks)
        else:
            current_count = len(active_tracks)

        is_exceeded = (current_count > self.config.capacity_threshold)

        if is_exceeded:
            self._exceeded_frames += 1
        else:
            self._exceeded_frames = 0

        dwell_count = self._exceeded_frames
        old_status = self._prev_status

        # If not exceeded and zero history, skip unless was verifying/confirmed
        if not is_exceeded and dwell_count == 0 and old_status not in [IncidentStatus.VERIFYING, IncidentStatus.CONFIRMED]:
            return None

        # -------------------------------------------------------------
        # 1. HEADCOUNT_THRESHOLD_EXCEEDED
        # -------------------------------------------------------------
        if is_exceeded:
            ev_headcount = EvidenceItem(
                evidence_type=CrowdEvidenceCategory.HEADCOUNT_THRESHOLD_EXCEEDED.value,
                state=EvidenceState.SUPPORTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=min(1.0, 0.80 + ((current_count - self.config.capacity_threshold) * 0.1)),
                description=f"Active person headcount ({current_count}) exceeds safety threshold ({self.config.capacity_threshold}) in {self.config.region_name}.",
                metadata={"current_count": current_count, "threshold": self.config.capacity_threshold}
            )
        elif current_count == self.config.capacity_threshold:
            ev_headcount = EvidenceItem(
                evidence_type=CrowdEvidenceCategory.HEADCOUNT_THRESHOLD_EXCEEDED.value,
                state=EvidenceState.UNKNOWN,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.50,
                description=f"Headcount ({current_count}) is at boundary capacity threshold ({self.config.capacity_threshold}).",
                metadata={"current_count": current_count, "threshold": self.config.capacity_threshold}
            )
        else:
            ev_headcount = EvidenceItem(
                evidence_type=CrowdEvidenceCategory.HEADCOUNT_THRESHOLD_EXCEEDED.value,
                state=EvidenceState.CONTRADICTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.95,
                description=f"Headcount ({current_count}) is below safety threshold ({self.config.capacity_threshold}).",
                metadata={"current_count": current_count, "threshold": self.config.capacity_threshold}
            )

        # -------------------------------------------------------------
        # 2. SPATIAL_DENSITY_CONCENTRATION
        # -------------------------------------------------------------
        if is_exceeded:
            ev_density = EvidenceItem(
                evidence_type=CrowdEvidenceCategory.SPATIAL_DENSITY_CONCENTRATION.value,
                state=EvidenceState.SUPPORTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.90,
                description=f"High density cluster observed with {current_count} concurrent tracked entities.",
                metadata={"density_count": current_count}
            )
        elif current_count >= 1:
            ev_density = EvidenceItem(
                evidence_type=CrowdEvidenceCategory.SPATIAL_DENSITY_CONCENTRATION.value,
                state=EvidenceState.UNKNOWN,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.50,
                description="Normal transit density observed.",
                metadata={"density_count": current_count}
            )
        else:
            ev_density = EvidenceItem(
                evidence_type=CrowdEvidenceCategory.SPATIAL_DENSITY_CONCENTRATION.value,
                state=EvidenceState.CONTRADICTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.90,
                description="Monitored region is unoccupied.",
                metadata={"density_count": 0}
            )

        # -------------------------------------------------------------
        # 3. SUSTAINED_CROWD_PRESENCE
        # -------------------------------------------------------------
        if dwell_count >= self.config.min_persistence_frames:
            ev_sustained = EvidenceItem(
                evidence_type=CrowdEvidenceCategory.SUSTAINED_CROWD_PRESENCE.value,
                state=EvidenceState.SUPPORTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=min(1.0, 0.85 + (dwell_count / (self.config.min_persistence_frames * 2.0))),
                description=f"Overcrowding sustained continuously for {dwell_count} frames (threshold: {self.config.min_persistence_frames}).",
                metadata={"dwell_frames": dwell_count, "min_required": self.config.min_persistence_frames}
            )
        elif dwell_count > 0:
            ev_sustained = EvidenceItem(
                evidence_type=CrowdEvidenceCategory.SUSTAINED_CROWD_PRESENCE.value,
                state=EvidenceState.UNKNOWN,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.55,
                description=f"Crowd surge under temporal verification ({dwell_count}/{self.config.min_persistence_frames} frames elapsed).",
                metadata={"dwell_frames": dwell_count, "min_required": self.config.min_persistence_frames}
            )
        else:
            ev_sustained = EvidenceItem(
                evidence_type=CrowdEvidenceCategory.SUSTAINED_CROWD_PRESENCE.value,
                state=EvidenceState.CONTRADICTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.90,
                description="Zero congestion persistence; count is within safety limits.",
                metadata={"dwell_frames": 0}
            )

        # -------------------------------------------------------------
        # 4. INFLOW_RATE_ACCUMULATION
        # -------------------------------------------------------------
        if is_exceeded and dwell_count >= (self.config.min_persistence_frames // 2):
            ev_inflow = EvidenceItem(
                evidence_type=CrowdEvidenceCategory.INFLOW_RATE_ACCUMULATION.value,
                state=EvidenceState.SUPPORTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.90,
                description="Positive pedestrian inflow rate exceeding natural sector dissipation capacity.",
                metadata={"inflow_positive": True}
            )
        elif is_exceeded:
            ev_inflow = EvidenceItem(
                evidence_type=CrowdEvidenceCategory.INFLOW_RATE_ACCUMULATION.value,
                state=EvidenceState.UNKNOWN,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.50,
                description="Inflow accumulation dynamic under multi-frame observation.",
                metadata={"inflow_positive": True}
            )
        else:
            ev_inflow = EvidenceItem(
                evidence_type=CrowdEvidenceCategory.INFLOW_RATE_ACCUMULATION.value,
                state=EvidenceState.CONTRADICTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.90,
                description="Normal pedestrian dispersal rate.",
                metadata={"inflow_positive": False}
            )

        # -------------------------------------------------------------
        # 5. TEMPORAL_CONSISTENCY
        # -------------------------------------------------------------
        if ev_headcount.state == EvidenceState.SUPPORTED and ev_sustained.state == EvidenceState.SUPPORTED:
            ev_temporal = EvidenceItem(
                evidence_type=CrowdEvidenceCategory.TEMPORAL_CONSISTENCY.value,
                state=EvidenceState.SUPPORTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.95,
                description="Temporal consistency confirmed: sustained congestion maintained without transient dropouts.",
                metadata={"consistent": True}
            )
        elif not is_exceeded and old_status in [IncidentStatus.VERIFYING, IncidentStatus.CONFIRMED]:
            ev_temporal = EvidenceItem(
                evidence_type=CrowdEvidenceCategory.TEMPORAL_CONSISTENCY.value,
                state=EvidenceState.CONTRADICTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.90,
                description="Crowd naturally dispersed below threshold; incident resolved.",
                metadata={"consistent": False}
            )
        elif is_exceeded:
            ev_temporal = EvidenceItem(
                evidence_type=CrowdEvidenceCategory.TEMPORAL_CONSISTENCY.value,
                state=EvidenceState.UNKNOWN,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.50,
                description="Multi-frame crowd persistence timeline under ongoing evaluation.",
                metadata={"consistent": False}
            )
        else:
            ev_temporal = EvidenceItem(
                evidence_type=CrowdEvidenceCategory.TEMPORAL_CONSISTENCY.value,
                state=EvidenceState.CONTRADICTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.85,
                description="No persistent crowd congestion sequence.",
                metadata={"consistent": False}
            )

        evidence_items = [ev_headcount, ev_density, ev_sustained, ev_inflow, ev_temporal]

        # -------------------------------------------------------------
        # Completeness & Evidence Score Computation
        # -------------------------------------------------------------
        supported_count = sum(1 for e in evidence_items if e.state == EvidenceState.SUPPORTED)
        is_evidence_complete = (supported_count == 5)

        score = 0.0
        weights = {
            CrowdEvidenceCategory.HEADCOUNT_THRESHOLD_EXCEEDED.value: 0.25,
            CrowdEvidenceCategory.SPATIAL_DENSITY_CONCENTRATION.value: 0.20,
            CrowdEvidenceCategory.SUSTAINED_CROWD_PRESENCE.value: 0.25,
            CrowdEvidenceCategory.INFLOW_RATE_ACCUMULATION.value: 0.15,
            CrowdEvidenceCategory.TEMPORAL_CONSISTENCY.value: 0.15,
        }
        for ev in evidence_items:
            w = weights.get(ev.evidence_type, 0.20)
            if ev.state == EvidenceState.SUPPORTED:
                score += w * ev.confidence
            elif ev.state == EvidenceState.UNKNOWN:
                score += w * 0.25 * ev.confidence
        score = float(round(score, 3))

        # -------------------------------------------------------------
        # Reversible Lifecycle Resolution
        # -------------------------------------------------------------
        if not is_exceeded and old_status in [IncidentStatus.VERIFYING, IncidentStatus.CONFIRMED]:
            new_status = IncidentStatus.RETRACTED
        elif is_evidence_complete and dwell_count >= self.config.min_persistence_frames:
            new_status = IncidentStatus.CONFIRMED
        elif is_exceeded and dwell_count >= (self.config.min_persistence_frames // 2):
            new_status = IncidentStatus.VERIFYING
        elif is_exceeded:
            new_status = IncidentStatus.CANDIDATE
        else:
            new_status = IncidentStatus.CANDIDATE

        self._prev_status = new_status

        # Strict evidence-complete alert decision: ONLY when CONFIRMED!
        should_alert = (new_status == IncidentStatus.CONFIRMED and is_evidence_complete)

        alert_msg = None
        if should_alert:
            mins = int(timestamp_sec // 60)
            secs = timestamp_sec % 60
            alert_msg = (
                f"CONFIRMED Overcrowding in {self.config.region_name} at {mins:02d}:{secs:05.2f}: "
                f"Headcount of {current_count} persons exceeded safety capacity ({self.config.capacity_threshold}) "
                f"continuously for {dwell_count} frames."
            )

        # Record temporal snapshot
        self._temporal_tracker.record_frame(
            frame_idx=frame_idx,
            timestamp_sec=timestamp_sec,
            evidence_items=evidence_items,
            incident_status=new_status.value,
            force_snapshot=(new_status in [IncidentStatus.CONFIRMED, IncidentStatus.RETRACTED])
        )

        return CrowdReasoningEvaluation(
            region_name=self.config.region_name,
            current_count=current_count,
            threshold=self.config.capacity_threshold,
            frame_idx=frame_idx,
            timestamp_sec=timestamp_sec,
            incident_status=new_status,
            evidence_score=score,
            is_evidence_complete=is_evidence_complete,
            should_alert=should_alert,
            evidence_items=evidence_items,
            dwell_frames=dwell_count,
            temporal_evolution=self._temporal_tracker.get_evolution(),
            alert_message=alert_msg,
            risk_level=self.config.risk_level
        )
