# px4-ros2-sitl-lab

This repository is a research-oriented scaffold for quadrotor simulation trajectory tracking and log analysis based on PX4 SITL, Gazebo, and ROS 2 Offboard control.

Current status: Phase 1 completed: PX4 SITL + Gazebo X500 launched successfully.

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
2. Run the official PX4 ROS 2 Offboard demo
3. Implement custom trajectory nodes
4. Record logs with rosbag2 and PX4 ULog
5. Visualize tracking errors
6. Organize README, results, and experiment notes

## Notes

PX4-Autopilot is kept outside this repository at `/home/yjs/src/PX4-Autopilot`. ROS 2 and Offboard control have not been installed or verified yet.
