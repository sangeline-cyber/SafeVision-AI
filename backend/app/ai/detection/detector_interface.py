"""
SafeVision AI - Object and Person Detection Module Interface

STATUS: NOT IMPLEMENTED YET
Pipeline component for YOLO-family person and safety object detection.
"""

from abc import abstractmethod
from typing import List, Optional
import numpy as np
from backend.app.ai.base import BaseAIModule, BoundingBox


class IPersonObjectDetector(BaseAIModule):
    """
    Interface for real-time person and object detection.
    """

    @abstractmethod
    def detect(self, frame: np.ndarray, confidence_threshold: float = 0.5) -> List[BoundingBox]:
        """
        Detects persons and context objects in a raw video frame.

        Args:
            frame: Raw BGR/RGB video frame numpy array
            confidence_threshold: Minimum confidence filter

        Returns:
            List of detected bounding boxes with classifications
        """
        raise NotImplementedError("NOT IMPLEMENTED YET: YOLO detection pipeline will be integrated in Phase 2.")
