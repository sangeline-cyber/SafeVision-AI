# SafeVision AI - Dataset Directory Structure

This directory stores datasets and metadata for the SafeVision AI project: Context-Aware Autonomous Safety Event Detection and Evidence Verification System (HNX26PSI07).

## Directory Organization

```
data/
├── raw/            # Unprocessed external benchmark video clips and feeds
├── processed/      # Normalized, extracted frames, bounding boxes, trajectories
└── annotations/    # Ground-truth event labels, zone polygons, and temporal evidence spans
```

## Dataset Strategy

### 1. External Benchmark Datasets (Planned)
- **UCF-Crime**: Surveillance anomaly examples, fight scenarios, abnormal safety events.
- **UR Fall Detection Dataset**: Fall incidents across diverse camera angles vs. daily living activities (ADL).
- **VIRAT**: Real-world realistic normal surveillance activity, complex multi-entity interaction, contextual behaviour.
- **UBnormal**: Open-set evaluation and unnatural behaviour benchmark.

### 2. SafeVision Scenario Dataset (Custom Controlled Set)
Controlled recordings designed to evaluate our 3-state evidence reasoning and prevent false positives from everyday activities:
- **Normal Activities**: Standing, walking, sitting, waiting, talking, bending/tying shoes, phone usage, regular entry/exit.
- **Safety Events**: Simulated falls with recovery vs non-recovery, restricted-zone perimeter violations, controlled aggression, high-density queue/crowd accumulation.

> **Note**: Datasets are not downloaded automatically during initial repository setup. Raw video assets are omitted from source control via `.gitignore`.
