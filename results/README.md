# Results

This directory stores lightweight, reproducible result summaries for PX4 SITL experiments.

## Phase 4 Hover Analysis

The first successful Offboard hover CSV is analyzed by:

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

The source CSV is `logs/offboard_hover_first_success.csv`.

Summary:

- Whole-run samples: `364`
- Median control frequency estimate: `20.00 Hz`
- Full hover-stage duration: `12.000 s`
- Full hover-stage z RMSE: `1.0455 m`
- Full hover-stage XY RMSE: `0.0466 m`
- Steady-state hover definition: `stage == "hover" and z <= -1.8`
- Steady-state hover duration: `5.200 s`
- Steady-state z RMSE: `0.0864 m`
- Steady-state z MAE: `0.0713 m`
- Steady-state XY RMSE: `0.0313 m`
- Steady-state final position error: `0.0327 m`

The full hover-stage metrics intentionally retain the climb-to-altitude transient. Use the steady-state hover metrics when evaluating settled tracking near the target NED altitude `z=-2.0`.

## Figure-Eight Analysis

The first copied figure-eight Offboard CSV is analyzed by:

```bash
python analysis/analyze_figure8.py
```

Generated outputs:

- `results/figure8_metrics.json`
- `results/figure8_metrics.md`
- `results/figures/figure8_xy_tracking.png`
- `results/figures/figure8_z_tracking.png`
- `results/figures/figure8_position_error.png`
- `results/figures/figure8_velocity.png`

The source CSV is `logs/figure8_first_success.csv`.

The tracking-stage filter is `stage == "figure8"`. The CSV also contains a `landing` stage, so this dataset records a completed SITL trajectory sequence.

Summary:

- Whole-run samples: `941`
- Median logging/control frequency estimate: `20.00 Hz`
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

Hover is fixed-point tracking, while figure-eight is time-varying XY tracking. Both are PX4 SITL-only results using ROS 2 Offboard setpoints through `/fmu/in/...`.
