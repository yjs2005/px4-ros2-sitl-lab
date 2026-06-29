# Trajectory Tracking

This document records the trajectory-tracking workflow for the PX4 ROS 2 SITL lab. The scope is simulation-only and not for real aircraft deployment.

## Coordinate Convention

PX4 local position uses NED coordinates:

- `x`: North
- `y`: East
- `z`: Down

Negative `z` means upward. A target of `z=-2.0` means about 2 meters above the local origin.

## Current Verified Experiments

### Hover

The first successful hover experiment tracks:

```text
PX4 NED: x = 0.0, y = 0.0, z = -2.0
```

Input CSV:

```text
logs/offboard_hover_first_success.csv
```

Analysis:

```bash
python analysis/analyze_offboard_hover.py
```

Key steady-state result:

- z RMSE: `0.0864 m`
- XY RMSE: `0.0313 m`
- final position error: `0.0327 m`

### Figure-Eight

The first successful figure-eight experiment uses:

```text
x(t) = A * sin(omega * t)
y(t) = B * sin(2 * omega * t)
z(t) = -2.0
```

Input CSV:

```text
logs/figure8_first_success.csv
```

Analysis:

```bash
python analysis/analyze_figure8.py
```

Tracking-stage filter:

```text
stage == "figure8"
```

Key result:

- tracking duration: `40.000 s`
- XY RMSE: `0.2003 m`
- z RMSE: `0.1944 m`
- 3D position RMSE: `0.2791 m`

## Unified Multi-Trajectory Node

The new `offboard_trajectory` node is a parameterized trajectory runner for later SITL experiments.

Supported `trajectory` parameter values:

- `hover`
- `line`
- `square`
- `circle`
- `figure8`
- `z_step`

Run example:

```bash
ros2 run px4_offboard_lab offboard_trajectory --ros-args -p trajectory:=circle -p controller_mode:=baseline
```

Or through the helper:

```bash
bash scripts/run_trajectory.sh circle baseline
bash scripts/run_trajectory.sh circle feedforward
bash scripts/run_trajectory.sh square smooth
```

The node uses this common Offboard sequence:

```text
setpoint warm-up -> arm -> OFFBOARD -> pretrack hover -> tracking -> land -> finish
```

All modes publish setpoints at 20 Hz by default and log CSV rows with:

- vehicle state
- target setpoint
- target velocity setpoint
- stage
- trajectory type
- controller mode
- XY position error
- 3D position error

Generated logs are named:

```text
offboard_trajectory_<trajectory>_<controller_mode>_<timestamp>.csv
```

When launched through `scripts/run_trajectory.sh`, CSV logs are saved under the project `logs/` directory automatically. Existing CSV files are not overwritten or deleted.

The node prints one of these exit messages:

- `CSV saved to: <absolute_path>`
- `CSV saving disabled`
- `No samples recorded`
- a concrete CSV error message if saving failed

## Controller Modes

The unified node supports:

- `baseline`: position-only setpoint; velocity and acceleration are NaN.
- `feedforward`: position plus analytic velocity feedforward; acceleration remains NaN.
- `smooth`: smooth time scaling / corner slowdown plus velocity feedforward.

PX4 internal controllers are not modified. PX4 still performs the inner position, velocity, attitude, and rate control. The experiment changes only the ROS 2 Offboard setpoint generation strategy.

See `docs/control_improvement.md` for the planned baseline vs improved comparison experiments.

## Trajectory Definitions

### `hover`

```text
x = 0
y = 0
z = altitude
```

### `line`

Smooth x-axis sweep:

```text
x = amplitude_x * sin(omega * t)
y = 0
z = altitude
```

### `square`

Linear interpolation around four corners with side length `square_size`.

### `circle`

```text
x = radius * cos(omega * t)
y = radius * sin(omega * t)
z = altitude
```

### `figure8`

```text
x = amplitude_x * sin(omega * t)
y = amplitude_y * sin(2 * omega * t)
z = altitude
```

### `z_step`

```text
x = 0
y = 0
z switches smoothly between -1.5 and -2.5
```

## Trajectory Suite Analysis

Future line/square/circle/z_step runs can be summarized together:

```bash
python analysis/analyze_trajectory_suite.py
```

The suite analyzer scans:

- `logs/trajectory_*.csv`
- `logs/offboard_trajectory_*.csv`
- `logs/figure8_first_success.csv`

Outputs:

- `results/trajectory_suite_metrics.csv`
- `results/trajectory_suite_metrics.json`
- `results/trajectory_suite_metrics.md`
- `results/figures/trajectory_suite_metrics.png`

The existing hover and figure-eight analysis files are not overwritten.

## Control Mode Comparison

After paired baseline/improved runs are available:

```bash
python analysis/compare_control_modes.py
```

The script scans only new logs that explicitly include `controller_mode`, such as:

```text
offboard_trajectory_circle_baseline_<timestamp>.csv
offboard_trajectory_circle_feedforward_<timestamp>.csv
offboard_trajectory_square_smooth_<timestamp>.csv
```

It does not treat the existing `figure8_first_success.csv` as a feedforward result.

## Safety Constraints

- SITL only.
- Do not connect these nodes to a real aircraft.
- Keep setpoint rate at or above 10 Hz; this package defaults to 20 Hz.
- Keep trajectories small until tracking behavior is measured.
- QGroundControl should be open, or SITL preflight checks should be otherwise resolved, before attempting Offboard takeoff.
