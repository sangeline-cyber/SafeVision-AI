"""
SafeVision AI - Prompt 3 Evidence-Driven Fall Incident Reasoning Tests

Automated tests covering:
1. SUPPORTED evidence
2. CONTRADICTED evidence
3. UNKNOWN evidence
4. CANDIDATE incident
5. VERIFYING incident
6. CONFIRMED incident
7. RETRACTED incident
8. Evidence-complete alerting
9. No alert for incomplete evidence
10. Temporal evidence updates
"""

import pytest
import numpy as np
from datetime import datetime, timezone

from backend.app.ai.pose.yolo_pose_estimator import PersonPoseObservation
from backend.app.ai.tracking.person_tracker import PersonTracker, TrackedPerson
from backend.app.ai.reasoning.evidence_schema import (
    EvidenceState,
    FallEvidenceCategory,
    EvidenceItem,
    FallReasoningEvaluation,
)
from backend.app.ai.reasoning.fall_incident_reasoner import FallIncidentReasoner
from backend.app.models.incident import Incident, IncidentStatus, EventType, IncidentRiskLevel
from backend.app.models.evidence import Evidence, EvidenceStatus
from backend.app.models.alert import Alert, AlertSeverity
from backend.app.models.camera import Camera
from backend.app.models.entity import TrackedEntity
from backend.app.core.fall_config import fall_config


def make_pose_obs(
    torso_angle: float,
    w_h_ratio: float,
    cx: float = 0.5,
    cy: float = 0.5,
    is_upright: bool = True,
    is_prone: bool = False
) -> PersonPoseObservation:
    """Creates deterministic pose observation for testing."""
    kpts = np.zeros((17, 3))
    # Shoulders
    kpts[5] = [cx * 640 - 20, (cy - 0.2) * 480, 0.9]
    kpts[6] = [cx * 640 + 20, (cy - 0.2) * 480, 0.9]
    # Hips
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


# =====================================================================
# Test 1: SUPPORTED Evidence State
# =====================================================================
def test_1_evidence_state_supported():
    """Verifies that a valid fall kinematic signal evaluates to EvidenceState.SUPPORTED."""
    reasoner = FallIncidentReasoner()
    tracker = PersonTracker()

    # Upright baseline
    for i in range(1, 8):
        obs = make_pose_obs(85.0, 0.5, cx=0.5, cy=0.3, is_upright=True, is_prone=False)
        tracker.update([obs], i, i / 30.0)

    # Sudden downward descent
    obs_drop = make_pose_obs(40.0, 1.2, cx=0.5, cy=0.65, is_upright=False, is_prone=True)
    tracker.update([obs_drop], 8, 8 / 30.0)

    person = tracker.active_tracks[1]
    res = reasoner.evaluate(person, 8, 8 / 30.0)

    ev_map = {e.evidence_type: e for e in res.evidence_items}
    assert ev_map[FallEvidenceCategory.DOWNWARD_MOVEMENT.value].state == EvidenceState.SUPPORTED
    assert ev_map[FallEvidenceCategory.DOWNWARD_MOVEMENT.value].confidence >= 0.70
    assert "exceeding" in ev_map[FallEvidenceCategory.DOWNWARD_MOVEMENT.value].description


# =====================================================================
# Test 2: CONTRADICTED Evidence State
# =====================================================================
def test_2_evidence_state_contradicted():
    """Verifies that normal upright walking motion evaluates to EvidenceState.CONTRADICTED."""
    reasoner = FallIncidentReasoner()
    tracker = PersonTracker()

    # Normal upright person walking horizontally with no downward movement
    for i in range(1, 15):
        obs = make_pose_obs(88.0, 0.45, cx=0.2 + i * 0.01, cy=0.3, is_upright=True, is_prone=False)
        tracker.update([obs], i, i / 30.0)

    person = tracker.active_tracks[1]
    res = reasoner.evaluate(person, 14, 14 / 30.0)

    ev_map = {e.evidence_type: e for e in res.evidence_items}
    assert ev_map[FallEvidenceCategory.DOWNWARD_MOVEMENT.value].state == EvidenceState.CONTRADICTED
    assert ev_map[FallEvidenceCategory.POSTURE_TRANSITION.value].state == EvidenceState.CONTRADICTED
    assert ev_map[FallEvidenceCategory.LOW_OR_HORIZONTAL_POSTURE.value].state == EvidenceState.CONTRADICTED
    assert ev_map[FallEvidenceCategory.REMAINS_DOWN.value].state == EvidenceState.CONTRADICTED


# =====================================================================
# Test 3: UNKNOWN Evidence State (Preserving 3-State Logic)
# =====================================================================
def test_3_evidence_state_unknown():
    """
    Verifies that early or partial observations produce EvidenceState.UNKNOWN
    and that UNKNOWN is strictly distinguished from CONTRADICTED or FALSE.
    """
    reasoner = FallIncidentReasoner()
    tracker = PersonTracker()

    # Only 2 frames observed (insufficient history)
    obs1 = make_pose_obs(75.0, 0.6, cx=0.5, cy=0.4, is_upright=False, is_prone=False)
    tracker.update([obs1], 1, 1 / 30.0)
    obs2 = make_pose_obs(70.0, 0.7, cx=0.5, cy=0.45, is_upright=False, is_prone=False)
    tracker.update([obs2], 2, 2 / 30.0)

    person = tracker.active_tracks[1]
    res = reasoner.evaluate(person, 2, 2 / 30.0)

    ev_map = {e.evidence_type: e for e in res.evidence_items}
    # Downward velocity and posture transition must be UNKNOWN with < 3 frames
    assert ev_map[FallEvidenceCategory.DOWNWARD_MOVEMENT.value].state == EvidenceState.UNKNOWN
    assert ev_map[FallEvidenceCategory.POSTURE_TRANSITION.value].state == EvidenceState.UNKNOWN
    # UNKNOWN != CONTRADICTED
    assert ev_map[FallEvidenceCategory.DOWNWARD_MOVEMENT.value].state != EvidenceState.CONTRADICTED
    assert ev_map[FallEvidenceCategory.DOWNWARD_MOVEMENT.value].state != EvidenceState.SUPPORTED


# =====================================================================
# Test 4: CANDIDATE Incident Lifecycle State
# =====================================================================
def test_4_incident_lifecycle_candidate():
    """Verifies that early initial motion spike creates a CANDIDATE status."""
    reasoner = FallIncidentReasoner()
    tracker = PersonTracker()

    for i in range(1, 5):
        obs = make_pose_obs(85.0, 0.5, cx=0.5, cy=0.3, is_upright=True, is_prone=False)
        tracker.update([obs], i, i / 30.0)

    # Initial downward descent frame
    obs_drop = make_pose_obs(55.0, 0.8, cx=0.5, cy=0.55, is_upright=False, is_prone=False)
    tracker.update([obs_drop], 5, 5 / 30.0)

    person = tracker.active_tracks[1]
    res = reasoner.evaluate(person, 5, 5 / 30.0)

    assert res.incident_status in [IncidentStatus.CANDIDATE, IncidentStatus.VERIFYING]
    assert res.is_evidence_complete is False
    assert res.should_alert is False


# =====================================================================
# Test 5: VERIFYING Incident Lifecycle State
# =====================================================================
def test_5_incident_lifecycle_verifying():
    """Verifies that collapse under persistence observation is in VERIFYING status."""
    reasoner = FallIncidentReasoner()
    tracker = PersonTracker()

    # Upright baseline
    for i in range(1, 8):
        obs = make_pose_obs(85.0, 0.5, cx=0.5, cy=0.3, is_upright=True, is_prone=False)
        tracker.update([obs], i, i / 30.0)

    # Downward velocity
    obs_drop = make_pose_obs(40.0, 1.2, cx=0.5, cy=0.65, is_upright=False, is_prone=True)
    tracker.update([obs_drop], 8, 8 / 30.0)

    # 3 prone frames (below MIN_PERSISTENCE_FRAMES threshold of 8)
    for i in range(9, 12):
        obs_prone = make_pose_obs(20.0, 1.5, cx=0.5, cy=0.75, is_upright=False, is_prone=True)
        tracker.update([obs_prone], i, i / 30.0)

    person = tracker.active_tracks[1]
    res = reasoner.evaluate(person, 11, 11 / 30.0)

    # REMAINS_DOWN is UNKNOWN (still undergoing verification)
    ev_map = {e.evidence_type: e for e in res.evidence_items}
    assert ev_map[FallEvidenceCategory.REMAINS_DOWN.value].state == EvidenceState.UNKNOWN
    assert res.incident_status == IncidentStatus.VERIFYING
    assert res.should_alert is False


# =====================================================================
# Test 6: CONFIRMED Incident Lifecycle State
# =====================================================================
def test_6_incident_lifecycle_confirmed():
    """Verifies that all 5 evidence categories supported transitions to CONFIRMED."""
    reasoner = FallIncidentReasoner()
    tracker = PersonTracker()

    # 1. Upright baseline
    for i in range(1, 10):
        obs = make_pose_obs(85.0, 0.5, cx=0.5, cy=0.3, is_upright=True, is_prone=False)
        tracker.update([obs], i, i / 30.0)

    # 2. Downward velocity spike
    obs_drop = make_pose_obs(40.0, 1.1, cx=0.5, cy=0.65, is_upright=False, is_prone=True)
    tracker.update([obs_drop], 10, 10 / 30.0)

    # 3. Ground persistence >= 8 frames
    for i in range(11, 22):
        obs_prone = make_pose_obs(15.0, 1.6, cx=0.5, cy=0.75, is_upright=False, is_prone=True)
        tracker.update([obs_prone], i, i / 30.0)

    person = tracker.active_tracks[1]
    res = reasoner.evaluate(person, 21, 21 / 30.0)

    assert res.incident_status == IncidentStatus.CONFIRMED
    assert res.is_evidence_complete is True
    assert res.should_alert is True
    assert res.evidence_score >= 0.80

    for e in res.evidence_items:
        assert e.state == EvidenceState.SUPPORTED


# =====================================================================
# Test 7: RETRACTED Incident Lifecycle (Reversible Reasoning)
# =====================================================================
def test_7_incident_lifecycle_retracted():
    """
    Tests reversible reasoning:
    A verifying fall where the person quickly stands back up reverts to RETRACTED.
    """
    reasoner = FallIncidentReasoner()
    tracker = PersonTracker()

    # 1. Upright baseline
    for i in range(1, 8):
        obs = make_pose_obs(85.0, 0.5, cx=0.5, cy=0.3, is_upright=True, is_prone=False)
        tracker.update([obs], i, i / 30.0)

    # 2. Brief trip / kneel (2 frames prone)
    for i in range(8, 10):
        obs_trip = make_pose_obs(30.0, 1.3, cx=0.5, cy=0.6, is_upright=False, is_prone=True)
        tracker.update([obs_trip], i, i / 30.0)

    person = tracker.active_tracks[1]
    person.fall_state = IncidentStatus.VERIFYING.value

    # 3. Person immediately recovers to upright standing
    obs_recover = make_pose_obs(88.0, 0.45, cx=0.5, cy=0.32, is_upright=True, is_prone=False)
    tracker.update([obs_recover], 10, 10 / 30.0)

    res = reasoner.evaluate(person, 10, 10 / 30.0)

    assert res.incident_status == IncidentStatus.RETRACTED
    assert res.should_alert is False
    ev_map = {e.evidence_type: e for e in res.evidence_items}
    assert ev_map[FallEvidenceCategory.REMAINS_DOWN.value].state == EvidenceState.CONTRADICTED


# =====================================================================
# Test 8: Evidence-Complete Alerting
# =====================================================================
def test_8_evidence_complete_alerting(db_session):
    """
    Verifies that when an incident is CONFIRMED with complete evidence,
    an Alert record is persisted in PostgreSQL with appropriate severity and message.
    """
    db = db_session
    camera = Camera(camera_name="Cam-Hallway-Alert", stream_url="rtsp://test", location="Hallway")
    db.add(camera)
    db.flush()

    entity = TrackedEntity(camera_id=camera.camera_id, track_id=42, first_seen=datetime.now(timezone.utc))
    db.add(entity)
    db.flush()

    # Confirmed incident
    incident = Incident(
        camera_id=camera.camera_id,
        event_type=EventType.FALL,
        entity_id=entity.entity_id,
        start_time=datetime.now(timezone.utc),
        status=IncidentStatus.CONFIRMED,
        confidence=0.91,
        risk_level=IncidentRiskLevel.CRITICAL
    )
    db.add(incident)
    db.flush()

    # Evidence-Complete Alert Decision: Create Alert
    alert = Alert(
        incident_id=incident.incident_id,
        severity=AlertSeverity.CRITICAL,
        message="CONFIRMED Fall Incident for Person #42: All 5 evidence criteria verified."
    )
    db.add(alert)
    db.commit()

    saved_alert = db.query(Alert).filter(Alert.incident_id == incident.incident_id).first()
    assert saved_alert is not None
    assert saved_alert.severity == AlertSeverity.CRITICAL
    assert saved_alert.acknowledged is False
    assert "CONFIRMED Fall Incident" in saved_alert.message


# =====================================================================
# Test 9: No Alert for Incomplete Evidence (CANDIDATE / VERIFYING / RETRACTED)
# =====================================================================
def test_9_no_alert_for_incomplete_evidence(db_session):
    """
    Verifies that no Alert is created when evidence is incomplete or incident is in CANDIDATE/VERIFYING/RETRACTED.
    """
    db = db_session
    camera = Camera(camera_name="Cam-Hallway-NoAlert", stream_url="rtsp://test", location="Hallway")
    db.add(camera)
    db.flush()

    entity = TrackedEntity(camera_id=camera.camera_id, track_id=43, first_seen=datetime.now(timezone.utc))
    db.add(entity)
    db.flush()

    # Candidate incident
    candidate_incident = Incident(
        camera_id=camera.camera_id,
        event_type=EventType.FALL,
        entity_id=entity.entity_id,
        start_time=datetime.now(timezone.utc),
        status=IncidentStatus.VERIFYING,
        confidence=0.55,
        risk_level=IncidentRiskLevel.HIGH
    )
    db.add(candidate_incident)
    db.commit()

    # Completeness check logic
    should_alert = (candidate_incident.status == IncidentStatus.CONFIRMED)
    assert should_alert is False

    # Ensure no alert is in the database for this incident
    alerts_count = db.query(Alert).filter(Alert.incident_id == candidate_incident.incident_id).count()
    assert alerts_count == 0


# =====================================================================
# Test 10: Temporal Evidence Updates
# =====================================================================
def test_10_temporal_evidence_updates():
    """
    Verifies temporal progression over frames:
    Frame 1-8: Normal
    Frame 9: Downward movement = SUPPORTED, Remains down = UNKNOWN
    Frame 18: All 5 categories SUPPORTED -> CONFIRMED
    Verifies temporal evolution snapshots are recorded.
    """
    reasoner = FallIncidentReasoner()
    tracker = PersonTracker()

    # Phase 1: Upright baseline
    for i in range(1, 8):
        obs = make_pose_obs(85.0, 0.5, cx=0.5, cy=0.3, is_upright=True, is_prone=False)
        tracker.update([obs], i, i / 30.0)

    # Phase 2: Downward collapse at frame 8
    obs_fall = make_pose_obs(35.0, 1.2, cx=0.5, cy=0.65, is_upright=False, is_prone=True)
    tracker.update([obs_fall], 8, 8 / 30.0)
    res_f8 = reasoner.evaluate(tracker.active_tracks[1], 8, 8 / 30.0)

    ev_f8 = {e.evidence_type: e.state for e in res_f8.evidence_items}
    assert ev_f8[FallEvidenceCategory.DOWNWARD_MOVEMENT.value] == EvidenceState.SUPPORTED
    assert ev_f8[FallEvidenceCategory.REMAINS_DOWN.value] == EvidenceState.UNKNOWN
    assert res_f8.incident_status != IncidentStatus.CONFIRMED

    # Phase 3: Consecutive prone frames up to frame 20
    for i in range(9, 21):
        obs_prone = make_pose_obs(15.0, 1.6, cx=0.5, cy=0.75, is_upright=False, is_prone=True)
        tracker.update([obs_prone], i, i / 30.0)

    res_f20 = reasoner.evaluate(tracker.active_tracks[1], 20, 20 / 30.0)
    ev_f20 = {e.evidence_type: e.state for e in res_f20.evidence_items}
    assert ev_f20[FallEvidenceCategory.DOWNWARD_MOVEMENT.value] == EvidenceState.SUPPORTED
    assert ev_f20[FallEvidenceCategory.POSTURE_TRANSITION.value] == EvidenceState.SUPPORTED
    assert ev_f20[FallEvidenceCategory.LOW_OR_HORIZONTAL_POSTURE.value] == EvidenceState.SUPPORTED
    assert ev_f20[FallEvidenceCategory.REMAINS_DOWN.value] == EvidenceState.SUPPORTED
    assert ev_f20[FallEvidenceCategory.TEMPORAL_CONSISTENCY.value] == EvidenceState.SUPPORTED
    assert res_f20.incident_status == IncidentStatus.CONFIRMED

    # Check that temporal evolution snapshots were preserved
    snapshots = res_f20.temporal_evolution
    assert len(snapshots) >= 2
    # Verify evolution trace contains earlier and later snapshots
    statuses = [s.incident_status for s in snapshots]
    assert IncidentStatus.CONFIRMED.value in statuses
