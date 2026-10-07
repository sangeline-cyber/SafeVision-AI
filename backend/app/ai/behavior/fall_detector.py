"""
SafeVision AI - Fall Detection Pipeline & Annotation Engine

Combines YOLO Pose estimation, continuous person tracking, and 3-State Evidence Reasoning
to detect falls, manage incident lifecycles, and export annotated evidence snapshots.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
import os
import cv2
import numpy as np

from backend.app.ai.pose.yolo_pose_estimator import YOLOPoseEstimator, PersonPoseObservation
from backend.app.ai.tracking.person_tracker import PersonTracker, TrackedPerson
from backend.app.ai.evidence.fall_evidence_reasoner import FallEvidenceReasoner
from backend.app.ai.base import EvidenceObservation
from backend.app.models.incident import IncidentStatus, IncidentRiskLevel
from backend.app.core.fall_config import fall_config
from backend.app.core.config import settings
from backend.app.core.logging import logger


# COCO Pose Skeleton Pairs for Drawing
SKELETON_EDGES = [
    (0, 1), (0, 2), (1, 3), (2, 4), # Face
    (5, 6), # Shoulders
    (5, 7), (7, 9), # Left Arm
    (6, 8), (8, 10), # Right Arm
    (5, 11), (6, 12), # Torso
    (11, 12), # Hips
    (11, 13), (13, 15), # Left Leg
    (12, 14), (14, 16) # Right Leg
]


@dataclass
class DetectedFallEvent:
    track_id: int
    frame_idx: int
    timestamp_sec: float
    status: IncidentStatus
    evidence_score: float
    evidence_items: List[EvidenceObservation]
    evidence_image_path: Optional[str] = None
    risk_level: IncidentRiskLevel = IncidentRiskLevel.CRITICAL


class FallDetectionEngine:
    """
    Main Fall Detection and Temporal Verification Engine.
    """

    def __init__(self):
        self.pose_estimator = YOLOPoseEstimator()
        self.tracker = PersonTracker()
        self.reasoner = FallEvidenceReasoner()
        self.confirmed_incidents: List[DetectedFallEvent] = []

    def initialize(self) -> None:
        self.pose_estimator.initialize()

    def process_frame(
        self,
        frame: np.ndarray,
        frame_idx: int,
        fps: float,
        save_evidence_dir: Optional[str] = None
    ) -> Tuple[List[TrackedPerson], List[DetectedFallEvent]]:
        """
        Processes a single frame: runs YOLO pose, updates tracks, evaluates 3-state fall evidence,
        and generates annotated snapshot images when falls are confirmed or verified.
        """
        timestamp_sec = frame_idx / max(1.0, fps)
        
        # 1. Pose estimation on current frame
        observations = self.pose_estimator.detect_and_estimate(frame)

        # 2. Multi-person tracking update
        active_tracks = self.tracker.update(observations, frame_idx, timestamp_sec)

        events_in_frame: List[DetectedFallEvent] = []

        # 3. Evidence evaluation per tracked person
        for person in active_tracks:
            # Check cooldown
            if (frame_idx - person.last_incident_frame) < fall_config.COOLDOWN_FRAMES:
                continue

            evidence_items, score, status = self.reasoner.evaluate_person_evidence(
                person, frame_idx, timestamp_sec
            )

            old_state = person.fall_state
            person.fall_state = status.value

            # Trigger event when entering VERIFYING, CONFIRMED, or RETRACTED
            if status == IncidentStatus.CONFIRMED and old_state != "CONFIRMED":
                person.last_incident_frame = frame_idx
                evidence_img_path = None
                
                if save_evidence_dir:
                    os.makedirs(save_evidence_dir, exist_ok=True)
                    filename = f"evidence_fall_track{person.track_id}_frame{frame_idx}.jpg"
                    evidence_img_path = os.path.join(save_evidence_dir, filename)
                    self._save_annotated_evidence_frame(frame, person, evidence_items, score, evidence_img_path, timestamp_sec)

                event = DetectedFallEvent(
                    track_id=person.track_id,
                    frame_idx=frame_idx,
                    timestamp_sec=timestamp_sec,
                    status=IncidentStatus.CONFIRMED,
                    evidence_score=score,
                    evidence_items=evidence_items,
                    evidence_image_path=evidence_img_path,
                    risk_level=IncidentRiskLevel.CRITICAL
                )
                events_in_frame.append(event)
                self.confirmed_incidents.append(event)
                logger.info(f"CONFIRMED Fall Event detected at {timestamp_sec:.2f}s for Track #{person.track_id} (Score: {score})")

            elif status == IncidentStatus.RETRACTED and old_state in ["CANDIDATE", "VERIFYING"]:
                logger.info(f"Fall Retracted at {timestamp_sec:.2f}s for Track #{person.track_id} (Recovery detected)")

        return active_tracks, events_in_frame

    def _save_annotated_evidence_frame(
        self,
        frame: np.ndarray,
        person: TrackedPerson,
        evidence_items: List[EvidenceObservation],
        score: float,
        output_path: str,
        timestamp_sec: float
    ) -> None:
        """
        Draws skeletal keypoints, bounding box, evidence metrics, and SafeVision AI HUD onto the snapshot.
        """
        annotated = frame.copy()
        obs = person.current_obs
        x1, y1, x2, y2 = map(int, obs.bbox)
        kpts = obs.keypoints

        # Draw Bounding Box (Red for Confirmed Fall)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 2)

        # Draw Pose Skeleton
        for idx1, idx2 in SKELETON_EDGES:
            if kpts[idx1][2] >= 0.3 and kpts[idx2][2] >= 0.3:
                pt1 = (int(kpts[idx1][0]), int(kpts[idx1][1]))
                pt2 = (int(kpts[idx2][0]), int(kpts[idx2][1]))
                cv2.line(annotated, pt1, pt2, (0, 255, 255), 2)

        # Draw Keypoints
        for k in kpts:
            if k[2] >= 0.3:
                cv2.circle(annotated, (int(k[0]), int(k[1])), 4, (0, 255, 0), -1)

        # Top HUD Banner
        h, w = annotated.shape[:2]
        cv2.rectangle(annotated, (0, 0), (w, 60), (15, 23, 42), -1)
        
        mins = int(timestamp_sec // 60)
        secs = timestamp_sec % 60
        time_str = f"{mins:02d}:{secs:05.2f}"

        cv2.putText(
            annotated,
            f"SAFEVISION AI | CONFIRMED FALL - Track #{person.track_id}",
            (15, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 0, 255),
            2
        )
        cv2.putText(
            annotated,
            f"Time: {time_str} | Evidence Score: {score:.2f} | Torso Angle: {obs.torso_angle_deg:.1f} deg",
            (15, 48),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.50,
            (200, 200, 200),
            1
        )

        cv2.imwrite(output_path, annotated)
