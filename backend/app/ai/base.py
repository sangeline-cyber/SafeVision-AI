"""
SafeVision AI - Base Module Interfaces and Data Structures

STATUS: FOUNDATION PLACEHOLDER INTERFACES (NOT IMPLEMENTED YET)
This module defines the architectural contracts for computer vision, tracking,
pose estimation, behavior analysis, and multi-frame 3-state evidence reasoning.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import numpy as np


@dataclass
class BoundingBox:
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    confidence: float
    class_id: int
    class_name: str


@dataclass
class Keypoint:
    x: float
    y: float
    confidence: float
    name: str


@dataclass
class PoseSkeleton:
    keypoints: Dict[str, Keypoint]
    box: BoundingBox
    confidence: float


@dataclass
class TrackedObject:
    track_id: int
    camera_id: int
    bbox: BoundingBox
    first_seen: datetime
    last_seen: datetime
    history_trajectory: List[Tuple[float, float, datetime]] = field(default_factory=list)
    pose: Optional[PoseSkeleton] = None
    velocity_vector: Tuple[float, float] = (0.0, 0.0)


@dataclass
class EvidenceObservation:
    evidence_type: str
    description: str
    status: str  # "SUPPORTED", "CONTRADICTED", "UNKNOWN"
    confidence: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAIModule(ABC):
    """
    Abstract Base Class for all AI and Computer Vision pipeline components.
    """
    @abstractmethod
    def initialize(self, model_path: Optional[str] = None) -> None:
        """Loads and initializes model artifacts."""
        raise NotImplementedError("NOT IMPLEMENTED YET: Real AI model loading scheduled for subsequent phase.")

    @abstractmethod
    def is_ready(self) -> bool:
        """Returns whether the model is loaded and ready for inference."""
        return False
