# Reproducibility

This project was developed on Windows 11 with WSL2 Ubuntu 22.04. It uses PX4 SITL, Gazebo Harmonic, ROS 2 Humble, Micro XRCE-DDS Agent, and a custom ROS 2 Python package for Offboard control.

All flight-control scripts in this repository are simulation-only and not for real aircraft deployment.

## Local Paths

Windows repository:

```text
D:\42系保研准备\px4-ros2-sitl-lab
```

WSL repository copy:

```text
/home/yjs/src/px4-ros2-sitl-lab
```

External PX4-Autopilot checkout:

```text
/home/yjs/src/PX4-Autopilot
```

External ROS 2 workspace:

```text
/home/yjs/px4_ros2_ws
```

PX4-Autopilot and the ROS 2 workspace are not committed into this repository.

## Build The ROS 2 Package

Copy or sync `ros2/px4_offboard_lab` into:

```text
~/px4_ros2_ws/src/px4_offboard_lab
```

Then build:

```bash
cd ~/px4_ros2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash || true
colcon build --symlink-install
source install/setup.bash
ros2 pkg executables px4_offboard_lab
```

Expected executables:

```text
px4_offboard_lab offboard_hover
px4_offboard_lab offboard_figure8
px4_offboard_lab offboard_trajectory
```

## Run Hover In SITL

Start these processes manually in separate terminals:

```bash
MicroXRCEAgent udp4 -p 8888
```

```bash
cd ~/src/PX4-Autopilot
make px4_sitl gz_x500
```

QGroundControl should be open, or SITL preflight checks should otherwise be resolved.

Then run:

```bash
cd ~/src/px4-ros2-sitl-lab
bash scripts/run_offboard_hover.sh
```

## Run Figure-Eight In SITL

Start the same Agent and PX4 SITL Gazebo processes, then run:

```bash
cd ~/src/px4-ros2-sitl-lab
bash scripts/run_figure8.sh
```

The figure-eight node publishes a small bounded trajectory:

```text
x(t) = A * sin(omega * t)
y(t) = B * sin(2 * omega * t)
z(t) = -2.0
```

PX4 local position is NED, so negative `z` means upward.

## Run A Multi-Trajectory Experiment In SITL

The unified node supports:

```text
hover line square circle figure8 z_step
```

Example:

```bash
cd ~/src/px4-ros2-sitl-lab
bash scripts/run_trajectory.sh circle
```

Equivalent direct ROS 2 command:

```bash
ros2 run px4_offboard_lab offboard_trajectory --ros-args -p trajectory:=circle
```

Only hover and figure-eight have committed successful CSV results in this repository. Other modes are implemented and should be run deliberately in SITL before claiming results.

## Reproduce Analysis Only

The committed CSV logs are enough to reproduce the metrics, figures, and GIF without running PX4 or Gazebo:

```bash
cd ~/src/px4-ros2-sitl-lab
python3 analysis/analyze_offboard_hover.py
python3 analysis/analyze_figure8.py
python3 analysis/analyze_trajectory_suite.py
python3 analysis/generate_summary_visuals.py
python3 analysis/generate_gifs.py
```

Or:

```bash
bash scripts/analyze_all.sh
python3 analysis/generate_gifs.py
```

Primary outputs:

- `results/offboard_hover_metrics.md`
- `results/figure8_metrics.md`
- `results/trajectory_suite_metrics.md`
- `results/summary_metrics.md`
- `results/figures/metrics_summary.png`
- `media/figure8_tracking.gif`

## Artifact Policy

Committed:

- Lightweight CSV logs under `logs/*.csv`.
- Markdown and JSON metrics under `results/`.
- PNG figures under `results/figures/`.
- Small GIF media under `media/`.

Ignored:

- PX4 ULog binaries under `logs/ulg/*.ulg`.
- ROS workspace outputs such as `build/`, `install/`, `log/`, and `.colcon/`.
- Python caches and local IDE settings.

Do not connect these nodes to a physical aircraft.
