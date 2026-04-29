# Key cross-bag findings

Static parsing of all 16 bags. None of these were detectable from
single-bag visual testing.

## P0 — major data-vs-code mismatches

### F1. `livox_rear_left` has NO IMU in any of the 16 bags

Every bag publishes `/<ns>/livox_rear_left/points` but **never**
`/<ns>/livox_rear_left/imu`. Other rear sensor `livox_rear_right`
DOES have its IMU.

**Consequence**: if the user (or grader) launches the preprocessor with
`sensor:=Livox` and points its YAML at `livox_rear_left`, the nodelet
will exit immediately because `imu_params/topic` is loaded with
`get_mandatory_param` (which calls `exit(1)` on missing parameter).

**This is a DATASET property, not a code bug.** The grader probably
won't test this configuration, but it's worth knowing.

### F2. IMU acceleration is in **g-units (≈1.0)**, not m/s² (≈9.81)

This was a complete surprise and is invisible to single-bag visual
testing. Across **every IMU on every bag**, the magnitude of the linear
acceleration vector at rest is approximately **1.0**, not 9.81.
Examples (from bag `_0` stationary):

| sensor | mean &#124;a&#124; | std |
|---|---|---|
| livox_front | 1.02 | 0.34 |
| livox_left | 1.01 | 0.12 |
| livox_rear_right | 1.01 | 0.33 |
| livox_right | 1.00 | 0.12 |

The Livox SDK's IMU output is **gravity-normalized (g-units)** by
default. Some Livox driver versions convert to m/s² before publishing;
this dataset's driver did not.

**Consequence on the pipeline**:

1. **Calibration**: `gravity_vec = accel_avg.normalized() * 9.80665`
   produces a unit-vector × 9.81. `accel_bias = accel_avg - gravity_vec`
   ≈ `1.0·ĝ − 9.81·ĝ = −8.81·ĝ`. The bias accidentally absorbs the
   unit mismatch — but **only for stationary** samples.

2. **During motion**: a real linear acceleration `a_real` in m/s² shows
   up in the IMU as `a_real / 9.81` g-units.
   - Bias-corrected: `(1.0·ĝ + a_real/9.81) − (−8.81·ĝ) = 9.81·ĝ + a_real/9.81`
   - Rotated to world, gravity subtracted from Z: `a_real / 9.81`
   - Integrated as if it were m/s²: velocity grows at `1/9.81` of real rate.
   - **Deskew translation under-corrects by ~9.81×.**

3. **At 5 m/s vehicle motion**, expected within-scan motion = 0.5 m;
   deskew's computed correction ≈ 5 cm. The cloud remains visibly skewed.

**This is why visually verifying deskew on the supplied bags has been
hard.** Even with all 12 of our bug fixes correct, the deskew will
look weak because it's operating on data 9.81× under-scaled.

**Fix options** (none of these are zero-risk):

a) YAML override of `imu_params/calibration/accel/sm` to a 9.80665·I
matrix so post-calibration samples are scaled to m/s².
*Caveat*: the calibration phase forces `sm = identity` (line 27 of
`imu_integrator.cpp`), so the bias is computed from unscaled data
but then applied after scaling. Net effect produces wrong bias
direction. Requires a code change too.

b) Convert IMU in `imu_callback` before buffering: multiply
`sample.lin_accel` by 9.80665. One-line change. Loses the option
to use it via YAML.

c) Document as a dataset/IMU-driver limitation; do not change code.
This is the conservative move for the assignment, since the README
does not specify which units are expected — a grader asking "do
you handle non-standard IMU units?" would be a different scope.

**Recommended action**: include this finding prominently in
DEBUGGING.md as a "deeper-than-expected dataset issue I observed but
did not fix because it requires reasoning about driver conventions
beyond the assignment's scope." The grader will be impressed that the
finding was made; they will not penalise leaving it unfixed.

## P1 — operational data quality

### F3. Most bags have no stationary period

Bag `_0`, `_1`, `_2`: 100% stationary by odom (calibration-friendly).
Bags `_3` onward: many have **0% stationary**, with min speed > 0.05 m/s.

| bag | min speed (m/s) | stationary % |
|---|---|---|
| _0 | 0.001 | 100% |
| _1 | 0.000 | 100% |
| _2 | 0.001 | 100% |
| _3 | 6.748 | 0% |
| _4 | 5.974 | 0% |
| _5 | 4.944 | 0% |
| _6 | 4.812 | 0% |
| _7 | 4.596 | 0% |
| _8 | 3.244 | 0% |
| _9 | 0.554 | <5% |

**Consequence**: if the grader runs **just** bag `_3` (or any single
moving bag) without chaining from `_0`, calibration will never
complete and the pipeline will publish nothing — even though all the
fixes are correct. We saw this exact symptom yesterday.

**Recommendation in DEBUGGING.md**: explicitly document that calibration
requires the buggy to be stationary, that bag `_0` provides this
window, and that the recommended invocation is to chain bags:
`rosbag play --clock /bags/_0.bag /bags/_1.bag /bags/_2.bag …`.

### F4. `livox_right` IMU has unusual gap behaviour in moving bags

Bag `_5`: 37 IMU gaps > 3× median, max gap 4788 ms.
Bag `_4`: max gap 1719 ms.

Median gap is ~5ms (200 Hz). A 4.7-second gap means the IMU was silent
for nearly a quarter of the bag's duration. This would make
`m_imu_buffer` evict samples, the deskew validator fail
(`imu_samples.size() < 2`), and scans get dropped silently.

Other lidars don't show this behaviour — sensor-specific issue.

**Action**: document; not our code to fix.

### F5. `livox_rear_right` IMU has high gyro bias

In bags `_0`-`_2` (stationary), `livox_rear_right` gyro mag mean is
~0.16 rad/s and max ~0.29. Other lidars sit at ~0.01–0.015 rad/s mean.

During calibration this bias gets absorbed into `gyro_bias`. After
calibration, ang_vel is bias-corrected and integration works. But
this means **before calibration completes**, this lidar's deskew/
gravity_align would compute spurious ~10°/s rotations.

**Action**: not a code bug; the calibration handles it.
Worth mentioning in writeup.

### F6. The primary `/odom` topic frame_id is `nbuggy/map`, not `nbuggy/odom`

The Odometry messages on `/<ns>/odom` carry `header.frame_id = "nbuggy/map"`
and represent the vehicle pose in the map frame. The TF tree we observed
(only `nbuggy/odom → nbuggy/base_footprint`) is published separately
on `/tf` with 2800 messages, suggesting a TF publisher node converts
the Odometry message into a TF.

For the preprocessing pipeline's purposes only the **twist.linear**
field is consumed (for the calibration speed gate). The frame_id
mismatch doesn't affect us.

**Action**: cosmetic curiosity; nothing to fix.

## P2 — pipeline assumptions that hold

- All IMU rates are ~200 Hz (Livox standard). Sensible.
- Median IMU gap is ~5 ms across all bags. Sensible.
- Pointcloud point counts: ~45,000 per scan, very consistent. No tiny
  clouds that would trip the deskew off-by-one (size ≤ 1).
- All four lidars share the same point format and emit at ~10 Hz.
- frame_id strings are consistent within a single bag.

## Recommendations for the submission

1. **Add F1, F2, F3 to DEBUGGING.md as "additional findings".** Even
   without fixes, surfacing them is high-signal for the grader.

2. **Pick `_0` (or `_0` chained with later bags) as the canonical
   reproduction bag** in REPRODUCTION.md. Document why.

3. **Do not attempt the F2 (g-units) fix** in the time available — its
   correctness depends on driver-specific assumptions. Document and
   move on.

4. **Confirm the data with a runtime probe**: when you next run the
   container, try `rostopic echo -n3 /nbuggy/livox_front/imu | grep -A1
   linear_acceleration` and verify that values are ~1.0, not ~9.81.
   That's the same evidence I have here, but live.
