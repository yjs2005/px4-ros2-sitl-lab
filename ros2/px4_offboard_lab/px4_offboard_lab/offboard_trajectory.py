#!/usr/bin/env python3
"""Simulation-only multi-trajectory PX4 Offboard node.

WARNING: simulation-only, not for real aircraft.

This node is intended for PX4 SITL with Gazebo and Micro XRCE-DDS Agent.
It publishes position setpoints in PX4 local NED coordinates. Negative z
means upward. Do not connect this node to a real vehicle.
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


SUPPORTED_TRAJECTORIES = {"hover", "line", "square", "circle", "figure8", "z_step"}
NAN_VECTOR = [math.nan, math.nan, math.nan]


class OffboardTrajectory(Node):
    """Publish a parameterized SITL-only PX4 Offboard trajectory."""

    def __init__(self, dry_run_cli: bool = False) -> None:
        super().__init__("offboard_trajectory")

        self.declare_parameter("trajectory", "figure8")
        self.declare_parameter("altitude", -2.0)
        self.declare_parameter("rate_hz", 20.0)
        self.declare_parameter("duration_s", 40.0)
        self.declare_parameter("amplitude_x", 1.0)
        self.declare_parameter("amplitude_y", 0.8)
        self.declare_parameter("radius", 1.0)
        self.declare_parameter("square_size", 1.5)
        self.declare_parameter("warmup_s", 5.0)
        self.declare_parameter("pretrack_hover_s", 3.0)
        self.declare_parameter("landing_s", 8.0)
        self.declare_parameter("command_delay_s", 0.5)
        self.declare_parameter("dry_run", False)
        self.declare_parameter("log_directory", str(Path.home() / "px4_ros2_ws" / "logs"))
        self.declare_parameter("vehicle_status_topic", "/fmu/out/vehicle_status")
        self.declare_parameter("vehicle_odometry_topic", "/fmu/out/vehicle_odometry")

        self.trajectory = str(self.get_parameter("trajectory").value).strip().lower()
        if self.trajectory not in SUPPORTED_TRAJECTORIES:
            raise ValueError(
                f"Unsupported trajectory '{self.trajectory}'. "
                f"Choose one of: {', '.join(sorted(SUPPORTED_TRAJECTORIES))}"
            )

        self.altitude = float(self.get_parameter("altitude").value)
        self.rate_hz = max(10.0, float(self.get_parameter("rate_hz").value))
        self.duration_s = max(1.0, float(self.get_parameter("duration_s").value))
        self.amplitude_x = float(self.get_parameter("amplitude_x").value)
        self.amplitude_y = float(self.get_parameter("amplitude_y").value)
        self.radius = float(self.get_parameter("radius").value)
        self.square_size = float(self.get_parameter("square_size").value)
        self.warmup_s = max(0.5, float(self.get_parameter("warmup_s").value))
        self.pretrack_hover_s = max(0.0, float(self.get_parameter("pretrack_hover_s").value))
        self.landing_s = max(1.0, float(self.get_parameter("landing_s").value))
        self.command_delay_s = max(0.1, float(self.get_parameter("command_delay_s").value))
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
        self.warmup_setpoint_count = max(1, int(self.warmup_s * self.rate_hz))
        self.stage_started_ns = self.get_clock().now().nanoseconds
        self.tracking_started_ns: int | None = None
        self.last_state_print_ns = 0
        self.done = False
        self.current_target = (0.0, 0.0, self.altitude)

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
                "position_error_xy",
                "position_error_3d",
            ],
        )
        self.csv_writer.writeheader()

        self.timer = self.create_timer(1.0 / self.rate_hz, self.timer_callback)

        self.get_logger().warning("SIMULATION ONLY: do not use this node on a real aircraft.")
        self.get_logger().info(
            "Trajectory=%s altitude_ned=%.2f duration=%.1fs rate=%.1fHz; negative z is upward."
            % (self.trajectory, self.altitude, self.duration_s, self.rate_hz)
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
        filename = f"offboard_trajectory_{self.trajectory}_{stamp}.csv"
        return (log_dir / filename).open("w", newline="", encoding="utf-8")

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
                    self.change_stage("dry_run_pretrack_hover", now_ns)
                else:
                    self.arm()
                    self.change_stage("arming", now_ns)
        elif self.stage == "arming":
            if self.stage_elapsed_seconds(now_ns) >= self.command_delay_s:
                self.engage_offboard_mode()
                self.change_stage("offboard", now_ns)
        elif self.stage == "offboard":
            if self.stage_elapsed_seconds(now_ns) >= self.command_delay_s:
                self.change_stage("pretrack_hover", now_ns)
        elif self.stage in {"pretrack_hover", "dry_run_pretrack_hover"}:
            if self.stage_elapsed_seconds(now_ns) >= self.pretrack_hover_s:
                self.tracking_started_ns = now_ns
                self.change_stage("tracking", now_ns)
        elif self.stage == "tracking":
            if self.tracking_elapsed_seconds(now_ns) >= self.duration_s:
                if self.dry_run:
                    self.change_stage("dry_run_complete", now_ns)
                    self.request_shutdown()
                else:
                    self.land()
                    self.change_stage("landing", now_ns)
        elif self.stage == "landing":
            if self.stage_elapsed_seconds(now_ns) >= self.landing_s:
                self.change_stage("complete", now_ns)
                self.request_shutdown()

    def compute_target(self, now_ns: int) -> tuple[float, float, float]:
        if self.stage != "tracking" or self.tracking_started_ns is None:
            return (0.0, 0.0, self.altitude)

        t = min(self.tracking_elapsed_seconds(now_ns), self.duration_s)
        phase = 2.0 * math.pi * t / self.duration_s

        if self.trajectory == "hover":
            return (0.0, 0.0, self.altitude)
        if self.trajectory == "line":
            x = self.amplitude_x * math.sin(phase)
            return (x, 0.0, self.altitude)
        if self.trajectory == "square":
            x, y = self.square_target(t)
            return (x, y, self.altitude)
        if self.trajectory == "circle":
            x = self.radius * math.cos(phase)
            y = self.radius * math.sin(phase)
            return (x, y, self.altitude)
        if self.trajectory == "figure8":
            x = self.amplitude_x * math.sin(phase)
            y = self.amplitude_y * math.sin(2.0 * phase)
            return (x, y, self.altitude)
        if self.trajectory == "z_step":
            z = self.z_step_target(t)
            return (0.0, 0.0, z)

        return (0.0, 0.0, self.altitude)

    def square_target(self, t: float) -> tuple[float, float]:
        half = self.square_size / 2.0
        corners = [
            (-half, -half),
            (half, -half),
            (half, half),
            (-half, half),
            (-half, -half),
        ]
        segment_duration = self.duration_s / 4.0
        segment = min(3, int(t / segment_duration))
        local_t = (t - segment * segment_duration) / segment_duration
        x0, y0 = corners[segment]
        x1, y1 = corners[segment + 1]
        x = x0 + (x1 - x0) * local_t
        y = y0 + (y1 - y0) * local_t
        return x, y

    def z_step_target(self, t: float) -> float:
        # NED z is negative upward. Smooth steps avoid abrupt setpoint jumps.
        low = -1.5
        high = -2.5
        period = max(2.0, self.duration_s / 4.0)
        step = int(t / period) % 2
        target = high if step else low
        previous = low if step else high
        blend_s = min(2.0, period / 3.0)
        phase = (t % period) / blend_s
        if phase >= 1.0:
            return target
        smooth = 0.5 - 0.5 * math.cos(math.pi * phase)
        return previous + (target - previous) * smooth

    def stage_elapsed_seconds(self, now_ns: int) -> float:
        return (now_ns - self.stage_started_ns) / 1e9

    def tracking_elapsed_seconds(self, now_ns: int) -> float:
        if self.tracking_started_ns is None:
            return 0.0
        return (now_ns - self.tracking_started_ns) / 1e9

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
            "trajectory=%s stage=%s arming_state=%s nav_state=%s "
            "position_ned=(%.2f, %.2f, %.2f) target_ned=(%.2f, %.2f, %.2f)"
            % (
                self.trajectory,
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

    @staticmethod
    def position_errors(position: list[float], target: tuple[float, float, float]) -> tuple[float, float]:
        if any(math.isnan(value) for value in position):
            return math.nan, math.nan
        dx = position[0] - target[0]
        dy = position[1] - target[1]
        dz = position[2] - target[2]
        xy_error = math.sqrt(dx * dx + dy * dy)
        position_error = math.sqrt(dx * dx + dy * dy + dz * dz)
        return xy_error, position_error

    def write_csv_row(self, now_us: int, target: tuple[float, float, float]) -> None:
        position, velocity = self.position_and_velocity()
        arming_state = self.vehicle_status.arming_state if self.vehicle_status else -1
        nav_state = self.vehicle_status.nav_state if self.vehicle_status else -1
        xy_error, position_error = self.position_errors(position, target)
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
                "trajectory_type": self.trajectory,
                "position_error_xy": xy_error,
                "position_error_3d": position_error,
            }
        )
        self.csv_file.flush()

    def request_shutdown(self) -> None:
        self.done = True
        self.get_logger().info("Offboard trajectory node sequence complete; shutting down.")
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
        description="Simulation-only PX4 SITL Offboard multi-trajectory node.",
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
    node = OffboardTrajectory(dry_run_cli=cli_args.dry_run)
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
