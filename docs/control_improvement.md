# Control Improvement Plan

This project does not rewrite PX4 internal flight control. PX4 still runs its built-in position, velocity, attitude, and rate controllers.

The experiment changes only the ROS 2 Offboard setpoint generation layer.

## Control Modes

### `baseline`

Baseline is position-only setpoint tracking:

- publish `TrajectorySetpoint.position`
- set `TrajectorySetpoint.velocity` to NaN
- set acceleration to NaN

This is the reference mode for comparing dynamic trajectory tracking.

### `feedforward`

Feedforward publishes position plus analytic target velocity:

- publish `TrajectorySetpoint.position`
- publish `TrajectorySetpoint.velocity`
- keep acceleration as NaN for now

For circle:

```text
x = R * cos(wt)
y = R * sin(wt)
vx = -R * w * sin(wt)
vy =  R * w * cos(wt)
```

For figure-eight:

```text
x = A * sin(wt)
y = B * sin(2wt)
vx = A * w * cos(wt)
vy = 2 * B * w * cos(2wt)
```

Position-only tracking tells PX4 where the target is. Velocity feedforward also tells PX4 the expected direction and speed of motion, which may reduce phase lag on dynamic trajectories.

### `planar_ff`

Planar feedforward is a z-safe variant intended for cases where XY tracking improves with feedforward but vertical tracking becomes worse.

It still does not rewrite or bypass PX4 internal control. The only change is in the ROS 2 Offboard setpoint generator:

- publish `TrajectorySetpoint.position`
- set `vx` and `vy` to `ff_gain * analytic_velocity_xy`
- set `vz` to `0.0`
- keep acceleration as NaN
- keep the target altitude fixed by the NED altitude parameter, normally `z=-2.0`

The `ff_gain` parameter controls feedforward strength. Planned figure-eight tests:

```bash
bash scripts/run_trajectory.sh figure8 planar_ff 0.5
bash scripts/run_trajectory.sh figure8 planar_ff 0.8
bash scripts/run_trajectory.sh figure8 planar_ff 1.0
```

This mode was added because existing figure-eight comparison data showed that full velocity feedforward can reduce XY error while increasing z RMSE, 3D RMSE, and max 3D error. `planar_ff` limits velocity feedforward to the horizontal plane so the vertical channel is not driven by z-velocity feedforward.

### `smooth`

Smooth mode is intended for trajectories with discontinuities or sharp changes:

- `line`
- `square`
- `z_step`

It uses smoothstep time scaling and velocity feedforward. For square trajectories, the current implementation slows down at corners instead of commanding an abrupt velocity direction change. For `z_step`, smooth mode turns a hard altitude step into a smooth transition.

PX4 local position uses NED coordinates. Negative `z` means upward.

## Completed And Planned Comparison Experiments

Committed paired SITL CSV logs already exist for:

- `circle baseline` vs `circle feedforward`
- `figure8 baseline` vs `figure8 feedforward`
- `square baseline` vs `square smooth`

Additional planned paired SITL experiments are:

- `figure8 baseline` vs `figure8 planar_ff` with `ff_gain=0.5`, `0.8`, and `1.0`
- `line baseline` vs `line smooth`
- `z_step baseline` vs `z_step smooth`

Example commands:

```bash
bash scripts/run_trajectory.sh circle baseline
bash scripts/run_trajectory.sh circle feedforward
bash scripts/run_trajectory.sh figure8 planar_ff 0.8
bash scripts/run_trajectory.sh square smooth
```

Each command saves a CSV automatically to:

```text
logs/offboard_trajectory_<trajectory>_<controller_mode>_<YYYYMMDD_HHMMSS>.csv
```

For `planar_ff`, the filename also includes the gain when possible:

```text
logs/offboard_trajectory_<trajectory>_planar_ff_g0p8_<YYYYMMDD_HHMMSS>.csv
```

The run script only starts the ROS 2 trajectory node. It does not start PX4, Gazebo, or Agent; it does not kill processes; it does not delete logs; and it does not modify PX4 parameters.

## Validity Checks

A CSV should be treated as a failed run and excluded from final comparisons if:

- `arming_state` does not reach or remain near `2` during the expected flight window.
- `position_ned.z` stays far from the target altitude, for example never approaching `-2.0`.
- the log never reaches the intended tracking stage.

Do not delete failed logs. Move them to `logs/bad_runs/` so they remain available for debugging but are not mixed into final metrics.

## Analysis

After paired CSV logs are available, run:

```bash
python3 analysis/compare_control_modes.py
```

Outputs:

- `results/control_comparison_metrics.csv`
- `results/control_comparison_metrics.json`
- `results/control_comparison_metrics.md`
- `results/figures/control_comparison_xy_rmse.png`
- `results/figures/control_comparison_3d_rmse.png`
- `results/figures/control_comparison_percent_improvement.png`

If paired baseline/improved logs are not available, the script exits normally and reports:

```text
No paired baseline/improved logs found yet. Run paired SITL experiments first.
```

Do not claim error reduction in README Results until paired SITL runs have been completed and analyzed.
