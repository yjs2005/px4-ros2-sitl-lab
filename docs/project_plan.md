# Project Plan

## Phase 0: Repository Scaffold and Environment Check

- Initialize repository structure.
- Record local Windows, WSL, Git, Python, CPU, memory, disk, and GPU information.
- Identify whether the machine is ready for PX4 SITL + Gazebo + ROS 2 Humble.

## Phase 1: Install ROS 2 Humble

- Install ROS 2 Humble on Ubuntu 22.04.
- Verify shell setup and basic ROS 2 commands.
- Record installation notes and issues.

## Phase 2: Install and Build PX4 SITL

- Clone PX4-Autopilot.
- Install required dependencies.
- Build the SITL target.
- Record build logs and troubleshooting notes.

## Phase 3: Start Gazebo X500 Simulation

- Launch the PX4 Gazebo X500 SITL simulation.
- Confirm simulator startup and vehicle state topics.
- Record baseline startup behavior.

## Phase 4: Run Official ROS 2 Offboard Demo

- Build px4_msgs and px4_ros_com.
- Start Micro XRCE-DDS Agent.
- Run the official Offboard control demo.
- Verify setpoint publishing and vehicle response.

## Phase 5: Implement Custom Trajectory Tracking Node

- Implement takeoff and hover commands.
- Implement square trajectory tracking.
- Implement circular trajectory tracking.
- Implement figure-eight trajectory tracking.
- Keep controller and trajectory parameters documented.

## Phase 6: Log Recording, Error Analysis, and Visualization

- Record rosbag2 topics and PX4 ULog files.
- Extract trajectory reference and vehicle state.
- Compute tracking error metrics.
- Generate plots and figures for analysis.

