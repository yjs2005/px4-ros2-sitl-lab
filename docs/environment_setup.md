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

- ROS 2 Humble: verified installed at `/opt/ros/humble/bin/ros2`
- PX4-Autopilot: verified cloned at `/home/yjs/src/PX4-Autopilot`
- PX4 Gazebo dependencies: verified installed with `bash ./Tools/setup/ubuntu.sh`
- Micro XRCE-DDS Agent: verified available as `MicroXRCEAgent`
- px4_msgs: verified cloned and built in `/home/yjs/px4_ros2_ws`
- px4_ros_com: verified cloned and built in `/home/yjs/px4_ros2_ws`

## Planned Check Commands

```bash
make px4_sitl gz_x500
ros2 topic list | grep fmu
```

Verification status:

- `make px4_sitl gz_x500`: verified successful.
- `ros2 topic list | grep fmu`: verified successful.
- `ros2 topic echo /fmu/out/vehicle_odometry --once`: verified successful.

## Current Local Environment Check

See [../notes/local_environment_report.md](../notes/local_environment_report.md).

The current repository records that PX4 SITL + Gazebo X500 and the PX4-to-ROS 2 topic bridge have been verified. It does not claim that custom Offboard control has already been written or run successfully.

## 2026-06-28 WSL Status And PX4 Clone Note

- WSL2 Ubuntu-22.04 is available and can access `/home/yjs/src/px4-ros2-sitl-lab`.
- Basic Ubuntu tools are present, including Git `2.34.1`.
- ROS 2, PX4 setup scripts, and PX4 compilation were intentionally not run during this check.
- `PX4-Autopilot` cloning from GitHub is currently unreliable. Previous normal clone and shallow clone attempts failed, and the latest lightweight clone timed out while connecting to `github.com:443`.
- Windows user proxy is enabled as `127.0.0.1:7890`, but WSL has no proxy environment variables or Git proxy configured. WSL also prints a `localhost` proxy warning, so the Windows localhost proxy may not be synchronized into WSL NAT mode.
- Recommended next step: configure a WSL-accessible proxy or switch to a more stable network before retrying PX4-Autopilot clone.

## Verified Phase 1 Setup

- WSL2 Ubuntu-22.04 is available.
- `PX4-Autopilot` has been cloned successfully at `/home/yjs/src/PX4-Autopilot`.
- `bash ./Tools/setup/ubuntu.sh` completed and installed PX4 dependencies, including Gazebo Harmonic.
- `make px4_sitl gz_x500` launched PX4 SITL successfully.
- Gazebo Sim opened and displayed the `x500_0` quadrotor.
- PX4 reached the `pxh>` prompt and reported that the startup script returned successfully.
- PX4 ULog was generated at `./log/2026-06-28/12_55_55.ulg`.
- Current warnings `Preflight Fail: No connection to the GCS` and `system power unavailable` are deferred to later QGroundControl / Offboard work.

## Verified Phase 2 Communication

- Phase 2 completed: PX4 SITL, Gazebo, Micro XRCE-DDS Agent, and ROS 2 topic bridge verified.
- ROS 2 Humble is available at `/opt/ros/humble/bin/ros2`.
- Micro XRCE-DDS Agent was started with `MicroXRCEAgent udp4 -p 8888`.
- PX4 SITL was started from `/home/yjs/src/PX4-Autopilot` with `make px4_sitl gz_x500`.
- Agent log path: `/tmp/px4_agent.log`.
- PX4 SITL log path: `/tmp/px4_sitl.log`.
- ROS 2 topic capture path: `/tmp/px4_topics.txt`.
- ROS 2 odometry capture path: `/tmp/px4_odometry_once.txt`.
- Agent log confirmed `session established`.
- PX4 log confirmed `Gazebo world is ready`, `Spawning Gazebo model`, `world: default, model: x500_0`, and `uxrce_dds_client` using UDP `127.0.0.1:8888`.
- ROS 2 observed both `/fmu/in/...` and `/fmu/out/...` topics, including `/fmu/in/trajectory_setpoint`, `/fmu/in/offboard_control_mode`, `/fmu/out/vehicle_odometry`, and `/fmu/out/vehicle_status_v4`.
- A single `/fmu/out/vehicle_odometry` message was read successfully with `ros2 topic echo /fmu/out/vehicle_odometry --once`.
- In non-interactive WSL commands, explicitly sourcing `/opt/ros/humble/setup.bash` and `~/px4_ros2_ws/install/setup.bash` was required for `ros2` to be available.
