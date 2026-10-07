"""
SafeVision AI - Fall Detection & Temporal Verification Configuration

This module centralizes all kinematic, pose, temporal, and confidence thresholds
for the real-time Fall Detection and Evidence Verification Engine.
"""

from pydantic import BaseModel, Field


class FallDetectionConfig(BaseModel):
    """
    Configuration parameters for human pose analysis and multi-frame fall verification.
    """

    # --- Pose & Detection Confidence ---
    MODEL_NAME: str = Field(
        default="yolo11n-pose.pt",
        description="Pretrained YOLO pose model artifact name (e.g. yolo11n-pose.pt or yolov8n-pose.pt)"
    )
    PERSON_DETECTION_CONFIDENCE: float = Field(
        default=0.40,
        ge=0.1,
        le=1.0,
        description="Minimum bounding box detection confidence for person class"
    )
    KEYPOINT_CONFIDENCE_THRESHOLD: float = Field(
        default=0.30,
        ge=0.1,
        le=1.0,
        description="Minimum confidence required for keypoint estimation"
    )

    # --- Kinematic & Orientation Thresholds ---
    TORSO_ANGLE_HORIZONTAL_THRESHOLD_DEG: float = Field(
        default=45.0,
        ge=10.0,
        le=80.0,
        description="Torso angle (relative to horizontal) below which person is considered prone/horizontal"
    )
    TORSO_ANGLE_UPRIGHT_THRESHOLD_DEG: float = Field(
        default=60.0,
        ge=45.0,
        le=90.0,
        description="Torso angle (relative to horizontal) above which person is considered upright"
    )
    ASPECT_RATIO_COLLAPSE_THRESHOLD: float = Field(
        default=1.05,
        ge=0.5,
        le=3.0,
        description="Width-to-Height bounding box ratio (W/H) indicating horizontal posture collapse"
    )
    DOWNWARD_VELOCITY_THRESHOLD: float = Field(
        default=0.20,
        ge=0.01,
        le=2.0,
        description="Minimum vertical descent velocity (normalized box centroid delta Y per second) indicating sudden fall descent"
    )

    # --- Temporal State Machine & Multi-Frame Verification ---
    MIN_PERSISTENCE_FRAMES: int = Field(
        default=8,
        ge=2,
        le=120,
        description="Minimum consecutive frames person must remain in prone/low posture before confirming fall"
    )
    RECOVERY_WINDOW_FRAMES: int = Field(
        default=25,
        ge=5,
        le=200,
        description="Observation window to check whether person recovers (stands back up), triggering RETRACTED state"
    )
    COOLDOWN_FRAMES: int = Field(
        default=40,
        ge=10,
        le=300,
        description="Cooldown period after an incident before generating a new candidate for the same track ID"
    )

    # --- Tracking ---
    MAX_TRACK_DISTANCE: float = Field(
        default=0.45,
        ge=0.05,
        le=1.0,
        description="Maximum normalized centroid distance to associate detections across consecutive frames"
    )


fall_config = FallDetectionConfig()
