# Environment Setup

## Recommended Environment

- Ubuntu 22.04
- ROS 2 Humble
- PX4 SITL
- Gazebo

## Recommended Hardware

- 16 GB RAM or more
- More than 50 GB free disk space
- Dedicated GPU recommended for smoother Gazebo rendering

## Planned Installation Items

- ROS 2 Humble
- PX4-Autopilot
- Micro XRCE-DDS Agent
- px4_msgs
- px4_ros_com

## Planned Check Commands

```bash
make px4_sitl gz_x500
ros2 topic list | grep fmu
```

## Current Local Environment Check

See [../notes/local_environment_report.md](../notes/local_environment_report.md).

The current repository only records the local environment status. It does not claim that PX4 SITL, Gazebo, or ROS 2 Humble has already been installed or run successfully.

