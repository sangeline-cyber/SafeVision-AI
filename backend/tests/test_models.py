from datetime import datetime, timezone
from backend.app.models.user import User, UserRole
from backend.app.models.camera import Camera, CameraStatus
from backend.app.models.zone import Zone, ZoneType, RiskLevel
from backend.app.models.entity import TrackedEntity
from backend.app.models.incident import Incident, IncidentStatus, EventType, IncidentRiskLevel
from backend.app.models.evidence import Evidence, EvidenceStatus
from backend.app.models.alert import Alert, AlertSeverity
from backend.app.models.event_rule import EventRule
from backend.app.core.security import get_password_hash, verify_password


def test_user_model_and_hashing(db_session):
    """
    Tests creating a User model, hashing password, and database persistence.
    """
    raw_password = "SecurePassword2026!"
    hashed = get_password_hash(raw_password)
    assert verify_password(raw_password, hashed)

    user = User(
        name="Security Lead",
        email="lead@safevision.ai",
        password_hash=hashed,
        role=UserRole.ADMIN
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.user_id is not None
    assert user.email == "lead@safevision.ai"
    assert user.role == UserRole.ADMIN


def test_camera_zone_and_entity_relationship(db_session):
    """
    Tests Camera, Zone polygon, and TrackedEntity foreign key relationships.
    """
    camera = Camera(
        camera_name="Main Entry Gate 1",
        location="Sector A North Perimeter",
        stream_url="rtsp://192.168.1.100:554/live/ch0",
        status=CameraStatus.ACTIVE
    )
    db_session.add(camera)
    db_session.commit()
    db_session.refresh(camera)

    zone = Zone(
        camera_id=camera.camera_id,
        zone_name="Perimeter Restricted Strip",
        zone_type=ZoneType.RESTRICTED,
        polygon_coordinates=[{"x": 100, "y": 150}, {"x": 400, "y": 150}, {"x": 400, "y": 300}, {"x": 100, "y": 300}],
        risk_level=RiskLevel.CRITICAL
    )
    entity = TrackedEntity(
        camera_id=camera.camera_id,
        track_id=101
    )
    db_session.add_all([zone, entity])
    db_session.commit()
    db_session.refresh(zone)
    db_session.refresh(entity)

    assert zone.zone_id is not None
    assert entity.entity_id is not None
    assert len(camera.zones) == 1
    assert len(camera.entities) == 1


def test_incident_and_three_state_evidence(db_session):
    """
    Tests Incident reversible lifecycle and 3-State Evidence creation.
    """
    camera = Camera(
        camera_name="Warehouse Floor Camera",
        location="Logistics Hub Bay 3",
        stream_url="rtsp://192.168.1.105:554/live/ch0",
        status=CameraStatus.ACTIVE
    )
    db_session.add(camera)
    db_session.commit()

    incident = Incident(
        camera_id=camera.camera_id,
        event_type=EventType.FALL,
        status=IncidentStatus.VERIFYING,
        confidence=0.82,
        risk_level=IncidentRiskLevel.HIGH
    )
    db_session.add(incident)
    db_session.commit()
    db_session.refresh(incident)

    # 3-State Evidence entries
    ev1 = Evidence(
        incident_id=incident.incident_id,
        evidence_type="downward_velocity",
        description="Rapid descent velocity detected across 12 frames",
        status=EvidenceStatus.SUPPORTED,
        confidence=0.89
    )
    ev2 = Evidence(
        incident_id=incident.incident_id,
        evidence_type="posture_horizontal",
        description="Subject body axis horizontal relative to ground floor",
        status=EvidenceStatus.SUPPORTED,
        confidence=0.91
    )
    ev3 = Evidence(
        incident_id=incident.incident_id,
        evidence_type="recovery_check",
        description="Partial occlusion by pallet rack, head keypoint obscured",
        status=EvidenceStatus.UNKNOWN,
        confidence=0.0
    )
    db_session.add_all([ev1, ev2, ev3])
    db_session.commit()

    # Verify incident and evidence items
    db_session.refresh(incident)
    assert len(incident.evidence_items) == 3
    assert any(e.status == EvidenceStatus.UNKNOWN for e in incident.evidence_items)
    assert any(e.status == EvidenceStatus.SUPPORTED for e in incident.evidence_items)

    # Transition incident status to CONFIRMED
    incident.status = IncidentStatus.CONFIRMED
    alert = Alert(
        incident_id=incident.incident_id,
        severity=AlertSeverity.CRITICAL,
        message="Confirmed Fall Incident detected in Bay 3 with sustained ground orientation.",
        acknowledged=False
    )
    db_session.add(alert)
    db_session.commit()
    db_session.refresh(alert)

    assert alert.alert_id is not None
    assert incident.status == IncidentStatus.CONFIRMED


def test_event_rule_model(db_session):
    """
    Tests EventRule model creation and storage of required evidence schema.
    """
    rule = EventRule(
        event_type=EventType.FALL,
        required_evidence={
            "schema_version": "1.0",
            "items": ["person_detected", "downward_movement", "posture_transition", "ground_level", "persistence", "recovery_check"],
            "min_supported_count": 5
        },
        threshold=0.80,
        verification_duration=3.5
    )
    db_session.add(rule)
    db_session.commit()
    db_session.refresh(rule)

    assert rule.rule_id is not None
    assert rule.event_type == EventType.FALL
    assert rule.required_evidence["min_supported_count"] == 5
