# px4-ros2-sitl-lab

This repository is a research-oriented scaffold for quadrotor simulation trajectory tracking and log analysis based on PX4 SITL, Gazebo, and ROS 2 Offboard control.

Current status: Phase 4 hover trajectory analysis completed; the first figure-eight Offboard trajectory CSV has been analyzed from PX4 SITL.

## Project Goal

Build a reproducible PX4 SITL + Gazebo + ROS 2 Offboard workflow for simulated quadrotor trajectory tracking and post-flight log analysis.

## Planned Tech Stack

- PX4-Autopilot
- Gazebo
- ROS 2 Humble
- Micro XRCE-DDS Agent
- px4_msgs
- Python
- Matplotlib
- rosbag2

## Planned Features

- Takeoff
- Hover
- Square trajectory tracking
- Circular trajectory tracking
- Figure-eight trajectory tracking
- Log recording
- Trajectory error analysis

## Roadmap

1. Environment setup
2. Verify PX4 SITL, Gazebo, Micro XRCE-DDS Agent, and ROS 2 topic bridge
3. Implement and verify ROS 2 Offboard takeoff and hover node in PX4 SITL
4. Analyze hover tracking logs and generate figures
5. Implement figure-eight Offboard trajectory node
6. Analyze first figure-eight trajectory CSV
7. Record future trajectory logs with rosbag2 and PX4 ULog
8. Organize README, results, and experiment notes

## Phase 3 Offboard Hover Node

The Phase 3 package is `px4_offboard_lab`.

Source copy in this repository:

```text
ros2/px4_offboard_lab/
```

Workspace location for building and running:

```text
~/px4_ros2_ws/src/px4_offboard_lab
```

The node publishes:

- `/fmu/in/offboard_control_mode`
- `/fmu/in/trajectory_setpoint`
- `/fmu/in/vehicle_command`

The node subscribes:

- `/fmu/out/vehicle_status`
- `/fmu/out/vehicle_status_v4` for the currently observed PX4 message-versioned topic
- `/fmu/out/vehicle_odometry`

The verified target hover point is PX4 local NED `(x=0.0, y=0.0, z=-2.0)`. In NED, negative `z` means upward. The first successful run converged to about `z=-1.97 m`.

To build after copying the package into the ROS 2 workspace:

```bash
cd ~/px4_ros2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
colcon build --symlink-install
source install/setup.bash
ros2 pkg list | grep px4_offboard_lab
```

To run later in SITL only, first start these in separate terminals:

```bash
MicroXRCEAgent udp4 -p 8888
cd ~/src/PX4-Autopilot && make px4_sitl gz_x500
```

Then run:

```bash
bash scripts/run_offboard_hover.sh
```

For command-free rehearsal:

```bash
bash scripts/run_offboard_hover.sh --dry-run
```

Verified Phase 3 control flow:

```text
setpoint warm-up -> arm -> OFFBOARD -> hover -> land -> disarm
```

Observed success markers:

- PX4 commander reported `Armed by external command`.
- PX4 commander reported `Takeoff detected`.
- ROS 2 node reached hover stage with `arming_state=2` and `nav_state=14`.
- Vehicle reached close to NED target `(0.0, 0.0, -2.0)`, with observed `z` about `-1.97 m`.
- Node sent `Land command sent`.
- PX4 commander reported `Landing detected` and `Disarmed by landing`.
- Node printed `Offboard hover node sequence complete; shutting down`.

Experiment artifacts:

- Lightweight CSV artifact intended for this repository: `logs/offboard_hover_first_success.csv`.
- Local ULog artifact: `logs/ulg/offboard_hover_first_success.ulg`.

ULog files are ignored by default and should not be committed unless there is a specific reason to preserve a small curated binary artifact.

## Phase 4 Hover Analysis

Phase 4 computed trajectory metrics and generated plots from the first successful hover CSV.

Source artifact:

- [logs/offboard_hover_first_success.csv](logs/offboard_hover_first_success.csv)

Results:

- [results/offboard_hover_metrics.md](results/offboard_hover_metrics.md)
- [results/offboard_hover_metrics.json](results/offboard_hover_metrics.json)
- [results/figures/offboard_hover_z.png](results/figures/offboard_hover_z.png)
- [results/figures/offboard_hover_xy.png](results/figures/offboard_hover_xy.png)
- [results/figures/offboard_hover_ned_position.png](results/figures/offboard_hover_ned_position.png)
- [results/figures/offboard_hover_velocity.png](results/figures/offboard_hover_velocity.png)

Summary from the CSV:

- Whole-run samples: `364`
- Whole-run duration: `18.150 s`
- Median control frequency estimate: `20.00 Hz`

Full hover-stage metrics include the climb and convergence transient after the node enters the `hover` stage:

- Hover-stage samples: `241`
- Hover-stage duration: `12.000 s`
- Full hover-stage z RMSE: `1.0455 m`
- Full hover-stage XY RMSE: `0.0466 m`
- Full hover-stage max speed: `1.1084 m/s`

Steady-state hover metrics use samples where `stage == "hover"` and `z <= -1.8`, isolating the settled portion near the target altitude:

- Steady-state samples: `105`
- Steady-state duration: `5.200 s`
- Steady-state z RMSE: `0.0864 m`
- Steady-state z MAE: `0.0713 m`
- Steady-state max absolute z error: `0.1955 m`
- Steady-state XY RMSE: `0.0313 m`
- Steady-state max XY error: `0.0470 m`
- Steady-state final position error: `0.0327 m`
- Steady-state max speed: `0.0977 m/s`

The final hover z error is `0.0124 m`; the larger full hover-stage z RMSE is retained because it captures the climb-to-altitude transient.

To regenerate:

```bash
python analysis/analyze_offboard_hover.py
```

## Figure-Eight Experiment And Analysis

The `offboard_figure8` node has been implemented and built in the existing `px4_offboard_lab` package. The first figure-eight CSV has been copied into this repository and analyzed offline.

Default trajectory:

```text
x(t) = 1.0 * sin(omega * t)
y(t) = 0.6 * sin(2 * omega * t)
z(t) = -2.0
duration ~= 40 s
rate = 20 Hz
```

The node uses the same safety and Offboard flow:

```text
setpoint warm-up -> arm -> OFFBOARD -> pre-figure-eight hover -> figure-eight -> land
```

Figure-eight source artifact:

- [logs/figure8_first_success.csv](logs/figure8_first_success.csv)

Figure-eight results:

- [results/figure8_metrics.md](results/figure8_metrics.md)
- [results/figure8_metrics.json](results/figure8_metrics.json)
- [results/figures/figure8_xy_tracking.png](results/figures/figure8_xy_tracking.png)
- [results/figures/figure8_z_tracking.png](results/figures/figure8_z_tracking.png)
- [results/figures/figure8_position_error.png](results/figures/figure8_position_error.png)
- [results/figures/figure8_velocity.png](results/figures/figure8_velocity.png)

The CSV contains `warmup`, `arming`, `offboard`, `pre_figure8_hover`, `figure8`, and `landing` stages. Tracking metrics use `stage == "figure8"` as the figure-eight window.

Summary from the figure-eight CSV:

- Whole-run samples: `941`
- Whole-run duration: `50.800 s`
- Median frequency estimate: `20.00 Hz`
- Figure-eight tracking samples: `758`
- Figure-eight tracking duration: `40.000 s`
- XY RMSE: `0.2003 m`
- XY MAE: `0.1850 m`
- Max XY error: `0.5037 m`
- z RMSE: `0.1944 m`
- z MAE: `0.0671 m`
- Max absolute z error: `1.3490 m`
- 3D position RMSE: `0.2791 m`
- Max 3D position error: `1.3506 m`
- Final position error before landing: `0.2492 m`
- Max speed during tracking: `1.0536 m/s`

This is time-varying trajectory tracking: the node generated changing `target_x` and `target_y` setpoints through PX4 `/fmu/in/...` topics. Hover is fixed-point tracking at `(0, 0, -2)`, while figure-eight tracking follows a moving XY setpoint at the same NED altitude convention.

After building and starting the required SITL processes manually, run:

```bash
bash scripts/run_figure8.sh
```

To regenerate the offline analysis:

```bash
python analysis/analyze_figure8.py
```

## Safety

The Offboard nodes are simulation-only and not for real aircraft deployment. Do not connect them to a physical vehicle.

## Notes

PX4-Autopilot is kept outside this repository at `/home/yjs/src/PX4-Autopilot`. ROS 2 Humble, Micro XRCE-DDS Agent, `px4_msgs`, and `px4_ros_com` have been installed and the PX4-to-ROS 2 `/fmu/...` topic bridge has been verified. Custom Offboard hover has been verified in PX4 SITL, and figure-eight Offboard code is ready for a later SITL-only experiment.
