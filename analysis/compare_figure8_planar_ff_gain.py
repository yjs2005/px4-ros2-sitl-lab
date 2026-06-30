#!/usr/bin/env python3
"""Compare figure-eight baseline, feedforward, and planar_ff gain sweep logs."""

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
TRACKING_STAGE_NAMES = {"tracking", "trajectory", "figure8"}
MODE_ORDER = ["baseline", "feedforward", "planar_ff_g0p5", "planar_ff_g0p8", "planar_ff_g1"]
MODE_LABELS = {
    "baseline": "baseline",
    "feedforward": "feedforward",
    "planar_ff_g0p5": "planar_ff g=0.5",
    "planar_ff_g0p8": "planar_ff g=0.8",
    "planar_ff_g1": "planar_ff g=1.0",
}
GAIN_LABELS = {
    0.5: "planar_ff_g0p5",
    0.8: "planar_ff_g0p8",
    1.0: "planar_ff_g1",
}


@dataclass(frozen=True)
class LoadedLog:
    key: str
    path: Path
    rows: pd.DataFrame


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--logs-dir", type=Path, default=repo_root / "logs")
    parser.add_argument("--results-dir", type=Path, default=repo_root / "results")
    return parser.parse_args()


def latest_timestamp_key(path: Path) -> tuple[str, float]:
    match = re.search(r"_(\d{8}_\d{6})\.csv$", path.name)
    stamp = match.group(1) if match else ""
    return stamp, path.stat().st_mtime


def parse_gain_from_name(path: Path) -> float | None:
    match = re.search(r"_g([0-9]+(?:p[0-9]+)?)_", path.name)
    if not match:
        return None
    return float(match.group(1).replace("p", "."))


def mode_key_from_path(path: Path) -> str | None:
    name = path.name
    if "bad_runs" in path.parts:
        return None
    if not name.startswith("offboard_trajectory_figure8_"):
        return None
    if "_baseline_" in name:
        return "baseline"
    if "_feedforward_" in name:
        return "feedforward"
    if "_planar_ff_" in name:
        gain = parse_gain_from_name(path)
        if gain is None:
            return None
        rounded = round(gain, 3)
        for expected, key in GAIN_LABELS.items():
            if math.isclose(rounded, expected, abs_tol=1e-3):
                return key
    return None


def discover_latest_logs(logs_dir: Path) -> dict[str, Path]:
    candidates: dict[str, list[Path]] = {key: [] for key in MODE_ORDER}
    for path in logs_dir.glob("offboard_trajectory_figure8_*.csv"):
        key = mode_key_from_path(path)
        if key in candidates:
            candidates[key].append(path)

    selected: dict[str, Path] = {}
    for key, paths in candidates.items():
        if paths:
            selected[key] = sorted(paths, key=latest_timestamp_key)[-1]
    return selected


def load_tracking_rows(path: Path, repo_root: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"{path.name}: missing required columns {missing}")

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
        raise ValueError(f"{path.name}: no numeric samples")

    df = df.sort_values("timestamp").reset_index(drop=True)
    df["stage"] = df["stage"].astype(str)
    df["trajectory_type"] = df["trajectory_type"].astype(str).str.strip().str.lower()
    df["controller_mode"] = df["controller_mode"].astype(str).str.strip().str.lower()
    df["stage_normalized"] = df["stage"].str.strip().str.lower()
    rows = df[
        (df["trajectory_type"] == "figure8")
        & (
            df["stage_normalized"].isin(TRACKING_STAGE_NAMES)
            | (df["stage_normalized"] == df["trajectory_type"])
        )
    ].copy()
    if rows.empty:
        raise ValueError(f"{path.name}: no figure-eight tracking rows")

    rows["time_s"] = (rows["timestamp"] - rows["timestamp"].iloc[0]) / 1_000_000.0
    rows["x_error"] = rows["x"] - rows["target_x"]
    rows["y_error"] = rows["y"] - rows["target_y"]
    rows["z_error"] = rows["z"] - rows["target_z"]
    rows["xy_error"] = (rows["x_error"] ** 2 + rows["y_error"] ** 2) ** 0.5
    rows["position_error"] = (rows["xy_error"] ** 2 + rows["z_error"] ** 2) ** 0.5
    rows["speed"] = (rows["vx"] ** 2 + rows["vy"] ** 2 + rows["vz"] ** 2) ** 0.5
    try:
        rows["source_file"] = path.relative_to(repo_root).as_posix()
    except ValueError:
        rows["source_file"] = path.as_posix()
    return rows.reset_index(drop=True)


def rmse(series: pd.Series) -> float:
    if series.empty:
        return math.nan
    return float((series.pow(2).mean()) ** 0.5)


def percent_improvement(baseline: float, value: float) -> float:
    if baseline == 0.0 or math.isnan(baseline) or math.isnan(value):
        return math.nan
    return float((baseline - value) / baseline * 100.0)


def compute_metrics(key: str, path: Path, rows: pd.DataFrame) -> dict[str, Any]:
    return {
        "mode_key": key,
        "label": MODE_LABELS[key],
        "controller_mode": str(rows["controller_mode"].iloc[0]),
        "ff_gain": float(rows["ff_gain"].dropna().iloc[0]) if rows["ff_gain"].notna().any() else 1.0,
        "samples": int(len(rows)),
        "duration_s": float((rows["timestamp"].iloc[-1] - rows["timestamp"].iloc[0]) / 1_000_000.0),
        "xy_rmse_m": rmse(rows["xy_error"]),
        "z_rmse_m": rmse(rows["z_error"]),
        "position_rmse_m": rmse(rows["position_error"]),
        "max_position_error_m": float(rows["position_error"].max()),
        "final_position_error_before_landing_m": float(rows["position_error"].iloc[-1]),
        "max_speed_mps": float(rows["speed"].max()),
        "source_file": path.as_posix(),
    }


def build_analysis(logs_dir: Path) -> tuple[dict[str, Any], list[LoadedLog]]:
    repo_root = logs_dir.parent
    selected = discover_latest_logs(logs_dir)
    loaded: list[LoadedLog] = []
    skipped: dict[str, str] = {}
    metrics: list[dict[str, Any]] = []

    for key in MODE_ORDER:
        path = selected.get(key)
        if path is None:
            skipped[key] = "no matching log found"
            continue
        try:
            rows = load_tracking_rows(path, repo_root)
        except Exception as exc:  # noqa: BLE001 - keep report generation robust.
            skipped[key] = str(exc)
            continue
        loaded.append(LoadedLog(key, path, rows))
        metrics.append(compute_metrics(key, path.relative_to(repo_root), rows))

    baseline = next((row for row in metrics if row["mode_key"] == "baseline"), None)
    baseline_metrics = baseline or {}
    for row in metrics:
        row["xy_rmse_improvement_percent"] = percent_improvement(
            float(baseline_metrics.get("xy_rmse_m", math.nan)),
            float(row["xy_rmse_m"]),
        )
        row["z_rmse_improvement_percent"] = percent_improvement(
            float(baseline_metrics.get("z_rmse_m", math.nan)),
            float(row["z_rmse_m"]),
        )
        row["position_rmse_improvement_percent"] = percent_improvement(
            float(baseline_metrics.get("position_rmse_m", math.nan)),
            float(row["position_rmse_m"]),
        )
        row["max_position_error_improvement_percent"] = percent_improvement(
            float(baseline_metrics.get("max_position_error_m", math.nan)),
            float(row["max_position_error_m"]),
        )

    data = {
        "description": "Figure-eight baseline, full feedforward, and planar_ff gain sweep.",
        "tracking_filter": "trajectory_type == figure8 and stage in tracking/trajectory/figure8",
        "selection_policy": "For each mode/gain, use the latest matching file in logs/. logs/bad_runs is not scanned.",
        "mode_order": MODE_ORDER,
        "selected_logs": {key: selected[key].relative_to(repo_root).as_posix() for key in selected},
        "skipped": skipped,
        "metrics": metrics,
    }
    return data, loaded


def write_outputs(data: dict[str, Any], results_dir: Path) -> None:
    results_dir.mkdir(parents=True, exist_ok=True)
    metrics = data["metrics"]
    csv_columns = [
        "mode_key",
        "label",
        "controller_mode",
        "ff_gain",
        "samples",
        "duration_s",
        "xy_rmse_m",
        "z_rmse_m",
        "position_rmse_m",
        "max_position_error_m",
        "final_position_error_before_landing_m",
        "max_speed_mps",
        "xy_rmse_improvement_percent",
        "z_rmse_improvement_percent",
        "position_rmse_improvement_percent",
        "max_position_error_improvement_percent",
        "source_file",
    ]
    pd.DataFrame(metrics, columns=csv_columns).to_csv(
        results_dir / "figure8_planar_ff_gain_metrics.csv",
        index=False,
    )
    (results_dir / "figure8_planar_ff_gain_metrics.json").write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )
    write_markdown(data, results_dir / "figure8_planar_ff_gain_metrics.md")


def fmt(value: Any, digits: int = 4) -> str:
    if value is None:
        return "n/a"
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    if math.isnan(numeric):
        return "n/a"
    return f"{numeric:.{digits}f}"


def write_markdown(data: dict[str, Any], output_path: Path) -> None:
    lines = [
        "# Figure-Eight Planar Feedforward Gain Sweep",
        "",
        "This report compares figure-eight baseline, full velocity feedforward, and planar feedforward gains.",
        "",
        "- Full `feedforward` can reduce XY tracking error but may worsen z and 3D errors.",
        "- `planar_ff` applies velocity feedforward only in the NED XY plane and keeps `vz=0.0`.",
        "- Positive improvement means the metric is lower than baseline.",
        "",
        "## Metrics",
        "",
        "| Mode | ff_gain | Samples | Duration (s) | XY RMSE (m) | z RMSE (m) | 3D RMSE (m) | Max 3D (m) | Final before landing (m) | Max speed (m/s) |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in data["metrics"]:
        lines.append(
            "| %s | %s | %d | %s | %s | %s | %s | %s | %s | %s |"
            % (
                row["label"],
                fmt(row["ff_gain"], 2),
                row["samples"],
                fmt(row["duration_s"], 3),
                fmt(row["xy_rmse_m"], 4),
                fmt(row["z_rmse_m"], 4),
                fmt(row["position_rmse_m"], 4),
                fmt(row["max_position_error_m"], 4),
                fmt(row["final_position_error_before_landing_m"], 4),
                fmt(row["max_speed_mps"], 4),
            )
        )

    lines.extend(
        [
            "",
            "## Improvement Relative To Baseline",
            "",
            "| Mode | ff_gain | XY RMSE | z RMSE | 3D RMSE | Max 3D error |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in data["metrics"]:
        lines.append(
            "| %s | %s | %s%% | %s%% | %s%% | %s%% |"
            % (
                row["label"],
                fmt(row["ff_gain"], 2),
                fmt(row["xy_rmse_improvement_percent"], 2),
                fmt(row["z_rmse_improvement_percent"], 2),
                fmt(row["position_rmse_improvement_percent"], 2),
                fmt(row["max_position_error_improvement_percent"], 2),
            )
        )

    conclusion = build_conclusion(data["metrics"])
    lines.extend(
        [
            "",
            "## Observation",
            "",
            conclusion,
            "",
            "## Selected Logs",
            "",
        ]
    )
    for key in MODE_ORDER:
        path = data["selected_logs"].get(key)
        if path:
            lines.append(f"- `{MODE_LABELS[key]}`: `{path}`")
    if data["skipped"]:
        lines.extend(["", "## Skipped", ""])
        for key, reason in data["skipped"].items():
            lines.append(f"- `{key}`: {reason}")

    lines.extend(
        [
            "",
            "## Figures",
            "",
            "- `results/figures/figure8_planar_ff_xy_rmse.png`",
            "- `results/figures/figure8_planar_ff_z_rmse.png`",
            "- `results/figures/figure8_planar_ff_3d_rmse.png`",
            "- `results/figures/figure8_planar_ff_final_error.png`",
            "- `results/figures/figure8_planar_ff_xy_tracking.png`",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def build_conclusion(metrics: list[dict[str, Any]]) -> str:
    if not metrics:
        return "No valid figure-eight comparison logs were found."
    baseline = next((row for row in metrics if row["mode_key"] == "baseline"), None)
    feedforward = next((row for row in metrics if row["mode_key"] == "feedforward"), None)
    planar_rows = [row for row in metrics if row["mode_key"].startswith("planar_ff")]
    parts: list[str] = []
    if baseline and feedforward:
        parts.append(
            "Full feedforward changes XY RMSE from "
            f"{baseline['xy_rmse_m']:.4f} m to {feedforward['xy_rmse_m']:.4f} m, "
            f"while z RMSE changes from {baseline['z_rmse_m']:.4f} m to "
            f"{feedforward['z_rmse_m']:.4f} m and 3D RMSE changes from "
            f"{baseline['position_rmse_m']:.4f} m to {feedforward['position_rmse_m']:.4f} m."
        )
    if planar_rows:
        best_3d = min(planar_rows, key=lambda row: row["position_rmse_m"])
        best_xy = min(planar_rows, key=lambda row: row["xy_rmse_m"])
        parts.append(
            f"Among planar_ff runs, {best_3d['label']} has the lowest 3D RMSE "
            f"({best_3d['position_rmse_m']:.4f} m), while {best_xy['label']} has the lowest "
            f"XY RMSE ({best_xy['xy_rmse_m']:.4f} m)."
        )
        if baseline:
            balanced = min(
                planar_rows,
                key=lambda row: row["xy_rmse_m"] / baseline["xy_rmse_m"]
                + row["z_rmse_m"] / baseline["z_rmse_m"]
                + row["position_rmse_m"] / baseline["position_rmse_m"],
            )
            parts.append(
                f"Using equal normalized XY/z/3D error weighting, {balanced['label']} is the most balanced "
                "planar_ff setting in this dataset."
            )
    return " ".join(parts)


def plot_bar(metrics: list[dict[str, Any]], metric_key: str, title: str, ylabel: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    labels = [row["label"].replace(" ", "\n") for row in metrics]
    values = [row[metric_key] for row in metrics]
    plt.figure(figsize=(9.2, 5.2))
    plt.bar(labels, values, color=["#6b7280", "#2563eb", "#16a34a", "#22c55e", "#84cc16"][: len(labels)])
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    plt.savefig(output_path, dpi=170)
    plt.close()


def plot_xy_tracking(logs: list[LoadedLog], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(7.2, 6.4))
    if not logs:
        plt.text(0.5, 0.5, "No valid logs", ha="center", va="center")
        plt.axis("off")
    else:
        reference = logs[0].rows
        plt.plot(
            reference["target_x"],
            reference["target_y"],
            color="#111827",
            linestyle="--",
            linewidth=1.5,
            label="target XY",
        )
        colors = {
            "baseline": "#6b7280",
            "feedforward": "#2563eb",
            "planar_ff_g0p5": "#16a34a",
            "planar_ff_g0p8": "#22c55e",
            "planar_ff_g1": "#84cc16",
        }
        for log in logs:
            rows = log.rows
            plt.plot(
                rows["x"],
                rows["y"],
                linewidth=1.2,
                color=colors.get(log.key, None),
                label=MODE_LABELS[log.key],
            )
        plt.xlabel("NED x (m)")
        plt.ylabel("NED y (m)")
        plt.title("Figure-Eight XY Tracking: Baseline vs Feedforward vs Planar FF")
        plt.axis("equal")
        plt.grid(alpha=0.25)
        plt.legend(loc="best", fontsize=8)
    plt.tight_layout()
    plt.savefig(output_path, dpi=170)
    plt.close()


def write_figures(data: dict[str, Any], logs: list[LoadedLog], figures_dir: Path) -> None:
    metrics = data["metrics"]
    plot_bar(
        metrics,
        "xy_rmse_m",
        "Figure-Eight XY RMSE",
        "XY RMSE (m)",
        figures_dir / "figure8_planar_ff_xy_rmse.png",
    )
    plot_bar(
        metrics,
        "z_rmse_m",
        "Figure-Eight z RMSE",
        "z RMSE (m)",
        figures_dir / "figure8_planar_ff_z_rmse.png",
    )
    plot_bar(
        metrics,
        "position_rmse_m",
        "Figure-Eight 3D RMSE",
        "3D RMSE (m)",
        figures_dir / "figure8_planar_ff_3d_rmse.png",
    )
    plot_bar(
        metrics,
        "final_position_error_before_landing_m",
        "Figure-Eight Final Error Before Landing",
        "Final error (m)",
        figures_dir / "figure8_planar_ff_final_error.png",
    )
    plot_xy_tracking(logs, figures_dir / "figure8_planar_ff_xy_tracking.png")


def main() -> None:
    args = parse_args()
    logs_dir = args.logs_dir.resolve()
    results_dir = args.results_dir.resolve()
    data, logs = build_analysis(logs_dir)
    write_outputs(data, results_dir)
    write_figures(data, logs, results_dir / "figures")
    print(f"metrics={results_dir / 'figure8_planar_ff_gain_metrics.md'}")
    print(f"valid_logs={len(logs)}")
    if data["skipped"]:
        print(f"skipped={data['skipped']}")


if __name__ == "__main__":
    main()
