# Offboard Hover Metrics

Source CSV: `logs/offboard_hover_first_success.csv`

Target position is PX4 local NED. Negative `z` means upward.

- Target NED: `x=0.00`, `y=0.00`, `z=-2.00`
- Whole-run samples: `364`
- Whole-run duration: `18.150 s`
- Median control frequency estimate: `20.00 Hz`

## Full Hover Stage

The full hover stage includes climb and convergence samples before the vehicle settles near the target altitude.

- Hover samples: `241`
- Hover duration: `12.000 s`
- Final hover z error: `0.0124 m`
- Hover z RMSE: `1.0455 m`
- Hover z MAE: `0.6963 m`
- Hover max absolute z error: `2.0018 m`
- Hover XY RMSE: `0.0466 m`
- Hover max XY error: `0.1159 m`
- Final hover position error: `0.0327 m`
- Max speed during hover: `1.1084 m/s`

## Steady-State Hover

Selection: `stage == "hover" and z <= -1.8`.

- Steady-state hover samples: `105`
- Steady-state hover duration: `5.200 s`
- Steady-state z RMSE: `0.0864 m`
- Steady-state z MAE: `0.0713 m`
- Steady-state max absolute z error: `0.1955 m`
- Steady-state XY RMSE: `0.0313 m`
- Steady-state max XY error: `0.0470 m`
- Steady-state final position error: `0.0327 m`
- Steady-state max speed: `0.0977 m/s`

## Stage Sample Counts

- `warmup`: `41`
- `arming`: `10`
- `offboard`: `11`
- `hover`: `241`
- `landing`: `61`

## Figures

- [Z tracking](figures/offboard_hover_z.png)
- [XY trajectory](figures/offboard_hover_xy.png)
- [NED position](figures/offboard_hover_ned_position.png)
- [NED velocity](figures/offboard_hover_velocity.png)
