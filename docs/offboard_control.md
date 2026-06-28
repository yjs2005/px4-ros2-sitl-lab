# Offboard Control

This document describes the Phase 3 Offboard hover node for PX4 SITL. It is simulation-only and must not be used on a real aircraft.

Phase 3 is now verified in PX4 SITL: ROS 2 Offboard hover reached the target NED hover point and completed the land/disarm sequence.

## Control Flow

The `px4_offboard_lab` package provides a Python node named `offboard_hover`.

The node:

1. Publishes `/fmu/in/offboard_control_mode`.
2. Publishes `/fmu/in/trajectory_setpoint`.
3. Sends warm-up setpoints before changing flight mode.
4. Sends an arm command on `/fmu/in/vehicle_command`.
5. Sends an OFFBOARD mode command on `/fmu/in/vehicle_command`.
6. Holds a local NED target of `x=0.0`, `y=0.0`, `z=-2.0` for about 12 seconds.
7. Sends a land command and exits after the landing stage starts.

The default publish rate is 20 Hz. PX4 Offboard control requires a continuous setpoint stream; the rate must stay above 10 Hz.

## Topic Direction

PX4 uXRCE-DDS topics are named from the flight controller perspective:

- `/fmu/in/...` topics are inputs to PX4. The ROS 2 node publishes commands and setpoints here.
- `/fmu/out/...` topics are outputs from PX4. The ROS 2 node subscribes to vehicle state here.

This node publishes:

- `/fmu/in/offboard_control_mode`
- `/fmu/in/trajectory_setpoint`
- `/fmu/in/vehicle_command`

This node subscribes:

- `/fmu/out/vehicle_status`
- `/fmu/out/vehicle_status_v4` as a compatibility topic for the currently observed PX4 bridge
- `/fmu/out/vehicle_odometry`

## NED Coordinates

PX4 local position setpoints use the NED frame:

- `x`: North
- `y`: East
- `z`: Down

Because `z` points down, a negative `z` command means the vehicle should move upward. The default hover target is:

```text
x = 0.0
y = 0.0
z = -2.0
```

This means hover about 2 meters above the local origin.

## Why Warm-Up Setpoints Are Required

PX4 rejects or fails out of Offboard mode if it does not receive a stable stream of Offboard setpoints. The node therefore publishes setpoints for a warm-up period before sending arm and OFFBOARD commands.

The sequence is:

```text
setpoint warm-up -> arm -> OFFBOARD -> hover -> land -> disarm
```

This avoids switching to OFFBOARD before PX4 has received valid control input.

## Verified SITL Result

Target position:

```text
PX4 NED: x = 0.0, y = 0.0, z = -2.0
```

Observed result:

- PX4 commander reported `Armed by external command`.
- PX4 commander reported `Takeoff detected`.
- ROS 2 node entered hover stage with `arming_state=2` and `nav_state=14`.
- Vehicle reached close to the target hover point.
- Observed NED `z` converged to about `-1.97 m`.
- Node sent `Land command sent`.
- PX4 commander reported `Landing detected`.
- PX4 commander reported `Disarmed by landing`.
- Node printed `Offboard hover node sequence complete; shutting down`.

The first failed run did not take off because PX4 preflight health checks were not satisfied, including the missing GCS condition. The successful run required a QGroundControl connection or otherwise resolving the SITL preflight checks before Offboard takeoff.

## CSV Logging

The node writes a CSV log under `~/px4_ros2_ws/logs/` by default. Fields:

- `timestamp`
- `arming_state`
- `nav_state`
- `x`, `y`, `z`
- `vx`, `vy`, `vz`
- `target_x`, `target_y`, `target_z`
- `stage`

The first successful hover CSV has been copied into this repository:

```text
logs/offboard_hover_first_success.csv
```

The corresponding ULog was copied locally:

```text
logs/ulg/offboard_hover_first_success.ulg
```

The ULog is a local binary artifact only. `logs/ulg/*.ulg` is ignored by default and should not be committed unless intentionally curated.

## Run Conditions

Only run this node in SITL after these processes are already running:

```bash
MicroXRCEAgent udp4 -p 8888
cd ~/src/PX4-Autopilot && make px4_sitl gz_x500
source /opt/ros/humble/setup.bash
source ~/px4_ros2_ws/install/setup.bash
```

Then run:

```bash
ros2 run px4_offboard_lab offboard_hover
```

For a command-free rehearsal:

```bash
ros2 run px4_offboard_lab offboard_hover --dry-run
```

Phase 3 hover has been verified in PX4 SITL. This does not imply real-aircraft readiness.
