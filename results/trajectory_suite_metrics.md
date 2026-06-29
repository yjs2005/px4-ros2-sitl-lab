# Trajectory Suite Metrics

This summary scans committed or future trajectory CSV logs without overwriting individual hover or figure-eight analyses.

Tracking-stage inference:

`rows where stage is tracking/trajectory/figure8, or where stage equals trajectory_type`

## Metrics

| Trajectory | Samples | Duration (s) | XY RMSE (m) | XY MAE (m) | Max XY (m) | z RMSE (m) | z MAE (m) | 3D RMSE (m) | Max 3D (m) | Max speed (m/s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| figure8 | 758 | 40.000 | 0.2003 | 0.1850 | 0.5037 | 0.1944 | 0.0671 | 0.2791 | 1.3506 | 1.0536 |

## Source Files

- `figure8`:
  - `logs/figure8_first_success.csv`

## Figure

- `results/figures/trajectory_suite_metrics.png`
