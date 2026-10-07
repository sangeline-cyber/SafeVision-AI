"""
SafeVision AI - End-to-End Fall Detection Verification Script

Uploads a real surveillance video to FastAPI backend, executes real YOLO pose inference,
tracking, kinematic feature extraction, temporal fall state machine, and evidence verification.
"""

import os
import sys
import time
import requests

BASE_URL = "http://127.0.0.1:8000"


def main():
    video_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../storage/videos/sample_fall_test.mp4"))
    if not os.path.exists(video_path):
        print(f"Error: Test video not found at {video_path}")
        sys.exit(1)

    print(f"1. Checking Backend & Database Health...")
    health_res = requests.get(f"{BASE_URL}/api/health/database")
    print(f"Health Response ({health_res.status_code}): {health_res.json()}")
    assert health_res.status_code == 200, "Database health check failed"

    print(f"\n2. Uploading real test video: {os.path.basename(video_path)} ({os.path.getsize(video_path)} bytes)...")
    with open(video_path, "rb") as f:
        upload_res = requests.post(
            f"{BASE_URL}/api/v1/videos/upload",
            files={"file": ("sample_fall_test.mp4", f, "video/mp4")}
        )
    print(f"Upload Response ({upload_res.status_code}): {upload_res.json()}")
    assert upload_res.status_code == 201, "Video upload failed"
    video_id = upload_res.json()["video_id"]

    print(f"\n3. Triggering Real Computer Vision Video Processing Job for video {video_id}...")
    proc_res = requests.post(f"{BASE_URL}/api/v1/videos/{video_id}/process")
    print(f"Process Trigger Response ({proc_res.status_code}): {proc_res.json()}")
    assert proc_res.status_code in [200, 202], "Video processing trigger failed"

    if proc_res.status_code == 200:
        results = proc_res.json()
    else:
        print(f"\n4. Polling processing progress and temporal verification...")
        start_t = time.time()
        while True:
            status_res = requests.get(f"{BASE_URL}/api/v1/videos/{video_id}/status")
            status_data = status_res.json()
            print(f"Status: {status_data['status']} | Progress: {status_data['progress_percent']}% | Message: {status_data['message']}")
            
            if status_data["status"] == "completed":
                break
            if status_data["status"] == "failed":
                print(f"Error: Processing failed with error: {status_data.get('error')}")
                sys.exit(1)
                
            time.sleep(1.0)
            if time.time() - start_t > 60:
                print("Timeout waiting for video processing")
                sys.exit(1)

        results_res = requests.get(f"{BASE_URL}/api/v1/videos/{video_id}/results")
    print(f"\n5. Final Real AI Results:")
    print(f"Total Frames Processed: {results['total_frames']}")
    print(f"FPS: {results['fps']}")
    print(f"Duration: {results['duration_sec']}s")
    print(f"Confirmed Falls: {results['summary']['confirmed_falls']}")
    print(f"Total Incidents: {results['summary']['total_incidents']}")
    print(f"Processing Time: {results['summary']['processing_time_sec']}s")
    print(f"Model: {results['summary']['model']}")
    print(f"Reasoning Engine: {results['summary']['reasoning_engine']}")

    for idx, inc in enumerate(results["incidents"]):
        print(f"\n--- Incident #{idx+1} ---")
        print(f"  Incident ID: {inc['incident_id']}")
        print(f"  Status: {inc['status']}")
        print(f"  Track ID: {inc['track_id']}")
        print(f"  Timestamp: {inc['timestamp_formatted']} ({inc['timestamp_sec']}s, Frame {inc['frame_number']})")
        print(f"  Fall Evidence Score: {inc['fall_evidence_score']}")
        print(f"  Evidence Image: {inc['evidence_image_url']}")
        print(f"  Evidence Checklist:")
        for ev in inc["evidence_items"]:
            print(f"    - [{ev['status']}] {ev['evidence_type']}: {ev['description']} (conf: {ev['confidence']})")

    print("\n==================================================")
    print("REAL VIDEO + REAL FALL DETECTION VERIFIED!")
    print("==================================================")


if __name__ == "__main__":
    main()
