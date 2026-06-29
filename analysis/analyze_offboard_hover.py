#!/usr/bin/env python3
"""Analyze the first successful PX4 Offboard hover CSV log."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


REQUIRED_COLUMNS = [
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
]

STEADY_STATE_Z_THRESHOLD_NED = -1.8
STEADY_STATE_FALLBACK_SECONDS = 5.0


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--csv",
        type=Path,
        default=repo_root / "logs" / "offboard_hover_first_success.csv",
        help="Input Offboard hover CSV log.",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=repo_root / "results",
        help="Directory for metrics and figures.",
    )
    return parser.parse_args()


def load_log(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}")

    numeric_columns = [column for column in REQUIRED_COLUMNS if column != "stage"]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df = df.dropna(subset=["timestamp", "x", "y", "z", "vx", "vy", "vz"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    if df.empty:
        raise ValueError("CSV contains no usable samples.")

    df["time_s"] = (df["timestamp"] - df["timestamp"].iloc[0]) / 1_000_000.0
    df["z_error"] = df["z"] - df["target_z"]
    df["xy_error"] = ((df["x"] - df["target_x"]) ** 2 + (df["y"] - df["target_y"]) ** 2) ** 0.5
    df["position_error"] = (
        (df["x"] - df["target_x"]) ** 2
        + (df["y"] - df["target_y"]) ** 2
        + (df["z"] - df["target_z"]) ** 2
    ) ** 0.5
    df["speed"] = (df["vx"] ** 2 + df["vy"] ** 2 + df["vz"] ** 2) ** 0.5
    return df


def rmse(series: pd.Series) -> float:
    if series.empty:
        return math.nan
    return float((series.pow(2).mean()) ** 0.5)


def frequency_hz(df: pd.DataFrame) -> dict[str, float]:
    intervals = df["timestamp"].diff().dropna() / 1_000_000.0
    intervals = intervals[intervals > 0]
    if intervals.empty:
        return {
            "mean_hz": math.nan,
            "median_hz": math.nan,
            "mean_dt_s": math.nan,
            "median_dt_s": math.nan,
        }
    mean_dt = float(intervals.mean())
    median_dt = float(intervals.median())
    return {
        "mean_hz": 1.0 / mean_dt,
        "median_hz": 1.0 / median_dt,
        "mean_dt_s": mean_dt,
        "median_dt_s": median_dt,
    }


def subset_metrics(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {
            "samples": 0,
            "duration_s": 0.0,
            "frequency": frequency_hz(df),
        }

    final = df.iloc[-1]
    return {
        "samples": int(len(df)),
        "duration_s": float(df["time_s"].iloc[-1] - df["time_s"].iloc[0]),
        "frequency": frequency_hz(df),
        "final_position": {
            "x": float(final["x"]),
            "y": float(final["y"]),
            "z": float(final["z"]),
        },
        "final_target": {
            "x": float(final["target_x"]),
            "y": float(final["target_y"]),
            "z": float(final["target_z"]),
        },
        "final_z_error_m": float(final["z_error"]),
        "final_position_error_m": float(final["position_error"]),
        "z_rmse_m": rmse(df["z_error"]),
        "z_mae_m": float(df["z_error"].abs().mean()),
        "max_abs_z_error_m": float(df["z_error"].abs().max()),
        "xy_rmse_m": rmse(df["xy_error"]),
        "max_xy_error_m": float(df["xy_error"].max()),
        "max_speed_mps": float(df["speed"].max()),
    }


def steady_state_hover_subset(hover: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    if hover.empty:
        return hover.copy(), {
            "method": "none",
            "criteria": "no hover samples available",
            "z_threshold_ned_m": STEADY_STATE_Z_THRESHOLD_NED,
            "fallback_last_seconds": STEADY_STATE_FALLBACK_SECONDS,
        }

    by_altitude = hover[hover["z"] <= STEADY_STATE_Z_THRESHOLD_NED].copy()
    if not by_altitude.empty:
        return by_altitude, {
            "method": "z_threshold",
            "criteria": f'stage == "hover" and z <= {STEADY_STATE_Z_THRESHOLD_NED}',
            "z_threshold_ned_m": STEADY_STATE_Z_THRESHOLD_NED,
            "fallback_last_seconds": STEADY_STATE_FALLBACK_SECONDS,
            "time_start_s": float(by_altitude["time_s"].iloc[0]),
            "time_end_s": float(by_altitude["time_s"].iloc[-1]),
        }

    cutoff_s = float(hover["time_s"].iloc[-1] - STEADY_STATE_FALLBACK_SECONDS)
    last_seconds = hover[hover["time_s"] >= cutoff_s].copy()
    return last_seconds, {
        "method": "last_seconds_fallback",
        "criteria": f"last {STEADY_STATE_FALLBACK_SECONDS:.1f} seconds of hover",
        "z_threshold_ned_m": STEADY_STATE_Z_THRESHOLD_NED,
        "fallback_last_seconds": STEADY_STATE_FALLBACK_SECONDS,
        "time_start_s": float(last_seconds["time_s"].iloc[0]) if not last_seconds.empty else math.nan,
        "time_end_s": float(last_seconds["time_s"].iloc[-1]) if not last_seconds.empty else math.nan,
    }


def build_metrics(df: pd.DataFrame, csv_path: Path) -> dict[str, Any]:
    hover = df[df["stage"] == "hover"].copy()
    steady_hover, steady_hover_selection = steady_state_hover_subset(hover)
    metrics = {
        "source_csv": str(csv_path.as_posix()),
        "target_position_ned": {
            "x": float(df["target_x"].dropna().iloc[-1]),
            "y": float(df["target_y"].dropna().iloc[-1]),
            "z": float(df["target_z"].dropna().iloc[-1]),
        },
        "whole_run": subset_metrics(df),
        "hover": subset_metrics(hover),
        "steady_state_hover": subset_metrics(steady_hover),
        "steady_state_hover_selection": steady_hover_selection,
        "stages": {
            stage: int(count)
            for stage, count in df["stage"].value_counts(sort=False).items()
        },
    }
    metrics["summary"] = {
        "samples": metrics["whole_run"]["samples"],
        "control_frequency_estimate_hz": metrics["whole_run"]["frequency"]["median_hz"],
        "hover_duration_s": metrics["hover"]["duration_s"],
        "final_hover_z_error_m": metrics["hover"]["final_z_error_m"],
        "hover_z_rmse_m": metrics["hover"]["z_rmse_m"],
        "hover_z_mae_m": metrics["hover"]["z_mae_m"],
        "hover_max_abs_z_error_m": metrics["hover"]["max_abs_z_error_m"],
        "hover_xy_rmse_m": metrics["hover"]["xy_rmse_m"],
        "hover_max_xy_error_m": metrics["hover"]["max_xy_error_m"],
        "final_hover_position_error_m": metrics["hover"]["final_position_error_m"],
        "hover_max_speed_mps": metrics["hover"]["max_speed_mps"],
        "steady_state_hover_samples": metrics["steady_state_hover"]["samples"],
        "steady_state_hover_duration_s": metrics["steady_state_hover"]["duration_s"],
        "steady_state_hover_z_rmse_m": metrics["steady_state_hover"]["z_rmse_m"],
        "steady_state_hover_z_mae_m": metrics["steady_state_hover"]["z_mae_m"],
        "steady_state_hover_max_abs_z_error_m": metrics["steady_state_hover"]["max_abs_z_error_m"],
        "steady_state_hover_xy_rmse_m": metrics["steady_state_hover"]["xy_rmse_m"],
        "steady_state_hover_max_xy_error_m": metrics["steady_state_hover"]["max_xy_error_m"],
        "steady_state_hover_final_position_error_m": metrics["steady_state_hover"]["final_position_error_m"],
        "steady_state_hover_max_speed_mps": metrics["steady_state_hover"]["max_speed_mps"],
    }
    return metrics


def write_json(metrics: dict[str, Any], output_path: Path) -> None:
    output_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")


def fmt(value: float, digits: int = 4) -> str:
    if value is None or math.isnan(float(value)):
        return "n/a"
    return f"{float(value):.{digits}f}"


def write_markdown(metrics: dict[str, Any], output_path: Path) -> None:
    summary = metrics["summary"]
    hover = metrics["hover"]
    steady = metrics["steady_state_hover"]
    steady_selection = metrics["steady_state_hover_selection"]
    whole = metrics["whole_run"]
    target = metrics["target_position_ned"]
    lines = [
        "# Offboard Hover Metrics",
        "",
        "Source CSV: `logs/offboard_hover_first_success.csv`",
        "",
        "Target position is PX4 local NED. Negative `z` means upward.",
        "",
        f"- Target NED: `x={target['x']:.2f}`, `y={target['y']:.2f}`, `z={target['z']:.2f}`",
        f"- Whole-run samples: `{whole['samples']}`",
        f"- Whole-run duration: `{fmt(whole['duration_s'], 3)} s`",
        f"- Median control frequency estimate: `{fmt(summary['control_frequency_estimate_hz'], 2)} Hz`",
        "",
        "## Full Hover Stage",
        "",
        "The full hover stage includes climb and convergence samples before the vehicle settles near the target altitude.",
        "",
        f"- Hover samples: `{hover['samples']}`",
        f"- Hover duration: `{fmt(summary['hover_duration_s'], 3)} s`",
        f"- Final hover z error: `{fmt(summary['final_hover_z_error_m'], 4)} m`",
        f"- Hover z RMSE: `{fmt(summary['hover_z_rmse_m'], 4)} m`",
        f"- Hover z MAE: `{fmt(summary['hover_z_mae_m'], 4)} m`",
        f"- Hover max absolute z error: `{fmt(summary['hover_max_abs_z_error_m'], 4)} m`",
        f"- Hover XY RMSE: `{fmt(summary['hover_xy_rmse_m'], 4)} m`",
        f"- Hover max XY error: `{fmt(summary['hover_max_xy_error_m'], 4)} m`",
        f"- Final hover position error: `{fmt(summary['final_hover_position_error_m'], 4)} m`",
        f"- Max speed during hover: `{fmt(summary['hover_max_speed_mps'], 4)} m/s`",
        "",
        "## Steady-State Hover",
        "",
        f"Selection: `{steady_selection['criteria']}`.",
        "",
        f"- Steady-state hover samples: `{steady['samples']}`",
        f"- Steady-state hover duration: `{fmt(summary['steady_state_hover_duration_s'], 3)} s`",
        f"- Steady-state z RMSE: `{fmt(summary['steady_state_hover_z_rmse_m'], 4)} m`",
        f"- Steady-state z MAE: `{fmt(summary['steady_state_hover_z_mae_m'], 4)} m`",
        f"- Steady-state max absolute z error: `{fmt(summary['steady_state_hover_max_abs_z_error_m'], 4)} m`",
        f"- Steady-state XY RMSE: `{fmt(summary['steady_state_hover_xy_rmse_m'], 4)} m`",
        f"- Steady-state max XY error: `{fmt(summary['steady_state_hover_max_xy_error_m'], 4)} m`",
        f"- Steady-state final position error: `{fmt(summary['steady_state_hover_final_position_error_m'], 4)} m`",
        f"- Steady-state max speed: `{fmt(summary['steady_state_hover_max_speed_mps'], 4)} m/s`",
        "",
        "## Stage Sample Counts",
        "",
    ]
    for stage, count in metrics["stages"].items():
        lines.append(f"- `{stage}`: `{count}`")
    lines.extend(
        [
            "",
            "## Figures",
            "",
            "- [Z tracking](figures/offboard_hover_z.png)",
            "- [XY trajectory](figures/offboard_hover_xy.png)",
            "- [NED position](figures/offboard_hover_ned_position.png)",
            "- [NED velocity](figures/offboard_hover_velocity.png)",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def save_figures(df: pd.DataFrame, figures_dir: Path) -> None:
    figures_dir.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(9, 4.8))
    plt.plot(df["time_s"], df["z"], label="z")
    plt.plot(df["time_s"], df["target_z"], "--", label="target_z")
    plt.xlabel("Time (s)")
    plt.ylabel("NED z (m)")
    plt.title("Offboard Hover Z Tracking")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(figures_dir / "offboard_hover_z.png", dpi=160)
    plt.close()

    plt.figure(figsize=(6.2, 6.2))
    plt.plot(df["y"], df["x"], label="trajectory")
    plt.scatter(df["target_y"].iloc[-1], df["target_x"].iloc[-1], marker="x", s=80, label="target")
    plt.xlabel("East y (m)")
    plt.ylabel("North x (m)")
    plt.title("Offboard Hover XY Trajectory")
    plt.axis("equal")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(figures_dir / "offboard_hover_xy.png", dpi=160)
    plt.close()

    plt.figure(figsize=(9, 5.2))
    plt.plot(df["time_s"], df["x"], label="x")
    plt.plot(df["time_s"], df["y"], label="y")
    plt.plot(df["time_s"], df["z"], label="z")
    plt.plot(df["time_s"], df["target_z"], "--", color="0.5", label="target_z")
    plt.xlabel("Time (s)")
    plt.ylabel("Position (m)")
    plt.title("Offboard Hover NED Position")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(figures_dir / "offboard_hover_ned_position.png", dpi=160)
    plt.close()

    plt.figure(figsize=(9, 5.2))
    plt.plot(df["time_s"], df["vx"], label="vx")
    plt.plot(df["time_s"], df["vy"], label="vy")
    plt.plot(df["time_s"], df["vz"], label="vz")
    plt.xlabel("Time (s)")
    plt.ylabel("Velocity (m/s)")
    plt.title("Offboard Hover NED Velocity")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(figures_dir / "offboard_hover_velocity.png", dpi=160)
    plt.close()


def main() -> None:
    args = parse_args()
    csv_path = args.csv.resolve()
    results_dir = args.results_dir.resolve()
    figures_dir = results_dir / "figures"

    df = load_log(csv_path)
    metrics = build_metrics(df, csv_path)

    results_dir.mkdir(parents=True, exist_ok=True)
    write_json(metrics, results_dir / "offboard_hover_metrics.json")
    write_markdown(metrics, results_dir / "offboard_hover_metrics.md")
    save_figures(df, figures_dir)

    summary = metrics["summary"]
    print("Offboard hover analysis complete")
    print(f"samples={summary['samples']}")
    print(f"frequency_hz={summary['control_frequency_estimate_hz']:.3f}")
    print(f"hover_duration_s={summary['hover_duration_s']:.3f}")
    print(f"hover_z_rmse_m={summary['hover_z_rmse_m']:.4f}")
    print(f"steady_state_hover_duration_s={summary['steady_state_hover_duration_s']:.3f}")
    print(f"steady_state_hover_z_rmse_m={summary['steady_state_hover_z_rmse_m']:.4f}")
    print(f"final_hover_position_error_m={summary['final_hover_position_error_m']:.4f}")


if __name__ == "__main__":
    main()
