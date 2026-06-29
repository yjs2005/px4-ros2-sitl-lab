# Trajectory Tracking

This document records the Phase 4 trajectory-analysis workflow and the planned PX4 SITL figure-eight Offboard experiment. The scope is simulation-only and not for real aircraft deployment.

## Hover Tracking

The first successful hover experiment used the target:

```text
PX4 NED: x = 0.0, y = 0.0, z = -2.0
```

PX4 local position uses NED coordinates: North, East, Down. Negative `z` is upward, so `z=-2.0` means about 2 meters above the local origin.

The hover CSV is:

```text
logs/offboard_hover_first_success.csv
```

The analysis script computes whole-run and hover-stage metrics, then creates tracking plots:

```bash
python analysis/analyze_offboard_hover.py
```

Generated outputs:

- `results/offboard_hover_metrics.json`
- `results/offboard_hover_metrics.md`
- `results/figures/offboard_hover_z.png`
- `results/figures/offboard_hover_xy.png`
- `results/figures/offboard_hover_ned_position.png`
- `results/figures/offboard_hover_velocity.png`

## Figure-Eight Tracking

The `offboard_figure8` node is implemented for a later PX4 SITL experiment. It is not yet flight-verified.

The small figure-eight setpoint is:

```text
x(t) = A * sin(omega * t)
y(t) = B * sin(2 * omega * t)
z(t) = -2.0
```

Default parameters:

- `A = 1.0 m`
- `B = 0.6 m`
- `z = -2.0 m`
- duration about `40 s`
- publish rate `20 Hz`

The trajectory starts near `(0, 0, -2)` after warm-up and a short hover, then returns to a small bounded path suitable for the default Gazebo world.

## Offboard Warm-Up

PX4 Offboard mode requires a continuous stream of setpoints before and during OFFBOARD mode. The nodes therefore use:

```text
setpoint warm-up -> arm -> OFFBOARD -> trajectory -> land
```

Switching to OFFBOARD before setpoints are streaming can cause mode rejection or failsafe.

## Safety Constraints

- SITL only.
- Do not connect these nodes to a real aircraft.
- Keep setpoint rate at or above 10 Hz; this package defaults to 20 Hz.
- Keep trajectories small until tracking behavior is measured.
- QGroundControl should be open, or SITL preflight checks should be otherwise resolved, before attempting Offboard takeoff.

## Figure-Eight Metrics To Compute Later

After a figure-eight run, save the node CSV and PX4 ULog. Recommended metrics:

- XY RMSE
- z RMSE
- max position error
- max speed
- tracking plots for x/y/z position
- XY trajectory plot against target
- velocity plots
- CSV and ULog artifact paths

Do not claim figure-eight flight success until the SITL experiment has actually been run.
