# Trajectory Tracking

This document records the Phase 4 trajectory-analysis workflow and the first PX4 SITL figure-eight Offboard analysis. The scope is simulation-only and not for real aircraft deployment.

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

The `offboard_figure8` node has been implemented and the first copied CSV has been analyzed offline:

```text
logs/figure8_first_success.csv
```

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

The analyzed CSV contains these stages:

- `warmup`
- `arming`
- `offboard`
- `pre_figure8_hover`
- `figure8`
- `landing`

The tracking-stage filter is:

```text
stage == "figure8"
```

Generated outputs:

- `results/figure8_metrics.json`
- `results/figure8_metrics.md`
- `results/figures/figure8_xy_tracking.png`
- `results/figures/figure8_z_tracking.png`
- `results/figures/figure8_position_error.png`
- `results/figures/figure8_velocity.png`
- `media/figure8_tracking.gif`

Summary:

- Whole-run samples: `941`
- Whole-run duration: `50.800 s`
- Median logging/control frequency estimate: `20.00 Hz`
- Figure-eight tracking samples: `758`
- Figure-eight tracking duration: `40.000 s`
- XY RMSE: `0.2003 m`
- XY MAE: `0.1850 m`
- Max XY error: `0.5037 m`
- z RMSE: `0.1944 m`
- z MAE: `0.0671 m`
- Max absolute z error: `1.3490 m`
- 3D position RMSE: `0.2791 m`
- Max 3D position error: `1.3506 m`
- Final position error before landing: `0.2492 m`
- Max speed during tracking: `1.0536 m/s`

The CSV shows time-varying `target_x` and `target_y` setpoints, a figure-eight tracking stage, and a landing stage. This supports recording the figure-eight Offboard trajectory experiment as completed in PX4 SITL for this dataset.

## Hover vs Figure-Eight Tracking

Hover tracking is fixed-point tracking: the target remains near PX4 NED `(0, 0, -2)`.

Figure-eight tracking is time-varying trajectory tracking: `target_x` and `target_y` change continuously while `target_z` remains `-2.0`.

Both experiments use ROS 2 Offboard setpoints through PX4 `/fmu/in/...` topics and observe vehicle state through `/fmu/out/...` topics.

Project-level summaries are available at:

- `results/summary_metrics.md`
- `results/summary_metrics.json`
- `results/summary_metrics.csv`
- `results/figures/metrics_summary.png`
- `results/project_pipeline.md`

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

## Figure-Eight Metrics

After a figure-eight run, save the node CSV and PX4 ULog. Recommended metrics:

- XY RMSE
- z RMSE
- max position error
- max speed
- tracking plots for x/y/z position
- XY trajectory plot against target
- velocity plots
- CSV and ULog artifact paths

Do not use these SITL results as evidence of real-aircraft readiness.
