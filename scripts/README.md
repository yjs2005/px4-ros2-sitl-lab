# Scripts

This directory contains small helper scripts for SITL-only node launch and offline analysis.

## SITL Runners

- `run_offboard_hover.sh`: sources ROS 2 and runs `ros2 run px4_offboard_lab offboard_hover` after the user confirms SITL prerequisites.
- `run_figure8.sh`: sources ROS 2 and runs `ros2 run px4_offboard_lab offboard_figure8` after the user confirms SITL prerequisites.
- `run_trajectory.sh`: runs the unified `offboard_trajectory` node with a trajectory and controller mode, for example `circle baseline`, `circle feedforward`, or `square smooth`.

The runner scripts do not start PX4, Gazebo, or Micro XRCE-DDS Agent automatically, and they do not kill existing processes.

`run_trajectory.sh` also sets:

```text
log_dir=<project-root>/logs
save_csv=true
```

New logs are saved as:

```text
logs/offboard_trajectory_<trajectory>_<controller_mode>_<timestamp>.csv
```

The script does not delete old CSV files and does not modify PX4 parameters.

## Offline Analysis

- `analyze_all.sh`: runs hover analysis, figure-eight analysis, trajectory-suite analysis, control-mode comparison, and project-level summary generation from committed CSV files.

GIF generation is kept separate:

```bash
python3 analysis/generate_gifs.py
```
