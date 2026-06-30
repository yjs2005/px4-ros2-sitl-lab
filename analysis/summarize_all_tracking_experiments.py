#!/usr/bin/env python3
"""Summarize all completed PX4 Offboard tracking comparison experiments."""

from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


TRACKING_STAGE_NAMES = {"tracking", "trajectory", "circle", "square", "figure8"}
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
    "controller_mode",
]

EXPERIMENTS: list[dict[str, Any]] = [
    {
        "key": "circle_baseline",
        "trajectory": "circle",
        "mode": "baseline",
        "label": "circle baseline",
        "pattern": "offboard_trajectory_circle_baseline_*.csv",
    },
    {
        "key": "circle_feedforward",
        "trajectory": "circle",
        "mode": "feedforward",
        "label": "circle feedforward",
        "pattern": "offboard_trajectory_circle_feedforward_*.csv",
    },
    {
        "key": "square_baseline",
        "trajectory": "square",
        "mode": "baseline",
        "label": "square baseline",
        "pattern": "offboard_trajectory_square_baseline_*.csv",
    },
    {
        "key": "square_smooth",
        "trajectory": "square",
        "mode": "smooth",
        "label": "square smooth",
        "pattern": "offboard_trajectory_square_smooth_*.csv",
    },
    {
        "key": "figure8_baseline",
        "trajectory": "figure8",
        "mode": "baseline",
        "label": "figure8 baseline",
        "pattern": "offboard_trajectory_figure8_baseline_*.csv",
    },
    {
        "key": "figure8_feedforward",
        "trajectory": "figure8",
        "mode": "feedforward",
        "label": "figure8 feedforward",
        "pattern": "offboard_trajectory_figure8_feedforward_*.csv",
    },
    {
        "key": "figure8_planar_ff_g0p5",
        "trajectory": "figure8",
        "mode": "planar_ff_g0p5",
        "label": "figure8 planar_ff g=0.5",
        "pattern": "offboard_trajectory_figure8_planar_ff_g0p5_*.csv",
    },
    {
        "key": "figure8_planar_ff_g0p8",
        "trajectory": "figure8",
        "mode": "planar_ff_g0p8",
        "label": "figure8 planar_ff g=0.8",
        "pattern": "offboard_trajectory_figure8_planar_ff_g0p8_*.csv",
    },
    {
        "key": "figure8_planar_ff_g1",
        "trajectory": "figure8",
        "mode": "planar_ff_g1",
        "label": "figure8 planar_ff g=1.0",
        "pattern": "offboard_trajectory_figure8_planar_ff_g1_*.csv",
    },
]

IMPROVEMENT_PAIRS = [
    ("circle feedforward vs baseline", "circle_baseline", "circle_feedforward"),
    ("square smooth vs baseline", "square_baseline", "square_smooth"),
    ("figure8 feedforward vs baseline", "figure8_baseline", "figure8_feedforward"),
    ("figure8 planar_ff g=0.5 vs baseline", "figure8_baseline", "figure8_planar_ff_g0p5"),
    ("figure8 planar_ff g=0.8 vs baseline", "figure8_baseline", "figure8_planar_ff_g0p8"),
    ("figure8 planar_ff g=1.0 vs baseline", "figure8_baseline", "figure8_planar_ff_g1"),
    ("figure8 planar_ff g=0.5 vs feedforward", "figure8_feedforward", "figure8_planar_ff_g0p5"),
    ("figure8 planar_ff g=0.8 vs feedforward", "figure8_feedforward", "figure8_planar_ff_g0p8"),
    ("figure8 planar_ff g=1.0 vs feedforward", "figure8_feedforward", "figure8_planar_ff_g1"),
]

FIGURE_FILES = [
    "all_tracking_xy_rmse.png",
    "all_tracking_3d_rmse.png",
    "all_tracking_z_rmse.png",
    "all_tracking_xy_error_std.png",
    "all_tracking_3d_error_std.png",
    "all_tracking_final_error.png",
    "all_tracking_improvement_summary.png",
    "circle_xy_tracking_comparison.png",
    "square_xy_tracking_comparison.png",
    "figure8_xy_tracking_comparison.png",
    "figure8_planar_ff_gain_xy_tracking_comparison.png",
    "circle_error_timeseries.png",
    "square_error_timeseries.png",
    "figure8_error_timeseries.png",
    "figure8_planar_ff_gain_error_timeseries.png",
    "circle_error_std_comparison.png",
    "square_error_std_comparison.png",
    "figure8_error_std_comparison.png",
]

COLORS = {
    "baseline": "#6b7280",
    "feedforward": "#2563eb",
    "smooth": "#9333ea",
    "planar_ff_g0p5": "#16a34a",
    "planar_ff_g0p8": "#22c55e",
    "planar_ff_g1": "#84cc16",
}


@dataclass(frozen=True)
class ExperimentData:
    spec: dict[str, Any]
    path: Path
    rows: pd.DataFrame
    metrics: dict[str, Any]


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--logs-dir", type=Path, default=repo_root / "logs")
    parser.add_argument("--results-dir", type=Path, default=repo_root / "results")
    return parser.parse_args()


def timestamp_key(path: Path) -> tuple[str, float]:
    match = re.search(r"_(\d{8}_\d{6})\.csv$", path.name)
    return (match.group(1) if match else "", path.stat().st_mtime)


def select_latest_csv(logs_dir: Path, pattern: str) -> Path | None:
    candidates = sorted(logs_dir.glob(pattern), key=timestamp_key)
    return candidates[-1] if candidates else None


def load_tracking_rows(path: Path, trajectory: str, repo_root: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"missing required columns: {missing}")

    if "ff_gain" not in df.columns:
        df["ff_gain"] = 1.0

    numeric_columns = [
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
        "ff_gain",
    ]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df = df.dropna(subset=numeric_columns[:-1])
    if df.empty:
        raise ValueError("no numeric samples")

    df = df.sort_values("timestamp").reset_index(drop=True)
    df["stage"] = df["stage"].astype(str)
    df["trajectory_type"] = df["trajectory_type"].astype(str).str.strip().str.lower()
    df["controller_mode"] = df["controller_mode"].astype(str).str.strip().str.lower()
    df["stage_normalized"] = df["stage"].str.strip().str.lower()
    rows = df[
        (df["trajectory_type"] == trajectory)
        & (
            df["stage_normalized"].isin(TRACKING_STAGE_NAMES)
            | (df["stage_normalized"] == trajectory)
        )
    ].copy()
    if rows.empty:
        raise ValueError("no tracking-stage rows")

    rows["time_s"] = (rows["timestamp"] - rows["timestamp"].iloc[0]) / 1_000_000.0
    rows["x_error"] = rows["x"] - rows["target_x"]
    rows["y_error"] = rows["y"] - rows["target_y"]
    rows["z_error"] = rows["z"] - rows["target_z"]
    rows["abs_z_error"] = rows["z_error"].abs()
    rows["xy_error"] = (rows["x_error"] ** 2 + rows["y_error"] ** 2) ** 0.5
    rows["position_error"] = (rows["xy_error"] ** 2 + rows["z_error"] ** 2) ** 0.5
    rows["speed"] = (rows["vx"] ** 2 + rows["vy"] ** 2 + rows["vz"] ** 2) ** 0.5
    try:
        rows["source_file"] = path.relative_to(repo_root).as_posix()
    except ValueError:
        rows["source_file"] = path.as_posix()
    return rows.reset_index(drop=True)


def rmse(series: pd.Series) -> float:
    return float((series.pow(2).mean()) ** 0.5) if not series.empty else math.nan


def std(series: pd.Series) -> float:
    return float(series.std(ddof=0)) if not series.empty else math.nan


def compute_metrics(spec: dict[str, Any], path: Path, rows: pd.DataFrame) -> dict[str, Any]:
    return {
        "key": spec["key"],
        "trajectory": spec["trajectory"],
        "mode": spec["mode"],
        "label": spec["label"],
        "selected_csv": path.as_posix(),
        "samples": int(len(rows)),
        "duration_s": float((rows["timestamp"].iloc[-1] - rows["timestamp"].iloc[0]) / 1_000_000.0),
        "xy_rmse_m": rmse(rows["xy_error"]),
        "xy_mae_m": float(rows["xy_error"].mean()),
        "xy_error_std_m": std(rows["xy_error"]),
        "z_rmse_m": rmse(rows["z_error"]),
        "z_mae_m": float(rows["abs_z_error"].mean()),
        "z_error_std_m": std(rows["abs_z_error"]),
        "position_rmse_m": rmse(rows["position_error"]),
        "position_mae_m": float(rows["position_error"].mean()),
        "position_error_std_m": std(rows["position_error"]),
        "max_position_error_m": float(rows["position_error"].max()),
        "final_position_error_before_landing_m": float(rows["position_error"].iloc[-1]),
        "max_speed_mps": float(rows["speed"].max()),
    }


def load_all(logs_dir: Path) -> tuple[dict[str, ExperimentData], list[dict[str, Any]]]:
    repo_root = logs_dir.parent
    loaded: dict[str, ExperimentData] = {}
    missing: list[dict[str, Any]] = []
    for spec in EXPERIMENTS:
        selected = select_latest_csv(logs_dir, spec["pattern"])
        if selected is None:
            missing.append(
                {
                    "key": spec["key"],
                    "trajectory": spec["trajectory"],
                    "mode": spec["mode"],
                    "pattern": spec["pattern"],
                    "notes": "missing CSV",
                }
            )
            continue
        try:
            rows = load_tracking_rows(selected, spec["trajectory"], repo_root)
        except Exception as exc:  # noqa: BLE001 - report invalid logs without aborting.
            missing.append(
                {
                    "key": spec["key"],
                    "trajectory": spec["trajectory"],
                    "mode": spec["mode"],
                    "pattern": spec["pattern"],
                    "selected_csv": selected.relative_to(repo_root).as_posix(),
                    "notes": str(exc),
                }
            )
            continue
        rel_path = selected.relative_to(repo_root)
        metrics = compute_metrics(spec, rel_path, rows)
        loaded[spec["key"]] = ExperimentData(spec=spec, path=rel_path, rows=rows, metrics=metrics)
    return loaded, missing


def percent_improvement(reference: float, candidate: float) -> float:
    if reference == 0.0 or math.isnan(reference) or math.isnan(candidate):
        return math.nan
    return float((reference - candidate) / reference * 100.0)


def build_improvements(loaded: dict[str, ExperimentData]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    metric_keys = [
        "xy_rmse_m",
        "z_rmse_m",
        "position_rmse_m",
        "max_position_error_m",
        "final_position_error_before_landing_m",
        "xy_error_std_m",
        "position_error_std_m",
        "max_speed_mps",
    ]
    for label, reference_key, candidate_key in IMPROVEMENT_PAIRS:
        reference = loaded.get(reference_key)
        candidate = loaded.get(candidate_key)
        row: dict[str, Any] = {
            "comparison": label,
            "reference": reference.metrics["label"] if reference else reference_key,
            "candidate": candidate.metrics["label"] if candidate else candidate_key,
            "whether_valid": bool(reference and candidate),
        }
        if not reference or not candidate:
            row["notes"] = "missing reference or candidate CSV"
            for metric_key in metric_keys:
                row[f"{metric_key}_improvement_percent"] = math.nan
            rows.append(row)
            continue
        row["notes"] = ""
        for metric_key in metric_keys:
            row[f"{metric_key}_improvement_percent"] = percent_improvement(
                float(reference.metrics[metric_key]),
                float(candidate.metrics[metric_key]),
            )
        rows.append(row)
    return rows


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def fmt(value: Any, digits: int = 3) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    if math.isnan(numeric):
        return "n/a"
    return f"{numeric:.{digits}f}"


def fmt_percent(value: Any) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "n/a"
    if math.isnan(numeric):
        return "n/a"
    return f"{numeric:.2f}%"


def write_metrics_markdown(metrics: list[dict[str, Any]], output_path: Path) -> None:
    lines = [
        "# All Tracking Metrics",
        "",
        "Metrics are computed on tracking-stage rows only. `z error std` is the standard deviation of absolute z error.",
        "",
        "| Trajectory | Mode | Samples | Duration (s) | XY RMSE | XY MAE | XY std | z RMSE | z MAE | z std | 3D RMSE | 3D MAE | 3D std | Max 3D | Final error | Max speed |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in metrics:
        lines.append(
            "| %s | %s | %d | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |"
            % (
                row["trajectory"],
                row["mode"],
                row["samples"],
                fmt(row["duration_s"]),
                fmt(row["xy_rmse_m"]),
                fmt(row["xy_mae_m"]),
                fmt(row["xy_error_std_m"]),
                fmt(row["z_rmse_m"]),
                fmt(row["z_mae_m"]),
                fmt(row["z_error_std_m"]),
                fmt(row["position_rmse_m"]),
                fmt(row["position_mae_m"]),
                fmt(row["position_error_std_m"]),
                fmt(row["max_position_error_m"]),
                fmt(row["final_position_error_before_landing_m"]),
                fmt(row["max_speed_mps"]),
            )
        )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_improvements_markdown(rows: list[dict[str, Any]], output_path: Path) -> None:
    lines = [
        "# All Tracking Improvements",
        "",
        "Positive percentages mean the candidate metric is lower than the reference metric.",
        "",
        "| Comparison | XY RMSE | z RMSE | 3D RMSE | Max 3D | Final error | XY std | 3D std | Notes |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| %s | %s | %s | %s | %s | %s | %s | %s | %s |"
            % (
                row["comparison"],
                fmt_percent(row["xy_rmse_m_improvement_percent"]),
                fmt_percent(row["z_rmse_m_improvement_percent"]),
                fmt_percent(row["position_rmse_m_improvement_percent"]),
                fmt_percent(row["max_position_error_m_improvement_percent"]),
                fmt_percent(row["final_position_error_before_landing_m_improvement_percent"]),
                fmt_percent(row["xy_error_std_m_improvement_percent"]),
                fmt_percent(row["position_error_std_m_improvement_percent"]),
                row.get("notes", ""),
            )
        )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tables(loaded: dict[str, ExperimentData], missing: list[dict[str, Any]], results_dir: Path) -> None:
    metrics = [loaded[spec["key"]].metrics for spec in EXPERIMENTS if spec["key"] in loaded]
    improvements = build_improvements(loaded)

    pd.DataFrame(metrics).to_csv(results_dir / "all_tracking_metrics.csv", index=False)
    write_json(results_dir / "all_tracking_metrics.json", {"metrics": metrics, "missing": missing})
    write_metrics_markdown(metrics, results_dir / "all_tracking_metrics.md")

    pd.DataFrame(improvements).to_csv(results_dir / "all_tracking_improvements.csv", index=False)
    write_json(results_dir / "all_tracking_improvements.json", {"improvements": improvements})
    write_improvements_markdown(improvements, results_dir / "all_tracking_improvements.md")


def display_label(data: ExperimentData) -> str:
    return data.metrics["mode"].replace("_", " ")


def plot_bar(
    loaded: dict[str, ExperimentData],
    metric_key: str,
    title: str,
    ylabel: str,
    output_path: Path,
) -> None:
    rows = [loaded[spec["key"]] for spec in EXPERIMENTS if spec["key"] in loaded]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(11, 5.6))
    if not rows:
        plt.text(0.5, 0.5, "No valid logs", ha="center", va="center")
        plt.axis("off")
    else:
        labels = [f"{row.metrics['trajectory']}\n{display_label(row)}" for row in rows]
        values = [row.metrics[metric_key] for row in rows]
        colors = [COLORS.get(row.spec["mode"], "#64748b") for row in rows]
        plt.bar(labels, values, color=colors, edgecolor="#1f2937", linewidth=0.7)
        plt.ylabel(ylabel)
        plt.title(title)
        plt.grid(axis="y", alpha=0.25)
        plt.xticks(rotation=0, fontsize=8)
    plt.tight_layout()
    plt.savefig(output_path, dpi=180)
    plt.close()


def plot_improvement_summary(improvements: list[dict[str, Any]], output_path: Path) -> None:
    rows = [row for row in improvements if row.get("whether_valid")]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(12, 6.2))
    if not rows:
        plt.text(0.5, 0.5, "No valid paired comparisons", ha="center", va="center")
        plt.axis("off")
    else:
        labels = [row["comparison"].replace(" vs ", "\nvs ") for row in rows]
        x = list(range(len(rows)))
        width = 0.25
        series = [
            ("XY RMSE", "xy_rmse_m_improvement_percent", "#2563eb"),
            ("z RMSE", "z_rmse_m_improvement_percent", "#f97316"),
            ("3D RMSE", "position_rmse_m_improvement_percent", "#16a34a"),
        ]
        for offset, (name, key, color) in zip([-width, 0.0, width], series):
            values = [row[key] for row in rows]
            plt.bar([pos + offset for pos in x], values, width=width, label=name, color=color)
        plt.axhline(0.0, color="#111827", linewidth=0.8)
        plt.ylabel("Improvement vs reference (%)")
        plt.title("Tracking Improvement Summary")
        plt.xticks(x, labels, rotation=35, ha="right", fontsize=8)
        plt.grid(axis="y", alpha=0.25)
        plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=180)
    plt.close()


def plot_xy_comparison(
    loaded: dict[str, ExperimentData],
    keys: list[str],
    title: str,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    present = [loaded[key] for key in keys if key in loaded]
    plt.figure(figsize=(7.2, 6.4))
    if not present:
        plt.text(0.5, 0.5, "No valid logs", ha="center", va="center")
        plt.axis("off")
    else:
        ref = present[0].rows
        plt.plot(ref["target_x"], ref["target_y"], "--", color="#111827", linewidth=1.5, label="target XY")
        for item in present:
            plt.plot(
                item.rows["x"],
                item.rows["y"],
                linewidth=1.2,
                color=COLORS.get(item.spec["mode"], None),
                label=display_label(item),
            )
        plt.xlabel("NED x (m)")
        plt.ylabel("NED y (m)")
        plt.title(title)
        plt.axis("equal")
        plt.grid(alpha=0.25)
        plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(output_path, dpi=180)
    plt.close()


def plot_error_timeseries(
    loaded: dict[str, ExperimentData],
    keys: list[str],
    title: str,
    output_path: Path,
    include_z: bool,
) -> None:
    present = [loaded[key] for key in keys if key in loaded]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    nrows = 3 if include_z else 2
    fig, axes = plt.subplots(nrows, 1, figsize=(10, 7.4 if include_z else 5.4), sharex=True)
    if nrows == 1:
        axes = [axes]
    if not present:
        axes[0].text(0.5, 0.5, "No valid logs", ha="center", va="center")
        axes[0].axis("off")
    else:
        plots = [("xy_error", "XY error (m)")]
        if include_z:
            plots.append(("abs_z_error", "|z error| (m)"))
        plots.append(("position_error", "3D error (m)"))
        for ax, (column, ylabel) in zip(axes, plots):
            for item in present:
                ax.plot(
                    item.rows["time_s"],
                    item.rows[column],
                    linewidth=1.1,
                    color=COLORS.get(item.spec["mode"], None),
                    label=display_label(item),
                )
            ax.set_ylabel(ylabel)
            ax.grid(alpha=0.25)
        axes[0].set_title(title)
        axes[-1].set_xlabel("Tracking time (s)")
        axes[0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_error_std(
    loaded: dict[str, ExperimentData],
    keys: list[str],
    title: str,
    output_path: Path,
) -> None:
    present = [loaded[key] for key in keys if key in loaded]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(7.8, 5.0))
    if not present:
        plt.text(0.5, 0.5, "No valid logs", ha="center", va="center")
        plt.axis("off")
    else:
        labels = [display_label(item) for item in present]
        x = list(range(len(present)))
        width = 0.25
        series = [
            ("XY std", "xy_error_std_m", "#2563eb"),
            ("z std", "z_error_std_m", "#f97316"),
            ("3D std", "position_error_std_m", "#16a34a"),
        ]
        for offset, (name, key, color) in zip([-width, 0.0, width], series):
            values = [item.metrics[key] for item in present]
            plt.bar([pos + offset for pos in x], values, width=width, label=name, color=color)
        plt.ylabel("Error std (m)")
        plt.title(title)
        plt.xticks(x, labels, rotation=15, ha="right")
        plt.grid(axis="y", alpha=0.25)
        plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=180)
    plt.close()


def write_figures(loaded: dict[str, ExperimentData], results_dir: Path) -> None:
    figures_dir = results_dir / "figures"
    plot_bar(loaded, "xy_rmse_m", "All Tracking XY RMSE", "XY RMSE (m)", figures_dir / "all_tracking_xy_rmse.png")
    plot_bar(loaded, "position_rmse_m", "All Tracking 3D RMSE", "3D RMSE (m)", figures_dir / "all_tracking_3d_rmse.png")
    plot_bar(loaded, "z_rmse_m", "All Tracking z RMSE", "z RMSE (m)", figures_dir / "all_tracking_z_rmse.png")
    plot_bar(loaded, "xy_error_std_m", "All Tracking XY Error Std", "XY error std (m)", figures_dir / "all_tracking_xy_error_std.png")
    plot_bar(loaded, "position_error_std_m", "All Tracking 3D Error Std", "3D error std (m)", figures_dir / "all_tracking_3d_error_std.png")
    plot_bar(
        loaded,
        "final_position_error_before_landing_m",
        "All Tracking Final Error Before Landing",
        "Final 3D error (m)",
        figures_dir / "all_tracking_final_error.png",
    )
    plot_improvement_summary(build_improvements(loaded), figures_dir / "all_tracking_improvement_summary.png")

    plot_xy_comparison(
        loaded,
        ["circle_baseline", "circle_feedforward"],
        "Circle XY Tracking: Baseline vs Feedforward",
        figures_dir / "circle_xy_tracking_comparison.png",
    )
    plot_xy_comparison(
        loaded,
        ["square_baseline", "square_smooth"],
        "Square XY Tracking: Baseline vs Smooth",
        figures_dir / "square_xy_tracking_comparison.png",
    )
    plot_xy_comparison(
        loaded,
        ["figure8_baseline", "figure8_feedforward", "figure8_planar_ff_g0p8"],
        "Figure-Eight XY Tracking: Baseline vs Feedforward vs Planar FF g=0.8",
        figures_dir / "figure8_xy_tracking_comparison.png",
    )
    plot_xy_comparison(
        loaded,
        [
            "figure8_baseline",
            "figure8_feedforward",
            "figure8_planar_ff_g0p5",
            "figure8_planar_ff_g0p8",
            "figure8_planar_ff_g1",
        ],
        "Figure-Eight XY Tracking: Planar FF Gain Sweep",
        figures_dir / "figure8_planar_ff_gain_xy_tracking_comparison.png",
    )

    plot_error_timeseries(
        loaded,
        ["circle_baseline", "circle_feedforward"],
        "Circle Tracking Error Time Series",
        figures_dir / "circle_error_timeseries.png",
        include_z=False,
    )
    plot_error_timeseries(
        loaded,
        ["square_baseline", "square_smooth"],
        "Square Tracking Error Time Series",
        figures_dir / "square_error_timeseries.png",
        include_z=False,
    )
    plot_error_timeseries(
        loaded,
        ["figure8_baseline", "figure8_feedforward", "figure8_planar_ff_g0p8"],
        "Figure-Eight Tracking Error Time Series",
        figures_dir / "figure8_error_timeseries.png",
        include_z=True,
    )
    plot_error_timeseries(
        loaded,
        [
            "figure8_baseline",
            "figure8_feedforward",
            "figure8_planar_ff_g0p5",
            "figure8_planar_ff_g0p8",
            "figure8_planar_ff_g1",
        ],
        "Figure-Eight Planar FF Gain Sweep Error Time Series",
        figures_dir / "figure8_planar_ff_gain_error_timeseries.png",
        include_z=True,
    )

    plot_error_std(
        loaded,
        ["circle_baseline", "circle_feedforward"],
        "Circle Error Stability",
        figures_dir / "circle_error_std_comparison.png",
    )
    plot_error_std(
        loaded,
        ["square_baseline", "square_smooth"],
        "Square Error Stability",
        figures_dir / "square_error_std_comparison.png",
    )
    plot_error_std(
        loaded,
        ["figure8_baseline", "figure8_feedforward", "figure8_planar_ff_g0p8"],
        "Figure-Eight Error Stability",
        figures_dir / "figure8_error_std_comparison.png",
    )


def metric_lookup(loaded: dict[str, ExperimentData], key: str, metric_key: str) -> float:
    item = loaded.get(key)
    if item is None:
        return math.nan
    return float(item.metrics[metric_key])


def lower_text(candidate: float, reference: float) -> str:
    if math.isnan(candidate) or math.isnan(reference):
        return "cannot be evaluated because data is missing"
    return "lower" if candidate < reference else "higher"


def write_experiment_summary(
    loaded: dict[str, ExperimentData],
    missing: list[dict[str, Any]],
    results_dir: Path,
) -> None:
    metrics = [loaded[spec["key"]].metrics for spec in EXPERIMENTS if spec["key"] in loaded]
    improvements = build_improvements(loaded)
    all_present = not missing and len(metrics) == len(EXPERIMENTS)

    selected_lines = []
    for spec in EXPERIMENTS:
        item = loaded.get(spec["key"])
        if item:
            selected_lines.append(f"- `{spec['label']}`: `{item.metrics['selected_csv']}`")
        else:
            selected_lines.append(f"- `{spec['label']}`: missing")

    circle_base_xy = metric_lookup(loaded, "circle_baseline", "xy_rmse_m")
    circle_ff_xy = metric_lookup(loaded, "circle_feedforward", "xy_rmse_m")
    circle_base_3d = metric_lookup(loaded, "circle_baseline", "position_rmse_m")
    circle_ff_3d = metric_lookup(loaded, "circle_feedforward", "position_rmse_m")
    square_base_xy = metric_lookup(loaded, "square_baseline", "xy_rmse_m")
    square_smooth_xy = metric_lookup(loaded, "square_smooth", "xy_rmse_m")
    square_base_3d = metric_lookup(loaded, "square_baseline", "position_rmse_m")
    square_smooth_3d = metric_lookup(loaded, "square_smooth", "position_rmse_m")
    fig_base_xy = metric_lookup(loaded, "figure8_baseline", "xy_rmse_m")
    fig_ff_xy = metric_lookup(loaded, "figure8_feedforward", "xy_rmse_m")
    fig_base_z = metric_lookup(loaded, "figure8_baseline", "z_rmse_m")
    fig_ff_z = metric_lookup(loaded, "figure8_feedforward", "z_rmse_m")
    fig_base_3d = metric_lookup(loaded, "figure8_baseline", "position_rmse_m")
    fig_ff_3d = metric_lookup(loaded, "figure8_feedforward", "position_rmse_m")
    fig_planar_xy = metric_lookup(loaded, "figure8_planar_ff_g0p8", "xy_rmse_m")
    fig_planar_z = metric_lookup(loaded, "figure8_planar_ff_g0p8", "z_rmse_m")
    fig_planar_3d = metric_lookup(loaded, "figure8_planar_ff_g0p8", "position_rmse_m")

    lines = [
        "# Experiment Summary",
        "",
        "This summary is generated from existing CSV logs only. No PX4, Gazebo, ROS 2 node, or Offboard experiment is run by the analysis.",
        "",
        "## Experiment Data Audit",
        "",
        "All required circle, square, and figure-eight comparison CSV files are present." if all_present else "Some required CSV files are missing or invalid.",
        "",
        "Selected CSV files:",
        "",
        *selected_lines,
        "",
        "Detailed audit files:",
        "",
        "- `results/experiment_artifact_audit.md`",
        "- `results/experiment_artifact_audit.csv`",
        "- `results/experiment_artifact_audit.json`",
        "",
        "## Overall Metrics",
        "",
        "See `results/all_tracking_metrics.md` for the full table.",
        "",
        "| Trajectory | Mode | XY RMSE (m) | z RMSE (m) | 3D RMSE (m) | Final error (m) |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in metrics:
        lines.append(
            "| %s | %s | %s | %s | %s | %s |"
            % (
                row["trajectory"],
                row["mode"],
                fmt(row["xy_rmse_m"]),
                fmt(row["z_rmse_m"]),
                fmt(row["position_rmse_m"]),
                fmt(row["final_position_error_before_landing_m"]),
            )
        )

    lines.extend(
        [
            "",
            "## Improvement Summary",
            "",
            "See `results/all_tracking_improvements.md` for the full table. Positive values mean lower error than the reference.",
            "",
            "| Comparison | XY RMSE | z RMSE | 3D RMSE | Max 3D error |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in improvements:
        lines.append(
            "| %s | %s | %s | %s | %s |"
            % (
                row["comparison"],
                fmt_percent(row["xy_rmse_m_improvement_percent"]),
                fmt_percent(row["z_rmse_m_improvement_percent"]),
                fmt_percent(row["position_rmse_m_improvement_percent"]),
                fmt_percent(row["max_position_error_m_improvement_percent"]),
            )
        )

    lines.extend(
        [
            "",
            "## Key Observations",
            "",
            (
                f"- Circle feedforward has {lower_text(circle_ff_xy, circle_base_xy)} XY RMSE "
                f"({fmt(circle_base_xy)} -> {fmt(circle_ff_xy)} m) and "
                f"{lower_text(circle_ff_3d, circle_base_3d)} 3D RMSE "
                f"({fmt(circle_base_3d)} -> {fmt(circle_ff_3d)} m)."
            ),
            (
                f"- Square smooth has {lower_text(square_smooth_xy, square_base_xy)} XY RMSE "
                f"({fmt(square_base_xy)} -> {fmt(square_smooth_xy)} m) and "
                f"{lower_text(square_smooth_3d, square_base_3d)} 3D RMSE "
                f"({fmt(square_base_3d)} -> {fmt(square_smooth_3d)} m)."
            ),
            (
                f"- Figure-eight full feedforward has {lower_text(fig_ff_xy, fig_base_xy)} XY RMSE "
                f"({fmt(fig_base_xy)} -> {fmt(fig_ff_xy)} m), but z RMSE is "
                f"{lower_text(fig_ff_z, fig_base_z)} ({fmt(fig_base_z)} -> {fmt(fig_ff_z)} m) "
                f"and 3D RMSE is {lower_text(fig_ff_3d, fig_base_3d)} "
                f"({fmt(fig_base_3d)} -> {fmt(fig_ff_3d)} m)."
            ),
            (
                f"- Figure-eight planar_ff g=0.8 gives XY RMSE {fmt(fig_planar_xy)} m, "
                f"z RMSE {fmt(fig_planar_z)} m, and 3D RMSE {fmt(fig_planar_3d)} m. "
                "In this dataset it is more balanced than full feedforward because it keeps strong XY improvement while avoiding the large z/3D degradation."
            ),
            "- Metrics are single-run SITL observations, not a robustness benchmark.",
            "",
            "## Recommended README Figures",
            "",
            "- `results/figures/all_tracking_xy_rmse.png`",
            "- `results/figures/all_tracking_3d_rmse.png`",
            "- `results/figures/circle_xy_tracking_comparison.png`",
            "- `results/figures/square_xy_tracking_comparison.png`",
            "- `results/figures/figure8_planar_ff_gain_xy_tracking_comparison.png`",
            "- `results/figures/figure8_planar_ff_3d_rmse.png`",
            "",
        ]
    )
    (results_dir / "experiment_summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    logs_dir = args.logs_dir.resolve()
    results_dir = args.results_dir.resolve()
    results_dir.mkdir(parents=True, exist_ok=True)

    loaded, missing = load_all(logs_dir)
    write_tables(loaded, missing, results_dir)
    write_figures(loaded, results_dir)
    write_experiment_summary(loaded, missing, results_dir)

    print(f"valid_experiments={len(loaded)}")
    print(f"missing_or_invalid={len(missing)}")
    print(f"metrics={results_dir / 'all_tracking_metrics.md'}")
    print(f"improvements={results_dir / 'all_tracking_improvements.md'}")
    print(f"summary={results_dir / 'experiment_summary.md'}")


if __name__ == "__main__":
    main()
