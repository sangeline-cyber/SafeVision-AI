# SafeVision AI - Evidence Reasoning Engine Specification

## Overview
The **Evidence Reasoning Engine** is the core decision component of SafeVision AI. It maps raw computer vision measurements into structured evidence observations and evaluates incident lifecycles without relying on black-box heuristics or single-frame triggers.

## 3-State Evidence Logic

Traditional vision systems use binary flags (`true`/`false`), which leads to fatal false negatives under occlusion. SafeVision AI implements ternary Kleene logic:

| State | Definition | Example Scenario |
|---|---|---|
| `SUPPORTED` | Observable physical evidence confirms requirement | Torso angle shifted from vertical (85°) to horizontal (12°) |
| `CONTRADICTED` | Physical observation contradicts requirement | Entity velocity remains at walking speed (1.2 m/s) with upright spine |
| `UNKNOWN` | Keypoints or bounding box obscured by foreground object | Lower limbs blocked by a desk or pallet; state held neutral |

---

## 4 MVP Safety Event Schemas

### 1. Fall / Person Down
1. **Person Detected**: High-confidence bounding box from YOLO.
2. **Previously Upright**: Bounding box height-to-width ratio $H/W > 1.4$ for preceding $N$ frames.
3. **Downward Velocity**: Center-of-mass vertical descent velocity exceeds $V_{fall}$.
4. **Posture Transition**: Torso vector angle drops below $30^\circ$ relative to ground plane.
5. **Ground-Level Posture**: Inverted aspect ratio ($W/H > 1.2$) located near floor plane.
6. **Persistence**: Entity remains at ground level for $T_{persist} \ge 2.5\text{s}$.
7. **Recovery Check**: If person stands back up during verification window, incident moves to `RETRACTED`.

### 2. Restricted-Zone Intrusion
1. **Entity Identification**: Persistent track ID from ByteTrack.
2. **Boundary Crossing**: Entity centroid or bottom keypoint intersects polygon boundary.
3. **Direction of Crossing**: Velocity vector normal points inward toward restricted zone.
4. **Duration Inside Zone**: Time elapsed inside perimeter exceeds dwell threshold $T_{dwell}$.
5. **Zone Context**: Active schedule and classification (e.g., Hazardous Equipment Zone).

### 3. Fighting / Aggressive Activity
1. **Multiple Entities**: $\ge 2$ tracked individuals within interaction distance ($d < 1.5\text{m}$).
2. **Spatial Interaction**: Overlapping bounding boxes or high interaction graph affinity.
3. **High-Energy Movement**: High optical flow kinetic energy and sudden acceleration peaks.
4. **Temporal Persistence**: Aggressive interaction sustained for duration $T_{fight} > 2.0\text{s}$.

### 4. Crowd / Overcrowding
1. **Entity Count**: Cumulative count of detected people in designated zone.
2. **Spatial Concentration**: Density (people per square meter) exceeds capacity limit.
3. **Temporal Growth Rate**: Inflow rate positive and sustained over observation window.
4. **Bottleneck Dwell**: Mean transit velocity within zone drops below normal flow threshold.
