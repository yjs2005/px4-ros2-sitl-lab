# Figure-Eight Tracking Metrics

Source CSV: `logs/figure8_first_success.csv`

PX4 local position uses NED coordinates. Negative `z` means upward.

- Tracking filter: `stage == "figure8"`
- Landing stage present: `True`
- Target NED altitude: `z=-2.00`
- Whole-run samples: `941`
- Whole-run duration: `50.800 s`
- Median whole-run frequency estimate: `20.00 Hz`

## Figure-Eight Tracking Stage

- Tracking samples: `758`
- Tracking duration: `40.000 s`
- Median tracking frequency estimate: `20.00 Hz`
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

## Stage Sample Counts

- `warmup`: `41`
- `arming`: `10`
- `offboard`: `11`
- `pre_figure8_hover`: `61`
- `figure8`: `758`
- `landing`: `60`

## Figures

- [XY tracking](figures/figure8_xy_tracking.png)
- [Z tracking](figures/figure8_z_tracking.png)
- [Position error](figures/figure8_position_error.png)
- [Velocity](figures/figure8_velocity.png)
