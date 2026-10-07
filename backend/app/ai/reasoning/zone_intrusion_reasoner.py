"""
SafeVision AI - Restricted-Zone Intrusion Reasoner (3-State Kleene Logic)

Evaluates configurable polygonal security zones against person tracking coordinates.
Requires multi-frame dwell verification before triggering CONFIRMED alerts.
Supports reversible lifecycle: CANDIDATE -> VERIFYING -> CONFIRMED / RETRACTED.
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
import numpy as np

from backend.app.ai.tracking.person_tracker import TrackedPerson
from backend.app.ai.reasoning.evidence_schema import (
    EvidenceState,
    IntrusionEvidenceCategory,
    EvidenceItem,
    IntrusionReasoningEvaluation,
    TemporalFrameSnapshot,
)
from backend.app.ai.reasoning.temporal_evidence_tracker import TemporalEvidenceTracker
from backend.app.models.incident import IncidentStatus, IncidentRiskLevel
from backend.app.core.logging import logger


@dataclass
class RestrictedZoneConfig:
    zone_id: int = 1
    zone_name: str = "Restricted Perimeter Sector A"
    # Polygon vertices in normalized [0.0, 1.0] coordinates: [(x1, y1), (x2, y2), ...]
    polygon: List[Tuple[float, float]] = field(default_factory=lambda: [
        (0.20, 0.20),
        (0.80, 0.20),
        (0.80, 0.85),
        (0.20, 0.85)
    ])
    min_dwell_frames: int = 10  # Dwell persistence threshold
    risk_level: IncidentRiskLevel = IncidentRiskLevel.HIGH
    is_active: bool = True


def point_in_polygon(x: float, y: float, polygon: List[Tuple[float, float]]) -> bool:
    """
    Ray-casting algorithm to determine if a point (x, y) is strictly inside a polygon.
    """
    n = len(polygon)
    if n < 3:
        return False
    inside = False
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside


def point_polygon_distance(x: float, y: float, polygon: List[Tuple[float, float]]) -> float:
    """
    Calculates minimal Euclidean distance from (x, y) to polygon edges.
    """
    min_dist = float("inf")
    n = len(polygon)
    for i in range(n):
        p1 = np.array(polygon[i])
        p2 = np.array(polygon[(i + 1) % n])
        p = np.array([x, y])
        line_vec = p2 - p1
        line_len = np.linalg.norm(line_vec)
        if line_len < 1e-6:
            dist = np.linalg.norm(p - p1)
        else:
            t = max(0.0, min(1.0, np.dot(p - p1, line_vec) / (line_len ** 2)))
            proj = p1 + t * line_vec
            dist = np.linalg.norm(p - proj)
        min_dist = min(min_dist, dist)
    return float(min_dist)


class ZoneIntrusionReasoner:
    """
    Deterministic rule-and-evidence reasoning engine for Restricted-Zone Intrusion.
    Tracks dwell time and enforces multi-frame temporal persistence.
    """

    def __init__(self, zone_config: Optional[RestrictedZoneConfig] = None):
        self.zone = zone_config or RestrictedZoneConfig()
        self._dwell_trackers: Dict[int, int] = {}  # track_id -> consecutive frames inside
        self._prev_status: Dict[int, IncidentStatus] = {}  # track_id -> last status
        self._temporal_trackers: Dict[int, TemporalEvidenceTracker] = {}

    def get_or_create_tracker(self, track_id: int) -> TemporalEvidenceTracker:
        if track_id not in self._temporal_trackers:
            self._temporal_trackers[track_id] = TemporalEvidenceTracker(track_id)
        return self._temporal_trackers[track_id]

    def evaluate_person(
        self,
        person: TrackedPerson,
        frame_idx: int,
        timestamp_sec: float,
        frame_width: int = 640,
        frame_height: int = 480
    ) -> IntrusionReasoningEvaluation:
        """
        Evaluates a tracked person against the configured restricted zone.
        Uses normalized feet location (bottom-center of bounding box).
        """
        obs = person.current_obs
        x1, y1, x2, y2 = obs.bbox
        # Normalized feet coordinate (ground contact position)
        feet_x = ((x1 + x2) / 2.0) / max(1.0, frame_width)
        feet_y = y2 / max(1.0, frame_height)

        is_inside = point_in_polygon(feet_x, feet_y, self.zone.polygon)
        dist_to_boundary = point_polygon_distance(feet_x, feet_y, self.zone.polygon)

        # Update dwell frame counter
        if is_inside:
            self._dwell_trackers[person.track_id] = self._dwell_trackers.get(person.track_id, 0) + 1
        else:
            self._dwell_trackers[person.track_id] = 0

        dwell_count = self._dwell_trackers[person.track_id]
        old_status = self._prev_status.get(person.track_id, IncidentStatus.CANDIDATE)
        temporal_tracker = self.get_or_create_tracker(person.track_id)

        # -------------------------------------------------------------
        # 1. ZONE_BOUNDARY_PROXIMITY
        # -------------------------------------------------------------
        if is_inside:
            ev_boundary = EvidenceItem(
                evidence_type=IntrusionEvidenceCategory.ZONE_BOUNDARY_PROXIMITY.value,
                state=EvidenceState.SUPPORTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.95,
                description=f"Person #{person.track_id} crossed perimeter edge into {self.zone.zone_name}.",
                metadata={"distance": dist_to_boundary, "inside": True}
            )
        elif dist_to_boundary <= 0.08:
            ev_boundary = EvidenceItem(
                evidence_type=IntrusionEvidenceCategory.ZONE_BOUNDARY_PROXIMITY.value,
                state=EvidenceState.UNKNOWN,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.60,
                description=f"Person #{person.track_id} is in immediate proximity to perimeter boundary ({dist_to_boundary:.3f} normalized dist).",
                metadata={"distance": dist_to_boundary, "inside": False}
            )
        else:
            ev_boundary = EvidenceItem(
                evidence_type=IntrusionEvidenceCategory.ZONE_BOUNDARY_PROXIMITY.value,
                state=EvidenceState.CONTRADICTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.90,
                description=f"Person #{person.track_id} is outside perimeter buffer zone ({dist_to_boundary:.3f} normalized dist).",
                metadata={"distance": dist_to_boundary, "inside": False}
            )

        # -------------------------------------------------------------
        # 2. POLYGON_INTERSECTION
        # -------------------------------------------------------------
        if is_inside:
            ev_polygon = EvidenceItem(
                evidence_type=IntrusionEvidenceCategory.POLYGON_INTERSECTION.value,
                state=EvidenceState.SUPPORTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.98,
                description=f"Ground contact position ({feet_x:.2f}, {feet_y:.2f}) strictly intersects restricted polygon coordinates.",
                metadata={"feet": (feet_x, feet_y)}
            )
        else:
            ev_polygon = EvidenceItem(
                evidence_type=IntrusionEvidenceCategory.POLYGON_INTERSECTION.value,
                state=EvidenceState.CONTRADICTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.95,
                description=f"Subject coordinates ({feet_x:.2f}, {feet_y:.2f}) lie outside restricted zone perimeter.",
                metadata={"feet": (feet_x, feet_y)}
            )

        # -------------------------------------------------------------
        # 3. ZONE_DWELL_TIME
        # -------------------------------------------------------------
        if dwell_count >= self.zone.min_dwell_frames:
            ev_dwell = EvidenceItem(
                evidence_type=IntrusionEvidenceCategory.ZONE_DWELL_TIME.value,
                state=EvidenceState.SUPPORTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=min(1.0, 0.80 + (dwell_count / (self.zone.min_dwell_frames * 2.0))),
                description=f"Subject sustained dwell inside restricted zone for {dwell_count} frames (threshold: {self.zone.min_dwell_frames}).",
                metadata={"dwell_frames": dwell_count, "min_required": self.zone.min_dwell_frames}
            )
        elif dwell_count > 0:
            ev_dwell = EvidenceItem(
                evidence_type=IntrusionEvidenceCategory.ZONE_DWELL_TIME.value,
                state=EvidenceState.UNKNOWN,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.55,
                description=f"Dwell duration verifying: {dwell_count}/{self.zone.min_dwell_frames} frames inside perimeter.",
                metadata={"dwell_frames": dwell_count, "min_required": self.zone.min_dwell_frames}
            )
        else:
            ev_dwell = EvidenceItem(
                evidence_type=IntrusionEvidenceCategory.ZONE_DWELL_TIME.value,
                state=EvidenceState.CONTRADICTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.90,
                description="Zero dwell duration; subject not present inside zone.",
                metadata={"dwell_frames": 0}
            )

        # -------------------------------------------------------------
        # 4. TEMPORAL_PERSISTENCE
        # -------------------------------------------------------------
        if is_inside and dwell_count >= self.zone.min_dwell_frames:
            ev_persistence = EvidenceItem(
                evidence_type=IntrusionEvidenceCategory.TEMPORAL_PERSISTENCE.value,
                state=EvidenceState.SUPPORTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.95,
                description="Continuous temporal presence confirmed across multi-frame observation window.",
                metadata={"sustained": True}
            )
        elif is_inside and dwell_count < self.zone.min_dwell_frames:
            ev_persistence = EvidenceItem(
                evidence_type=IntrusionEvidenceCategory.TEMPORAL_PERSISTENCE.value,
                state=EvidenceState.UNKNOWN,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.50,
                description="Temporal persistence undergoing multi-frame verification.",
                metadata={"sustained": False}
            )
        elif not is_inside and old_status in [IncidentStatus.VERIFYING, IncidentStatus.CONFIRMED]:
            ev_persistence = EvidenceItem(
                evidence_type=IntrusionEvidenceCategory.TEMPORAL_PERSISTENCE.value,
                state=EvidenceState.CONTRADICTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.92,
                description="Subject exited restricted zone; persistence contradicted.",
                metadata={"sustained": False}
            )
        else:
            ev_persistence = EvidenceItem(
                evidence_type=IntrusionEvidenceCategory.TEMPORAL_PERSISTENCE.value,
                state=EvidenceState.CONTRADICTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.85,
                description="No persistent perimeter occupancy detected.",
                metadata={"sustained": False}
            )

        # -------------------------------------------------------------
        # 5. ACTIVE_SCHEDULE_RESTRICTION
        # -------------------------------------------------------------
        if self.zone.is_active:
            ev_schedule = EvidenceItem(
                evidence_type=IntrusionEvidenceCategory.ACTIVE_SCHEDULE_RESTRICTION.value,
                state=EvidenceState.SUPPORTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=1.0,
                description=f"Security zone policy is ACTIVE for {self.zone.zone_name}.",
                metadata={"zone_id": self.zone.zone_id}
            )
        else:
            ev_schedule = EvidenceItem(
                evidence_type=IntrusionEvidenceCategory.ACTIVE_SCHEDULE_RESTRICTION.value,
                state=EvidenceState.CONTRADICTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=1.0,
                description=f"Security policy is currently INACTIVE for {self.zone.zone_name}.",
                metadata={"zone_id": self.zone.zone_id}
            )

        evidence_items = [ev_boundary, ev_polygon, ev_dwell, ev_persistence, ev_schedule]

        # -------------------------------------------------------------
        # Completeness & Evidence Score Computation
        # -------------------------------------------------------------
        supported_count = sum(1 for e in evidence_items if e.state == EvidenceState.SUPPORTED)
        is_evidence_complete = (supported_count == 5)

        score = 0.0
        weights = {
            IntrusionEvidenceCategory.ZONE_BOUNDARY_PROXIMITY.value: 0.20,
            IntrusionEvidenceCategory.POLYGON_INTERSECTION.value: 0.25,
            IntrusionEvidenceCategory.ZONE_DWELL_TIME.value: 0.25,
            IntrusionEvidenceCategory.TEMPORAL_PERSISTENCE.value: 0.15,
            IntrusionEvidenceCategory.ACTIVE_SCHEDULE_RESTRICTION.value: 0.15,
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
        if not is_inside and old_status in [IncidentStatus.VERIFYING, IncidentStatus.CONFIRMED]:
            new_status = IncidentStatus.RETRACTED
        elif is_evidence_complete and dwell_count >= self.zone.min_dwell_frames:
            new_status = IncidentStatus.CONFIRMED
        elif is_inside and dwell_count >= (self.zone.min_dwell_frames // 2):
            new_status = IncidentStatus.VERIFYING
        elif is_inside or (dist_to_boundary <= 0.05):
            new_status = IncidentStatus.CANDIDATE
        else:
            new_status = IncidentStatus.CANDIDATE

        self._prev_status[person.track_id] = new_status

        # Strict evidence-complete alert decision: ONLY when CONFIRMED!
        should_alert = (new_status == IncidentStatus.CONFIRMED and is_evidence_complete)

        alert_msg = None
        if should_alert:
            mins = int(timestamp_sec // 60)
            secs = timestamp_sec % 60
            alert_msg = (
                f"CONFIRMED Restricted Zone Intrusion: Person #{person.track_id} entered and remained "
                f"inside {self.zone.zone_name} for {dwell_count} frames at {mins:02d}:{secs:05.2f}."
            )

        # Record temporal snapshot
        temporal_tracker.record_frame(
            frame_idx=frame_idx,
            timestamp_sec=timestamp_sec,
            evidence_items=evidence_items,
            incident_status=new_status.value,
            force_snapshot=(new_status in [IncidentStatus.CONFIRMED, IncidentStatus.RETRACTED])
        )

        return IntrusionReasoningEvaluation(
            track_id=person.track_id,
            zone_id=self.zone.zone_id,
            zone_name=self.zone.zone_name,
            frame_idx=frame_idx,
            timestamp_sec=timestamp_sec,
            incident_status=new_status,
            evidence_score=score,
            is_evidence_complete=is_evidence_complete,
            should_alert=should_alert,
            evidence_items=evidence_items,
            dwell_frames=dwell_count,
            temporal_evolution=temporal_tracker.get_evolution(),
            alert_message=alert_msg,
            risk_level=self.zone.risk_level
        )
