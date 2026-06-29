#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${repo_root}"

echo "Running offline analyses from: ${repo_root}"
echo

python3 analysis/analyze_offboard_hover.py
echo
python3 analysis/analyze_figure8.py
echo
python3 analysis/generate_summary_visuals.py
echo
python3 analysis/analyze_trajectory_suite.py
echo
python3 analysis/compare_control_modes.py

cat <<'MSG'

Generated result files:
  results/offboard_hover_metrics.md
  results/offboard_hover_metrics.json
  results/figure8_metrics.md
  results/figure8_metrics.json
  results/summary_metrics.md
  results/summary_metrics.json
  results/summary_metrics.csv
  results/figures/metrics_summary.png
  results/project_pipeline.md
  results/trajectory_suite_metrics.md
  results/trajectory_suite_metrics.json
  results/trajectory_suite_metrics.csv
  results/figures/trajectory_suite_metrics.png
  results/control_comparison_metrics.md
  results/control_comparison_metrics.json
  results/control_comparison_metrics.csv
  results/figures/control_comparison_xy_rmse.png
  results/figures/control_comparison_3d_rmse.png
  results/figures/control_comparison_percent_improvement.png

GIF generation is separate:
  python3 analysis/generate_gifs.py
MSG
