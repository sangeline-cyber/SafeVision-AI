"""
SafeVision AI - Fall Evidence Reasoner (3-State Logic)

Evaluates the 5-point Fall Evidence Schema:
1. Rapid downward vertical velocity
2. Posture transition (upright -> horizontal collapse)
3. Ground-level horizontal orientation
4. Sustained ground persistence
5. Recovery check (triggers RETRACTED if person resumes upright posture)
"""

from typing import List, Dict, Any, Tuple
from datetime import datetime

from backend.app.ai.base import EvidenceObservation
from backend.app.ai.tracking.person_tracker import TrackedPerson, TrackHistoryPoint
from backend.app.models.evidence import EvidenceStatus
from backend.app.models.incident import IncidentStatus, IncidentRiskLevel
from backend.app.core.fall_config import fall_config


class FallEvidenceReasoner:
    """
    Deterministic rule-and-evidence reasoning engine for Fall Detection.
    """

    def evaluate_person_evidence(
        self,
        person: TrackedPerson,
        current_frame: int,
        timestamp_sec: float
    ) -> Tuple[List[EvidenceObservation], float, IncidentStatus]:
        """
        Evaluates multi-frame historical trajectory of a tracked person against the Fall Evidence Schema.

        Returns:
            (evidence_items, evidence_score, incident_status)
        """
        history = list(person.history)
        if len(history) < 3:
            return [], 0.0, IncidentStatus.CANDIDATE

        evidence_list: List[EvidenceObservation] = []
        now = datetime.now()

        # -------------------------------------------------------------
        # 1. Downward Velocity Evidence
        # -------------------------------------------------------------
        # Look back up to 20 frames for downward velocity spike
        recent_window = history[-min(len(history), 20):]
        max_downward_vel = max((pt.vertical_velocity for pt in recent_window), default=0.0)
        
        if max_downward_vel >= fall_config.DOWNWARD_VELOCITY_THRESHOLD:
            ev1_status = EvidenceStatus.SUPPORTED
            ev1_conf = min(1.0, max_downward_vel / (fall_config.DOWNWARD_VELOCITY_THRESHOLD * 2.5))
            ev1_desc = f"Downward vertical velocity spike detected ({max_downward_vel:.2f} delta Y/s)"
        elif max_downward_vel > (fall_config.DOWNWARD_VELOCITY_THRESHOLD * 0.5):
            ev1_status = EvidenceStatus.UNKNOWN
            ev1_conf = 0.5
            ev1_desc = f"Moderate downward movement observed ({max_downward_vel:.2f} delta Y/s)"
        else:
            ev1_status = EvidenceStatus.CONTRADICTED
            ev1_conf = 0.8
            ev1_desc = f"Downward velocity within benign bounds ({max_downward_vel:.2f} delta Y/s)"

        evidence_list.append(EvidenceObservation(
            evidence_type="rapid_downward_velocity",
            description=ev1_desc,
            status=ev1_status.value,
            confidence=float(ev1_conf),
            timestamp=now
        ))

        # -------------------------------------------------------------
        # 2. Posture Transition Collapse Evidence
        # -------------------------------------------------------------
        # Check if person was upright earlier and is now prone/horizontal
        was_upright = any(
            (pt.torso_angle >= fall_config.TORSO_ANGLE_UPRIGHT_THRESHOLD_DEG or pt.observation.is_upright)
            for pt in history[:-min(len(history), 5)]
        )
        is_currently_prone = person.current_obs.is_prone or (person.current_obs.torso_angle_deg <= fall_config.TORSO_ANGLE_HORIZONTAL_THRESHOLD_DEG)

        if was_upright and is_currently_prone:
            ev2_status = EvidenceStatus.SUPPORTED
            ev2_conf = 0.90
            ev2_desc = f"Observed rapid posture collapse from upright to prone ({person.current_obs.torso_angle_deg:.1f}° torso angle)"
        elif is_currently_prone and not was_upright:
            ev2_status = EvidenceStatus.UNKNOWN
            ev2_conf = 0.50
            ev2_desc = "Person observed prone, but upright baseline was partially obscured"
        else:
            ev2_status = EvidenceStatus.CONTRADICTED
            ev2_conf = 0.85
            ev2_desc = "Person maintained upright spinal alignment throughout observation"

        evidence_list.append(EvidenceObservation(
            evidence_type="posture_transition_collapse",
            description=ev2_desc,
            status=ev2_status.value,
            confidence=float(ev2_conf),
            timestamp=now
        ))

        # -------------------------------------------------------------
        # 3. Ground-Level Orientation Evidence
        # -------------------------------------------------------------
        curr_obs = person.current_obs
        aspect_w_h = curr_obs.aspect_ratio_w_h

        if curr_obs.torso_angle_deg <= fall_config.TORSO_ANGLE_HORIZONTAL_THRESHOLD_DEG and aspect_w_h >= 1.0:
            ev3_status = EvidenceStatus.SUPPORTED
            ev3_conf = 0.92
            ev3_desc = f"Subject body axis is horizontal (torso: {curr_obs.torso_angle_deg:.1f}°, W/H: {aspect_w_h:.2f})"
        elif curr_obs.torso_angle_deg <= 55.0 or aspect_w_h >= fall_config.ASPECT_RATIO_COLLAPSE_THRESHOLD:
            ev3_status = EvidenceStatus.UNKNOWN
            ev3_conf = 0.60
            ev3_desc = f"Intermediate body tilt observed (torso: {curr_obs.torso_angle_deg:.1f}°, W/H: {aspect_w_h:.2f})"
        else:
            ev3_status = EvidenceStatus.CONTRADICTED
            ev3_conf = 0.90
            ev3_desc = f"Subject orientation is vertical upright (torso: {curr_obs.torso_angle_deg:.1f}°)"

        evidence_list.append(EvidenceObservation(
            evidence_type="ground_level_orientation",
            description=ev3_desc,
            status=ev3_status.value,
            confidence=float(ev3_conf),
            timestamp=now
        ))

        # -------------------------------------------------------------
        # 4. Sustained Ground Persistence Evidence
        # -------------------------------------------------------------
        # Count consecutive prone frames in recent history
        prone_frames_count = 0
        for pt in reversed(history):
            if pt.observation.is_prone or pt.torso_angle <= fall_config.TORSO_ANGLE_HORIZONTAL_THRESHOLD_DEG:
                prone_frames_count += 1
            else:
                break

        if prone_frames_count >= fall_config.MIN_PERSISTENCE_FRAMES:
            ev4_status = EvidenceStatus.SUPPORTED
            ev4_conf = min(1.0, 0.70 + (prone_frames_count / 30.0))
            ev4_desc = f"Person remained prone for {prone_frames_count} consecutive frames (exceeds {fall_config.MIN_PERSISTENCE_FRAMES} threshold)"
        elif prone_frames_count >= (fall_config.MIN_PERSISTENCE_FRAMES // 2):
            ev4_status = EvidenceStatus.UNKNOWN
            ev4_conf = 0.50
            ev4_desc = f"Prone posture currently verifying ({prone_frames_count}/{fall_config.MIN_PERSISTENCE_FRAMES} frames)"
        else:
            ev4_status = EvidenceStatus.CONTRADICTED
            ev4_conf = 0.85
            ev4_desc = f"Transient or non-persistent posture shift ({prone_frames_count} frames)"

        evidence_list.append(EvidenceObservation(
            evidence_type="sustained_ground_persistence",
            description=ev4_desc,
            status=ev4_status.value,
            confidence=float(ev4_conf),
            timestamp=now
        ))

        # -------------------------------------------------------------
        # 5. Recovery Absence & Retraction Check
        # -------------------------------------------------------------
        # If person was in a verifying/possible fall state, but then stood back upright within recovery window
        has_recovered = (
            prone_frames_count < 3 and 
            curr_obs.is_upright and 
            curr_obs.torso_angle_deg >= fall_config.TORSO_ANGLE_UPRIGHT_THRESHOLD_DEG and
            was_upright
        )

        if has_recovered and person.fall_state in ["CANDIDATE", "VERIFYING"]:
            ev5_status = EvidenceStatus.CONTRADICTED  # Recovery contradicts the sustained fall
            ev5_conf = 0.95
            ev5_desc = "Person recovered and resumed upright standing posture (Fall Retracted)"
        elif is_currently_prone and prone_frames_count >= fall_config.MIN_PERSISTENCE_FRAMES:
            ev5_status = EvidenceStatus.SUPPORTED
            ev5_conf = 0.85
            ev5_desc = "No recovery motion observed; person remains stationary on ground"
        else:
            ev5_status = EvidenceStatus.UNKNOWN
            ev5_conf = 0.50
            ev5_desc = "Recovery window is currently undergoing temporal observation"

        evidence_list.append(EvidenceObservation(
            evidence_type="recovery_absence",
            description=ev5_desc,
            status=ev5_status.value,
            confidence=float(ev5_conf),
            timestamp=now
        ))

        # -------------------------------------------------------------
        # Lifecycle Resolution & Fall Evidence Score Computation
        # -------------------------------------------------------------
        supported_count = sum(1 for e in evidence_list if e.status == EvidenceStatus.SUPPORTED.value)
        contradicted_count = sum(1 for e in evidence_list if e.status == EvidenceStatus.CONTRADICTED.value)

        # Weight components: velocity (0.25), collapse (0.25), prone orientation (0.25), persistence (0.25)
        evidence_score = 0.0
        weights = {
            "rapid_downward_velocity": 0.25,
            "posture_transition_collapse": 0.25,
            "ground_level_orientation": 0.25,
            "sustained_ground_persistence": 0.25
        }
        for ev in evidence_list:
            if ev.evidence_type in weights:
                if ev.status == EvidenceStatus.SUPPORTED.value:
                    evidence_score += weights[ev.evidence_type] * ev.confidence
                elif ev.status == EvidenceStatus.UNKNOWN.value:
                    evidence_score += weights[ev.evidence_type] * 0.3 * ev.confidence

        # Lifecycle state transitions
        if has_recovered:
            new_status = IncidentStatus.RETRACTED
        elif supported_count >= 4 and prone_frames_count >= fall_config.MIN_PERSISTENCE_FRAMES:
            new_status = IncidentStatus.CONFIRMED
        elif supported_count >= 2 or (ev1_status == EvidenceStatus.SUPPORTED and is_currently_prone):
            new_status = IncidentStatus.VERIFYING
        elif ev1_status == EvidenceStatus.SUPPORTED or is_currently_prone:
            new_status = IncidentStatus.CANDIDATE
        else:
            new_status = IncidentStatus.RETRACTED if person.fall_state == "VERIFYING" else IncidentStatus.CANDIDATE

        return evidence_list, float(round(evidence_score, 3)), new_status
