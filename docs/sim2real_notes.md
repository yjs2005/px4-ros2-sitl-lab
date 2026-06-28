# Sim-to-Real Notes

This project currently focuses on simulation only. The items below are future considerations for understanding the gap between SITL, HITL, and real low-speed flight tests.

## Coordinate Frames

- PX4 commonly uses NED conventions.
- ROS commonly uses ENU conventions.
- Offboard commands must handle frame conversion carefully.

## Offboard Setpoint Frequency

- Offboard setpoints must be published continuously.
- Low or unstable setpoint frequency may trigger failsafe behavior.
- The target frequency should be documented and validated during experiments.

## Sensor Noise

- SITL sensor models may not fully represent real IMU, GPS, barometer, optical flow, or motion-capture noise.
- Future tests should introduce noise assumptions explicitly before comparing results.

## Execution Delay

- Real systems include communication, computation, actuator, and estimator delays.
- Delay can affect tracking stability and overshoot.
- Logs should include timestamps suitable for delay analysis.

## Failsafe

- Offboard loss and estimator failure behavior must be understood before any real-world test.
- Failsafe parameters should be reviewed in simulation first.

## Geofence

- Geofence settings should be considered before HITL or real-world testing.
- The allowed flight area should be conservative and easy to monitor.

## Manual Takeover

- Any future physical test would require a reliable manual takeover path.
- Pilot, RC link, kill switch, and emergency procedure checks must be completed before arming real hardware.

## Migration Path

1. Validate logic in SITL.
2. Move to HITL only after simulation behavior is stable and logged.
3. Perform any real vehicle test only as a low-speed, low-altitude, supervised test with manual takeover ready.

No real vehicle deployment has been completed in this repository.

