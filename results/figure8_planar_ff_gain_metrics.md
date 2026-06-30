# Figure-Eight Planar Feedforward Gain Sweep

This report compares figure-eight baseline, full velocity feedforward, and planar feedforward gains.

- Full `feedforward` can reduce XY tracking error but may worsen z and 3D errors.
- `planar_ff` applies velocity feedforward only in the NED XY plane and keeps `vz=0.0`.
- Positive improvement means the metric is lower than baseline.

## Metrics

| Mode | ff_gain | Samples | Duration (s) | XY RMSE (m) | z RMSE (m) | 3D RMSE (m) | Max 3D (m) | Final before landing (m) | Max speed (m/s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 1.00 | 800 | 39.950 | 0.2208 | 0.1871 | 0.2894 | 1.3343 | 0.2825 | 1.0560 |
| feedforward | 1.00 | 778 | 40.000 | 0.0611 | 0.3790 | 0.3839 | 2.0077 | 0.0168 | 1.1865 |
| planar_ff g=0.5 | 0.50 | 776 | 39.950 | 0.1479 | 0.1999 | 0.2487 | 1.2288 | 0.1856 | 0.7354 |
| planar_ff g=0.8 | 0.80 | 780 | 40.000 | 0.0770 | 0.1990 | 0.2134 | 1.4118 | 0.0684 | 1.0736 |
| planar_ff g=1.0 | 1.00 | 749 | 40.000 | 0.0903 | 0.2086 | 0.2273 | 1.2557 | 0.1069 | 0.7310 |

## Improvement Relative To Baseline

| Mode | ff_gain | XY RMSE | z RMSE | 3D RMSE | Max 3D error |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 1.00 | 0.00% | 0.00% | 0.00% | 0.00% |
| feedforward | 1.00 | 72.32% | -102.55% | -32.64% | -50.47% |
| planar_ff g=0.5 | 0.50 | 33.02% | -6.85% | 14.08% | 7.91% |
| planar_ff g=0.8 | 0.80 | 65.11% | -6.37% | 26.26% | -5.80% |
| planar_ff g=1.0 | 1.00 | 59.11% | -11.51% | 21.45% | 5.89% |

## Observation

Full feedforward changes XY RMSE from 0.2208 m to 0.0611 m, while z RMSE changes from 0.1871 m to 0.3790 m and 3D RMSE changes from 0.2894 m to 0.3839 m. Among planar_ff runs, planar_ff g=0.8 has the lowest 3D RMSE (0.2134 m), while planar_ff g=0.8 has the lowest XY RMSE (0.0770 m). Using equal normalized XY/z/3D error weighting, planar_ff g=0.8 is the most balanced planar_ff setting in this dataset.

## Selected Logs

- `baseline`: `logs/offboard_trajectory_figure8_baseline_20260630_115423.csv`
- `feedforward`: `logs/offboard_trajectory_figure8_feedforward_20260630_120214.csv`
- `planar_ff g=0.5`: `logs/offboard_trajectory_figure8_planar_ff_g0p5_20260630_130443.csv`
- `planar_ff g=0.8`: `logs/offboard_trajectory_figure8_planar_ff_g0p8_20260630_130300.csv`
- `planar_ff g=1.0`: `logs/offboard_trajectory_figure8_planar_ff_g1_20260630_130606.csv`

## Figures

- `results/figures/figure8_planar_ff_xy_rmse.png`
- `results/figures/figure8_planar_ff_z_rmse.png`
- `results/figures/figure8_planar_ff_3d_rmse.png`
- `results/figures/figure8_planar_ff_final_error.png`
- `results/figures/figure8_planar_ff_xy_tracking.png`
