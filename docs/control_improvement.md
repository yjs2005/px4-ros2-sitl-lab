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

### `smooth`

Smooth mode is intended for trajectories with discontinuities or sharp changes:

- `line`
- `square`
- `z_step`

It uses smoothstep time scaling and velocity feedforward. For square trajectories, the current implementation slows down at corners instead of commanding an abrupt velocity direction change. For `z_step`, smooth mode turns a hard altitude step into a smooth transition.

PX4 local position uses NED coordinates. Negative `z` means upward.

## Planned Comparison Experiments

The planned paired SITL experiments are:

- `circle baseline` vs `circle feedforward`
- `figure8 baseline` vs `figure8 feedforward`
- `square baseline` vs `square smooth`
- `line baseline` vs `line smooth`
- `z_step baseline` vs `z_step smooth`

Example commands:

```bash
bash scripts/run_trajectory.sh circle baseline
bash scripts/run_trajectory.sh circle feedforward
bash scripts/run_trajectory.sh square smooth
```

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
