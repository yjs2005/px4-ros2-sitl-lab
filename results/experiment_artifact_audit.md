# Experiment Artifact Audit

This audit scans only `logs/*.csv`; it does not read `logs/bad_runs/`.

CSV status: all expected experiment CSV files are valid.

## CSV Inventory

| Trajectory | Mode | Selected CSV | Size (bytes) | Samples | Duration (s) | Valid | Notes |
| --- | --- | --- | ---: | ---: | ---: | --- | --- |
| circle | baseline | `logs/offboard_trajectory_circle_baseline_20260629_235707.csv` | 227778 | 771 | 40.000 | yes |  |
| circle | feedforward | `logs/offboard_trajectory_circle_feedforward_20260630_003510.csv` | 257488 | 772 | 39.950 | yes |  |
| square | baseline | `logs/offboard_trajectory_square_baseline_20260630_120601.csv` | 210283 | 771 | 39.950 | yes |  |
| square | smooth | `logs/offboard_trajectory_square_smooth_20260630_120804.csv` | 227368 | 767 | 39.950 | yes |  |
| figure8 | baseline | `logs/offboard_trajectory_figure8_baseline_20260630_115423.csv` | 235554 | 800 | 39.950 | yes |  |
| figure8 | feedforward | `logs/offboard_trajectory_figure8_feedforward_20260630_120214.csv` | 255699 | 778 | 40.000 | yes |  |
| figure8 | planar_ff_g0p5 | `logs/offboard_trajectory_figure8_planar_ff_g0p5_20260630_130443.csv` | 262035 | 776 | 39.950 | yes |  |
| figure8 | planar_ff_g0p8 | `logs/offboard_trajectory_figure8_planar_ff_g0p8_20260630_130300.csv` | 262604 | 780 | 40.000 | yes |  |
| figure8 | planar_ff_g1 | `logs/offboard_trajectory_figure8_planar_ff_g1_20260630_130606.csv` | 254786 | 749 | 40.000 | yes |  |

## Figure Coverage

All expected comparison figures are present.

## Selected Figure Groups

### circle baseline

- `results/figures/all_tracking_3d_error_std.png`
- `results/figures/all_tracking_3d_rmse.png`
- `results/figures/all_tracking_final_error.png`
- `results/figures/all_tracking_improvement_summary.png`
- `results/figures/all_tracking_xy_error_std.png`
- `results/figures/all_tracking_xy_rmse.png`
- `results/figures/all_tracking_z_rmse.png`
- `results/figures/circle_error_std_comparison.png`
- `results/figures/circle_error_timeseries.png`
- `results/figures/circle_xy_tracking_comparison.png`

### circle feedforward

- `results/figures/all_tracking_3d_error_std.png`
- `results/figures/all_tracking_3d_rmse.png`
- `results/figures/all_tracking_final_error.png`
- `results/figures/all_tracking_improvement_summary.png`
- `results/figures/all_tracking_xy_error_std.png`
- `results/figures/all_tracking_xy_rmse.png`
- `results/figures/all_tracking_z_rmse.png`
- `results/figures/circle_error_std_comparison.png`
- `results/figures/circle_error_timeseries.png`
- `results/figures/circle_xy_tracking_comparison.png`

### square baseline

- `results/figures/all_tracking_3d_error_std.png`
- `results/figures/all_tracking_3d_rmse.png`
- `results/figures/all_tracking_final_error.png`
- `results/figures/all_tracking_improvement_summary.png`
- `results/figures/all_tracking_xy_error_std.png`
- `results/figures/all_tracking_xy_rmse.png`
- `results/figures/all_tracking_z_rmse.png`
- `results/figures/square_error_std_comparison.png`
- `results/figures/square_error_timeseries.png`
- `results/figures/square_xy_tracking_comparison.png`

### square smooth

- `results/figures/all_tracking_3d_error_std.png`
- `results/figures/all_tracking_3d_rmse.png`
- `results/figures/all_tracking_final_error.png`
- `results/figures/all_tracking_improvement_summary.png`
- `results/figures/all_tracking_xy_error_std.png`
- `results/figures/all_tracking_xy_rmse.png`
- `results/figures/all_tracking_z_rmse.png`
- `results/figures/square_error_std_comparison.png`
- `results/figures/square_error_timeseries.png`
- `results/figures/square_xy_tracking_comparison.png`

### figure8 baseline

- `results/figures/all_tracking_3d_error_std.png`
- `results/figures/all_tracking_3d_rmse.png`
- `results/figures/all_tracking_final_error.png`
- `results/figures/all_tracking_improvement_summary.png`
- `results/figures/all_tracking_xy_error_std.png`
- `results/figures/all_tracking_xy_rmse.png`
- `results/figures/all_tracking_z_rmse.png`
- `results/figures/figure8_error_std_comparison.png`
- `results/figures/figure8_error_timeseries.png`
- `results/figures/figure8_planar_ff_gain_error_timeseries.png`
- `results/figures/figure8_planar_ff_gain_xy_tracking_comparison.png`
- `results/figures/figure8_xy_tracking_comparison.png`

### figure8 feedforward

- `results/figures/all_tracking_3d_error_std.png`
- `results/figures/all_tracking_3d_rmse.png`
- `results/figures/all_tracking_final_error.png`
- `results/figures/all_tracking_improvement_summary.png`
- `results/figures/all_tracking_xy_error_std.png`
- `results/figures/all_tracking_xy_rmse.png`
- `results/figures/all_tracking_z_rmse.png`
- `results/figures/figure8_error_std_comparison.png`
- `results/figures/figure8_error_timeseries.png`
- `results/figures/figure8_planar_ff_gain_error_timeseries.png`
- `results/figures/figure8_planar_ff_gain_xy_tracking_comparison.png`
- `results/figures/figure8_xy_tracking_comparison.png`

### figure8 planar_ff_g0p5

- `results/figures/all_tracking_3d_error_std.png`
- `results/figures/all_tracking_3d_rmse.png`
- `results/figures/all_tracking_final_error.png`
- `results/figures/all_tracking_improvement_summary.png`
- `results/figures/all_tracking_xy_error_std.png`
- `results/figures/all_tracking_xy_rmse.png`
- `results/figures/all_tracking_z_rmse.png`
- `results/figures/figure8_planar_ff_3d_rmse.png`
- `results/figures/figure8_planar_ff_final_error.png`
- `results/figures/figure8_planar_ff_gain_error_timeseries.png`
- `results/figures/figure8_planar_ff_gain_xy_tracking_comparison.png`
- `results/figures/figure8_planar_ff_xy_rmse.png`
- `results/figures/figure8_planar_ff_z_rmse.png`

### figure8 planar_ff_g0p8

- `results/figures/all_tracking_3d_error_std.png`
- `results/figures/all_tracking_3d_rmse.png`
- `results/figures/all_tracking_final_error.png`
- `results/figures/all_tracking_improvement_summary.png`
- `results/figures/all_tracking_xy_error_std.png`
- `results/figures/all_tracking_xy_rmse.png`
- `results/figures/all_tracking_z_rmse.png`
- `results/figures/figure8_error_std_comparison.png`
- `results/figures/figure8_error_timeseries.png`
- `results/figures/figure8_planar_ff_3d_rmse.png`
- `results/figures/figure8_planar_ff_final_error.png`
- `results/figures/figure8_planar_ff_gain_error_timeseries.png`
- `results/figures/figure8_planar_ff_gain_xy_tracking_comparison.png`
- `results/figures/figure8_planar_ff_xy_rmse.png`
- `results/figures/figure8_planar_ff_z_rmse.png`
- `results/figures/figure8_xy_tracking_comparison.png`

### figure8 planar_ff_g1

- `results/figures/all_tracking_3d_error_std.png`
- `results/figures/all_tracking_3d_rmse.png`
- `results/figures/all_tracking_final_error.png`
- `results/figures/all_tracking_improvement_summary.png`
- `results/figures/all_tracking_xy_error_std.png`
- `results/figures/all_tracking_xy_rmse.png`
- `results/figures/all_tracking_z_rmse.png`
- `results/figures/figure8_planar_ff_3d_rmse.png`
- `results/figures/figure8_planar_ff_final_error.png`
- `results/figures/figure8_planar_ff_gain_error_timeseries.png`
- `results/figures/figure8_planar_ff_gain_xy_tracking_comparison.png`
- `results/figures/figure8_planar_ff_xy_rmse.png`
- `results/figures/figure8_planar_ff_z_rmse.png`
