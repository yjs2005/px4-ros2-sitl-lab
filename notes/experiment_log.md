# Experiment Log

## Template

### Date

- 

### Environment

- OS:
- ROS 2:
- PX4:
- Gazebo:
- Branch / commit:

### Goal

- 

### Commands

```bash

```

### Observations

- 

### Issues

- 

### Conclusion

- 

### Next Step

- 

## 2026-06-28 WSL PX4 Clone Attempt

### Environment

- Windows 11 host with WSL2 Ubuntu-22.04.
- WSL project path is available at `/home/yjs/src/px4-ros2-sitl-lab`.
- WSL check passed: `~/src` exists, memory is about 9.7 GiB, swap is 8.0 GiB, root filesystem has about 954 GiB available, and Git is `2.34.1`.
- No ROS 2 installation, PX4 setup script, or PX4 build was run.

### Goal

- Clean any incomplete `PX4-Autopilot` checkout and retry a lighter PX4 clone from GitHub.

### Commands

```bash
wsl -d Ubuntu-22.04 -- bash -lc "cd ~/src && pwd && ls -la"
wsl -d Ubuntu-22.04 -- bash -lc "free -h && df -h && git --version"
wsl -d Ubuntu-22.04 -- bash -lc "rm -rf ~/src/PX4-Autopilot"
wsl -d Ubuntu-22.04 -- bash -lc "git config --global http.version HTTP/1.1"
wsl -d Ubuntu-22.04 -- bash -lc "git config --global core.compression 0"
wsl -d Ubuntu-22.04 -- bash -lc "git config --global submodule.fetchJobs 1"
wsl -d Ubuntu-22.04 -- bash -lc "cd ~/src && git clone --depth 1 --filter=blob:none --recurse-submodules --shallow-submodules https://github.com/PX4/PX4-Autopilot.git"
```

### Observations

- WSL Ubuntu-22.04 is usable.
- Windows user proxy is enabled as `127.0.0.1:7890`, while WinHTTP is direct access.
- WSL has no `http_proxy` or `https_proxy` environment variables and no Git proxy configured.
- WSL startup prints a `localhost` proxy related warning, which suggests the Windows localhost proxy is not automatically usable from WSL NAT mode.

### Issues

- Previous normal clone and shallow clone attempts from GitHub failed.
- The lighter clone also failed before downloading repository data:

```text
fatal: unable to access 'https://github.com/PX4/PX4-Autopilot.git/': Failed to connect to github.com port 443 after 134774 ms: Connection timed out
```

### Conclusion

- PX4-Autopilot cloning from GitHub remains blocked by network connectivity or proxy routing, not by local WSL storage or basic tools.
- Likely causes are unstable GitHub connectivity and WSL not inheriting the Windows localhost proxy.

### Next Step

- Configure a WSL-accessible proxy explicitly, or retry from a different network, then rerun the lightweight clone.

## 2026-06-28 PX4 SITL Gazebo X500 Phase 1 Verification

### Environment

- OS: Windows 11 host with WSL2 Ubuntu-22.04.
- PX4: `PX4-Autopilot` cloned at `/home/yjs/src/PX4-Autopilot`.
- Gazebo: Gazebo Harmonic installed through the PX4 Ubuntu setup script.
- ROS 2: not installed in this phase.

### Goal

- Verify that PX4 SITL can launch the Gazebo X500 simulation.

### Commands

```bash
cd /home/yjs/src/PX4-Autopilot
bash ./Tools/setup/ubuntu.sh
make px4_sitl gz_x500
```

### Observations

- PX4 SITL started successfully with Gazebo Sim.
- Gazebo Sim window opened and the `x500_0` quadrotor appeared in the scene.
- PX4 startup completed and the terminal reached the `pxh>` prompt.
- PX4 reported that the startup script returned successfully.
- ULog was generated at `./log/2026-06-28/12_55_55.ulg`.

### Issues

- Current warnings:
  - `Preflight Fail: No connection to the GCS`
  - `system power unavailable`
- These warnings are recorded for the later QGroundControl / Offboard phase and are not considered blockers for Phase 1.

### Conclusion

- Phase 1 completed: PX4 SITL + Gazebo X500 launched successfully.

### Next Step

- Continue with QGroundControl, ROS 2, and Offboard integration in later phases.

## 2026-06-28 PX4 ROS 2 Topic Bridge Phase 2 Verification

### Environment

- OS: Windows 11 host with WSL2 Ubuntu-22.04.
- PX4: `PX4-Autopilot` at `/home/yjs/src/PX4-Autopilot`.
- ROS 2: Humble at `/opt/ros/humble/bin/ros2`.
- ROS 2 workspace: `/home/yjs/px4_ros2_ws`.
- Packages: `px4_msgs` and `px4_ros_com` built with `colcon build --symlink-install`.
- Agent: `MicroXRCEAgent` available from source install.

### Goal

- Verify that PX4 SITL, Gazebo, Micro XRCE-DDS Agent, and ROS 2 can communicate through the `/fmu/...` topic bridge.

### Commands

```bash
MicroXRCEAgent udp4 -p 8888
cd /home/yjs/src/PX4-Autopilot
make px4_sitl gz_x500
source /opt/ros/humble/setup.bash
source /home/yjs/px4_ros2_ws/install/setup.bash
ros2 topic list | grep fmu
timeout 10 ros2 topic echo /fmu/out/vehicle_odometry --once
```

### Logs And Result Files

- Agent log: `/tmp/px4_agent.log`.
- PX4 SITL log: `/tmp/px4_sitl.log`.
- ROS 2 topic capture: `/tmp/px4_topics.txt`.
- ROS 2 odometry capture: `/tmp/px4_odometry_once.txt`.

### Observations

- Micro XRCE-DDS Agent started on UDP port `8888`.
- Agent log showed `session established` and DDS entities being created.
- PX4 SITL launched Gazebo X500 again.
- PX4 log showed `Gazebo world is ready`, `Spawning Gazebo model`, `world: default, model: x500_0`, and `uxrce_dds_client` connecting to `127.0.0.1:8888`.
- ROS 2 topic list showed `/fmu/in/...` and `/fmu/out/...` topics.
- Observed input topics include `/fmu/in/offboard_control_mode`, `/fmu/in/trajectory_setpoint`, and `/fmu/in/vehicle_command`.
- Observed output topics include `/fmu/out/vehicle_odometry`, `/fmu/out/vehicle_status_v4`, and `/fmu/out/vehicle_local_position_v1`.
- One `/fmu/out/vehicle_odometry` message was read successfully. The captured message included timestamp `1782654529684813`, position values, orientation quaternion, velocity, variances, and `quality: 0`.

### Issues

- `source ~/.bashrc` did not expose `ros2` inside the non-interactive WSL script. Explicitly sourcing `/opt/ros/humble/setup.bash` and `~/px4_ros2_ws/install/setup.bash` worked.
- `ros2 interface list | grep px4_msgs | head` can print `BrokenPipeError` because `head` closes the pipe early. This is not treated as a ROS 2 or `px4_msgs` failure.
- `Preflight Fail: No connection to the GCS` and `system power unavailable` remain deferred to later QGroundControl / Offboard work.

### Conclusion

- Phase 2 completed: PX4 SITL, Gazebo, Micro XRCE-DDS Agent, and ROS 2 topic bridge verified.

### Next Step

- Proceed to QGroundControl / Offboard validation before writing custom trajectory control code.

## 2026-06-28 Phase 3 Offboard Hover Code Implementation

### Environment

- OS: Windows 11 host with WSL2 Ubuntu-22.04.
- PX4: `PX4-Autopilot` at `/home/yjs/src/PX4-Autopilot`.
- ROS 2: Humble.
- ROS 2 workspace: `/home/yjs/px4_ros2_ws`.
- Existing bridge packages: `px4_msgs` and `px4_ros_com`.

### Goal

- Create a simulation-only ROS 2 Python package for PX4 Offboard takeoff, hover, CSV logging, and landing-stage handoff.

### Commands

```bash
cd ~/px4_ros2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
colcon build --symlink-install
source install/setup.bash
ros2 pkg list | grep px4_offboard_lab
```

### Observations

- Package source was added under `ros2/px4_offboard_lab/` in this repository.
- The package is intended to be copied to `~/px4_ros2_ws/src/px4_offboard_lab` for build and SITL-only execution.
- Node name: `offboard_hover`.
- Default target is PX4 NED `(x=0.0, y=0.0, z=-2.0)`.
- The node publishes setpoints at 20 Hz and sends warm-up setpoints before requesting arm and OFFBOARD mode.
- CSV logs are written under `~/px4_ros2_ws/logs/` by default.

### Issues

- No Offboard flight test was run in this phase.
- This entry records code implementation and build validation only, not flight success.

### Build Validation

```text
Starting >>> px4_msgs
Finished <<< px4_msgs
Starting >>> px4_offboard_lab
Starting >>> px4_ros_com
Finished <<< px4_ros_com
Finished <<< px4_offboard_lab
Summary: 3 packages finished
```

Package discovery:

```text
px4_offboard_lab
```

### Conclusion

- Phase 3 Offboard hover code implementation and build validation completed.
- No Offboard flight test was run, so this is not a flight-success record.

### Next Step

- Run the hover node deliberately in PX4 SITL only after starting Micro XRCE-DDS Agent, PX4 SITL Gazebo, and sourcing the ROS 2 workspace.
