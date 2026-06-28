# px4-ros2-sitl-lab

This repository is a research-oriented scaffold for quadrotor simulation trajectory tracking and log analysis based on PX4 SITL, Gazebo, and ROS 2 Offboard control.

Current status: Phase 3 in progress: ROS 2 Offboard hover package implemented and built for SITL. No Offboard flight test has been run from this repository yet.

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
3. Implement ROS 2 Offboard takeoff and hover node
4. Record logs with rosbag2 and PX4 ULog
5. Visualize tracking errors
6. Organize README, results, and experiment notes

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

The default target hover point is PX4 local NED `(x=0.0, y=0.0, z=-2.0)`. In NED, negative `z` means upward.

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

## Safety

The Offboard hover node is simulation-only and not for real aircraft. Do not connect it to a physical vehicle. Phase 3 code creation and build validation do not count as a successful flight test.

## Notes

PX4-Autopilot is kept outside this repository at `/home/yjs/src/PX4-Autopilot`. ROS 2 Humble, Micro XRCE-DDS Agent, `px4_msgs`, and `px4_ros_com` have been installed and the PX4-to-ROS 2 `/fmu/...` topic bridge has been verified. Custom Offboard hover code now exists, but actual hover flight validation is still pending.
