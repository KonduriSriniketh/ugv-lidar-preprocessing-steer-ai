# Reproduction

Step-by-step instructions to build, launch, and verify the fixed
pipeline against the supplied bags. All commands assume the bags
live at `~/bags/` on the host, mounted read-only into the
container.

## Prerequisites

- Docker (Desktop on Windows + WSL2, or Linux native).
- The 16 supplied bags at `~/bags/`. Filenames have the form
  `2025-12-30-18-XX-XX_N.bag` where `N` is `0` through `15`.
- An X server reachable from the container if you want RViz
  (Linux: native; WSL2: WSLg, no extra setup).

## Build the image

From the repository root:

```bash
docker build -t ugv-lidar:dev .
```

The Dockerfile is `ros:noetic-ros-core` plus the build- and
runtime-side ROS packages needed for this pipeline (build
tooling, pluginlib, PCL, RViz, rosbag, dynamic_reconfigure,
TF tools, x11-apps). One-time build, ~5 minutes.

## Start the container

```bash
docker run -it --rm --name ugv-lidar \
  --network host \
  -e DISPLAY=$DISPLAY -e QT_X11_NO_MITSHM=1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v "$PWD":/ws/src/ugv_lidar_preprocessing \
  -v ~/bags:/bags:ro \
  ugv-lidar:dev bash
```

Notes:
- `--rm` deletes the container on exit; we re-mount each session.
- `--network host` so all ROS topics resolve cleanly between
  shells.
- Source dir is bind-mounted so edits on the host are picked up
  inside the container without rebuilding the image.
- WSL2 with WSLg: if RViz fails with "cannot open display", add
  `-v /mnt/wslg:/mnt/wslg` and
  `-e WAYLAND_DISPLAY=$WAYLAND_DISPLAY`.

The first shell that starts the container is **T1** (roscore).
For every subsequent shell open a new terminal on the host and
run:

```bash
docker exec -it ugv-lidar bash
```

## Build the workspace (T1)

Inside T1:

```bash
source /opt/ros/noetic/setup.bash
cd /ws
catkin build -j4              # or `catkin_make` — pick one and stick with it
source devel/setup.bash
roscore
```

Leave `roscore` running in T1.

## Launch the nodelet (T2)

```bash
docker exec -it ugv-lidar bash
```

Inside T2:

```bash
source /opt/ros/noetic/setup.bash
source /ws/devel/setup.bash
rosparam set /use_sim_time true
roslaunch ugv_lidar_preprocessing lidar_preprocessing_nodelet.launch \
    sensor:=Livox namespace:=nbuggy
```

Two things to watch for in the log:

1. **Plugin chain**:
   ```
   Plugin Execution Order for enabled preprocessors:
   pointcloud_deskew -> gravity_align -> livox_tag_filter
   ```
   Disabled plugins (voxel grid, ROR by default) are correctly
   omitted.

2. **Calibration**: starts when the bag begins flowing IMU
   samples. Completes within ~3 s of bag time on a stationary
   bag.

The default namespace in the launch file is `rbuggy`, but the
supplied bags use `nbuggy`, so the `namespace:=nbuggy` argument
is mandatory.

## Play bags (T3) — chain stationary first

```bash
docker exec -it ugv-lidar bash
```

Inside T3:

```bash
source /opt/ros/noetic/setup.bash
rosbag play --clock --rate 0.5 \
    /bags/2025-12-30-18-03-34_0.bag \
    /bags/2025-12-30-18-05-14_5.bag
```

**Why chain `_0` first.** Bags `_0`, `_1`, `_2` are 100%
stationary. The nodelet's calibration phase needs ~3 seconds of
stationary IMU samples; if you play a moving bag (`_3+`) by
itself, calibration's velocity gate never permits the fit and
the pipeline stays silent forever. Chaining a stationary bag
first lets calibration complete; the moving portion then
exercises deskew and gravity_align.

The `--rate 0.5` is so RViz has time to render and you have time
to scrutinise. Drop it for full-rate playback.

`--clock` is required because we set `/use_sim_time true` in
T2 — without it, ROS time freezes and TF lookups fail.

## Verify outputs

In a fourth shell:

```bash
docker exec -it ugv-lidar bash
source /opt/ros/noetic/setup.bash

rostopic hz /clock                                  # ~100 Hz
rostopic hz /nbuggy/livox_front/imu                 # ~200 Hz
rostopic hz /nbuggy/livox_front/points              #  ~10 Hz
rostopic hz /nbuggy/livox_front/points_processed    #  ~10 Hz (after calib)

rostopic echo -n1 /nbuggy/livox_front/points_processed | grep frame_id
# expect: frame_id: "nbuggy/livox_front_gravity_frame"

rosrun tf tf_echo nbuggy/livox_front nbuggy/livox_front_gravity_frame
# expect: zero translation, small non-identity rotation (mounting offset)
```

## RViz visual check (optional)

```bash
docker exec -it ugv-lidar bash
source /opt/ros/noetic/setup.bash
source /ws/devel/setup.bash
rviz
```

Configuration:

- **Fixed Frame:** `nbuggy/livox_front` (or
  `nbuggy/livox_front_gravity_frame` for the gravity-aligned
  view).
- Add a **PointCloud2** display for `/nbuggy/livox_front/points`
  (raw — colour red, size 0.02, decay 0).
- Add a **PointCloud2** display for
  `/nbuggy/livox_front/points_processed` (processed — colour
  green, size 0.02, decay 0).

Expected observations:

- **Stationary phase (`_0`):** red and green clouds overlay
  exactly. This confirms TF correctly inverts the gravity
  rotation and deskew is a no-op when there's no motion.
- **Moving phase (`_5`):** red and green start to diverge on
  fast-moving features. Specifically: vertical poles and
  building edges are smeared in red (raw) and visibly sharper
  in green (deskewed). The translational portion of the
  correction is partial — see `audit/notes/key_findings.md`
  finding F2 for why.

## Optional: A/B confirm deskew with dynamic_reconfigure

While a bag is playing, in any sourced shell:

```bash
# Disable deskew → green should become identical to red
rosrun dynamic_reconfigure dynparam set \
    /nbuggy/ugv_lidar_pre_processing_nodelet \
    pointcloud_deskew_enabled false

# Re-enable → green diverges from red on motion
rosrun dynamic_reconfigure dynparam set \
    /nbuggy/ugv_lidar_pre_processing_nodelet \
    pointcloud_deskew_enabled true
```

Same approach works for `gravity_align_enabled`,
`voxel_grid_filter_enabled`, `radius_outlier_removal_enabled`,
`livox_tag_filter_enabled`, plus their numeric parameters
(leaf size, radius, min neighbours, etc.).

## Optional: cross-bag audit

The static-analysis Python parser used during debugging lives
in `audit/`. It needs no ROS or pip — just stdlib:

```bash
cd audit/scripts
python3 run_audit.py > ../notes/cross_bag_audit.md
```

Edit the bag directory inside `run_audit.py` if your layout
differs from `~/bags/`.

## Common pitfalls

- **`rostopic hz` says "no new messages" but topics exist.**
  `/clock` is not flowing or `/use_sim_time` is mismatched.
  Confirm `rostopic hz /clock` shows ~100 Hz and rosbag was
  started with `--clock`.
- **TF errors after bag finishes / loops.** When `rosbag play`
  exits, sim-time stops advancing. Restart the bag (do not use
  `-l` for short bags — the loop-back triggers TF
  jump-back warnings; chain bags instead).
- **No output from `points_processed` for the first 3 s.**
  Expected — calibration window. Play a stationary bag first.
- **RViz can't find frames.** Ensure RViz was launched
  *after* the bag started publishing `/clock`. If not, close
  RViz and relaunch.
