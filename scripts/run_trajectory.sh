#!/usr/bin/env bash
set -eo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

TRAJECTORY="${1:-circle}"
CONTROLLER_MODE="${2:-baseline}"

case "${TRAJECTORY}" in
  hover|line|square|circle|figure8|z_step)
    ;;
  *)
    echo "Unsupported trajectory: ${TRAJECTORY}"
    echo "Choose one of: hover, line, square, circle, figure8, z_step"
    exit 1
    ;;
esac

case "${CONTROLLER_MODE}" in
  baseline|feedforward|smooth)
    ;;
  *)
    echo "Unsupported controller mode: ${CONTROLLER_MODE}"
    echo "Choose one of: baseline, feedforward, smooth"
    exit 1
    ;;
esac

cat <<MSG
PX4 Offboard trajectory runner (SITL only).

Selected trajectory: ${TRAJECTORY}
Selected controller mode: ${CONTROLLER_MODE}
CSV log directory: ${PROJECT_ROOT}/logs

Prerequisites:
  1. QGroundControl should be open.
  2. MicroXRCEAgent should be running:
     MicroXRCEAgent udp4 -p 8888
  3. PX4 SITL should be running:
     cd ~/src/PX4-Autopilot && make px4_sitl gz_x500

This script only runs the ROS 2 trajectory node.
It does not start PX4, Gazebo, or Agent.
It does not kill processes, delete files, reset anything, or modify PX4 parameters.
MSG

if [[ -f /opt/ros/humble/setup.bash ]]; then
  source /opt/ros/humble/setup.bash
fi

if [[ -f "${HOME}/px4_ros2_ws/install/setup.bash" ]]; then
  source "${HOME}/px4_ros2_ws/install/setup.bash"
fi

if ! command -v ros2 >/dev/null 2>&1; then
  echo "ros2 is not available. Source ROS 2 first, for example:"
  echo "  source /opt/ros/humble/setup.bash"
  exit 1
fi

if ! ros2 pkg list | grep -qx "px4_offboard_lab"; then
  echo "px4_offboard_lab is not available."
  echo "Build it first:"
  echo "  cd ~/px4_ros2_ws && colcon build --symlink-install"
  exit 1
fi

if ! ros2 pkg executables px4_offboard_lab | awk '{print $2}' | grep -qx "offboard_trajectory"; then
  echo "offboard_trajectory executable is not available."
  echo "Build it first:"
  echo "  cd ~/px4_ros2_ws && colcon build --symlink-install"
  exit 1
fi

set +e
ros2 run px4_offboard_lab offboard_trajectory --ros-args \
  -p trajectory:="${TRAJECTORY}" \
  -p controller_mode:="${CONTROLLER_MODE}" \
  -p log_dir:="${PROJECT_ROOT}/logs" \
  -p save_csv:=true
status=$?
set -e

echo
echo "Latest CSV files:"
if compgen -G "${PROJECT_ROOT}/logs/*.csv" >/dev/null; then
  ls -lt "${PROJECT_ROOT}"/logs/*.csv | head -5
else
  echo "No CSV files found in ${PROJECT_ROOT}/logs"
fi

exit "${status}"
