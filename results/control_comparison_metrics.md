# Control Mode Comparison Metrics

No paired baseline/improved logs found yet. Run paired SITL experiments first.

This analysis only uses logs that explicitly include a `controller_mode` column and match the new `offboard_trajectory_*_<mode>_*.csv` naming pattern.

## Metrics By Trajectory And Mode

| Trajectory | Mode | Samples | Duration (s) | XY RMSE (m) | z RMSE (m) | 3D RMSE (m) | Max 3D (m) | Final before landing (m) | Max speed (m/s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| n/a | n/a | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

## Paired Improvements

| Trajectory | Improved mode | XY RMSE improvement | z RMSE improvement | 3D RMSE improvement | Max error improvement |
| --- | --- | ---: | ---: | ---: | ---: |
| n/a | n/a | n/a | n/a | n/a | n/a |

## Figures

- `results/figures/control_comparison_xy_rmse.png`
- `results/figures/control_comparison_3d_rmse.png`
- `results/figures/control_comparison_percent_improvement.png`
