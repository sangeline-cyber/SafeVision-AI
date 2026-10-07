"""
SafeVision AI - Temporal Evidence Lifecycle Tracker

Tracks and preserves the chronological evolution of evidence states across video frames.
Prevents single-frame snap judgements and ensures the full reasoning progression is traceable.
"""

from collections import deque
from typing import Dict, List, Optional
from backend.app.ai.reasoning.evidence_schema import TemporalFrameSnapshot, EvidenceItem


class TemporalEvidenceTracker:
    """
    Maintains the historical evidence evolution for a tracked person.
    """

    def __init__(self, track_id: int, max_snapshots: int = 40):
        self.track_id = track_id
        self.snapshots: deque[TemporalFrameSnapshot] = deque(maxlen=max_snapshots)
        self.last_recorded_status: Optional[str] = None
        self.last_recorded_frame: int = -1

    def record_frame(
        self,
        frame_idx: int,
        timestamp_sec: float,
        evidence_items: List[EvidenceItem],
        incident_status: str,
        force_snapshot: bool = False
    ) -> None:
        """
        Records an evidence snapshot for the frame.
        Captures periodically or when an evidence state or incident status changes.
        """
        states = {item.evidence_type: item.state.value for item in evidence_items}
        
        status_changed = (self.last_recorded_status != incident_status)
        periodic_interval = (frame_idx - self.last_recorded_frame >= 10)

        if status_changed or periodic_interval or force_snapshot:
            snapshot = TemporalFrameSnapshot(
                frame_idx=frame_idx,
                timestamp_sec=timestamp_sec,
                evidence_states=states,
                incident_status=incident_status
            )
            self.snapshots.append(snapshot)
            self.last_recorded_status = incident_status
            self.last_recorded_frame = frame_idx

    def get_evolution(self) -> List[TemporalFrameSnapshot]:
        """
        Returns all preserved chronological snapshots of evidence evolution.
        """
        return list(self.snapshots)
