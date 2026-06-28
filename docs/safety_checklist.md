# Safety Checklist

## Simulation Stage

- Confirm this repository is being used for simulation only.
- Confirm PX4 SITL starts without critical errors.
- Confirm Gazebo vehicle model loads correctly.
- Confirm Offboard setpoints are published at a stable rate.
- Confirm failsafe behavior is understood before testing custom nodes.
- Confirm logs are recorded for each experiment.
- Confirm experiment parameters are written in `notes/experiment_log.md`.

## Future Real-World Safety Checks

These items are for future planning only. This repository currently does not perform real vehicle flight.

- Verify airframe, propellers, battery, sensors, and wiring.
- Verify RC link, manual mode, and kill switch.
- Verify geofence and failsafe parameters.
- Verify local regulations and test site safety.
- Keep the first real test low-speed, low-altitude, and supervised.
- Keep a trained pilot ready for manual takeover.
- Do not arm real hardware unless the full safety procedure has been reviewed.

## Current Scope

The current project scope is PX4 SITL + Gazebo + ROS 2 simulation. It does not include real aircraft flight.

