"""
SafeVision AI - Test Video Generator

Creates a realistic test surveillance video (MP4) containing a person walking, falling,
and remaining on the ground for temporal fall detection verification.
"""

import os
import cv2
import numpy as np


def generate_surveillance_fall_video(output_path: str, duration_sec: int = 8, fps: int = 25):
    """
    Generates a 25 FPS MP4 video of a synthetic surveillance scene:
    - 0s - 3s: Person upright walking across hallway
    - 3s - 4s: Rapid downward descent and rotation into horizontal orientation (The Fall)
    - 4s - 8s: Person remains prone on the floor (Persistence window)
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    width, height = 640, 480
    total_frames = duration_sec * fps
    
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    floor_y = 380

    for frame_idx in range(total_frames):
        t = frame_idx / fps
        # Surveillance background: gray warehouse/hallway floor and wall
        frame = np.full((height, width, 3), (220, 220, 225), dtype=np.uint8)
        # Floor
        cv2.rectangle(frame, (0, floor_y - 60), (width, height), (160, 165, 175), -1)
        # Grid tiles
        for x in range(0, width, 80):
            cv2.line(frame, (x, floor_y - 60), (x, height), (140, 145, 155), 1)

        # Draw Person
        if t < 3.0:
            # Phase 1: Walking upright
            px = int(120 + t * 45)
            head_y = int(floor_y - 180 + np.sin(t * 8) * 4)
            shoulder_y = head_y + 25
            hip_y = head_y + 90
            feet_y = floor_y - 10

            # Head
            cv2.circle(frame, (px, head_y), 18, (45, 45, 55), -1)
            # Torso (Dark Blue jacket)
            cv2.rectangle(frame, (px - 22, shoulder_y), (px + 22, hip_y), (140, 60, 40), -1)
            # Legs
            cv2.line(frame, (px - 10, hip_y), (px - 12 + int(np.sin(t * 8) * 12), feet_y), (50, 50, 60), 6)
            cv2.line(frame, (px + 10, hip_y), (px + 12 - int(np.sin(t * 8) * 12), feet_y), (50, 50, 60), 6)

        elif t < 4.0:
            # Phase 2: The Fall (Rapid downward descent and tilt from 3.0s to 4.0s)
            fall_prog = (t - 3.0) / 1.0
            px = int(120 + 3.0 * 45 + fall_prog * 35)
            
            # Angle rotates from 90° (upright) to 10° (horizontal)
            angle_rad = (1.0 - fall_prog) * (np.pi / 2.0) + fall_prog * 0.15
            
            hip_x = px
            hip_y = int((floor_y - 90) + fall_prog * 80)
            
            # Head position based on rotation angle
            torso_len = 110
            head_x = int(hip_x - np.cos(angle_rad) * torso_len)
            head_y = int(hip_y - np.sin(angle_rad) * torso_len)

            # Head
            cv2.circle(frame, (head_x, head_y), 18, (45, 45, 55), -1)
            # Torso
            cv2.line(frame, (head_x, head_y), (hip_x, hip_y), (140, 60, 40), 30)
            # Legs
            cv2.line(frame, (hip_x, hip_y), (hip_x + 50, floor_y - 10), (50, 50, 60), 6)

        else:
            # Phase 3: Person on floor (Sustained prone state)
            px = 285
            py = floor_y - 15
            # Prone horizontal body
            cv2.circle(frame, (px - 60, py - 10), 16, (45, 45, 55), -1)
            cv2.rectangle(frame, (px - 45, py - 20), (px + 40, py + 5), (140, 60, 40), -1)
            cv2.line(frame, (px + 40, py - 8), (px + 90, py - 2), (50, 50, 60), 6)

        # Timestamp on video feed
        mins = int(t // 60)
        secs = t % 60
        cv2.putText(
            frame,
            f"CAM-01 LOBBY | {mins:02d}:{secs:05.2f} | 25.0 FPS",
            (15, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (20, 20, 30),
            2
        )
        out.write(frame)

    out.release()
    print(f"Sample surveillance video generated at: {output_path} ({total_frames} frames, {duration_sec}s)")


if __name__ == "__main__":
    sample_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../storage/videos/sample_fall_test.mp4"))
    generate_surveillance_fall_video(sample_path)
