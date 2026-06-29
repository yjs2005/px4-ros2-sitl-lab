# Project Pipeline

```mermaid
flowchart LR
  A["Windows 11 + WSL2 Ubuntu 22.04"] --> B["PX4 SITL + Gazebo Harmonic X500"]
  B --> C["Micro XRCE-DDS Agent"]
  C --> D["ROS 2 Humble / px4_msgs / px4_ros_com"]
  D --> E["Offboard hover node"]
  D --> F["Figure-eight node"]
  E --> G["CSV logs"]
  F --> G
  G --> H["Analysis scripts"]
  H --> I["Figures / metrics / README"]
```

The repository stores the project code, lightweight CSV logs, generated figures, and summary metrics. PX4-Autopilot and the ROS 2 workspace remain external dependencies.
