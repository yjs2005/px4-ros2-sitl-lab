#!/usr/bin/env python3
"""Generate lightweight GIF visualizations from existing CSV logs."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.animation import FuncAnimation, PillowWriter


REQUIRED_COLUMNS = [
    "timestamp",
    "x",
    "y",
    "z",
    "target_x",
    "target_y",
    "target_z",
    "stage",
]


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--csv",
        type=Path,
        default=repo_root / "logs" / "figure8_first_success.csv",
        help="Input figure-eight CSV log.",
    )
    parser.add_argument(
        "--media-dir",
        type=Path,
        default=repo_root / "media",
        help="Output media directory.",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=100,
        help="Maximum number of animation frames.",
    )
    return parser.parse_args()


def load_figure8(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}")

    numeric_columns = [column for column in REQUIRED_COLUMNS if column != "stage"]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df = df.dropna(subset=numeric_columns)
    df = df.sort_values("timestamp").reset_index(drop=True)
    df["stage"] = df["stage"].astype(str)
    df["time_s"] = (df["timestamp"] - df["timestamp"].iloc[0]) / 1_000_000.0
    tracking = df[df["stage"].str.strip().str.lower() == "figure8"].copy()
    if tracking.empty:
        raise ValueError("No figure-eight rows found with stage == 'figure8'.")
    tracking["tracking_time_s"] = tracking["time_s"] - tracking["time_s"].iloc[0]
    return tracking.reset_index(drop=True)


def frame_indices(sample_count: int, max_frames: int) -> list[int]:
    if sample_count <= 0:
        return []
    if sample_count <= max_frames:
        return list(range(sample_count))
    step = (sample_count - 1) / (max_frames - 1)
    return sorted({round(i * step) for i in range(max_frames)})


def generate_figure8_gif(tracking: pd.DataFrame, output_path: Path, max_frames: int) -> None:
    indices = frame_indices(len(tracking), max_frames)
    if not indices:
        raise ValueError("No animation frames available.")

    x_min = min(tracking["y"].min(), tracking["target_y"].min()) - 0.25
    x_max = max(tracking["y"].max(), tracking["target_y"].max()) + 0.25
    y_min = min(tracking["x"].min(), tracking["target_x"].min()) - 0.25
    y_max = max(tracking["x"].max(), tracking["target_x"].max()) + 0.25

    fig, ax = plt.subplots(figsize=(6.2, 6.2))
    ax.plot(
        tracking["target_y"],
        tracking["target_x"],
        "--",
        color="#2563eb",
        linewidth=1.6,
        label="target trajectory",
    )
    actual_line, = ax.plot([], [], color="#f97316", linewidth=2.0, label="actual trajectory")
    target_point = ax.scatter([], [], marker="x", s=70, color="#1d4ed8", label="current target")
    vehicle_point = ax.scatter([], [], marker="o", s=54, color="#ea580c", label="current vehicle")
    time_text = ax.text(0.02, 0.98, "", transform=ax.transAxes, ha="left", va="top")

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("East y (m)")
    ax.set_ylabel("North x (m)")
    ax.set_title("Figure-Eight Tracking on NED XY Plane")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right", fontsize=8)

    def update(frame_index: int):
        i = indices[frame_index]
        current = tracking.iloc[i]
        history = tracking.iloc[: i + 1]
        actual_line.set_data(history["y"], history["x"])
        target_point.set_offsets([[current["target_y"], current["target_x"]]])
        vehicle_point.set_offsets([[current["y"], current["x"]]])
        time_text.set_text(f"NED XY plane\\nt = {current['tracking_time_s']:.1f} s")
        return actual_line, target_point, vehicle_point, time_text

    animation = FuncAnimation(fig, update, frames=len(indices), interval=90, blit=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    animation.save(output_path, writer=PillowWriter(fps=12), dpi=90)
    plt.close(fig)


def write_media_readme(output_path: Path, gif_path: Path, tracking: pd.DataFrame) -> None:
    size_mb = gif_path.stat().st_size / (1024 * 1024)
    lines = [
        "# Media",
        "",
        "This directory stores lightweight visual assets generated from committed CSV logs. No Gazebo recording or live simulation rerun is required.",
        "",
        "## Figure-Eight Tracking GIF",
        "",
        "- Source CSV: `logs/figure8_first_success.csv`",
        "- Output: `media/figure8_tracking.gif`",
        f"- Tracking samples in source CSV: `{len(tracking)}`",
        f"- GIF size: `{size_mb:.2f} MB`",
        "",
        "The GIF shows the target and actual XY trajectories in the PX4 local NED plane. The horizontal axis is East `y`, and the vertical axis is North `x`.",
        "",
        "This visualization is simulation-only and not evidence of real-aircraft readiness.",
        "",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    csv_path = args.csv.resolve()
    media_dir = args.media_dir.resolve()
    tracking = load_figure8(csv_path)
    gif_path = media_dir / "figure8_tracking.gif"
    generate_figure8_gif(tracking, gif_path, args.max_frames)
    write_media_readme(media_dir / "README.md", gif_path, tracking)

    print("GIF generated")
    print(f"gif={gif_path}")
    print(f"size_mb={gif_path.stat().st_size / (1024 * 1024):.2f}")
    print(f"media_readme={media_dir / 'README.md'}")


if __name__ == "__main__":
    main()
