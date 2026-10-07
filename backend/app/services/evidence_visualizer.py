"""
SafeVision AI - Multi-Event Evidence Frame Visualizer

Renders evidence snapshots with HUD telemetry, bounding boxes, pose overlays,
polygonal perimeters, and interaction vectors for:
- RESTRICTED-ZONE INTRUSION
- FIGHTING / AGGRESSIVE ACTIVITY
- OVERCROWDING
- FALL DETECTION (backward compatibility)
"""

import os
from typing import List, Tuple, Optional
import cv2
import numpy as np

from backend.app.ai.tracking.person_tracker import TrackedPerson
from backend.app.ai.reasoning.zone_intrusion_reasoner import RestrictedZoneConfig
from backend.app.ai.reasoning.overcrowding_reasoner import CrowdRegionConfig


SKELETON_EDGES = [
    (0, 1), (0, 2), (1, 3), (2, 4),           # Facial keypoints
    (5, 6),                                   # Shoulders
    (5, 7), (7, 9),                           # Left arm
    (6, 8), (8, 10),                          # Right arm
    (5, 11), (6, 12),                         # Torso sides
    (11, 12),                                 # Hips
    (11, 13), (13, 15),                       # Left leg
    (12, 14), (14, 16),                       # Right leg
]


def draw_hud_banner(annotated: np.ndarray, title: str, subtitle: str, alert_color: Tuple[int, int, int] = (0, 0, 255)) -> None:
    """
    Renders the SafeVision AI HUD banner at the top of the frame.
    """
    h, w = annotated.shape[:2]
    cv2.rectangle(annotated, (0, 0), (w, 64), (15, 23, 42), -1)
    cv2.line(annotated, (0, 64), (w, 64), alert_color, 2)

    cv2.putText(
        annotated,
        title,
        (16, 26),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        alert_color,
        2,
        cv2.LINE_AA
    )
    cv2.putText(
        annotated,
        subtitle,
        (16, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        (203, 213, 225),
        1,
        cv2.LINE_AA
    )


def save_intrusion_evidence_frame(
    frame: np.ndarray,
    person: TrackedPerson,
    zone_config: RestrictedZoneConfig,
    score: float,
    dwell_frames: int,
    timestamp_sec: float,
    output_path: str
) -> None:
    """
    Draws polygon boundary, ground contact point, person bbox, and HUD for zone intrusion.
    """
    annotated = frame.copy()
    h, w = annotated.shape[:2]

    # 1. Draw polygon boundary
    pts = np.array([[int(px * w), int(py * h)] for px, py in zone_config.polygon], np.int32)
    pts = pts.reshape((-1, 1, 2))

    # Semi-transparent overlay fill
    overlay = annotated.copy()
    cv2.fillPoly(overlay, [pts], (0, 0, 180))  # Translucent red
    cv2.addWeighted(overlay, 0.25, annotated, 0.75, 0, annotated)

    # Perimeter outline
    cv2.polylines(annotated, [pts], True, (0, 0, 255), 2, cv2.LINE_AA)

    # Zone name badge
    if len(zone_config.polygon) > 0:
        first_pt = (int(zone_config.polygon[0][0] * w), int(zone_config.polygon[0][1] * h) - 8)
        cv2.putText(
            annotated,
            f"RESTRICTED ZONE: {zone_config.zone_name}",
            first_pt,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 255),
            1,
            cv2.LINE_AA
        )

    # 2. Draw person bbox & ground feet contact point
    obs = person.current_obs
    x1, y1, x2, y2 = map(int, obs.bbox)
    feet_x = int((x1 + x2) / 2.0)
    feet_y = y2

    cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 2)
    cv2.circle(annotated, (feet_x, feet_y), 6, (0, 255, 255), -1)
    cv2.putText(
        annotated,
        f"INTRUDER #{person.track_id}",
        (x1, max(18, y1 - 8)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 0, 255),
        2,
        cv2.LINE_AA
    )

    # 3. HUD
    mins = int(timestamp_sec // 60)
    secs = timestamp_sec % 60
    time_str = f"{mins:02d}:{secs:05.2f}"
    title = f"SAFEVISION AI | RESTRICTED-ZONE INTRUSION - Track #{person.track_id}"
    subtitle = (
        f"Zone: {zone_config.zone_name} | Dwell: {dwell_frames} frames "
        f"(Threshold: {zone_config.min_dwell_frames}) | Score: {score:.2f} | Time: {time_str}"
    )
    draw_hud_banner(annotated, title, subtitle, alert_color=(0, 0, 255))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, annotated)


def save_fighting_evidence_frame(
    frame: np.ndarray,
    p1: TrackedPerson,
    p2: TrackedPerson,
    score: float,
    interaction_distance: float,
    engagement_frames: int,
    timestamp_sec: float,
    output_path: str
) -> None:
    """
    Draws interacting bboxes, connecting proximity line, and HUD for fighting altercation.
    """
    annotated = frame.copy()

    # Draw both subjects' bboxes
    for p, color in [(p1, (0, 0, 255)), (p2, (0, 140, 255))]:
        obs = p.current_obs
        x1, y1, x2, y2 = map(int, obs.bbox)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            annotated,
            f"FIGHT Track #{p.track_id}",
            (x1, max(18, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2,
            cv2.LINE_AA
        )

        # Pose skeleton if available
        kpts = obs.keypoints
        if kpts is not None and len(kpts) >= 17:
            for idx1, idx2 in SKELETON_EDGES:
                if kpts[idx1][2] >= 0.3 and kpts[idx2][2] >= 0.3:
                    pt1 = (int(kpts[idx1][0]), int(kpts[idx1][1]))
                    pt2 = (int(kpts[idx2][0]), int(kpts[idx2][1]))
                    cv2.line(annotated, pt1, pt2, (0, 255, 255), 1, cv2.LINE_AA)

    # Connecting line between centroids
    c1 = (int(p1.current_obs.centroid[0]), int(p1.current_obs.centroid[1]))
    c2 = (int(p2.current_obs.centroid[0]), int(p2.current_obs.centroid[1]))
    cv2.line(annotated, c1, c2, (0, 255, 255), 2, cv2.LINE_AA)

    mid_pt = ((c1[0] + c2[0]) // 2, (c1[1] + c2[1]) // 2)
    cv2.putText(
        annotated,
        f"Prox: {interaction_distance:.2f}",
        mid_pt,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 0),
        1,
        cv2.LINE_AA
    )

    # HUD
    mins = int(timestamp_sec // 60)
    secs = timestamp_sec % 60
    time_str = f"{mins:02d}:{secs:05.2f}"
    title = f"SAFEVISION AI | FIGHTING / AGGRESSIVE ACTIVITY - Tracks #{p1.track_id} & #{p2.track_id}"
    subtitle = (
        f"Sustained Altercation: {engagement_frames} frames | Prox: {interaction_distance:.2f} "
        f"| Score: {score:.2f} | Time: {time_str}"
    )
    draw_hud_banner(annotated, title, subtitle, alert_color=(0, 0, 255))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, annotated)


def save_overcrowding_evidence_frame(
    frame: np.ndarray,
    active_tracks: List[TrackedPerson],
    region_config: CrowdRegionConfig,
    score: float,
    current_count: int,
    dwell_frames: int,
    timestamp_sec: float,
    output_path: str
) -> None:
    """
    Draws crowd density bboxes, region polygon if configured, and HUD for overcrowding.
    """
    annotated = frame.copy()
    h, w = annotated.shape[:2]

    # Draw region polygon if specified
    if region_config.polygon and len(region_config.polygon) >= 3:
        pts = np.array([[int(px * w), int(py * h)] for px, py in region_config.polygon], np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.polylines(annotated, [pts], True, (0, 165, 255), 2, cv2.LINE_AA)
        first_pt = (int(region_config.polygon[0][0] * w), int(region_config.polygon[0][1] * h) - 8)
        cv2.putText(
            annotated,
            f"CROWD ZONE: {region_config.region_name}",
            first_pt,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 165, 255),
            1,
            cv2.LINE_AA
        )

    # Draw bboxes for all tracked crowd members
    for idx, p in enumerate(active_tracks, 1):
        x1, y1, x2, y2 = map(int, p.current_obs.bbox)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 140, 255), 2)
        cv2.putText(
            annotated,
            f"Person {idx} (#{p.track_id})",
            (x1, max(16, y1 - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 255, 255),
            1,
            cv2.LINE_AA
        )

    # HUD
    mins = int(timestamp_sec // 60)
    secs = timestamp_sec % 60
    time_str = f"{mins:02d}:{secs:05.2f}"
    title = f"SAFEVISION AI | OVERCROWDING SURGE - {current_count} Persons (Threshold: {region_config.capacity_threshold})"
    subtitle = (
        f"Zone: {region_config.region_name} | Persistence: {dwell_frames} frames "
        f"(Threshold: {region_config.min_persistence_frames}) | Score: {score:.2f} | Time: {time_str}"
    )
    draw_hud_banner(annotated, title, subtitle, alert_color=(0, 140, 255))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, annotated)
