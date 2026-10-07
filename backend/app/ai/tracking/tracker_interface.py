"""
SafeVision AI - Multi-Object Tracking Module Interface

STATUS: NOT IMPLEMENTED YET
Pipeline component for ByteTrack-based continuous multi-entity association across frames.
"""

from abc import abstractmethod
from typing import List
import numpy as np
from backend.app.ai.base import BaseAIModule, BoundingBox, TrackedObject


class IMultiObjectTracker(BaseAIModule):
    """
    Interface for ByteTrack multi-object tracking across video frames.
    """

    @abstractmethod
    def update(self, frame: np.ndarray, detections: List[BoundingBox], camera_id: int) -> List[TrackedObject]:
        """
        Updates tracked entity associations using current detections.

        Args:
            frame: Video frame numpy array
            detections: Current frame detections from detector
            camera_id: Origin camera ID

        Returns:
            List of updated TrackedObject instances with persistent track IDs
        """
        raise NotImplementedError("NOT IMPLEMENTED YET: ByteTrack tracking pipeline will be integrated in Phase 2.")
