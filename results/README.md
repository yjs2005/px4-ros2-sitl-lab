# Results

## Final experiment summary

The final offline analysis compares circle, square, and figure-eight tracking experiments across baseline and improved Offboard setpoint strategies. It uses only existing CSV logs and does not rerun PX4, Gazebo, ROS 2 nodes, or Offboard experiments.

Summary documents:

- [experiment_artifact_audit.md](experiment_artifact_audit.md)
- [all_tracking_metrics.md](all_tracking_metrics.md)
- [all_tracking_improvements.md](all_tracking_improvements.md)
- [experiment_summary.md](experiment_summary.md)

Key figures:

- `results/figures/all_tracking_xy_rmse.png`
- `results/figures/all_tracking_3d_rmse.png`
- `results/figures/all_tracking_z_rmse.png`
- `results/figures/all_tracking_improvement_summary.png`
- `results/figures/circle_xy_tracking_comparison.png`
- `results/figures/square_xy_tracking_comparison.png`
- `results/figures/figure8_xy_tracking_comparison.png`
- `results/figures/figure8_planar_ff_gain_xy_tracking_comparison.png`
- `results/figures/circle_error_timeseries.png`
- `results/figures/square_error_timeseries.png`
- `results/figures/figure8_error_timeseries.png`
- `results/figures/figure8_planar_ff_gain_error_timeseries.png`
- `results/figures/circle_error_std_comparison.png`
- `results/figures/square_error_std_comparison.png`
- `results/figures/figure8_error_std_comparison.png`

High-level observations from the current SITL CSV logs:

- Circle feedforward lowers XY RMSE and 3D RMSE, although max 3D error is slightly higher.
- Square smooth lowers XY RMSE and 3D RMSE, while XY/3D error standard deviation is higher in this single run.
- Figure-eight full feedforward strongly lowers XY RMSE but worsens z RMSE, 3D RMSE, and max 3D error.
- Figure-eight `planar_ff g=0.8` is the best tested tradeoff in this dataset: it keeps strong XY improvement while avoiding the full feedforward z/3D degradation.

本目录保存 PX4 SITL Offboard 实验的轻量、可复现分析结果，包括 Markdown 指标、JSON/CSV 汇总和 PNG 图表。

## 项目级汇总

生成命令：

```bash
python analysis/generate_summary_visuals.py
```

输出：

- `results/summary_metrics.md`
- `results/summary_metrics.json`
- `results/summary_metrics.csv`
- `results/figures/metrics_summary.png`
- `results/project_pipeline.md`

项目级汇总优先读取已有分析 JSON，不改变 hover 或 figure-eight 的原始分析逻辑。

![Metrics summary](figures/metrics_summary.png)

## Trajectory Suite Analysis

The suite analyzer is intended for comparing multiple trajectory modes after future runs:

```bash
python analysis/analyze_trajectory_suite.py
```

It scans:

- `logs/trajectory_*.csv`
- `logs/offboard_trajectory_*.csv`
- `logs/figure8_first_success.csv`

Outputs:

- `results/trajectory_suite_metrics.csv`
- `results/trajectory_suite_metrics.json`
- `results/trajectory_suite_metrics.md`
- `results/figures/trajectory_suite_metrics.png`

At the moment, committed measured results include hover and figure-eight. The new unified node also supports line, square, circle, and z_step, but those modes should not be reported as completed until their SITL CSV logs are captured and analyzed.

## Control Mode Comparison

The control comparison analyzer is for paired baseline vs improved experiments:

```bash
python analysis/compare_control_modes.py
```

It scans only logs that explicitly include `controller_mode` and match:

- `logs/offboard_trajectory_*_baseline_*.csv`
- `logs/offboard_trajectory_*_feedforward_*.csv`
- `logs/offboard_trajectory_*_planar_ff_*.csv`
- `logs/offboard_trajectory_*_smooth_*.csv`

Outputs:

- `results/control_comparison_metrics.csv`
- `results/control_comparison_metrics.json`
- `results/control_comparison_metrics.md`
- `results/figures/control_comparison_xy_rmse.png`
- `results/figures/control_comparison_3d_rmse.png`
- `results/figures/control_comparison_percent_improvement.png`

If paired logs are missing, the script exits normally and reports that paired SITL experiments should be run first. Existing hover and figure-eight result files are not reclassified as feedforward or smooth results.

## Figure-eight planar feedforward gain sweep

Generation command:

```bash
python analysis/compare_figure8_planar_ff_gain.py
```

Purpose:

- Full velocity feedforward significantly reduced figure-eight XY RMSE.
- The same full feedforward run increased z RMSE, 3D RMSE, and max 3D error.
- Planar feedforward was tested with `ff_gain = 0.5`, `0.8`, and `1.0` to check whether XY improvement could be retained while reducing vertical/3D degradation.

Inputs:

- `logs/offboard_trajectory_figure8_baseline_20260630_115423.csv`
- `logs/offboard_trajectory_figure8_feedforward_20260630_120214.csv`
- `logs/offboard_trajectory_figure8_planar_ff_g0p5_20260630_130443.csv`
- `logs/offboard_trajectory_figure8_planar_ff_g0p8_20260630_130300.csv`
- `logs/offboard_trajectory_figure8_planar_ff_g1_20260630_130606.csv`

Outputs:

- `results/figure8_planar_ff_gain_metrics.csv`
- `results/figure8_planar_ff_gain_metrics.json`
- `results/figure8_planar_ff_gain_metrics.md`
- `results/figures/figure8_planar_ff_xy_rmse.png`
- `results/figures/figure8_planar_ff_z_rmse.png`
- `results/figures/figure8_planar_ff_3d_rmse.png`
- `results/figures/figure8_planar_ff_final_error.png`
- `results/figures/figure8_planar_ff_xy_tracking.png`

Key observation from this dataset:

- Baseline: XY RMSE `0.2208 m`, z RMSE `0.1871 m`, 3D RMSE `0.2894 m`.
- Full feedforward: XY RMSE improved to `0.0611 m`, but z RMSE worsened to `0.3790 m` and 3D RMSE worsened to `0.3839 m`.
- `planar_ff g=0.8`: XY RMSE `0.0770 m`, z RMSE `0.1990 m`, 3D RMSE `0.2134 m`.

In this run, `planar_ff g=0.8` gives the best tradeoff among the tested planar gains: it keeps most of the XY improvement from full feedforward while avoiding the large z/3D error increase seen in full feedforward. This is an experiment observation from the current SITL logs, not a general robustness claim.

![Figure-eight planar FF XY RMSE](figures/figure8_planar_ff_xy_rmse.png)

![Figure-eight planar FF z RMSE](figures/figure8_planar_ff_z_rmse.png)

![Figure-eight planar FF 3D RMSE](figures/figure8_planar_ff_3d_rmse.png)

![Figure-eight planar FF XY tracking](figures/figure8_planar_ff_xy_tracking.png)

## Hover Analysis

输入 CSV：

- `logs/offboard_hover_first_success.csv`

生成命令：

```bash
python analysis/analyze_offboard_hover.py
```

输出：

- `results/offboard_hover_metrics.json`
- `results/offboard_hover_metrics.md`
- `results/figures/offboard_hover_z.png`
- `results/figures/offboard_hover_xy.png`
- `results/figures/offboard_hover_ned_position.png`
- `results/figures/offboard_hover_velocity.png`

关键结果：

- Steady-state hover definition: `stage == "hover" and z <= -1.8`
- Steady-state z RMSE: `0.0864 m`
- Steady-state XY RMSE: `0.0313 m`
- Steady-state final position error: `0.0327 m`

完整 hover 图表：

![Hover z tracking](figures/offboard_hover_z.png)

![Hover XY trajectory](figures/offboard_hover_xy.png)

![Hover NED position](figures/offboard_hover_ned_position.png)

![Hover velocity](figures/offboard_hover_velocity.png)

## Figure-Eight Analysis

输入 CSV：

- `logs/figure8_first_success.csv`

生成命令：

```bash
python analysis/analyze_figure8.py
```

输出：

- `results/figure8_metrics.json`
- `results/figure8_metrics.md`
- `results/figures/figure8_xy_tracking.png`
- `results/figures/figure8_z_tracking.png`
- `results/figures/figure8_position_error.png`
- `results/figures/figure8_velocity.png`

Tracking-stage filter:

```text
stage == "figure8"
```

关键结果：

- Tracking duration: `40.000 s`
- XY RMSE: `0.2003 m`
- z RMSE: `0.1944 m`
- 3D position RMSE: `0.2791 m`
- Max 3D position error: `1.3506 m`
- Final position error before landing: `0.2492 m`

完整 figure-eight 图表：

![Figure-eight XY tracking](figures/figure8_xy_tracking.png)

![Figure-eight z tracking](figures/figure8_z_tracking.png)

![Figure-eight position error](figures/figure8_position_error.png)

![Figure-eight velocity](figures/figure8_velocity.png)

## Media

生成命令：

```bash
python analysis/generate_gifs.py
```

输出：

- `media/figure8_tracking.gif`

GIF 由 `logs/figure8_first_success.csv` 离线生成，展示 NED XY 平面上的目标轨迹和实际轨迹。它不依赖重新运行 PX4 或 Gazebo。

## 说明

Hover 是固定点跟踪，figure-eight 是时变 XY 轨迹跟踪。两者均为 PX4 SITL 仿真结果，使用 ROS 2 Offboard setpoint 通过 PX4 `/fmu/in/...` 话题发送控制输入。
