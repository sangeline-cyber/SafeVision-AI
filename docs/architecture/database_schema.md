# SafeVision AI - Database Architecture & Schema

SafeVision AI uses PostgreSQL for metadata, entity tracking histories, incident lifecycles, structured evidence records, and alert distribution. Raw video files and binary clips are persisted in storage volumes.

## Relational Entity-Relationship Summary

```mermaid
erDiagram
    USERS {
        int user_id PK
        string name
        string email UK
        string password_hash
        string role
        datetime created_at
    }

    CAMERAS ||--o{ ZONES : contains
    CAMERAS ||--o{ TRACKED_ENTITIES : detects
    CAMERAS ||--o{ INCIDENTS : captures

    CAMERAS {
        int camera_id PK
        string camera_name
        string location
        string stream_url
        string status
        datetime created_at
    }

    ZONES {
        int zone_id PK
        int camera_id FK
        string zone_name
        string zone_type
        json polygon_coordinates
        string risk_level
    }

    TRACKED_ENTITIES ||--o{ INCIDENTS : involves
    TRACKED_ENTITIES {
        int entity_id PK
        int camera_id FK
        int track_id
        datetime first_seen
        datetime last_seen
    }

    INCIDENTS ||--o{ EVIDENCE : substantiates
    INCIDENTS ||--o{ ALERTS : triggers
    INCIDENTS {
        int incident_id PK
        int camera_id FK
        string event_type
        int entity_id FK
        datetime start_time
        datetime end_time
        string status
        float confidence
        string risk_level
    }

    EVIDENCE {
        int evidence_id PK
        int incident_id FK
        string evidence_type
        text description
        string status
        float confidence
        datetime timestamp
    }

    ALERTS {
        int alert_id PK
        int incident_id FK
        string severity
        text message
        datetime created_at
        boolean acknowledged
    }

    EVENT_RULES {
        int rule_id PK
        string event_type UK
        json required_evidence
        float threshold
        float verification_duration
    }
```

## Enums and Constraints
- **Incident Status**: `CANDIDATE`, `VERIFYING`, `CONFIRMED`, `RETRACTED`
- **Evidence Status**: `SUPPORTED`, `CONTRADICTED`, `UNKNOWN`
- **User Roles**: `admin`, `operator`, `analyst`, `viewer`
- **Camera Status**: `active`, `inactive`, `error`, `maintenance`
- **Zone Types**: `restricted`, `hazard`, `monitored`, `entry_exit`, `crowd_watch`
- **Risk Levels / Severities**: `low`, `medium`, `high`, `critical`
