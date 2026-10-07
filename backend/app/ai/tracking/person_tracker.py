"""
SafeVision AI - Persistent Person Tracker

Associates person detections across consecutive video frames, maintains historical
kinematic trajectories, and computes vertical and horizontal velocities.
"""

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import math
import numpy as np

from backend.app.ai.pose.yolo_pose_estimator import PersonPoseObservation
from backend.app.core.fall_config import fall_config


@dataclass
class TrackHistoryPoint:
    frame_idx: int
    timestamp_sec: float
    observation: PersonPoseObservation
    centroid: Tuple[float, float]
    torso_angle: float
    aspect_w_h: float
    vertical_velocity: float = 0.0  # Downward velocity (positive delta Y per second)


class TrackedPerson:
    """
    Maintains continuous multi-frame state for a single tracked person entity.
    """

    def __init__(self, track_id: int, initial_obs: PersonPoseObservation, frame_idx: int, timestamp_sec: float):
        self.track_id = track_id
        self.history: deque[TrackHistoryPoint] = deque(maxlen=60)  # ~2-3 seconds at 25-30 fps
        self.last_seen_frame = frame_idx
        self.first_seen_frame = frame_idx
        self.missed_frames = 0
        self.fall_state: str = "NORMAL"  # "NORMAL", "CANDIDATE", "VERIFYING", "CONFIRMED", "RETRACTED"
        self.state_entered_frame: int = frame_idx
        self.last_incident_frame: int = -100

        # Add initial point
        self.update(initial_obs, frame_idx, timestamp_sec)

    def update(self, obs: PersonPoseObservation, frame_idx: int, timestamp_sec: float) -> None:
        self.last_seen_frame = frame_idx
        self.missed_frames = 0

        # Compute vertical descent velocity
        v_velocity = 0.0
        if len(self.history) > 0:
            prev = self.history[-1]
            dt = max(0.001, timestamp_sec - prev.timestamp_sec)
            dy = obs.centroid[1] - prev.centroid[1]
            v_velocity = dy / dt  # Positive means moving downwards in screen coordinates

        pt = TrackHistoryPoint(
            frame_idx=frame_idx,
            timestamp_sec=timestamp_sec,
            observation=obs,
            centroid=obs.centroid,
            torso_angle=obs.torso_angle_deg,
            aspect_w_h=obs.aspect_ratio_w_h,
            vertical_velocity=v_velocity
        )
        self.history.append(pt)

    @property
    def current_obs(self) -> PersonPoseObservation:
        return self.history[-1].observation

    @property
    def latest_point(self) -> TrackHistoryPoint:
        return self.history[-1]


class PersonTracker:
    """
    Lightweight, deterministic multi-person tracker designed for continuous video streams.
    """

    def __init__(self, max_distance: Optional[float] = None, max_missed: int = 15):
        self.max_distance = max_distance if max_distance is not None else fall_config.MAX_TRACK_DISTANCE
        self.max_missed = max_missed
        self.next_track_id = 1
        self.active_tracks: Dict[int, TrackedPerson] = {}

    def update(
        self,
        observations: List[PersonPoseObservation],
        frame_idx: int,
        timestamp_sec: float
    ) -> List[TrackedPerson]:
        """
        Matches incoming observations with active tracks and registers new tracks.
        """
        matched_tracks = set()
        matched_obs = set()

        # Compute cost matrix (Euclidean centroid distance)
        if self.active_tracks and observations:
            track_ids = list(self.active_tracks.keys())
            
            distances = np.zeros((len(track_ids), len(observations)))
            for t_idx, tid in enumerate(track_ids):
                track = self.active_tracks[tid]
                last_c = track.latest_point.centroid
                for o_idx, obs in enumerate(observations):
                    c = obs.centroid
                    dist = math.hypot(last_c[0] - c[0], last_c[1] - c[1])
                    distances[t_idx, o_idx] = dist

            # Greedy nearest-neighbor assignment
            while True:
                min_val = np.min(distances)
                if min_val > self.max_distance:
                    break
                t_idx, o_idx = np.unravel_index(np.argmin(distances), distances.shape)
                if distances[t_idx, o_idx] == np.inf:
                    break

                tid = track_ids[t_idx]
                self.active_tracks[tid].update(observations[o_idx], frame_idx, timestamp_sec)
                matched_tracks.add(tid)
                matched_obs.add(o_idx)

                distances[t_idx, :] = np.inf
                distances[:, o_idx] = np.inf

        # Register new detections as new tracks
        for o_idx, obs in enumerate(observations):
            if o_idx not in matched_obs:
                tid = self.next_track_id
                self.next_track_id += 1
                self.active_tracks[tid] = TrackedPerson(tid, obs, frame_idx, timestamp_sec)

        # Handle unmatched tracks & aging
        to_delete = []
        for tid, track in self.active_tracks.items():
            if tid not in matched_tracks and frame_idx != track.last_seen_frame:
                track.missed_frames += 1
                if track.missed_frames > self.max_missed:
                    to_delete.append(tid)

        for tid in to_delete:
            del self.active_tracks[tid]

        return list(self.active_tracks.values())
