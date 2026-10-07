"""
SafeVision AI - Video Processing Service

Manages video ingestion, frame extraction, AI model inference, incident database persistence,
and progress telemetry for uploaded surveillance video files.
"""

import os
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.database.session import SessionLocal
from backend.app.models.camera import Camera, CameraStatus
from backend.app.models.entity import TrackedEntity
from backend.app.models.incident import Incident, IncidentStatus, EventType, IncidentRiskLevel
from backend.app.models.evidence import Evidence, EvidenceStatus
from backend.app.models.alert import Alert, AlertSeverity
from backend.app.schemas.video import (
    VideoProcessingStatusResponse,
    VideoAnalysisResultResponse,
    IncidentDetectionResponse,
    EvidenceItemResponse,
)


class VideoProcessingManager:
    """
    Singleton service managing active video processing jobs and results.
    """

    def __init__(self):
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._results: Dict[str, VideoAnalysisResultResponse] = {}

    def register_video(self, video_id: str, filepath: str, filename: str) -> None:
        """
        Registers an uploaded video file for processing.
        """
        self._jobs[video_id] = {
            "video_id": video_id,
            "filepath": filepath,
            "filename": filename,
            "status": "pending",
            "progress_percent": 0.0,
            "processed_frames": 0,
            "total_frames": 0,
            "fps": 30.0,
            "start_time": None,
            "elapsed_time_sec": 0.0,
            "incidents_count": 0,
            "error": None
        }

    def get_status(self, video_id: str) -> Optional[VideoProcessingStatusResponse]:
        """
        Retrieves live telemetry status of a video processing job.
        """
        job = self._jobs.get(video_id)
        if not job:
            return None
        return VideoProcessingStatusResponse(
            video_id=video_id,
            status=job["status"],
            progress_percent=job["progress_percent"],
            processed_frames=job["processed_frames"],
            total_frames=job["total_frames"],
            fps=job["fps"],
            elapsed_time_sec=job["elapsed_time_sec"],
            incidents_count=job["incidents_count"],
            error=job["error"]
        )

    def get_results(self, video_id: str) -> Optional[VideoAnalysisResultResponse]:
        """
        Retrieves completed analysis results for a video.
        """
        return self._results.get(video_id)

    def process_video(self, video_id: str) -> VideoAnalysisResultResponse:
        """
        Executes real computer vision inference frame-by-frame on the video.
        """
        job = self._jobs.get(video_id)
        if not job:
            raise ValueError(f"Video job {video_id} not found.")

        filepath = job["filepath"]
        filename = job["filename"]
        logger.info(f"Starting video analysis on: {filepath}")

        import cv2
        from backend.app.ai.behavior.fall_detector import FallDetectionEngine, DetectedFallEvent

        job["status"] = "processing"
        job["start_time"] = time.time()

        cap = cv2.VideoCapture(filepath)
        if not cap.isOpened():
            err = f"Failed to open video file: {filepath}"
            logger.error(err)
            job["status"] = "failed"
            job["error"] = err
            raise RuntimeError(err)

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = float(cap.get(cv2.CAP_PROP_FPS)) or 30.0
        duration_sec = total_frames / fps if total_frames > 0 else 0.0

        job["total_frames"] = total_frames
        job["fps"] = fps

        engine = FallDetectionEngine()
        engine.initialize()

        from backend.app.ai.reasoning.fall_incident_reasoner import FallIncidentReasoner
        from backend.app.ai.reasoning.evidence_schema import FallReasoningEvaluation
        from backend.app.ai.reasoning.zone_intrusion_reasoner import ZoneIntrusionReasoner, RestrictedZoneConfig
        from backend.app.ai.reasoning.fighting_reasoner import FightIncidentReasoner, FightReasonerConfig
        from backend.app.ai.reasoning.overcrowding_reasoner import OvercrowdingReasoner, CrowdRegionConfig
        from backend.app.services.evidence_visualizer import (
            save_intrusion_evidence_frame,
            save_fighting_evidence_frame,
            save_overcrowding_evidence_frame
        )

        incident_reasoner = FallIncidentReasoner()
        zone_config = RestrictedZoneConfig(
            zone_id=1,
            zone_name="High-Security Server Room Perimeter",
            polygon=[(0.40, 0.45), (0.85, 0.45), (0.85, 0.85), (0.40, 0.85)],
            min_dwell_frames=10
        )
        fight_config = FightReasonerConfig()
        crowd_config = CrowdRegionConfig(
            capacity_threshold=3,
            min_persistence_frames=10
        )

        zone_reasoner = ZoneIntrusionReasoner(zone_config=zone_config)
        fight_reasoner = FightIncidentReasoner(config=fight_config)
        crowd_reasoner = OvercrowdingReasoner(config=crowd_config)

        evidence_dir = settings.EVIDENCE_CLIPS_PATH
        os.makedirs(evidence_dir, exist_ok=True)

        frame_idx = 0
        all_detected_events: List[Any] = []
        recorded_track_states: Dict[int, str] = {}
        recorded_intrusion_states: Dict[int, str] = {}
        recorded_fight_states: Dict[Tuple[int, int], str] = {}
        recorded_crowd_state: str = "NORMAL"

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_idx += 1
                timestamp_sec = frame_idx / max(1.0, fps)
                
                # 1. Run real YOLO Pose & Person Tracking (Protected Modules)
                active_tracks, legacy_events = engine.process_frame(frame, frame_idx, fps, save_evidence_dir=evidence_dir)
                
                # 2. Run Evidence Reasoning Layer for Fall (Protected Prompt 3)
                for person in active_tracks:
                    reasoning_eval = incident_reasoner.evaluate(person, frame_idx, timestamp_sec)
                    old_state = recorded_track_states.get(person.track_id, "NORMAL")
                    new_state = reasoning_eval.incident_status.value
                    recorded_track_states[person.track_id] = new_state

                    # Locate evidence image if saved for this track
                    ev_img_path = None
                    for leg_ev in legacy_events:
                        if leg_ev.track_id == person.track_id and leg_ev.evidence_image_path:
                            ev_img_path = leg_ev.evidence_image_path
                            break

                    # Register incident on state transition to CONFIRMED or RETRACTED
                    if reasoning_eval.incident_status == IncidentStatus.CONFIRMED and old_state != "CONFIRMED":
                        if not ev_img_path:
                            filename_img = f"evidence_fall_track{person.track_id}_frame{frame_idx}.jpg"
                            ev_img_path = os.path.join(evidence_dir, filename_img)
                            engine._save_annotated_evidence_frame(frame, person, [], reasoning_eval.evidence_score, ev_img_path, timestamp_sec)

                        # Remove any premature retraction for this track
                        all_detected_events = [
                            ev for ev in all_detected_events
                            if not (
                                (isinstance(ev, dict) and ev.get("eval") and getattr(ev["eval"], "track_id", None) == person.track_id and ev.get("event_type", "fall") == "fall" and ev["eval"].incident_status == IncidentStatus.RETRACTED) or
                                (not isinstance(ev, dict) and getattr(ev, "track_id", None) == person.track_id and getattr(ev, "status", None) == IncidentStatus.RETRACTED)
                            )
                        ]
                        all_detected_events.append({
                            "event_type": "fall",
                            "eval": reasoning_eval,
                            "evidence_image_path": ev_img_path,
                            "track_id": person.track_id
                        })
                        job["incidents_count"] = len(all_detected_events)
                        logger.info(f"Reasoning Layer: CONFIRMED Fall Incident for Track #{person.track_id} (Alert={reasoning_eval.should_alert})")

                    elif reasoning_eval.incident_status == IncidentStatus.RETRACTED and old_state in ["VERIFYING", "CONFIRMED"]:
                        all_detected_events.append({
                            "event_type": "fall",
                            "eval": reasoning_eval,
                            "evidence_image_path": ev_img_path,
                            "track_id": person.track_id
                        })
                        logger.info(f"Reasoning Layer: RETRACTED Fall Incident for Track #{person.track_id} (Recovery detected)")

                # 3. Run Restricted-Zone Intrusion Reasoner (Prompt 4)
                for person in active_tracks:
                    intrusion_eval = zone_reasoner.evaluate_person(
                        person, frame_idx, timestamp_sec,
                        frame_width=frame.shape[1], frame_height=frame.shape[0]
                    )
                    old_int_state = recorded_intrusion_states.get(person.track_id, "NORMAL")
                    new_int_state = intrusion_eval.incident_status.value
                    recorded_intrusion_states[person.track_id] = new_int_state

                    if intrusion_eval.incident_status == IncidentStatus.CONFIRMED:
                        existing_int = next(
                            (ev for ev in all_detected_events if isinstance(ev, dict) and ev.get("event_type") == "intrusion" and ev.get("track_id") == person.track_id and ev["eval"].incident_status == IncidentStatus.CONFIRMED),
                            None
                        )
                        if existing_int is None:
                            int_filename = f"evidence_intrusion_track{person.track_id}_frame{frame_idx}.jpg"
                            int_img_path = os.path.join(evidence_dir, int_filename)
                            save_intrusion_evidence_frame(
                                frame, person, zone_config, intrusion_eval.evidence_score,
                                intrusion_eval.dwell_frames, timestamp_sec, int_img_path
                            )
                            all_detected_events.append({
                                "event_type": "intrusion",
                                "eval": intrusion_eval,
                                "evidence_image_path": int_img_path,
                                "track_id": person.track_id
                            })
                            job["incidents_count"] = len(all_detected_events)
                            logger.info(f"Reasoning Layer: CONFIRMED Restricted-Zone Intrusion for Track #{person.track_id} (Dwell={intrusion_eval.dwell_frames} frames, Alert={intrusion_eval.should_alert})")
                        else:
                            if intrusion_eval.evidence_score > existing_int["eval"].evidence_score:
                                existing_int["eval"] = intrusion_eval

                    elif intrusion_eval.incident_status == IncidentStatus.RETRACTED and old_int_state in ["VERIFYING", "CONFIRMED"]:
                        all_detected_events.append({
                            "event_type": "intrusion",
                            "eval": intrusion_eval,
                            "evidence_image_path": None,
                            "track_id": person.track_id
                        })
                        logger.info(f"Reasoning Layer: RETRACTED Intrusion for Track #{person.track_id} (Exited restricted zone)")

                # 4. Run Fighting / Physical Aggression Reasoner (Prompt 4)
                fight_evals = fight_reasoner.evaluate_scene(active_tracks, frame_idx, timestamp_sec)
                for fight_eval in fight_evals:
                    p_ids = fight_eval.involved_track_ids
                    pair_key = (min(p_ids[0], p_ids[1]), max(p_ids[0], p_ids[1]))
                    old_fight_state = recorded_fight_states.get(pair_key, "NORMAL")
                    new_fight_state = fight_eval.incident_status.value
                    recorded_fight_states[pair_key] = new_fight_state

                    if fight_eval.incident_status == IncidentStatus.CONFIRMED:
                        existing_fight = next(
                            (ev for ev in all_detected_events if isinstance(ev, dict) and ev.get("event_type") == "fight" and ev["eval"].incident_status == IncidentStatus.CONFIRMED),
                            None
                        )
                        if existing_fight is None:
                            p1_cand = next((p for p in active_tracks if p.track_id == pair_key[0]), None)
                            p2_cand = next((p for p in active_tracks if p.track_id == pair_key[1]), None)
                            fight_img_path = None
                            if p1_cand and p2_cand:
                                fight_filename = f"evidence_fight_tracks_{pair_key[0]}_{pair_key[1]}_frame{frame_idx}.jpg"
                                fight_img_path = os.path.join(evidence_dir, fight_filename)
                                save_fighting_evidence_frame(
                                    frame, p1_cand, p2_cand, fight_eval.evidence_score,
                                    fight_eval.interaction_distance,
                                    fight_reasoner._engagement_trackers.get(pair_key, 0),
                                    timestamp_sec, fight_img_path
                                )
                            all_detected_events.append({
                                "event_type": "fight",
                                "eval": fight_eval,
                                "evidence_image_path": fight_img_path,
                                "track_id": pair_key[0],
                                "pair_key": pair_key,
                                "involved_track_ids": p_ids
                            })
                            job["incidents_count"] = len(all_detected_events)
                            logger.info(f"Reasoning Layer: CONFIRMED Fighting Altercation between Tracks #{pair_key[0]} and #{pair_key[1]} (Alert={fight_eval.should_alert})")
                        else:
                            if fight_eval.evidence_score > existing_fight["eval"].evidence_score:
                                existing_fight["eval"] = fight_eval

                    elif fight_eval.incident_status == IncidentStatus.RETRACTED and old_fight_state in ["VERIFYING", "CONFIRMED"]:
                        all_detected_events.append({
                            "event_type": "fight",
                            "eval": fight_eval,
                            "evidence_image_path": None,
                            "track_id": pair_key[0],
                            "pair_key": pair_key,
                            "involved_track_ids": p_ids
                        })
                        logger.info(f"Reasoning Layer: RETRACTED Fighting Altercation between Tracks #{pair_key[0]} and #{pair_key[1]} (Disengaged/Separated)")

                # 5. Run Overcrowding Reasoner (Prompt 4)
                crowd_eval = crowd_reasoner.evaluate_crowd(
                    active_tracks, frame_idx, timestamp_sec,
                    frame_width=frame.shape[1], frame_height=frame.shape[0]
                )
                if crowd_eval is not None:
                    old_crw_state = recorded_crowd_state
                    new_crw_state = crowd_eval.incident_status.value
                    recorded_crowd_state = new_crw_state

                    if crowd_eval.incident_status == IncidentStatus.CONFIRMED:
                        existing_crowd = next(
                            (ev for ev in all_detected_events if isinstance(ev, dict) and ev.get("event_type") == "crowd" and ev["eval"].incident_status == IncidentStatus.CONFIRMED),
                            None
                        )
                        if existing_crowd is None:
                            crowd_filename = f"evidence_crowd_frame{frame_idx}.jpg"
                            crowd_img_path = os.path.join(evidence_dir, crowd_filename)
                            save_overcrowding_evidence_frame(
                                frame, active_tracks, crowd_config, crowd_eval.evidence_score,
                                crowd_eval.current_count, crowd_eval.dwell_frames,
                                timestamp_sec, crowd_img_path
                            )
                            all_detected_events.append({
                                "event_type": "crowd",
                                "eval": crowd_eval,
                                "evidence_image_path": crowd_img_path,
                                "track_id": None
                            })
                            job["incidents_count"] = len(all_detected_events)
                            logger.info(f"Reasoning Layer: CONFIRMED Overcrowding in {crowd_config.region_name} (Count={crowd_eval.current_count}, Alert={crowd_eval.should_alert})")
                        else:
                            if crowd_eval.evidence_score > existing_crowd["eval"].evidence_score:
                                existing_crowd["eval"] = crowd_eval

                    elif crowd_eval.incident_status == IncidentStatus.RETRACTED and old_crw_state in ["VERIFYING", "CONFIRMED"]:
                        all_detected_events.append({
                            "event_type": "crowd",
                            "eval": crowd_eval,
                            "evidence_image_path": None,
                            "track_id": None
                        })
                        logger.info(f"Reasoning Layer: RETRACTED Overcrowding (Headcount returned below safety threshold)")

                # If legacy events fired, capture confirmed genuine falls
                for leg_ev in legacy_events:
                    if leg_ev.status == IncidentStatus.CONFIRMED:
                        already_has_confirmed = any(
                            (isinstance(ev, dict) and ev.get("eval") and getattr(ev["eval"], "track_id", None) == leg_ev.track_id and ev.get("event_type", "fall") == "fall" and ev["eval"].incident_status == IncidentStatus.CONFIRMED) or
                            (not isinstance(ev, dict) and getattr(ev, "track_id", None) == leg_ev.track_id and getattr(ev, "status", None) == IncidentStatus.CONFIRMED)
                            for ev in all_detected_events
                        )
                        has_fall_evidence = any(
                            (getattr(e, 'status', None) == EvidenceStatus.SUPPORTED.value or getattr(e, 'state', None) == EvidenceState.SUPPORTED)
                            and any(kw in getattr(e, 'evidence_type', '').lower() for kw in ['velocity', 'collapse', 'posture', 'downward', 'ground'])
                            for e in getattr(leg_ev, 'evidence_items', [])
                        )
                        if not already_has_confirmed and (has_fall_evidence or leg_ev.evidence_score >= 0.70):
                            all_detected_events = [
                                ev for ev in all_detected_events
                                if not (
                                    (isinstance(ev, dict) and ev.get("eval") and getattr(ev["eval"], "track_id", None) == leg_ev.track_id and ev.get("event_type", "fall") == "fall" and ev["eval"].incident_status == IncidentStatus.RETRACTED) or
                                    (not isinstance(ev, dict) and getattr(ev, "track_id", None) == leg_ev.track_id and getattr(ev, "status", None) == IncidentStatus.RETRACTED)
                                )
                            ]
                            all_detected_events.append(leg_ev)
                            job["incidents_count"] = len(all_detected_events)
                            logger.info(f"Fall Detection Engine: CONFIRMED Fall Event registered for Track #{leg_ev.track_id} (Image={leg_ev.evidence_image_path})")

                # Update progress telemetry
                job["processed_frames"] = frame_idx
                job["progress_percent"] = round((frame_idx / max(1, total_frames)) * 100.0, 1)
                job["elapsed_time_sec"] = round(time.time() - job["start_time"], 2)

        except Exception as e:
            logger.exception(f"Error during video processing loop: {e}")
            job["status"] = "failed"
            job["error"] = str(e)
            cap.release()
            raise
        finally:
            cap.release()

        job["status"] = "completed"
        job["progress_percent"] = 100.0
        job["elapsed_time_sec"] = round(time.time() - job["start_time"], 2)

        # Persist detected incidents and evidence into PostgreSQL
        incident_responses = self._save_incidents_to_db(video_id, filename, all_detected_events, incident_reasoner, zone_config)

        result = VideoAnalysisResultResponse(
            video_id=video_id,
            filename=filename,
            total_frames=total_frames,
            fps=fps,
            duration_sec=round(duration_sec, 2),
            processed_at=datetime.now(timezone.utc),
            incidents=incident_responses,
            summary={
                "total_incidents": len(incident_responses),
                "confirmed_falls": sum(1 for inc in incident_responses if inc.event_type.lower() == "fall" and inc.status == IncidentStatus.CONFIRMED),
                "confirmed_intrusions": sum(1 for inc in incident_responses if inc.event_type.lower() == "intrusion" and inc.status == IncidentStatus.CONFIRMED),
                "confirmed_fights": sum(1 for inc in incident_responses if inc.event_type.lower() == "fight" and inc.status == IncidentStatus.CONFIRMED),
                "confirmed_crowd": sum(1 for inc in incident_responses if inc.event_type.lower() == "crowd" and inc.status == IncidentStatus.CONFIRMED),
                "retracted_events": sum(1 for inc in incident_responses if inc.status == IncidentStatus.RETRACTED),
                "processing_time_sec": job["elapsed_time_sec"],
                "model": "YOLO Pose Pretrained",
                "reasoning_engine": "SafeVision 3-State Multi-Event Temporal Reasoner"
            }
        )
        self._results[video_id] = result
        return result

    def _save_incidents_to_db(
        self,
        video_id: str,
        filename: str,
        events: List[Any],
        incident_reasoner: Optional[Any] = None,
        zone_config: Optional[Any] = None
    ) -> List[IncidentDetectionResponse]:
        """
        Saves detected incidents, entities, and evidence items into the PostgreSQL database.
        Supports all 4 safety event types: FALL, INTRUSION, FIGHT, CROWD.
        """
        incident_responses: List[IncidentDetectionResponse] = []
        db = None
        try:
            db = SessionLocal()
            
            # Find or create a default Camera record for uploaded video feeds
            camera = db.query(Camera).filter(Camera.camera_name == f"Upload-{filename}").first()
            if not camera:
                camera = Camera(
                    camera_name=f"Upload-{filename}",
                    location="Video Analysis Feed",
                    stream_url=f"/storage/videos/{filename}",
                    status=CameraStatus.ACTIVE
                )
                db.add(camera)
                db.commit()
                db.refresh(camera)

            # Ensure Zone record exists in DB for this camera if zone_config is provided
            if zone_config:
                try:
                    from backend.app.models.zone import Zone, ZoneType, RiskLevel
                    zone_rec = db.query(Zone).filter(Zone.camera_id == camera.camera_id).first()
                    if not zone_rec:
                        zone_rec = Zone(
                            camera_id=camera.camera_id,
                            zone_name=zone_config.zone_name,
                            zone_type=ZoneType.RESTRICTED,
                            polygon_coordinates=[{"x": p[0], "y": p[1]} for p in zone_config.polygon],
                            risk_level=RiskLevel.HIGH
                        )
                        db.add(zone_rec)
                        db.commit()
                except Exception as ze:
                    logger.warning(f"Zone registration note: {ze}")

            for ev_wrapper in events:
                # Handle both reasoned evaluation dict and legacy DetectedFallEvent
                if isinstance(ev_wrapper, dict) and "eval" in ev_wrapper:
                    reasoning_eval = ev_wrapper["eval"]
                    event_type_str = ev_wrapper.get("event_type", "fall")
                    ev_img_path = ev_wrapper.get("evidence_image_path")
                    track_id = getattr(reasoning_eval, "track_id", None)
                    participant_ids = list(reasoning_eval.involved_track_ids) if hasattr(reasoning_eval, "involved_track_ids") and reasoning_eval.involved_track_ids else None
                    if track_id is None and participant_ids:
                        track_id = participant_ids[0]
                    status = reasoning_eval.incident_status
                    confidence = reasoning_eval.evidence_score
                    risk_level = reasoning_eval.risk_level
                    timestamp_sec = reasoning_eval.timestamp_sec
                    is_evidence_complete = reasoning_eval.is_evidence_complete
                    should_alert = reasoning_eval.should_alert
                    alert_message = reasoning_eval.alert_message
                    temporal_trace = [s.to_dict() for s in reasoning_eval.temporal_evolution]
                    raw_evidence_items = reasoning_eval.evidence_items
                else:
                    ev = ev_wrapper
                    event_type_str = "fall"
                    ev_img_path = getattr(ev, "evidence_image_path", None)
                    track_id = ev.track_id
                    participant_ids = None
                    status = ev.status
                    confidence = ev.evidence_score
                    risk_level = getattr(ev, "risk_level", IncidentRiskLevel.HIGH)
                    timestamp_sec = ev.timestamp_sec
                    is_evidence_complete = (status == IncidentStatus.CONFIRMED)
                    should_alert = (status == IncidentStatus.CONFIRMED)
                    alert_message = f"Confirmed Fall Event detected at {timestamp_sec:.2f}s for Track #{track_id}."
                    temporal_trace = [s.to_dict() for s in incident_reasoner.get_or_create_tracker(track_id).get_evolution()] if incident_reasoner else []
                    raw_evidence_items = ev.evidence_items

                # Event type enum mapping
                if event_type_str == "intrusion":
                    event_type_enum = EventType.INTRUSION
                elif event_type_str == "fight":
                    event_type_enum = EventType.FIGHT
                elif event_type_str == "crowd":
                    event_type_enum = EventType.CROWD
                else:
                    event_type_enum = EventType.FALL

                # Create or find tracked entity (if track_id is present)
                entity_id = None
                if track_id is not None:
                    entity = db.query(TrackedEntity).filter(
                        TrackedEntity.camera_id == camera.camera_id,
                        TrackedEntity.track_id == track_id
                    ).first()
                    if not entity:
                        entity = TrackedEntity(
                            camera_id=camera.camera_id,
                            track_id=track_id,
                            first_seen=datetime.now(timezone.utc),
                            last_seen=datetime.now(timezone.utc)
                        )
                        db.add(entity)
                        db.commit()
                        db.refresh(entity)
                    entity_id = entity.entity_id

                # Create Incident
                incident = Incident(
                    camera_id=camera.camera_id,
                    event_type=event_type_enum,
                    entity_id=entity_id,
                    start_time=datetime.now(timezone.utc),
                    status=status,
                    confidence=confidence,
                    risk_level=risk_level
                )
                db.add(incident)
                db.commit()
                db.refresh(incident)

                # Create Evidence records (3-state logic)
                ev_items_response: List[EvidenceItemResponse] = []
                for ev_item in raw_evidence_items:
                    ev_type = ev_item.evidence_type
                    ev_desc = ev_item.description
                    ev_status_val = ev_item.state.value if hasattr(ev_item, "state") else ev_item.status
                    ev_conf = ev_item.confidence

                    evidence_record = Evidence(
                        incident_id=incident.incident_id,
                        evidence_type=ev_type,
                        description=ev_desc,
                        status=EvidenceStatus(ev_status_val),
                        confidence=ev_conf,
                        timestamp=datetime.now(timezone.utc)
                    )
                    db.add(evidence_record)
                    ev_items_response.append(EvidenceItemResponse(
                        evidence_type=ev_type,
                        description=ev_desc,
                        status=EvidenceStatus(ev_status_val),
                        confidence=ev_conf,
                        timestamp_sec=round(timestamp_sec, 2)
                    ))
                db.commit()

                # Evidence-Complete Alerting: ONLY generate Alert if should_alert is True!
                alert_id = None
                if should_alert:
                    severity = AlertSeverity.CRITICAL if risk_level == IncidentRiskLevel.CRITICAL else AlertSeverity.HIGH
                    alert_record = Alert(
                        incident_id=incident.incident_id,
                        severity=severity,
                        message=alert_message or f"Confirmed {event_type_str.upper()} Incident detected at {timestamp_sec:.2f}s."
                    )
                    db.add(alert_record)
                    db.commit()
                    db.refresh(alert_record)
                    alert_id = alert_record.alert_id

                mins = int(timestamp_sec // 60)
                secs = timestamp_sec % 60
                time_fmt = f"{mins:02d}:{secs:05.2f}"

                # Relative evidence image URL
                evidence_url = None
                if ev_img_path:
                    img_name = os.path.basename(ev_img_path)
                    evidence_url = f"/api/v1/evidence/{img_name}"

                incident_responses.append(IncidentDetectionResponse(
                    incident_id=incident.incident_id,
                    event_type=event_type_str.upper(),
                    track_id=track_id,
                    participant_ids=participant_ids,
                    timestamp_sec=round(timestamp_sec, 2),
                    timestamp_formatted=time_fmt,
                    status=status,
                    confidence=confidence,
                    risk_level=risk_level,
                    evidence_frame_url=evidence_url,
                    evidence_image_url=evidence_url,
                    evidence_items=ev_items_response,
                    is_evidence_complete=is_evidence_complete,
                    should_alert=should_alert,
                    alert_id=alert_id,
                    alert_message=alert_message,
                    temporal_trace=temporal_trace
                ))

        except Exception as db_err:
            logger.warning(f"Database write skipped or error: {db_err}")
            if not incident_responses:
                for ev_wrapper in events:
                    if isinstance(ev_wrapper, dict) and "eval" in ev_wrapper:
                        re = ev_wrapper["eval"]
                        ev_type_str = ev_wrapper.get("event_type", "fall")
                        ev_img_path = ev_wrapper.get("evidence_image_path")
                        t_sec = re.timestamp_sec
                        mins = int(t_sec // 60)
                        secs = t_sec % 60
                        time_fmt = f"{mins:02d}:{secs:05.2f}"
                        tr_id = getattr(re, "track_id", None)
                        if tr_id is None and hasattr(re, "involved_track_ids") and re.involved_track_ids:
                            tr_id = re.involved_track_ids[0]
                        ev_items_res = [
                            EvidenceItemResponse(
                                evidence_type=e.evidence_type,
                                description=e.description,
                                status=EvidenceStatus(e.state.value if hasattr(e, "state") else e.status),
                                confidence=e.confidence,
                                timestamp_sec=round(t_sec, 2)
                            )
                            for e in re.evidence_items
                        ]
                        ev_url = f"/api/v1/evidence/{os.path.basename(ev_img_path)}" if ev_img_path else None
                        incident_responses.append(IncidentDetectionResponse(
                            incident_id=None,
                            event_type=ev_type_str.upper(),
                            track_id=tr_id,
                            participant_ids=list(re.involved_track_ids) if hasattr(re, "involved_track_ids") and re.involved_track_ids else None,
                            timestamp_sec=round(t_sec, 2),
                            timestamp_formatted=time_fmt,
                            status=re.incident_status,
                            confidence=re.evidence_score,
                            risk_level=re.risk_level,
                            evidence_frame_url=ev_url,
                            evidence_image_url=ev_url,
                            evidence_items=ev_items_res,
                            is_evidence_complete=re.is_evidence_complete,
                            should_alert=re.should_alert,
                            alert_id=None,
                            alert_message=re.alert_message,
                            temporal_trace=[s.to_dict() for s in re.temporal_evolution]
                        ))
                    else:
                        ev = ev_wrapper
                        t_sec = ev.timestamp_sec
                        mins = int(t_sec // 60)
                        secs = t_sec % 60
                        time_fmt = f"{mins:02d}:{secs:05.2f}"
                        ev_url = None
                        if getattr(ev, "evidence_image_path", None):
                            ev_url = f"/api/v1/evidence/{os.path.basename(ev.evidence_image_path)}"

                        ev_items_res = [
                            EvidenceItemResponse(
                                evidence_type=e.evidence_type,
                                description=e.description,
                                status=EvidenceStatus(e.status),
                                confidence=e.confidence,
                                timestamp_sec=round(t_sec, 2)
                            )
                            for e in ev.evidence_items
                        ]
                        incident_responses.append(IncidentDetectionResponse(
                            incident_id=None,
                            event_type="FALL",
                            track_id=ev.track_id,
                            timestamp_sec=round(t_sec, 2),
                            timestamp_formatted=time_fmt,
                            status=ev.status,
                            confidence=ev.evidence_score,
                            risk_level=getattr(ev, "risk_level", IncidentRiskLevel.HIGH),
                            evidence_frame_url=ev_url,
                            evidence_image_url=ev_url,
                            evidence_items=ev_items_res,
                            is_evidence_complete=(ev.status == IncidentStatus.CONFIRMED),
                            should_alert=(ev.status == IncidentStatus.CONFIRMED),
                            alert_id=None,
                            alert_message=f"Confirmed Fall Event detected at {t_sec:.2f}s for Track #{ev.track_id}." if ev.status == IncidentStatus.CONFIRMED else None,
                            temporal_trace=[s.to_dict() for s in incident_reasoner.get_or_create_tracker(ev.track_id).get_evolution()] if incident_reasoner else []
                        ))
        finally:
            if db:
                db.close()

        return incident_responses


video_service = VideoProcessingManager()
