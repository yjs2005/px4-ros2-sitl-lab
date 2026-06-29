# PX4 ROS 2 SITL 无人机 Offboard 控制与轨迹分析实验

基于 PX4 SITL、Gazebo Harmonic、ROS 2 Humble 的无人机 Offboard 仿真控制项目，实现 X500 四旋翼定点悬停、8 字轨迹跟踪、CSV 日志记录和离线轨迹误差分析。

## 动态效果：8 字轨迹跟踪

下面的 GIF 由 `logs/figure8_first_success.csv` 生成，展示目标轨迹与实际轨迹在 NED XY 平面上的推进过程，不是重新录屏或重新运行 Gazebo。

![Figure-eight tracking GIF](media/figure8_tracking.gif)

## 核心结果

PX4 local position 使用 NED 坐标系，`z` 轴向下，因此 `z=-2.0` 表示向上约 2 m。

| 实验 | 控制目标 | 关键结果 |
| --- | --- | --- |
| 定点悬停 | NED `(0, 0, -2)` | 稳态 z RMSE `0.0864 m`，XY RMSE `0.0313 m`，最终位置误差 `0.0327 m` |
| 8 字轨迹 | `x=sin(t)`, `y=sin(2t)`, `z=-2`，跟踪 `40.000 s` | XY RMSE `0.2003 m`，z RMSE `0.1944 m`，3D RMSE `0.2791 m` |

详细指标见：

- [results/summary_metrics.md](results/summary_metrics.md)
- [results/offboard_hover_metrics.md](results/offboard_hover_metrics.md)
- [results/figure8_metrics.md](results/figure8_metrics.md)

## 项目亮点

- 搭建 PX4 SITL + Gazebo Harmonic X500 四旋翼仿真环境。
- 使用 Micro XRCE-DDS Agent 打通 PX4 与 ROS 2 `/fmu/...` 话题桥接。
- 实现 ROS 2 Python Offboard 节点，按 20 Hz 发布 setpoint，并在切入 OFFBOARD 前进行 setpoint warm-up。
- 在 PX4 NED 坐标系下完成定点悬停与 8 字轨迹跟踪。
- 记录 CSV 日志，生成 JSON / Markdown 指标、PNG 图表和 GIF 动态可视化。
- 不提交 PX4-Autopilot、ULog 大文件和构建产物，仓库保持轻量、可复现。

## 方法流程

完整流程图见 [results/project_pipeline.md](results/project_pipeline.md)。

```text
Windows / WSL2 Ubuntu
-> PX4 SITL + Gazebo Harmonic X500
-> Micro XRCE-DDS Agent
-> ROS 2 Humble + px4_msgs + px4_ros_com
-> ROS 2 Offboard hover / figure-eight nodes
-> CSV logs
-> analysis scripts
-> metrics / figures / GIF / README
```

## 结果图精选

![Metrics summary](results/figures/metrics_summary.png)

![Figure-eight XY tracking](results/figures/figure8_xy_tracking.png)

![Hover z tracking](results/figures/offboard_hover_z.png)

完整图表见 [results/README.md](results/README.md)。

## 快速复现

详细环境说明见 [docs/reproducibility.md](docs/reproducibility.md)。下面只保留核心命令。

### 构建 ROS 2 Package

```bash
cd ~/px4_ros2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash || true
colcon build --symlink-install
source install/setup.bash
ros2 pkg executables px4_offboard_lab
```

### 启动 SITL 与 Agent

分别在不同终端中启动：

```bash
MicroXRCEAgent udp4 -p 8888
```

```bash
cd ~/src/PX4-Autopilot
make px4_sitl gz_x500
```

运行 Offboard 前应打开 QGroundControl，或确保 SITL preflight checks 已解决。

### 运行 Hover / Figure-Eight

```bash
bash scripts/run_offboard_hover.sh
bash scripts/run_figure8.sh
```

### 运行离线分析

不需要重新运行 PX4 或 Gazebo，可直接从已提交 CSV 复现实验图表：

```bash
bash scripts/analyze_all.sh
python3 analysis/generate_gifs.py
```

## 项目结构

```text
px4-ros2-sitl-lab/
├── analysis/              # 离线分析、汇总图和 GIF 生成脚本
├── docs/                  # 环境、Offboard、轨迹和复现说明
├── logs/                  # 轻量 CSV 实验日志
├── media/                 # GIF 可视化产物
├── notes/                 # 实验记录与 troubleshooting
├── results/               # 指标、图表和项目级汇总
├── ros2/px4_offboard_lab/ # ROS 2 Offboard package 源码副本
└── scripts/               # SITL 运行脚本和离线分析入口
```

更完整说明见 [docs/project_structure.md](docs/project_structure.md)。

## 数据与可视化产物

- Hover CSV: [logs/offboard_hover_first_success.csv](logs/offboard_hover_first_success.csv)
- Figure-eight CSV: [logs/figure8_first_success.csv](logs/figure8_first_success.csv)
- 指标与图表: [results/](results/)
- 动态可视化: [media/figure8_tracking.gif](media/figure8_tracking.gif)

`logs/ulg/*.ulg` 为本地 PX4 ULog 二进制日志，默认不提交。PX4-Autopilot 和 ROS 2 workspace 也不放入本仓库。

## 局限性

- 仅完成 SITL 仿真验证，未做真机部署。
- 8 字结果来自一次受控仿真实验，不是鲁棒性 benchmark。
- 指标受 PX4 参数、Gazebo 仿真环境、Offboard 控制参数、QGroundControl / failsafe 状态影响。
- ULog、大型视频和构建产物默认不提交，以保持仓库轻量。

