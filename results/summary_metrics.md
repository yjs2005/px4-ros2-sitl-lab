# Summary Metrics

This project-level summary is generated from existing analysis JSON files:

- `results/offboard_hover_metrics.json`
- `results/figure8_metrics.json`

PX4 local position uses NED coordinates. Negative `z` means upward.

## Key Results

| Experiment | Metric | Value | Unit |
| --- | --- | ---: | --- |
| hover_steady_state | steady_state_z_rmse | 0.0864 | m |
| hover_steady_state | steady_state_xy_rmse | 0.0313 | m |
| hover_steady_state | final_position_error | 0.0327 | m |
| hover_steady_state | max_steady_state_speed | 0.0977 | m/s |
| figure8_tracking | tracking_duration | 39.9998 | s |
| figure8_tracking | xy_rmse | 0.2003 | m |
| figure8_tracking | z_rmse | 0.1944 | m |
| figure8_tracking | position_rmse | 0.2791 | m |
| figure8_tracking | max_position_error | 1.3506 | m |
| figure8_tracking | final_position_error_before_landing | 0.2492 | m |
| figure8_tracking | max_tracking_speed | 1.0536 | m/s |

## Hover Steady-State

- Definition: `stage == "hover" and z <= -1.8`
- Samples: `105`
- Duration: `5.200 s`
- z RMSE: `0.0864 m`
- XY RMSE: `0.0313 m`
- Final position error: `0.0327 m`
- Max steady-state speed: `0.0977 m/s`

## Figure-Eight Tracking

- Definition: `stage == "figure8"`
- Samples: `758`
- Duration: `40.000 s`
- XY RMSE: `0.2003 m`
- z RMSE: `0.1944 m`
- 3D position RMSE: `0.2791 m`
- Max 3D position error: `1.3506 m`
- Final position error before landing: `0.2492 m`
- Max tracking speed: `1.0536 m/s`

## Generated Figure

- `results/figures/metrics_summary.png`
