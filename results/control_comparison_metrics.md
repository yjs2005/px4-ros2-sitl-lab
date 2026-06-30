# Control Mode Comparison Metrics

Paired baseline/improved logs found.

This analysis only uses logs that explicitly include a `controller_mode` column and match the new `offboard_trajectory_*_<mode>_*.csv` naming pattern.

## Metrics By Trajectory And Mode

| Trajectory | Mode | ff_gain | Samples | Duration (s) | XY RMSE (m) | z RMSE (m) | 3D RMSE (m) | Max 3D (m) | Final before landing (m) | Max speed (m/s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| circle | baseline | 1.00 | 771 | 40.000 | 0.2281 | 0.1905 | 0.2972 | 1.6321 | 0.1332 | 1.0982 |
| circle | feedforward | 1.00 | 772 | 39.950 | 0.1559 | 0.1971 | 0.2513 | 1.6924 | 0.0200 | 1.1328 |
| figure8 | baseline | 1.00 | 800 | 39.950 | 0.2208 | 0.1871 | 0.2894 | 1.3343 | 0.2825 | 1.0560 |
| figure8 | feedforward | 1.00 | 778 | 40.000 | 0.0611 | 0.3790 | 0.3839 | 2.0077 | 0.0168 | 1.1865 |
| square | baseline | 1.00 | 771 | 39.950 | 0.2403 | 0.2046 | 0.3156 | 1.8296 | 0.1478 | 1.0977 |
| square | smooth | 1.00 | 767 | 39.950 | 0.1928 | 0.2000 | 0.2778 | 1.8015 | 0.0675 | 1.1051 |

## Paired Improvements

| Trajectory | Improved mode | ff_gain | XY RMSE improvement | z RMSE improvement | 3D RMSE improvement | Max error improvement |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| circle | feedforward | 1.00 | 31.63% | -3.46% | 15.43% | -3.69% |
| figure8 | feedforward | 1.00 | 72.32% | -102.55% | -32.64% | -50.47% |
| square | smooth | 1.00 | 19.76% | 2.27% | 11.99% | 1.53% |

## Figures

- `results/figures/control_comparison_xy_rmse.png`
- `results/figures/control_comparison_3d_rmse.png`
- `results/figures/control_comparison_percent_improvement.png`
