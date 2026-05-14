# Setup notes (rebuild-from-clean)

This file records the system-level installs done so far so the project
is reproducible from a fresh clone.

## Apt packages installed

```bash
# ROS 2 Jazzy is at /opt/ros/jazzy/ on the system disk (per CLAUDE.md).
# Vendor-bundled Gazebo Harmonic ships with ros_gz; no separate install.

# Tooling for the Blender / mesh / texture pipeline
sudo apt install -y blender assimp-utils

# General build tools (also needed for PX4 SITL build)
sudo apt install -y \
  clang-18 lld-18 build-essential cmake \
  python3 python3-pip python3-venv \
  libsdl2-dev libglu1-mesa-dev libglew-dev xdg-utils \
  libfontconfig1-dev libfreetype-dev libxi-dev libxext-dev libxrandr-dev \
  libssl-dev libspeechd-dev libtbb-dev libuv1-dev \
  curl wget unzip rsync libomp5 libpng16-16
```

## Pip packages (user-local)

```bash
pip install --user --break-system-packages trimesh pycollada pygltflib
```

## External clones / installs (NOT committed to this repo)

- `~/.gz/fuel` symlinked to `data/gz_fuel_cache/` (per CLAUDE.md).

- `ros2_ws/src/clearpath_simulator/` — re-clone with:
  ```bash
  cd ros2_ws/src
  git clone -b jazzy --depth 1 https://github.com/clearpathrobotics/clearpath_simulator.git
  touch clearpath_simulator/clearpath_generator_gz/COLCON_IGNORE
  touch clearpath_simulator/clearpath_simulator/COLCON_IGNORE
  ```
  Build with: `colcon build --packages-select clearpath_gz drone_description drone_sim_bringup`.

- **PX4-Autopilot v1.16** — installed at `/media/abrar/AbrarSSD/ROS/PX4-Autopilot/`.
  Used for SITL drone control work (target tracking + landing on moving vehicle).
  Re-clone with:
  ```bash
  cd /media/abrar/AbrarSSD/ROS/
  git clone --recursive --branch v1.16.0 https://github.com/PX4/PX4-Autopilot.git
  cd PX4-Autopilot
  bash ./Tools/setup/ubuntu.sh    # WARN: targets Ubuntu 22.04, may need tweaks for 24.04
  make px4_sitl gz_x500           # first SITL build, ~30-60 min
  ```

## Large texture / mesh assets that are .gitignored but needed at runtime

- `ros2_ws/src/drone_description/models/prayag/textures/prayag_aerial.png`
  — re-download with:
  ```bash
  cd ros2_ws/src/drone_description/models/prayag/textures
  curl -LO https://raw.githubusercontent.com/saiaravind19/gazebo_terrain_generator/main/sample_worlds/prayag/textures/prayag_aerial.png
  ```

- `ros2_ws/src/drone_description/models/office_subdivided/meshes/*.glb`
  — regenerate with:
  ```bash
  cp /path/to/clearpath_gz/meshes/office/*.jpg /tmp/
  assimp export <clearpath>/meshes/office/office_construction.dae /tmp/office_construction.glb glb2
  blender --background --python tools/subdivide_dae_by_material.py -- \
    /tmp/office_construction.glb \
    ros2_ws/src/drone_description/models/office_subdivided/meshes
  ```

- Fuel models: prefetch with `tools/prefetch_fuel.py <world.sdf>` then
  patch with `tools/fix_fuel_textures.py` and (per-prop labels) with
  `tools/label_fuel_model.py <subpath> <label>`.

## Dead-ends (kept here as breadcrumbs so we don't repeat them)

- **CARLA 0.9.15**: 8.4 GB download started, scrapped. Official minimum is
  6 GB VRAM; we have 4 GB. Below the line.
- **Cosys-AirSim full photoreal**: needs UE5 (8 GB+ VRAM minimum) plus a
  ~150 GB UE5 source install. Not viable on this hardware.
- **Cosys-AirSim Blocks env**: would run on 4 GB but Blocks is just colored
  boxes, worse visuals than what we already have in Gazebo.
- **NVIDIA Isaac Sim**: needs RTX 3070+ (8 GB).

The hardware ceiling is real. Photoreal interactive sims are out.

## What we landed on (per the project pivot)

The project is a **control / drone-target-tracking research project**, not
a perception-dataset research project. Photoreal visuals are not on the
critical path. We use:

- **Gazebo Harmonic** (existing) for the simulator
- **PX4 SITL v1.16** for FPV drone flight dynamics + Acro-mode rate control
- **Existing Gazebo worlds** (orchard, construction, etc.) for the scene
- **Existing perception captures + foundation models** as building blocks
  for the higher-level control loop
- The **paper contribution** lives in the trajectory planner / state
  estimator / landing controller for moving targets, not in the perception.
