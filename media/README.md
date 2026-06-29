# Media

This directory stores lightweight visual assets generated from committed CSV logs. No Gazebo recording or live simulation rerun is required.

## Figure-Eight Tracking GIF

- Source CSV: `logs/figure8_first_success.csv`
- Output: `media/figure8_tracking.gif`
- Tracking samples in source CSV: `758`
- GIF size: `0.60 MB`

The GIF shows the target and actual XY trajectories in the PX4 local NED plane. The horizontal axis is East `y`, and the vertical axis is North `x`.

This visualization is simulation-only and not evidence of real-aircraft readiness.

## Gazebo Screenshots And Videos

Optional Gazebo screenshots can be saved under:

```text
media/screenshots/
```

Optional videos can be saved under:

```text
media/videos/
```

Suggested demos:

- `circle_gazebo_demo`
- `circle_baseline_vs_feedforward`
- `square_gazebo_demo`
- `square_baseline_vs_smooth`
- `figure8_gazebo_demo`

Large videos should not be committed by default. See `docs/visual_recording.md`.
