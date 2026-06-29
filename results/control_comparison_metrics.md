# Control Mode Comparison Metrics

Paired baseline/improved logs found.

This analysis only uses logs that explicitly include a `controller_mode` column and match the new `offboard_trajectory_*_<mode>_*.csv` naming pattern.

## Metrics By Trajectory And Mode

| Trajectory | Mode | Samples | Duration (s) | XY RMSE (m) | z RMSE (m) | 3D RMSE (m) | Max 3D (m) | Final before landing (m) | Max speed (m/s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| circle | baseline | 771 | 40.000 | 0.2281 | 0.1905 | 0.2972 | 1.6321 | 0.1332 | 1.0982 |
| circle | feedforward | 772 | 39.950 | 0.1559 | 0.1971 | 0.2513 | 1.6924 | 0.0200 | 1.1328 |

## Paired Improvements

| Trajectory | Improved mode | XY RMSE improvement | z RMSE improvement | 3D RMSE improvement | Max error improvement |
| --- | --- | ---: | ---: | ---: | ---: |
| circle | feedforward | 31.63% | -3.46% | 15.43% | -3.69% |

## Figures

- `results/figures/control_comparison_xy_rmse.png`
- `results/figures/control_comparison_3d_rmse.png`
- `results/figures/control_comparison_percent_improvement.png`
