# SafeVision AI - REST API Specification

## Base URL
- Development: `http://localhost:8000/api`

---

## 1. System Health Endpoints

### System Health Check
`GET /api/health`

**Description**: Returns operational health status of SafeVision AI backend.

**Response**: `200 OK`
```json
{
  "status": "ok",
  "service": "SafeVision AI"
}
```

---

### Database Health Check
`GET /api/health/database`

**Description**: Executes a live `SELECT 1` ping query against PostgreSQL via SQLAlchemy connection pool.

**Response (Connected)**: `200 OK`
```json
{
  "status": "connected",
  "database": "postgresql",
  "connected": true,
  "server": "localhost",
  "database_name": "safevision_db",
  "ping": true
}
```

---

## 2. Video Processing & Fall Detection Endpoints

### Upload Surveillance Video
`POST /api/v1/videos/upload`

**Description**: Accepts a real video file (MP4, AVI, MOV, WebM up to 500MB) via `multipart/form-data`. Saves to `storage/videos/` and registers processing job.

**Response**: `201 Created`
```json
{
  "video_id": "8f3b2a1c9e0d",
  "filename": "surveillance_hallway.mp4",
  "file_size_bytes": 14205830,
  "video_url": "/api/v1/videos/8f3b2a1c9e0d/stream",
  "uploaded_at": "2026-10-07T12:00:00Z"
}
```

---

### Process Video with YOLO Pose & Evidence Reasoner
`POST /api/v1/videos/{video_id}/process`

**Description**: Runs real frame-by-frame inference, tracks persons, calculates torso angles and descent velocities, verifies fall evidence over multiple frames, generates annotated snapshot images, and persists confirmed incidents into PostgreSQL.

**Response**: `200 OK`
```json
{
  "video_id": "8f3b2a1c9e0d",
  "filename": "surveillance_hallway.mp4",
  "total_frames": 360,
  "fps": 30.0,
  "duration_sec": 12.0,
  "processed_at": "2026-10-07T12:00:15Z",
  "incidents": [
    {
      "incident_id": 1,
      "event_type": "fall",
      "track_id": 1,
      "timestamp_sec": 7.42,
      "timestamp_formatted": "00:07.42",
      "status": "CONFIRMED",
      "confidence": 0.89,
      "risk_level": "critical",
      "evidence_frame_url": "/api/v1/evidence/evidence_fall_track1_frame222.jpg",
      "evidence_items": [
        {
          "evidence_type": "rapid_downward_velocity",
          "description": "Downward vertical velocity spike detected (0.14 delta Y/s)",
          "status": "SUPPORTED",
          "confidence": 0.92,
          "timestamp_sec": 7.42
        },
        {
          "evidence_type": "posture_transition_collapse",
          "description": "Observed rapid posture collapse from upright to prone (18.4° torso angle)",
          "status": "SUPPORTED",
          "confidence": 0.90,
          "timestamp_sec": 7.42
        },
        {
          "evidence_type": "ground_level_orientation",
          "description": "Subject body axis is horizontal (torso: 18.4°, W/H: 1.55)",
          "status": "SUPPORTED",
          "confidence": 0.92,
          "timestamp_sec": 7.42
        },
        {
          "evidence_type": "sustained_ground_persistence",
          "description": "Person remained prone for 12 consecutive frames",
          "status": "SUPPORTED",
          "confidence": 0.88,
          "timestamp_sec": 7.42
        },
        {
          "evidence_type": "recovery_absence",
          "description": "No recovery motion observed; person remains stationary on ground",
          "status": "SUPPORTED",
          "confidence": 0.85,
          "timestamp_sec": 7.42
        }
      ]
    }
  ],
  "summary": {
    "total_incidents": 1,
    "confirmed_falls": 1,
    "retracted_events": 0,
    "processing_time_sec": 4.12,
    "model": "YOLO Pose Pretrained",
    "reasoning_engine": "SafeVision 3-State Temporal Evidence Reasoner"
  }
}
```

---

### Stream Uploaded Video
`GET /api/v1/videos/{video_id}/stream`

**Description**: Streams uploaded video file with Range support for HTML5 video element and seeking.

---

### Get Evidence Snapshot Frame
`GET /api/v1/evidence/{filename}`

**Description**: Serves annotated high-resolution evidence snapshot images with HUD, bounding box, and pose skeleton overlays.

---

### Query Incident by ID from PostgreSQL
`GET /api/v1/incidents/{incident_id}`

**Description**: Fetches incident record and associated 3-state evidence rows from PostgreSQL.
