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
- PX4-Autopilot: verified cloned at `/home/yjs/src/PX4-Autopilot`
- PX4 Gazebo dependencies: verified installed with `bash ./Tools/setup/ubuntu.sh`
- Micro XRCE-DDS Agent
- px4_msgs
- px4_ros_com

## Planned Check Commands

```bash
make px4_sitl gz_x500
ros2 topic list | grep fmu
```

Verification status:

- `make px4_sitl gz_x500`: verified successful.
- `ros2 topic list | grep fmu`: not verified; ROS 2 is not installed yet.

## Current Local Environment Check

See [../notes/local_environment_report.md](../notes/local_environment_report.md).

The current repository records that PX4 SITL + Gazebo X500 has been verified. It does not claim that ROS 2 Humble or Offboard control has already been installed or run successfully.

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
