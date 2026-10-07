import pytest
import numpy as np
from backend.app.ai.pose.yolo_pose_estimator import PersonPoseObservation
from backend.app.ai.tracking.person_tracker import PersonTracker, TrackedPerson
from backend.app.ai.evidence.fall_evidence_reasoner import FallEvidenceReasoner
from backend.app.models.incident import IncidentStatus
from backend.app.models.evidence import EvidenceStatus


def create_obs(
    torso_angle: float,
    w_h_ratio: float,
    cx: float = 0.5,
    cy: float = 0.5,
    is_upright: bool = True,
    is_prone: bool = False
) -> PersonPoseObservation:
    kpts = np.zeros((17, 3))
    kpts[5] = [cx * 640 - 20, (cy - 0.2) * 480, 0.9]
    kpts[6] = [cx * 640 + 20, (cy - 0.2) * 480, 0.9]
    kpts[11] = [cx * 640 - 15, (cy + 0.1) * 480, 0.9]
    kpts[12] = [cx * 640 + 15, (cy + 0.1) * 480, 0.9]

    return PersonPoseObservation(
        bbox=(100, 100, 200, 300),
        normalized_bbox=(0.2, 0.2, 0.4, 0.6),
        confidence=0.95,
        keypoints=kpts,
        torso_angle_deg=torso_angle,
        aspect_ratio_w_h=w_h_ratio,
        aspect_ratio_h_w=1.0 / max(0.01, w_h_ratio),
        centroid=(cx, cy),
        is_upright=is_upright,
        is_prone=is_prone
    )


def test_slow_sitting_down_does_not_trigger_fall():
    """
    Ensures that an intentional slow sitting action (no sudden downward velocity)
    does NOT trigger a CONFIRMED fall alert.
    """
    reasoner = FallEvidenceReasoner()
    tracker = PersonTracker()

    # Person slowly lowers over 75 frames (2.5 seconds, smooth gradual drift ~0.08 delta Y/s)
    for frame_idx in range(1, 75):
        prog = frame_idx / 75.0
        cy = 0.3 + 0.2 * prog  # Gentle downward drift (total 0.2 over 2.5s = 0.08 / s)
        angle = 85.0 - 25.0 * prog  # 85 deg down to 60 deg (seated posture)
        ratio = 0.5 + 0.2 * prog
        obs = create_obs(
            torso_angle=angle,
            w_h_ratio=ratio,
            cx=0.5,
            cy=cy,
            is_upright=(angle > 55.0),
            is_prone=False
        )
        tracker.update([obs], frame_idx, timestamp_sec=frame_idx / 30.0)

    person = tracker.active_tracks[1]
    ev_list, score, status = reasoner.evaluate_person_evidence(person, 74, 74 / 30.0)

    # Status must NOT be confirmed because velocity spike is absent
    assert status != IncidentStatus.CONFIRMED
    vel_ev = next(e for e in ev_list if e.evidence_type == "rapid_downward_velocity")
    assert vel_ev.status != EvidenceStatus.SUPPORTED.value


def test_evidence_checklist_items_populated():
    """
    Verifies that all 5 structured evidence signals are evaluated and populated.
    """
    reasoner = FallEvidenceReasoner()
    tracker = PersonTracker()

    # Normal upright person
    for i in range(1, 10):
        obs = create_obs(torso_angle=85.0, w_h_ratio=0.5, cx=0.5, cy=0.3)
        tracker.update([obs], i, timestamp_sec=i / 30.0)

    person = tracker.active_tracks[1]
    ev_list, score, status = reasoner.evaluate_person_evidence(person, 9, 9 / 30.0)

    assert len(ev_list) == 5
    evidence_names = [e.evidence_type for e in ev_list]
    assert "rapid_downward_velocity" in evidence_names
    assert "posture_transition_collapse" in evidence_names
    assert "ground_level_orientation" in evidence_names
    assert "sustained_ground_persistence" in evidence_names
    assert "recovery_absence" in evidence_names
