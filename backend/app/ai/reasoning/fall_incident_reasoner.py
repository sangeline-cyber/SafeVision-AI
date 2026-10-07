"""
SafeVision AI - Evidence-Driven Fall Incident Reasoner

Implements the 5-point Fall Evidence Schema, 3-state Kleene logic,
reversible incident lifecycle, and evidence-complete alerting decision.

The 5 Evidence Categories:
1. DOWNWARD_MOVEMENT
2. POSTURE_TRANSITION
3. LOW_OR_HORIZONTAL_POSTURE
4. REMAINS_DOWN
5. TEMPORAL_CONSISTENCY

Lifecycle:
CANDIDATE -> VERIFYING -> CONFIRMED
VERIFYING -> RETRACTED
CONFIRMED -> RETRACTED
"""

from typing import Dict, List, Tuple, Optional
from datetime import datetime

from backend.app.ai.tracking.person_tracker import TrackedPerson, TrackHistoryPoint
from backend.app.ai.reasoning.evidence_schema import (
    EvidenceState,
    FallEvidenceCategory,
    EvidenceItem,
    FallReasoningEvaluation,
)
from backend.app.ai.reasoning.temporal_evidence_tracker import TemporalEvidenceTracker
from backend.app.models.incident import IncidentStatus, IncidentRiskLevel
from backend.app.core.fall_config import fall_config
from backend.app.core.logging import logger


class FallIncidentReasoner:
    """
    Deterministic rule-and-evidence reasoning engine for Fall Safety Events.
    Evaluates existing tracked person kinematics against the 5-point evidence schema.
    """

    def __init__(self):
        self._temporal_trackers: Dict[int, TemporalEvidenceTracker] = {}

    def get_or_create_tracker(self, track_id: int) -> TemporalEvidenceTracker:
        if track_id not in self._temporal_trackers:
            self._temporal_trackers[track_id] = TemporalEvidenceTracker(track_id)
        return self._temporal_trackers[track_id]

    def evaluate(
        self,
        person: TrackedPerson,
        frame_idx: int,
        timestamp_sec: float
    ) -> FallReasoningEvaluation:
        """
        Evaluates the 5-point Fall Evidence Schema for a tracked person at the given frame.
        Returns a complete FallReasoningEvaluation with 3-state evidence items,
        reversible incident status, and alert decision.
        """
        history = list(person.history)
        tracker = self.get_or_create_tracker(person.track_id)
        old_state = person.fall_state

        # -------------------------------------------------------------
        # 1. DOWNWARD_MOVEMENT
        # -------------------------------------------------------------
        if len(history) < 3:
            ev_downward = EvidenceItem(
                evidence_type=FallEvidenceCategory.DOWNWARD_MOVEMENT.value,
                state=EvidenceState.UNKNOWN,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.50,
                description="Insufficient history (< 3 frames) to determine downward velocity vector.",
                metadata={"history_len": len(history)}
            )
        else:
            recent_window = history[-min(len(history), 20):]
            max_downward_vel = max((pt.vertical_velocity for pt in recent_window), default=0.0)

            if max_downward_vel >= fall_config.DOWNWARD_VELOCITY_THRESHOLD:
                conf = min(1.0, max_downward_vel / (fall_config.DOWNWARD_VELOCITY_THRESHOLD * 2.0))
                ev_downward = EvidenceItem(
                    evidence_type=FallEvidenceCategory.DOWNWARD_MOVEMENT.value,
                    state=EvidenceState.SUPPORTED,
                    timestamp_sec=timestamp_sec,
                    frame_idx=frame_idx,
                    confidence=float(conf),
                    description=f"Rapid downward velocity spike detected ({max_downward_vel:.2f} delta Y/s, exceeding {fall_config.DOWNWARD_VELOCITY_THRESHOLD:.2f} threshold).",
                    metadata={"velocity": max_downward_vel, "threshold": fall_config.DOWNWARD_VELOCITY_THRESHOLD}
                )
            elif max_downward_vel > (fall_config.DOWNWARD_VELOCITY_THRESHOLD * 0.5):
                ev_downward = EvidenceItem(
                    evidence_type=FallEvidenceCategory.DOWNWARD_MOVEMENT.value,
                    state=EvidenceState.UNKNOWN,
                    timestamp_sec=timestamp_sec,
                    frame_idx=frame_idx,
                    confidence=0.50,
                    description=f"Moderate downward movement observed ({max_downward_vel:.2f} delta Y/s); below sudden descent threshold.",
                    metadata={"velocity": max_downward_vel}
                )
            else:
                ev_downward = EvidenceItem(
                    evidence_type=FallEvidenceCategory.DOWNWARD_MOVEMENT.value,
                    state=EvidenceState.CONTRADICTED,
                    timestamp_sec=timestamp_sec,
                    frame_idx=frame_idx,
                    confidence=0.85,
                    description=f"Downward movement within benign limits ({max_downward_vel:.2f} delta Y/s); vertical position remains stable.",
                    metadata={"velocity": max_downward_vel}
                )

        # -------------------------------------------------------------
        # 2. POSTURE_TRANSITION
        # -------------------------------------------------------------
        was_upright = any(
            (pt.torso_angle >= fall_config.TORSO_ANGLE_UPRIGHT_THRESHOLD_DEG or pt.observation.is_upright)
            for pt in history[:-min(len(history), 5)]
        )
        curr_obs = person.current_obs
        is_currently_prone = curr_obs.is_prone or (curr_obs.torso_angle_deg <= fall_config.TORSO_ANGLE_HORIZONTAL_THRESHOLD_DEG)
        is_currently_upright = curr_obs.is_upright or (curr_obs.torso_angle_deg >= fall_config.TORSO_ANGLE_UPRIGHT_THRESHOLD_DEG)

        if len(history) < 5:
            ev_transition = EvidenceItem(
                evidence_type=FallEvidenceCategory.POSTURE_TRANSITION.value,
                state=EvidenceState.UNKNOWN,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.50,
                description="Observing initial posture baseline (< 5 frames).",
                metadata={"history_len": len(history)}
            )
        elif was_upright and is_currently_prone:
            ev_transition = EvidenceItem(
                evidence_type=FallEvidenceCategory.POSTURE_TRANSITION.value,
                state=EvidenceState.SUPPORTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.92,
                description=f"Significant posture transition observed from upright baseline to horizontal/prone collapse (torso: {curr_obs.torso_angle_deg:.1f}°).",
                metadata={"was_upright": True, "torso_angle": curr_obs.torso_angle_deg}
            )
        elif is_currently_prone and not was_upright:
            ev_transition = EvidenceItem(
                evidence_type=FallEvidenceCategory.POSTURE_TRANSITION.value,
                state=EvidenceState.UNKNOWN,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.50,
                description="Subject observed in low posture, but prior upright baseline was obscured or outside frame.",
                metadata={"was_upright": False}
            )
        elif not is_currently_prone and is_currently_upright:
            ev_transition = EvidenceItem(
                evidence_type=FallEvidenceCategory.POSTURE_TRANSITION.value,
                state=EvidenceState.CONTRADICTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.90,
                description="Subject maintained upright spinal alignment throughout observation window.",
                metadata={"torso_angle": curr_obs.torso_angle_deg}
            )
        else:
            ev_transition = EvidenceItem(
                evidence_type=FallEvidenceCategory.POSTURE_TRANSITION.value,
                state=EvidenceState.UNKNOWN,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.60,
                description=f"Intermediate posture transition (torso: {curr_obs.torso_angle_deg:.1f}°); undergoing multi-frame observation.",
                metadata={"torso_angle": curr_obs.torso_angle_deg}
            )

        # -------------------------------------------------------------
        # 3. LOW_OR_HORIZONTAL_POSTURE
        # -------------------------------------------------------------
        torso_angle = curr_obs.torso_angle_deg
        aspect_w_h = curr_obs.aspect_ratio_w_h

        if torso_angle <= fall_config.TORSO_ANGLE_HORIZONTAL_THRESHOLD_DEG and aspect_w_h >= 1.0:
            ev_low = EvidenceItem(
                evidence_type=FallEvidenceCategory.LOW_OR_HORIZONTAL_POSTURE.value,
                state=EvidenceState.SUPPORTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.94,
                description=f"Subject body axis is horizontally oriented on ground (torso: {torso_angle:.1f}°, W/H: {aspect_w_h:.2f}).",
                metadata={"torso_angle": torso_angle, "aspect_w_h": aspect_w_h}
            )
        elif torso_angle >= fall_config.TORSO_ANGLE_UPRIGHT_THRESHOLD_DEG and curr_obs.aspect_ratio_h_w > 1.25:
            ev_low = EvidenceItem(
                evidence_type=FallEvidenceCategory.LOW_OR_HORIZONTAL_POSTURE.value,
                state=EvidenceState.CONTRADICTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.90,
                description=f"Subject posture is vertical upright (torso: {torso_angle:.1f}°, H/W: {curr_obs.aspect_ratio_h_w:.2f}).",
                metadata={"torso_angle": torso_angle}
            )
        else:
            ev_low = EvidenceItem(
                evidence_type=FallEvidenceCategory.LOW_OR_HORIZONTAL_POSTURE.value,
                state=EvidenceState.UNKNOWN,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.55,
                description=f"Ambiguous posture orientation (torso: {torso_angle:.1f}°, W/H: {aspect_w_h:.2f}); neither flat nor upright.",
                metadata={"torso_angle": torso_angle, "aspect_w_h": aspect_w_h}
            )

        # -------------------------------------------------------------
        # 4. REMAINS_DOWN
        # -------------------------------------------------------------
        prone_frames_count = 0
        for pt in reversed(history):
            if pt.observation.is_prone or pt.torso_angle <= fall_config.TORSO_ANGLE_HORIZONTAL_THRESHOLD_DEG:
                prone_frames_count += 1
            else:
                break

        has_recovered = (
            prone_frames_count < 3 and 
            curr_obs.is_upright and 
            curr_obs.torso_angle_deg >= fall_config.TORSO_ANGLE_UPRIGHT_THRESHOLD_DEG and
            was_upright
        )

        if has_recovered:
            ev_remains = EvidenceItem(
                evidence_type=FallEvidenceCategory.REMAINS_DOWN.value,
                state=EvidenceState.CONTRADICTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.95,
                description="Subject resumed upright standing posture (recovery detected; contradicts sustained fall).",
                metadata={"has_recovered": True, "prone_frames": prone_frames_count}
            )
        elif prone_frames_count >= fall_config.MIN_PERSISTENCE_FRAMES:
            conf = min(1.0, 0.75 + (prone_frames_count / 30.0))
            ev_remains = EvidenceItem(
                evidence_type=FallEvidenceCategory.REMAINS_DOWN.value,
                state=EvidenceState.SUPPORTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=float(conf),
                description=f"Subject remained continuously prone for {prone_frames_count} frames (exceeds {fall_config.MIN_PERSISTENCE_FRAMES} persistence threshold).",
                metadata={"prone_frames": prone_frames_count, "min_required": fall_config.MIN_PERSISTENCE_FRAMES}
            )
        elif prone_frames_count > 0 or ev_downward.state == EvidenceState.SUPPORTED:
            ev_remains = EvidenceItem(
                evidence_type=FallEvidenceCategory.REMAINS_DOWN.value,
                state=EvidenceState.UNKNOWN,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.50,
                description=f"Ground persistence currently verifying ({prone_frames_count}/{fall_config.MIN_PERSISTENCE_FRAMES} required frames elapsed).",
                metadata={"prone_frames": prone_frames_count, "min_required": fall_config.MIN_PERSISTENCE_FRAMES}
            )
        else:
            ev_remains = EvidenceItem(
                evidence_type=FallEvidenceCategory.REMAINS_DOWN.value,
                state=EvidenceState.CONTRADICTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.85,
                description="Subject is not remaining down on the ground.",
                metadata={"prone_frames": 0}
            )

        # -------------------------------------------------------------
        # 5. TEMPORAL_CONSISTENCY
        # -------------------------------------------------------------
        if (
            ev_downward.state == EvidenceState.SUPPORTED and
            ev_transition.state == EvidenceState.SUPPORTED and
            ev_low.state == EvidenceState.SUPPORTED and
            ev_remains.state == EvidenceState.SUPPORTED
        ):
            ev_temporal = EvidenceItem(
                evidence_type=FallEvidenceCategory.TEMPORAL_CONSISTENCY.value,
                state=EvidenceState.SUPPORTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.95,
                description="Consistent temporal sequence: Upright -> Rapid descent -> Posture collapse -> Sustained ground presence.",
                metadata={"sequence_complete": True}
            )
        elif ev_remains.state == EvidenceState.CONTRADICTED and old_state in [IncidentStatus.VERIFYING.value, IncidentStatus.CONFIRMED.value]:
            ev_temporal = EvidenceItem(
                evidence_type=FallEvidenceCategory.TEMPORAL_CONSISTENCY.value,
                state=EvidenceState.CONTRADICTED,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.90,
                description="Temporal sequence contradicts fall event: no sustained presence or normal motion observed.",
                metadata={"sequence_complete": False}
            )
        elif ev_downward.state == EvidenceState.SUPPORTED or ev_transition.state == EvidenceState.SUPPORTED:
            ev_temporal = EvidenceItem(
                evidence_type=FallEvidenceCategory.TEMPORAL_CONSISTENCY.value,
                state=EvidenceState.UNKNOWN,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.50,
                description="Temporal sequence partially observed; causal sequence undergoing ongoing multi-frame evaluation.",
                metadata={"sequence_complete": False}
            )
        else:
            ev_temporal = EvidenceItem(
                evidence_type=FallEvidenceCategory.TEMPORAL_CONSISTENCY.value,
                state=EvidenceState.UNKNOWN,
                timestamp_sec=timestamp_sec,
                frame_idx=frame_idx,
                confidence=0.50,
                description="Temporal consistency cannot be determined; event has not developed.",
                metadata={"sequence_complete": False}
            )

        evidence_items = [ev_downward, ev_transition, ev_low, ev_remains, ev_temporal]

        # -------------------------------------------------------------
        # Evidence Completeness & Score Calculation
        # -------------------------------------------------------------
        supported_count = sum(1 for e in evidence_items if e.state == EvidenceState.SUPPORTED)
        contradicted_count = sum(1 for e in evidence_items if e.state == EvidenceState.CONTRADICTED)

        is_evidence_complete = (supported_count == 5)

        # Weighted Fall Evidence Score (0.0 to 1.0)
        weights = {
            FallEvidenceCategory.DOWNWARD_MOVEMENT.value: 0.20,
            FallEvidenceCategory.POSTURE_TRANSITION.value: 0.20,
            FallEvidenceCategory.LOW_OR_HORIZONTAL_POSTURE.value: 0.20,
            FallEvidenceCategory.REMAINS_DOWN.value: 0.20,
            FallEvidenceCategory.TEMPORAL_CONSISTENCY.value: 0.20
        }
        score = 0.0
        for ev in evidence_items:
            w = weights.get(ev.evidence_type, 0.20)
            if ev.state == EvidenceState.SUPPORTED:
                score += w * ev.confidence
            elif ev.state == EvidenceState.UNKNOWN:
                score += w * 0.25 * ev.confidence

        score = float(round(score, 3))

        # -------------------------------------------------------------
        # Reversible Incident Lifecycle Resolution
        # -------------------------------------------------------------
        if has_recovered:
            new_status = IncidentStatus.RETRACTED
        elif is_evidence_complete:
            new_status = IncidentStatus.CONFIRMED
        elif (
            ev_downward.state == EvidenceState.SUPPORTED and 
            (ev_transition.state == EvidenceState.SUPPORTED or is_currently_prone)
        ):
            new_status = IncidentStatus.VERIFYING
        elif ev_downward.state == EvidenceState.SUPPORTED or is_currently_prone:
            new_status = IncidentStatus.CANDIDATE
        else:
            if old_state in [IncidentStatus.VERIFYING.value, IncidentStatus.CONFIRMED.value] and not is_currently_prone:
                new_status = IncidentStatus.RETRACTED
            else:
                new_status = IncidentStatus.CANDIDATE

        # -------------------------------------------------------------
        # Evidence-Complete Alerting Decision
        # -------------------------------------------------------------
        # Strictly generate alert ONLY when status is CONFIRMED and evidence is complete!
        should_alert = (new_status == IncidentStatus.CONFIRMED and is_evidence_complete)

        alert_msg = None
        if should_alert:
            mins = int(timestamp_sec // 60)
            secs = timestamp_sec % 60
            alert_msg = (
                f"CONFIRMED Fall Incident for Person #{person.track_id} at {mins:02d}:{secs:05.2f}: "
                f"All 5 evidence criteria verified (Downward Movement, Posture Transition, "
                f"Horizontal Posture, Ground Persistence, Temporal Consistency)."
            )

        # Record temporal snapshot
        tracker.record_frame(
            frame_idx=frame_idx,
            timestamp_sec=timestamp_sec,
            evidence_items=evidence_items,
            incident_status=new_status.value,
            force_snapshot=(new_status in [IncidentStatus.CONFIRMED, IncidentStatus.RETRACTED])
        )

        return FallReasoningEvaluation(
            track_id=person.track_id,
            frame_idx=frame_idx,
            timestamp_sec=timestamp_sec,
            incident_status=new_status,
            evidence_score=score,
            is_evidence_complete=is_evidence_complete,
            should_alert=should_alert,
            evidence_items=evidence_items,
            temporal_evolution=tracker.get_evolution(),
            alert_message=alert_msg,
            risk_level=IncidentRiskLevel.CRITICAL if should_alert else IncidentRiskLevel.HIGH
        )
