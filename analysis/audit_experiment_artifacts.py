#!/usr/bin/env python3
"""Audit expected tracking experiment CSV logs and generated figures."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

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
TRACKING_STAGE_NAMES = {"tracking", "trajectory", "circle", "square", "figure8"}

GLOBAL_FIGURES = [
    "all_tracking_xy_rmse.png",
    "all_tracking_3d_rmse.png",
    "all_tracking_z_rmse.png",
    "all_tracking_xy_error_std.png",
    "all_tracking_3d_error_std.png",
    "all_tracking_final_error.png",
    "all_tracking_improvement_summary.png",
]

EXPERIMENTS: list[dict[str, Any]] = [
    {
        "trajectory": "circle",
        "mode": "baseline",
        "pattern": "offboard_trajectory_circle_baseline_*.csv",
        "figures": [
            "circle_xy_tracking_comparison.png",
            "circle_error_timeseries.png",
            "circle_error_std_comparison.png",
        ],
    },
    {
        "trajectory": "circle",
        "mode": "feedforward",
        "pattern": "offboard_trajectory_circle_feedforward_*.csv",
        "figures": [
            "circle_xy_tracking_comparison.png",
            "circle_error_timeseries.png",
            "circle_error_std_comparison.png",
        ],
    },
    {
        "trajectory": "square",
        "mode": "baseline",
        "pattern": "offboard_trajectory_square_baseline_*.csv",
        "figures": [
            "square_xy_tracking_comparison.png",
            "square_error_timeseries.png",
            "square_error_std_comparison.png",
        ],
    },
    {
        "trajectory": "square",
        "mode": "smooth",
        "pattern": "offboard_trajectory_square_smooth_*.csv",
        "figures": [
            "square_xy_tracking_comparison.png",
            "square_error_timeseries.png",
            "square_error_std_comparison.png",
        ],
    },
    {
        "trajectory": "figure8",
        "mode": "baseline",
        "pattern": "offboard_trajectory_figure8_baseline_*.csv",
        "figures": [
            "figure8_xy_tracking_comparison.png",
            "figure8_planar_ff_gain_xy_tracking_comparison.png",
            "figure8_error_timeseries.png",
            "figure8_planar_ff_gain_error_timeseries.png",
            "figure8_error_std_comparison.png",
        ],
    },
    {
        "trajectory": "figure8",
        "mode": "feedforward",
        "pattern": "offboard_trajectory_figure8_feedforward_*.csv",
        "figures": [
            "figure8_xy_tracking_comparison.png",
            "figure8_planar_ff_gain_xy_tracking_comparison.png",
            "figure8_error_timeseries.png",
            "figure8_planar_ff_gain_error_timeseries.png",
            "figure8_error_std_comparison.png",
        ],
    },
    {
        "trajectory": "figure8",
        "mode": "planar_ff_g0p5",
        "pattern": "offboard_trajectory_figure8_planar_ff_g0p5_*.csv",
        "figures": [
            "figure8_planar_ff_gain_xy_tracking_comparison.png",
            "figure8_planar_ff_gain_error_timeseries.png",
            "figure8_planar_ff_xy_rmse.png",
            "figure8_planar_ff_z_rmse.png",
            "figure8_planar_ff_3d_rmse.png",
            "figure8_planar_ff_final_error.png",
        ],
    },
    {
        "trajectory": "figure8",
        "mode": "planar_ff_g0p8",
        "pattern": "offboard_trajectory_figure8_planar_ff_g0p8_*.csv",
        "figures": [
            "figure8_xy_tracking_comparison.png",
            "figure8_planar_ff_gain_xy_tracking_comparison.png",
            "figure8_error_timeseries.png",
            "figure8_planar_ff_gain_error_timeseries.png",
            "figure8_error_std_comparison.png",
            "figure8_planar_ff_xy_rmse.png",
            "figure8_planar_ff_z_rmse.png",
            "figure8_planar_ff_3d_rmse.png",
            "figure8_planar_ff_final_error.png",
        ],
    },
    {
        "trajectory": "figure8",
        "mode": "planar_ff_g1",
        "pattern": "offboard_trajectory_figure8_planar_ff_g1_*.csv",
        "figures": [
            "figure8_planar_ff_gain_xy_tracking_comparison.png",
            "figure8_planar_ff_gain_error_timeseries.png",
            "figure8_planar_ff_xy_rmse.png",
            "figure8_planar_ff_z_rmse.png",
            "figure8_planar_ff_3d_rmse.png",
            "figure8_planar_ff_final_error.png",
        ],
    },
]


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


def csv_stats(path: Path, trajectory: str) -> tuple[int, float, bool, str]:
    try:
        df = pd.read_csv(path)
    except Exception as exc:  # noqa: BLE001
        return 0, math.nan, False, f"read failed: {exc}"

    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        return 0, math.nan, False, f"missing columns: {missing}"

    for column in ["timestamp", "x", "y", "z", "vx", "vy", "vz", "target_x", "target_y", "target_z"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df = df.dropna(subset=["timestamp", "x", "y", "z", "target_x", "target_y", "target_z"])
    if df.empty:
        return 0, math.nan, False, "no numeric samples"

    df["stage_normalized"] = df["stage"].astype(str).str.strip().str.lower()
    df["trajectory_type"] = df["trajectory_type"].astype(str).str.strip().str.lower()
    rows = df[
        (df["trajectory_type"] == trajectory)
        & (
            df["stage_normalized"].isin(TRACKING_STAGE_NAMES)
            | (df["stage_normalized"] == trajectory)
        )
    ].sort_values("timestamp")
    if rows.empty:
        return 0, math.nan, False, "no tracking-stage rows"
    duration_s = float((rows["timestamp"].iloc[-1] - rows["timestamp"].iloc[0]) / 1_000_000.0)
    return int(len(rows)), duration_s, duration_s > 0.0, ""


def figure_status(results_dir: Path, figure_names: list[str]) -> tuple[list[str], list[str]]:
    figures_dir = results_dir / "figures"
    present: list[str] = []
    missing: list[str] = []
    for name in sorted(set(GLOBAL_FIGURES + figure_names)):
        path = figures_dir / name
        if path.exists() and path.stat().st_size > 0:
            present.append(f"results/figures/{name}")
        else:
            missing.append(f"results/figures/{name}")
    return present, missing


def build_audit(logs_dir: Path, results_dir: Path) -> list[dict[str, Any]]:
    repo_root = logs_dir.parent
    rows: list[dict[str, Any]] = []
    for spec in EXPERIMENTS:
        selected = select_latest_csv(logs_dir, spec["pattern"])
        if selected is None:
            present, missing = figure_status(results_dir, spec["figures"])
            rows.append(
                {
                    "trajectory": spec["trajectory"],
                    "mode": spec["mode"],
                    "selected_csv": "",
                    "file_size": 0,
                    "samples": 0,
                    "duration_s": math.nan,
                    "whether_valid": False,
                    "figures_present": ";".join(present),
                    "figures_missing": ";".join(missing),
                    "notes": "missing CSV",
                }
            )
            continue

        samples, duration_s, valid, note = csv_stats(selected, spec["trajectory"])
        present, missing = figure_status(results_dir, spec["figures"])
        rows.append(
            {
                "trajectory": spec["trajectory"],
                "mode": spec["mode"],
                "selected_csv": selected.relative_to(repo_root).as_posix(),
                "file_size": selected.stat().st_size,
                "samples": samples,
                "duration_s": duration_s,
                "whether_valid": valid,
                "figures_present": ";".join(present),
                "figures_missing": ";".join(missing),
                "notes": note,
            }
        )
    return rows


def fmt(value: Any, digits: int = 3) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    if math.isnan(numeric):
        return "n/a"
    return f"{numeric:.{digits}f}"


def write_markdown(rows: list[dict[str, Any]], output_path: Path) -> None:
    all_valid = all(row["whether_valid"] for row in rows)
    missing_figures = sorted(
        {
            figure
            for row in rows
            for figure in str(row["figures_missing"]).split(";")
            if figure
        }
    )
    lines = [
        "# Experiment Artifact Audit",
        "",
        "This audit scans only `logs/*.csv`; it does not read `logs/bad_runs/`.",
        "",
        "CSV status: " + ("all expected experiment CSV files are valid." if all_valid else "some expected CSV files are missing or invalid."),
        "",
        "## CSV Inventory",
        "",
        "| Trajectory | Mode | Selected CSV | Size (bytes) | Samples | Duration (s) | Valid | Notes |",
        "| --- | --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| %s | %s | `%s` | %d | %d | %s | %s | %s |"
            % (
                row["trajectory"],
                row["mode"],
                row["selected_csv"],
                row["file_size"],
                row["samples"],
                fmt(row["duration_s"]),
                "yes" if row["whether_valid"] else "no",
                row["notes"],
            )
        )

    lines.extend(["", "## Figure Coverage", ""])
    if missing_figures:
        lines.append("Missing expected figures:")
        lines.append("")
        for figure in missing_figures:
            lines.append(f"- `{figure}`")
    else:
        lines.append("All expected comparison figures are present.")

    lines.extend(["", "## Selected Figure Groups", ""])
    for row in rows:
        present = [figure for figure in str(row["figures_present"]).split(";") if figure]
        lines.append(f"### {row['trajectory']} {row['mode']}")
        lines.append("")
        for figure in present:
            lines.append(f"- `{figure}`")
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    logs_dir = args.logs_dir.resolve()
    results_dir = args.results_dir.resolve()
    results_dir.mkdir(parents=True, exist_ok=True)

    rows = build_audit(logs_dir, results_dir)
    pd.DataFrame(rows).to_csv(results_dir / "experiment_artifact_audit.csv", index=False)
    (results_dir / "experiment_artifact_audit.json").write_text(
        json.dumps({"rows": rows}, indent=2),
        encoding="utf-8",
    )
    write_markdown(rows, results_dir / "experiment_artifact_audit.md")
    print(f"audit_rows={len(rows)}")
    print(f"valid_csv={sum(1 for row in rows if row['whether_valid'])}")
    print(f"audit={results_dir / 'experiment_artifact_audit.md'}")


if __name__ == "__main__":
    main()
