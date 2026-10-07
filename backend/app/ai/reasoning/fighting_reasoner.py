"""
SafeVision AI - Fighting & Aggressive Interaction Reasoner (3-State Kleene Logic)

Analyzes multi-person interaction dynamics, inter-person proximity, kinetic energy/acceleration,
and multi-frame sustained engagement.
Eliminates single-frame false positives (e.g. casual passing, greetings, waving).
Supports reversible lifecycle: CANDIDATE -> VERIFYING -> CONFIRMED / RETRACTED.
"""

from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
import numpy as np

from backend.app.ai.tracking.person_tracker import TrackedPerson
from backend.app.ai.reasoning.evidence_schema import (
    EvidenceState,
    FightEvidenceCategory,
    EvidenceItem,
    FightReasoningEvaluation,
    TemporalFrameSnapshot,
)
from backend.app.ai.reasoning.temporal_evidence_tracker import TemporalEvidenceTracker
from backend.app.models.incident import IncidentStatus, IncidentRiskLevel
from backend.app.core.logging import logger


@dataclass
class FightReasonerConfig:
    proximity_threshold_norm: float = 0.35  # Normalized distance between centroids for close interaction
    kinetic_velocity_threshold: float = 0.18  # High velocity / motion energy threshold
    min_engagement_frames: int = 8  # Minimum consecutive frames of aggressive interaction
    cooldown_frames: int = 30


class FightIncidentReasoner:
    """
    Deterministic rule-and-evidence reasoning engine for Fighting / Physical Aggression.
    Evaluates pairwise interactions across all active tracked persons in the scene.
    """

    def __init__(self, config: Optional[FightReasonerConfig] = None):
        self.config = config or FightReasonerConfig()
        # Pair key: tuple(sorted([id1, id2])) -> consecutive interaction frames
        self._engagement_trackers: Dict[Tuple[int, int], int] = {}
        self._prev_status: Dict[Tuple[int, int], IncidentStatus] = {}
        self._temporal_trackers: Dict[Tuple[int, int], TemporalEvidenceTracker] = {}

    def get_or_create_tracker(self, pair_key: Tuple[int, int]) -> TemporalEvidenceTracker:
        pseudo_id = pair_key[0] * 1000 + pair_key[1]
        if pair_key not in self._temporal_trackers:
            self._temporal_trackers[pair_key] = TemporalEvidenceTracker(pseudo_id)
        return self._temporal_trackers[pair_key]

    def evaluate_scene(
        self,
        active_tracks: List[TrackedPerson],
        frame_idx: int,
        timestamp_sec: float
    ) -> List[FightReasoningEvaluation]:
        """
        Evaluates pairwise interactions among all tracked persons.
        Returns evaluation for each pair exhibiting suspicious or aggressive interaction.
        """
        evaluations: List[FightReasoningEvaluation] = []
        n = len(active_tracks)

        if n < 2:
            return evaluations

        # Test each pair
        for i in range(n):
            for j in range(i + 1, n):
                p1 = active_tracks[i]
                p2 = active_tracks[j]
                pair_key = (min(p1.track_id, p2.track_id), max(p1.track_id, p2.track_id))
                eval_res = self._evaluate_pair(p1, p2, pair_key, frame_idx, timestamp_sec)
                if eval_res is not None:
                    evaluations.append(eval_res)

        return evaluations

    def _evaluate_pair(
        self,
        p1: TrackedPerson,
        p2: TrackedPerson,
        pair_key: Tuple[int, int],
        frame_idx: int,
        timestamp_sec: float
    ) -> Optional[FightReasoningEvaluation]:
        c1 = np.array(p1.current_obs.centroid)
        c2 = np.array(p2.current_obs.centroid)
        dist = float(np.linalg.norm(c1 - c2))

        # Check box overlap (intersection over min area)
        b1 = p1.current_obs.bbox
        b2 = p2.current_obs.bbox
        dx = min(b1[2], b2[2]) - max(b1[0], b2[0])
        dy = min(b1[3], b2[3]) - max(b1[1], b2[1])
        has_overlap = (dx > 0 and dy > 0)

        # Kinetic energy metric: combine vertical velocities and centroid motion
        vel1 = abs(p1.current_obs.vertical_velocity if hasattr(p1.current_obs, "vertical_velocity") else 0.0)
        vel2 = abs(p2.current_obs.vertical_velocity if hasattr(p2.current_obs, "vertical_velocity") else 0.0)
        if len(p1.history) >= 2:
            v1_vec = np.linalg.norm(np.array(p1.history[-1].observation.centroid) - np.array(p1.history[-2].observation.centroid))
        else:
            v1_vec = 0.0
        if len(p2.history) >= 2:
            v2_vec = np.linalg.norm(np.array(p2.history[-1].observation.centroid) - np.array(p2.history[-2].observation.centroid))
        else:
            v2_vec = 0.0

        kinetic_metric = float(max(vel1 + vel2, (v1_vec + v2_vec) * 15.0))

        # Proximity test
        in_proximity = (dist <= self.config.proximity_threshold_norm) or has_overlap
        is_high_kinetic = (kinetic_metric >= self.config.kinetic_velocity_threshold)

        # Update engagement frames
        if in_proximity and (is_high_kinetic or self._engagement_trackers.get(pair_key, 0) > 0):
            self._engagement_trackers[pair_key] = self._engagement_trackers.get(pair_key, 0) + 1
        else:
            self._engagement_trackers[pair_key] = 0

        engagement_count = self._engagement_trackers[pair_key]
        old_status = self._prev_status.get(pair_key, IncidentStatus.CANDIDATE)
        tracker = self.get_or_create_tracker(pair_key)

        # If pair is far and was never active, skip evaluation
        if not in_proximity and engagement_count == 0 and old_status == IncidentStatus.CANDIDATE:
            return None

        # -------------------------------------------------------------
        # 1. MULTI_PERSON_PROXIMITY
        # -------------------------------------------------------------
        if in_proximity:
            ev_prox = EvidenceItem(
                evidence_type=FightEvidenceCategory.MULTI_PERSON_PROXIMITY.value,
                state=EvidenceState.SUPPORTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.94,
                description=f"Persons #{p1.track_id} and #{p2.track_id} in close physical proximity ({dist:.2f} norm dist, overlap={has_overlap}).",
                metadata={"distance": dist, "overlap": has_overlap}
            )
        elif dist <= self.config.proximity_threshold_norm * 1.5:
            ev_prox = EvidenceItem(
                evidence_type=FightEvidenceCategory.MULTI_PERSON_PROXIMITY.value,
                state=EvidenceState.UNKNOWN,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.55,
                description=f"Persons #{p1.track_id} and #{p2.track_id} in intermediate proximity ({dist:.2f} norm dist).",
                metadata={"distance": dist}
            )
        else:
            ev_prox = EvidenceItem(
                evidence_type=FightEvidenceCategory.MULTI_PERSON_PROXIMITY.value,
                state=EvidenceState.CONTRADICTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.90,
                description=f"Spatial distance ({dist:.2f} norm dist) exceeds altercation threshold.",
                metadata={"distance": dist}
            )

        # -------------------------------------------------------------
        # 2. MUTUAL_INTERACTION_DYNAMICS
        # -------------------------------------------------------------
        if in_proximity and (has_overlap or dist < 0.20):
            ev_dynamics = EvidenceItem(
                evidence_type=FightEvidenceCategory.MUTUAL_INTERACTION_DYNAMICS.value,
                state=EvidenceState.SUPPORTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.92,
                description="Dense physical contact and converging trajectories between tracked subjects.",
                metadata={"overlap": has_overlap}
            )
        elif in_proximity:
            ev_dynamics = EvidenceItem(
                evidence_type=FightEvidenceCategory.MUTUAL_INTERACTION_DYNAMICS.value,
                state=EvidenceState.UNKNOWN,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.55,
                description="Subjects in close vicinity; interaction dynamics verifying.",
                metadata={"overlap": False}
            )
        else:
            ev_dynamics = EvidenceItem(
                evidence_type=FightEvidenceCategory.MUTUAL_INTERACTION_DYNAMICS.value,
                state=EvidenceState.CONTRADICTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.88,
                description="No mutual trajectory convergence or body contact.",
                metadata={"overlap": False}
            )

        # -------------------------------------------------------------
        # 3. HIGH_KINETIC_MOTION
        # -------------------------------------------------------------
        if is_high_kinetic and in_proximity:
            ev_kinetic = EvidenceItem(
                evidence_type=FightEvidenceCategory.HIGH_KINETIC_MOTION.value,
                state=EvidenceState.SUPPORTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=min(1.0, 0.75 + (kinetic_metric / (self.config.kinetic_velocity_threshold * 2.0))),
                description=f"High kinetic agitation detected ({kinetic_metric:.2f} velocity/energy metric exceeds {self.config.kinetic_velocity_threshold:.2f}).",
                metadata={"kinetic_metric": kinetic_metric}
            )
        elif in_proximity:
            ev_kinetic = EvidenceItem(
                evidence_type=FightEvidenceCategory.HIGH_KINETIC_MOTION.value,
                state=EvidenceState.UNKNOWN,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.50,
                description=f"Moderate motion observed ({kinetic_metric:.2f}); observing for rapid reciprocating strikes.",
                metadata={"kinetic_metric": kinetic_metric}
            )
        else:
            ev_kinetic = EvidenceItem(
                evidence_type=FightEvidenceCategory.HIGH_KINETIC_MOTION.value,
                state=EvidenceState.CONTRADICTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.85,
                description="Low kinetic variance; normal calm movements.",
                metadata={"kinetic_metric": kinetic_metric}
            )

        # -------------------------------------------------------------
        # 4. SUSTAINED_ENGAGEMENT
        # -------------------------------------------------------------
        if engagement_count >= self.config.min_engagement_frames:
            ev_sustained = EvidenceItem(
                evidence_type=FightEvidenceCategory.SUSTAINED_ENGAGEMENT.value,
                state=EvidenceState.SUPPORTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=min(1.0, 0.80 + (engagement_count / (self.config.min_engagement_frames * 2.0))),
                description=f"Physical altercation sustained across {engagement_count} consecutive frames (threshold: {self.config.min_engagement_frames}).",
                metadata={"engagement_frames": engagement_count}
            )
        elif engagement_count > 0:
            ev_sustained = EvidenceItem(
                evidence_type=FightEvidenceCategory.SUSTAINED_ENGAGEMENT.value,
                state=EvidenceState.UNKNOWN,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.50,
                description=f"Altercation duration verifying ({engagement_count}/{self.config.min_engagement_frames} frames).",
                metadata={"engagement_frames": engagement_count}
            )
        else:
            ev_sustained = EvidenceItem(
                evidence_type=FightEvidenceCategory.SUSTAINED_ENGAGEMENT.value,
                state=EvidenceState.CONTRADICTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.90,
                description="No sustained engagement detected.",
                metadata={"engagement_frames": 0}
            )

        # -------------------------------------------------------------
        # 5. TEMPORAL_CONSISTENCY
        # -------------------------------------------------------------
        if ev_prox.state == EvidenceState.SUPPORTED and ev_kinetic.state == EvidenceState.SUPPORTED and ev_sustained.state == EvidenceState.SUPPORTED:
            ev_temporal = EvidenceItem(
                evidence_type=FightEvidenceCategory.TEMPORAL_CONSISTENCY.value,
                state=EvidenceState.SUPPORTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.95,
                description="Consistent altercation sequence: Rapid approach -> Interpersonal contact -> Sustained violent motion.",
                metadata={"consistent": True}
            )
        elif not in_proximity and old_status in [IncidentStatus.VERIFYING, IncidentStatus.CONFIRMED]:
            ev_temporal = EvidenceItem(
                evidence_type=FightEvidenceCategory.TEMPORAL_CONSISTENCY.value,
                state=EvidenceState.CONTRADICTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.92,
                description="Subjects naturally separated; altercation contradicted or disengaged.",
                metadata={"consistent": False}
            )
        elif in_proximity:
            ev_temporal = EvidenceItem(
                evidence_type=FightEvidenceCategory.TEMPORAL_CONSISTENCY.value,
                state=EvidenceState.UNKNOWN,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.50,
                description="Multi-frame altercation timeline undergoing active temporal evaluation.",
                metadata={"consistent": False}
            )
        else:
            ev_temporal = EvidenceItem(
                evidence_type=FightEvidenceCategory.TEMPORAL_CONSISTENCY.value,
                state=EvidenceState.CONTRADICTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.88,
                description="No temporal consistency for altercation.",
                metadata={"consistent": False}
            )

        evidence_items = [ev_prox, ev_dynamics, ev_kinetic, ev_sustained, ev_temporal]

        # -------------------------------------------------------------
        # Completeness & Evidence Score Computation
        # -------------------------------------------------------------
        supported_count = sum(1 for e in evidence_items if e.state == EvidenceState.SUPPORTED)
        is_evidence_complete = (supported_count == 5)

        score = 0.0
        weights = {
            FightEvidenceCategory.MULTI_PERSON_PROXIMITY.value: 0.20,
            FightEvidenceCategory.MUTUAL_INTERACTION_DYNAMICS.value: 0.20,
            FightEvidenceCategory.HIGH_KINETIC_MOTION.value: 0.25,
            FightEvidenceCategory.SUSTAINED_ENGAGEMENT.value: 0.25,
            FightEvidenceCategory.TEMPORAL_CONSISTENCY.value: 0.10,
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
        if not in_proximity and old_status in [IncidentStatus.VERIFYING, IncidentStatus.CONFIRMED]:
            new_status = IncidentStatus.RETRACTED
        elif is_evidence_complete and engagement_count >= self.config.min_engagement_frames:
            new_status = IncidentStatus.CONFIRMED
        elif in_proximity and is_high_kinetic and engagement_count >= (self.config.min_engagement_frames // 2):
            new_status = IncidentStatus.VERIFYING
        elif in_proximity:
            new_status = IncidentStatus.CANDIDATE
        else:
            new_status = IncidentStatus.CANDIDATE

        self._prev_status[pair_key] = new_status

        # Strict evidence-complete alert decision
        should_alert = (new_status == IncidentStatus.CONFIRMED and is_evidence_complete)

        alert_msg = None
        if should_alert:
            mins = int(timestamp_sec // 60)
            secs = timestamp_sec % 60
            alert_msg = (
                f"CONFIRMED Physical Altercation between Persons #{pair_key[0]} and #{pair_key[1]} at {mins:02d}:{secs:05.2f}: "
                f"Sustained high-energy violent engagement verified for {engagement_count} frames."
            )

        # Record temporal snapshot
        tracker.record_frame(
            frame_idx=frame_idx,
            timestamp_sec=timestamp_sec,
            evidence_items=evidence_items,
            incident_status=new_status.value,
            force_snapshot=(new_status in [IncidentStatus.CONFIRMED, IncidentStatus.RETRACTED])
        )

        return FightReasoningEvaluation(
            involved_track_ids=[pair_key[0], pair_key[1]],
            frame_idx=frame_idx,
            timestamp_sec=timestamp_sec,
            incident_status=new_status,
            evidence_score=score,
            is_evidence_complete=is_evidence_complete,
            should_alert=should_alert,
            evidence_items=evidence_items,
            interaction_distance=round(dist, 2),
            temporal_evolution=tracker.get_evolution(),
            alert_message=alert_msg,
            risk_level=IncidentRiskLevel.CRITICAL
        )
