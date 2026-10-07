import pytest
import numpy as np
from backend.app.ai.pose.yolo_pose_estimator import PersonPoseObservation
from backend.app.ai.tracking.person_tracker import PersonTracker, TrackedPerson
from backend.app.ai.evidence.fall_evidence_reasoner import FallEvidenceReasoner
from backend.app.models.incident import IncidentStatus
from backend.app.models.evidence import EvidenceStatus


def create_mock_obs(
    torso_angle: float,
    w_h_ratio: float,
    cx: float = 0.5,
    cy: float = 0.5,
    is_upright: bool = True,
    is_prone: bool = False
) -> PersonPoseObservation:
    """Helper to create deterministic mock pose observations for unit testing."""
    kpts = np.zeros((17, 3))
    # Shoulders at (0.5, cy - 0.2)
    kpts[5] = [cx * 640 - 20, (cy - 0.2) * 480, 0.9]
    kpts[6] = [cx * 640 + 20, (cy - 0.2) * 480, 0.9]
    # Hips at (0.5, cy + 0.1)
    kpts[11] = [cx * 640 - 15, (cy + 0.1) * 480, 0.9]
    kpts[12] = [cx * 640 + 15, (cy + 0.1) * 480, 0.9]

    return PersonPoseObservation(
        bbox=(100, 100, 200, 300),
        normalized_bbox=(0.2, 0.2, 0.4, 0.6),
        confidence=0.92,
        keypoints=kpts,
        torso_angle_deg=torso_angle,
        aspect_ratio_w_h=w_h_ratio,
        aspect_ratio_h_w=1.0 / max(0.01, w_h_ratio),
        centroid=(cx, cy),
        is_upright=is_upright,
        is_prone=is_prone
    )


def test_fall_state_transition_normal_to_confirmed():
    """
    Tests the complete fall detection transition:
    UPRIGHT (Normal) -> RAPID DESCENT -> PRONE COLLAPSE -> SUSTAINED GROUND -> CONFIRMED
    """
    reasoner = FallEvidenceReasoner()
    tracker = PersonTracker()

    # Step 1: Upright standing frames (Normal baseline)
    for frame_idx in range(1, 10):
        obs = create_mock_obs(torso_angle=85.0, w_h_ratio=0.5, cx=0.5, cy=0.3, is_upright=True, is_prone=False)
        tracker.update([obs], frame_idx, timestamp_sec=frame_idx / 30.0)

    person = tracker.active_tracks[1]
    ev_list, score, status = reasoner.evaluate_person_evidence(person, 10, 10 / 30.0)
    assert status in [IncidentStatus.CANDIDATE, IncidentStatus.RETRACTED]

    # Step 2: Rapid downward motion spike
    obs_falling = create_mock_obs(torso_angle=55.0, w_h_ratio=0.9, cx=0.5, cy=0.6, is_upright=False, is_prone=False)
    tracker.update([obs_falling], 11, timestamp_sec=11 / 30.0)

    # Step 3: Person on ground prone for consecutive frames
    for frame_idx in range(12, 25):
        obs_prone = create_mock_obs(torso_angle=20.0, w_h_ratio=1.6, cx=0.5, cy=0.75, is_upright=False, is_prone=True)
        tracker.update([obs_prone], frame_idx, timestamp_sec=frame_idx / 30.0)

    ev_list, score, final_status = reasoner.evaluate_person_evidence(person, 24, 24 / 30.0)

    # Check evidence statuses
    supported_types = {e.evidence_type for e in ev_list if e.status == EvidenceStatus.SUPPORTED.value}
    assert "rapid_downward_velocity" in supported_types
    assert "posture_transition_collapse" in supported_types
    assert "ground_level_orientation" in supported_types
    assert "sustained_ground_persistence" in supported_types
    assert final_status == IncidentStatus.CONFIRMED
    assert score >= 0.70


def test_fall_retraction_on_person_recovery():
    """
    Tests reversible lifecycle:
    Possible fall detected -> Person stands back up -> Incident marked RETRACTED
    """
    reasoner = FallEvidenceReasoner()
    tracker = PersonTracker()

    # Step 1: Initial upright frames
    for frame_idx in range(1, 6):
        obs = create_mock_obs(torso_angle=85.0, w_h_ratio=0.5, cx=0.5, cy=0.3, is_upright=True, is_prone=False)
        tracker.update([obs], frame_idx, timestamp_sec=frame_idx / 30.0)

    # Step 2: Momentary trip / kneel (2 frames prone)
    for frame_idx in range(6, 8):
        obs_trip = create_mock_obs(torso_angle=35.0, w_h_ratio=1.2, cx=0.5, cy=0.6, is_upright=False, is_prone=True)
        tracker.update([obs_trip], frame_idx, timestamp_sec=frame_idx / 30.0)

    person = tracker.active_tracks[1]
    person.fall_state = "VERIFYING"  # Candidate under verification

    # Step 3: Person immediately stands back upright (Recovery)
    obs_recovered = create_mock_obs(torso_angle=88.0, w_h_ratio=0.45, cx=0.5, cy=0.35, is_upright=True, is_prone=False)
    tracker.update([obs_recovered], 9, timestamp_sec=9 / 30.0)

    ev_list, score, final_status = reasoner.evaluate_person_evidence(person, 9, 9 / 30.0)

    # Must be RETRACTED to prevent false alarm
    assert final_status == IncidentStatus.RETRACTED
    recovery_ev = next(e for e in ev_list if e.evidence_type == "recovery_absence")
    assert recovery_ev.status == EvidenceStatus.CONTRADICTED.value
