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

## Progress checkpoint (state of the project)

### What works end-to-end

- **ROS 2 Jazzy + Gazebo Harmonic + ros_gz bridge** — proven on this hardware.
- **Camera rig (kinematic stereo + segmentation + depth)** as an SDF in
  `ros2_ws/src/drone_description/models/camera_rig/`. Spawnable into any
  world. Outputs 4 image topics + 2 camera_info.
- **Capture pipeline** — `drone_sim_bringup/dataset_capture.py` teleports
  the rig through poses and saves PNG stereo + depth (16-bit mm) +
  semantic seg (8-bit per channel) + per-pose `metadata.json` +
  per-run `intrinsics.json`. Handles the "wait for fresh frame" race
  via header.stamp comparison.
- **Per-pixel semantic segmentation** working in two worlds:
  - `construction_labeled.sdf` — Clearpath construction site, .dae
    subdivided per material (9 classes), labels 10/50/51/60.
  - `orchard_labeled.sdf` — Clearpath olive orchard (48×38 m), 3 visuals
    (ground/trunks/leaves), labels 10/30/31. Centered at world origin
    via `<pose>-23.97 -18.92 0 0 0 0</pose>`.
- **Depth ground truth** via `depth_camera` sensor co-located with stereo_left,
  saved as 16-bit PNG in millimetres (KITTI-style).
- **PX4-Autopilot v1.16 SITL binary** — built (`build/px4_sitl_default/bin/px4`).
  See "PX4 SITL build gotcha" below for the next-step state.
- **Repo on GitHub**: https://github.com/abrar-nazib/drone-targeting-research
  (SSH remote, public).

### Tooling built

- `tools/label_world.py` — walks a world SDF, inserts `gz::sim::systems::Label`
  plugins on includes + inline models per `tools/labels.yaml` rules.
- `tools/label_fuel_model.py` — patches a Fuel-cached model's `model.sdf`
  to add a Label plugin to every visual (so spawned Fuel models carry labels).
- `tools/prefetch_fuel.py` — pre-downloads Fuel models referenced by a world,
  with cache-presence verification.
- `tools/fix_fuel_textures.py` — symlinks textures into mesh dirs +
  patches `.mtl` files to strip un-resolvable `model://` URI prefixes
  (works around the broken-textures bug in OpenRobotics car models).
- `tools/subdivide_dae_by_material.py` — Blender headless script that
  splits a `.glb` by material into per-material `.glb` files (with
  textures embedded).
- `tools/labels.yaml` — project label schema (background=0, ground=10,
  person=20, vegetation=30, tree=31, car=40, truck_bus=41, building=50,
  wall=51, street_furniture=60, water=70, terrain_natural=80, drone=90).

### Worlds available (under `ros2_ws/src/drone_sim_bringup/worlds/`)

- `empty_lab.sdf` — minimal smoke-test world.
- `urban_test.sdf` — hand-built urban scene (parked, mediocre visuals).
- `data_collection.sdf` — flat-color grass/road/soil strips (parked,
  PBR-on-primitives didn't render textures in Harmonic).
- `construction_labeled.sdf` — **active**. ~30×30 m, photo-textured.
- `orchard_labeled.sdf` — **active**. 48×38 m olive orchard, real aerial
  photo. Best world for the drone-follow-car scenario.
- `prayag_labeled.sdf` — 2.3 km satellite-textured terrain, Indian foothills.
  Visual quality the user found unacceptable; included for completeness.

### What's next (in flight)

The PX4 SITL `make px4_sitl gz_x500` test is the immediate next step. Once
SITL flies a stock x500 in Gazebo Harmonic, the plan continues:

1. Retune x500 SDF for FPV dynamics (TWR 7-12:1, faster motors).
2. Spawn a moving target rover (`r1_rover` or `rover_ackermann`,
   ships with PX4) on a programmed path through orchard or construction.
3. uXRCE-DDS bridge → ROS 2 Jazzy comms with the PX4 SITL.
4. State estimator + landing controller (the paper contribution).

## Hardware & environment context

- **ROS 2 Jazzy is installed at `/opt/ros/jazzy`** (system disk, not the SSD).
  This is intentional — apt-managed packages cannot be cleanly relocated to
  `/media/abrar/AbrarSSD` without breaking dependency resolution. Don't
  propose moving the ROS install.
- **Project files live on the SSD** (`/media/abrar/AbrarSSD/ROS/`):
  - This repo at `/media/abrar/AbrarSSD/ROS/drone_targeting_research/`.
  - Colcon workspace at `ros2_ws/`.
  - PX4-Autopilot at `/media/abrar/AbrarSSD/ROS/PX4-Autopilot/` (parallel
    to the project repo).
  - World/SDF assets, Fuel cache, dataset captures all on the SSD.
  System-disk free is ~134 GB; SSD free is ~380 GB.
- **Gazebo Fuel cache is symlinked to the SSD.** Harmonic does **not** honor
  `GZ_FUEL_CACHE_PATH` (env var doesn't exist), so the relocation is via
  symlink: `~/.gz/fuel -> data/gz_fuel_cache`. Don't restore the directory.
- **GPU: RTX 3050 Mobile (3.96 GB VRAM)**. Hard ceiling. Photoreal UE5
  interactive sims (CARLA / Cosys-AirSim photoreal / Isaac Sim) all
  require 6-8+ GB and are out. See "Dead-ends" below.
- **CPU: i5-11300H (8 threads), 32 GB RAM** — fine for everything we do.
- Linux (KDE Neon, Ubuntu 24.04 Noble base). ROS 2 **Jazzy Jalisco**.
  Sim target is **Gazebo Harmonic** (the REP-2000 pairing for Jazzy).

## Repo layout (current)

```
drone_targeting_research/
├── README.md             # original research rationale (superseded by CLAUDE.md)
├── CLAUDE.md             # this file (current source of truth)
├── SETUP.md              # rebuild-from-clean instructions
├── .gitignore            # excludes build artifacts, third-party clones, large textures
├── .claude/
│   ├── skills/
│   │   ├── ros/          # comprehensive ROS 2 Jazzy reference (~17 files)
│   │   └── px4-gazebo/   # PX4 SITL + Gazebo Harmonic + uXRCE-DDS reference (8 files)
│   └── agents/
│       └── ros-expert.md # subagent: ROS 2 / Gazebo / drone-sim specialist
├── tools/                # all the python helpers (label_world, prefetch_fuel, etc.)
├── research/             # deep-research deliverables from agents
│   ├── drone_simulation.md     # PX4 + Gazebo + FPV dynamics deep-dive
│   ├── prebuilt_worlds.md      # Clearpath / spaceros / etc.
│   ├── world_assets.md         # Fuel asset survey
│   └── photoreal_options.md    # CARLA/UE5/AirSim hardware reality + foundation models
├── ros2_ws/
│   ├── src/
│   │   ├── drone_description/  # camera rig SDF + subdivided meshes + prayag
│   │   ├── drone_sim_bringup/  # launches, capture node, worlds, bridge config
│   │   └── clearpath_simulator/  # third-party (gitignored, re-clone per SETUP.md)
│   ├── build/, install/, log/  # gitignored
└── data/
    ├── captures/         # dataset capture runs (gitignored)
    └── gz_fuel_cache/    # Fuel cache symlinked from ~/.gz/fuel (gitignored)
```

## Working agreements specific to this project

- **Use the `ros-expert` subagent** for any non-trivial ROS 2 question,
  package authoring, launch-file design, tf2 wiring, Gazebo bridge setup,
  or sim integration question. The agent is briefed on Jazzy + Harmonic
  specifically.
- **Use the `ros` skill** as the in-context cheat sheet for CLI commands,
  workspace layout, and core concepts. It is the first thing to consult
  before reaching for `WebFetch` against `docs.ros.org`.
- **Use the `px4-gazebo` skill** for any PX4 SITL / Gazebo Harmonic /
  uXRCE-DDS / offboard / `pxh>` / `failsafe_flags` / EKF2-debugging
  question. Covers all `gz_*` make targets, every stock world, custom
  airframes, FPV tuning, the full `/fmu/in/*` `/fmu/out/*` topic
  catalogue, and the lockstep-starvation + EKF2-missing-data diagnosis
  trees specific to this hardware. **Read the skill before web-searching
  PX4 docs.**
- ROS distribution is **Jazzy**. Don't generate commands for Humble / Iron /
  Foxy / Rolling without explicit confirmation.
- **Gazebo means modern Gazebo Harmonic** (`gz sim`), not Gazebo Classic.
  Bridge package is `ros_gz_bridge`, not `gazebo_ros`.
- Always source the underlay (`/opt/ros/jazzy/setup.bash`) **before** the
  workspace overlay (`install/local_setup.bash`), in a fresh terminal.
- **Default to the foundation-model + Gazebo-testbench plan.** Don't propose
  more interactive UE5 / Unity sims — they don't fit on 4 GB VRAM. See
  `research/photoreal_options.md` for the why.
- **Periodic git commits** to the public repo as we add code. SSH remote
  only (per global rule).

### Tool / build gotchas learned the hard way

- **PX4 SITL build for `gz_x500` needs ROS sourced + `GZ_DISTRO=harmonic`**
  before running CMake. Without it, the gz_bridge module can't find
  gz-transport / gz-sim and fails with "Gazebo simulation dependencies not
  found". Fix:
  ```bash
  source /opt/ros/jazzy/setup.bash
  export GZ_DISTRO=harmonic
  # If a stale cache from a prior build exists:
  cd build/px4_sitl_default && cmake . && cd -
  make px4_sitl gz_x500
  ```
- **Fuel `model://` URIs don't resolve to the cache** for old OpenRobotics
  car models. Two-part fix is in `tools/fix_fuel_textures.py`: symlink
  texture files into `meshes/` AND patch `.mtl` files to strip
  `model://` prefixes. Run it after every new Fuel download.
- **Ubuntu's apt-packaged Blender 4.0.2 was built without Collada support.**
  Use `assimp export <input>.dae <output>.glb glb2` to convert to .glb
  first, then Blender can import the .glb.
- **glTF axis convention is Y-up; Gazebo SDF is Z-up.** When using `<mesh>`
  geometry that points at a `.glb`, add `<pose>0 0 0 1.5708 0 0 0</pose>`
  on the model so the orientation is correct.
- **Spawned Fuel models silently get label 0 (background)** unless their
  `model.sdf` has a Label plugin. Use `tools/label_fuel_model.py` to patch
  the cached model.sdf before spawning.
- **GitHub auth on this machine is SSH only.** Per global rule, never use
  HTTPS — it prompts ksshaskpass and fails. `gh` is configured for SSH.

## Dead-ends (so we don't repeat them)

These were attempted and abandoned. Documented to prevent rediscovery:

- **CARLA 0.9.15** (8.4 GB). Official minimum is 6 GB VRAM; we have 4 GB.
  Download started, killed at 5.5 GB. Below the line.
- **CARLA 0.10** (UE5). Even higher VRAM requirement (16 GB+). Out.
- **Cosys-AirSim photoreal envs**. Need UE5 install (~150 GB) + 4-8 GB VRAM.
  Setup is multi-day. UE5 itself officially requires 8+ GB VRAM for
  photoreal envs.
- **Cosys-AirSim Blocks env**. Would run on 4 GB but Blocks is just colored
  boxes — worse visuals than what we already have in Gazebo. No win.
- **NVIDIA Isaac Sim**. Officially requires RTX 3070+ (8 GB). We have 3050 4 GB.
- **Microsoft AirSim**. Deprecated 2022. Skip.
- **Flightmare / RotorS / CoppeliaSim**. Evaluated and rejected per
  `research/photoreal_options.md` — RotorS is Gazebo Classic + ROS 1
  (its physics is in gz-sim already); Flightmare is stale + Unity VRAM;
  CoppeliaSim is unconventional for drone research.
- **Hand-built data_collection world with PBR ground textures**. PBR
  materials with `<albedo_map>` on primitive `<box>` / `<plane>` geometry
  silently fail texture-load in Harmonic and render as black. Workaround
  is to use mesh geometry with proper UVs (.glb / .obj). Parked the
  hand-built world; Clearpath assets are better.

## Out of scope (current framing)

- **Custom perception model training from scratch** — use foundation models
  (FoundationStereo, DepthAnything) instead. See `research/photoreal_options.md`.
- **Real hardware flight, hardware-in-loop with a real flight controller** —
  pure sim work for the paper.
- **Multi-drone / swarm** scenarios.
- **Reinforcement-learning policy training** — classical control + estimator
  is the contribution.
- **Photoreal interactive sim** — hardware doesn't permit. Period.
