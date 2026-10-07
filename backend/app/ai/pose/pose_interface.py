"""
SafeVision AI - Pose Estimation Module Interface

STATUS: NOT IMPLEMENTED YET
Pipeline component for YOLO-Pose / MediaPipe anatomical keypoint extraction
for fall detection posture transitions and ground-level orientation estimation.
"""

from abc import abstractmethod
from typing import List, Optional
import numpy as np
from backend.app.ai.base import BaseAIModule, PoseSkeleton, TrackedObject


class IPoseEstimator(BaseAIModule):
    """
    Interface for human pose keypoint estimation.
    """

    @abstractmethod
    def estimate_pose(self, frame: np.ndarray, entity: TrackedObject) -> Optional[PoseSkeleton]:
        """
        Extracts anatomical keypoints (head, shoulders, hips, knees, ankles) for a tracked entity.

        Args:
            frame: Video frame numpy array
            entity: Tracked person entity

        Returns:
            PoseSkeleton or None if person is obscured
        """
        raise NotImplementedError("NOT IMPLEMENTED YET: Pose estimation model will be integrated in Phase 2.")
