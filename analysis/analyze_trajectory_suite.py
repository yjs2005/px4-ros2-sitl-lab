#!/usr/bin/env python3
"""Analyze all available Offboard trajectory CSV logs as a trajectory suite."""

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

TRACKING_STAGE_NAMES = {"tracking", "trajectory", "figure8"}


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--logs-dir",
        type=Path,
        default=repo_root / "logs",
        help="Directory containing trajectory CSV logs.",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=repo_root / "results",
        help="Directory for generated suite metrics.",
    )
    return parser.parse_args()


def discover_csvs(logs_dir: Path) -> list[Path]:
    paths: set[Path] = set()
    for pattern in ("trajectory_*.csv", "offboard_trajectory_*.csv"):
        paths.update(logs_dir.glob(pattern))
    figure8 = logs_dir / "figure8_first_success.csv"
    if figure8.exists():
        paths.add(figure8)
    return sorted(paths)


def load_csv(path: Path, logs_dir: Path) -> pd.DataFrame | None:
    df = pd.read_csv(path)
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        return None

    numeric_columns = [column for column in REQUIRED_COLUMNS if column not in {"stage", "trajectory_type"}]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df = df.dropna(subset=numeric_columns)
    if df.empty:
        return None

    df = df.sort_values("timestamp").reset_index(drop=True)
    try:
        source_file = path.relative_to(logs_dir.parent).as_posix()
    except ValueError:
        source_file = path.name
    df["source_file"] = source_file
    df["stage"] = df["stage"].astype(str)
    df["trajectory_type"] = df["trajectory_type"].astype(str).str.strip().str.lower()
    df["stage_normalized"] = df["stage"].str.strip().str.lower()
    df["time_s"] = (df["timestamp"] - df["timestamp"].iloc[0]) / 1_000_000.0
    df["x_error"] = df["x"] - df["target_x"]
    df["y_error"] = df["y"] - df["target_y"]
    df["z_error"] = df["z"] - df["target_z"]
    df["xy_error"] = (df["x_error"] ** 2 + df["y_error"] ** 2) ** 0.5
    df["position_error"] = (df["xy_error"] ** 2 + df["z_error"] ** 2) ** 0.5
    df["speed"] = (df["vx"] ** 2 + df["vy"] ** 2 + df["vz"] ** 2) ** 0.5
    return df


def tracking_rows(df: pd.DataFrame) -> pd.DataFrame:
    by_stage = df[df["stage_normalized"].isin(TRACKING_STAGE_NAMES)].copy()
    same_as_type = df[df["stage_normalized"] == df["trajectory_type"]].copy()
    combined = pd.concat([by_stage, same_as_type], ignore_index=False)
    combined = combined[~combined.index.duplicated(keep="first")]
    return combined.sort_values("timestamp").reset_index(drop=True)


def rmse(series: pd.Series) -> float:
    if series.empty:
        return math.nan
    return float((series.pow(2).mean()) ** 0.5)


def frequency_hz(df: pd.DataFrame) -> float:
    intervals = df["timestamp"].diff().dropna() / 1_000_000.0
    intervals = intervals[intervals > 0]
    if intervals.empty:
        return math.nan
    return float(1.0 / intervals.median())


def duration_sum_s(df: pd.DataFrame) -> float:
    total = 0.0
    for _source, group in df.groupby("source_file"):
        if len(group) < 2:
            continue
        total += float((group["timestamp"].iloc[-1] - group["timestamp"].iloc[0]) / 1_000_000.0)
    return total


def compute_metrics(df: pd.DataFrame) -> dict[str, Any]:
    return {
        "samples": int(len(df)),
        "duration_s": duration_sum_s(df),
        "frequency_hz_median": frequency_hz(df),
        "xy_rmse_m": rmse(df["xy_error"]),
        "xy_mae_m": float(df["xy_error"].mean()),
        "max_xy_error_m": float(df["xy_error"].max()),
        "z_rmse_m": rmse(df["z_error"]),
        "z_mae_m": float(df["z_error"].abs().mean()),
        "position_rmse_m": rmse(df["position_error"]),
        "max_position_error_m": float(df["position_error"].max()),
        "max_speed_mps": float(df["speed"].max()),
        "source_files": sorted(df["source_file"].unique().tolist()),
    }


def build_suite_metrics(logs_dir: Path) -> tuple[dict[str, Any], pd.DataFrame]:
    discovered = discover_csvs(logs_dir)
    loaded: list[pd.DataFrame] = []
    skipped: dict[str, str] = {}

    for path in discovered:
        df = load_csv(path, logs_dir)
        if df is None:
            skipped[path.as_posix()] = "missing required columns or no numeric samples"
            continue
        rows = tracking_rows(df)
        if rows.empty:
            skipped[path.as_posix()] = "no inferred tracking-stage rows"
            continue
        loaded.append(rows)

    if not loaded:
        raise ValueError("No usable trajectory tracking CSV logs found.")

    suite_df = pd.concat(loaded, ignore_index=True)
    metrics_by_type = {
        trajectory_type: compute_metrics(group)
        for trajectory_type, group in suite_df.groupby("trajectory_type", sort=True)
    }
    suite = {
        "source_patterns": [
            "logs/trajectory_*.csv",
            "logs/offboard_trajectory_*.csv",
            "logs/figure8_first_success.csv",
        ],
        "tracking_stage_inference": (
            "rows where stage is tracking/trajectory/figure8, or where stage equals trajectory_type"
        ),
        "discovered_files": [path.as_posix() for path in discovered],
        "skipped_files": skipped,
        "metrics_by_trajectory_type": metrics_by_type,
    }
    return suite, suite_df


def write_json(metrics: dict[str, Any], output_path: Path) -> None:
    output_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")


def write_csv(metrics: dict[str, Any], output_path: Path) -> None:
    rows = []
    for trajectory_type, values in metrics["metrics_by_trajectory_type"].items():
        row = {"trajectory_type": trajectory_type}
        for key, value in values.items():
            if key != "source_files":
                row[key] = value
        row["source_files"] = ";".join(values["source_files"])
        rows.append(row)
    pd.DataFrame(rows).to_csv(output_path, index=False)


def fmt(value: float, digits: int = 4) -> str:
    if value is None or math.isnan(float(value)):
        return "n/a"
    return f"{float(value):.{digits}f}"


def write_markdown(metrics: dict[str, Any], output_path: Path) -> None:
    lines = [
        "# Trajectory Suite Metrics",
        "",
        "This summary scans committed or future trajectory CSV logs without overwriting individual hover or figure-eight analyses.",
        "",
        "Tracking-stage inference:",
        "",
        f"`{metrics['tracking_stage_inference']}`",
        "",
        "## Metrics",
        "",
        "| Trajectory | Samples | Duration (s) | XY RMSE (m) | XY MAE (m) | Max XY (m) | z RMSE (m) | z MAE (m) | 3D RMSE (m) | Max 3D (m) | Max speed (m/s) |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for trajectory_type, values in metrics["metrics_by_trajectory_type"].items():
        lines.append(
            "| %s | %d | %s | %s | %s | %s | %s | %s | %s | %s | %s |"
            % (
                trajectory_type,
                values["samples"],
                fmt(values["duration_s"], 3),
                fmt(values["xy_rmse_m"], 4),
                fmt(values["xy_mae_m"], 4),
                fmt(values["max_xy_error_m"], 4),
                fmt(values["z_rmse_m"], 4),
                fmt(values["z_mae_m"], 4),
                fmt(values["position_rmse_m"], 4),
                fmt(values["max_position_error_m"], 4),
                fmt(values["max_speed_mps"], 4),
            )
        )

    lines.extend(["", "## Source Files", ""])
    for trajectory_type, values in metrics["metrics_by_trajectory_type"].items():
        lines.append(f"- `{trajectory_type}`:")
        for source in values["source_files"]:
            lines.append(f"  - `{source}`")
    if metrics["skipped_files"]:
        lines.extend(["", "## Skipped Files", ""])
        for source, reason in metrics["skipped_files"].items():
            lines.append(f"- `{source}`: {reason}")
    lines.extend(
        [
            "",
            "## Figure",
            "",
            "- `results/figures/trajectory_suite_metrics.png`",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def save_figure(metrics: dict[str, Any], output_path: Path) -> None:
    trajectories = list(metrics["metrics_by_trajectory_type"].keys())
    xy_values = [metrics["metrics_by_trajectory_type"][name]["xy_rmse_m"] for name in trajectories]
    z_values = [metrics["metrics_by_trajectory_type"][name]["z_rmse_m"] for name in trajectories]
    pos_values = [metrics["metrics_by_trajectory_type"][name]["position_rmse_m"] for name in trajectories]

    x = range(len(trajectories))
    width = 0.24
    plt.figure(figsize=(9, 5.2))
    plt.bar([i - width for i in x], xy_values, width=width, label="XY RMSE")
    plt.bar(list(x), z_values, width=width, label="z RMSE")
    plt.bar([i + width for i in x], pos_values, width=width, label="3D RMSE")
    plt.xticks(list(x), trajectories)
    plt.ylabel("Error (m)")
    plt.title("Trajectory Suite Tracking Error Summary")
    plt.grid(axis="y", alpha=0.25)
    plt.legend()
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=170)
    plt.close()


def main() -> None:
    args = parse_args()
    logs_dir = args.logs_dir.resolve()
    results_dir = args.results_dir.resolve()
    metrics, _suite_df = build_suite_metrics(logs_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    write_json(metrics, results_dir / "trajectory_suite_metrics.json")
    write_csv(metrics, results_dir / "trajectory_suite_metrics.csv")
    write_markdown(metrics, results_dir / "trajectory_suite_metrics.md")
    save_figure(metrics, results_dir / "figures" / "trajectory_suite_metrics.png")

    print("Trajectory suite analysis complete")
    print(f"trajectory_types={','.join(metrics['metrics_by_trajectory_type'].keys())}")
    print(f"metrics_md={results_dir / 'trajectory_suite_metrics.md'}")
    print(f"metrics_csv={results_dir / 'trajectory_suite_metrics.csv'}")
    print(f"metrics_json={results_dir / 'trajectory_suite_metrics.json'}")
    print(f"figure={results_dir / 'figures' / 'trajectory_suite_metrics.png'}")


if __name__ == "__main__":
    main()
