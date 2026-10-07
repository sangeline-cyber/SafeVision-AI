# SafeVision AI - Dataset Strategy & Benchmark Plan

## Dataset Architecture

SafeVision AI uses a structured dataset pipeline to train and evaluate the multi-stage vision models and 3-state evidence reasoning system.

## 1. External Benchmark Datasets (Planned)

### UCF-Crime
- **Focus**: Real-world surveillance anomalies, fights, assaults, and abrupt safety hazards.
- **Role in SafeVision**: Evaluation of the fighting and high-energy interaction evidence schemas.

### UR Fall Detection Dataset
- **Focus**: Indoor depth and RGB camera recordings of falls vs. activities of daily living (ADL).
- **Role in SafeVision**: Benchmarking posture transition velocities and separating falls from sitting/lying down.

### VIRAT Video Dataset
- **Focus**: Realistic high-resolution surveillance of natural outdoor activities, pedestrian paths, and vehicle interaction.
- **Role in SafeVision**: Multi-entity tracking continuity, zone transit dynamics, and benign background behavior calibration.

### UBnormal
- **Focus**: Open-set unnatural behaviors and atypical motions.
- **Role in SafeVision**: Stress-testing false positive resistance and open-set robustness.

---

## 2. SafeVision Scenario Dataset (Custom Benchmark)

To rigorously evaluate the 3-state evidence reasoner and eliminate false positives, a curated benchmark of paired normal and anomalous activities is scheduled:

| Category | Normal Control Activities | Safety Event Scenarios |
|---|---|---|
| **Posture Dynamics** | Standing, walking, sitting on bench/chair, bending to tie shoes, picking up dropped object | Uncontrolled fall backwards, slip-and-fall forwards, collapse with no recovery |
| **Perimeter & Transit** | Walking parallel to perimeter, regular door entry/exit, badge scanning | Crossing virtual restricted line, loitering inside prohibited equipment perimeter |
| **Social Interaction** | People talking, hugging, greeting, walking side-by-side, handshakes | Physical fighting, shoving, aggressive chasing |
| **Density & Traffic** | Regular transit queues, orderly boarding, normal lobby flow | Sudden bottleneck congestion, surge beyond square-meter threshold |

> **Compliance Note**: Datasets are not downloaded or trained during foundation phase. Data directories (`data/raw`, `data/processed`, `data/annotations`) are initialized with `.gitkeep` for version control.
