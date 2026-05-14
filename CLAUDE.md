# Drone Targeting Research

## Goal (current framing — pivoted from the original README)

Academic / paper-shaped research project: **autonomous landing of an FPV
quadrotor on a moving ground vehicle, using stereo onboard perception.**

The contribution lives in the **control / trajectory planner / state
estimator / landing controller** — not in perception and not in
photorealism. Perception is a building block: pretrained foundation
model on Gazebo's RGB output (or ground-truth depth in early prototyping).
The Gazebo orchard / construction worlds are the deployment testbench;
visuals do not need to be photoreal for control-loop research.

The original README scope ("create dataset, train stereo+seg model from
scratch, photoreal worlds") is **superseded by this control framing.**
The 4 GB GPU made photoreal interactive sim impossible (CARLA / UE5 / Isaac
Sim all need 6-8 GB+). Instead of fighting the hardware wall we use
existing perception models and put the research effort in the control
layer.

The pipeline this repo supports:

1. ROS 2 Jazzy (installed at `/opt/ros/jazzy/`).
2. **Gazebo Harmonic** as the simulator (already wired up).
3. **PX4-Autopilot v1.16 SITL** with the FPV-tuned x500 (TWR 7-12:1) for
   real flight dynamics. Installed at `/media/abrar/AbrarSSD/ROS/PX4-Autopilot/`.
4. Existing Gazebo worlds (orchard, construction, etc.) as the scene.
   Visual fidelity is not in scope.
5. A moving target vehicle (Fuel car driven on a programmed path through
   the world) as the landing target.
6. A target detection / tracking pipeline (ground-truth pose initially,
   foundation perception model later if time permits).
7. A trajectory planner + landing controller — the actual paper
   contribution.

The README.md remains in the repo as the original scope statement.
Anything in this CLAUDE.md supersedes it for current work.

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
