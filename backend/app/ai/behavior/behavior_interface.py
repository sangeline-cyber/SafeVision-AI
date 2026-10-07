"""
SafeVision AI - Behavior and Action Recognition Module Interface

STATUS: NOT IMPLEMENTED YET
Pipeline component for spatio-temporal action recognition, interaction energy measurement,
and crowd density estimation.
"""

from abc import abstractmethod
from typing import List, Dict, Any
import numpy as np
from backend.app.ai.base import BaseAIModule, TrackedObject


class IBehaviorAnalyzer(BaseAIModule):
    """
    Interface for spatio-temporal safety behavior analysis.
    """

    @abstractmethod
    def analyze_interaction(self, entities: List[TrackedObject], frame_window: List[np.ndarray]) -> Dict[str, Any]:
        """
        Analyzes multi-entity interactions (e.g., fight kinetic energy, crowd density flux).

        Args:
            entities: Active tracked entities in the frame window
            frame_window: Sliding buffer of recent video frames

        Returns:
            Dictionary of computed behavior metrics (energy score, density count, proximity index)
        """
        raise NotImplementedError("NOT IMPLEMENTED YET: Behavior recognition module will be integrated in Phase 2.")
