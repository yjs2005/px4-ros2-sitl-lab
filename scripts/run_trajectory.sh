#!/usr/bin/env bash
set -euo pipefail

trajectory="${1:-}"
controller_mode="${2:-baseline}"

if [[ -z "${trajectory}" ]]; then
  cat <<'MSG'
Usage:
  bash scripts/run_trajectory.sh hover baseline
  bash scripts/run_trajectory.sh line baseline
  bash scripts/run_trajectory.sh line smooth
  bash scripts/run_trajectory.sh square baseline
  bash scripts/run_trajectory.sh square smooth
  bash scripts/run_trajectory.sh circle baseline
  bash scripts/run_trajectory.sh circle feedforward
  bash scripts/run_trajectory.sh figure8 baseline
  bash scripts/run_trajectory.sh figure8 feedforward
  bash scripts/run_trajectory.sh z_step baseline
  bash scripts/run_trajectory.sh z_step smooth
MSG
  exit 1
fi

case "${trajectory}" in
  hover|line|square|circle|figure8|z_step)
    ;;
  *)
    echo "Unsupported trajectory: ${trajectory}"
    echo "Choose one of: hover, line, square, circle, figure8, z_step"
    exit 1
    ;;
esac

case "${controller_mode}" in
  baseline|feedforward|smooth)
    ;;
  *)
    echo "Unsupported controller mode: ${controller_mode}"
    echo "Choose one of: baseline, feedforward, smooth"
    exit 1
    ;;
esac

cat <<MSG
PX4 Offboard trajectory runner (SITL only).

Selected trajectory: ${trajectory}
Selected controller mode: ${controller_mode}

Before continuing, confirm:
  1. QGroundControl is open, or SITL preflight checks are otherwise resolved.
  2. Terminal 1 is running:
     MicroXRCEAgent udp4 -p 8888
  3. Terminal 2 is running:
     cd ~/src/PX4-Autopilot && make px4_sitl gz_x500
  4. This terminal can source the ROS 2 workspace.

This script only sources ROS 2 and runs the offboard_trajectory node.
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

ros2 run px4_offboard_lab offboard_trajectory --ros-args \
  -p trajectory:="${trajectory}" \
  -p controller_mode:="${controller_mode}"
