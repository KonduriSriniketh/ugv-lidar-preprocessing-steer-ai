# ugv_lidar_preprocessing

ugv_lidar_preprocessing is a ROS nodelet-based LiDAR preprocessing pipeline. It is built around
plugin modules so each step can be enabled or disabled depending on the sensor and use case.

## Features

- Deskewing (motion compensation using IMU integration)
- Gravity alignment
- Voxel grid downsampling
- Radius outlier removal
- Livox tag filtering (return and noise filtering)

## Deskewing and IMU integration (DLIO attribution)

The LiDAR deskewing and IMU integration logic in this package is adapted from DLIO
(Direct LiDAR-Inertial Odometry), located at [direct_lidar_inertial_odometry](https://bitbucket.org/autonomouscv/direct_lidar_inertial_odometry/src/develop/)

## Supported inputs

- `sensor_msgs/PointCloud2` for Ouster, Velodyne, and Livox point types.
- IMU is required when deskew or gravity alignment is enabled.

## Pipeline and plugin order

Plugins are executed in a fixed order; disabled plugins are skipped:

1. Deskew (motion compensation)
2. Gravity alignment
3. Voxel grid filter
4. Radius outlier removal
5. Livox tag filter

This order is enforced in code, so you only control whether a step is enabled.

## Quick start

Launch the nodelet directly:

```bash
roslaunch ugv_lidar_preprocessing pointcloud_deskewer_nodelet.launch \
  namespace:=<robot_namespace> \
  sensor:=<Livox|Velodyne|Ouster>
```

## Topics

### Input

- `input_topic` (default: `points`)
- IMU topic is required if deskew or gravity alignment is enabled.

### Output

Output topics are derived from the input topic prefix and are not configurable to avoid mismatches.
Example: if `input_topic` is `livox_front/points`:

- `livox_front/points_processed` (combined filtered cloud, or return 0 if per-return is enabled)
- `livox_front/points2_processed` (return 1, only when per-return is enabled)
- `livox_front/points3_processed` (return 2, only when per-return is enabled)

## Frames and TF

- When gravity alignment is enabled and a valid alignment is computed, the output frame is set to
  `<input_frame>_gravity_frame`.
- A TF is published from `<input_frame>` to `<input_frame>_gravity_frame` with zero translation
  and the alignment rotation.

If you view both raw and processed clouds in a fixed frame (e.g., `base_footprint` or `map`), they
can appear identical because TF transforms both into the same frame. To inspect the alignment,
compare the TF between `<input_frame>` and `<input_frame>_gravity_frame`.

## Configuration

### YAML structure

Parameters are namespaced by plugin. The current format is:

```yaml
input_topic: "livox_front/points"

imu_params:
  topic: "livox_front/imu"
  buffer_size: 1.0

  calibration:
    enabled: true
    time: 3
    external_velocity:
      max_speed_mps: 0.01
      max_age_sec: 0.5
    gyro:
      bias: [0.0, 0.0, 0.0]
    accel:
      bias: [0.0, 0.0, 0.0]
      sm: [1., 0., 0.,
           0., 1., 0.,
           0., 0., 1.]

  integration:
    integration_params:
      approximate_gravity: true
      gravity_mps2: 9.80665

pointcloud_deskew:
  enabled: true
  lidar_to_imu_translation: [0.0, 0.0, 0.0]
  lidar_to_imu_rotation: [1.0, 0.0, 0.0,
                          0.0, 1.0, 0.0,
                          0.0, 0.0, 1.0]

gravity_align:
  enabled: true

voxel_grid_filter:
  enabled: false
  leaf_size: 0.1

radius_outlier_removal:
  enabled: false
  radius: 0.5
  min_neighbors: 5

livox_tag_filter:
  enabled: true
  remove_high_confidence_noise: true
  remove_moderate_confidence_noise: true
  remove_low_confidence_noise: false
  remove_intensity_noise: true
  output_per_return: false
```

### Notes

- `imu_params/topic` is mandatory when deskew or gravity alignment is enabled.
- `imu_params/buffer_size` should be >= `imu_params/calibration/time` so calibration has enough samples.
- `imu_params/calibration/external_velocity` expects `<namespace>/odom` (`nav_msgs/Odometry`) and requires linear speed <= `max_speed_mps`.
- `lidar_to_imu_rotation` is a 3x3 row-major rotation matrix.
- YAML values override dynamic reconfigure defaults on nodelet initialization.

## Livox tag filtering

When enabled:

- Points at (0, 0, 0) are dropped (Livox indicates out-of-range points this way).
- Tag bits are interpreted as:
  - [5:4] return number (0/1/2)
  - [3:2] intensity noise group
  - [1:0] spatial noise group
  - [7:6] reserved (always kept)

Filtering toggles allow removing:

- High confidence spatial noise
- Moderate confidence spatial noise
- Low confidence spatial noise
- Low-intensity noise

When `output_per_return` is true, the output topics switch to return-specific clouds.

For more information on this, refer to [this](https://dl.djicdn.com/downloads/Livox/HAP/HAP(T1)_User_Manual_V1.2_EN.pdf) Livox documentation, page 14.

## Dynamic reconfigure

Dynamic reconfigure is supported via `PreprocessingParams.cfg` with flattened parameter names
(`pointcloud_deskew_enabled`, `gravity_align_enabled`, `voxel_grid_filter_leaf_size`, etc).
YAML values take precedence on startup; dynamic reconfigure changes apply at runtime.

## Performance

- Deskew and gravity alignment are parallelized with OpenMP in per-point loops.
- IMU integration is kept single-threaded and lightweight.

## Integration with ugv_launch

- Defaults: `config/lidar_preprocessing_params.yaml`
- Platform overrides:
  `src/core/Bringup/ugv_launch/params/<platform>/Perception/lidar_preprocessing_lidar_*.yaml`
- Launch wiring:
  `src/core/Bringup/ugv_launch/launch/platform_perception.launch`

## Troubleshooting

- Output looks identical to raw: check TF between `<input_frame>` and
  `<input_frame>_gravity_frame` to confirm alignment is non-identity.
- VoxelGrid warning about leaf size: increase `voxel_grid_filter/leaf_size` or
  verify the input cloud is non-empty.
- Livox tag filter enabled on non-Livox sensors: it will be disabled with a warning.
