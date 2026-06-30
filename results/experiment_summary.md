# Experiment Summary

This summary is generated from existing CSV logs only. No PX4, Gazebo, ROS 2 node, or Offboard experiment is run by the analysis.

## Experiment Data Audit

All required circle, square, and figure-eight comparison CSV files are present.

Selected CSV files:

- `circle baseline`: `logs/offboard_trajectory_circle_baseline_20260629_235707.csv`
- `circle feedforward`: `logs/offboard_trajectory_circle_feedforward_20260630_003510.csv`
- `square baseline`: `logs/offboard_trajectory_square_baseline_20260630_120601.csv`
- `square smooth`: `logs/offboard_trajectory_square_smooth_20260630_120804.csv`
- `figure8 baseline`: `logs/offboard_trajectory_figure8_baseline_20260630_115423.csv`
- `figure8 feedforward`: `logs/offboard_trajectory_figure8_feedforward_20260630_120214.csv`
- `figure8 planar_ff g=0.5`: `logs/offboard_trajectory_figure8_planar_ff_g0p5_20260630_130443.csv`
- `figure8 planar_ff g=0.8`: `logs/offboard_trajectory_figure8_planar_ff_g0p8_20260630_130300.csv`
- `figure8 planar_ff g=1.0`: `logs/offboard_trajectory_figure8_planar_ff_g1_20260630_130606.csv`

Detailed audit files:

- `results/experiment_artifact_audit.md`
- `results/experiment_artifact_audit.csv`
- `results/experiment_artifact_audit.json`

## Overall Metrics

See `results/all_tracking_metrics.md` for the full table.

| Trajectory | Mode | XY RMSE (m) | z RMSE (m) | 3D RMSE (m) | Final error (m) |
| --- | --- | ---: | ---: | ---: | ---: |
| circle | baseline | 0.228 | 0.190 | 0.297 | 0.133 |
| circle | feedforward | 0.156 | 0.197 | 0.251 | 0.020 |
| square | baseline | 0.240 | 0.205 | 0.316 | 0.148 |
| square | smooth | 0.193 | 0.200 | 0.278 | 0.068 |
| figure8 | baseline | 0.221 | 0.187 | 0.289 | 0.282 |
| figure8 | feedforward | 0.061 | 0.379 | 0.384 | 0.017 |
| figure8 | planar_ff_g0p5 | 0.148 | 0.200 | 0.249 | 0.186 |
| figure8 | planar_ff_g0p8 | 0.077 | 0.199 | 0.213 | 0.068 |
| figure8 | planar_ff_g1 | 0.090 | 0.209 | 0.227 | 0.107 |

## Improvement Summary

See `results/all_tracking_improvements.md` for the full table. Positive values mean lower error than the reference.

| Comparison | XY RMSE | z RMSE | 3D RMSE | Max 3D error |
| --- | ---: | ---: | ---: | ---: |
| circle feedforward vs baseline | 31.63% | -3.46% | 15.43% | -3.69% |
| square smooth vs baseline | 19.76% | 2.27% | 11.99% | 1.53% |
| figure8 feedforward vs baseline | 72.32% | -102.55% | -32.64% | -50.47% |
| figure8 planar_ff g=0.5 vs baseline | 33.02% | -6.85% | 14.08% | 7.91% |
| figure8 planar_ff g=0.8 vs baseline | 65.11% | -6.37% | 26.26% | -5.80% |
| figure8 planar_ff g=1.0 vs baseline | 59.11% | -11.51% | 21.45% | 5.89% |
| figure8 planar_ff g=0.5 vs feedforward | -142.00% | 47.25% | 35.22% | 38.80% |
| figure8 planar_ff g=0.8 vs feedforward | -26.08% | 47.48% | 44.41% | 29.68% |
| figure8 planar_ff g=1.0 vs feedforward | -47.75% | 44.95% | 40.78% | 37.46% |

## Key Observations

- Circle feedforward has lower XY RMSE (0.228 -> 0.156 m) and lower 3D RMSE (0.297 -> 0.251 m).
- Square smooth has lower XY RMSE (0.240 -> 0.193 m) and lower 3D RMSE (0.316 -> 0.278 m).
- Figure-eight full feedforward has lower XY RMSE (0.221 -> 0.061 m), but z RMSE is higher (0.187 -> 0.379 m) and 3D RMSE is higher (0.289 -> 0.384 m).
- Figure-eight planar_ff g=0.8 gives XY RMSE 0.077 m, z RMSE 0.199 m, and 3D RMSE 0.213 m. In this dataset it is more balanced than full feedforward because it keeps strong XY improvement while avoiding the large z/3D degradation.
- Metrics are single-run SITL observations, not a robustness benchmark.

## Recommended README Figures

- `results/figures/all_tracking_xy_rmse.png`
- `results/figures/all_tracking_3d_rmse.png`
- `results/figures/circle_xy_tracking_comparison.png`
- `results/figures/square_xy_tracking_comparison.png`
- `results/figures/figure8_planar_ff_gain_xy_tracking_comparison.png`
- `results/figures/figure8_planar_ff_3d_rmse.png`
