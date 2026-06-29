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

## 2026-06-28 Phase 3 Offboard Hover SITL Success

### Environment

- OS: Windows 11 host with WSL2 Ubuntu-22.04.
- PX4: `PX4-Autopilot` at `/home/yjs/src/PX4-Autopilot`.
- ROS 2: Humble.
- ROS 2 workspace: `/home/yjs/px4_ros2_ws`.
- Package: `px4_offboard_lab`.
- Vehicle: Gazebo X500 in PX4 SITL.

### Goal

- Verify ROS 2 Offboard takeoff, hover, land, and disarm in PX4 SITL.

### Control Flow

```text
setpoint warm-up -> arm -> OFFBOARD -> hover -> land -> disarm
```

### Target

- PX4 local NED target: `(x=0.0, y=0.0, z=-2.0)`.
- NED `z` is positive downward, so negative `z` means upward.

### Observations

- PX4 commander reported `Armed by external command`.
- PX4 commander reported `Takeoff detected`.
- ROS 2 node entered hover stage with `arming_state=2` and `nav_state=14`.
- Vehicle reached close to the target NED hover position `(0.0, 0.0, -2.0)`.
- Observed NED `z` converged to about `-1.97 m`.
- Node sent `Land command sent`.
- PX4 commander reported `Landing detected`.
- PX4 commander reported `Disarmed by landing`.
- Node printed `Offboard hover node sequence complete; shutting down`.

### Artifacts

- Committable lightweight CSV: `logs/offboard_hover_first_success.csv`.
- Local ULog artifact: `logs/ulg/offboard_hover_first_success.ulg`.
- ULog files under `logs/ulg/*.ulg` are ignored by default and are not intended for normal commits.

### Issues

- The first failed run was caused by missing GCS / preflight health checks and did not take off.
- The successful run required a QGroundControl connection or otherwise resolving the SITL preflight checks.

### Conclusion

- Phase 3 completed: ROS 2 Offboard hover in PX4 SITL verified.
- This result is simulation-only and not for real aircraft deployment.

### Next Step

- Preserve the CSV artifact, keep ULog local by default, and proceed to structured trajectory experiments only in SITL.

## 2026-06-29 Phase 4 Hover Analysis And Figure-Eight Node

### Environment

- OS: Windows 11 host with WSL2 Ubuntu-22.04.
- PX4: `PX4-Autopilot` at `/home/yjs/src/PX4-Autopilot`.
- ROS 2: Humble.
- ROS 2 workspace: `/home/yjs/px4_ros2_ws`.
- Package: `px4_offboard_lab`.
- Source CSV: `logs/offboard_hover_first_success.csv`.

### Goal

- Analyze the successful hover CSV and generate tracking metrics and figures.
- Implement a SITL-only figure-eight Offboard node without running a live figure-eight experiment.

### Commands

```bash
python3 analysis/analyze_offboard_hover.py
python3 -m py_compile ros2/px4_offboard_lab/px4_offboard_lab/offboard_hover.py
python3 -m py_compile ros2/px4_offboard_lab/px4_offboard_lab/offboard_figure8.py
cd ~/px4_ros2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash || true
colcon build --symlink-install
source install/setup.bash
ros2 pkg list | grep px4_offboard_lab
ros2 pkg executables px4_offboard_lab
```

### Hover Analysis Outputs

- `analysis/analyze_offboard_hover.py`
- `results/offboard_hover_metrics.json`
- `results/offboard_hover_metrics.md`
- `results/figures/offboard_hover_z.png`
- `results/figures/offboard_hover_xy.png`
- `results/figures/offboard_hover_ned_position.png`
- `results/figures/offboard_hover_velocity.png`

### Hover Metrics Summary

- Whole-run samples: `364`
- Whole-run duration: `18.150 s`
- Median control frequency estimate: `20.00 Hz`
- Hover samples: `241`
- Hover duration: `12.000 s`
- Final hover z error: `0.0124 m`
- Full hover-stage z RMSE: `1.0455 m`
- Full hover-stage z MAE: `0.6963 m`
- Full hover-stage max absolute z error: `2.0018 m`
- Full hover-stage XY RMSE: `0.0466 m`
- Full hover-stage max XY error: `0.1159 m`
- Full hover-stage max speed: `1.1084 m/s`

The full hover-stage z RMSE includes the climb/convergence portion of the CSV `hover` stage, so it is larger than the final settled error.

### Steady-State Hover Metrics

Steady-state hover is defined as samples where `stage == "hover"` and `z <= -1.8`, isolating the settled portion near the NED target altitude `z=-2.0`.

- Steady-state samples: `105`
- Steady-state duration: `5.200 s`
- Steady-state z RMSE: `0.0864 m`
- Steady-state z MAE: `0.0713 m`
- Steady-state max absolute z error: `0.1955 m`
- Steady-state XY RMSE: `0.0313 m`
- Steady-state max XY error: `0.0470 m`
- Steady-state final position error: `0.0327 m`
- Steady-state max speed: `0.0977 m/s`

### Figure-Eight Implementation

- Added `offboard_figure8` node under `ros2/px4_offboard_lab/px4_offboard_lab/offboard_figure8.py`.
- Added `offboard_figure8` console entry point.
- Added `scripts/run_figure8.sh`.
- Added `docs/trajectory_tracking.md`.
- Default figure-eight setpoint: `x(t)=1.0*sin(omega*t)`, `y(t)=0.6*sin(2*omega*t)`, `z=-2.0`, duration about `40 s`, publish rate `20 Hz`.

### Build Validation

```text
Summary: 3 packages finished
```

Package discovery:

```text
px4_offboard_lab
```

Executables:

```text
px4_offboard_lab offboard_figure8
px4_offboard_lab offboard_hover
```

### Issues

- No live figure-eight Offboard flight was run.
- The figure-eight node is implemented and build-verified only.

### Conclusion

- Phase 4 hover trajectory analysis completed.
- Figure-eight Offboard node implemented and available for a later SITL-only flight experiment.

### Next Step

- Run the figure-eight experiment manually in SITL after QGroundControl/preflight readiness, Agent, PX4 SITL Gazebo, and ROS 2 workspace sourcing are confirmed.

## 2026-06-29 Figure-Eight Offboard CSV Analysis

### Environment

- OS: Windows 11 host with WSL2 Ubuntu-22.04.
- PX4: `PX4-Autopilot` at `/home/yjs/src/PX4-Autopilot`.
- ROS 2: Humble.
- ROS 2 workspace: `/home/yjs/px4_ros2_ws`.
- Package: `px4_offboard_lab`.
- Source CSV: `logs/figure8_first_success.csv`.

### Goal

- Analyze the first copied figure-eight Offboard CSV without rerunning PX4, Gazebo, Micro XRCE-DDS Agent, or any Offboard node.

### Commands

```bash
python3 -m py_compile analysis/analyze_figure8.py
python3 analysis/analyze_figure8.py
```

### Tracking-Stage Filter

- Observed CSV stages: `warmup`, `arming`, `offboard`, `pre_figure8_hover`, `figure8`, `landing`.
- The tracking-stage filter is `stage == "figure8"`.
- The CSV contains a `landing` stage after figure-eight tracking.

### Outputs

- `analysis/analyze_figure8.py`
- `results/figure8_metrics.json`
- `results/figure8_metrics.md`
- `results/figures/figure8_xy_tracking.png`
- `results/figures/figure8_z_tracking.png`
- `results/figures/figure8_position_error.png`
- `results/figures/figure8_velocity.png`

### Metrics Summary

- Whole-run samples: `941`
- Whole-run duration: `50.800 s`
- Median logging/control frequency estimate: `20.00 Hz`
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

### Observations

- Figure-eight Offboard trajectory experiment completed in PX4 SITL for this CSV dataset.
- The node generated time-varying `target_x` and `target_y` setpoints.
- The vehicle entered the `figure8` tracking stage and the CSV ended with a `landing` stage.
- PX4 local position uses NED coordinates; negative `z` means upward.
- Hover tracking is fixed-point tracking, while figure-eight tracking is a moving setpoint trajectory.
- Both experiments use ROS 2 Offboard setpoints through PX4 `/fmu/in/...` topics.

### Issues

- No live experiment was rerun during this analysis.
- These results are simulation-only and not for real aircraft deployment.

### Conclusion

- Figure-eight CSV analysis completed and generated tracking metrics plus plots.

### Next Step

- Use the generated figures and metrics for comparison with later trajectory experiments, such as square or circular paths.

## 2026-06-29 Final Repository Packaging

### Environment

- OS: Windows 11 host with WSL2 Ubuntu-22.04.
- PX4: external checkout at `/home/yjs/src/PX4-Autopilot`.
- ROS 2 workspace: external workspace at `/home/yjs/px4_ros2_ws`.
- Repository: `D:\42系保研准备\px4-ros2-sitl-lab`.

### Goal

- Organize the project into a GitHub-ready open-source repository suitable for project display and resume reference.
- Keep only lightweight reproducible artifacts in the repository.
- Do not rerun PX4, Gazebo, Micro XRCE-DDS Agent, or Offboard flight experiments.

### Commands

```bash
python3 -m py_compile analysis/analyze_offboard_hover.py analysis/analyze_figure8.py analysis/generate_summary_visuals.py analysis/generate_gifs.py
python3 analysis/analyze_offboard_hover.py
python3 analysis/analyze_figure8.py
python3 analysis/generate_summary_visuals.py
python3 analysis/generate_gifs.py
```

### Outputs

- `results/summary_metrics.md`
- `results/summary_metrics.json`
- `results/summary_metrics.csv`
- `results/figures/metrics_summary.png`
- `results/project_pipeline.md`
- `media/figure8_tracking.gif`
- `media/README.md`
- `docs/reproducibility.md`
- `docs/project_structure.md`
- `scripts/analyze_all.sh`

### Final Project Status

- Phase 1 completed: PX4 SITL + Gazebo X500 started.
- Phase 2 completed: Micro XRCE-DDS Agent + PX4 + ROS 2 `/fmu` bridge verified.
- Phase 3 completed: Offboard hover takeoff, hover, land, and disarm verified in SITL.
- Phase 4 completed: hover tracking analysis, figure-eight node, figure-eight tracking analysis, metrics summaries, figures, and GIF visualization.

### Summary Metrics

- Hover steady-state z RMSE: `0.0864 m`.
- Hover steady-state XY RMSE: `0.0313 m`.
- Hover steady-state final position error: `0.0327 m`.
- Figure-eight XY RMSE: `0.2003 m`.
- Figure-eight z RMSE: `0.1944 m`.
- Figure-eight 3D position RMSE: `0.2791 m`.
- Figure-eight max 3D position error: `1.3506 m`.

### Artifact Policy

- Keep committed CSV logs:
  - `logs/offboard_hover_first_success.csv`
  - `logs/figure8_first_success.csv`
- Keep committed lightweight outputs:
  - `results/*.md`
  - `results/*.json`
  - `results/*.csv`
  - `results/figures/*.png`
  - `media/*.gif`
- Keep PX4 ULog files local by default:
  - `logs/ulg/*.ulg`
- Ignore caches, ROS build outputs, local IDE settings, and large binary media.

### Conclusion

- Final repository packaging completed for a lightweight GitHub presentation workflow.
- The project is still simulation-only and not for real aircraft deployment.
