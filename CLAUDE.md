# Drone Targeting Research

## Goal

Build a ROS 2-based simulation environment to train an FPV drone to follow a
target. The pipeline this repo is meant to support, end-to-end:

1. ROS 2 (Jazzy) installed on the SSD (this disk), not the user's main device.
2. A photoreal-quality simulator wired to ROS 2.
3. Two world variants:
   - **Urban**: cars, humans, roads, houses.
   - **Open terrain**: trees, forest, mountains, roads, occasional houses.
   World assets must look as close to picture-perfect as possible.
4. A dataset captured from a stereo camera mounted on the simulated drone,
   sampled across many positions, with per-pixel semantic segmentation labels.
5. A stereo vision model trained on that dataset to do (a) depth estimation
   and (b) semantic segmentation.

The README.md in this directory is the source of truth for scope. Do not
silently expand beyond it.

## Hardware & environment context

- **ROS 2 Jazzy is installed at `/opt/ros/jazzy`** (system disk, not the SSD).
  This is intentional — apt-managed packages cannot be cleanly relocated to
  `/media/abrar/AbrarSSD` without breaking dependency resolution. Don't
  propose moving the ROS install.
- **Project files live on the SSD** (`/media/abrar/AbrarSSD/ROS/`) wherever
  possible — that is the storage priority. This includes:
  - This repo (already there).
  - The colcon workspace at `ros2_ws/` (created).
  - World/SDF assets, mesh libraries, downloaded Gazebo Fuel collections.
  - Stereo dataset captures and any rosbag recordings.
  - Model checkpoints and training artifacts.
  System-disk free space is 134 GB and shrinking; SSD free space is 387 GB.
- **Gazebo Fuel cache is symlinked to the SSD.** Harmonic does **not** honor
  a `GZ_FUEL_CACHE_PATH` env var (it doesn't exist in this version), so the
  only way to relocate the cache is via symlink or the gz config file.
  Done as: `~/.gz/fuel -> /media/abrar/AbrarSSD/ROS/drone_targeting_research/data/gz_fuel_cache`.
  Don't restore the `~/.gz/fuel` directory directly — keep the symlink.
- The user's training GPU is an **RTX 3050 (3.96 GB VRAM)** — small. Any ML
  training step (stereo / segmentation model) must follow the global GPU
  utilization rule (≥85% of available memory at the chosen batch/resolution).
  Don't blindly copy batch sizes from larger-GPU references.
- Linux (Ubuntu-family). ROS 2 **Jazzy Jalisco** is the target distribution
  (matches Ubuntu 24.04 Noble). Sim target is **Gazebo Harmonic** (the pair
  REP-2000 designates for Jazzy).

## Repo layout (current and intended)

```
drone_targeting_research/
├── README.md              # research rationale (source of truth for scope)
├── CLAUDE.md              # this file
└── .claude/
    ├── skills/
    │   └── ros/SKILL.md   # ROS 2 Jazzy reference for this project
    └── agents/
        └── ros-expert.md  # subagent: ROS 2 / Gazebo / drone-sim specialist
```

A ROS 2 workspace (`ros2_ws/src/...`) and dataset/model directories will be
added as the project progresses — they don't exist yet.

## Working agreements specific to this project

- **Use the `ros-expert` subagent** for any non-trivial ROS 2 question,
  package authoring, launch-file design, tf2 wiring, Gazebo bridge setup,
  or sim integration question. The agent is briefed on Jazzy + Harmonic
  specifically.
- **Use the `ros` skill** as the in-context cheat sheet for CLI commands,
  workspace layout, and core concepts. It is the first thing to consult
  before reaching for `WebFetch` against `docs.ros.org`.
- ROS distribution is **Jazzy** unless the user says otherwise. Do not
  generate commands for Humble, Iron, Foxy, or Rolling without explicit
  confirmation — the apt package names and REP-2000 sim pairings differ.
- Gazebo means **modern Gazebo (gz sim)**, not Gazebo Classic. The bridge
  package is `ros_gz_bridge`, not `gazebo_ros`.
- Always source the underlay (`/opt/ros/jazzy/setup.bash`) **before**
  sourcing a workspace overlay (`install/local_setup.bash`), and do it in a
  fresh terminal — don't build and source in the same shell.

## Out of scope (for now)

- Real hardware flight, PX4/Ardupilot integration, RC link work — sim only.
- Reinforcement-learning policy training — the README scopes this phase to
  perception (depth + segmentation), not control.
- Multi-robot or swarm scenarios.
