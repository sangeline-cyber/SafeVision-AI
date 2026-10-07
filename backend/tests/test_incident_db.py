import pytest
from datetime import datetime, timezone
from backend.app.models.camera import Camera
from backend.app.models.incident import Incident, EventType, IncidentStatus, IncidentRiskLevel
from backend.app.models.evidence import Evidence, EvidenceStatus
from backend.app.models.entity import TrackedEntity


def test_database_incident_and_evidence_creation(db_session):
    """
    Verifies creating real Camera, TrackedEntity, Incident, and Evidence records in PostgreSQL.
    """
    db = db_session
    # 1. Create Camera
    camera = Camera(
        camera_name="Lobby Entrance Cam 01",
        stream_url="rtsp://192.168.1.100/stream1",
        location="Main Lobby Reception Area"
    )
    db.add(camera)
    db.flush()

    assert camera.camera_id is not None

    # 2. Create TrackedEntity
    entity = TrackedEntity(
        camera_id=camera.camera_id,
        track_id=101,
        first_seen=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc)
    )
    db.add(entity)
    db.flush()

    assert entity.entity_id is not None

    # 3. Create Incident
    incident = Incident(
        camera_id=camera.camera_id,
        event_type=EventType.FALL,
        status=IncidentStatus.CONFIRMED,
        risk_level=IncidentRiskLevel.HIGH,
        confidence=0.88,
        entity_id=entity.entity_id,
        start_time=datetime.now(timezone.utc)
    )
    db.add(incident)
    db.flush()

    assert incident.incident_id is not None
    assert incident.status == IncidentStatus.CONFIRMED

    # 4. Create Evidence record
    evidence = Evidence(
        incident_id=incident.incident_id,
        evidence_type="rapid_downward_velocity",
        description="Downward velocity spike of 0.28 normalized/sec exceeding threshold.",
        status=EvidenceStatus.SUPPORTED,
        confidence=0.92,
        timestamp=datetime.now(timezone.utc)
    )
    db.add(evidence)
    db.commit()

    # Query back from DB
    saved_incident = db.query(Incident).filter(Incident.incident_id == incident.incident_id).first()
    assert saved_incident is not None
    assert len(saved_incident.evidence_items) == 1
    assert saved_incident.evidence_items[0].status == EvidenceStatus.SUPPORTED
    assert saved_incident.evidence_items[0].evidence_type == "rapid_downward_velocity"
