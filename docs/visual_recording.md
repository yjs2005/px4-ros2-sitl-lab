# Visual Recording

This document explains how to capture visual evidence of PX4 SITL trajectory experiments. Do not rerun these steps unless you intentionally want to perform a new SITL experiment.

## Watch The Vehicle In Gazebo

Start the required processes in this order:

1. Open QGroundControl, or otherwise resolve SITL preflight checks.
2. Start Micro XRCE-DDS Agent:

```bash
MicroXRCEAgent udp4 -p 8888
```

3. Start PX4 SITL Gazebo:

```bash
cd ~/src/PX4-Autopilot
make px4_sitl gz_x500
```

4. Run a trajectory node:

```bash
bash scripts/run_trajectory.sh circle
```

Supported trajectories:

```text
hover line square circle figure8 z_step
```

## Screenshots

Use Windows screenshot:

```text
Win + Shift + S
```

Suggested output folder:

```text
media/screenshots/
```

Suggested names:

- `circle_gazebo_demo.png`
- `square_gazebo_demo.png`
- `figure8_gazebo_demo.png`

## Screen Recording

Options:

- Windows Game Bar: `Win + G`
- OBS Studio

Suggested output folder:

```text
media/videos/
```

Suggested recordings:

- `circle_gazebo_demo`
- `square_gazebo_demo`
- `figure8_gazebo_demo`

Do not commit large raw videos by default. Keep large videos local, or use a documented release asset / Git LFS workflow if a video must be published.

## CSV GIF vs Gazebo Video

`media/figure8_tracking.gif` is generated offline from `logs/figure8_first_success.csv`. It visualizes tracking data and does not require Gazebo.

Gazebo screenshots or videos show the simulated vehicle in the 3D scene. They are useful for presentation, but they should be kept small and intentionally curated.
