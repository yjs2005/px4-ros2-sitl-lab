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

GIF generation is separate:
  python3 analysis/generate_gifs.py
MSG
