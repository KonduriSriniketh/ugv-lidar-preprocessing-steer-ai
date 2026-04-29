# Audit

Cross-bag and static-analysis artifacts produced during the debugging of
this package. Kept here so the methodology is reproducible alongside the
fixes themselves.

## Contents

- `findings.md` — static-review findings: defects flagged from a top-to-bottom
  read of the codebase after the runtime-loud bugs were already fixed.
- `notes/cross_bag_audit.md` — per-bag report from running `run_audit.py`
  over all 16 supplied bags.
- `notes/key_findings.md` — synthesis of the cross-bag report. Highlights
  dataset-level properties (g-units IMU, missing rear-left IMU, stationary
  windows) that affect grading even though they are not bugs in this code.
- `scripts/bag_parser.py` — pure-Python ROS1 bag V2.0 parser. Stdlib only;
  no `pip install rosbag` needed. Used because the audit shell did not have
  ROS or pip available.
- `scripts/run_audit.py` — driver that walks a directory of `.bag` files,
  parses each one with `bag_parser`, and emits a structured Markdown report.

## Reproducing the audit

```bash
cd <package_root>/audit/scripts
python3 run_audit.py > ../notes/cross_bag_audit.md
```

Expects bags at `/home/<user>/bags/`. Adjust the path inside `run_audit.py`
if your layout differs.

## How the audit fits into the debugging story

These artifacts were produced after the loud runtime bugs (build, plugin
chain, calibration gate, gravity-TF publication, frame_id, plugin XML,
buffer_size, gravity-TF rotation direction) were already isolated and
fixed. The static review surfaced three quieter integrator defects in the
deskew path (sort direction, reference_index off-by-one, state-persistence
guard). The cross-bag run surfaced dataset-level properties (see
`notes/key_findings.md`) that are documented but intentionally not patched
in this submission.
