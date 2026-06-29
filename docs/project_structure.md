# Project Structure

This repository keeps the custom ROS 2 package, helper scripts, lightweight experiment logs, and offline analysis artifacts. PX4-Autopilot and the ROS 2 workspace stay outside the repository.

## `ros2/`

Repository source copy of the custom ROS 2 package:

```text
ros2/px4_offboard_lab/
```

Main nodes:

- `offboard_hover.py`: SITL-only Offboard takeoff, hover, land, and CSV logging.
- `offboard_figure8.py`: SITL-only Offboard figure-eight trajectory tracking and CSV logging.

The package should be synced into:

```text
~/px4_ros2_ws/src/px4_offboard_lab
```

## `scripts/`

Shell helpers for SITL and offline workflows:

- `run_offboard_hover.sh`: sources ROS 2 and runs the hover node after the user confirms SITL prerequisites.
- `run_figure8.sh`: sources ROS 2 and runs the figure-eight node after the user confirms SITL prerequisites.
- `analyze_all.sh`: runs the offline hover, figure-eight, and summary analysis scripts.

These scripts do not start PX4, Gazebo, or Micro XRCE-DDS Agent automatically.

## `analysis/`

Offline Python scripts:

- `analyze_offboard_hover.py`: parses `logs/offboard_hover_first_success.csv`.
- `analyze_figure8.py`: parses `logs/figure8_first_success.csv`.
- `generate_summary_visuals.py`: reads existing metrics JSON files and generates project-level summaries.
- `generate_gifs.py`: generates `media/figure8_tracking.gif` from the figure-eight CSV.

## `logs/`

Committed lightweight CSV experiment logs:

- `offboard_hover_first_success.csv`
- `figure8_first_success.csv`

Local PX4 ULog files belong under `logs/ulg/` and are ignored by default.

## `results/`

Generated analysis outputs:

- `offboard_hover_metrics.md` / `.json`
- `figure8_metrics.md` / `.json`
- `summary_metrics.md` / `.json` / `.csv`
- `project_pipeline.md`
- `figures/*.png`

## `media/`

Small visual assets generated from logs:

- `figure8_tracking.gif`
- `README.md`

## `docs/`

Project documentation:

- `environment_setup.md`
- `offboard_control.md`
- `trajectory_tracking.md`
- `reproducibility.md`
- `project_structure.md`
- safety and sim-to-real notes

## `notes/`

Working records and debugging notes:

- `experiment_log.md`: chronological project progress.
- `troubleshooting.md`: setup, bridge, Offboard, coordinate, and artifact-management issues.
- `local_environment_report.md`: environment notes.
