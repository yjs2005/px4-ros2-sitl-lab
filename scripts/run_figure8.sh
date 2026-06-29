#!/usr/bin/env bash
set -euo pipefail

cat <<'MSG'
PX4 Offboard figure-eight runner (SITL only).

Before continuing, confirm:
  1. QGroundControl is open, or SITL preflight checks are otherwise resolved.
  2. MicroXRCEAgent is running:
     MicroXRCEAgent udp4 -p 8888
  3. PX4 SITL Gazebo is running:
     cd ~/src/PX4-Autopilot && make px4_sitl gz_x500
  4. The ROS 2 workspace has been built and can be sourced.

This script only sources ROS 2 and runs the offboard_figure8 node.
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

ros2 run px4_offboard_lab offboard_figure8 "$@"
