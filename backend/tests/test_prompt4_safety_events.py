"""
SafeVision AI - Prompt 4 Comprehensive Safety Events Test Suite
Tests:
1. Restricted-Zone Intrusion Reasoner (Dwell persistence, boundary math, lifecycle, evidence)
2. Fighting / Aggressive Activity Reasoner (Proximity, kinetic energy, sustained engagement, retraction)
3. Overcrowding Reasoner (Headcount threshold, persistence window, dispersal retraction)
"""

import pytest
import numpy as np

from backend.app.ai.tracking.person_tracker import TrackedPerson
from backend.app.ai.pose.yolo_pose_estimator import PersonPoseObservation
from backend.app.models.incident import IncidentStatus, IncidentRiskLevel
from backend.app.ai.reasoning.evidence_schema import (
    EvidenceState,
    IntrusionEvidenceCategory,
    FightEvidenceCategory,
    CrowdEvidenceCategory,
)
from backend.app.ai.reasoning.zone_intrusion_reasoner import (
    ZoneIntrusionReasoner,
    RestrictedZoneConfig,
    point_in_polygon,
    point_polygon_distance,
)
from backend.app.ai.reasoning.fighting_reasoner import (
    FightIncidentReasoner,
    FightReasonerConfig,
)
from backend.app.ai.reasoning.overcrowding_reasoner import (
    OvercrowdingReasoner,
    CrowdRegionConfig,
)


def _make_dummy_obs(
    bbox=(100.0, 100.0, 200.0, 300.0),
    centroid=(0.25, 0.35),
    torso_angle=80.0
) -> PersonPoseObservation:
    kpts = np.zeros((17, 3), dtype=np.float32)
    kpts[0] = [150, 120, 0.9]  # Nose
    kpts[5] = [130, 150, 0.9]  # L shoulder
    kpts[6] = [170, 150, 0.9]  # R shoulder
    kpts[11] = [140, 220, 0.9] # L hip
    kpts[12] = [160, 220, 0.9] # R hip
    kpts[15] = [140, 300, 0.9] # L ankle
    kpts[16] = [160, 300, 0.9] # R ankle

    w = float(bbox[2] - bbox[0])
    h = float(bbox[3] - bbox[1])

    return PersonPoseObservation(
        bbox=tuple(map(float, bbox)),
        normalized_bbox=(bbox[0]/640.0, bbox[1]/480.0, bbox[2]/640.0, bbox[3]/480.0),
        confidence=0.92,
        keypoints=kpts,
        torso_angle_deg=torso_angle,
        aspect_ratio_w_h=w / max(1.0, h),
        aspect_ratio_h_w=h / max(1.0, w),
        centroid=centroid,
        is_upright=True,
        is_prone=False
    )


def _create_person(track_id: int, obs: PersonPoseObservation, frame_idx: int = 1, timestamp_sec: float = 0.1) -> TrackedPerson:
    return TrackedPerson(track_id=track_id, initial_obs=obs, frame_idx=frame_idx, timestamp_sec=timestamp_sec)


# =====================================================================
# 1. RESTRICTED ZONE INTRUSION TESTS
# =====================================================================

class TestRestrictedZoneIntrusion:

    def test_point_in_polygon_and_distance_math(self):
        polygon = [(0.2, 0.2), (0.8, 0.2), (0.8, 0.8), (0.2, 0.8)]
        assert point_in_polygon(0.5, 0.5, polygon) is True
        assert point_in_polygon(0.1, 0.5, polygon) is False
        assert point_in_polygon(0.9, 0.9, polygon) is False

        # Distance calculation
        dist_inside = point_polygon_distance(0.5, 0.5, polygon)
        assert 0.25 <= dist_inside <= 0.35
        dist_outside = point_polygon_distance(0.1, 0.5, polygon)
        assert abs(dist_outside - 0.1) < 1e-4

    def test_single_frame_entry_does_not_alert(self):
        zone_config = RestrictedZoneConfig(
            polygon=[(0.2, 0.2), (0.8, 0.2), (0.8, 0.8), (0.2, 0.8)],
            min_dwell_frames=5
        )
        reasoner = ZoneIntrusionReasoner(zone_config=zone_config)

        # Person enters zone at frame 1: feet at (300, 300) in 600x600 -> norm (0.5, 0.5)
        obs = _make_dummy_obs(bbox=(250, 200, 350, 300))
        person = _create_person(1, obs, frame_idx=1, timestamp_sec=0.1)

        eval_res = reasoner.evaluate_person(person, frame_idx=1, timestamp_sec=0.1, frame_width=600, frame_height=600)

        # Must NOT alert on frame 1
        assert eval_res.should_alert is False
        assert eval_res.incident_status != IncidentStatus.CONFIRMED
        assert eval_res.dwell_frames == 1

    def test_sustained_dwell_confirms_and_alerts(self):
        min_dwell = 4
        zone_config = RestrictedZoneConfig(
            polygon=[(0.2, 0.2), (0.8, 0.2), (0.8, 0.8), (0.2, 0.8)],
            min_dwell_frames=min_dwell
        )
        reasoner = ZoneIntrusionReasoner(zone_config=zone_config)

        obs_init = _make_dummy_obs(bbox=(250, 200, 350, 300))
        person = _create_person(1, obs_init, frame_idx=1, timestamp_sec=0.1)

        last_eval = None
        for f in range(1, min_dwell + 2):
            obs = _make_dummy_obs(bbox=(250, 200, 350, 300))
            person.update(obs, frame_idx=f, timestamp_sec=f * 0.1)
            last_eval = reasoner.evaluate_person(person, frame_idx=f, timestamp_sec=f * 0.1, frame_width=600, frame_height=600)

        assert last_eval is not None
        assert last_eval.dwell_frames >= min_dwell
        assert last_eval.incident_status == IncidentStatus.CONFIRMED
        assert last_eval.is_evidence_complete is True
        assert last_eval.should_alert is True
        assert last_eval.alert_message is not None

        # Evidence verification
        evidence_dict = {e.evidence_type: e.state for e in last_eval.evidence_items}
        assert evidence_dict[IntrusionEvidenceCategory.ZONE_BOUNDARY_PROXIMITY.value] == EvidenceState.SUPPORTED
        assert evidence_dict[IntrusionEvidenceCategory.POLYGON_INTERSECTION.value] == EvidenceState.SUPPORTED
        assert evidence_dict[IntrusionEvidenceCategory.ZONE_DWELL_TIME.value] == EvidenceState.SUPPORTED
        assert evidence_dict[IntrusionEvidenceCategory.TEMPORAL_PERSISTENCE.value] == EvidenceState.SUPPORTED
        assert evidence_dict[IntrusionEvidenceCategory.ACTIVE_SCHEDULE_RESTRICTION.value] == EvidenceState.SUPPORTED

    def test_exit_retracts_intrusion(self):
        zone_config = RestrictedZoneConfig(
            polygon=[(0.2, 0.2), (0.8, 0.2), (0.8, 0.8), (0.2, 0.8)],
            min_dwell_frames=3
        )
        reasoner = ZoneIntrusionReasoner(zone_config=zone_config)

        obs_init = _make_dummy_obs(bbox=(250, 200, 350, 300))
        person = _create_person(1, obs_init, frame_idx=1, timestamp_sec=0.1)

        # Dwell inside to confirm
        for f in range(1, 4):
            obs = _make_dummy_obs(bbox=(250, 200, 350, 300))
            person.update(obs, frame_idx=f, timestamp_sec=f * 0.1)
            reasoner.evaluate_person(person, frame_idx=f, timestamp_sec=f * 0.1, frame_width=600, frame_height=600)

        # Step outside zone: feet at (50, 50) -> norm (0.08, 0.08)
        obs_outside = _make_dummy_obs(bbox=(30, 20, 70, 50))
        person.update(obs_outside, frame_idx=4, timestamp_sec=0.4)
        retract_eval = reasoner.evaluate_person(person, frame_idx=4, timestamp_sec=0.4, frame_width=600, frame_height=600)

        assert retract_eval.incident_status == IncidentStatus.RETRACTED
        assert retract_eval.should_alert is False


# =====================================================================
# 2. FIGHTING / AGGRESSIVE ACTIVITY TESTS
# =====================================================================

class TestFightingReasoner:

    def test_single_person_yields_no_altercation(self):
        reasoner = FightIncidentReasoner()
        obs1 = _make_dummy_obs(bbox=(100, 100, 200, 250))
        p1 = _create_person(1, obs1)

        evals = reasoner.evaluate_scene([p1], frame_idx=1, timestamp_sec=0.1)
        assert len(evals) == 0

    def test_far_apart_people_yield_no_altercation(self):
        reasoner = FightIncidentReasoner()
        # Far centroids
        obs1 = _make_dummy_obs(bbox=(10, 10, 50, 100), centroid=(0.05, 0.1))
        obs2 = _make_dummy_obs(bbox=(500, 500, 550, 600), centroid=(0.85, 0.9))
        p1 = _create_person(1, obs1)
        p2 = _create_person(2, obs2)

        evals = reasoner.evaluate_scene([p1, p2], frame_idx=1, timestamp_sec=0.1)
        assert len(evals) == 0

    def test_sustained_violent_altercation_confirms_and_alerts(self):
        config = FightReasonerConfig(
            proximity_threshold_norm=0.40,
            kinetic_velocity_threshold=0.15,
            min_engagement_frames=4
        )
        reasoner = FightIncidentReasoner(config=config)

        obs1_init = _make_dummy_obs(bbox=(100, 100, 180, 250), centroid=(0.25, 0.35))
        obs2_init = _make_dummy_obs(bbox=(120, 100, 200, 250), centroid=(0.28, 0.35))
        p1 = _create_person(1, obs1_init, frame_idx=1, timestamp_sec=0.1)
        p2 = _create_person(2, obs2_init, frame_idx=1, timestamp_sec=0.1)

        last_eval = None
        for f in range(1, 6):
            sign = 1 if f % 2 == 0 else -1
            # Mutually overlapping boxes and moving centroids
            c1_x = 0.25 + sign * 0.05
            c2_x = 0.28 - sign * 0.05
            obs1 = _make_dummy_obs(bbox=(100, 100, 180, 250), centroid=(c1_x, 0.35))
            obs2 = _make_dummy_obs(bbox=(120, 100, 200, 250), centroid=(c2_x, 0.35))
            p1.update(obs1, frame_idx=f, timestamp_sec=f * 0.1)
            p2.update(obs2, frame_idx=f, timestamp_sec=f * 0.1)

            evals = reasoner.evaluate_scene([p1, p2], frame_idx=f, timestamp_sec=f * 0.1)
            if evals:
                last_eval = evals[0]

        assert last_eval is not None
        assert last_eval.incident_status == IncidentStatus.CONFIRMED
        assert last_eval.is_evidence_complete is True
        assert last_eval.should_alert is True
        assert last_eval.alert_message is not None
        assert 1 in last_eval.involved_track_ids
        assert 2 in last_eval.involved_track_ids

        # 5-point evidence checklist
        states = {e.evidence_type: e.state for e in last_eval.evidence_items}
        assert states[FightEvidenceCategory.MULTI_PERSON_PROXIMITY.value] == EvidenceState.SUPPORTED
        assert states[FightEvidenceCategory.MUTUAL_INTERACTION_DYNAMICS.value] == EvidenceState.SUPPORTED
        assert states[FightEvidenceCategory.HIGH_KINETIC_MOTION.value] == EvidenceState.SUPPORTED
        assert states[FightEvidenceCategory.SUSTAINED_ENGAGEMENT.value] == EvidenceState.SUPPORTED
        assert states[FightEvidenceCategory.TEMPORAL_CONSISTENCY.value] == EvidenceState.SUPPORTED

    def test_separation_retracts_altercation(self):
        config = FightReasonerConfig(proximity_threshold_norm=0.40, min_engagement_frames=3)
        reasoner = FightIncidentReasoner(config=config)

        obs1_init = _make_dummy_obs(bbox=(100, 100, 180, 250), centroid=(0.25, 0.35))
        obs2_init = _make_dummy_obs(bbox=(120, 100, 200, 250), centroid=(0.28, 0.35))
        p1 = _create_person(1, obs1_init, frame_idx=1, timestamp_sec=0.1)
        p2 = _create_person(2, obs2_init, frame_idx=1, timestamp_sec=0.1)

        # Confirm fight
        for f in range(1, 5):
            sign = 1 if f % 2 == 0 else -1
            obs1 = _make_dummy_obs(bbox=(100, 100, 180, 250), centroid=(0.25 + sign * 0.05, 0.35))
            obs2 = _make_dummy_obs(bbox=(120, 100, 200, 250), centroid=(0.28 - sign * 0.05, 0.35))
            p1.update(obs1, frame_idx=f, timestamp_sec=f * 0.1)
            p2.update(obs2, frame_idx=f, timestamp_sec=f * 0.1)
            reasoner.evaluate_scene([p1, p2], frame_idx=f, timestamp_sec=f * 0.1)

        # Persons separate far away
        obs1_sep = _make_dummy_obs(bbox=(10, 10, 50, 100), centroid=(0.05, 0.05))
        obs2_sep = _make_dummy_obs(bbox=(500, 500, 550, 600), centroid=(0.85, 0.85))
        p1.update(obs1_sep, frame_idx=5, timestamp_sec=0.5)
        p2.update(obs2_sep, frame_idx=5, timestamp_sec=0.5)

        sep_evals = reasoner.evaluate_scene([p1, p2], frame_idx=5, timestamp_sec=0.5)
        assert len(sep_evals) > 0
        assert sep_evals[0].incident_status == IncidentStatus.RETRACTED
        assert sep_evals[0].should_alert is False


# =====================================================================
# 3. OVERCROWDING TESTS
# =====================================================================

class TestOvercrowdingReasoner:

    def test_headcount_below_capacity_does_not_alert(self):
        config = CrowdRegionConfig(capacity_threshold=3, min_persistence_frames=4)
        reasoner = OvercrowdingReasoner(config=config)

        # 2 people (threshold 3)
        tracks = []
        for i in range(2):
            obs = _make_dummy_obs(bbox=(100 * i, 100, 100 * i + 80, 250))
            p = _create_person(i + 1, obs, frame_idx=1, timestamp_sec=0.1)
            tracks.append(p)

        eval_res = reasoner.evaluate_crowd(tracks, frame_idx=1, timestamp_sec=0.1)
        assert eval_res is None or eval_res.should_alert is False

    def test_brief_surge_does_not_alert(self):
        threshold = 2
        min_persistence = 5
        config = CrowdRegionConfig(capacity_threshold=threshold, min_persistence_frames=min_persistence)
        reasoner = OvercrowdingReasoner(config=config)

        # 4 people on frame 1 (surge above threshold 2)
        tracks = []
        for i in range(4):
            obs = _make_dummy_obs(bbox=(50 * i, 50, 50 * i + 40, 150))
            p = _create_person(i + 1, obs, frame_idx=1, timestamp_sec=0.1)
            tracks.append(p)

        eval_res = reasoner.evaluate_crowd(tracks, frame_idx=1, timestamp_sec=0.1)
        assert eval_res is not None
        assert eval_res.incident_status != IncidentStatus.CONFIRMED
        assert eval_res.should_alert is False
        assert eval_res.dwell_frames == 1

    def test_sustained_overcrowding_confirms_and_alerts(self):
        threshold = 2
        min_persistence = 4
        config = CrowdRegionConfig(capacity_threshold=threshold, min_persistence_frames=min_persistence)
        reasoner = OvercrowdingReasoner(config=config)

        last_eval = None
        for f in range(1, min_persistence + 2):
            tracks = []
            for i in range(4):  # 4 people continuously
                obs = _make_dummy_obs(bbox=(50 * i, 50, 50 * i + 40, 150))
                p = _create_person(i + 1, obs, frame_idx=f, timestamp_sec=f * 0.1)
                tracks.append(p)
            last_eval = reasoner.evaluate_crowd(tracks, frame_idx=f, timestamp_sec=f * 0.1)

        assert last_eval is not None
        assert last_eval.incident_status == IncidentStatus.CONFIRMED
        assert last_eval.is_evidence_complete is True
        assert last_eval.should_alert is True
        assert last_eval.current_count == 4
        assert last_eval.threshold == threshold
        assert last_eval.alert_message is not None

        # 5-point evidence checklist
        states = {e.evidence_type: e.state for e in last_eval.evidence_items}
        assert states[CrowdEvidenceCategory.HEADCOUNT_THRESHOLD_EXCEEDED.value] == EvidenceState.SUPPORTED
        assert states[CrowdEvidenceCategory.SPATIAL_DENSITY_CONCENTRATION.value] == EvidenceState.SUPPORTED
        assert states[CrowdEvidenceCategory.SUSTAINED_CROWD_PRESENCE.value] == EvidenceState.SUPPORTED
        assert states[CrowdEvidenceCategory.INFLOW_RATE_ACCUMULATION.value] == EvidenceState.SUPPORTED
        assert states[CrowdEvidenceCategory.TEMPORAL_CONSISTENCY.value] == EvidenceState.SUPPORTED

    def test_crowd_dispersal_retracts_overcrowding(self):
        threshold = 2
        min_persistence = 3
        config = CrowdRegionConfig(capacity_threshold=threshold, min_persistence_frames=min_persistence)
        reasoner = OvercrowdingReasoner(config=config)

        # Confirm overcrowding
        for f in range(1, 5):
            tracks = []
            for i in range(4):
                obs = _make_dummy_obs(bbox=(50 * i, 50, 50 * i + 40, 150))
                p = _create_person(i + 1, obs, frame_idx=f, timestamp_sec=f * 0.1)
                tracks.append(p)
            reasoner.evaluate_crowd(tracks, frame_idx=f, timestamp_sec=f * 0.1)

        # Disperse crowd to 1 person (below threshold 2)
        obs_disp = _make_dummy_obs(bbox=(50, 50, 90, 150))
        tracks_dispersed = [_create_person(1, obs_disp, frame_idx=5, timestamp_sec=0.5)]

        dispersal_eval = reasoner.evaluate_crowd(tracks_dispersed, frame_idx=5, timestamp_sec=0.5)
        assert dispersal_eval is not None
        assert dispersal_eval.incident_status == IncidentStatus.RETRACTED
        assert dispersal_eval.should_alert is False
