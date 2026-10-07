"""
SafeVision AI - Real YOLO Pose Estimation & Posture Kinematics

Extracts human skeletal keypoints, torso inclination angle, aspect ratios,
and vertical kinematic centers from video frames using Ultralytics YOLO Pose.
"""

import math
import os
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any
import numpy as np

from backend.app.core.config import settings
from backend.app.core.fall_config import fall_config
from backend.app.core.logging import logger
from backend.app.ai.base import BaseAIModule, BoundingBox, Keypoint, PoseSkeleton
from backend.app.ai.pose.pose_interface import IPoseEstimator


# COCO Pose Keypoint Index Mapping
NOSE = 0
LEFT_EYE = 1
RIGHT_EYE = 2
LEFT_EAR = 3
RIGHT_EAR = 4
LEFT_SHOULDER = 5
RIGHT_SHOULDER = 6
LEFT_ELBOW = 7
RIGHT_ELBOW = 8
LEFT_WRIST = 9
RIGHT_WRIST = 10
LEFT_HIP = 11
RIGHT_HIP = 12
LEFT_KNEE = 13
RIGHT_KNEE = 14
LEFT_ANKLE = 15
RIGHT_ANKLE = 16

KEYPOINT_NAMES = {
    NOSE: "nose",
    LEFT_SHOULDER: "left_shoulder", RIGHT_SHOULDER: "right_shoulder",
    LEFT_HIP: "left_hip", RIGHT_HIP: "right_hip",
    LEFT_KNEE: "left_knee", RIGHT_KNEE: "right_knee",
    LEFT_ANKLE: "left_ankle", RIGHT_ANKLE: "right_ankle",
}


@dataclass
class PersonPoseObservation:
    """
    Extracted geometrical and kinematic observation of a person in a single frame.
    """
    bbox: Tuple[float, float, float, float]  # (x1, y1, x2, y2) in pixels
    normalized_bbox: Tuple[float, float, float, float]  # (x1, y1, x2, y2) in [0, 1]
    confidence: float
    keypoints: np.ndarray  # shape (17, 3) -> [x, y, conf]
    torso_angle_deg: float  # Angle of spine/torso with horizontal axis (0=flat, 90=upright)
    aspect_ratio_w_h: float  # Width / Height (higher = horizontal / prone)
    aspect_ratio_h_w: float  # Height / Width (higher = upright standing)
    centroid: Tuple[float, float]  # (cx, cy) normalized [0, 1]
    shoulder_mid: Optional[Tuple[float, float]] = None
    hip_mid: Optional[Tuple[float, float]] = None
    ankle_mid: Optional[Tuple[float, float]] = None
    is_upright: bool = False
    is_prone: bool = False


class YOLOPoseEstimator(IPoseEstimator):
    """
    Production YOLO Pose estimator leveraging lightweight YOLO models (YOLO11n-pose / YOLOv8n-pose).
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or fall_config.MODEL_NAME
        self.model: Optional[YOLO] = None
        self._is_ready = False

    def initialize(self, model_path: Optional[str] = None) -> None:
        """
        Loads the YOLO Pose weights.
        """
        from ultralytics import YOLO
        target_model = model_path or self.model_name
        logger.info(f"Initializing YOLO Pose estimator with model: {target_model}")
        try:
            self.model = YOLO(target_model)
            self._is_ready = True
            logger.info("YOLO Pose model loaded successfully.")
        except Exception as e:
            logger.warning(f"Failed to load {target_model}, attempting fallback to yolov8n-pose.pt: {e}")
            try:
                self.model = YOLO("yolov8n-pose.pt")
                self._is_ready = True
                logger.info("Fallback YOLOv8n-pose loaded successfully.")
            except Exception as e2:
                logger.error(f"Critical: Failed to load any YOLO Pose model: {e2}")
                raise

    def is_ready(self) -> bool:
        return self._is_ready and self.model is not None

    def estimate_pose(self, frame: np.ndarray, entity=None) -> Optional[PoseSkeleton]:
        """
        Implements base abstract interface.
        """
        return None

    def detect_and_estimate(self, frame: np.ndarray) -> List[PersonPoseObservation]:
        """
        Performs full inference on a video frame, extracting all person detections with their 
        17 keypoints and calculated posture angles.
        """
        if not self.is_ready():
            self.initialize()

        height, width = frame.shape[:2]
        results = self.model(
            frame,
            conf=fall_config.PERSON_DETECTION_CONFIDENCE,
            classes=[0],  # Person class only
            verbose=False
        )

        observations: List[PersonPoseObservation] = []

        if not results or len(results) == 0:
            return observations

        res = results[0]
        if res.boxes is None or res.keypoints is None:
            return observations

        boxes = res.boxes.xyxy.cpu().numpy()
        confidences = res.boxes.conf.cpu().numpy()
        keypoints_data = res.keypoints.data.cpu().numpy()  # shape: (N, 17, 3)

        for i, (box, conf) in enumerate(zip(boxes, confidences)):
            x1, y1, x2, y2 = box
            box_w = max(1.0, x2 - x1)
            box_h = max(1.0, y2 - y1)
            
            norm_box = (x1 / width, y1 / height, x2 / width, y2 / height)
            cx = ((x1 + x2) / 2.0) / width
            cy = ((y1 + y2) / 2.0) / height
            
            aspect_w_h = box_w / box_h
            aspect_h_w = box_h / box_w

            kpts = keypoints_data[i] if i < len(keypoints_data) else np.zeros((17, 3))
            
            # Compute torso inclination angle
            torso_angle, shoulder_mid, hip_mid = self._calculate_torso_angle(kpts, width, height)
            ankle_mid = self._calculate_ankle_mid(kpts, width, height)

            # Determine posture classification
            is_upright = (torso_angle >= fall_config.TORSO_ANGLE_UPRIGHT_THRESHOLD_DEG) and (aspect_h_w > 1.3)
            is_prone = (torso_angle <= fall_config.TORSO_ANGLE_HORIZONTAL_THRESHOLD_DEG) or (aspect_w_h >= fall_config.ASPECT_RATIO_COLLAPSE_THRESHOLD)

            obs = PersonPoseObservation(
                bbox=(float(x1), float(y1), float(x2), float(y2)),
                normalized_bbox=norm_box,
                confidence=float(conf),
                keypoints=kpts,
                torso_angle_deg=float(torso_angle),
                aspect_ratio_w_h=float(aspect_w_h),
                aspect_ratio_h_w=float(aspect_h_w),
                centroid=(float(cx), float(cy)),
                shoulder_mid=shoulder_mid,
                hip_mid=hip_mid,
                ankle_mid=ankle_mid,
                is_upright=is_upright,
                is_prone=is_prone
            )
            observations.append(obs)

        return observations

    def _calculate_torso_angle(
        self,
        kpts: np.ndarray,
        width: int,
        height: int
    ) -> Tuple[float, Optional[Tuple[float, float]], Optional[Tuple[float, float]]]:
        """
        Calculates angle in degrees of torso spine vector relative to horizontal ground axis.
        90° = vertical upright spine, 0° = completely horizontal.
        """
        l_sh = kpts[LEFT_SHOULDER]
        r_sh = kpts[RIGHT_SHOULDER]
        l_hip = kpts[LEFT_HIP]
        r_hip = kpts[RIGHT_HIP]

        conf_th = fall_config.KEYPOINT_CONFIDENCE_THRESHOLD

        # Calculate shoulder midpoint
        sh_points = []
        if l_sh[2] >= conf_th:
            sh_points.append(l_sh[:2])
        if r_sh[2] >= conf_th:
            sh_points.append(r_sh[:2])

        # Calculate hip midpoint
        hip_points = []
        if l_hip[2] >= conf_th:
            hip_points.append(l_hip[:2])
        if r_hip[2] >= conf_th:
            hip_points.append(r_hip[:2])

        if sh_points and hip_points:
            sh_mid = np.mean(sh_points, axis=0)
            hip_mid = np.mean(hip_points, axis=0)

            dx = float(sh_mid[0] - hip_mid[0])
            dy = float(sh_mid[1] - hip_mid[1])  # Screen Y increases downward

            # Angle with horizontal axis
            angle_rad = math.atan2(abs(dy), abs(dx))
            angle_deg = math.degrees(angle_rad)

            norm_sh_mid = (float(sh_mid[0] / width), float(sh_mid[1] / height))
            norm_hip_mid = (float(hip_mid[0] / width), float(hip_mid[1] / height))
            return angle_deg, norm_sh_mid, norm_hip_mid

        # Fallback: if keypoints are obscured, return neutral estimate
        return 75.0, None, None

    def _calculate_ankle_mid(self, kpts: np.ndarray, width: int, height: int) -> Optional[Tuple[float, float]]:
        conf_th = fall_config.KEYPOINT_CONFIDENCE_THRESHOLD
        ankles = []
        if kpts[LEFT_ANKLE][2] >= conf_th:
            ankles.append(kpts[LEFT_ANKLE][:2])
        if kpts[RIGHT_ANKLE][2] >= conf_th:
            ankles.append(kpts[RIGHT_ANKLE][:2])
        if ankles:
            mid = np.mean(ankles, axis=0)
            return (float(mid[0] / width), float(mid[1] / height))
        return None
