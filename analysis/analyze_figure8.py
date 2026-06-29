#!/usr/bin/env python3
"""Analyze the first successful PX4 Offboard figure-eight CSV log."""

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
    "trajectory_type",
]

TRACKING_STAGE_CANDIDATES = ["figure8", "tracking", "trajectory"]


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--csv",
        type=Path,
        default=repo_root / "logs" / "figure8_first_success.csv",
        help="Input Offboard figure-eight CSV log.",
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

    numeric_columns = [column for column in REQUIRED_COLUMNS if column not in {"stage", "trajectory_type"}]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    required_numeric = [
        "timestamp",
        "x",
        "y",
        "z",
        "vx",
        "vy",
        "vz",
        "target_x",
        "target_y",
        "target_z",
    ]
    df = df.dropna(subset=required_numeric)
    df = df.sort_values("timestamp").reset_index(drop=True)
    if df.empty:
        raise ValueError("CSV contains no usable samples.")

    df["stage"] = df["stage"].astype(str)
    df["trajectory_type"] = df["trajectory_type"].astype(str)
    df["stage_normalized"] = df["stage"].str.strip().str.lower()
    df["trajectory_type_normalized"] = df["trajectory_type"].str.strip().str.lower()
    df["time_s"] = (df["timestamp"] - df["timestamp"].iloc[0]) / 1_000_000.0

    df["x_error"] = df["x"] - df["target_x"]
    df["y_error"] = df["y"] - df["target_y"]
    df["z_error"] = df["z"] - df["target_z"]
    df["xy_error"] = (df["x_error"] ** 2 + df["y_error"] ** 2) ** 0.5
    df["position_error"] = (df["xy_error"] ** 2 + df["z_error"] ** 2) ** 0.5
    df["speed"] = (df["vx"] ** 2 + df["vy"] ** 2 + df["vz"] ** 2) ** 0.5
    return df


def rmse(series: pd.Series) -> float:
    if series.empty:
        return math.nan
    return float((series.pow(2).mean()) ** 0.5)


def frequency_hz(df: pd.DataFrame) -> dict[str, float]:
    if df.empty:
        return {
            "mean_hz": math.nan,
            "median_hz": math.nan,
            "mean_dt_s": math.nan,
            "median_dt_s": math.nan,
        }
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
        "time_start_s": float(df["time_s"].iloc[0]),
        "time_end_s": float(df["time_s"].iloc[-1]),
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
        "final_xy_error_m": float(final["xy_error"]),
        "final_z_error_m": float(final["z_error"]),
        "final_position_error_m": float(final["position_error"]),
        "xy_rmse_m": rmse(df["xy_error"]),
        "xy_mae_m": float(df["xy_error"].mean()),
        "max_xy_error_m": float(df["xy_error"].max()),
        "z_rmse_m": rmse(df["z_error"]),
        "z_mae_m": float(df["z_error"].abs().mean()),
        "max_abs_z_error_m": float(df["z_error"].abs().max()),
        "position_rmse_m": rmse(df["position_error"]),
        "max_position_error_m": float(df["position_error"].max()),
        "max_speed_mps": float(df["speed"].max()),
    }


def select_tracking_stage(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    stages = set(df["stage_normalized"].dropna().unique())
    for candidate in TRACKING_STAGE_CANDIDATES:
        if candidate in stages:
            tracking = df[df["stage_normalized"] == candidate].copy()
            return tracking, {
                "method": "stage_name",
                "criteria": f'stage == "{candidate}"',
                "selected_stage": candidate,
                "candidate_order": TRACKING_STAGE_CANDIDATES,
            }

    trajectory_rows = df[df["trajectory_type_normalized"] == "figure8"].copy()
    excluded = {"warmup", "arming", "offboard", "pre_figure8_hover", "landing", "complete"}
    inferred = trajectory_rows[~trajectory_rows["stage_normalized"].isin(excluded)].copy()
    if not inferred.empty:
        selected_stages = sorted(inferred["stage_normalized"].unique().tolist())
        return inferred, {
            "method": "trajectory_type_fallback",
            "criteria": 'trajectory_type == "figure8" excluding setup and landing stages',
            "selected_stages": selected_stages,
            "candidate_order": TRACKING_STAGE_CANDIDATES,
        }

    raise ValueError(
        "Could not infer figure-eight tracking rows. "
        f"Observed stages: {sorted(stages)}"
    )


def build_metrics(df: pd.DataFrame, csv_path: Path) -> dict[str, Any]:
    tracking, tracking_filter = select_tracking_stage(df)
    metrics = {
        "source_csv": str(csv_path.as_posix()),
        "tracking_stage_filter": tracking_filter,
        "stages": {
            str(stage): int(count)
            for stage, count in df["stage"].value_counts(sort=False).items()
        },
        "trajectory_types": {
            str(kind): int(count)
            for kind, count in df["trajectory_type"].value_counts(sort=False).items()
        },
        "target_z_ned_m": float(df["target_z"].dropna().median()),
        "whole_run": subset_metrics(df),
        "figure8_tracking": subset_metrics(tracking),
        "landing_stage_present": bool((df["stage_normalized"] == "landing").any()),
        "offboard_or_tracking_present": bool(
            df["stage_normalized"].isin(["offboard", "figure8", "tracking", "trajectory"]).any()
        ),
    }
    tracking_metrics = metrics["figure8_tracking"]
    metrics["summary"] = {
        "samples": metrics["whole_run"]["samples"],
        "control_frequency_estimate_hz": metrics["whole_run"]["frequency"]["median_hz"],
        "tracking_samples": tracking_metrics["samples"],
        "tracking_duration_s": tracking_metrics["duration_s"],
        "tracking_frequency_estimate_hz": tracking_metrics["frequency"]["median_hz"],
        "tracking_xy_rmse_m": tracking_metrics["xy_rmse_m"],
        "tracking_xy_mae_m": tracking_metrics["xy_mae_m"],
        "tracking_max_xy_error_m": tracking_metrics["max_xy_error_m"],
        "tracking_z_rmse_m": tracking_metrics["z_rmse_m"],
        "tracking_z_mae_m": tracking_metrics["z_mae_m"],
        "tracking_max_abs_z_error_m": tracking_metrics["max_abs_z_error_m"],
        "tracking_position_rmse_m": tracking_metrics["position_rmse_m"],
        "tracking_max_position_error_m": tracking_metrics["max_position_error_m"],
        "final_position_error_before_landing_m": tracking_metrics["final_position_error_m"],
        "tracking_max_speed_mps": tracking_metrics["max_speed_mps"],
    }
    return metrics


def write_json(metrics: dict[str, Any], output_path: Path) -> None:
    output_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")


def fmt(value: float, digits: int = 4) -> str:
    if value is None or math.isnan(float(value)):
        return "n/a"
    return f"{float(value):.{digits}f}"


def write_markdown(metrics: dict[str, Any], output_path: Path) -> None:
    whole = metrics["whole_run"]
    tracking = metrics["figure8_tracking"]
    summary = metrics["summary"]
    tracking_filter = metrics["tracking_stage_filter"]
    lines = [
        "# Figure-Eight Tracking Metrics",
        "",
        "Source CSV: `logs/figure8_first_success.csv`",
        "",
        "PX4 local position uses NED coordinates. Negative `z` means upward.",
        "",
        f"- Tracking filter: `{tracking_filter['criteria']}`",
        f"- Landing stage present: `{metrics['landing_stage_present']}`",
        f"- Target NED altitude: `z={metrics['target_z_ned_m']:.2f}`",
        f"- Whole-run samples: `{whole['samples']}`",
        f"- Whole-run duration: `{fmt(whole['duration_s'], 3)} s`",
        f"- Median whole-run frequency estimate: `{fmt(summary['control_frequency_estimate_hz'], 2)} Hz`",
        "",
        "## Figure-Eight Tracking Stage",
        "",
        f"- Tracking samples: `{tracking['samples']}`",
        f"- Tracking duration: `{fmt(summary['tracking_duration_s'], 3)} s`",
        f"- Median tracking frequency estimate: `{fmt(summary['tracking_frequency_estimate_hz'], 2)} Hz`",
        f"- XY RMSE: `{fmt(summary['tracking_xy_rmse_m'], 4)} m`",
        f"- XY MAE: `{fmt(summary['tracking_xy_mae_m'], 4)} m`",
        f"- Max XY error: `{fmt(summary['tracking_max_xy_error_m'], 4)} m`",
        f"- z RMSE: `{fmt(summary['tracking_z_rmse_m'], 4)} m`",
        f"- z MAE: `{fmt(summary['tracking_z_mae_m'], 4)} m`",
        f"- Max absolute z error: `{fmt(summary['tracking_max_abs_z_error_m'], 4)} m`",
        f"- 3D position RMSE: `{fmt(summary['tracking_position_rmse_m'], 4)} m`",
        f"- Max 3D position error: `{fmt(summary['tracking_max_position_error_m'], 4)} m`",
        f"- Final position error before landing: `{fmt(summary['final_position_error_before_landing_m'], 4)} m`",
        f"- Max speed during tracking: `{fmt(summary['tracking_max_speed_mps'], 4)} m/s`",
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
            "- [XY tracking](figures/figure8_xy_tracking.png)",
            "- [Z tracking](figures/figure8_z_tracking.png)",
            "- [Position error](figures/figure8_position_error.png)",
            "- [Velocity](figures/figure8_velocity.png)",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def save_figures(df: pd.DataFrame, tracking: pd.DataFrame, figures_dir: Path) -> None:
    figures_dir.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(7.2, 6.4))
    plt.plot(tracking["target_y"], tracking["target_x"], "--", label="target")
    plt.plot(tracking["y"], tracking["x"], label="actual")
    if not tracking.empty:
        plt.scatter(tracking["target_y"].iloc[0], tracking["target_x"].iloc[0], marker="o", s=40, label="target start")
        plt.scatter(tracking["y"].iloc[0], tracking["x"].iloc[0], marker="s", s=40, label="actual start")
        plt.scatter(tracking["y"].iloc[-1], tracking["x"].iloc[-1], marker="x", s=70, label="actual end")
    plt.xlabel("East y (m)")
    plt.ylabel("North x (m)")
    plt.title("Figure-Eight XY Tracking")
    plt.axis("equal")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(figures_dir / "figure8_xy_tracking.png", dpi=160)
    plt.close()

    plt.figure(figsize=(9, 4.8))
    plt.plot(df["time_s"], df["z"], label="z")
    plt.plot(df["time_s"], df["target_z"], "--", label="target_z")
    plt.xlabel("Time (s)")
    plt.ylabel("NED z (m)")
    plt.title("Figure-Eight Z Tracking")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(figures_dir / "figure8_z_tracking.png", dpi=160)
    plt.close()

    plt.figure(figsize=(9, 4.8))
    plt.plot(df["time_s"], df["xy_error"], label="XY error")
    plt.plot(df["time_s"], df["position_error"], label="3D position error")
    plt.xlabel("Time (s)")
    plt.ylabel("Error (m)")
    plt.title("Figure-Eight Position Error")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(figures_dir / "figure8_position_error.png", dpi=160)
    plt.close()

    plt.figure(figsize=(9, 5.2))
    plt.plot(df["time_s"], df["vx"], label="vx")
    plt.plot(df["time_s"], df["vy"], label="vy")
    plt.plot(df["time_s"], df["vz"], label="vz")
    plt.xlabel("Time (s)")
    plt.ylabel("Velocity (m/s)")
    plt.title("Figure-Eight NED Velocity")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(figures_dir / "figure8_velocity.png", dpi=160)
    plt.close()


def main() -> None:
    args = parse_args()
    csv_path = args.csv.resolve()
    results_dir = args.results_dir.resolve()
    figures_dir = results_dir / "figures"

    df = load_log(csv_path)
    tracking, _ = select_tracking_stage(df)
    metrics = build_metrics(df, csv_path)

    results_dir.mkdir(parents=True, exist_ok=True)
    write_json(metrics, results_dir / "figure8_metrics.json")
    write_markdown(metrics, results_dir / "figure8_metrics.md")
    save_figures(df, tracking, figures_dir)

    summary = metrics["summary"]
    print("Figure-eight analysis complete")
    print(f"samples={summary['samples']}")
    print(f"frequency_hz={summary['control_frequency_estimate_hz']:.3f}")
    print(f"tracking_filter={metrics['tracking_stage_filter']['criteria']}")
    print(f"tracking_duration_s={summary['tracking_duration_s']:.3f}")
    print(f"tracking_xy_rmse_m={summary['tracking_xy_rmse_m']:.4f}")
    print(f"tracking_z_rmse_m={summary['tracking_z_rmse_m']:.4f}")
    print(f"tracking_position_rmse_m={summary['tracking_position_rmse_m']:.4f}")


if __name__ == "__main__":
    main()
