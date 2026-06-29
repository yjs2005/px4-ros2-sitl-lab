# Scripts

This directory contains small helper scripts for SITL-only node launch and offline analysis.

## SITL Runners

- `run_offboard_hover.sh`: sources ROS 2 and runs `ros2 run px4_offboard_lab offboard_hover` after the user confirms SITL prerequisites.
- `run_figure8.sh`: sources ROS 2 and runs `ros2 run px4_offboard_lab offboard_figure8` after the user confirms SITL prerequisites.
- `run_trajectory.sh`: runs the unified `offboard_trajectory` node with `hover`, `line`, `square`, `circle`, `figure8`, or `z_step`.

The runner scripts do not start PX4, Gazebo, or Micro XRCE-DDS Agent automatically, and they do not kill existing processes.

## Offline Analysis

- `analyze_all.sh`: runs hover analysis, figure-eight analysis, trajectory-suite analysis, and project-level summary generation from committed CSV files.

GIF generation is kept separate:

```bash
python3 analysis/generate_gifs.py
```
