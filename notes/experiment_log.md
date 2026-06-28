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
