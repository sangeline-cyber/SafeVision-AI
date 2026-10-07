"""Initial schema for SafeVision AI

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-10-07 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        'users',
        sa.Column('user_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='operator'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('user_id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_user_id'), 'users', ['user_id'], unique=False)

    # 2. cameras table
    op.create_table(
        'cameras',
        sa.Column('camera_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('camera_name', sa.String(length=255), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=False),
        sa.Column('stream_url', sa.String(length=1024), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('camera_id')
    )
    op.create_index(op.f('ix_cameras_camera_id'), 'cameras', ['camera_id'], unique=False)
    op.create_index(op.f('ix_cameras_camera_name'), 'cameras', ['camera_name'], unique=False)

    # 3. zones table
    op.create_table(
        'zones',
        sa.Column('zone_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('camera_id', sa.Integer(), nullable=False),
        sa.Column('zone_name', sa.String(length=255), nullable=False),
        sa.Column('zone_type', sa.String(length=50), nullable=False, server_default='restricted'),
        sa.Column('polygon_coordinates', sa.JSON(), nullable=False),
        sa.Column('risk_level', sa.String(length=50), nullable=False, server_default='high'),
        sa.ForeignKeyConstraint(['camera_id'], ['cameras.camera_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('zone_id')
    )
    op.create_index(op.f('ix_zones_camera_id'), 'zones', ['camera_id'], unique=False)
    op.create_index(op.f('ix_zones_zone_id'), 'zones', ['zone_id'], unique=False)

    # 4. tracked_entities table
    op.create_table(
        'tracked_entities',
        sa.Column('entity_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('camera_id', sa.Integer(), nullable=False),
        sa.Column('track_id', sa.Integer(), nullable=False),
        sa.Column('first_seen', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_seen', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['camera_id'], ['cameras.camera_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('entity_id')
    )
    op.create_index(op.f('ix_tracked_entities_camera_id'), 'tracked_entities', ['camera_id'], unique=False)
    op.create_index(op.f('ix_tracked_entities_entity_id'), 'tracked_entities', ['entity_id'], unique=False)
    op.create_index(op.f('ix_tracked_entities_track_id'), 'tracked_entities', ['track_id'], unique=False)

    # 5. incidents table
    op.create_table(
        'incidents',
        sa.Column('incident_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('camera_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='CANDIDATE'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('risk_level', sa.String(length=50), nullable=False, server_default='medium'),
        sa.ForeignKeyConstraint(['camera_id'], ['cameras.camera_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['entity_id'], ['tracked_entities.entity_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('incident_id')
    )
    op.create_index(op.f('ix_incidents_camera_id'), 'incidents', ['camera_id'], unique=False)
    op.create_index(op.f('ix_incidents_entity_id'), 'incidents', ['entity_id'], unique=False)
    op.create_index(op.f('ix_incidents_event_type'), 'incidents', ['event_type'], unique=False)
    op.create_index(op.f('ix_incidents_incident_id'), 'incidents', ['incident_id'], unique=False)
    op.create_index(op.f('ix_incidents_start_time'), 'incidents', ['start_time'], unique=False)
    op.create_index(op.f('ix_incidents_status'), 'incidents', ['status'], unique=False)

    # 6. evidence table
    op.create_table(
        'evidence',
        sa.Column('evidence_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('incident_id', sa.Integer(), nullable=False),
        sa.Column('evidence_type', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='UNKNOWN'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.incident_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('evidence_id')
    )
    op.create_index(op.f('ix_evidence_evidence_id'), 'evidence', ['evidence_id'], unique=False)
    op.create_index(op.f('ix_evidence_evidence_type'), 'evidence', ['evidence_type'], unique=False)
    op.create_index(op.f('ix_evidence_incident_id'), 'evidence', ['incident_id'], unique=False)
    op.create_index(op.f('ix_evidence_status'), 'evidence', ['status'], unique=False)

    # 7. alerts table
    op.create_table(
        'alerts',
        sa.Column('alert_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('incident_id', sa.Integer(), nullable=False),
        sa.Column('severity', sa.String(length=50), nullable=False, server_default='high'),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('acknowledged', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.incident_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('alert_id')
    )
    op.create_index(op.f('ix_alerts_acknowledged'), 'alerts', ['acknowledged'], unique=False)
    op.create_index(op.f('ix_alerts_alert_id'), 'alerts', ['alert_id'], unique=False)
    op.create_index(op.f('ix_alerts_incident_id'), 'alerts', ['incident_id'], unique=False)
    op.create_index(op.f('ix_alerts_severity'), 'alerts', ['severity'], unique=False)

    # 8. event_rules table
    op.create_table(
        'event_rules',
        sa.Column('rule_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('required_evidence', sa.JSON(), nullable=False),
        sa.Column('threshold', sa.Float(), nullable=False, server_default='0.75'),
        sa.Column('verification_duration', sa.Float(), nullable=False, server_default='3.0'),
        sa.PrimaryKeyConstraint('rule_id')
    )
    op.create_index(op.f('ix_event_rules_event_type'), 'event_rules', ['event_type'], unique=True)
    op.create_index(op.f('ix_event_rules_rule_id'), 'event_rules', ['rule_id'], unique=False)


def downgrade() -> None:
    op.drop_table('event_rules')
    op.drop_table('alerts')
    op.drop_table('evidence')
    op.drop_table('incidents')
    op.drop_table('tracked_entities')
    op.drop_table('zones')
    op.drop_table('cameras')
    op.drop_table('users')
