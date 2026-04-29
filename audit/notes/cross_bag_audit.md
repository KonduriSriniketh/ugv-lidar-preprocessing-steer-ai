# Cross-bag audit

Bags scanned: 16
Bag dir: `/home/sutd_ubuntu20/bags`

## 2025-12-30-18-03-34_0.bag

_(parsed in 1.0s)_

### Per-lidar inventory

| lidar | has_points | has_imu | points (n_pts min/med/max) | IMU rate Hz | IMU |a| (m/s²) | IMU |g| (rad/s) | gap_max ms |
|---|---|---|---|---|---|---|---|
| livox_front | ✓ | ✓ | 44736/45216/45696 | 202.7 | 1.02±0.34 | 0.0118/0.0289 | 7.7 |
| livox_left | ✓ | ✓ | 44544/45216/45888 | 202.8 | 1.01±0.12 | 0.0146/0.0311 | 8.5 |
| livox_rear_left | ✓ | — | 44640/45216/45792 | - | - | - | - |
| livox_rear_right | ✓ | ✓ | 44736/45216/45792 | 202.3 | 1.01±0.33 | 0.1546/0.2834 | 7.5 |
| livox_right | ✓ | ✓ | 44928/45216/45600 | 202.8 | 1.00±0.12 | 0.0136/0.0332 | 7.3 |

### Odometry (`/<ns>/odom`)

- topic: /nbuggy/odom
- frame_ids: ['nbuggy/map']
- speed: min=0.001, max=0.020, mean=0.009 m/s
- stationary (speed<0.05): 100.0% of 779 samples

### ⚠ Findings

  - livox_front: |accel| mean = 1.018 m/s² (expected ~9.81)
  - livox_left: |accel| mean = 1.010 m/s² (expected ~9.81)
  - livox_rear_left: HAS /points but MISSING /imu — preprocessing would refuse to start.
  - livox_rear_right: |accel| mean = 1.012 m/s² (expected ~9.81)
  - livox_right: |accel| mean = 1.003 m/s² (expected ~9.81)

## 2025-12-30-18-03-54_1.bag

_(parsed in 1.7s)_

### Per-lidar inventory

| lidar | has_points | has_imu | points (n_pts min/med/max) | IMU rate Hz | IMU |a| (m/s²) | IMU |g| (rad/s) | gap_max ms |
|---|---|---|---|---|---|---|---|
| livox_front | ✓ | ✓ | 44544/45216/45792 | 202.7 | 1.02±0.35 | 0.0119/0.0312 | 7.8 |
| livox_left | ✓ | ✓ | 44640/45216/45888 | 202.4 | 1.01±0.12 | 0.0145/0.0310 | 7.4 |
| livox_rear_left | ✓ | — | 44736/45216/45696 | - | - | - | - |
| livox_rear_right | ✓ | ✓ | 44736/45216/45600 | 202.5 | 1.01±0.34 | 0.1602/0.2884 | 7.4 |
| livox_right | ✓ | ✓ | 44736/45216/45600 | 202.2 | 1.00±0.12 | 0.0136/0.0315 | 7.1 |

### Odometry (`/<ns>/odom`)

- topic: /nbuggy/car_interface/odom
- frame_ids: ['car_interface']
- speed: min=0.000, max=0.000, mean=0.000 m/s
- stationary (speed<0.05): 100.0% of 200 samples

### ⚠ Findings

  - livox_front: |accel| mean = 1.019 m/s² (expected ~9.81)
  - livox_left: |accel| mean = 1.009 m/s² (expected ~9.81)
  - livox_rear_left: HAS /points but MISSING /imu — preprocessing would refuse to start.
  - livox_rear_right: |accel| mean = 1.015 m/s² (expected ~9.81)
  - livox_right: |accel| mean = 1.003 m/s² (expected ~9.81)

## 2025-12-30-18-04-14_2.bag

_(parsed in 1.5s)_

### Per-lidar inventory

| lidar | has_points | has_imu | points (n_pts min/med/max) | IMU rate Hz | IMU |a| (m/s²) | IMU |g| (rad/s) | gap_max ms |
|---|---|---|---|---|---|---|---|
| livox_front | ✓ | ✓ | 44448/45216/45792 | 202.9 | 1.02±0.35 | 0.0121/0.0278 | 7.8 |
| livox_left | ✓ | ✓ | 44448/45216/45888 | 202.9 | 1.01±0.13 | 0.0145/0.0305 | 8.7 |
| livox_rear_left | ✓ | — | 44544/45216/45792 | - | - | - | - |
| livox_rear_right | ✓ | ✓ | 44736/45216/45792 | 202.3 | 1.02±0.36 | 0.1644/0.2945 | 8.9 |
| livox_right | ✓ | ✓ | 44640/45216/45888 | 202.6 | 1.00±0.13 | 0.0136/0.0361 | 7.6 |

### Odometry (`/<ns>/odom`)

- topic: /nbuggy/odom
- frame_ids: ['nbuggy/map']
- speed: min=0.001, max=0.021, mean=0.008 m/s
- stationary (speed<0.05): 100.0% of 800 samples

### ⚠ Findings

  - livox_front: |accel| mean = 1.018 m/s² (expected ~9.81)
  - livox_left: |accel| mean = 1.009 m/s² (expected ~9.81)
  - livox_rear_left: HAS /points but MISSING /imu — preprocessing would refuse to start.
  - livox_rear_right: |accel| mean = 1.015 m/s² (expected ~9.81)
  - livox_right: |accel| mean = 1.003 m/s² (expected ~9.81)

## 2025-12-30-18-04-34_3.bag

_(parsed in 0.9s)_

### Per-lidar inventory

| lidar | has_points | has_imu | points (n_pts min/med/max) | IMU rate Hz | IMU |a| (m/s²) | IMU |g| (rad/s) | gap_max ms |
|---|---|---|---|---|---|---|---|
| livox_front | ✓ | ✓ | 44544/45216/45696 | 125.4 | 1.02±0.34 | 0.0122/0.0304 | 4789.8 |
| livox_left | ✓ | ✓ | 44736/45216/45792 | 125.7 | 1.01±0.12 | 0.0141/0.0291 | 4786.8 |
| livox_rear_left | ✓ | — | 44736/45216/45696 | - | - | - | - |
| livox_rear_right | ✓ | ✓ | 44736/45216/45792 | 125.4 | 1.02±0.38 | 0.1706/0.3183 | 4785.1 |
| livox_right | ✓ | ✓ | 44640/45216/45696 | 124.7 | 1.00±0.14 | 0.0139/0.0352 | 4788.5 |

### Odometry (`/<ns>/odom`)

- topic: /nbuggy/odom
- frame_ids: ['nbuggy/map']
- speed: min=0.001, max=0.020, mean=0.009 m/s
- stationary (speed<0.05): 100.0% of 494 samples

### ⚠ Findings

  - livox_front: IMU gap up to 4789.8 ms (rate=125.4 Hz)
  - livox_front: |accel| mean = 1.021 m/s² (expected ~9.81)
  - livox_front: 38 IMU gaps > 3× median (out of 2508)
  - livox_left: IMU gap up to 4786.8 ms (rate=125.7 Hz)
  - livox_left: |accel| mean = 1.008 m/s² (expected ~9.81)
  - livox_left: 35 IMU gaps > 3× median (out of 2514)
  - livox_rear_left: HAS /points but MISSING /imu — preprocessing would refuse to start.
  - livox_rear_right: IMU gap up to 4785.1 ms (rate=125.4 Hz)
  - livox_rear_right: |accel| mean = 1.017 m/s² (expected ~9.81)
  - livox_rear_right: 36 IMU gaps > 3× median (out of 2509)
  - livox_right: IMU gap up to 4788.5 ms (rate=124.7 Hz)
  - livox_right: |accel| mean = 1.002 m/s² (expected ~9.81)
  - livox_right: 37 IMU gaps > 3× median (out of 2494)

## 2025-12-30-18-04-54_4.bag

_(parsed in 1.6s)_

### Per-lidar inventory

| lidar | has_points | has_imu | points (n_pts min/med/max) | IMU rate Hz | IMU |a| (m/s²) | IMU |g| (rad/s) | gap_max ms |
|---|---|---|---|---|---|---|---|
| livox_front | ✓ | ✓ | 44448/45216/45888 | 203.8 | 1.03±0.38 | 0.0127/0.0292 | 7.7 |
| livox_left | ✓ | ✓ | 44640/45216/45888 | 202.8 | 1.01±0.13 | 0.0150/0.0327 | 7.2 |
| livox_rear_left | ✓ | — | 44640/45216/45792 | - | - | - | - |
| livox_rear_right | ✓ | ✓ | 44544/45216/45792 | 202.1 | 1.02±0.38 | 0.1769/0.3151 | 6.7 |
| livox_right | ✓ | ✓ | 44832/45216/46080 | 202.7 | 1.00±0.15 | 0.0144/0.0364 | 7.5 |

### Odometry (`/<ns>/odom`)

- topic: /nbuggy/odom
- frame_ids: ['nbuggy/map']
- speed: min=0.001, max=0.021, mean=0.009 m/s
- stationary (speed<0.05): 100.0% of 800 samples

### ⚠ Findings

  - livox_front: |accel| mean = 1.025 m/s² (expected ~9.81)
  - livox_left: |accel| mean = 1.010 m/s² (expected ~9.81)
  - livox_rear_left: HAS /points but MISSING /imu — preprocessing would refuse to start.
  - livox_rear_right: |accel| mean = 1.018 m/s² (expected ~9.81)
  - livox_right: |accel| mean = 1.003 m/s² (expected ~9.81)

## 2025-12-30-18-05-14_5.bag

_(parsed in 1.6s)_

### Per-lidar inventory

| lidar | has_points | has_imu | points (n_pts min/med/max) | IMU rate Hz | IMU |a| (m/s²) | IMU |g| (rad/s) | gap_max ms |
|---|---|---|---|---|---|---|---|
| livox_front | ✓ | ✓ | 44640/45216/45792 | 202.9 | 1.02±0.38 | 0.0126/0.0299 | 7.5 |
| livox_left | ✓ | ✓ | 44352/45216/46176 | 202.9 | 1.01±0.13 | 0.0152/0.0327 | 6.7 |
| livox_rear_left | ✓ | — | 44736/45216/45792 | - | - | - | - |
| livox_rear_right | ✓ | ✓ | 44448/45216/45792 | 202.6 | 1.02±0.37 | 0.1758/0.3188 | 7.3 |
| livox_right | ✓ | ✓ | 44640/45216/45792 | 202.1 | 1.00±0.14 | 0.0144/0.0361 | 7.8 |

### Odometry (`/<ns>/odom`)

- topic: /nbuggy/odom
- frame_ids: ['nbuggy/map']
- speed: min=0.001, max=0.021, mean=0.010 m/s
- stationary (speed<0.05): 100.0% of 800 samples

### ⚠ Findings

  - livox_front: |accel| mean = 1.024 m/s² (expected ~9.81)
  - livox_left: |accel| mean = 1.011 m/s² (expected ~9.81)
  - livox_rear_left: HAS /points but MISSING /imu — preprocessing would refuse to start.
  - livox_rear_right: |accel| mean = 1.017 m/s² (expected ~9.81)
  - livox_right: |accel| mean = 1.003 m/s² (expected ~9.81)

## 2025-12-30-18-05-34_6.bag

_(parsed in 1.6s)_

### Per-lidar inventory

| lidar | has_points | has_imu | points (n_pts min/med/max) | IMU rate Hz | IMU |a| (m/s²) | IMU |g| (rad/s) | gap_max ms |
|---|---|---|---|---|---|---|---|
| livox_front | ✓ | ✓ | 44352/45216/45888 | 202.3 | 1.02±0.35 | 0.0137/0.0861 | 8.8 |
| livox_left | ✓ | ✓ | 44160/45216/46176 | 203.0 | 1.01±0.14 | 0.0160/0.0899 | 8.1 |
| livox_rear_left | ✓ | — | 44448/45216/45888 | - | - | - | - |
| livox_rear_right | ✓ | ✓ | 44544/45216/46080 | 202.4 | 1.02±0.40 | 0.1701/0.3125 | 8.0 |
| livox_right | ✓ | ✓ | 44448/45216/46080 | 202.4 | 1.00±0.14 | 0.0152/0.0854 | 7.4 |

### Odometry (`/<ns>/odom`)

- topic: /nbuggy/odom
- frame_ids: ['nbuggy/map']
- speed: min=0.000, max=0.520, mean=0.015 m/s
- stationary (speed<0.05): 97.8% of 800 samples

### ⚠ Findings

  - livox_front: |accel| mean = 1.023 m/s² (expected ~9.81)
  - livox_left: |accel| mean = 1.012 m/s² (expected ~9.81)
  - livox_rear_left: HAS /points but MISSING /imu — preprocessing would refuse to start.
  - livox_rear_right: |accel| mean = 1.018 m/s² (expected ~9.81)
  - livox_right: |accel| mean = 1.003 m/s² (expected ~9.81)

## 2025-12-30-18-05-54_7.bag

_(parsed in 2.1s)_

### Per-lidar inventory

| lidar | has_points | has_imu | points (n_pts min/med/max) | IMU rate Hz | IMU |a| (m/s²) | IMU |g| (rad/s) | gap_max ms |
|---|---|---|---|---|---|---|---|
| livox_front | ✓ | ✓ | 43680/45216/46752 | 202.9 | 1.16±0.35 | 0.1227/0.4242 | 9.2 |
| livox_left | ✓ | ✓ | 43584/45216/46944 | 203.1 | 1.17±0.33 | 0.1279/0.3973 | 8.9 |
| livox_rear_left | ✓ | — | 43872/45216/46464 | - | - | - | - |
| livox_rear_right | ✓ | ✓ | 43968/45216/46848 | 202.6 | 1.19±0.39 | 0.1451/0.4896 | 8.9 |
| livox_right | ✓ | ✓ | 43392/45216/46944 | 202.4 | 1.16±0.34 | 0.1289/0.4258 | 9.0 |

### Odometry (`/<ns>/odom`)

- topic: /nbuggy/odom
- frame_ids: ['nbuggy/map']
- speed: min=0.554, max=11.144, mean=7.759 m/s
- stationary (speed<0.05): 0.0% of 800 samples

### ⚠ Findings

  - livox_front: |accel| mean = 1.158 m/s² (expected ~9.81)
  - livox_left: |accel| mean = 1.174 m/s² (expected ~9.81)
  - livox_rear_left: HAS /points but MISSING /imu — preprocessing would refuse to start.
  - livox_rear_right: |accel| mean = 1.189 m/s² (expected ~9.81)
  - livox_right: |accel| mean = 1.164 m/s² (expected ~9.81)
  - odom: never below 0.05 m/s (min=0.554); calibration would never complete in this bag
  - odom: <5% stationary (0.0%); calibration window unlikely to fit

## 2025-12-30-18-06-14_8.bag

_(parsed in 4.8s)_

### Per-lidar inventory

| lidar | has_points | has_imu | points (n_pts min/med/max) | IMU rate Hz | IMU |a| (m/s²) | IMU |g| (rad/s) | gap_max ms |
|---|---|---|---|---|---|---|---|
| livox_front | ✓ | ✓ | 44448/45216/45696 | 203.2 | 1.18±0.33 | 0.1576/0.5438 | 8.7 |
| livox_left | ✓ | ✓ | 44352/45216/46176 | 202.9 | 1.19±0.36 | 0.1634/0.6121 | 9.1 |
| livox_rear_left | ✓ | — | 44544/45216/45984 | - | - | - | - |
| livox_rear_right | ✓ | ✓ | 44736/45216/45600 | 202.2 | 1.23±0.42 | 0.1800/0.7318 | 7.3 |
| livox_right | ✓ | ✓ | 44640/45216/45792 | 202.1 | 1.19±0.36 | 0.1646/0.6819 | 8.5 |

### Odometry (`/<ns>/odom`)

- topic: /nbuggy/odom
- frame_ids: ['nbuggy/map']
- speed: min=4.812, max=10.716, mean=8.142 m/s
- stationary (speed<0.05): 0.0% of 800 samples

### ⚠ Findings

  - livox_front: |accel| mean = 1.179 m/s² (expected ~9.81)
  - livox_left: |accel| mean = 1.190 m/s² (expected ~9.81)
  - livox_rear_left: HAS /points but MISSING /imu — preprocessing would refuse to start.
  - livox_rear_right: |accel| mean = 1.231 m/s² (expected ~9.81)
  - livox_right: |accel| mean = 1.187 m/s² (expected ~9.81)
  - odom: never below 0.05 m/s (min=4.812); calibration would never complete in this bag
  - odom: <5% stationary (0.0%); calibration window unlikely to fit

## 2025-12-30-18-06-34_9.bag

_(parsed in 1.1s)_

### Per-lidar inventory

| lidar | has_points | has_imu | points (n_pts min/med/max) | IMU rate Hz | IMU |a| (m/s²) | IMU |g| (rad/s) | gap_max ms |
|---|---|---|---|---|---|---|---|
| livox_front | ✓ | ✓ | 43392/45216/46944 | 203.0 | 1.22±0.37 | 0.2489/0.6413 | 8.8 |
| livox_left | ✓ | ✓ | 43968/45216/46464 | 202.7 | 1.23±0.36 | 0.2549/0.6656 | 9.3 |
| livox_rear_left | ✓ | — | 44256/45216/46080 | - | - | - | - |
| livox_rear_right | ✓ | ✓ | 44064/45216/46368 | 202.2 | 1.26±0.44 | 0.2637/0.6761 | 8.5 |
| livox_right | ✓ | ✓ | 43680/45216/47040 | 202.5 | 1.26±0.39 | 0.2553/0.6838 | 8.4 |

### Odometry (`/<ns>/odom`)

- topic: /nbuggy/odom
- frame_ids: ['nbuggy/map']
- speed: min=5.974, max=10.541, mean=7.900 m/s
- stationary (speed<0.05): 0.0% of 800 samples

### ⚠ Findings

  - livox_front: |accel| mean = 1.222 m/s² (expected ~9.81)
  - livox_left: |accel| mean = 1.230 m/s² (expected ~9.81)
  - livox_rear_left: HAS /points but MISSING /imu — preprocessing would refuse to start.
  - livox_rear_right: |accel| mean = 1.258 m/s² (expected ~9.81)
  - livox_right: |accel| mean = 1.259 m/s² (expected ~9.81)
  - odom: never below 0.05 m/s (min=5.974); calibration would never complete in this bag
  - odom: <5% stationary (0.0%); calibration window unlikely to fit

## 2025-12-30-18-06-54_10.bag

_(parsed in 1.0s)_

### Per-lidar inventory

| lidar | has_points | has_imu | points (n_pts min/med/max) | IMU rate Hz | IMU |a| (m/s²) | IMU |g| (rad/s) | gap_max ms |
|---|---|---|---|---|---|---|---|
| livox_front | ✓ | ✓ | 43488/45216/46752 | 203.6 | 1.20±0.35 | 0.2217/0.6330 | 7.9 |
| livox_left | ✓ | ✓ | 44640/45216/46080 | 202.7 | 1.20±0.39 | 0.2298/0.6443 | 8.2 |
| livox_rear_left | ✓ | — | 44544/45216/45792 | - | - | - | - |
| livox_rear_right | ✓ | ✓ | 44544/45216/45888 | 202.4 | 1.34±0.45 | 0.2444/0.7321 | 9.4 |
| livox_right | ✓ | ✓ | 44256/45216/46272 | 203.1 | 1.22±0.37 | 0.2285/0.6656 | 7.7 |

### Odometry (`/<ns>/odom`)

- topic: /nbuggy/odom
- frame_ids: ['nbuggy/map']
- speed: min=4.596, max=8.334, mean=6.808 m/s
- stationary (speed<0.05): 0.0% of 800 samples

### ⚠ Findings

  - livox_front: |accel| mean = 1.197 m/s² (expected ~9.81)
  - livox_left: |accel| mean = 1.197 m/s² (expected ~9.81)
  - livox_rear_left: HAS /points but MISSING /imu — preprocessing would refuse to start.
  - livox_rear_right: |accel| mean = 1.335 m/s² (expected ~9.81)
  - livox_right: |accel| mean = 1.217 m/s² (expected ~9.81)
  - odom: never below 0.05 m/s (min=4.596); calibration would never complete in this bag
  - odom: <5% stationary (0.0%); calibration window unlikely to fit

## 2025-12-30-18-07-14_11.bag

_(parsed in 1.0s)_

### Per-lidar inventory

| lidar | has_points | has_imu | points (n_pts min/med/max) | IMU rate Hz | IMU |a| (m/s²) | IMU |g| (rad/s) | gap_max ms |
|---|---|---|---|---|---|---|---|
| livox_front | ✓ | ✓ | 43968/45216/46272 | 203.5 | 1.12±0.28 | 0.2722/0.5514 | 8.8 |
| livox_left | ✓ | ✓ | 44448/45216/46080 | 203.0 | 1.12±0.27 | 0.2750/0.5418 | 8.2 |
| livox_rear_left | ✓ | — | 44544/45216/46272 | - | - | - | - |
| livox_rear_right | ✓ | ✓ | 44352/45216/46080 | 202.4 | 1.19±0.36 | 0.2838/0.5574 | 8.1 |
| livox_right | ✓ | ✓ | 44256/45216/46176 | 202.4 | 1.12±0.28 | 0.2746/0.5492 | 10.0 |

### Odometry (`/<ns>/odom`)

- topic: /nbuggy/odom
- frame_ids: ['nbuggy/map']
- speed: min=3.244, max=8.713, mean=5.955 m/s
- stationary (speed<0.05): 0.0% of 800 samples

### ⚠ Findings

  - livox_front: |accel| mean = 1.125 m/s² (expected ~9.81)
  - livox_left: |accel| mean = 1.125 m/s² (expected ~9.81)
  - livox_rear_left: HAS /points but MISSING /imu — preprocessing would refuse to start.
  - livox_rear_right: |accel| mean = 1.193 m/s² (expected ~9.81)
  - livox_right: |accel| mean = 1.124 m/s² (expected ~9.81)
  - odom: never below 0.05 m/s (min=3.244); calibration would never complete in this bag
  - odom: <5% stationary (0.0%); calibration window unlikely to fit

## 2025-12-30-18-07-34_12.bag

_(parsed in 0.7s)_

### Per-lidar inventory

| lidar | has_points | has_imu | points (n_pts min/med/max) | IMU rate Hz | IMU |a| (m/s²) | IMU |g| (rad/s) | gap_max ms |
|---|---|---|---|---|---|---|---|
| livox_front | ✓ | ✓ | 44448/45216/46272 | 136.4 | 1.24±0.39 | 0.2500/0.5171 | 2447.7 |
| livox_left | ✓ | ✓ | 44640/45216/45984 | 136.4 | 1.27±0.39 | 0.2589/0.5127 | 2445.2 |
| livox_rear_left | ✓ | — | 44544/45216/45792 | - | - | - | - |
| livox_rear_right | ✓ | ✓ | 44352/45216/46080 | 136.5 | 1.25±0.46 | 0.2711/0.6021 | 2445.7 |
| livox_right | ✓ | ✓ | 43968/45216/46560 | 135.9 | 1.24±0.43 | 0.2608/0.5502 | 1719.9 |

### Odometry (`/<ns>/odom`)

- topic: /nbuggy/odom
- frame_ids: ['nbuggy/map']
- speed: min=6.748, max=11.749, mean=8.299 m/s
- stationary (speed<0.05): 0.0% of 541 samples

### ⚠ Findings

  - livox_front: IMU gap up to 2447.7 ms (rate=136.4 Hz)
  - livox_front: |accel| mean = 1.240 m/s² (expected ~9.81)
  - livox_left: IMU gap up to 2445.2 ms (rate=136.4 Hz)
  - livox_left: |accel| mean = 1.272 m/s² (expected ~9.81)
  - livox_rear_left: HAS /points but MISSING /imu — preprocessing would refuse to start.
  - livox_rear_right: IMU gap up to 2445.7 ms (rate=136.5 Hz)
  - livox_rear_right: |accel| mean = 1.253 m/s² (expected ~9.81)
  - livox_right: IMU gap up to 1719.9 ms (rate=135.9 Hz)
  - livox_right: |accel| mean = 1.241 m/s² (expected ~9.81)
  - odom: never below 0.05 m/s (min=6.748); calibration would never complete in this bag
  - odom: <5% stationary (0.0%); calibration window unlikely to fit

## 2025-12-30-18-07-54_13.bag

_(parsed in 1.0s)_

### Per-lidar inventory

| lidar | has_points | has_imu | points (n_pts min/med/max) | IMU rate Hz | IMU |a| (m/s²) | IMU |g| (rad/s) | gap_max ms |
|---|---|---|---|---|---|---|---|
| livox_front | ✓ | ✓ | 44448/45216/45792 | 202.9 | 1.21±0.37 | 0.2101/0.7689 | 7.4 |
| livox_left | ✓ | ✓ | 44736/45216/45696 | 203.2 | 1.26±0.38 | 0.2182/0.8721 | 8.8 |
| livox_rear_left | ✓ | — | 44640/45216/45792 | - | - | - | - |
| livox_rear_right | ✓ | ✓ | 44736/45216/45792 | 202.0 | 1.29±0.46 | 0.2323/0.9080 | 8.2 |
| livox_right | ✓ | ✓ | 44736/45216/45792 | 202.2 | 1.27±0.41 | 0.2193/0.8823 | 8.1 |

### Odometry (`/<ns>/odom`)

- topic: /nbuggy/car_interface/odom
- frame_ids: ['car_interface']
- speed: min=4.944, max=10.611, mean=9.125 m/s
- stationary (speed<0.05): 0.0% of 200 samples

### ⚠ Findings

  - livox_front: |accel| mean = 1.213 m/s² (expected ~9.81)
  - livox_left: |accel| mean = 1.259 m/s² (expected ~9.81)
  - livox_rear_left: HAS /points but MISSING /imu — preprocessing would refuse to start.
  - livox_rear_right: |accel| mean = 1.287 m/s² (expected ~9.81)
  - livox_right: |accel| mean = 1.270 m/s² (expected ~9.81)
  - odom: never below 0.05 m/s (min=4.944); calibration would never complete in this bag
  - odom: <5% stationary (0.0%); calibration window unlikely to fit

## 2025-12-30-18-08-14_14.bag

_(parsed in 1.0s)_

### Per-lidar inventory

| lidar | has_points | has_imu | points (n_pts min/med/max) | IMU rate Hz | IMU |a| (m/s²) | IMU |g| (rad/s) | gap_max ms |
|---|---|---|---|---|---|---|---|
| livox_front | ✓ | ✓ | 44640/45216/45888 | 202.4 | 1.01±0.19 | 0.0267/0.2957 | 8.2 |
| livox_left | ✓ | ✓ | 44832/45216/45696 | 202.6 | 1.01±0.10 | 0.0290/0.2965 | 8.0 |
| livox_rear_left | ✓ | — | 44736/45216/45792 | - | - | - | - |
| livox_rear_right | ✓ | ✓ | 44448/45216/45984 | 202.1 | 1.01±0.26 | 0.1013/0.3154 | 8.5 |
| livox_right | ✓ | ✓ | 44544/45216/45792 | 202.2 | 1.01±0.10 | 0.0283/0.2834 | 8.6 |

### Odometry (`/<ns>/odom`)

- topic: /nbuggy/odom
- frame_ids: ['nbuggy/map']
- speed: min=0.000, max=4.809, mean=0.795 m/s
- stationary (speed<0.05): 66.6% of 800 samples

### ⚠ Findings

  - livox_front: |accel| mean = 1.013 m/s² (expected ~9.81)
  - livox_left: |accel| mean = 1.014 m/s² (expected ~9.81)
  - livox_rear_left: HAS /points but MISSING /imu — preprocessing would refuse to start.
  - livox_rear_right: |accel| mean = 1.014 m/s² (expected ~9.81)
  - livox_right: |accel| mean = 1.011 m/s² (expected ~9.81)

## 2025-12-30-18-08-34_15.bag

_(parsed in 0.4s)_

### Per-lidar inventory

| lidar | has_points | has_imu | points (n_pts min/med/max) | IMU rate Hz | IMU |a| (m/s²) | IMU |g| (rad/s) | gap_max ms |
|---|---|---|---|---|---|---|---|
| livox_front | ✓ | ✓ | 44544/45216/45888 | 202.5 | 1.00±0.20 | 0.0102/0.0235 | 7.4 |
| livox_left | ✓ | ✓ | 44736/45216/45984 | 202.8 | 1.01±0.09 | 0.0122/0.0246 | 8.5 |
| livox_rear_left | ✓ | — | 44736/45216/45696 | - | - | - | - |
| livox_rear_right | ✓ | ✓ | 44544/45216/45984 | 202.5 | 1.01±0.28 | 0.1073/0.2061 | 9.1 |
| livox_right | ✓ | ✓ | 44640/45216/45888 | 203.0 | 1.00±0.08 | 0.0107/0.0299 | 8.5 |

### Odometry (`/<ns>/odom`)

- topic: /nbuggy/odom
- frame_ids: ['nbuggy/map']
- speed: min=0.000, max=0.016, mean=0.007 m/s
- stationary (speed<0.05): 100.0% of 327 samples

### ⚠ Findings

  - livox_front: |accel| mean = 1.004 m/s² (expected ~9.81)
  - livox_left: |accel| mean = 1.006 m/s² (expected ~9.81)
  - livox_rear_left: HAS /points but MISSING /imu — preprocessing would refuse to start.
  - livox_rear_right: |accel| mean = 1.007 m/s² (expected ~9.81)
  - livox_right: |accel| mean = 1.001 m/s² (expected ~9.81)

