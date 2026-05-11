# Reproduction Notes

Per-bug instructions to reproduce each defect and verify its fix. The
goal of this document is to satisfy deliverable #2 of the assignment:
"a brief set of steps to reproduce each issue and verify the fix
(command lines are sufficient)."

For an extended environment guide (RViz visual checks, common
pitfalls, optional cross-bag audit) see `REPRODUCTION.md`. The
**Setup** section immediately below is everything required to run any
of the per-bug walks in this file.

## Setup

One-time work to build the Docker image and start the container. All
later sections assume this is done.

### Prerequisites

- Docker (Linux native, or Desktop on Windows + WSL2).
- The 16 supplied bags at `~/bags/` on the host. Filenames have the
  form `2025-12-30-18-XX-XX_N.bag` where `N` is `0`–`15`.
- An X server reachable from the container if you want RViz
  (Linux: native; WSL2: WSLg, no extra setup).

### Step 1 — Build the Docker image (one-time)

From the submission repo root on the **host**:

```bash
cd ~/ugv_lidar_preprocessing_submission
docker build -t ugv-lidar:dev .
```

The Dockerfile is `ros:noetic-ros-core` plus the build- and
runtime-side packages needed for this pipeline (catkin tooling,
pluginlib, PCL, RViz, rosbag, dynamic_reconfigure, TF tools, x11-apps).
~5 minutes the first time, cached afterwards.

### Step 2 — Start the container (T1)

```bash
cd ~/ugv_lidar_preprocessing_submission
docker run -it --rm --name ugv-lidar \
    --network host \
    -e DISPLAY=$DISPLAY -e QT_X11_NO_MITSHM=1 \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v "$PWD":/ws/src/ugv_lidar_preprocessing \
    -v ~/bags:/bags:ro \
    ugv-lidar:dev bash
```

What each flag does:

- `--rm` — container is destroyed when you exit; we re-mount each
  session so there is no persistent state to clean up.
- `--network host` — all ROS topics resolve cleanly between shells.
- `-v "$PWD":/ws/src/ugv_lidar_preprocessing` — bind-mounts the
  submission tree into the workspace. `git checkout` on the host is
  immediately visible inside the container; no image rebuild needed
  to switch commits.
- `-v ~/bags:/bags:ro` — bags mounted read-only at `/bags`.
- `-e DISPLAY=… -v /tmp/.X11-unix:/tmp/.X11-unix` — RViz/rqt windows
  open on the host display.
- WSL2 with WSLg, if RViz fails with "cannot open display": add
  `-v /mnt/wslg:/mnt/wslg` and `-e WAYLAND_DISPLAY=$WAYLAND_DISPLAY`.

The shell that started the container is **T1**.

### Step 3 — Open additional shells (T2, T3, T4) as needed

For every extra shell, on the **host**:

```bash
docker exec -it ugv-lidar bash
```

In each shell, source ROS once:

```bash
source /opt/ros/noetic/setup.bash
```

After the workspace is built, also source `devel`:

```bash
source /ws/devel/setup.bash
```

### Step 4 — Initial workspace build (T1)

```bash
# In T1
source /opt/ros/noetic/setup.bash
cd /ws
catkin build               # first build takes ~1 min
source devel/setup.bash
roscore                    # leave running
```

`roscore` stays running for the duration of the session.

### Step 5 — Standard launch / play / verify pattern

This is the per-walk pattern most bugs use. Skip to a bug section
below for its specific reproduce/verify commands; the snippets here
are referenced by name in the per-bug entries.

**Launch the nodelet (T2):**

```bash
source /opt/ros/noetic/setup.bash
source /ws/devel/setup.bash
rosparam set /use_sim_time true
roslaunch ugv_lidar_preprocessing lidar_preprocessing_nodelet.launch \
    sensor:=Livox namespace:=nbuggy
```

The launch file's default namespace is `rbuggy`; the supplied bags
use `nbuggy`, so `namespace:=nbuggy` is mandatory.

**Play bags (T3) — chain stationary first:**

```bash
source /opt/ros/noetic/setup.bash
rosbag play --clock --rate 0.5 \
    /bags/2025-12-30-18-03-34_0.bag \
    /bags/2025-12-30-18-05-14_5.bag
```

`_0` is 100 % stationary so calibration completes; `_5` then exercises
deskew and gravity_align under 4.6 m/s motion. `--clock` is required
because T2 set `/use_sim_time true`. Without `--rate 0.5` the bag
plays at full rate; drop it once you don't need RViz framerate.

**Verify topics (T4):**

```bash
source /opt/ros/noetic/setup.bash
rostopic hz /clock                                  # ~100 Hz
rostopic hz /nbuggy/livox_front/imu                 # ~200 Hz
rostopic hz /nbuggy/livox_front/points              #  ~10 Hz
rostopic hz /nbuggy/livox_front/points_processed    #  ~10 Hz (after calib)
```

## Walk pattern

Every bug follows the same recipe:

1. `git checkout <buggy-commit>` — places the tree in the buggy state
2. Rebuild what's needed (full workspace, or one library)
3. Run the reproduce command — observe the documented symptom
4. `git checkout <fix-commit>` — applies the smallest patch that
   resolves the bug
5. Rebuild and run the verify command — observe the corrected
   behaviour

A&plus;B verification (revert → reproduce → re-apply → verify) was the
discipline used during debugging to make every fix causal rather than
coincidental.

## Commit map

The submission repo's history is the bug-fix sequence in encounter
order. Each fix commit's parent is the buggy commit for the next bug.

| Bug | Buggy commit (HEAD before fix) | Fix commit | Fix message                                                                |
| --- | ------------------------------ | ---------- | -------------------------------------------------------------------------- |
| #1  | `43e3743` (baseline)           | `29aa48d`  | Restore source files lost to overaggressive CMake glob exclusion           |
| #2  | `29aa48d`                      | `263f131`  | Fix PLUGINLIB_EXPORT_CLASS symbol typo for Livox voxel grid plugin         |
| #3  | `263f131`                      | `3465e28`  | Lift YAML parameters out of unused `core:` wrapper so `input_topic` loads  |
| #4  | `3465e28`                      | `c96d252`  | Order plugin chain to match documented pipeline (deskew first)             |
| #5  | `c96d252`                      | `14bdfe2`  | Correct inverted IMU calibration staleness comparison                      |
| —   | `14bdfe2`                      | `d79ba7d`  | (Environment) Add runtime tools needed to play bags, inspect TF, run GUIs  |
| #6  | `d79ba7d`                      | `7fa8d53`  | Publish gravity-alignment TF directly from lidar frame                     |
| #7  | `7fa8d53`                      | `a0b0ec9`  | Stamp output cloud with gravity-aligned frame_id when alignment is valid   |
| #8  | `a0b0ec9`                      | `e85ce38`  | Match XML class type to renamed C++ symbol for Livox voxel grid plugin     |
| #9  | `e85ce38`                      | `0f68ecf`  | Raise IMU `buffer_size` to satisfy README invariant `buffer >= calib_time` |
| #10 | `0f68ecf`                      | `abd8e63`  | Publish gravity TF as inverse of alignment rotation                        |
| #11 | `abd8e63`                      | `59f8c8e`  | Sort scan points ascending by time so deskew integrates forward            |
| #12 | `59f8c8e`                      | `2e3bc77`  | Use median index for deskew reference, drop off-by-one                     |
| #13 | `2e3bc77`                      | `e45d40a`  | Persist deskew integrator state across scans (drop unreachable guard)      |
| #14 | (no fix — documented)          | —          | Pipeline silent during calibration window; behaviour-only finding          |

## Conventions used below

- **`git` runs on the host, not in the container.** The container
  image deliberately omits `git` (ROS runtime/build packages only),
  and `--rm` would discard any in-container apt installs anyway. Open
  a separate host shell at `~/ugv_lidar_preprocessing_submission/`
  for all `git checkout` commands. The bind mount propagates
  host-side changes into the container instantly — no rebuild, no
  re-mount.

  ```
  Host shell (git):           Container shell (build/run):
   cd ~/ugv_lidar_preprocessing_submission
   git checkout <sha>   ──►   cd /ws
                              catkin clean -y && catkin build
  ```

- **Container shells** are labelled `T1` (roscore / catkin build),
  `T2` (roslaunch), `T3` (`rosbag play`), `T4` (verification
  commands). Open new shells with `docker exec -it ugv-lidar bash`
  and source ROS each time.
- The submission tree is bind-mounted at `/ws/src/ugv_lidar_preprocessing`,
  so paths inside the container mirror the host.
- `catkin build` runs from `/ws`. Use `catkin clean -y` between bug
  walks to avoid stale objects when toggling commits.
- Stationary bag `_0` is chained before any moving bag so calibration
  completes; otherwise the pipeline stays silent (see bug #14).
- The `rosbag play` line used throughout (unless overridden):

  ```bash
  rosbag play --clock --rate 0.5 \
      /bags/2025-12-30-18-03-34_0.bag \
      /bags/2025-12-30-18-05-14_5.bag
  ```

---

## Bug #1 — CMake glob excluded all sources

**Fix commit:** `29aa48d`
**File:** `CMakeLists.txt:85`

Unanchored regex `"src/ugv_lidar_preprocessing/.*"` matches every
absolute path returned by `GLOB_RECURSE` (the catkin layout puts the
package at `<ws>/src/ugv_lidar_preprocessing/`, so that substring
appears in every path). `SOURCES` collapses to empty; `add_library`
gets no inputs.

### Reproduce

```bash
# Host
cd ~/ugv_lidar_preprocessing_submission && git checkout 43e3743

# Container T1
cd /ws && catkin clean -y && catkin build ugv_lidar_preprocessing
```

Expect:

```
CMake Error at CMakeLists.txt:86 (add_library):
  No SOURCES given to target: ugv_lidar_preprocessing
```

### Verify fix

```bash
# Host
cd ~/ugv_lidar_preprocessing_submission && git checkout 29aa48d

# Container T1
cd /ws && catkin clean -y && catkin build ugv_lidar_preprocessing
```

Expect: CMake configure step now succeeds (no `No SOURCES given`
error). The build progresses into compilation and **fails on the next
bug** (bug #2's typo) — which is expected at this commit. Fix #1 is
confirmed by the configure error disappearing and compilation
beginning.

---

## Bug #2 — `PLUGINLIB_EXPORT_CLASS` symbol typo (Livox voxel grid)

**Fix commit:** `263f131`
**File:** `src/ugv_lidar_preprocessing/plugins/plugins_exporter.cpp:62`

Macro registers the non-existent type
`LivoxVoxelGridFilterPlugins` (trailing `s`); the alias declared
earlier in the same file is `LivoxVoxelGridFilterPlugin`. Only the
Livox line has this typo.

### Reproduce

```bash
# Host  (fix #1 applied; bug #2 still present)
cd ~/ugv_lidar_preprocessing_submission && git checkout 29aa48d

# Container T1
cd /ws && catkin clean -y && catkin build ugv_lidar_preprocessing
```

Expect (the cascade of secondary errors below the first one is
expected — they're follow-on diagnostics inside the macro expansion):

```
plugins_exporter.cpp:62:53: error: 'LivoxVoxelGridFilterPlugins' in
namespace 'lidar_preprocessing_plugins' does not name a type; did you
mean 'LivoxVoxelGridFilterPlugin'?
   62 | PLUGINLIB_EXPORT_CLASS(lidar_preprocessing_plugins::LivoxVoxelGridFilterPlugins,
      |                                                     ^~~~~~~~~~~~~~~~~~~~~~~~~~~
      |                                                     LivoxVoxelGridFilterPlugin
...
make[2]: *** [...plugins_exporter.cpp.o] Error 1
Failed    <<< ugv_lidar_preprocessing                [ 21.3 seconds ]
[build] Summary: 1 of 2 packages succeeded.
[build]   Failed:    1 packages failed.
```

The first line — `error: 'LivoxVoxelGridFilterPlugins' ... does not
name a type; did you mean 'LivoxVoxelGridFilterPlugin'?` — is the
diagnostic that pinpoints the bug.

### Verify fix

```bash
# Host
cd ~/ugv_lidar_preprocessing_submission && git checkout 263f131

# Container T1
cd /ws && catkin clean -y && catkin build ugv_lidar_preprocessing
```

Expect: build succeeds:

```
[build] Summary: All 1 packages succeeded!
```

Both libraries produced:

```bash
ls /ws/devel/lib/libugv_lidar_preprocessing.so \
   /ws/devel/lib/libugv_lidar_preprocessing_plugins.so
```

The XML-side counterpart of the same typo is bug #8 — fires only at
runtime when pluginlib resolves the class.

---

## Bug #3 — YAML `core:` wrapper hid `input_topic`

**Fix commit:** `3465e28`
**File:** `config/lidar_preprocessing_params.yaml:1-2`

The YAML wraps only `input_topic` under a top-level `core:` key:

```yaml
core:
  input_topic: "livox_front/points"
```

The nodelet reads the param via `get_optional_param("input_topic", …, nh)`
where `nh` is the private node handle, so it looks up
`<priv>/input_topic`. With the wrapper the actual key is
`<priv>/core/input_topic` — never queried. The optional getter falls
back to its default `"points"` and emits a warning. The nodelet
subscribes to the wrong topic and never receives clouds. No crash,
no exception — silent failure.

### Reproduce

```bash
# Host  (fixes #1 + #2 applied; bug #3 still present)
cd ~/ugv_lidar_preprocessing_submission && git checkout 263f131

# Container T1 — build, then keep roscore running
cd /ws && catkin clean -y && catkin build && source devel/setup.bash
roscore &

# Container T2 — launch the nodelet, watch the startup log
source /opt/ros/noetic/setup.bash
source /ws/devel/setup.bash
rosparam set /use_sim_time true
roslaunch ugv_lidar_preprocessing lidar_preprocessing_nodelet.launch \
    sensor:=Livox namespace:=nbuggy
```

Expect this WARN line in T2's launch output:

```
[WARN] [<timestamp>]: Optional parameter input_topic not set, using default value
```

Confirm the param landed at the wrong key (in a third shell):

```bash
# Container T3
source /opt/ros/noetic/setup.bash

# Where the YAML actually put the key (proves the bug):
rosparam get /nbuggy/ugv_lidar_pre_processing_nodelet/core/input_topic
# expect: livox_front/points

# Where the C++ looks for it (the lookup the optional getter performs):
rosparam get /nbuggy/ugv_lidar_pre_processing_nodelet/input_topic
# expect: ERROR: Parameter [/nbuggy/ugv_lidar_pre_processing_nodelet/input_topic] is not set
```

Note: `rosnode info` against the nodelet only shows the `bond/Status`
subscription — the pointcloud subscription is owned by the manager
process, not the nodelet's logical node, so it is not visible there.
Use the `rosparam get` pair above instead.

### Verify fix

```bash
# Host
cd ~/ugv_lidar_preprocessing_submission && git checkout 3465e28

# Container T2 — Ctrl-C the roslaunch, then re-launch
roslaunch ugv_lidar_preprocessing lidar_preprocessing_nodelet.launch \
    sensor:=Livox namespace:=nbuggy
```

Expect: no `Optional parameter input_topic not set` line in the
launch log. The two `rosparam get` commands swap behaviour:

```bash
rosparam get /nbuggy/ugv_lidar_pre_processing_nodelet/core/input_topic
# expect: ERROR (key removed by the YAML restructure)

rosparam get /nbuggy/ugv_lidar_pre_processing_nodelet/input_topic
# expect: livox_front/points
```

No rebuild needed for this fix — YAML is reloaded by `roslaunch` at
launch time.

Note: the same launch will also show
`Plugin Execution Order ... livox_tag_filter -> deskew -> gravity_align`,
which is bug #4 surfacing in the same log. Fix #3 first
(it came first in the log); bug #4 is the next entry.

---

## Bug #4 — Plugin execution order did not match documented pipeline

**Fix commit:** `c96d252`
**File:** `src/lidar_preprocessing_nodelet.cpp:523`

The `kPluginOrder` constexpr array iterated as
`{ror, livox_tag, deskew, voxel, gravity_align}`. The README and the
architectural intent require
`{deskew, gravity_align, voxel, ror, livox_tag}`. With only deskew,
gravity_align, and livox_tag enabled (the YAML default), the startup
log shows the wrong chain. Most concerning: `livox_tag` runs BEFORE
`deskew`, dropping (0,0,0) sentinel points before the deskew step
sees the full per-point timestamp distribution.

### Reproduce

```bash
# Host  (fixes #1 + #2 + #3 applied; bug #4 still present)
cd ~/ugv_lidar_preprocessing_submission && git checkout 3465e28

# Container T1 — rebuild (C++ change, unlike YAML bug #3)
cd /ws && catkin clean -y && catkin build && source devel/setup.bash

# Container T2 — Ctrl-C any running roslaunch, then re-launch
roslaunch ugv_lidar_preprocessing lidar_preprocessing_nodelet.launch \
    sensor:=Livox namespace:=nbuggy
```

Expect this INFO line in T2's log:

```
[INFO] [<timestamp>]: Plugin Execution Order for enabled preprocessors:
       livox_tag_filter -> deskew -> gravity_align
```

(Disabled plugins — voxel_grid, ROR — are correctly omitted in both
the buggy and the fixed code; only the order of *enabled* ones is wrong.)

Optional: enable voxel_grid + ROR via dynparam to see the full buggy chain:

```bash
# Container T3
rosrun dynamic_reconfigure dynparam set \
    /nbuggy/ugv_lidar_pre_processing_nodelet voxel_grid_filter_enabled true
rosrun dynamic_reconfigure dynparam set \
    /nbuggy/ugv_lidar_pre_processing_nodelet radius_outlier_removal_enabled true
```

T2's log will now print the full buggy chain:
`ror -> livox_tag_filter -> deskew -> voxel_grid -> gravity_align`,
mirroring the buggy `kPluginOrder` array exactly.

WARNING: enabling voxel_grid at this commit also surfaces bug #8 as
a side effect:

```
[ERROR] Failed to load plugin 'voxel_grid': MultiLibraryClassLoader:
        Could not create object of class type
        lidar_preprocessing_plugins::LivoxVoxelGridFilterPlugins as no
        factory exists for it.
```

That is the XML-side counterpart of the same typo bug #2 fixed on the
C++ side — see the bug #8 section. The execution-order line still
prints correctly with `voxel_grid` in the buggy position before the
load attempt fails, so the bug #4 verification stands. If you want a
clean bug #4 reproduction without the bug #8 noise, skip this dynparam
step (the three-plugin default chain
`livox_tag_filter -> deskew -> gravity_align` is enough to confirm
bug #4).

### Verify fix

```bash
# Host
cd ~/ugv_lidar_preprocessing_submission && git checkout c96d252

# Container T1 — rebuild
cd /ws && catkin clean -y && catkin build && source devel/setup.bash

# Container T2 — Ctrl-C, re-launch
roslaunch ugv_lidar_preprocessing lidar_preprocessing_nodelet.launch \
    sensor:=Livox namespace:=nbuggy
```

Expect:

```
[INFO] [<timestamp>]: Plugin Execution Order for enabled preprocessors:
       deskew -> gravity_align -> livox_tag_filter
```

If you re-enable voxel_grid + ROR via dynparam, the order becomes:
`deskew -> gravity_align -> voxel_grid -> ror -> livox_tag_filter` —
the full README-documented pipeline.

---

## Bug #5 — Inverted staleness check blocked IMU calibration forever

**Fix commit:** `14bdfe2`
**File:** `src/ugv_lidar_preprocessing/utils/imu_integrator.cpp:82`

Predicate inverted: code checks `velocity_age < max_age` and marks
the sample stale, but "stale" means `velocity_age > max_age`. Fresh
samples are rejected as stale; calibration never completes; the
pipeline runs but `points_processed` never publishes. The WARN log
line is self-contradictory — it prints `age 0.031 s > 0.500 s` when
0.031 is not greater than 0.500, exposing the mismatch between the
message format (assumes `>`) and the buggy code (uses `<`).

This is the first bug that needs bags playing — the calibration
logic only runs when IMU and external odometry samples are flowing.

### Reproduce

```bash
# Host  (fixes #1..#4 applied; bug #5 still present)
cd ~/ugv_lidar_preprocessing_submission && git checkout c96d252

# Container T1 — roscore must be running; rebuild
pgrep -af roscore || (roscore &)
cd /ws && catkin clean -y && catkin build && source devel/setup.bash

# Container T2 — launch the nodelet
source /opt/ros/noetic/setup.bash
source /ws/devel/setup.bash
rosparam set /use_sim_time true
roslaunch ugv_lidar_preprocessing lidar_preprocessing_nodelet.launch \
    sensor:=Livox namespace:=nbuggy

# Container T3 — play the STATIONARY bag (mandatory; moving bags hit
# a different gate that masks bug #5)
source /opt/ros/noetic/setup.bash
rosbag play --clock --rate 0.5 /bags/2025-12-30-18-03-34_0.bag
```

Expect repeating WARN lines in T2's log:

```
[WARN] [<timestamp>]: IMU calibration waiting: external velocity stale
       (age 0.031 s > 0.500 s)
```

Note `0.031 > 0.500` is mathematically false — that contradiction
between message and value is the tell.

Confirm no output flows even after the bag has been playing for >3 s:

```bash
# Container T4
source /opt/ros/noetic/setup.bash
rostopic hz /nbuggy/livox_front/points_processed
# expect: "no new messages" — calibration is permanently blocked
```

For comparison, the upstream topics ARE flowing (the nodelet itself
is alive):

```bash
rostopic hz /nbuggy/livox_front/points    # ~10 Hz
rostopic hz /nbuggy/livox_front/imu       # ~200 Hz
rostopic hz /nbuggy/odom                  # has messages
```

### Verify fix

```bash
# Host
cd ~/ugv_lidar_preprocessing_submission && git checkout 14bdfe2

# Container T1 — rebuild
cd /ws && catkin clean -y && catkin build && source devel/setup.bash

# Container T2 — Ctrl-C, re-launch
roslaunch ugv_lidar_preprocessing lidar_preprocessing_nodelet.launch \
    sensor:=Livox namespace:=nbuggy

# Container T3 — replay stationary bag
rosbag play --clock --rate 0.5 /bags/2025-12-30-18-03-34_0.bag
```

Expect within ~3 s of bag-time start, T2's log shows:

```
[INFO] [<timestamp>]: Calibration complete
```

The "stale" warning is gone. Output now flows:

```bash
# Container T4
rostopic hz /nbuggy/livox_front/points_processed
# expect: ~10 Hz
```

---

## Bug #6 — Gravity TF lookup against a frame that doesn't exist

**Fix commit:** `7fa8d53`
**File:** `src/lidar_preprocessing_nodelet.cpp:1082-1117`

`publish_gravity_alignment_tf` tried to publish the gravity TF
parented at `m_gravity_parent_frame` (`nbuggy/base_footprint`),
requiring a `base_footprint → lidar_frame` lookup against the live
TF buffer. The bag's TF tree only contains `odom → base_footprint` —
no link reaches the lidar. Lookup throws on every scan; the gravity
TF is never published.

The fix removes the lookup-and-compose entirely and publishes
`lidar_frame → <lidar_frame>_gravity_frame` directly with zero
translation and the alignment rotation. Gravity_align is a per-sensor
rotation; there is no semantic need to involve `base_footprint`.

### Reproduce

```bash
# Host  (fixes #1..#5 applied; bug #6 still present)
cd ~/ugv_lidar_preprocessing_submission && git checkout 14bdfe2

# Container T1 — rebuild
pgrep -af roscore || (roscore &)
cd /ws && catkin clean -y && catkin build && source devel/setup.bash

# Container T2 — launch
source /opt/ros/noetic/setup.bash
source /ws/devel/setup.bash
rosparam set /use_sim_time true
roslaunch ugv_lidar_preprocessing lidar_preprocessing_nodelet.launch \
    sensor:=Livox namespace:=nbuggy

# Container T3 — play stationary bag
source /opt/ros/noetic/setup.bash
rosbag play --clock --rate 0.5 /bags/2025-12-30-18-03-34_0.bag
```

Expect repeating WARN lines in T2's log (throttled to ~once per 2 s):

```
[WARN] [<timestamp>]: Failed to lookup TF from 'nbuggy/livox_front'
to 'nbuggy/base_footprint': "nbuggy/livox_front" passed to
lookupTransform argument source_frame does not exist.
```

Confirm the gravity TF is never published:

```bash
# Container T4
source /opt/ros/noetic/setup.bash
rosrun tf tf_echo nbuggy/livox_front nbuggy/livox_front_gravity_frame
# expect: "Failure at <time>" / "Could not find a connection between
# 'nbuggy/livox_front' and 'nbuggy/livox_front_gravity_frame'"
```

The actual TF tree (for context):

```bash
rostopic echo -n5 /tf | grep -E "frame_id|child_frame_id"
# expect only: nbuggy/odom -> nbuggy/base_footprint
# (no link to any lidar frame)
```

### Verify fix

```bash
# Host
cd ~/ugv_lidar_preprocessing_submission && git checkout 7fa8d53

# Container T1 — rebuild
cd /ws && catkin clean -y && catkin build && source devel/setup.bash

# Container T2 — Ctrl-C, re-launch
roslaunch ugv_lidar_preprocessing lidar_preprocessing_nodelet.launch \
    sensor:=Livox namespace:=nbuggy

# Container T3 — Ctrl-C if running, replay stationary bag
rosbag play --clock --rate 0.5 /bags/2025-12-30-18-03-34_0.bag
```

Expect: no `Failed to lookup TF` warnings. The gravity TF is now
published every scan:

```bash
# Container T4
rosrun tf tf_echo nbuggy/livox_front nbuggy/livox_front_gravity_frame
# expect: zero translation, small non-identity rotation, e.g.
#   - Translation: [0.000, 0.000, 0.000]
#   - Rotation: in RPY (degree) [~0.1, ~-0.6, 0.000]
```

The small RPY values are the lidar mounting tilt + body roll/pitch
that gravity_align is correcting for. Yaw is exactly zero because
gravity_align cannot determine yaw from gravity alone.

Note: bug #7 (processed cloud kept raw frame_id) is also present at
this commit and is not visible in the log. It only shows when you
inspect the processed cloud's `frame_id` directly. Covered next.

---

## Bug #7 — Processed cloud kept the raw lidar's `frame_id`

**Fix commit:** `a0b0ec9`
**File:** `src/lidar_preprocessing_nodelet.cpp:1058-1062`

`publish_output` copies `input_msg->header` (including `frame_id`)
into the output message, then has an `if (get_gravity_alignment(...))`
guard whose body was empty — with a misleading comment claiming
"Intentionally keep the original frame_id even when alignment is
available." The README contract requires the output frame_id to be
rewritten to `<input_frame>_gravity_frame` when alignment is active.
Result: the output cloud's geometry is gravity-aligned but its
header still claims `nbuggy/livox_front`. Consumers (RViz, downstream
nodes) misrender the cloud at the un-rotated lidar pose. Silent — no
log line, no exception.

The fix is one line inside the `if` block, setting
`output_msg.header.frame_id = gravity_aligned_frame(input_msg->header.frame_id)`.

### Reproduce

```bash
# Host  (fixes #1..#6 applied; bug #7 still present)
cd ~/ugv_lidar_preprocessing_submission && git checkout 7fa8d53

# Container T1 — rebuild
pgrep -af roscore || (roscore &)
cd /ws && catkin clean -y && catkin build && source devel/setup.bash

# Container T2 — launch
source /opt/ros/noetic/setup.bash
source /ws/devel/setup.bash
rosparam set /use_sim_time true
roslaunch ugv_lidar_preprocessing lidar_preprocessing_nodelet.launch \
    sensor:=Livox namespace:=nbuggy

# Container T3 — play stationary bag
source /opt/ros/noetic/setup.bash
rosbag play --clock --rate 0.5 /bags/2025-12-30-18-03-34_0.bag
```

After calibration completes (~3 s), inspect the processed cloud's
header:

```bash
# Container T4
source /opt/ros/noetic/setup.bash
rostopic echo -n1 /nbuggy/livox_front/points_processed | grep frame_id
# expect: frame_id: "nbuggy/livox_front"
```

That's the bug — the cloud's header still names the un-aligned frame
even though gravity_align is active and the points are in the
gravity-aligned frame.

For comparison, the raw cloud has the same frame_id (correctly):

```bash
rostopic echo -n1 /nbuggy/livox_front/points | grep frame_id
# expect: frame_id: "nbuggy/livox_front"  (same as processed — that's the bug)
```

### Verify fix

```bash
# Host
cd ~/ugv_lidar_preprocessing_submission && git checkout a0b0ec9

# Container T1 — rebuild
cd /ws && catkin clean -y && catkin build && source devel/setup.bash

# Container T2 — Ctrl-C, re-launch
roslaunch ugv_lidar_preprocessing lidar_preprocessing_nodelet.launch \
    sensor:=Livox namespace:=nbuggy

# Container T3 — Ctrl-C if running, replay stationary bag
rosbag play --clock --rate 0.5 /bags/2025-12-30-18-03-34_0.bag
```

After calibration completes, the processed cloud's header now names
the gravity-aligned frame:

```bash
# Container T4
rostopic echo -n1 /nbuggy/livox_front/points_processed | grep frame_id
# expect: frame_id: "nbuggy/livox_front_gravity_frame"
```

Combined check that fixes #6 and #7 together produce a coherent
gravity-aligned pipeline:

```bash
# 1. Cloud claims to be in the gravity-aligned frame
rostopic echo -n1 /nbuggy/livox_front/points_processed | grep frame_id
# expect: frame_id: "nbuggy/livox_front_gravity_frame"

# 2. The gravity-aligned frame exists in the TF tree
rosrun tf tf_echo nbuggy/livox_front nbuggy/livox_front_gravity_frame
# expect: zero translation, small RPY rotation
```

Both must succeed for downstream consumers to render and transform
the gravity-aligned cloud correctly.

---

## Bug #8 — XML class type mismatch (Livox voxel grid)

**Fix commit:** `e85ce38`
**File:** `lidar_preprocessing_plugins.xml:75`

Same trailing `s` typo as bug #2, but on the XML side. The
`<class type="...">` attribute reads
`LivoxVoxelGridFilterPlugins` while the C++ side
(post-fix-#2) registers `LivoxVoxelGridFilterPlugin`. Pluginlib
parses the XML, asks `dlsym` for the typo'd symbol, finds nothing,
and fails to instantiate. Build is unaffected (XML is not validated
at compile time); only the runtime instantiation of `voxel_grid`
hits the error.

### Reproduce

```bash
# Host  (fixes #1..#7 applied; bug #8 still present)
cd ~/ugv_lidar_preprocessing_submission && git checkout a0b0ec9

# Container T1 — rebuild
pgrep -af roscore || (roscore &)
cd /ws && catkin clean -y && catkin build && source devel/setup.bash

# Container T2 — launch
source /opt/ros/noetic/setup.bash
source /ws/devel/setup.bash
rosparam set /use_sim_time true
roslaunch ugv_lidar_preprocessing lidar_preprocessing_nodelet.launch \
    sensor:=Livox namespace:=nbuggy

# Container T3 — bag is optional for this bug; calibration is unrelated.
# But we want a clean log to see the error in isolation.
source /opt/ros/noetic/setup.bash
rosbag play --clock --rate 0.5 /bags/2025-12-30-18-03-34_0.bag
```

Trigger the load attempt (in T4):

```bash
# Container T4
source /opt/ros/noetic/setup.bash
rosrun dynamic_reconfigure dynparam set \
    /nbuggy/ugv_lidar_pre_processing_nodelet voxel_grid_filter_enabled true
```

Expect this ERROR line in T2's log:

```
[ERROR] [<timestamp>]: Failed to load plugin 'voxel_grid':
MultiLibraryClassLoader: Could not create object of class type
lidar_preprocessing_plugins::LivoxVoxelGridFilterPlugins as no factory
exists for it. Make sure that the library exists and was explicitly
loaded through MultiLibraryClassLoader::loadLibrary()
```

Confirm the XML has the typo:

```bash
# Container T4 (or any sourced shell)
grep "LivoxVoxelGridFilter" /ws/src/ugv_lidar_preprocessing/lidar_preprocessing_plugins.xml
# expect: type="lidar_preprocessing_plugins::LivoxVoxelGridFilterPlugins"
```

And confirm the C++ side has NO trailing `s` (post-fix-#2):

```bash
grep "LivoxVoxelGridFilter" \
    /ws/src/ugv_lidar_preprocessing/src/ugv_lidar_preprocessing/plugins/plugins_exporter.cpp
# expect: ...LivoxVoxelGridFilterPlugin (no trailing s)
```

The two-line diff isolates the mismatch to the XML.

### Verify fix

```bash
# Host
cd ~/ugv_lidar_preprocessing_submission && git checkout e85ce38

# Container T1 — rebuild (re-stages the XML into /ws/devel; fast, no C++ recompile)
cd /ws && catkin build && source devel/setup.bash

# Container T2 — Ctrl-C, re-launch
roslaunch ugv_lidar_preprocessing lidar_preprocessing_nodelet.launch \
    sensor:=Livox namespace:=nbuggy

# Container T3 — Ctrl-C if running, replay stationary bag
rosbag play --clock --rate 0.5 /bags/2025-12-30-18-03-34_0.bag

# Container T4 — toggle voxel_grid on
rosrun dynamic_reconfigure dynparam set \
    /nbuggy/ugv_lidar_pre_processing_nodelet voxel_grid_filter_enabled true
```

Expect: no `Failed to load plugin 'voxel_grid'` error. T2's log shows
the plugin loaded successfully and the execution order updates:

```
[INFO] [<timestamp>]: Plugin Execution Order for enabled preprocessors:
       deskew -> gravity_align -> voxel_grid -> livox_tag_filter
```

Confirm the XML is now correct:

```bash
grep "LivoxVoxelGridFilter" /ws/src/ugv_lidar_preprocessing/lidar_preprocessing_plugins.xml
# expect: type="lidar_preprocessing_plugins::LivoxVoxelGridFilterPlugin"  (no s)
```

Optional behavioural check — the voxel grid is now actually
filtering points. Compare counts:

```bash
# Container T4 — set a coarse leaf size for visible reduction
rosrun dynamic_reconfigure dynparam set \
    /nbuggy/ugv_lidar_pre_processing_nodelet voxel_grid_filter_leaf_size 0.5

# Compare raw vs processed point counts
rostopic echo -n1 /nbuggy/livox_front/points           | grep "width"
rostopic echo -n1 /nbuggy/livox_front/points_processed | grep "width"
# expect: processed << raw  (e.g. 4,200 vs 45,000)
```

---

## Bug #9 — `buffer_size` violated documented invariant

**Fix commit:** `0f68ecf`
**File:** `config/lidar_preprocessing_params.yaml:5`

YAML shipped with `imu_params/buffer_size: 1.0` while
`imu_params/calibration/time: 3`. The README explicitly requires
`buffer_size >= calibration/time` so calibration has enough buffered
samples. No runtime symptom on the supplied bags — the calibration
accumulator is decoupled from the buffer, so calibration completes
even when the buffer is shorter than `calibration/time`. Bug found
by contract-reading (README vs YAML), not by observation.

Why it still matters: (a) shipped default contradicts documented
invariant; (b) latent failure if calibration is later refactored to
read back from the buffer, or if `calibration/time` is increased.

### Reproduce

This bug has no runtime symptom on the supplied bags. "Reproduction"
is showing the contract violation; "verification" is showing the
contract holding.

```bash
# Host  (fixes #1..#8 applied; bug #9 still present)
cd ~/ugv_lidar_preprocessing_submission && git checkout e85ce38

# Static check — read the YAML and confirm the invariant violation
grep -E "buffer_size|^\s*time:" \
    /ws/src/ugv_lidar_preprocessing/config/lidar_preprocessing_params.yaml
# expect:
#   buffer_size: 1.0 # Seconds of IMU data to buffer for deskewing
#       time: 3
# 1.0 < 3 → invariant `buffer_size >= calibration/time` violated
```

Confirm at runtime (parameters loaded from YAML):

```bash
# Container T1 — roscore + build
pgrep -af roscore || (roscore &)
cd /ws && catkin build && source devel/setup.bash

# Container T2 — launch
source /opt/ros/noetic/setup.bash
source /ws/devel/setup.bash
rosparam set /use_sim_time true
roslaunch ugv_lidar_preprocessing lidar_preprocessing_nodelet.launch \
    sensor:=Livox namespace:=nbuggy &

sleep 2

# Container T2 — confirm the loaded params show the violation
rosparam get /nbuggy/ugv_lidar_pre_processing_nodelet/imu_params/buffer_size
# expect: 1.0
rosparam get /nbuggy/ugv_lidar_pre_processing_nodelet/imu_params/calibration/time
# expect: 3
```

Note: a stationary bag still completes calibration and `points_processed`
still flows — the bug is *latent*, not observable on this dataset.

### Verify fix

```bash
# Host
cd ~/ugv_lidar_preprocessing_submission && git checkout 0f68ecf

# YAML-only fix — no C++ recompile needed; just relaunch
# Container T2 — Ctrl-C, re-launch
roslaunch ugv_lidar_preprocessing lidar_preprocessing_nodelet.launch \
    sensor:=Livox namespace:=nbuggy &
sleep 2

rosparam get /nbuggy/ugv_lidar_pre_processing_nodelet/imu_params/buffer_size
# expect: 3.0  (was 1.0)
```

Static re-check:

```bash
grep -E "buffer_size|^\s*time:" \
    /ws/src/ugv_lidar_preprocessing/config/lidar_preprocessing_params.yaml
# expect:
#   buffer_size: 3.0 # ... (must be >= calibration/time)
#       time: 3
# 3.0 >= 3 → invariant satisfied
```

Regression-style behavioural check:
- Stationary bag still completes calibration in ~3 s.
- `rostopic hz /nbuggy/livox_front/points_processed` still ~10 Hz.
- Deskew quality unchanged on the supplied bags.

---

## Bug #10 — Gravity TF rotation published in the wrong direction

**Fix commit:** `abd8e63`
**File:** `src/lidar_preprocessing_nodelet.cpp:1085-1098`

`publish_gravity_alignment_tf` stored the **same `align_q`** that the
gravity_align plugin uses to rotate points (`p_gravity = align_q * p_lidar`).
ROS TF convention requires the published rotation to be the inverse —
the rotation that takes a vector from child (gravity_frame) coordinates
to parent (lidar_frame) coordinates: `p_lidar = align_q.conjugate() * p_gravity`.
With the bug present, consumers that ask TF to convert points back to
the lidar frame apply `align_q` again, picking up `align_q² * p_lidar`
— the rotation gets applied twice. Visible in RViz as a vertical gap
between raw and processed clouds that grows linearly with range
(~17 cm at 10 m, ~35 cm at 20 m for a typical 0.5° tilt).

The fix takes the conjugate before publishing:
`const Eigen::Quaternionf tf_q = align_q.conjugate();`

### Reproduce

```bash
# Host  (fixes #1..#9 applied; bug #10 still present)
cd ~/ugv_lidar_preprocessing_submission && git checkout 0f68ecf

# Container T1 — rebuild
pgrep -af roscore || (roscore &)
cd /ws && catkin clean -y && catkin build && source devel/setup.bash

# Container T2 — launch
source /opt/ros/noetic/setup.bash
source /ws/devel/setup.bash
rosparam set /use_sim_time true
roslaunch ugv_lidar_preprocessing lidar_preprocessing_nodelet.launch \
    sensor:=Livox namespace:=nbuggy

# Container T3 — play stationary bag
source /opt/ros/noetic/setup.bash
rosbag play --clock --rate 0.5 /bags/2025-12-30-18-03-34_0.bag
```

After calibration completes, compare the published TF rotation to the
expected direction. The buggy TF stores `align_q` directly, so its
RPY should match the *forward* alignment direction (the rotation
applied to the points):

```bash
# Container T4
source /opt/ros/noetic/setup.bash
rosrun tf tf_echo nbuggy/livox_front nbuggy/livox_front_gravity_frame
# expect: zero translation, RPY signs match the lidar's tilt direction
# (e.g., positive pitch if the lidar is mounted nose-up)
```

Optional visual proof — open RViz, set Fixed Frame to
`nbuggy/livox_front`, display both `/nbuggy/livox_front/points` (raw,
red) and `/nbuggy/livox_front/points_processed` (processed, green).
The processed cloud will appear *rotated by twice the alignment angle*
relative to the raw cloud — a vertical gap that grows linearly with
range.

### Verify fix

```bash
# Host
cd ~/ugv_lidar_preprocessing_submission && git checkout abd8e63

# Container T1 — rebuild
cd /ws && catkin clean -y && catkin build && source devel/setup.bash

# Container T2 — Ctrl-C, re-launch
roslaunch ugv_lidar_preprocessing lidar_preprocessing_nodelet.launch \
    sensor:=Livox namespace:=nbuggy

# Container T3 — Ctrl-C if running, replay stationary bag
rosbag play --clock --rate 0.5 /bags/2025-12-30-18-03-34_0.bag
```

After calibration completes, the TF rotation has flipped sign on
roll/pitch (yaw stays at zero):

```bash
# Container T4
rosrun tf tf_echo nbuggy/livox_front nbuggy/livox_front_gravity_frame
# expect: same magnitudes as before, but with roll and pitch signs flipped
# This is the algebraic signature of taking the conjugate.
```

Optional visual proof: in RViz with both clouds displayed in the
lidar fixed frame, raw and processed now overlay exactly when
stationary — confirming the TF correctly inverts the gravity
rotation and consumers round-trip back to the original points.

---

## Bug #11 — Sort comparator descending instead of ascending

**Fix commit:** `59f8c8e`
**File:** `src/lidar_preprocessing_nodelet.cpp:738`

`sort_points_by_time` used `>` instead of `<` in the comparator,
sorting points **descending** by per-point timestamp. Downstream
code (deskew and gravity_align) assumes ascending order and computes
its `time_offset` from `points.front()` (gravity_align) and
`points.back()` (deskew). Reversed order makes both compute the
wrong reference time, and the IMU integrator is fed a reversed
timeline — the per-point rotation correction is applied with the
wrong sign on roughly half the points.

Symptom: with the buggy moving, the processed cloud appears
visibly **shaky** — frame-to-frame jitter, smear pointing the wrong
way along the motion axis. The signature: deskew ON looks *worse*
than deskew OFF — the wrong sign for a working filter.

### Reproduce

For this bug, switch the YAML to point at `livox_rear_right` instead
of the default `livox_front`. The rear_right lidar makes the
wrong-sign deskew artefact dramatically more visible because of its
mounting geometry, range coverage, and rotational dynamics during
motion (see audit finding F5 for context on its gyro profile).

```bash
# Host  (fixes #1..#10 applied; bug #11 still present)
cd ~/ugv_lidar_preprocessing_submission && git checkout abd8e63

# Host — temporarily switch YAML to livox_rear_right
sed -i 's|livox_front/points|livox_rear_right/points|g; s|livox_front/imu|livox_rear_right/imu|g' \
    config/lidar_preprocessing_params.yaml

# Confirm the swap
grep -E "input_topic|topic:" config/lidar_preprocessing_params.yaml | head -3
# expect:
#   input_topic: "livox_rear_right/points"
#     topic: "livox_rear_right/imu"

# Container T1 — rebuild
pgrep -af roscore || (roscore &)
cd /ws && catkin clean -y && catkin build && source devel/setup.bash

# Container T2 — launch
source /opt/ros/noetic/setup.bash
source /ws/devel/setup.bash
rosparam set /use_sim_time true
roslaunch ugv_lidar_preprocessing lidar_preprocessing_nodelet.launch \
    sensor:=Livox namespace:=nbuggy

# Container T3 — chain stationary first, then MOVING bag _7 (4.6 m/s)
source /opt/ros/noetic/setup.bash
rosbag play --clock --rate 0.5 \
    /bags/2025-12-30-18-03-34_0.bag \
    /bags/2025-12-30-18-05-54_7.bag
```

A/B test deskew on/off via dynparam (in T4) once the moving portion
plays:

```bash
# Container T4
source /opt/ros/noetic/setup.bash

# Disable deskew → green should LOOK BETTER (more stable) than with deskew on
rosrun dynamic_reconfigure dynparam set \
    /nbuggy/ugv_lidar_pre_processing_nodelet pointcloud_deskew_enabled false

# Re-enable → green now looks WORSE (shakier) — that wrong-sign signature is the bug
rosrun dynamic_reconfigure dynparam set \
    /nbuggy/ugv_lidar_pre_processing_nodelet pointcloud_deskew_enabled true
```

In RViz with raw (red) and processed (green) clouds for
`/nbuggy/livox_rear_right/...` displayed in the lidar fixed frame,
the buggy deskew makes vertical poles and building edges *more*
smeared than the raw cloud during fast motion. The effect is much
larger than on `livox_front` because of rear_right's mounting and
range profile — the wrong-sign per-point rotations sweep features
through a larger arc.

Code-side static check (proves the comparator direction):

```bash
grep -A3 "sort_points_by_time" \
    /ws/src/ugv_lidar_preprocessing/src/lidar_preprocessing_nodelet.cpp | grep "time_seconds"
# expect: ... time_seconds(lhs, sweep_ref_time) >    (descending — bug)
```

### Verify fix

```bash
# Host
cd ~/ugv_lidar_preprocessing_submission && git checkout 59f8c8e

# Re-apply the rear_right YAML override (git checkout reset it to livox_front)
sed -i 's|livox_front/points|livox_rear_right/points|g; s|livox_front/imu|livox_rear_right/imu|g' \
    config/lidar_preprocessing_params.yaml

# Container T1 — rebuild
cd /ws && catkin clean -y && catkin build && source devel/setup.bash

# Container T2 — Ctrl-C, re-launch
roslaunch ugv_lidar_preprocessing lidar_preprocessing_nodelet.launch \
    sensor:=Livox namespace:=nbuggy

# Container T3 — Ctrl-C if running, replay chain
rosbag play --clock --rate 0.5 \
    /bags/2025-12-30-18-03-34_0.bag \
    /bags/2025-12-30-18-05-54_7.bag
```

Repeat the dynparam A/B in T4. With the fix:

- **Deskew off:** green ≈ red (deskew is a no-op when disabled).
- **Deskew on:** green is *steadier* than red on stationary features
  and *sharper* than red on vertical features at peak motion.
  The shaky-when-deskew-on symptom is gone.

Code-side static check:

```bash
grep -A3 "sort_points_by_time" \
    /ws/src/ugv_lidar_preprocessing/src/lidar_preprocessing_nodelet.cpp | grep "time_seconds"
# expect: ... time_seconds(lhs, sweep_ref_time) <    (ascending — fixed)
```

### Restore default YAML when done with bug #11

```bash
# Host — discard the rear_right override, return YAML to shipped state
cd ~/ugv_lidar_preprocessing_submission
git checkout -- config/lidar_preprocessing_params.yaml

# Confirm it's back to livox_front
grep -E "input_topic|topic:" config/lidar_preprocessing_params.yaml | head -3
# expect:
#   input_topic: "livox_front/points"
#     topic: "livox_front/imu"
```

Subsequent bug walks resume on `livox_front`. Skipping this restore
will cause subsequent bugs' `rostopic` / `tf_echo` commands to look
for `livox_front` topics that aren't being processed.

---

## Bug #12 — `reference_index` off-by-one

**Fix commit:** `2e3bc77`
**File:** `src/ugv_lidar_preprocessing/plugins/pointcloud_deskew_plugin.cpp:92`

Buggy:
```cpp
std::size_t reference_index = timestamps.size() / 2 + 1;  // off by one
```
Fixed:
```cpp
std::size_t reference_index = timestamps.size() / 2;       // median
```

The `+ 1` makes the index one past the median, contradicting the
"median timestamp as the reference" intent in the comment immediately
above. On the supplied bags (~45,000 points per scan) the off-by-one
stays well in-bounds and the chosen reference shifts by less than a
microsecond — no observable effect. On a small cloud (`size <= 1`)
the index would be **out of bounds**, the integrator validator
rejects the result, and the scan is silently dropped.

This is a Tier 2 / static-review bug — caught by reading code, not
by running it. No observable symptom on the supplied dataset.

### Reproduce

Code-side proof:

```bash
# Container T4 (or any sourced shell)
grep -B1 "reference_index" \
    /ws/src/ugv_lidar_preprocessing/src/ugv_lidar_preprocessing/plugins/pointcloud_deskew_plugin.cpp \
    | head -6
# expect:
#   // Take the median timestamp as the reference
#   std::size_t reference_index = timestamps.size() / 2 + 1;
# The code's stated intent ("median") and its actual computation ("median + 1") disagree.
```

Behavioural reproduction would require a synthetic small-cloud test
that the supplied bags don't trigger.

### Verify fix

```bash
# Host
cd ~/ugv_lidar_preprocessing_submission && git checkout 2e3bc77

# Container T1 — rebuild
cd /ws && catkin clean -y && catkin build && source devel/setup.bash

# Static check
grep -B1 "reference_index" \
    /ws/src/ugv_lidar_preprocessing/src/ugv_lidar_preprocessing/plugins/pointcloud_deskew_plugin.cpp \
    | head -6
# expect: std::size_t reference_index = timestamps.size() / 2;   (no + 1)
```

Regression check on supplied bags: deskew quality unchanged
(both before and after produce the same processed cloud at full
~45k points per scan because the reference timestamp shift is sub-µs).

---

## Bug #13 — Integrator state never persisted across scans (unreachable guard)

**Fix commit:** `e45d40a`
**File:** `src/ugv_lidar_preprocessing/plugins/pointcloud_deskew_plugin.cpp:134`

Buggy:
```cpp
if (result.reference_state_valid && reference_index == 0)
{
    m_imu_integrator->set_state(result.reference_state);
}
```
Fixed:
```cpp
if (result.reference_state_valid)
{
    m_imu_integrator->set_state(result.reference_state);
}
```

After fix #12, `reference_index = size / 2 ≥ 1` for any non-empty
cloud. The `&& reference_index == 0` clause is therefore
**unreachable** — `set_state` is dead code. The integrator's running
state (velocity, bias updates) never gets pushed back into the
singleton, so each scan re-bootstraps from the calibrated zero state.
Within-scan deskew can recover quickly, but the back-propagation step
is starved of inter-scan context.

Subtle effect on a single scan; cumulatively important for any code
path that relies on multi-scan integrator continuity.

### Reproduce

Code-side proof — the guard makes the body unreachable after fix #12:

```bash
grep -B1 -A4 "set_state" \
    /ws/src/ugv_lidar_preprocessing/src/ugv_lidar_preprocessing/plugins/pointcloud_deskew_plugin.cpp \
    | head -10
# expect:
#   if (result.reference_state_valid && reference_index == 0)
#   {
#       m_imu_integrator->set_state(result.reference_state);
#   }
# Combined with reference_index = size/2 from fix #12, the second clause
# can never be true, so set_state never fires.
```

To prove unreachability empirically, one could add a debug
`NODELET_INFO_STREAM("set_state called")` line and observe it never
prints during bag playback.

### Verify fix

```bash
# Host
cd ~/ugv_lidar_preprocessing_submission && git checkout e45d40a

# Container T1 — rebuild
cd /ws && catkin clean -y && catkin build && source devel/setup.bash

# Static check
grep -B1 -A4 "set_state" \
    /ws/src/ugv_lidar_preprocessing/src/ugv_lidar_preprocessing/plugins/pointcloud_deskew_plugin.cpp \
    | head -10
# expect:
#   if (result.reference_state_valid)
#   {
#       m_imu_integrator->set_state(result.reference_state);
#   }
```

Regression check: deskew quality on supplied bags unchanged. The
behavioural difference only manifests on multi-scan integrator
continuity, which the supplied workload doesn't directly exercise.

---

## Bug #14 — Pipeline silent during the calibration window

**Status:** Documented; no code change.
**File:** `src/lidar_preprocessing_nodelet.cpp:771-775`

During the ~3-second calibration window, the nodelet returns from
its pointcloud callback **before** publishing:

```cpp
if (gate_status && gate_status->calibration_enabled)
    return;
```

So `/<ns>/livox_*/points_processed` is silent for the first ~3 s of
bag time. After calibration completes, output flows at 10 Hz.

Whether this is a defect is interpretive — the README doesn't
specify a contract for "behaviour during calibration." Conservative
choice (current code): don't publish corrected output until biases
are known. Pragmatic alternative: publish raw passthrough during
calibration. The pragmatic fix changes the contract on
`points_processed` (no longer guaranteed "deskewed + aligned"), so
left as-is and documented.

### Reproduce

```bash
# Host  (all fixes applied; behaviour is intentional)
cd ~/ugv_lidar_preprocessing_submission && git checkout main

# Container T1 — confirm roscore + build are current
pgrep -af roscore || (roscore &)
cd /ws && catkin build && source devel/setup.bash

# Container T2 — launch
source /opt/ros/noetic/setup.bash
source /ws/devel/setup.bash
rosparam set /use_sim_time true
roslaunch ugv_lidar_preprocessing lidar_preprocessing_nodelet.launch \
    sensor:=Livox namespace:=nbuggy

# Container T3 — start a bag
source /opt/ros/noetic/setup.bash
rosbag play --clock --rate 0.5 /bags/2025-12-30-18-03-34_0.bag

# Container T4 — observe the silent window
source /opt/ros/noetic/setup.bash
rostopic hz /nbuggy/livox_front/points_processed
# expect: "no new messages" for the first ~3 s of bag time, then ~10 Hz
```

T2's log shows the calibration progressing during the silent window
and `Calibration complete` at the moment output starts.

### Verify (no fix)

This is intentional behaviour. The "verification" is twofold:

1. The silence is bounded — output begins as soon as calibration completes.
2. It is consistent with the README contract on `points_processed`
   (always deskewed + aligned, never raw passthrough).

Practical consequence for grading: a grader who plays only a moving
bag (`_3+`) by itself will **never** trigger calibration completion
(the velocity gate prevents it) and will see no output forever.
Solution: chain `_0` first.

```bash
# Recommended chain for any verification involving moving motion:
rosbag play --clock --rate 0.5 \
    /bags/2025-12-30-18-03-34_0.bag \
    /bags/2025-12-30-18-05-14_5.bag
```

---

## Summary table — all 14 bugs

| #   | Layer / type           | Buggy commit | Fix commit | Detection method            | Visible symptom           | Rebuild? |
| --- | ---------------------- | ------------ | ---------- | --------------------------- | ------------------------- | -------- |
| #1  | CMake glob             | `43e3743`    | `29aa48d`  | Build error                 | `No SOURCES given`        | (cmake)  |
| #2  | C++ macro              | `29aa48d`    | `263f131`  | Compile error               | `does not name a type`    | yes      |
| #3  | YAML wrapper           | `263f131`    | `3465e28`  | Startup log WARN            | `Optional parameter ...`  | no       |
| #4  | Plugin order array     | `3465e28`    | `c96d252`  | Startup log INFO            | Wrong execution order     | yes      |
| #5  | IMU staleness `<`/`>`  | `c96d252`    | `14bdfe2`  | Calibration log WARN        | Self-contradicting message| yes      |
| #6  | TF lookup vs tree      | `14bdfe2`    | `7fa8d53`  | Runtime log WARN            | TF lookup failed          | yes      |
| #7  | Output frame_id        | `7fa8d53`    | `a0b0ec9`  | `rostopic echo`             | Wrong frame_id            | yes      |
| #8  | XML class type         | `a0b0ec9`    | `e85ce38`  | dynparam ERROR              | `no factory exists`       | yes (XML)|
| #9  | YAML invariant         | `e85ce38`    | `0f68ecf`  | Contract reading            | None on supplied bags     | no       |
| #10 | Quaternion conjugate   | `0f68ecf`    | `abd8e63`  | RViz visual + `tf_echo`     | Range-dependent vertical gap | yes  |
| #11 | Sort comparator        | `abd8e63`    | `59f8c8e`  | Dynparam A/B + RViz         | "Deskew on" worse than off | yes     |
| #12 | Off-by-one index       | `59f8c8e`    | `2e3bc77`  | Static review               | None on supplied bags     | yes      |
| #13 | Unreachable set_state  | `2e3bc77`    | `e45d40a`  | Static review               | None on supplied bags     | yes      |
| #14 | Calibration silence    | (none)       | (none)     | Documented; intentional     | Silent first ~3s          | n/a      |
