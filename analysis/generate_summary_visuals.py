#!/usr/bin/env python3
"""Generate project-level metric summaries and a compact comparison figure."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=repo_root / "results",
        help="Directory containing existing metrics JSON files.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required metrics file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def metric(name: str, value: float, unit: str, experiment: str, description: str) -> dict[str, Any]:
    return {
        "experiment": experiment,
        "metric": name,
        "value": float(value),
        "unit": unit,
        "description": description,
    }


def build_summary(hover: dict[str, Any], figure8: dict[str, Any]) -> dict[str, Any]:
    hover_ss = hover["steady_state_hover"]
    figure8_summary = figure8["summary"]
    return {
        "source_files": {
            "hover": "results/offboard_hover_metrics.json",
            "figure8": "results/figure8_metrics.json",
        },
        "notes": [
            "Summary is generated from existing analysis JSON files.",
            "Hover metrics use the steady-state hover window from offboard_hover_metrics.json.",
            "Figure-eight metrics use the tracking window from figure8_metrics.json.",
            "PX4 local coordinates are NED; negative z means upward.",
        ],
        "experiments": {
            "hover_steady_state": {
                "definition": hover.get("steady_state_hover_selection", {}).get(
                    "criteria", 'stage == "hover" and z <= -1.8'
                ),
                "samples": hover_ss["samples"],
                "duration_s": hover_ss["duration_s"],
                "z_rmse_m": hover_ss["z_rmse_m"],
                "xy_rmse_m": hover_ss["xy_rmse_m"],
                "final_position_error_m": hover_ss["final_position_error_m"],
                "max_speed_mps": hover_ss["max_speed_mps"],
            },
            "figure8_tracking": {
                "definition": figure8.get("tracking_stage_filter", {}).get("criteria", 'stage == "figure8"'),
                "samples": figure8_summary["tracking_samples"],
                "duration_s": figure8_summary["tracking_duration_s"],
                "xy_rmse_m": figure8_summary["tracking_xy_rmse_m"],
                "z_rmse_m": figure8_summary["tracking_z_rmse_m"],
                "position_rmse_m": figure8_summary["tracking_position_rmse_m"],
                "max_position_error_m": figure8_summary["tracking_max_position_error_m"],
                "final_position_error_before_landing_m": figure8_summary[
                    "final_position_error_before_landing_m"
                ],
                "max_speed_mps": figure8_summary["tracking_max_speed_mps"],
            },
        },
    }


def rows_from_summary(summary: dict[str, Any]) -> list[dict[str, Any]]:
    hover = summary["experiments"]["hover_steady_state"]
    figure8 = summary["experiments"]["figure8_tracking"]
    return [
        metric("steady_state_z_rmse", hover["z_rmse_m"], "m", "hover_steady_state", "Steady hover z RMSE"),
        metric("steady_state_xy_rmse", hover["xy_rmse_m"], "m", "hover_steady_state", "Steady hover XY RMSE"),
        metric(
            "final_position_error",
            hover["final_position_error_m"],
            "m",
            "hover_steady_state",
            "Final steady hover position error",
        ),
        metric(
            "max_steady_state_speed",
            hover["max_speed_mps"],
            "m/s",
            "hover_steady_state",
            "Maximum speed during steady hover",
        ),
        metric("tracking_duration", figure8["duration_s"], "s", "figure8_tracking", "Figure-eight tracking duration"),
        metric("xy_rmse", figure8["xy_rmse_m"], "m", "figure8_tracking", "Figure-eight XY RMSE"),
        metric("z_rmse", figure8["z_rmse_m"], "m", "figure8_tracking", "Figure-eight z RMSE"),
        metric("position_rmse", figure8["position_rmse_m"], "m", "figure8_tracking", "Figure-eight 3D RMSE"),
        metric(
            "max_position_error",
            figure8["max_position_error_m"],
            "m",
            "figure8_tracking",
            "Figure-eight max 3D position error",
        ),
        metric(
            "final_position_error_before_landing",
            figure8["final_position_error_before_landing_m"],
            "m",
            "figure8_tracking",
            "Figure-eight final position error before landing",
        ),
        metric(
            "max_tracking_speed",
            figure8["max_speed_mps"],
            "m/s",
            "figure8_tracking",
            "Maximum speed during figure-eight tracking",
        ),
    ]


def fmt(value: float, digits: int = 4) -> str:
    if value is None or math.isnan(float(value)):
        return "n/a"
    return f"{float(value):.{digits}f}"


def write_json(summary: dict[str, Any], output_path: Path) -> None:
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def write_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["experiment", "metric", "value", "unit", "description"])
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(summary: dict[str, Any], rows: list[dict[str, Any]], output_path: Path) -> None:
    hover = summary["experiments"]["hover_steady_state"]
    figure8 = summary["experiments"]["figure8_tracking"]
    lines = [
        "# Summary Metrics",
        "",
        "This project-level summary is generated from existing analysis JSON files:",
        "",
        "- `results/offboard_hover_metrics.json`",
        "- `results/figure8_metrics.json`",
        "",
        "PX4 local position uses NED coordinates. Negative `z` means upward.",
        "",
        "## Key Results",
        "",
        "| Experiment | Metric | Value | Unit |",
        "| --- | --- | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['experiment']} | {row['metric']} | {fmt(row['value'], 4)} | {row['unit']} |"
        )
    lines.extend(
        [
            "",
            "## Hover Steady-State",
            "",
            f"- Definition: `{hover['definition']}`",
            f"- Samples: `{hover['samples']}`",
            f"- Duration: `{fmt(hover['duration_s'], 3)} s`",
            f"- z RMSE: `{fmt(hover['z_rmse_m'], 4)} m`",
            f"- XY RMSE: `{fmt(hover['xy_rmse_m'], 4)} m`",
            f"- Final position error: `{fmt(hover['final_position_error_m'], 4)} m`",
            f"- Max steady-state speed: `{fmt(hover['max_speed_mps'], 4)} m/s`",
            "",
            "## Figure-Eight Tracking",
            "",
            f"- Definition: `{figure8['definition']}`",
            f"- Samples: `{figure8['samples']}`",
            f"- Duration: `{fmt(figure8['duration_s'], 3)} s`",
            f"- XY RMSE: `{fmt(figure8['xy_rmse_m'], 4)} m`",
            f"- z RMSE: `{fmt(figure8['z_rmse_m'], 4)} m`",
            f"- 3D position RMSE: `{fmt(figure8['position_rmse_m'], 4)} m`",
            f"- Max 3D position error: `{fmt(figure8['max_position_error_m'], 4)} m`",
            f"- Final position error before landing: `{fmt(figure8['final_position_error_before_landing_m'], 4)} m`",
            f"- Max tracking speed: `{fmt(figure8['max_speed_mps'], 4)} m/s`",
            "",
            "## Generated Figure",
            "",
            "- `results/figures/metrics_summary.png`",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def save_metrics_figure(summary: dict[str, Any], figures_dir: Path) -> None:
    figures_dir.mkdir(parents=True, exist_ok=True)
    hover = summary["experiments"]["hover_steady_state"]
    figure8 = summary["experiments"]["figure8_tracking"]
    labels = [
        "Hover z\nRMSE",
        "Hover XY\nRMSE",
        "Figure-8 XY\nRMSE",
        "Figure-8 z\nRMSE",
        "Figure-8 3D\nRMSE",
    ]
    values = [
        hover["z_rmse_m"],
        hover["xy_rmse_m"],
        figure8["xy_rmse_m"],
        figure8["z_rmse_m"],
        figure8["position_rmse_m"],
    ]
    colors = ["#3b82f6", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6"]

    plt.figure(figsize=(9, 5.2))
    bars = plt.bar(labels, values, color=colors, edgecolor="#1f2937", linewidth=0.7)
    plt.ylabel("Error (m)")
    plt.title("PX4 SITL Offboard Tracking Error Summary")
    plt.grid(axis="y", alpha=0.25)
    for bar, value in zip(bars, values):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.008,
            f"{value:.3f} m",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    plt.ylim(0, max(values) * 1.25)
    plt.tight_layout()
    plt.savefig(figures_dir / "metrics_summary.png", dpi=170)
    plt.close()


def write_pipeline(output_path: Path) -> None:
    lines = [
        "# Project Pipeline",
        "",
        "```mermaid",
        "flowchart LR",
        '  A["Windows 11 + WSL2 Ubuntu 22.04"] --> B["PX4 SITL + Gazebo Harmonic X500"]',
        '  B --> C["Micro XRCE-DDS Agent"]',
        '  C --> D["ROS 2 Humble / px4_msgs / px4_ros_com"]',
        '  D --> E["Offboard hover node"]',
        '  D --> F["Figure-eight node"]',
        '  E --> G["CSV logs"]',
        '  F --> G',
        '  G --> H["Analysis scripts"]',
        '  H --> I["Figures / metrics / README"]',
        "```",
        "",
        "The repository stores the project code, lightweight CSV logs, generated figures, and summary metrics. PX4-Autopilot and the ROS 2 workspace remain external dependencies.",
        "",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    results_dir = args.results_dir.resolve()
    hover = load_json(results_dir / "offboard_hover_metrics.json")
    figure8 = load_json(results_dir / "figure8_metrics.json")
    summary = build_summary(hover, figure8)
    rows = rows_from_summary(summary)

    write_json(summary, results_dir / "summary_metrics.json")
    write_csv(rows, results_dir / "summary_metrics.csv")
    write_markdown(summary, rows, results_dir / "summary_metrics.md")
    save_metrics_figure(summary, results_dir / "figures")
    write_pipeline(results_dir / "project_pipeline.md")

    print("Summary visuals generated")
    print(f"summary_md={results_dir / 'summary_metrics.md'}")
    print(f"summary_json={results_dir / 'summary_metrics.json'}")
    print(f"summary_csv={results_dir / 'summary_metrics.csv'}")
    print(f"metrics_summary_png={results_dir / 'figures' / 'metrics_summary.png'}")
    print(f"project_pipeline_md={results_dir / 'project_pipeline.md'}")


if __name__ == "__main__":
    main()
