# Static re-audit findings

This document captures findings from a static re-read of the entire
package after the runtime-loud bugs were committed. Goal: catch missed
defects before submission.

## Summary

- **Three P0 (must-fix-blocking) defects in the deskew/integrator path:**
  the sort comparator, the reference_index off-by-one, and the
  integrator-state-persistence guard.
- One **P1** observation (calibration sign / robustness) and three
  **P2** observations (code-smell / convention issues that don't affect
  correctness for the supplied dataset).
- Sensor-specific code paths (Ouster + Velodyne) are all instantiated
  and exported; no Livox-specific bias.
- IMU integrator math (quaternion integration, back-propagation,
  Taylor-series jerk integration) is mathematically correct.
- Threading and locking are correct (single-direction lock acquisition,
  no deadlock potential).
- README claims align with code behavior after the existing fixes.

## P0 — must fix before submit

### Sort comparator descending instead of ascending
[`src/lidar_preprocessing_nodelet.cpp:737-740`]

The `sort_points_by_time` comparator uses `>` (descending). It must be
`<` (ascending) for the deskew/gravity_align time_offset math to work.

### Deskew reference_index off-by-one
[`src/.../plugins/pointcloud_deskew_plugin.cpp:92`]

`reference_index = timestamps.size() / 2 + 1` is 1 past median; for
small clouds (size <= 1) this is out of bounds, integration validator
returns false, deskew clears its output. Drop the `+ 1`.

### Deskew integrator state never persisted across scans
[`src/.../plugins/pointcloud_deskew_plugin.cpp:134`]

`if (result.reference_state_valid && reference_index == 0)` — the
`reference_index == 0` clause is structurally impossible (line 92
sets it to size/2 + 1, always >= 1). `set_state` is therefore dead
code; integrator state never carries forward.

## P1 — should consider

### `filter_points_by_imu_coverage` time-offset shift
[`src/lidar_preprocessing_nodelet.cpp:688-705`]

The function computes a `time_offset = sweep_ref_time - min_raw_time`
and applies it to each point's accessor result before comparing to
`latest_imu_stamp`:

```cpp
const double stamp =
    PointTimeAccessor<PointT>::time_seconds(pt, sweep_ref_time) + time_offset;
if (stamp <= latest_imu_stamp) ...
```

This shift is intended to normalize per-point times across sensor
conventions, but its correctness depends on the per-point time being
"close to" `sweep_ref_time`. Concretely:

- **Ouster (`pt.t` is unsigned offset in ns from sweep start)**:
  `min_raw_time = sweep_ref + 0 = sweep_ref`; `time_offset = 0`.
  Shift is a no-op. Behavior is correct.
- **Velodyne (`pt.time` is float seconds, can be negative if the
  driver centres the sweep stamp on the middle of the scan)**:
  `time_offset > 0`. Each point's compared time is shifted up,
  making the comparison too strict — points within IMU coverage
  may be incorrectly rejected. Effect: no scan loss in our Livox
  dataset, but a Velodyne dataset would see false rejections at
  the trailing edge of the scan.
- **Livox (`pt.timestamp * 1e-9` is absolute time)**:
  `min_raw_time` = earliest absolute time. If the lidar driver
  emits `header.stamp` at the END of the scan, `time_offset > 0`
  and the shift inflates each compared time, again making the
  comparison too strict. If the driver emits at the START,
  `time_offset` is roughly 0.

**Suggested action**: drop the `+ time_offset` from line 702 and
compare the raw `time_seconds(pt, sweep_ref)` directly to
`latest_imu_stamp`. This is correct for all three sensor types
because each accessor already returns absolute time. The current
code is robust to one convention but breaks others.

This is **P1** because:
- It does not affect the Livox dataset we tested with.
- Worst-case outcome is dropping more points than necessary, not
  geometric corruption.
- Fix is a 1-line change but slightly changes semantics.

## P2 — convention / code-smell, not bugs

### gravity_align uses `points.front()`, deskew uses `points.back()`
[`gravity_align_plugin.cpp:65`, `pointcloud_deskew_plugin.cpp:64`]

After the sort-ascending fix, gravity_align computes its
`time_offset` from the **earliest** point, while deskew uses the
**latest** point. Both produce internally-consistent timestamp
arrays for the integrator, but the inconsistency in convention is
confusing. No functional defect.

### `gravity_imu` is misnamed in `gravity_align_plugin.cpp`
[`gravity_align_plugin.cpp:101`]

```cpp
const Eigen::Vector3f gravity_imu = imu_to_world.transpose() * Eigen::Vector3f::UnitZ();
```

The vector computed is the world-Z (up) direction expressed in the
IMU frame — i.e., the **opposite** of gravity (which points down).
The flip below corrects for this by ensuring positive Z, but the
variable name is the opposite of what it holds. No functional defect.

### `m_imu_buffer_duration` default value mismatch
[`include/lidar_preprocessing_nodelet.hpp:452`,
 `src/lidar_preprocessing_nodelet.cpp:134`]

The header declares `double m_imu_buffer_duration{2.0};` but
`load_imu_params` reads the YAML with default `2.0` (matches header).
However, the YAML file ships `1.0` (now `3.0` after the buffer_size fix). So if
the YAML is missing the key entirely, the fallback is `2.0`, not the
header default. Minor and consistent in practice.

### Calibration constructor does not warn on bias prior overwrite
[`imu_integrator.cpp:24-32`]

```cpp
if (m_calibrate_imu)
    m_imu_accel_smatrix.setIdentity();   // overrides YAML matrix
else
    m_imu_accel_smatrix = imu_integrator_params.imu_calibration_params.imu_accel_smatrix;
```

When calibration is enabled, the user-supplied `accel.sm` matrix is
silently discarded in favour of identity. A WARN log here would be
helpful operationally, but the README implicitly documents this with
"During calibration, follow DLIO and use raw accel samples." No
defect.

## Sanity checks performed (no findings)

- **Plugin XML completeness**: 4 Ouster + 4 Velodyne + 5 Livox classes,
  each with a matching `using` alias and `PLUGINLIB_EXPORT_CLASS`.
- **IMU integrator quaternion derivative formula**: matches standard
  body-frame Hamilton convention (`dq/dt = 0.5 * q ⊗ ω`).
- **Position/velocity Taylor expansion**: code's `(1/6)·Δa·dt²` is
  equivalent to `(1/6)·j·dt³` because `j = Δa/dt`. Correct.
- **Back-propagation signs**: omega negation + forward-integration is
  equivalent to backward-integration. Sign on `accel` and `jerk` in
  position back-propagation is correctly negative (odd powers of dt).
- **`build_output_topic`**: handles trailing slashes, missing
  separators, empty inputs. Correct.
- **`is_preprocessor_enabled` warning for non-Livox sensors with
  livox_tag_filter enabled**: fires only on first init or toggle.
  Acceptable.
- **YAML overrides dynamic_reconfigure defaults**: `initialize_dynamic_reconfigure`
  reads YAML-loaded `m_plugin_params` then `updateConfig`. Correct.
- **TF inversion (gravity TF conjugate)**: handled.
- **Round-trip identity (raw vs processed)**: verified empirically
  via the user's A/B test.

## Recommendation

Fix the three **P0** items above (sort comparator, reference_index,
integrator-state guard) and decide on the calibration-window
publish-skip behaviour. The **P1** finding above
(`filter_points_by_imu_coverage` shift) is worth a one-line fix if
time permits, but is not blocking on the supplied Livox dataset.
The P2 items belong in the writeup, not commits.
