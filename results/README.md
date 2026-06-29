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
