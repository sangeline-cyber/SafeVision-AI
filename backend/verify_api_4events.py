import requests
import json

test_files = [
    ("FALL", "storage/videos/137c31f1-9ee_WhatsApp Video 2026-10-07 at 13.55.52.mp4"),
    ("INTRUSION", "storage/videos/6fed9d75-ee5_WhatsApp Video 2026-10-07 at 13.55.57.mp4"),
    ("FIGHT", "storage/videos/real_sparring_fight.mp4"),
    ("CROWD", "storage/videos/classroom.mp4"),
]

for label, fpath in test_files:
    print(f"\n==========================================")
    print(f"TESTING {label}: {fpath}")
    print(f"==========================================")
    fname = fpath.split("/")[-1]
    with open(fpath, "rb") as f:
        up_res = requests.post(
            "http://127.0.0.1:8000/api/v1/videos/upload",
            files={"file": (fname, f, "video/mp4")}
        )
    if up_res.status_code not in (200, 201):
        print(f"Upload failed: {up_res.status_code} {up_res.text}")
        continue
    vid_data = up_res.json()
    vid_id = vid_data["video_id"]
    print(f"Uploaded successfully: video_id={vid_id}")

    proc_res = requests.post(f"http://127.0.0.1:8000/api/v1/videos/{vid_id}/process")
    print(f"Process HTTP Status: {proc_res.status_code}")
    if proc_res.status_code != 200:
        print(f"Process failed: {proc_res.status_code} {proc_res.text}")
        continue

    proc_data = proc_res.json()
    summary = proc_data.get("summary", {})
    print(f"Processing Summary: {json.dumps(summary, indent=2)}")
    incidents = proc_data.get("incidents", [])
    print(f"Total Incidents Detected: {len(incidents)}")
    for i, inc in enumerate(incidents):
        print(f"\n--- Incident #{i+1} ---")
        print(f"  Detected event_type:    {inc.get('event_type')}")
        print(f"  Incident status:        {inc.get('status')}")
        print(f"  Evidence score:         {inc.get('confidence')}")
        print(f"  Evidence completeness:  {inc.get('is_evidence_complete')} ({sum(1 for ev in inc.get('evidence_items', []) if ev.get('status') == 'SUPPORTED')}/{len(inc.get('evidence_items', []))} SUPPORTED)")
        print(f"  Track / Participants:   track={inc.get('track_id')} | participants={inc.get('participant_ids')}")
        print(f"  Alert status:           should_alert={inc.get('should_alert')} | alert_id={inc.get('alert_id')}")
        print(f"  Alert message:          {inc.get('alert_message')}")
        print(f"  Evidence snapshot URL:  {inc.get('evidence_frame_url') or inc.get('evidence_image_url')}")
        print(f"  Evidence items ({len(inc.get('evidence_items', []))} total):")
        for ev in inc.get('evidence_items', []):
            print(f"    * [{ev.get('status')}] {ev.get('evidence_type')}: {ev.get('description')} (conf={ev.get('confidence')})")
