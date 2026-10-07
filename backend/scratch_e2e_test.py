import requests
import json

upload_url = "http://127.0.0.1:8000/api/v1/videos/upload"
video_path = "storage/videos/sample_fall_test.mp4"

with open(video_path, "rb") as f:
    upload_res = requests.post(upload_url, files={"file": ("real_surveillance_fall.mp4", f, "video/mp4")})

print("Upload response:", upload_res.status_code)
upload_data = upload_res.json()
video_id = upload_data["video_id"]
print(f"Video uploaded successfully. ID: {video_id}, Size: {upload_data['file_size_bytes']} bytes")

process_url = f"http://127.0.0.1:8000/api/v1/videos/{video_id}/process"
print(f"Triggering video analysis at {process_url}...")
proc_res = requests.post(process_url)
print("Process response status:", proc_res.status_code)

if proc_res.status_code == 200:
    data = proc_res.json()
    print("\n--- Summary ---")
    print(json.dumps(data.get("summary", {}), indent=2))
    print(f"\nIncidents Detected: {len(data.get('incidents', []))}")
    for i, inc in enumerate(data.get("incidents", []), 1):
        print(f"\n[Incident {i}]")
        print(f"  Incident ID in DB: {inc.get('incident_id')}")
        print(f"  Track ID: {inc.get('track_id')}")
        print(f"  Timestamp: {inc.get('timestamp_formatted')} ({inc.get('timestamp_sec')}s)")
        print(f"  Status: {inc.get('status')}")
        print(f"  Confidence: {inc.get('confidence')}")
        print(f"  Evidence Complete: {inc.get('is_evidence_complete')}")
        print(f"  Should Alert: {inc.get('should_alert')}")
        print(f"  Alert ID in DB: {inc.get('alert_id')}")
        print(f"  Alert Message: {inc.get('alert_message')}")
        print(f"  Temporal Trace Snapshots: {len(inc.get('temporal_trace', []))}")
        print("  5 Evidence Categories:")
        for ev in inc.get("evidence_items", []):
            print(f"    - {ev.get('evidence_type')}: [{ev.get('status')}] (conf: {ev.get('confidence'):.2f}) -> {ev.get('description')}")
else:
    print("Process error:", proc_res.text)
