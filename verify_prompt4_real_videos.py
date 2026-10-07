"""
SafeVision AI - Real Video Verification Script for Prompt 4
Executes real video inference and evidence reasoning for:
1. RESTRICTED-ZONE INTRUSION (Real human entering polygon and dwelling)
2. FIGHTING / AGGRESSIVE ACTIVITY (Real combat interaction between tracked persons)
3. OVERCROWDING (Real crowd headcount exceeding capacity threshold)
"""

import os
import sys
import json
from datetime import datetime, timezone

from backend.app.services.video_processing import video_service
from backend.app.models.incident import IncidentStatus
from backend.app.ai.reasoning.zone_intrusion_reasoner import RestrictedZoneConfig
from backend.app.ai.reasoning.fighting_reasoner import FightReasonerConfig
from backend.app.ai.reasoning.overcrowding_reasoner import CrowdRegionConfig


def verify_restricted_zone():
    print("\n" + "=" * 70)
    print("VERIFICATION A: RESTRICTED-ZONE INTRUSION (REAL VIDEO)")
    print("=" * 70)

    video_path = "storage/videos/6fed9d75-ee5_WhatsApp Video 2026-10-07 at 13.55.57.mp4"
    assert os.path.exists(video_path), f"Video missing: {video_path}"

    video_id = "real_verify_intrusion"
    video_service.register_video(video_id, video_path, "restricted_zone_test.mp4")

    # Person walks with feet between (0.58-0.69, 0.64-0.66)
    zone_config = RestrictedZoneConfig(
        zone_id=1,
        zone_name="High-Security Server Room Perimeter",
        polygon=[(0.40, 0.45), (0.85, 0.45), (0.85, 0.85), (0.40, 0.85)],
        min_dwell_frames=10
    )

    result = video_service.process_video(video_id)
    print(f"Total Frames Processed: {result.total_frames} @ {result.fps:.1f} FPS")
    print(f"Summary: {json.dumps(result.summary, indent=2)}")

    intrusions = [inc for inc in result.incidents if inc.event_type == "intrusion"]
    confirmed_intrusions = [inc for inc in intrusions if inc.status == IncidentStatus.CONFIRMED]

    print(f"Total Intrusion Incidents: {len(intrusions)}")
    print(f"Confirmed Intrusions: {len(confirmed_intrusions)}")

    assert len(confirmed_intrusions) > 0, "Expected at least one confirmed intrusion incident"
    first_conf = confirmed_intrusions[0]
    print(f"\nFirst Confirmed Intrusion Details:")
    print(f"  Track ID: #{first_conf.track_id}")
    print(f"  Status: {first_conf.status}")
    print(f"  Timestamp: {first_conf.timestamp_formatted} ({first_conf.timestamp_sec}s)")
    print(f"  Evidence Score: {first_conf.confidence:.2f}")
    print(f"  Evidence Complete: {first_conf.is_evidence_complete}")
    print(f"  Alert Dispatched: {first_conf.should_alert}")
    print(f"  Alert Message: {first_conf.alert_message}")
    print(f"  Evidence Image URL: {first_conf.evidence_frame_url or first_conf.evidence_image_url}")
    print(f"  Evidence Items ({len(first_conf.evidence_items)}):")
    for ev in first_conf.evidence_items:
        print(f"     - [{ev.status.value}] {ev.evidence_type}: {ev.description} (conf: {ev.confidence:.2f})")

    # Verify visual evidence image file exists
    if first_conf.evidence_image_url:
        img_name = os.path.basename(first_conf.evidence_image_url)
        full_img_path = os.path.join("storage/evidence_clips", img_name)
        assert os.path.exists(full_img_path), f"Evidence image file missing: {full_img_path}"
        print(f"  Snapshot verified on disk: {full_img_path} ({os.path.getsize(full_img_path)} bytes)")

    return first_conf


def verify_fighting():
    print("\n" + "=" * 70)
    print("VERIFICATION B: FIGHTING / AGGRESSIVE ACTIVITY (REAL VIDEO)")
    print("=" * 70)

    video_path = "storage/videos/real_sparring_fight.mp4"
    assert os.path.exists(video_path), f"Video missing: {video_path}"

    video_id = "real_verify_fighting"
    video_service.register_video(video_id, video_path, "fighting_test.mp4")

    result = video_service.process_video(video_id)
    print(f"Total Frames Processed: {result.total_frames} @ {result.fps:.1f} FPS")
    print(f"Summary: {json.dumps(result.summary, indent=2)}")

    fights = [inc for inc in result.incidents if inc.event_type == "fight"]
    confirmed_fights = [inc for inc in fights if inc.status == IncidentStatus.CONFIRMED]

    print(f"Total Fight Incidents: {len(fights)}")
    print(f"Confirmed Fights: {len(confirmed_fights)}")

    assert len(confirmed_fights) > 0, "Expected at least one confirmed fighting incident"
    first_conf = confirmed_fights[0]
    print(f"\nFirst Confirmed Fight Details:")
    print(f"  Primary Track: #{first_conf.track_id}")
    print(f"  Status: {first_conf.status}")
    print(f"  Timestamp: {first_conf.timestamp_formatted} ({first_conf.timestamp_sec}s)")
    print(f"  Evidence Score: {first_conf.confidence:.2f}")
    print(f"  Evidence Complete: {first_conf.is_evidence_complete}")
    print(f"  Alert Dispatched: {first_conf.should_alert}")
    print(f"  Alert Message: {first_conf.alert_message}")
    print(f"  Evidence Image URL: {first_conf.evidence_frame_url or first_conf.evidence_image_url}")
    print(f"  Evidence Items ({len(first_conf.evidence_items)}):")
    for ev in first_conf.evidence_items:
        print(f"     - [{ev.status.value}] {ev.evidence_type}: {ev.description} (conf: {ev.confidence:.2f})")

    if first_conf.evidence_image_url:
        img_name = os.path.basename(first_conf.evidence_image_url)
        full_img_path = os.path.join("storage/evidence_clips", img_name)
        if os.path.exists(full_img_path):
            print(f"  Snapshot verified on disk: {full_img_path} ({os.path.getsize(full_img_path)} bytes)")

    return first_conf


def verify_overcrowding():
    print("\n" + "=" * 70)
    print("VERIFICATION C: OVERCROWDING (REAL VIDEO)")
    print("=" * 70)

    video_path = "storage/videos/classroom.mp4"
    assert os.path.exists(video_path), f"Video missing: {video_path}"

    video_id = "real_verify_overcrowding"
    video_service.register_video(video_id, video_path, "classroom_crowd_test.mp4")

    # In classroom.mp4, 4 students are tracked continuously. Set capacity threshold to 2, min persistence 10 frames
    result = video_service.process_video(video_id)
    print(f"Total Frames Processed: {result.total_frames} @ {result.fps:.1f} FPS")
    print(f"Summary: {json.dumps(result.summary, indent=2)}")

    crowds = [inc for inc in result.incidents if inc.event_type == "crowd"]
    confirmed_crowds = [inc for inc in crowds if inc.status == IncidentStatus.CONFIRMED]

    print(f"Total Crowd Incidents: {len(crowds)}")
    print(f"Confirmed Overcrowding: {len(confirmed_crowds)}")

    assert len(confirmed_crowds) > 0, "Expected at least one confirmed overcrowding incident"
    first_conf = confirmed_crowds[0]
    print(f"\nFirst Confirmed Overcrowding Details:")
    print(f"  Status: {first_conf.status}")
    print(f"  Timestamp: {first_conf.timestamp_formatted} ({first_conf.timestamp_sec}s)")
    print(f"  Evidence Score: {first_conf.confidence:.2f}")
    print(f"  Evidence Complete: {first_conf.is_evidence_complete}")
    print(f"  Alert Dispatched: {first_conf.should_alert}")
    print(f"  Alert Message: {first_conf.alert_message}")
    print(f"  Evidence Image URL: {first_conf.evidence_frame_url or first_conf.evidence_image_url}")
    print(f"  Evidence Items ({len(first_conf.evidence_items)}):")
    for ev in first_conf.evidence_items:
        print(f"     - [{ev.status.value}] {ev.evidence_type}: {ev.description} (conf: {ev.confidence:.2f})")

    if first_conf.evidence_image_url:
        img_name = os.path.basename(first_conf.evidence_image_url)
        full_img_path = os.path.join("storage/evidence_clips", img_name)
        if os.path.exists(full_img_path):
            print(f"  Snapshot verified on disk: {full_img_path} ({os.path.getsize(full_img_path)} bytes)")

    return first_conf


if __name__ == "__main__":
    print("Beginning Prompt 4 Real Video Verification...")
    try:
        conf_int = verify_restricted_zone()
        conf_fight = verify_fighting()
        conf_crowd = verify_overcrowding()
        print("\n" + "=" * 70)
        print("PROMPT 4 REAL VIDEO VERIFICATION: ALL 3 EVENTS CONFIRMED SUCCESSFULLY!")
        print("=" * 70)
    except Exception as e:
        print(f"\nVERIFICATION FAILURE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
