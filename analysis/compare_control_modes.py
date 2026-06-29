#!/usr/bin/env python3
"""Compare baseline, feedforward, and smooth Offboard trajectory logs."""

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


CONTROLLER_MODES = ("baseline", "feedforward", "smooth")
TRACKING_STAGE_NAMES = {"tracking", "trajectory", "figure8", "line", "circle", "square", "z_step"}
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
    "target_vx",
    "target_vy",
    "target_vz",
    "stage",
    "trajectory_type",
    "controller_mode",
    "position_error_xy",
    "position_error_3d",
]


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--logs-dir", type=Path, default=repo_root / "logs")
    parser.add_argument("--results-dir", type=Path, default=repo_root / "results")
    return parser.parse_args()


def discover_logs(logs_dir: Path) -> list[Path]:
    paths: set[Path] = set()
    for mode in CONTROLLER_MODES:
        paths.update(logs_dir.glob(f"offboard_trajectory_*_{mode}_*.csv"))
    return sorted(paths)


def load_log(path: Path, repo_root: Path) -> tuple[pd.DataFrame | None, str | None]:
    df = pd.read_csv(path)
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        return None, f"missing required columns: {missing}"

    numeric_columns = [column for column in REQUIRED_COLUMNS if column not in {"stage", "trajectory_type", "controller_mode"}]
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
    if df.empty:
        return None, "no numeric samples"

    df = df.sort_values("timestamp").reset_index(drop=True)
    df["stage"] = df["stage"].astype(str)
    df["trajectory_type"] = df["trajectory_type"].astype(str).str.strip().str.lower()
    df["controller_mode"] = df["controller_mode"].astype(str).str.strip().str.lower()
    df["stage_normalized"] = df["stage"].str.strip().str.lower()
    try:
        df["source_file"] = path.relative_to(repo_root).as_posix()
    except ValueError:
        df["source_file"] = path.as_posix()
    df["time_s"] = (df["timestamp"] - df["timestamp"].iloc[0]) / 1_000_000.0
    df["x_error"] = df["x"] - df["target_x"]
    df["y_error"] = df["y"] - df["target_y"]
    df["z_error"] = df["z"] - df["target_z"]
    df["xy_error"] = (df["x_error"] ** 2 + df["y_error"] ** 2) ** 0.5
    df["position_error"] = (df["xy_error"] ** 2 + df["z_error"] ** 2) ** 0.5
    df["speed"] = (df["vx"] ** 2 + df["vy"] ** 2 + df["vz"] ** 2) ** 0.5
    return df, None


def tracking_rows(df: pd.DataFrame) -> pd.DataFrame:
    rows = df[
        df["stage_normalized"].isin(TRACKING_STAGE_NAMES)
        | (df["stage_normalized"] == df["trajectory_type"])
    ].copy()
    return rows.sort_values("timestamp").reset_index(drop=True)


def rmse(series: pd.Series) -> float:
    if series.empty:
        return math.nan
    return float((series.pow(2).mean()) ** 0.5)


def duration_sum_s(df: pd.DataFrame) -> float:
    total = 0.0
    for _source, group in df.groupby("source_file"):
        if len(group) > 1:
            total += float((group["timestamp"].iloc[-1] - group["timestamp"].iloc[0]) / 1_000_000.0)
    return total


def final_error_before_landing(df: pd.DataFrame) -> float:
    final_errors = []
    for _source, group in df.groupby("source_file"):
        if not group.empty:
            final_errors.append(float(group["position_error"].iloc[-1]))
    if not final_errors:
        return math.nan
    return float(sum(final_errors) / len(final_errors))


def compute_metrics(df: pd.DataFrame) -> dict[str, Any]:
    return {
        "samples": int(len(df)),
        "duration_s": duration_sum_s(df),
        "xy_rmse_m": rmse(df["xy_error"]),
        "xy_mae_m": float(df["xy_error"].mean()),
        "max_xy_error_m": float(df["xy_error"].max()),
        "z_rmse_m": rmse(df["z_error"]),
        "z_mae_m": float(df["z_error"].abs().mean()),
        "position_rmse_m": rmse(df["position_error"]),
        "max_position_error_m": float(df["position_error"].max()),
        "final_position_error_before_landing_m": final_error_before_landing(df),
        "max_speed_mps": float(df["speed"].max()),
        "source_files": sorted(df["source_file"].unique().tolist()),
    }


def percent_improvement(baseline: float, improved: float) -> float:
    if baseline is None or improved is None or math.isnan(baseline) or math.isnan(improved) or baseline == 0.0:
        return math.nan
    return float((baseline - improved) / baseline * 100.0)


def build_comparison(logs_dir: Path) -> dict[str, Any]:
    repo_root = logs_dir.parent
    discovered = discover_logs(logs_dir)
    skipped: dict[str, str] = {}
    loaded: list[pd.DataFrame] = []

    for path in discovered:
        df, reason = load_log(path, repo_root)
        if df is None:
            skipped[path.relative_to(repo_root).as_posix()] = reason or "failed to load"
            continue
        rows = tracking_rows(df)
        if rows.empty:
            skipped[path.relative_to(repo_root).as_posix()] = "no inferred tracking-stage rows"
            continue
        loaded.append(rows)

    if loaded:
        all_rows = pd.concat(loaded, ignore_index=True)
        metrics = {
            f"{trajectory_type}:{controller_mode}": {
                "trajectory_type": trajectory_type,
                "controller_mode": controller_mode,
                **compute_metrics(group),
            }
            for (trajectory_type, controller_mode), group in all_rows.groupby(
                ["trajectory_type", "controller_mode"], sort=True
            )
        }
    else:
        metrics = {}

    improvements: list[dict[str, Any]] = []
    trajectories = sorted({value["trajectory_type"] for value in metrics.values()})
    for trajectory in trajectories:
        baseline = metrics.get(f"{trajectory}:baseline")
        if baseline is None:
            continue
        for mode in ("feedforward", "smooth"):
            improved = metrics.get(f"{trajectory}:{mode}")
            if improved is None:
                continue
            improvements.append(
                {
                    "trajectory_type": trajectory,
                    "improved_mode": mode,
                    "xy_rmse_improvement_percent": percent_improvement(
                        baseline["xy_rmse_m"], improved["xy_rmse_m"]
                    ),
                    "z_rmse_improvement_percent": percent_improvement(
                        baseline["z_rmse_m"], improved["z_rmse_m"]
                    ),
                    "position_rmse_improvement_percent": percent_improvement(
                        baseline["position_rmse_m"], improved["position_rmse_m"]
                    ),
                    "max_error_improvement_percent": percent_improvement(
                        baseline["max_position_error_m"], improved["max_position_error_m"]
                    ),
                }
            )

    return {
        "source_patterns": [
            "logs/offboard_trajectory_*_baseline_*.csv",
            "logs/offboard_trajectory_*_feedforward_*.csv",
            "logs/offboard_trajectory_*_smooth_*.csv",
        ],
        "tracking_stage_inference": (
            "rows where stage is tracking/trajectory/figure8/line/circle/square/z_step, "
            "or where stage equals trajectory_type"
        ),
        "discovered_files": [path.relative_to(repo_root).as_posix() for path in discovered],
        "skipped_files": skipped,
        "metrics_by_trajectory_and_mode": metrics,
        "paired_improvements": improvements,
        "message": (
            "No paired baseline/improved logs found yet. Run paired SITL experiments first."
            if not improvements
            else "Paired baseline/improved logs found."
        ),
    }


def write_json(data: dict[str, Any], output_path: Path) -> None:
    output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def write_metrics_csv(data: dict[str, Any], output_path: Path) -> None:
    rows = []
    for values in data["metrics_by_trajectory_and_mode"].values():
        row = {key: value for key, value in values.items() if key != "source_files"}
        row["source_files"] = ";".join(values["source_files"])
        rows.append(row)
    columns = [
        "trajectory_type",
        "controller_mode",
        "samples",
        "duration_s",
        "xy_rmse_m",
        "xy_mae_m",
        "max_xy_error_m",
        "z_rmse_m",
        "z_mae_m",
        "position_rmse_m",
        "max_position_error_m",
        "final_position_error_before_landing_m",
        "max_speed_mps",
        "source_files",
    ]
    pd.DataFrame(rows, columns=columns).to_csv(output_path, index=False)


def fmt(value: float, digits: int = 4) -> str:
    if value is None or math.isnan(float(value)):
        return "n/a"
    return f"{float(value):.{digits}f}"


def write_markdown(data: dict[str, Any], output_path: Path) -> None:
    lines = [
        "# Control Mode Comparison Metrics",
        "",
        data["message"],
        "",
        "This analysis only uses logs that explicitly include a `controller_mode` column and match the new `offboard_trajectory_*_<mode>_*.csv` naming pattern.",
        "",
        "## Metrics By Trajectory And Mode",
        "",
        "| Trajectory | Mode | Samples | Duration (s) | XY RMSE (m) | z RMSE (m) | 3D RMSE (m) | Max 3D (m) | Final before landing (m) | Max speed (m/s) |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for values in data["metrics_by_trajectory_and_mode"].values():
        lines.append(
            "| %s | %s | %d | %s | %s | %s | %s | %s | %s | %s |"
            % (
                values["trajectory_type"],
                values["controller_mode"],
                values["samples"],
                fmt(values["duration_s"], 3),
                fmt(values["xy_rmse_m"], 4),
                fmt(values["z_rmse_m"], 4),
                fmt(values["position_rmse_m"], 4),
                fmt(values["max_position_error_m"], 4),
                fmt(values["final_position_error_before_landing_m"], 4),
                fmt(values["max_speed_mps"], 4),
            )
        )

    if not data["metrics_by_trajectory_and_mode"]:
        lines.append("| n/a | n/a | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |")

    lines.extend(
        [
            "",
            "## Paired Improvements",
            "",
            "| Trajectory | Improved mode | XY RMSE improvement | z RMSE improvement | 3D RMSE improvement | Max error improvement |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in data["paired_improvements"]:
        lines.append(
            "| %s | %s | %s%% | %s%% | %s%% | %s%% |"
            % (
                row["trajectory_type"],
                row["improved_mode"],
                fmt(row["xy_rmse_improvement_percent"], 2),
                fmt(row["z_rmse_improvement_percent"], 2),
                fmt(row["position_rmse_improvement_percent"], 2),
                fmt(row["max_error_improvement_percent"], 2),
            )
        )
    if not data["paired_improvements"]:
        lines.append("| n/a | n/a | n/a | n/a | n/a | n/a |")

    lines.extend(
        [
            "",
            "## Figures",
            "",
            "- `results/figures/control_comparison_xy_rmse.png`",
            "- `results/figures/control_comparison_3d_rmse.png`",
            "- `results/figures/control_comparison_percent_improvement.png`",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def plot_metric(data: dict[str, Any], metric_key: str, title: str, ylabel: str, output_path: Path) -> None:
    rows = list(data["metrics_by_trajectory_and_mode"].values())
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(9, 5.2))
    if not rows:
        plt.text(0.5, 0.5, "No control-mode logs found yet", ha="center", va="center")
        plt.axis("off")
    else:
        labels = [f"{row['trajectory_type']}\n{row['controller_mode']}" for row in rows]
        values = [row[metric_key] for row in rows]
        plt.bar(labels, values, color="#3b82f6", edgecolor="#1f2937", linewidth=0.7)
        plt.ylabel(ylabel)
        plt.title(title)
        plt.grid(axis="y", alpha=0.25)
        plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(output_path, dpi=170)
    plt.close()


def plot_improvements(data: dict[str, Any], output_path: Path) -> None:
    rows = data["paired_improvements"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(9, 5.2))
    if not rows:
        plt.text(
            0.5,
            0.5,
            "No paired baseline/improved logs found yet.\nRun paired SITL experiments first.",
            ha="center",
            va="center",
        )
        plt.axis("off")
    else:
        labels = [f"{row['trajectory_type']}\n{row['improved_mode']}" for row in rows]
        values = [row["position_rmse_improvement_percent"] for row in rows]
        plt.bar(labels, values, color="#22c55e", edgecolor="#1f2937", linewidth=0.7)
        plt.axhline(0.0, color="#111827", linewidth=0.8)
        plt.ylabel("3D RMSE improvement (%)")
        plt.title("Control Mode Percent Improvement")
        plt.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    plt.savefig(output_path, dpi=170)
    plt.close()


def main() -> None:
    args = parse_args()
    logs_dir = args.logs_dir.resolve()
    results_dir = args.results_dir.resolve()
    figures_dir = results_dir / "figures"
    data = build_comparison(logs_dir)

    results_dir.mkdir(parents=True, exist_ok=True)
    write_json(data, results_dir / "control_comparison_metrics.json")
    write_metrics_csv(data, results_dir / "control_comparison_metrics.csv")
    write_markdown(data, results_dir / "control_comparison_metrics.md")
    plot_metric(
        data,
        "xy_rmse_m",
        "Control Mode XY RMSE Comparison",
        "XY RMSE (m)",
        figures_dir / "control_comparison_xy_rmse.png",
    )
    plot_metric(
        data,
        "position_rmse_m",
        "Control Mode 3D RMSE Comparison",
        "3D RMSE (m)",
        figures_dir / "control_comparison_3d_rmse.png",
    )
    plot_improvements(data, figures_dir / "control_comparison_percent_improvement.png")

    print(data["message"])
    print(f"discovered_logs={len(data['discovered_files'])}")
    print(f"paired_improvements={len(data['paired_improvements'])}")
    print(f"metrics_md={results_dir / 'control_comparison_metrics.md'}")


if __name__ == "__main__":
    main()
