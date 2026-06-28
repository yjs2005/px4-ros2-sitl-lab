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
