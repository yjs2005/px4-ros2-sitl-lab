# Troubleshooting

## Template

### Problem Description

- 

### Error Message

```text

```

### Attempts

- 

### Final Solution

- 

### Related Environment

- OS:
- ROS 2:
- PX4:
- Gazebo:
- Command:

## PX4-Autopilot Clone From GitHub Times Out In WSL

### Problem Description

- WSL2 Ubuntu-22.04 is installed and usable, but PX4-Autopilot cannot be cloned reliably from GitHub.
- Earlier normal clone and shallow recursive clone attempts were slow or failed with an unexpected disconnect.
- The retry used a lighter partial clone after reducing Git parallelism and compression.

### Error Message

```text
fatal: unable to access 'https://github.com/PX4/PX4-Autopilot.git/': Failed to connect to github.com port 443 after 134774 ms: Connection timed out
```

### Attempts

- Removed possible incomplete checkout: `rm -rf ~/src/PX4-Autopilot`.
- Set Git to HTTP/1.1: `git config --global http.version HTTP/1.1`.
- Disabled Git compression: `git config --global core.compression 0`.
- Limited submodule fetch concurrency: `git config --global submodule.fetchJobs 1`.
- Retried with `--depth 1 --filter=blob:none --recurse-submodules --shallow-submodules`.

### Proxy Finding

- Windows user proxy is enabled at `127.0.0.1:7890`.
- WinHTTP proxy is direct access.
- WSL has no proxy environment variables and no Git proxy configured.
- WSL prints a `localhost` proxy warning at startup, indicating the Windows localhost proxy may not be available inside WSL NAT mode.

### Final Solution

- Not resolved in this attempt. No system proxy was changed.
- Next recommended action: configure a WSL-accessible proxy, or switch to a network with stable GitHub access, then retry the lightweight clone.

### Related Environment

- OS: Windows 11 + WSL2 Ubuntu-22.04
- ROS 2: not installed
- PX4: not cloned
- Gazebo: not installed
- Command: `git clone --depth 1 --filter=blob:none --recurse-submodules --shallow-submodules https://github.com/PX4/PX4-Autopilot.git`

## PX4 SITL Phase 1 Non-Blocking Warnings

### Problem Description

- PX4 SITL + Gazebo X500 now launches successfully, but PX4 still prints preflight and power warnings.
- These warnings do not block the Phase 1 goal because the simulator starts, Gazebo opens, `x500_0` appears, and PX4 reaches the `pxh>` prompt.

### Error Message

```text
Preflight Fail: No connection to the GCS
system power unavailable
```

### Attempts

- No fix attempted during Phase 1.
- The warnings are deferred to the QGroundControl / Offboard integration phase.

### Final Solution

- Not treated as a blocking problem for Phase 1.
- Revisit after QGroundControl and ROS 2 Offboard components are introduced.

### Related Environment

- OS: Windows 11 + WSL2 Ubuntu-22.04
- ROS 2: not installed
- PX4: cloned at `/home/yjs/src/PX4-Autopilot`
- Gazebo: Harmonic, installed through `bash ./Tools/setup/ubuntu.sh`
- Command: `make px4_sitl gz_x500`

## Phase 2 Non-Blocking Notes

### Problem Description

- PX4-to-ROS 2 communication is verified, but several notes should be kept for repeatability.
- These are not blockers for Phase 2.

### Messages

```text
BrokenPipeError: [Errno 32] Broken pipe
ros2: command not found
Preflight Fail: No connection to the GCS
system power unavailable
```

### Attempts

- `BrokenPipeError` appeared when piping `ros2 interface list | grep px4_msgs | head`; this happens because `head` exits early.
- In a non-interactive WSL script, `source ~/.bashrc` did not expose `ros2`.
- Explicit source commands worked:

```bash
source /opt/ros/humble/setup.bash
source ~/px4_ros2_ws/install/setup.bash
```

### Final Solution

- Do not treat the `head` pipeline `BrokenPipeError` as a build or interface error.
- For scripted checks, source ROS 2 and the workspace setup files explicitly instead of relying only on `~/.bashrc`.
- Keep the GCS and power warnings as later QGroundControl / Offboard phase items.

### Related Environment

- OS: Windows 11 + WSL2 Ubuntu-22.04
- ROS 2: Humble
- PX4: cloned at `/home/yjs/src/PX4-Autopilot`
- Gazebo: Harmonic
- Agent: `MicroXRCEAgent udp4 -p 8888`
- Command: `ros2 topic echo /fmu/out/vehicle_odometry --once`

## Phase 3 Offboard Hover Common Issues

### Offboard Mode Does Not Engage

- Check that `/fmu/in/offboard_control_mode` and `/fmu/in/trajectory_setpoint` are published before sending the OFFBOARD command.
- PX4 requires continuous setpoints before and during Offboard mode.
- Keep setpoint publish rate at 10 Hz or higher; this package defaults to 20 Hz.

### No `/fmu/out/vehicle_odometry`

- Confirm Micro XRCE-DDS Agent is running:

```bash
MicroXRCEAgent udp4 -p 8888
```

- Confirm PX4 SITL is running and the Agent session is established.
- Confirm the ROS 2 workspace is sourced:

```bash
source /opt/ros/humble/setup.bash
source ~/px4_ros2_ws/install/setup.bash
ros2 topic list | grep fmu
```

### Agent Does Not Connect

- Start Agent before PX4 SITL when possible.
- Check `/tmp/px4_agent.log` for `session established`.
- Check PX4 log for `uxrce_dds_client` using UDP `127.0.0.1:8888`.

### NED `z` Direction Is Reversed

- PX4 local setpoints use NED: North, East, Down.
- Positive `z` moves downward.
- Negative `z` moves upward.
- The default hover target is `z=-2.0`, meaning about 2 meters up from the local origin.

### Failsafe From Low Setpoint Rate

- Offboard control can fail if setpoint publication drops below PX4's required rate.
- Use a fixed timer at 20 Hz and avoid blocking work inside the timer callback.
- Do not run heavy logging, plotting, or shell commands inside the control loop.

### Vehicle Status Topic Has A Version Suffix

- Current Phase 2 topic discovery observed `/fmu/out/vehicle_status_v4`.
- The node subscribes to both `/fmu/out/vehicle_status` and `/fmu/out/vehicle_status_v4` for compatibility.

### Real-Aircraft Safety

- This package is simulation-only and not for real aircraft.
- Do not connect the node to a physical vehicle.
- Actual flight validation must be deliberately run in PX4 SITL after Agent, PX4, Gazebo, and ROS 2 topics are verified.

## Phase 3 First Failed Run: Preflight / GCS Not Ready

### Problem Description

- The first Offboard hover attempt did not take off.
- PX4 preflight health checks were not satisfied, including the missing GCS condition.

### Error Message

```text
Preflight Fail: No connection to the GCS
```

### Attempts

- Verified that the Offboard node was publishing the expected `/fmu/in/...` setpoints and commands.
- Checked PX4 commander output for arming, takeoff, landing, and disarm state changes.
- Resolved SITL preflight readiness by using a QGroundControl connection or otherwise satisfying the relevant SITL preflight checks.

### Final Solution

- The successful run completed after the preflight/GCS issue was resolved.
- PX4 commander reported `Armed by external command`, `Takeoff detected`, `Landing detected`, and `Disarmed by landing`.
- The node reached hover with `arming_state=2`, `nav_state=14`, converged to about `z=-1.97 m`, sent land, and shut down cleanly.

### Related Environment

- OS: Windows 11 + WSL2 Ubuntu-22.04
- ROS 2: Humble
- PX4: `/home/yjs/src/PX4-Autopilot`
- Gazebo: X500 SITL
- Agent: `MicroXRCEAgent udp4 -p 8888`
- Node: `ros2 run px4_offboard_lab offboard_hover`
