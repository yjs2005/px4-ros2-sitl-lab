#!/usr/bin/env python3
"""Simulation-only PX4 Offboard figure-eight node.

WARNING: simulation-only, not for real aircraft.

This node is intended only for PX4 SITL with Gazebo and Micro XRCE-DDS Agent.
Do not connect it to a real vehicle. PX4 local setpoints use NED coordinates,
so negative z means upward.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable

import rclpy
from px4_msgs.msg import OffboardControlMode
from px4_msgs.msg import TrajectorySetpoint
from px4_msgs.msg import VehicleCommand
from px4_msgs.msg import VehicleOdometry
from px4_msgs.msg import VehicleStatus
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy
from rclpy.qos import HistoryPolicy
from rclpy.qos import QoSProfile
from rclpy.qos import ReliabilityPolicy


DEFAULT_RATE_HZ = 20.0
DEFAULT_TARGET_ALTITUDE_NED = -2.0
DEFAULT_FIGURE8_AMP_X = 1.0
DEFAULT_FIGURE8_AMP_Y = 0.6
DEFAULT_FIGURE8_DURATION_S = 40.0
DEFAULT_WARMUP_DURATION_S = 2.0
DEFAULT_HOVER_BEFORE_FIGURE8_S = 3.0
DEFAULT_LANDING_DURATION_S = 3.0
DEFAULT_COMMAND_DELAY_S = 0.5
NAN_VECTOR = [math.nan, math.nan, math.nan]


class OffboardFigure8(Node):
    """Publish a small SITL-only PX4 Offboard figure-eight trajectory."""

    def __init__(self, dry_run_cli: bool = False) -> None:
        super().__init__("offboard_figure8")

        self.declare_parameter("rate_hz", DEFAULT_RATE_HZ)
        self.declare_parameter("target_altitude_ned", DEFAULT_TARGET_ALTITUDE_NED)
        self.declare_parameter("figure8_amp_x", DEFAULT_FIGURE8_AMP_X)
        self.declare_parameter("figure8_amp_y", DEFAULT_FIGURE8_AMP_Y)
        self.declare_parameter("figure8_duration_s", DEFAULT_FIGURE8_DURATION_S)
        self.declare_parameter("warmup_duration_s", DEFAULT_WARMUP_DURATION_S)
        self.declare_parameter("hover_before_figure8_s", DEFAULT_HOVER_BEFORE_FIGURE8_S)
        self.declare_parameter("landing_duration_s", DEFAULT_LANDING_DURATION_S)
        self.declare_parameter("command_delay_s", DEFAULT_COMMAND_DELAY_S)
        self.declare_parameter("dry_run", False)
        self.declare_parameter("log_directory", str(Path.home() / "px4_ros2_ws" / "logs"))
        self.declare_parameter("vehicle_status_topic", "/fmu/out/vehicle_status")
        self.declare_parameter("vehicle_odometry_topic", "/fmu/out/vehicle_odometry")

        self.rate_hz = float(self.get_parameter("rate_hz").value)
        if self.rate_hz < 10.0:
            self.get_logger().warning(
                f"Requested rate_hz={self.rate_hz:.1f} is too low for Offboard; using 10 Hz."
            )
            self.rate_hz = 10.0

        self.target_altitude_ned = float(self.get_parameter("target_altitude_ned").value)
        self.figure8_amp_x = float(self.get_parameter("figure8_amp_x").value)
        self.figure8_amp_y = float(self.get_parameter("figure8_amp_y").value)
        self.figure8_duration_s = float(self.get_parameter("figure8_duration_s").value)
        self.warmup_duration_s = float(self.get_parameter("warmup_duration_s").value)
        self.hover_before_figure8_s = float(self.get_parameter("hover_before_figure8_s").value)
        self.landing_duration_s = float(self.get_parameter("landing_duration_s").value)
        self.command_delay_s = float(self.get_parameter("command_delay_s").value)
        self.dry_run = bool(self.get_parameter("dry_run").value) or dry_run_cli

        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        self.offboard_control_mode_publisher = self.create_publisher(
            OffboardControlMode,
            "/fmu/in/offboard_control_mode",
            qos_profile,
        )
        self.trajectory_setpoint_publisher = self.create_publisher(
            TrajectorySetpoint,
            "/fmu/in/trajectory_setpoint",
            qos_profile,
        )
        self.vehicle_command_publisher = self.create_publisher(
            VehicleCommand,
            "/fmu/in/vehicle_command",
            qos_profile,
        )

        status_topic = str(self.get_parameter("vehicle_status_topic").value)
        for topic in self._unique_topics([status_topic, "/fmu/out/vehicle_status_v4"]):
            self.create_subscription(VehicleStatus, topic, self.vehicle_status_callback, qos_profile)

        odometry_topic = str(self.get_parameter("vehicle_odometry_topic").value)
        self.create_subscription(
            VehicleOdometry,
            odometry_topic,
            self.vehicle_odometry_callback,
            qos_profile,
        )

        self.vehicle_status: VehicleStatus | None = None
        self.vehicle_odometry: VehicleOdometry | None = None
        self.stage = "warmup"
        self.setpoint_count = 0
        self.warmup_setpoint_count = max(1, int(self.warmup_duration_s * self.rate_hz))
        self.stage_started_ns = self.get_clock().now().nanoseconds
        self.figure8_started_ns: int | None = None
        self.last_state_print_ns = 0
        self.done = False
        self.current_target = (0.0, 0.0, self.target_altitude_ned)

        self.csv_file = self._open_csv_log()
        self.csv_writer = csv.DictWriter(
            self.csv_file,
            fieldnames=[
                "timestamp",
                "arming_state",
                "nav_state",
                "x",
                "y",
                "z",
                "vx",
                "vy",
                "vz",
                "target_x",
                "target_y",
                "target_z",
                "stage",
                "trajectory_type",
            ],
        )
        self.csv_writer.writeheader()

        self.timer = self.create_timer(1.0 / self.rate_hz, self.timer_callback)

        self.get_logger().warning("SIMULATION ONLY: do not use this node on a real aircraft.")
        self.get_logger().info(
            "Figure-eight parameters: "
            f"altitude_ned={self.target_altitude_ned:.2f}, "
            f"amp_x={self.figure8_amp_x:.2f}, amp_y={self.figure8_amp_y:.2f}, "
            f"duration={self.figure8_duration_s:.1f}s, rate={self.rate_hz:.1f}Hz"
        )
        if self.dry_run:
            self.get_logger().warning("Dry-run is enabled: arm, OFFBOARD, and land commands are not sent.")
        self.get_logger().info(f"CSV log: {self.csv_file.name}")

    @staticmethod
    def _unique_topics(topics: Iterable[str]) -> list[str]:
        result: list[str] = []
        for topic in topics:
            if topic and topic not in result:
                result.append(topic)
        return result

    def _open_csv_log(self):
        log_dir = Path(str(self.get_parameter("log_directory").value)).expanduser()
        log_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return (log_dir / f"offboard_figure8_{stamp}.csv").open("w", newline="", encoding="utf-8")

    def vehicle_status_callback(self, msg: VehicleStatus) -> None:
        self.vehicle_status = msg

    def vehicle_odometry_callback(self, msg: VehicleOdometry) -> None:
        self.vehicle_odometry = msg

    def timer_callback(self) -> None:
        if self.done:
            return

        now = self.get_clock().now()
        now_ns = now.nanoseconds
        now_us = int(now_ns / 1000)

        target = self.compute_target(now_ns)
        self.current_target = target
        self.publish_offboard_control_mode(now_us)
        self.publish_trajectory_setpoint(now_us, target)
        self.write_csv_row(now_us, target)
        self.print_state_once_per_second(now_ns, target)
        self.update_stage(now_ns)
        self.setpoint_count += 1

    def update_stage(self, now_ns: int) -> None:
        if self.stage == "warmup":
            if self.setpoint_count >= self.warmup_setpoint_count:
                if self.dry_run:
                    self.change_stage("dry_run_pre_figure8_hover", now_ns)
                else:
                    self.arm()
                    self.change_stage("arming", now_ns)
        elif self.stage == "arming":
            if self.stage_elapsed_seconds(now_ns) >= self.command_delay_s:
                self.engage_offboard_mode()
                self.change_stage("offboard", now_ns)
        elif self.stage == "offboard":
            if self.stage_elapsed_seconds(now_ns) >= self.command_delay_s:
                self.change_stage("pre_figure8_hover", now_ns)
        elif self.stage == "pre_figure8_hover":
            if self.stage_elapsed_seconds(now_ns) >= self.hover_before_figure8_s:
                self.figure8_started_ns = now_ns
                self.change_stage("figure8", now_ns)
        elif self.stage == "figure8":
            if self.figure8_elapsed_seconds(now_ns) >= self.figure8_duration_s:
                if self.dry_run:
                    self.change_stage("dry_run_complete", now_ns)
                    self.request_shutdown()
                else:
                    self.land()
                    self.change_stage("landing", now_ns)
        elif self.stage == "dry_run_pre_figure8_hover":
            if self.stage_elapsed_seconds(now_ns) >= self.hover_before_figure8_s:
                self.figure8_started_ns = now_ns
                self.change_stage("figure8", now_ns)
        elif self.stage == "landing":
            if self.stage_elapsed_seconds(now_ns) >= self.landing_duration_s:
                self.change_stage("complete", now_ns)
                self.request_shutdown()

    def compute_target(self, now_ns: int) -> tuple[float, float, float]:
        if self.stage != "figure8" or self.figure8_started_ns is None:
            return (0.0, 0.0, self.target_altitude_ned)

        t = self.figure8_elapsed_seconds(now_ns)
        omega = 2.0 * math.pi / self.figure8_duration_s
        x = self.figure8_amp_x * math.sin(omega * t)
        y = self.figure8_amp_y * math.sin(2.0 * omega * t)
        z = self.target_altitude_ned
        return (x, y, z)

    def stage_elapsed_seconds(self, now_ns: int) -> float:
        return (now_ns - self.stage_started_ns) / 1e9

    def figure8_elapsed_seconds(self, now_ns: int) -> float:
        if self.figure8_started_ns is None:
            return 0.0
        return (now_ns - self.figure8_started_ns) / 1e9

    def change_stage(self, stage: str, now_ns: int) -> None:
        self.stage = stage
        self.stage_started_ns = now_ns
        self.get_logger().info(f"Stage changed to {stage}")

    def publish_offboard_control_mode(self, now_us: int) -> None:
        msg = OffboardControlMode()
        msg.timestamp = now_us
        msg.position = True
        msg.velocity = False
        msg.acceleration = False
        msg.attitude = False
        msg.body_rate = False
        msg.thrust_and_torque = False
        msg.direct_actuator = False
        self.offboard_control_mode_publisher.publish(msg)

    def publish_trajectory_setpoint(self, now_us: int, target: tuple[float, float, float]) -> None:
        msg = TrajectorySetpoint()
        msg.timestamp = now_us
        msg.position = [target[0], target[1], target[2]]
        msg.velocity = list(NAN_VECTOR)
        msg.acceleration = list(NAN_VECTOR)
        msg.jerk = list(NAN_VECTOR)
        msg.yaw = 0.0
        msg.yawspeed = math.nan
        self.trajectory_setpoint_publisher.publish(msg)

    def arm(self) -> None:
        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM,
            param1=float(VehicleCommand.ARMING_ACTION_ARM),
        )
        self.get_logger().info("Arm command sent")

    def engage_offboard_mode(self) -> None:
        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_DO_SET_MODE,
            param1=1.0,
            param2=6.0,
        )
        self.get_logger().info("OFFBOARD mode command sent")

    def land(self) -> None:
        self.publish_vehicle_command(VehicleCommand.VEHICLE_CMD_NAV_LAND)
        self.get_logger().info("Land command sent")

    def publish_vehicle_command(self, command: int, **params: float) -> None:
        if self.dry_run:
            self.get_logger().info(f"Dry-run: skipped vehicle command {command}")
            return

        msg = VehicleCommand()
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        msg.param1 = float(params.get("param1", 0.0))
        msg.param2 = float(params.get("param2", 0.0))
        msg.param3 = float(params.get("param3", 0.0))
        msg.param4 = float(params.get("param4", 0.0))
        msg.param5 = float(params.get("param5", 0.0))
        msg.param6 = float(params.get("param6", 0.0))
        msg.param7 = float(params.get("param7", 0.0))
        msg.command = int(command)
        msg.target_system = 1
        msg.target_component = 1
        msg.source_system = 1
        msg.source_component = 1
        msg.from_external = True
        self.vehicle_command_publisher.publish(msg)

    def print_state_once_per_second(self, now_ns: int, target: tuple[float, float, float]) -> None:
        if now_ns - self.last_state_print_ns < 1_000_000_000:
            return
        self.last_state_print_ns = now_ns

        arming_state = self.vehicle_status.arming_state if self.vehicle_status else -1
        nav_state = self.vehicle_status.nav_state if self.vehicle_status else -1
        position, _velocity = self.position_and_velocity()
        self.get_logger().info(
            "stage=%s arming_state=%s nav_state=%s "
            "position_ned=(%.2f, %.2f, %.2f) target_ned=(%.2f, %.2f, %.2f)"
            % (
                self.stage,
                arming_state,
                nav_state,
                position[0],
                position[1],
                position[2],
                target[0],
                target[1],
                target[2],
            )
        )

    def position_and_velocity(self) -> tuple[list[float], list[float]]:
        if self.vehicle_odometry is None:
            return list(NAN_VECTOR), list(NAN_VECTOR)
        return list(self.vehicle_odometry.position), list(self.vehicle_odometry.velocity)

    def write_csv_row(self, now_us: int, target: tuple[float, float, float]) -> None:
        position, velocity = self.position_and_velocity()
        arming_state = self.vehicle_status.arming_state if self.vehicle_status else -1
        nav_state = self.vehicle_status.nav_state if self.vehicle_status else -1
        self.csv_writer.writerow(
            {
                "timestamp": now_us,
                "arming_state": arming_state,
                "nav_state": nav_state,
                "x": position[0],
                "y": position[1],
                "z": position[2],
                "vx": velocity[0],
                "vy": velocity[1],
                "vz": velocity[2],
                "target_x": target[0],
                "target_y": target[1],
                "target_z": target[2],
                "stage": self.stage,
                "trajectory_type": "figure8",
            }
        )
        self.csv_file.flush()

    def request_shutdown(self) -> None:
        self.done = True
        self.get_logger().info("Offboard figure-eight node sequence complete; shutting down.")
        self.csv_file.flush()
        self.csv_file.close()
        rclpy.shutdown()

    def destroy_node(self) -> bool:
        if hasattr(self, "csv_file") and not self.csv_file.closed:
            self.csv_file.flush()
            self.csv_file.close()
        return super().destroy_node()


def parse_cli(argv: list[str]) -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(
        description="Simulation-only PX4 SITL Offboard figure-eight node.",
        add_help=True,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Publish setpoints but skip arm, OFFBOARD, and land vehicle commands.",
    )
    parsed, ros_args = parser.parse_known_args(argv[1:])
    return parsed, [argv[0]] + ros_args


def main(args: list[str] | None = None) -> None:
    argv = sys.argv if args is None else args
    cli_args, ros_args = parse_cli(argv)

    rclpy.init(args=ros_args)
    node = OffboardFigure8(dry_run_cli=cli_args.dry_run)
    try:
        rclpy.spin(node)
    except ExternalShutdownException:
        pass
    except KeyboardInterrupt:
        node.get_logger().info("Interrupted by user.")
    finally:
        if rclpy.ok():
            node.destroy_node()
            rclpy.shutdown()
        else:
            node.destroy_node()


if __name__ == "__main__":
    main()
