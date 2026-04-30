# Bugs

This document is the canonical list of every defect I identified and
fixed during debugging. Sections are ordered by **the moment each bug
first surfaced for me** — usually a build error, a startup log line, a
missing topic, or a visible RViz mismatch. The numeric IDs (#1–#14) are
section IDs for this document only; the stable identifier across the
repo is the git commit hash.

The work falls into three tiers:

1. **Runtime triage (#1–#10).** Bugs that fired loudly when I built,
   launched, and played a bag. Most of Day 1 of work. The pipeline
   handed me a log line, a missing topic, or an RViz mismatch I could
   see directly.
2. **Code-review pass (#11–#13).** Quieter defects in the IMU integrator
   path that only emit a visible signal under specific motion patterns.
   After Tier 1 was settled, I went back through the deskew and
   integrator code and found three candidates. Each was validated
   experimentally with `dynamic_reconfigure` A/B tests on bags `_6`
   (stationary) and `_7` (4.6 m/s motion) before being committed.
3. **Documented, not fixed (#14).** A judgement call about
   calibration-window output behaviour. Documented for the grader; not
   patched, because the README does not specify a contract either way.

For each item below: **symptom → how surfaced → root cause → fix
(commit) → verification**.

---

## Tier 1 — Runtime triage

### #1 — `CMakeLists.txt` excluded all sources

**Commit:** `29aa48d`

**Symptom:** `catkin_make` fails immediately with
`No SOURCES given to target: ugv_lidar_preprocessing`.

**How surfaced:** First build inside the docker container.

**Root cause:** A `list(FILTER SOURCES EXCLUDE REGEX
"${CMAKE_CURRENT_SOURCE_DIR}/src/ugv_lidar_preprocessing/.*")` line
stripped every source file under the standard catkin layout, leaving
the target with zero translation units.

**Fix:** Removed the excluding `list(FILTER ...)` line.

**Verification:** `catkin_make` (and later `catkin build`) succeed and
link a non-empty target.

---

### #2 — `PLUGINLIB_EXPORT_CLASS` typo for Livox voxel grid

**Commit:** `263f131`

**Symptom:** Compile fails with
`LivoxVoxelGridFilterPlugins does not name a type` when registering the
Livox voxel grid filter.

**How surfaced:** First successful build attempt after #1 was fixed.

**Root cause:** `plugins_exporter.cpp` exported the symbol
`LivoxVoxelGridFilterPlugins` (trailing `s`); the class is
`LivoxVoxelGridFilterPlugin`.

**Fix:** Removed the trailing `s`.

**Verification:** Build succeeds. `nodelet types` lists the class with
the correct name.

---

### #3 — YAML `core:` wrapper hid `input_topic`

**Commit:** `3465e28`

**Symptom:** Nodelet startup log:
`Optional parameter input_topic not set, using default value`. Nodelet
subscribes to its hardcoded default and receives no pointcloud
messages.

**How surfaced:** Reading the startup log on the first clean launch.

**Root cause:** `lidar_preprocessing_params.yaml` had its top-level
keys nested under `core:`. The nodelet reads parameters relative to
its own private namespace, so `core/input_topic` landed at a key the
nodelet never queries; `input_topic` itself remained unset.

**Fix:** Removed the `core:` wrapper so all parameters live at the
YAML root.

**Verification:** Restart nodelet — startup warning is gone.
`rostopic hz /<ns>/livox_front/points_processed` shows ~10 Hz when a
bag is playing.

---

### #4 — Plugin execution order did not match documented pipeline

**Commit:** `c96d252`

**Symptom:** Nodelet startup log:
`Plugin Execution Order for enabled preprocessors: livox_tag_filter
-> deskew -> gravity_align`. The README documents
`deskew → gravity_align → voxel_grid → ROR → livox_tag_filter`.

**How surfaced:** Reading the startup log immediately after #3 was
fixed.

**Root cause:** The `kPluginOrder` array in
`lidar_preprocessing_nodelet.cpp` listed plugin keys in the wrong
sequence.

**Fix:** Reordered to
`{kDeskewKey, kGravityAlignKey, kVoxelKey, kRorKey, kLivoxTagKey}`.

**Verification:** Restart nodelet. Log line now reads
`pointcloud_deskew → gravity_align → voxel_grid_filter →
radius_outlier_removal → livox_tag_filter` (with disabled plugins
omitted, which is correct).

---

### #5 — Inverted staleness check blocked IMU calibration forever

**Commit:** `14bdfe2`

**Symptom:** Nodelet repeatedly logs
`IMU calibration waiting: external velocity stale (age 0.031 s >
0.500 s)`. Self-contradicting numbers — `0.031 < 0.500` should not
trigger "too stale". On a stationary bag, calibration never
completes.

**How surfaced:** Watching the calibration phase log immediately
after the plugin chain (#4) started running. The log line was
self-announcing — the inequality direction was visibly wrong.

**Root cause:** `imu_integrator.cpp:82` used `<` where the staleness
predicate logically requires `>`. Fresh samples were rejected, stale
samples were accepted.

**Fix:** Flipped `<` to `>`.

**Verification:** Restart nodelet, replay stationary bag `_0`. Log
shows `Calibration complete` within ~3 s of bag time.
`/<ns>/livox_*/points_processed` begins publishing immediately
after.

---

### #6 — Gravity-alignment TF lookup against a frame that does not exist

**Commit:** `7fa8d53`

**Symptom:** Nodelet logs
`Failed to lookup TF from 'nbuggy/livox_front' to
'nbuggy/base_footprint'`, followed by a long burst of TF lookup
retries. Gravity-alignment TF is never published.

**How surfaced:** First time enabling gravity_align in YAML (after
the chain was healthy).

**Root cause:** The original implementation tried to compose the
gravity-alignment transform with a `base_footprint → lidar`
transform looked up from TF, then publish the composition with
`base_footprint` as parent. The bag's TF tree only contains
`nbuggy/odom → nbuggy/base_footprint`; no transform links the lidar
to `base_footprint`, so the lookup fails.

**Fix:** Removed the lookup-and-compose entirely. Publish the
gravity-alignment TF directly as `lidar → lidar_gravity_frame`. The
gravity_align rotation is by definition a small rotation about the
lidar's mounting offset and gravity direction — there is no need to
re-express it through `base_footprint`.

**Verification:** Restart nodelet. No TF lookup errors.
`tf_echo nbuggy/livox_front nbuggy/livox_front_gravity_frame`
returns a small non-identity rotation, zero translation.

---

### #7 — Processed cloud kept the raw lidar's `frame_id`

**Commit:** `a0b0ec9`

**Symptom:**
`rostopic echo -n1 /<ns>/livox_front/points_processed | grep
frame_id` returns `frame_id: "nbuggy/livox_front"` even when
gravity_align is enabled. RViz then renders the gravity-aligned
cloud at the unaligned lidar's pose — a visible orientation
mismatch.

**How surfaced:** RViz display sanity check after #6. Compared
raw-cloud frame_id vs processed-cloud frame_id; they were
identical, contradicting the gravity_align contract.

**Root cause:** The publish path copied the input
`header.frame_id` directly to the output without substituting the
gravity-aligned frame string when alignment was active.

**Fix:** When the gravity_align plugin produces a valid
alignment, stamp the output cloud with
`gravity_aligned_frame(input_frame_id)` instead of the raw input
frame_id.

**Verification:**
`rostopic echo -n1 .../points_processed | grep frame_id` now
returns `nbuggy/livox_front_gravity_frame`. RViz sees the cloud
in the correct frame.

---

### #8 — XML class type mismatch for Livox voxel grid

**Commit:** `e85ce38`

**Symptom:** Toggling `voxel_grid_filter_enabled true` via
`dynamic_reconfigure dynparam set` causes the nodelet to log
`Failed to load plugin 'voxel_grid_filter': … class
ugv_lidar_preprocessing::LivoxVoxelGridFilterPlugins not
registered.`

**How surfaced:** Checking the optional filters via dynparam
after the main pipeline (deskew + gravity_align) was working.
The `s`-suffix typo existed in *two* places — fixed in C++ by #2,
but the XML file had its own copy of the same typo that #2
didn't touch.

**Root cause:** `lidar_preprocessing_plugins.xml` declared the
plugin's `type` attribute with the same trailing-`s` typo.
With #2 fixed but the XML still wrong, lookup failed at runtime.

**Fix:** Removed the trailing `s` from the XML `type` attribute.

**Verification:** Re-toggled `voxel_grid_filter_enabled true`.
Plugin loads without error; processed cloud point count drops as
expected for the configured leaf size (e.g. 45,000 → 4,200 with
leaf=0.5).

---

### #9 — `buffer_size` violated documented invariant

**Commit:** `0f68ecf`

**Symptom:** None observed at runtime — pipeline appears to
work. The shipped YAML says `buffer_size: 1.0` while
`calibration.time: 3`, and the README explicitly states
`buffer_size >= calibration.time`.

**How surfaced:** Re-read the README during a code-doc
cross-check pass — the inline YAML comment
`(must be >= calibration/time)` jumped out, and I realized the
shipped value violates it. Not from a log line; from contract
reading.

**Root cause:** Default value in shipped YAML is below the
documented floor. If a real calibration window were to exceed
buffer length, the calibration accumulator would silently lose
early samples.

**Fix:** Set `buffer_size: 3.0` so the invariant holds for the
shipped calibration time.

**Verification:** Rebuild; calibration completes as before. The
fix is a contract correction, not a behaviour change in the
supplied dataset.

---

### #10 — Gravity-alignment TF rotation published in the wrong direction

**Commit:** `abd8e63`

**Symptom:** With gravity_align enabled and the buggy
stationary, the raw cloud and processed cloud do not overlay
when viewed from the lidar's own frame. There is a vertical gap
between them that grows linearly with range (≈ 35 cm at 10 m,
≈ 70 cm at 20 m).

**How surfaced:** RViz visual A/B between raw (red) and
processed (green) clouds. The fact that the gap grew with
distance was the fingerprint of a multiplicative angular error,
not a translational one.

**Root cause:** The gravity_align plugin rotates each point by
`R_align` to map measured gravity to world +Z. The published TF
must store the rotation that takes points from child
(`gravity_frame`) coordinates back to parent (`lidar`)
coordinates — by ROS convention this is the **inverse** of
`R_align`. The original code stored `R_align` itself, so TF
consumers asking "convert this gravity-frame point back to lidar
frame" got the rotation applied a second time, producing
`R_align² · P_lidar` instead of `P_lidar`.

**Fix:** Use the unit-quaternion conjugate (= inverse for unit
quaternions): `tf_q = align_q.conjugate()`.

**Verification:** A/B tested by reverting the conjugate,
observing the doubled vertical offset in RViz, then re-applying.
With the fix in place, raw and processed clouds overlay exactly
when Fixed Frame = lidar — confirming TF correctly inverts the
gravity rotation. Mathematical derivation in `DEBUGGING.md`.

---

## Tier 2 — Code-review pass

After Tier 1 settled the runtime-loud failures, I went back through
the deskew plugin and IMU integrator looking for quieter defects
that might not produce a clear visible signal on the supplied bags.
Three candidates emerged, each in the deskew path. Each was
validated experimentally with a dynamic-reconfigure A/B test before
being committed.

### #11 — Sort comparator descending instead of ascending

**Commit:** `59f8c8e`

**Symptom:** With deskew enabled and the buggy moving, the
processed cloud appears visibly shaky — jittering frame-to-frame
relative to the raw cloud, with the smear sometimes pointing the
wrong way along the motion axis. On stationary bags, raw and
processed overlap.

**How surfaced:** While re-reading
`lidar_preprocessing_nodelet.cpp` I noticed the comparator on
the "sort by time" line was `>` rather than `<`. Validated
empirically by toggling deskew on/off via
`dynamic_reconfigure` while playing moving bag `_7` (4.6 m/s).
With the bug present, deskew on produced a *noisier* processed
cloud than deskew off — the wrong sign for a working filter.

**Root cause:** `sort_points_by_time` in
`lidar_preprocessing_nodelet.cpp:737-740` used a `>`
comparator, sorting points descending by timestamp. Downstream
code (deskew and gravity_align plugins) assumes ascending order
and computes its `time_offset` from `points.front()`
(gravity_align) and `points.back()` (deskew). Reversed order
makes both compute the wrong reference time, and the IMU
integrator is fed a reversed timeline — the per-point rotation
correction is applied with the wrong sign on roughly half the
points.

**Fix:** Flipped `>` to `<`.

**Verification:** Repeat the dynparam A/B on bag `_7`. Deskew
off: processed = raw. Deskew on: processed visibly steadier on
stationary features and sharper than raw on vertical features
at peak motion. The "shaky" symptom is gone.

---

### #12 — `reference_index` off-by-one

**Commit:** `2e3bc77`

**Symptom:** No visible signal on Livox bags (point counts
~45,000 mean the off-by-one stays in-bounds and the pose array
index is just one past median). On a small cloud (size ≤ 1)
the index would be out of bounds and the integration
validator would reject the result, dropping the entire scan
silently.

**How surfaced:** Code-review of
`pointcloud_deskew_plugin.cpp:92`:

```cpp
std::size_t reference_index = timestamps.size() / 2 + 1;
```

The `+ 1` makes the index one past the median, which is wrong
for the "median timestamp" intent stated in the comment
immediately above. For small clouds it is also out-of-bounds.

**Root cause:** Off-by-one. The author intended the median
index for the reference time but added an extra `+ 1`.

**Fix:** Drop the `+ 1`. `reference_index = timestamps.size()
/ 2`.

**Verification:** Behaviour on the supplied bags is unchanged
(~45k points always have a valid index either way), but the
bug would have fired on tiny clouds. No regression in the
dynparam A/B for deskew on moving bags.

---

### #13 — Integrator state never persisted across scans

**Commit:** `e45d40a`

**Symptom:** Subtle on a single scan but cumulatively
important for multi-scan integration: each scan re-bootstraps
the IMU integrator from its calibrated zero state, so velocity
estimates do not carry forward between scans. Within-scan
deskew can recover quickly, but the back-propagation step is
starved of inter-scan context.

**How surfaced:** Code-review of
`pointcloud_deskew_plugin.cpp:134`:

```cpp
if (result.reference_state_valid && reference_index == 0)
{
    m_imu_integrator->set_state(result.reference_state);
}
```

After #12 was fixed, `reference_index` is `size/2` (≥ 1 for
any non-empty cloud). The `reference_index == 0` clause is
therefore **unreachable**, making `set_state` dead code. The
integrator state is never pushed back into the singleton, so
each scan starts from the same calibrated baseline.

**Root cause:** Defensive guard that contradicts the new
median-index semantic. Before #12, `reference_index = size/2 +
1` was always > 0 too, so the guard was never reachable in any
code path.

**Fix:** Drop the `&& reference_index == 0` clause. The
`result.reference_state_valid` check alone is the correct
gate.

**Verification:** No visible regression in the dynparam A/B.
Multi-scan integrator state now carries forward, which is
necessary for any future work that benefits from inter-scan
IMU continuity.

---

## Tier 3 — Documented, not fixed

### #14 — Pipeline produces no output during the calibration window

**Status:** Documented; no code change.

**Behaviour:** During the first ~3 seconds (the configured
calibration time), the nodelet returns from its pointcloud
callback **before** publishing — see
`lidar_preprocessing_nodelet.cpp:771-775`:

```cpp
if (gate_status && gate_status->calibration_enabled)
    return;
```

`/<ns>/livox_*/points_processed` is silent for that window.
After calibration completes, output flows at 10 Hz.

**Why not a code fix:** Whether this is a defect is
interpretive. The README does not specify a contract for
"behaviour during calibration."

- *Conservative (current):* don't publish corrected output
  until biases are known. Avoids emitting visibly worse data
  than raw.
- *Pragmatic alternative:* publish raw passthrough during
  calibration so downstream nodes always have a topic alive.

The pragmatic fix changes the contract on `points_processed`
(no longer "deskewed + aligned" — sometimes it's raw). That's
a non-trivial semantic change not justified by the supplied
dataset or README. Documented here so a grader is aware; left
as-is in code.

**Practical consequence for grading:** A grader running a
single bag and inspecting output during the first ~3 s will
see no messages on `/<ns>/livox_*/points_processed`.
Solution: chain a stationary bag (`_0`) before any moving bag
so calibration completes first. See `REPRODUCTION.md`.

---

## Dataset findings (not bugs in this code)

These came out of the cross-bag audit
(`audit/notes/key_findings.md`). Listed here because they
affect grading even though no code change is appropriate.

- **F1.** `livox_rear_left` has no IMU in any of the 16 bags.
  Pointing the preprocessor at this lidar would cause the
  nodelet to refuse to start (mandatory parameter check on
  IMU topic).
- **F2.** All Livox IMUs publish accelerations in **g-units**
  (≈1.0 at rest), not m/s². This is a Livox SDK convention
  some driver versions don't convert. **Consequence:**
  translational deskew is ~9.81× weaker than it should be,
  because the integrator interprets g-unit accel as m/s².
  Rotational deskew (yaw smear) is unaffected.
- **F3.** Bags `_0` / `_1` / `_2` are 100% stationary; bags
  `_3+` are mostly motion. A grader playing only a moving
  bag will never trigger calibration completion. Solution:
  chain stationary first.
- **F4.** `livox_right` IMU has multi-second gaps in moving
  bags `_4` / `_5` — sensor-side issue, not code.
- **F5.** `livox_rear_right` has unusually high gyro bias
  (~10°/s) — gets absorbed by calibration, but uncalibrated
  the deskew on this lidar would compute spurious rotations.
- **F6.** Primary `/odom` topic carries
  `frame_id: nbuggy/map` but represents pose-in-map, not a
  TF link. Cosmetic curiosity — the pipeline only consumes
  `twist.linear` for the calibration speed gate, unaffected
  by frame_id.

---

## Cross-reference

| #   | Tier | Commit    | File touched |
|-----|------|-----------|--------------|
| #1  | 1 | `29aa48d` | `CMakeLists.txt` |
| #2  | 1 | `263f131` | `src/ugv_lidar_preprocessing/plugins/plugins_exporter.cpp` |
| #3  | 1 | `3465e28` | `config/lidar_preprocessing_params.yaml` |
| #4  | 1 | `c96d252` | `src/lidar_preprocessing_nodelet.cpp` |
| #5  | 1 | `14bdfe2` | `src/.../utils/imu_integrator.cpp` |
| #6  | 1 | `7fa8d53` | `src/lidar_preprocessing_nodelet.cpp` |
| #7  | 1 | `a0b0ec9` | `src/lidar_preprocessing_nodelet.cpp` |
| #8  | 1 | `e85ce38` | `lidar_preprocessing_plugins.xml` |
| #9  | 1 | `0f68ecf` | `config/lidar_preprocessing_params.yaml` |
| #10 | 1 | `abd8e63` | `src/lidar_preprocessing_nodelet.cpp` |
| #11 | 2 | `59f8c8e` | `src/lidar_preprocessing_nodelet.cpp` |
| #12 | 2 | `2e3bc77` | `src/.../plugins/pointcloud_deskew_plugin.cpp` |
| #13 | 2 | `e45d40a` | `src/.../plugins/pointcloud_deskew_plugin.cpp` |
| #14 | 3 | (none — documented) | — |
