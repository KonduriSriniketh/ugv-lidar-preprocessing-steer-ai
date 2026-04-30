# Debugging notes

This document describes the methodology I used to find and fix the
defects in this package, the tools I used along the way, the use of
an LLM as a debugging partner, and a few math derivations that
weren't obvious from the code alone.

## Methodology overview

I worked in three tiers, each driven by what the running pipeline
showed me.

**Tier 1 — Runtime triage.** Build the package, launch it, play a
bag, watch the logs and RViz. Each loud failure (compile error,
log warning, missing topic, visible RViz mismatch) pointed at a
specific defect. For each one I formed a hypothesis, located the
relevant code, applied the smallest possible patch, and verified
with an A/B test before moving to the next failure. This pass found
ten of the thirteen committed bugs.

**Tier 2 — Code-review pass.** Once the runtime-loud failures were
gone, I went back through the deskew plugin and the IMU integrator
(the most non-obvious part of the pipeline) looking for quieter
defects that might not produce a clear visible signal on the
supplied bags. Three candidates emerged in
`pointcloud_deskew_plugin.cpp` and the sort step in the nodelet.
I validated each experimentally with `dynamic_reconfigure` A/B
tests on bags `_6` (stationary) and `_7` (4.6 m/s motion) before
committing.

**Tier 3 — Cross-bag audit.** Independent of fixes, I wrote a
stdlib-only Python parser for ROS1 V2.0 bag files and ran it over
all 16 supplied bags to surface dataset-level properties that
might affect grading even though they are not bugs in this code.
Six findings (`F1`–`F6`) are documented in
`audit/notes/key_findings.md` and summarised at the end of
`BUGS.md`.

The discipline that made each commit causal rather than
coincidental was the **A/B verification step**: revert the fix,
observe the broken state, re-apply, observe the restored state.
Done for every fix in Tier 1 and 2.

## Tools used

- **catkin / cmake** — building the package; surfaced bug #1.
- **roslaunch / nodelet manager** — launching the pipeline;
  startup logs surfaced bugs #2, #3, #4, #5, #6.
- **rosbag play (with `--clock`)** — reproducing test scenarios.
- **rostopic** — verifying topic names, rates, and message
  contents (`hz`, `echo -n1`, `info`).
- **rosrun tf tf_echo** — verifying TF transforms; surfaced bug
  #6, confirmed bug #10's fix.
- **rqt / dynamic_reconfigure dynparam** — runtime A/B toggles
  for every plugin in the chain; the validation harness for
  bugs #11, #12, #13 and the optional filters.
- **RViz** — visual A/B between raw and processed clouds;
  surfaced bug #7 (frame_id mismatch) and bug #10 (doubled
  rotation at distance).
- **Custom Python ROS1 bag parser** — see `audit/scripts/`.
  Pure stdlib, used because the audit shell didn't have ROS or
  pip available. Drives the cross-bag analysis.
- **Docker** — sandbox for the build/run environment;
  Dockerfile additions in commit `d79ba7d` made the runtime
  environment reproducible (the starter shipped only the
  build-side packages).
- **Claude Code (LLM)** — pair-debugging partner, see below for
  the specific roles.

## Use of an LLM as a debugging partner

I used Claude Code throughout this work as a pair-debugging
partner. The split of responsibilities was specific, and I think
worth describing in detail because it affects how to read this
submission.

**What the LLM did**

- **Code comprehension.** When I encountered a symptom, the LLM
  helped me locate the relevant section of code quickly,
  particularly in the IMU integrator and plugin chain — files I
  hadn't seen before.
- **Cross-checking math against canonical sources.** For the
  gravity-alignment TF (bug #10), the LLM walked me through ROS
  TF parent/child semantics from first principles so I could
  derive *why* the conjugate is the correct rotation rather than
  taking the answer on faith. For the IMU integrator, it
  cross-checked the quaternion derivative formula against the
  Hamilton body-frame convention and the position/velocity
  Taylor expansion against the standard `(1/6)·j·dt³` jerk
  term.
- **Generating helper tooling.** The Python ROS1 bag parser in
  `audit/scripts/bag_parser.py` was drafted by the LLM after I
  asked for a way to inspect bag contents without installing
  ROS or pip in the audit shell.
- **Drafting prose.** Commit messages, this document, and
  `BUGS.md` / `REPRODUCTION.md` were drafted with LLM
  assistance and edited by me. The fix code itself is mine.

**What I did**

- **Drove the runtime test loop.** Decided which bag to play,
  which RViz frame to use, which dynparam toggle to flip,
  which log to watch. The LLM never had access to the running
  pipeline — only my reports of what it produced.
- **Empirical A/B verification of every fix.** Before
  committing, I reverted each candidate fix, confirmed the
  broken state matched the original symptom, then re-applied
  and confirmed the symptom was gone. This is the discipline
  that ensures each commit is causal.
- **Rejected unsafe edits.** A few times the LLM proposed
  edits I declined as too aggressive (e.g. an early proposal
  for bug #6 that would have left the lookup-and-compose
  machinery in place "for safety"; I asked for the lookup to
  be removed entirely instead, since it could never succeed
  with the bag's TF tree).
- **Identified the README invariant violation (#9)
  independently.** This is the one bug I noticed by re-reading
  the README contract before the LLM had flagged it.
- **Cross-bag testing across all 16 bags.** Ran the audit
  myself, interpreted the per-bag report, and decided which
  findings (`F1`–`F6`) were dataset properties versus
  candidate bugs.
- **Visual validation in RViz.** All the red-vs-green overlay
  tests, the doubled-rotation observation that surfaced bug
  #10, and the dynparam A/B for the deskew bugs — all
  human-driven; the LLM never saw a frame.
- **Made integration decisions.** The decision to leave bug
  #14 documented rather than patched, the decision to
  document `F2` (g-units) rather than fix it, the decision to
  scope all fixes to minimal diffs — all mine.

**Why I'm being explicit about this**

A skim of the commit history could mistakenly imply that the
work was either purely human or purely LLM-generated. Neither is
accurate. The work was a tight loop where I drove the runtime
investigation and the LLM accelerated parts that benefited from
fast code lookup or first-principles derivation. The fix
*decisions* and the *empirical verification* were mine; the LLM
helped me get to the fix faster than I would have alone.

## Math derivation: why bug #10 needed the conjugate

The gravity_align plugin computes a unit quaternion `q_align`
that rotates the lidar's measured gravity direction onto world
+Z, then applies that rotation to every point of the cloud:

```
P_gravity = R_align · P_lidar              … (1)
```

where `R_align` is the rotation matrix corresponding to
`q_align`, and the cloud is published with
`frame_id = lidar_gravity_frame`.

The TF system stores transforms with the convention:

```
P_parent = R_msg · P_child + t_msg         … (2)
```

`R_msg` is the rotation in the `geometry_msgs/Transform` field.
For our gravity TF, parent = `lidar_frame` and child =
`gravity_frame`.

A consumer (RViz, downstream node) has `P_gravity` and wants
`P_lidar`. Solving (1):

```
P_lidar = R_align⁻¹ · P_gravity
```

Substituting into (2) with `t_msg = 0` (origin shared, only
rotation):

```
P_lidar = R_msg · P_gravity
```

So `R_msg = R_align⁻¹`. For a unit quaternion the inverse equals
the conjugate (`q⁻¹ = q* / |q|² = q*` when `|q| = 1`), so:

```cpp
tf_q = align_q.conjugate();
```

The original code stored `align_q` itself. The downstream effect
was that consumers computing `P_lidar` from `P_gravity` got:

```
P_displayed = R_align · P_gravity = R_align · (R_align · P_lidar)
            = R_align² · P_lidar
```

A **doubled rotation** rather than the inverse — exactly the
fingerprint I saw in RViz: a vertical gap that grew linearly
with range (≈ 35 cm at 10 m for a 2° mount offset, ≈ 70 cm at
20 m). The empirical A/B that confirmed the diagnosis was
reverting `conjugate()` and observing the gap, then restoring
and observing it collapse to zero.

## Audit summary

The cross-bag audit (see `audit/`) ran a stdlib-only Python
parser over all 16 supplied bags and surfaced six dataset-level
findings beyond the code bugs above:

- **F1.** `livox_rear_left` has no IMU on any of the 16 bags —
  preprocessor would refuse to start if pointed at this lidar.
- **F2.** All Livox IMUs publish accelerations in **g-units**
  (≈ 1.0 at rest), not m/s². This is a Livox driver convention.
  Consequence: translational deskew is ~9.81× weaker than
  intended because the integrator interprets g-unit accel as
  m/s². Rotational deskew is unaffected. Documented but not
  patched: a unit-conversion fix touches calibration semantics
  and is outside the assignment's scope.
- **F3.** Bags `_0` / `_1` / `_2` are 100% stationary; later
  bags are mostly motion. Drives the "chain stationary first"
  recommendation in `REPRODUCTION.md`.
- **F4.** `livox_right` IMU has multi-second gaps in moving
  bags `_4` / `_5` — sensor-side issue.
- **F5.** `livox_rear_right` has unusually high gyro bias
  (~10°/s) — absorbed by calibration on stationary bags.
- **F6.** Primary `/odom` topic has `frame_id: nbuggy/map` but
  represents pose-in-map; cosmetic, doesn't affect the
  pipeline's consumption.

Findings are summarised in `BUGS.md` and detailed in
`audit/notes/key_findings.md`. The static re-read findings
(P0/P1/P2 from the code review pass) are in `audit/findings.md`.

## What I deliberately left undone

- **Bug #14 (publish-skip during calibration).** Documented in
  `BUGS.md` Tier 3. The README does not specify the contract
  for this window, and the conservative behaviour is reasonable.
  Patching to "raw passthrough during calibration" changes the
  semantics of `points_processed` in a way that could surprise
  downstream consumers. Left for explicit discussion rather
  than silent change.
- **F2 (g-units IMU).** Translational deskew is ~10× under-scaled
  because the IMU publishes g-units. A YAML scale-matrix
  override or a one-line conversion in `imu_callback` would
  fix it, but both have downstream calibration consequences
  the assignment scope doesn't justify investigating. Visible
  in this submission as: deskew gives perfect rotational
  correction but only partial translational correction at
  speed.
- **P1 in audit `findings.md`** (the `time_offset` shift in
  `filter_points_by_imu_coverage`). Doesn't affect the
  supplied Livox dataset; would matter for a Velodyne dataset
  or a Livox driver that timestamps at end-of-scan. One-line
  fix with semantic implications — left out of the
  defect-fix scope.
- **P2 items in audit `findings.md`** (variable naming,
  default-value mismatches, missing WARN logs). Code smell,
  not defects.

## Acknowledgments

- The DLIO codebase (Direct LiDAR-Inertial Odometry) — origin
  of the IMU integrator math used by this package. Cross-checking
  formulas against DLIO confirmed the integrator math is correct
  and isolated the defects to the deskew/sort/state-persistence
  layer.
- Livox SDK documentation — for the tag-byte semantics used by
  the `LivoxTagFilter` plugin and the g-unit IMU convention
  noted in F2.
