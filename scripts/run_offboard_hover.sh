#!/usr/bin/env bash
set -euo pipefail

cat <<'MSG'
PX4 Offboard hover runner (SITL only).

Before continuing, start these in separate terminals:
  1. QGroundControl is open, or SITL preflight checks are otherwise resolved.
  2. MicroXRCEAgent udp4 -p 8888
  3. cd ~/src/PX4-Autopilot && make px4_sitl gz_x500
  4. Keep Gazebo and PX4 running until the hover node exits.

This script only sources ROS 2 and runs the offboard_hover node.
It does not start PX4, does not start Gazebo, and does not kill processes.
MSG

read -r -p "Continue only if this is PX4 SITL, not a real aircraft [y/N]: " answer
case "${answer}" in
  y|Y|yes|YES)
    ;;
  *)
    echo "Aborted."
    exit 1
    ;;
esac

source /opt/ros/humble/setup.bash
source "${HOME}/px4_ros2_ws/install/setup.bash"

if ! ros2 pkg list | grep -qx "px4_offboard_lab"; then
  echo "px4_offboard_lab is not built in ${HOME}/px4_ros2_ws."
  echo "Run: cd ~/px4_ros2_ws && colcon build --symlink-install"
  exit 1
fi

ros2 run px4_offboard_lab offboard_hover "$@"
