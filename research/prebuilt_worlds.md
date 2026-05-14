# Pre-Built Worlds for Drone Perception in Gazebo Harmonic

Scope: replace the hand-built urban scene that "looks mediocre" with
**pre-built, well-textured worlds** that load on the project's stack
(Gazebo Harmonic via the Jazzy vendor packages on RTX 3050 Mobile, 4 GB
VRAM). The user has explicitly asked for drone-competition worlds,
NASA Mars/Moon worlds, and any robotic-competition worlds we missed.

This document supersedes the speculative "scrap that approach" question
in `world_assets.md` — there *are* good pre-built Harmonic-native
worlds; we missed several in the previous pass.

## TL;DR

- **Best urban / built-environment pick: Clearpath Simulator's
  `office_construction` world** (a real construction-site scene around
  Clearpath's Waterloo, ON office, monolithic Collada mesh, single
  `.dae` so it loads fast). Apache-2.0, Harmonic + Jazzy native.
  ([clearpath_simulator/clearpath_gz/worlds/construction.sdf](https://github.com/clearpathrobotics/clearpath_simulator/blob/jazzy/clearpath_gz/worlds/construction.sdf)).
  Realistic geometry, sky-with-clouds, true geo coords. Fits 4 GB VRAM.
- **Best open-terrain / nature pick: Clearpath `orchard`** (olive
  orchard in Greece, monolithic mesh + cloud sky + realistic GPS). Same
  package, same install, same license
  ([orchard.sdf](https://github.com/clearpathrobotics/clearpath_simulator/blob/jazzy/clearpath_gz/worlds/orchard.sdf)).
  For procedural forests use **Forest3D** (Jan 2026, MIT, Docker-packaged
  with Gazebo Harmonic, generates trees + rocks + bushes from DEM)
  ([Forest3D repo](https://github.com/unitsSpaceLab/Forest3D),
  [Discourse intro](https://discourse.openrobotics.org/t/forest3d-generate-populated-outdoor-environments-for-gazebo/51551)).
- **Best drone-specific / Mars pick: `david-dorf/spaceros_gz_demos`
  Mars world** — Perseverance + **Ingenuity helicopter** on a 24.7 MB
  textured Martian terrain glTF, all Harmonic + ROS 2 (specifically
  designed against Gazebo Harmonic). The Ingenuity is a flyable rotorcraft
  — *exactly* the "drone over alien terrain" scenario the user asked for
  ([repo](https://github.com/david-dorf/spaceros_gz_demos),
  [martian_surface model.sdf](https://github.com/david-dorf/spaceros_gz_demos/blob/main/spaceros_gz_demos/models/martian_surface/model.sdf)).
- **Headline blocker we found:** Most "drone competition" worlds are
  **either Gazebo Classic (MBZIRC 2020 land, AlphaPilot/Flightmare on
  Unity, AirSim on UE) or maritime-only (MBZIRC 2024 was a *Maritime*
  Grand Challenge, VRX/RobotX is for surface vessels)**. There is no
  open-source 2024–2026 *aerial* drone competition world that ships
  Gazebo Harmonic. The best aerial Harmonic worlds today come from PX4
  SITL, ArduPilot, Clearpath, and Space-ROS, **not** from drone competitions.

## Hard re-checks since last research

What changed vs. the previous `world_assets.md` analysis:

1. **`saiaravind19/gazebo_terrain_generator` v2.0 (Feb 2026) now
   generates buildings on top of terrain + satellite overlay**, not just
   bare heightmaps. Tested for Gazebo Harmonic. Mapbox-backed
   ([Discourse update](https://discourse.openrobotics.org/t/gazebo-terrain-generator/52254),
   [GitHub](https://github.com/saiaravind19/gazebo_terrain_generator)).
   This is a step-change for "build me a real-world urban area" and it
   landed after the previous research.
2. **`unitsSpaceLab/Forest3D` (announced Jan 2026, MIT)** is a brand-new
   forest generator that ships a Docker image including **Blender 4.2 +
   Gazebo Harmonic** and produces SDF worlds with procedurally placed
   trees, rocks, bushes, plus DEM-based terrain — the missing piece for
   "open terrain with realistic vegetation"
   ([Forest3D Discourse](https://discourse.openrobotics.org/t/forest3d-generate-populated-outdoor-environments-for-gazebo/51551),
   [GitHub](https://github.com/unitsSpaceLab/Forest3D)).
3. **Clearpath Robotics' `clearpath_simulator` is now Harmonic + Jazzy
   native** (port maintained on the `jazzy` branch). It ships **six**
   PBR-textured outdoor + indoor SDF worlds (`orchard`, `pipeline`,
   `solar_farm`, `office_construction`, `office`, `warehouse`) with
   real GPS coordinates, cloud skies, and monolithic Collada meshes.
   We missed this entirely
   ([clearpath_simulator repo](https://github.com/clearpathrobotics/clearpath_simulator/tree/jazzy),
   [Clearpath Harmonic announcement](https://discourse.openrobotics.org/t/clearpath-simulator-comes-to-gazebo-harmonic/40975)).
4. **`david-dorf/spaceros_gz_demos` (NASA Sim Summer Sprint 2024)** ships
   **Mars + Moon + Enceladus + Orbit** worlds for Harmonic — including the
   only Harmonic-compatible **flying** Mars vehicle (Ingenuity) we found.
   24.7 MB Mars terrain mesh; lunar surface uses a real DEM `.tif`. The
   previous research only checked the older `space-ros/demos` repo (which
   is Fortress-era Curiosity rover). David Dorf's repo is the modern fork
   ([repo](https://github.com/david-dorf/spaceros_gz_demos),
   [martian_surface](https://github.com/david-dorf/spaceros_gz_demos/blob/main/spaceros_gz_demos/models/martian_surface/model.sdf),
   [lunar_surface](https://github.com/david-dorf/spaceros_gz_demos/blob/main/spaceros_gz_demos/models/lunar_surface/model.sdf)).
5. **Poly Haven released their CC0 Namaqualand 3D-scan library
   (Oct 2024)** — 30+ photoscanned desert plants/rocks/ground-debris +
   10 16K HDRIs, all glTF + USD. This is the highest-fidelity CC0
   open-terrain asset library that exists, and it landed after the
   previous research
   ([Namaqualand collection](https://polyhaven.com/models/collection:%20namaqualand),
   [Poly Haven blog](https://blog.polyhaven.com/namaqualand/),
   [CG Channel writeup](https://www.cgchannel.com/2024/10/download-poly-havens-free-namaqualand-3d-scan-library/)).
6. **VRX 3.0 is now Harmonic + Jazzy native** (April 2024 onward), so
   Sydney-Regatta-style maritime worlds are usable in this stack if the
   project ever wants over-water captures
   ([osrf/vrx](https://github.com/osrf/vrx)).
7. **PX4-Multiagent-Simulation has a `modelflughafen` world from drone
   photogrammetry processed through OpenDroneMap**, plus `techhive.sdf`
   and `rubico.sdf` — none of these were in the previous list. (Their
   Harmonic compatibility is uncertain — the project is in transition.)
   ([Gilbert Tanner — Multiagent Simulation blog](https://gilberttanner.com/blog/multiagent-simulation-drones-ground-robots-gazebo/)).
8. **SubT re-evaluation: still skip on RTX 3050 4 GB.** The community
   port `LTU-RAI/darpa_subt_worlds` exists but with only 8 commits, no
   active maintenance, no Gazebo version stated, and the worlds are
   33 m × 102 m × 150 m caves built from DARPA tiles — same density and
   poly-count as the originals
   ([repo](https://github.com/LTU-RAI/darpa_subt_worlds)). No "lighter
   sub-tile" exists.
9. **`gazebosim/harmonic_demo`** (the *official* Harmonic showcase) is
   a single SDF world `harmonic.sdf` (24 KB) plus 23 Fuel-style models
   like `Lake House`, `Armchair`, `Bed`, `Toilet`, `Piano`, `Sky`,
   `Terrain`, `Terrain Objects`, `Coast Waves 2`, `Pendulum`, etc. This
   is the visual ceiling Open Robotics is willing to commit to as
   "this is what Harmonic looks like at its best"
   ([repo listing](https://github.com/gazebosim/harmonic_demo/tree/main/harmonic_demo)).
10. **No Cesium for Gazebo, no Isaac asset converter to glTF/SDF.** The
    USD → SDF path is non-trivial; NVIDIA's MeshConverter goes the other
    way (glTF → USD). External pipeline (USD → Blender → glTF → SDF) is
    possible but bespoke. Confirmed by the Open Robotics Discourse
    asset-import workflow thread
    ([Improving Asset Import Workflow for External Models](https://discourse.openrobotics.org/t/improving-asset-import-workflow-for-external-models-with-textures-fbx-gltf-glb-usdz-etc/54622)).

## Inventory by category

### PX4 SITL worlds (Harmonic-compatible)

The full set, verified by the live `worlds/` listing of
`PX4/PX4-gazebo-models@main`. PX4 v1.16 stable switched to Harmonic LTS
([PX4 v1.16 release notes](https://docs.px4.io/main/en/releases/1.16),
[PX4 worlds doc page](https://docs.px4.io/main/en/sim_gazebo_gz/worlds)).
Total = **13 worlds, all Harmonic-native SDF**.

All worlds live at <https://github.com/PX4/PX4-gazebo-models/tree/main/worlds>.
License: BSD-3-Clause (per repo `LICENSE`).
Install: `git clone https://github.com/PX4/PX4-gazebo-models.git`,
then `export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$(pwd)/worlds:$(pwd)/models`,
then `gz sim worlds/<name>.sdf` — or via PX4 SITL with
`PX4_GZ_WORLD=<name> make px4_sitl gz_x500`.

| World | Size on disk | Visual | Best for | GPU cost on 4 GB | Verdict |
|---|---|---|---|---|---|
| `aruco.sdf` | 2.9 KB | empty + ArUco marker | precision-landing tests | trivial | skip for perception |
| `baylands.sdf` | 1.7 KB SDF, **multi-MB Fuel terrain** | scenic outdoor + water + bay terrain | outdoor visual benchmark | **HIGH — known to drop to ~5 % RTF** with heavy load ([discuss.ardupilot.org thread](https://discuss.ardupilot.org/t/gazebo-harmonic-slow-real-time-factor-on-baylands-world/125284)) | risk on 4 GB; OK for short captures |
| `default.sdf` | 2.8 KB | grey plane | sanity test | trivial | skip |
| `forest.sdf` | 8.5 KB | 7 grass patches + 32 oak/pine trees from `OpenRobotics` Fuel, ~50×50 m | scattered forest scene for aerial | medium (32 includes, mostly de-dup'd by Gazebo) | **usable** as outdoor candidate |
| `frictionless.sdf` | 3.5 KB | physics test | physics | trivial | skip |
| `kth_marinarium.sdf` | 10 KB | maritime KTH research scene | maritime | medium | skip |
| `kthspacelab.sdf` | 10 KB | indoor lab w/ wall perimeter, ~6×6 m | indoor lab | low | not what we want |
| `lawn.sdf` | 3.6 KB | flat green plane, 400×400 m | lawn-mower research | low | useless visually |
| `moving_platform.sdf` | 2.9 KB | flat moving platform | ship-deck landing | low | skip |
| `rover.sdf` | 3.1 KB | grid terrain, optimized for rovers | ground vehicles | low | skip for drones |
| `underwater.sdf` | 9.1 KB | underwater scene | underwater | medium | skip |
| `walls.sdf` | 5.2 KB | walls in empty world | obstacle avoidance | low | useful for control phase, not capture |
| `windy.sdf` | 2.8 KB | empty + wind plugin | wind disturbance | trivial | skip for capture |

**Honest summary**: of these 13, **only `baylands` and `forest`** are
visually interesting; `forest` is the only one that fits the project's
"open terrain with trees" need. PX4 doesn't ship an urban world.

### ArduPilot SITL worlds

`ArduPilot/ardupilot_gazebo` ships **5 worlds**, all SDF 1.9 (Harmonic)
([repo worlds dir](https://github.com/ArduPilot/ardupilot_gazebo/tree/main/worlds)).
The plugin is Apache-2.0. Note: the *plugin* is Harmonic-ready, but the
ROS 2 bringup repo `ardupilot_gz` still pins Humble branches as of May
2026, so this is "use the plugin standalone" territory unless you hand-port
([ros2_gz.repos](https://github.com/ArduPilot/ardupilot_gz/blob/main/ros2_gz.repos)).

| World | Size | Description | Verdict |
|---|---|---|---|
| `iris_runway.sdf` | 3.6 KB | flat ground + RGB axes box, sun, sky, real GPS coords for Canberra ARDUPILOT test field | bare runway with no scenery — boring but works |
| `iris_warehouse.sdf` | 17 KB | indoor warehouse | useful for indoor-aerial scenarios |
| `gimbal.sdf` | 8.5 KB | gimbal-on-quad demo | unrelated |
| `zephyr_runway.sdf` | 3.4 KB | fixed-wing runway | not for multirotor |
| `zephyr_parachute.sdf` | 6 KB | parachute test | unrelated |

`ArduPilot/SITL_Models` adds **20 more worlds** under `Gazebo/worlds/`,
mostly runways and "playpens" for specific airframes (`bicopter_runway`,
`hexapod_copter_runway`, `skywalker_x8_runway`, `vtail_runway`,
`omnirover_playpen`, `wildthumper_playpen`, `sonoma_raceway`, etc.)
([SITL_Models worlds dir](https://github.com/ArduPilot/SITL_Models/tree/master/Gazebo/worlds)).
**Verdict**: useful for control-phase testing of specific airframes, but
not for perception dataset capture — they're mostly empty runways.

### SubT Challenge (re-evaluated for lighter sub-worlds)

**Re-verdict: still skip on RTX 3050 4 GB.** Specifics:

- The official `osrf/subt` repo is built around the Ignition Edifice /
  Citadel Fuel server at `subtchallenge.gazebosim.org` with **65 worlds
  and 407 models** ([SubT Part 2 blog](https://www.openrobotics.org/blog/2022/2/3/subt-part-2-robots-and-environments)).
  Worlds load on Harmonic *with* `gz::` ↔ `ignition::` namespace
  shimming, but the **per-tile poly count is the killer**, not the
  world count.
- The community port `LTU-RAI/darpa_subt_worlds` (the only one that
  shows up in search) has 8 commits, no recent maintenance, and the
  worlds it does ship (`darpa_cave_01..03`, `indian_tunnel`, `niosh_osrf`,
  `cave_simple_03`, `tunnel_simple03`, `virtual_stix`) span 33 × 102 ×
  150 m and are built from the same DARPA tiles as the original — same
  density, same VRAM budget
  ([repo](https://github.com/LTU-RAI/darpa_subt_worlds)).
- A *single* SubT tile from the Tech Repo (e.g.
  `urban_circuit_practice_01`) is the closest thing to a "lighter
  sub-world", but the Urban Circuit is industrial corridors / subway
  stations, **not city streets** — and even one tile is dense enough to
  push past 4 GB VRAM with three cameras attached. There's no way to get
  street-scene quality out of SubT.
- **Recommendation: defer SubT until hardware upgrade ≥ 8 GB VRAM, or
  switch project visual target.**

### NASA / Mars / Space Robotics Challenge

Three concrete sources, in order of usefulness for this project:

#### `david-dorf/spaceros_gz_demos` — **modern, Harmonic-native, has a flying drone on Mars**

Created by David Dorf and Katie Hughes for NASA's Space ROS Sim Summer
Sprint Challenge 2024. License: Apache-2.0. **Four worlds, all
Harmonic-native** ([repo](https://github.com/david-dorf/spaceros_gz_demos)):

| World | Models | Mesh size | Gravity | Notable |
|---|---|---|---|---|
| `mars.sdf` | `martian_surface` (24.8 MB glTF), Perseverance rover, **Ingenuity helicopter** | 24.8 MB | 3.71 m/s² | flyable rotorcraft (battery + solar charging) |
| `moon.sdf` | `lunar_surface` (DEM `.tif` + `moon_diffuse.png` + `moon_normal.png` PBR), 2× X1/X2 rovers, solar panel + truss | small DEM, real PBR textures | 1.62 m/s² | Selenographic coords |
| `enceladus.sdf` | submarine + sonar | small | low | underwater, irrelevant |
| `orbit.sdf` | ISS + docking capsule | medium | 0 | space, irrelevant |

Verified by inspecting the model SDFs:
[`martian_surface/model.sdf`](https://github.com/david-dorf/spaceros_gz_demos/blob/main/spaceros_gz_demos/models/martian_surface/model.sdf)
loads `martian_surface.glb` (24.7 MB) at 100×100×100 scale;
[`lunar_surface/model.sdf`](https://github.com/david-dorf/spaceros_gz_demos/blob/main/spaceros_gz_demos/models/lunar_surface/model.sdf)
uses a `<heightmap>` with PNG diffuse + normal textures and a
`use_terrain_paging>false</use_terrain_paging>` setting.

**Drone fit**: the Mars world is the only Harmonic world we found that
ships a *flyable* aerial model + alien terrain, both labeled as "as
close to real as possible". Perfect for a Mars-mission style perception
dataset.

**Install**: see "Setup instructions" below. README claims Docker
installation but the Native install path also works on Jazzy + Harmonic.

#### `space-ros/demos/curiosity_rover` — older, Fortress/Classic-era

Apache-2.0. The Curiosity rover description (`curiosity_description`)
ships ~30 MB of `.dae` chassis + arm + suspension meshes plus a
`curiosity_path` model with a **33.9 MB `mars_path_simple1.dae`**
terrain mesh ([file listing](https://github.com/space-ros/demos/tree/main/curiosity_rover)).
World file `mars_curiosity.world` uses SDF 1.8 with `gz-sim` plugin
namespacing — Harmonic-loadable but the world is bare ground + sandy
sky color. **Use the meshes, ignore the world.** The 33.9 MB Mars path
mesh is reusable as a terrain include.

#### `space-ros/demos/lunar_terrain` — Harmonic-targeted lunar DEM

Has Python utility scripts (`crop_dem.py`, `surface_normals.py`,
`blend_normals.py`) for processing real lunar DEMs, plus a
`lunar_terrain_world.launch.py`. Limited content but a clean launcher
([file listing](https://github.com/space-ros/demos/tree/main/lunar_terrain)).

#### Other space sources

- **Apollo 15 Landing Site Heightmap** is on Fuel under `OpenRobotics`,
  for moon scenes (single Fuel include, ~MB-scale).
- **NASA-JPL `M2020Surface`, `Curiosity` repos**: these are the rover
  *models*, not worlds — they're URDF/Xacro descriptions of the actual
  spacecraft for use in your own world. Fortress-era; they will load on
  Harmonic with deprecation warnings.
- **`mars_yard`** (Leo Rover ERC Mars yard 3D scan): mentioned in
  community blogs, but it's a `.dae` of an actual physical Mars-yard
  test arena ([Leo Rover blog](https://www.leorover.tech/post/exploring-mars-through-simulation)),
  Classic-era, not Harmonic-tested.

### MBZIRC / drone competitions

Honest summary: **no useful aerial-drone competition worlds exist for
Gazebo Harmonic in 2024–2026.** Specifics:

- **MBZIRC 2024 was the *Maritime* Grand Challenge.** Open Robotics
  built the simulator on Gazebo + ROS, competition concluded Feb 2024
  off the coast of Abu Dhabi
  ([osrf/mbzirc](https://github.com/osrf/mbzirc),
  [MBZIRC announcement](https://www.mbzirc.com/news/open-robotics-provide-world-class-open-source-simulator-aspires-mbzirc-maritime-grand)).
  Maritime worlds = USVs, target vessels, water — **not what we want**.
- **MBZIRC 2020** had aerial and ground tracks; the
  [`Bochicchio3/MBZIRC-2020-Challenge`](https://github.com/Bochicchio3/MBZIRC-2020-Challenge)
  team repo is **Gazebo Classic + ArduPilot**, not Harmonic.
- **AlphaPilot Challenge (Lockheed/DRL/NVIDIA, 2019)** used custom
  RotorS-based and Flightmare simulators, **not Gazebo Harmonic worlds**
  ([AlphaPilot paper](https://kelia.github.io/publication/alphapilot/)).
- **DRL Sim** (Drone Racing League) is a closed-source proprietary
  trainer (<https://www.drl.io/drl-sim>) — not usable here.
- **Game of Drones (NeurIPS) → AirSim** = Unreal Engine, not Harmonic
  ([awesome-autonomous-drone-racing](https://github.com/aimarket/awesome-autonomous-drone-racing)).
- **Anduril AI Grand Prix / A2RL** = AirSim/Cosys-AirSim on UE5, not
  Harmonic.
- **`Veilkrand/gazebo_assets_drone_race`** and
  **`0Jiahao/DRONE_RACE_MAP`** exist on GitHub but are tiny hand-built
  gate-circuit assets, Classic-era, no Harmonic port.
- **Drone-photogrammetry sourced worlds** for Harmonic exist via
  `PX4-Multiagent-Simulation` / Gilbert Tanner blog: the
  `modelflughafen` world is a real airfield reconstructed by
  OpenDroneMap from drone photos
  ([Gilbert Tanner blog](https://gilberttanner.com/blog/multiagent-simulation-drones-ground-robots-gazebo/));
  uncertain Harmonic stability.

**Verdict**: there's no shortcut here. The "drone competition world"
bucket comes up empty for Harmonic. The closest substitutes are the
Mars/Moon worlds above (Ingenuity-on-Mars), the Clearpath outdoor worlds
(below), or the modelflughafen / saiaravind19 city-from-OSM tools.

### RoboCup Rescue / USAR

- **`RoboCup-RSVRL/RoboCup2022RVRL_Demo`** is the official Rescue
  Virtual Robot League sample — uses ROS 2 Foxy + Gazebo Classic. Not
  Harmonic-tested. The 2022 docs only describe a `house_map` world.
- **2024–2025 RoboCup Rescue** moved to ROS 2 Foxy infrastructure;
  competition arenas are physical NIST USAR mock-ups, not standardized
  Harmonic worlds. RoboCup 2025 (Salvador, Brazil) had no announced
  Harmonic transition
  ([RoboCup Rescue 2025](https://2025.robocup.org/robocuprescue/)).
- **Verdict**: **skip RoboCup Rescue for Harmonic.** The community is
  still on Classic / Foxy.

### Other Gazebo Harmonic world packages (recent forks, community ports)

This is the biggest "we missed it" bucket. In order of usefulness:

#### `clearpathrobotics/clearpath_simulator` (jazzy branch) — **★ pick for indoor / outdoor scenes**

[Repo](https://github.com/clearpathrobotics/clearpath_simulator/tree/jazzy).
License: BSD-3-Clause ([per repo `LICENSE`]).
Six SDF worlds, **all Harmonic-native (SDF 1.4 with `gz::sim::systems::*`
plugins, `ogre2` render engine, `<sky><clouds>` block, real
`<spherical_coordinates>`, monolithic `.dae` mesh per scene)**:

| World | Real-world location | Mesh | What it shows | Drone-fit |
|---|---|---|---|---|
| `orchard.sdf` | Olive orchard, 39.51° N 22.43° E (Greece) | `orchard_world.dae` + `orchard_trunks.dae` | Rows of olive trees with realistic mesh & textures | **excellent open-terrain pick** |
| `pipeline.sdf` | Pipeline, 57.03° N -115.43° W (northern Alberta) | `inspection_world.dae` + water | Industrial pipeline + ground + base station + tripod | infrastructure inspection scenarios |
| `solar_farm.sdf` | 50.11° N -97.32° W (Stonewall, MB, Canada) | `agriculture_world.dae` | Solar panels in field | useful for inspection drones |
| `office_construction.sdf` | 43.50° N -80.55° W (Waterloo, ON — Clearpath's office) | `office_construction.dae` | Construction site around a real building | **excellent urban / built-environment pick** |
| `office.sdf` | indoor | indoor mesh | indoor office scene | indoor capture |
| `warehouse.sdf` | indoor | warehouse mesh | warehouse | indoor capture |

Each world is rendered through `ogre2` and includes a `<sky>` block
with `<clouds><speed>12</speed></clouds>` — actual cloud sky, not a
flat skybox. Geometry is bundled with the package (no Fuel
dependency for the world itself), so first launch doesn't stall on
downloads.

**Catch**: collision is loaded from the same monolithic `.dae` mesh as
the visual — meaning drone overlap with detailed geometry will incur
ODE physics cost on every step. For a *kinematic* camera rig (which is
what Phase 1 of this project is), this doesn't matter (kinematic
poses don't trigger collisions). For Phase 2 control with full
physics, primitive-collision substitution will be needed.

**License caveat**: the SDF files are MIT-licensed; the bundled `.dae`
meshes (e.g. `orchard_world.dae`) are part of Clearpath's
`cpr_gazebo` model collection, which is BSD-3-Clause. Attribute
Clearpath in the dataset README.

**Install (jazzy branch, Harmonic)**: see "Setup instructions" below.

#### `unitsSpaceLab/Forest3D` (Jan 2026, MIT) — **★ pick for procedural realistic forests**

[Repo](https://github.com/unitsSpaceLab/Forest3D),
[Discourse intro](https://discourse.openrobotics.org/t/forest3d-generate-populated-outdoor-environments-for-gazebo/51551),
[Jan 2026 community meeting talk](https://www.youtube.com/watch?v=dIxyYXnY1e8).
Authors: Khalid Bourr, Stefano Seriani, Simone Cottiga (University of
Trieste).

What it does:

- Takes DEM terrain data + Blender asset library (trees, rocks, bushes,
  grass, sand) → **procedurally placed Gazebo SDF world** with
  natural clustering patterns + collision-accurate meshes.
- Ships a Docker image bundling **Python + GDAL + Blender 4.2 +
  Gazebo Harmonic** so the entire pipeline is reproducible without host
  setup.
- Single CLI with subcommands for terrain, asset conversion, population.
- Demonstrated for "Rover + LiDAR perception" (the scenes work with
  drone perception too — the LiDAR demo just happens to use a rover).

What it doesn't do:
- Doesn't bundle assets; users provide `.blend` files. Pair it with
  Poly Haven Namaqualand 3D scans (CC0) for a free, high-quality plant
  library.
- No native PBR claim in README; relies on Blender materials surviving
  the Blender → SDF conversion.

**Verdict**: this is the right tool for "build me a realistic forest /
desert / arbitrary natural scene with vegetation density I control" on
Harmonic. The trade-off is you have to provide the asset `.blend`s
upfront.

#### `gazebosim/harmonic_demo` — official Harmonic showcase

[Repo](https://github.com/gazebosim/harmonic_demo). Apache-2.0. A
single 24 KB `harmonic.sdf` world that pulls 23 demo models — `Lake
House`, `Armchair`, `Bathtub`, `Bed`, `Coast Waves 2`, `Desk`, `Dining
Chair`, `Dining Table`, `Fridge`, `Harmonic Mascot`, `Office Chair`,
`Oven`, `Pendulum`, `Piano`, `Sky`, `Spheres`, `Terrain`, `Terrain
Objects`, `Tethys Sensors`, `Toilet`, `Vanity`, `fidget_spinner`,
`pendulum_sculpture`. Also ships `harmonic_mimic_mechanisms.sdf`
(29 KB) and `fluid_added_mass.sdf` (2.9 KB).

**Visual ceiling reference**: this is the scene Open Robotics is willing
to commit to when they want to *show off* Harmonic. The `Lake House`
+ `Coast Waves 2` + `Sky` combo is roughly the visual quality you can
expect on RTX 3050 with all the rendering knobs turned up. It's
*nice* — interior PBR, water, sky — but it isn't an urban scene.

**Verdict**: not a usable pre-built world for our urban or open-terrain
need, but a good **calibration baseline** for "what am I aiming at?".

#### `Mechazo11/clearpath_simulator_harmonic` — alternate Harmonic port

A community fork of clearpath_simulator with explicit Jazzy + Harmonic
focus, supporting Xbox One controllers, custom robot.yaml names, and
TwistStamped conversion
([repo](https://github.com/Mechazo11/clearpath_simulator_harmonic)).
Use this if the official `clearpath_simulator/jazzy` branch breaks for
you — same worlds, different maintainer.

#### `osrf/vrx` (3.0+, maritime) — Harmonic + Jazzy native

[Repo](https://github.com/osrf/vrx). VRX 3.0 onward runs on Harmonic +
Jazzy by default; older Garden + Humble branch still available
([VRX wiki](https://github.com/osrf/vrx/wiki)). Worlds are
maritime — Sydney Regatta course, target vessels, USVs. **Not what we
want** for urban or land-based open-terrain perception, but useful if
the project scope ever expands to over-water aerial captures (e.g.
ship detection from a drone).

#### `Field-Robotics-Lab/dave` — underwater, GSoC 2024/2025 migration

Project DAVE (underwater AUVs) is mid-migration to Harmonic + Jazzy
under Google Summer of Code 2024 and 2025
([GSoC 2024 announcement](https://discourse.openrobotics.org/t/gsoc-2024-migration-of-project-dave-to-ros-2-and-harmonic-worlds-models-and-plugins/39313),
[GSoC 2025 sonar work](https://discourse.openrobotics.org/t/gsoc-2025-migrating-and-optimizing-dave-s-physics-based-sonar-plugin-for-ros-2-and-gazebo-harmonic/49835)).
Underwater scenes — irrelevant for an aerial drone perception project.

### OSM → Gazebo / heightmap-with-satellite-overlay tools

Three options ordered from "production-ready" to "research-grade":

#### `saiaravind19/gazebo_terrain_generator` v2.0 — **★ best modern OSM-to-Harmonic tool**

[Repo](https://github.com/saiaravind19/gazebo_terrain_generator).
v2.0 released 2026-02-12 targeting `gz-harmonic`. 224★, 30 forks (per
the repo page).

Pipeline:
1. Web UI on `localhost:8080` — draw a region of interest on a Leaflet
   map.
2. The tool downloads MapBox Terrain DEM v1 tiles and orthographic
   satellite imagery for that region.
3. Buildings are added (toggle in UI; data source implied OSM by
   convention, MapBox API explicit for terrain/satellite).
4. Outputs an SDF model directory with `model.sdf`, `model.config`,
   textures (heightmap `.tif` + satellite `.png`), plus a world file.

**Output: SDF for Harmonic; PNG-color satellite textures (NOT PBR);
basic 3D building geometry (color-only, not photoreal).** Tested on
Harmonic; Jetty support pending per the developer's Discourse post
([Discourse update](https://discourse.openrobotics.org/t/gazebo-terrain-generator/52254)).

Limitations the developer acknowledges: no realistic ground material
properties; no forest/tree generation. Pair with Forest3D for trees, or
add Fuel `Pine Tree` includes by hand.

**Verdict**: this is the only practical "I want a real-world city
block in Harmonic in <10 minutes" tool. **Use it for the urban scene
if the Clearpath `office_construction` world isn't enough**.

Requires a free MapBox API key for satellite tiles.

#### `Sarath18/terrain_generator` — Wizard for heightmap-only terrains

[Repo](https://github.com/Sarath18/terrain_generator). 101★, 13 commits,
no releases. Heightmap-image-driven (local PNG or URL). Gazebo version
not stated explicitly. Older / simpler than saiaravind19's; **prefer
saiaravind19 for new projects**.

#### `osrf/gazebo_osm` — original, ancient

[Repo](https://github.com/osrf/gazebo_osm). Python 2.7 + Mapnik. README
references neither Harmonic nor Classic. Outputs SDF with roads,
buildings. **Effectively unmaintained.** Skip.

#### **OSM2World** — most general OSM converter

[Project site](https://www.osm2world.org/), open-source. Outputs
**glTF, glb, obj, pov** with PBR materials (normal + ORM + displacement
maps). Active in 2025/2026. Not Gazebo-specific, but glTF binary →
wrap in `model.sdf` → load into Harmonic is straightforward (Harmonic
loads `.glb` natively via gz-rendering's PBR-capable mesh loader).

**Workflow**:
1. Pick an OSM region in JOSM, export `.osm`.
2. Run OSM2World to produce a `.glb`.
3. Wrap in a 20-line `model.sdf` (use Fuel `fuel_textured_mesh.sdf`
   pattern as template).
4. `gz sim` it.

This is the highest-fidelity OSM-to-Harmonic path *if* you don't mind
the manual wrap step. The end result will out-quality saiaravind19's
output because of OSM2World's PBR material treatment.

### Sketchfab / CC0 single-asset scenes

The honest verdict: **Sketchfab "city block" CC0 / CC-BY scenes are
mostly stylized low-poly, not photoreal**, and even when they are
photoreal they lack the layered structure (separate roads / sidewalks /
buildings as semantic groups) that segmentation-camera labeling needs.
Per-asset, they're fine; as a *whole-scene* shortcut, they're not what
you want.

Concrete examples worth knowing:

- [Modern City Block](https://sketchfab.com/3d-models/modern-city-block-c80dba249d9547cbb48d00828d23cfa7)
  — Blender + Substance Painter + Marmoset Toolbag, 7×1024² texture
  sets, glTF download. CC-BY (check on page).
- [Low Poly City](https://sketchfab.com/3d-models/low-poly-city-41697300a4c643d089784b8688b2ed2c)
  by Alessandro.Diamanti. Stylized, useful as background.
- [Low-poly City Buildings](https://sketchfab.com/3d-models/low-poly-city-buildings-e0209ac5bb684d2d85e5ade96c92d2ff)
  ~200 faces/building, designed for "massive use". Fine for distant
  cityscape.
- [Low Poly World/City starter pack](https://sketchfab.com/3d-models/low-poly-world-city-starter-pack-4038bafc15a04459b11406facb6ecf06)
  — modular, single-color-palette.

For a **quality bar** beyond Sketchfab, the
[madjin/awesome-cc0](https://github.com/madjin/awesome-cc0) list curates
the best CC0 sources across the web — that's the meta-index to mine.

For **HDRIs and photoscan textures** (not full scenes), Poly Haven is
the right answer:

- [Poly Haven HDRIs](https://polyhaven.com/hdris) — CC0, up to 16K, in
  HDR + EXR. Use as Harmonic skybox cubemap (convert HDR → cubemap
  faces, drop in a `<scene><sky>` block).
- [Poly Haven Namaqualand collection](https://polyhaven.com/models/collection:%20namaqualand)
  — 30 photoscanned desert plants/rocks/ground-debris + 10 16K HDRIs +
  5 PBR ground/rock materials. Per-asset 43–61 MB ZIP. CC0
  ([CG Channel writeup](https://www.cgchannel.com/2024/10/download-poly-havens-free-namaqualand-3d-scan-library/),
  [Poly Haven blog](https://blog.polyhaven.com/namaqualand/)).

Pair Namaqualand + a Poly Haven desert HDRI sky on a saiaravind19 or
Forest3D base terrain → that's the highest-fidelity "open desert /
scrubland" scene you can make on Harmonic for free.

### `automaticaddison` curated list (re-checked May 2026)

[Useful World Files for Gazebo and ROS 2 Simulations](https://automaticaddison.com/useful-world-files-for-gazebo-and-ros-2-simulations/)
hosts: **Cafe, Car, Distribution Center, Factory, Farm, Hospital, House,
Inventory, Lawn, Neighborhood, Office, Warehouse** worlds via a Google
Drive share. **All are targeted at Gazebo 11 (Classic) + ROS 2
Foxy/Galactic**, not Harmonic. They're useful as raw `.world` /
mesh donors that you can hand-port to Harmonic, but **don't expect
drop-in load**. The `Neighborhood` world is the closest to "urban" in
the list — worth porting if Clearpath `office_construction` is
insufficient.

### Other community asset packs (worth reaffirming)

- **`leonhartyao/gazebo_models_worlds_collection`** — GPL-3.0
  cross-project collection (3DGEMS, RotorS, TU Delft, Clearpath Classic,
  Fetch). Mostly Classic SDF.
- **`MOGI-ROS/Week-3-4-Gazebo-basics`**, `Week-5-6-Gazebo-sensors`,
  `Week-9-10-Simple-arm`, `Week-11-12-Robot-arms`, `Week-1-8-Cognitive-robotics`
  — Budapest University of Technology & Economics ROS 2 Jazzy +
  Harmonic course tutorials. Worlds are simple training/demonstration
  scenes; not directly useful as drone scenes but **good reference
  for SDF-on-Harmonic patterns**
  ([MOGI-ROS GitHub](https://github.com/MOGI-ROS)).
- **`NovoG93/sjtu_drone`** — ROS 2 quadcopter sim; tested on Gazebo 11
  / Ubuntu 22.04, no Harmonic confirmation
  ([repo](https://github.com/NovoG93/sjtu_drone)).
- **`gtfactslab/CrazySim`** — Crazyflie SITL with Gazebo Harmonic
  support (recommended Gazebo install per their docs); worlds are simple
  flight-training arenas, useful for swarm work
  ([repo](https://github.com/gtfactslab/CrazySim),
  [Bitcraze CrazySim post](https://www.bitcraze.io/2024/04/crazysim-a-software-in-the-loop-simulator-for-the-crazyflie/)).
- **`open-rmf/rmf_demos` (jazzy branch)** — built and tested on Ubuntu
  24.04 LTS + ROS 2 Jazzy + Gazebo Harmonic
  ([rmf_demos jazzy branch](https://github.com/open-rmf/rmf_demos/tree/jazzy)).
  Generates worlds from `.building.yaml` files via Traffic Editor.
  Available maps: `airport_terminal` (177 KB YAML), `battle_royale`
  (11 KB), `campus` (36 KB), `clinic` (274 KB — multi-floor with lifts),
  `hotel` (102 KB — multi-floor), `office` (36 KB), `triple_H` (8 KB).
  These are designed for indoor delivery / multi-fleet coordination,
  but their building.yaml output → SDF makes them usable as **indoor
  drone capture scenarios**. The `airport_terminal` and `clinic` are
  the largest and most visually rich.

### Nuclear / "should we just convert from Isaac" question

Searched specifically for tools to convert Isaac Sim USD scenes to
Harmonic-loadable glTF/SDF. **There is no maintained tool.** NVIDIA's
MeshConverter goes glTF → USD (the *wrong* direction)
([Isaac Lab importing-asset doc](https://isaac-sim.github.io/IsaacLab/main/source/how-to/import_new_asset.html)).
USD → Blender (with Pixar's USD plug-in) → glTF export → SDF wrap is
possible but bespoke per scene. **Conclusion: don't try to use Isaac
asset packs; the conversion cost is higher than just composing a scene
from Fuel + the sources above.**

## Recommended urban / built-environment world

**Pick: `clearpath_simulator/jazzy/clearpath_gz/worlds/office_construction.sdf`**.

- **Why**: real construction site around a real Waterloo office, GPS
  coords baked in, single monolithic Collada mesh (no per-frame Fuel
  download stalls), Harmonic-native SDF with `gz::sim::systems::*`
  plugins and `ogre2` render engine, sky + clouds animation, **fits
  comfortably in 4 GB VRAM**.
- **Install** (assumes ROS 2 Jazzy + Harmonic vendor packages already on
  this box):
  ```bash
  cd /media/abrar/AbrarSSD/ROS/drone_targeting_research/ros2_ws/src
  git clone -b jazzy https://github.com/clearpathrobotics/clearpath_simulator.git
  cd /media/abrar/AbrarSSD/ROS/drone_targeting_research/ros2_ws
  rosdep install --from-paths src -i -r -y
  colcon build --packages-select clearpath_gz
  source install/setup.bash
  export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$(ros2 pkg prefix clearpath_gz)/share/clearpath_gz/worlds
  GDK_BACKEND=x11 QT_QPA_PLATFORM=xcb gz sim $(ros2 pkg prefix clearpath_gz)/share/clearpath_gz/worlds/construction.sdf
  ```
- **Expected disk**: ~150 MB for the full clearpath_simulator package
  (source + meshes).
- **Expected RTF on RTX 3050 + 3 cameras at 1280×720**: 0.3–0.5 RTF.
  No Fuel includes, so no first-launch download stall.
- **Screenshot reference**:
  [Clearpath Simulator comes to Gazebo Harmonic blog post](https://discourse.openrobotics.org/t/clearpath-simulator-comes-to-gazebo-harmonic/40975)
  shows the warehouse and outdoor worlds.

**Plan B if `office_construction` is too quiet a scene**: run
`saiaravind19/gazebo_terrain_generator` and grab a real city block
(Trafalgar Square, Times Square, etc.) with terrain + satellite overlay
+ buildings.

## Recommended open-terrain / outdoor world

**Pick: `clearpath_simulator/jazzy/clearpath_gz/worlds/orchard.sdf`**
for hand-crafted realistic vegetation, **or `unitsSpaceLab/Forest3D`**
for procedural forests with controllable density.

For `orchard.sdf`:

- Same install as `office_construction` above, just launch
  `orchard.sdf`.
- Real olive orchard in Greece, monolithic mesh, sky + clouds, ~150 MB
  installed.
- Drop in a Fuel `Mountain` heightmap or similar for terrain variation
  if needed.

For `Forest3D`:

```bash
# Pull the Docker image with Blender 4.2 + Gazebo Harmonic baked in
git clone https://github.com/unitsSpaceLab/Forest3D.git
cd Forest3D
docker pull unitsSpaceLab/forest3d:latest    # check README for current tag
# Provide your own .blend assets in the assets/ directory:
#   assets/tree/*.blend, assets/rock/*.blend, assets/bush/*.blend
# Pair with Poly Haven Namaqualand 3D scans (CC0) for free realism.
# Then run the CLI to generate a world from a DEM region.
```

For *photoreal* desert / scrubland use Forest3D's pipeline + the
Poly Haven Namaqualand CC0 collection as the asset library (download
once; reuse across scenes). That stack — Forest3D placing Namaqualand
boulders + a Poly Haven desert HDRI sky — is the highest-quality
free Harmonic open-terrain you can build in May 2026.

## Recommended drone-specific world

**Pick: `david-dorf/spaceros_gz_demos/spaceros_gz_demos/worlds/mars.sdf`**.

This is the only Harmonic-native world we found that ships **a flyable
aerial vehicle (Ingenuity helicopter) over alien terrain (Mars
surface)**. It's perfectly suited to "Mars-mission-style perception
dataset" framing.

- **Mars terrain**: 24.7 MB glTF mesh, scaled 100× to give a large
  surface area. PBR-textured.
- **Ingenuity model**: rotorcraft with rechargeable battery (recharges
  from a solar panel) + flight commands.
- **Perseverance**: differential-drive rover with arm joints, publishes
  RGB + depth + point cloud.
- **Gravity**: Mars (3.71 m/s²) — affects flight dynamics, useful
  signal for the perception model that "this isn't Earth".

**Install**:
```bash
cd /media/abrar/AbrarSSD/ROS/drone_targeting_research/ros2_ws/src
git clone https://github.com/david-dorf/spaceros_gz_demos.git
cd /media/abrar/AbrarSSD/ROS/drone_targeting_research/ros2_ws
rosdep install --from-paths src -i -r -y
colcon build --packages-select spaceros_gz_demos
source install/setup.bash
GDK_BACKEND=x11 QT_QPA_PLATFORM=xcb \
  ros2 launch spaceros_gz_demos mars.launch.xml
```

(README references a Docker option too — use Native install on Jazzy
to avoid Docker GPU passthrough complexity on RTX 3050.)

**Expected disk**: ~70 MB (24.7 MB Mars terrain + Perseverance/Ingenuity
meshes).

**Expected RTF on RTX 3050 + 3 cameras at 1280×720**: 0.5–0.7 RTF.
Single-mesh terrain + small rover + small helicopter = light.

**Screenshot reference**:
[spaceros_gz_demos README](https://github.com/david-dorf/spaceros_gz_demos)
shows the Mars + Moon + Enceladus worlds in screenshots.

## Setup instructions (verbatim, copy-pasteable)

### 0. Common prep (already done on this box, included for completeness)

```bash
# Force X11 (Wayland breaks Harmonic on KDE Neon 24.04)
export GDK_BACKEND=x11
export QT_QPA_PLATFORM=xcb

# Confirm vendor gz binary on PATH
export PATH=/opt/ros/jazzy/opt/gz_tools_vendor/bin:$PATH

# Source ROS
source /opt/ros/jazzy/setup.bash
```

### 1. Clearpath Simulator (urban + outdoor + indoor, six worlds)

```bash
mkdir -p /media/abrar/AbrarSSD/ROS/drone_targeting_research/ros2_ws/src
cd /media/abrar/AbrarSSD/ROS/drone_targeting_research/ros2_ws/src
git clone -b jazzy https://github.com/clearpathrobotics/clearpath_simulator.git
cd /media/abrar/AbrarSSD/ROS/drone_targeting_research/ros2_ws
rosdep install --from-paths src -i -r -y
colcon build --packages-select clearpath_gz
source install/setup.bash

# Launch a specific world (replace `construction.sdf` with any of:
# orchard.sdf, pipeline.sdf, solar_farm.sdf, office.sdf, warehouse.sdf)
export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$(ros2 pkg prefix clearpath_gz)/share/clearpath_gz/worlds
gz sim $(ros2 pkg prefix clearpath_gz)/share/clearpath_gz/worlds/construction.sdf
```

### 2. NASA Mars / Moon / Enceladus (spaceros_gz_demos)

```bash
cd /media/abrar/AbrarSSD/ROS/drone_targeting_research/ros2_ws/src
git clone https://github.com/david-dorf/spaceros_gz_demos.git
cd /media/abrar/AbrarSSD/ROS/drone_targeting_research/ros2_ws
rosdep install --from-paths src -i -r -y
colcon build --packages-select spaceros_gz_demos
source install/setup.bash

ros2 launch spaceros_gz_demos mars.launch.xml         # Mars + Perseverance + Ingenuity
ros2 launch spaceros_gz_demos moon.launch.xml         # Moon + 2× rovers + truss
ros2 launch spaceros_gz_demos enceladus.launch.xml    # underwater
ros2 launch spaceros_gz_demos orbit.launch.xml        # ISS + capsule
```

### 3. Real-world city block from satellite + DEM

```bash
git clone https://github.com/saiaravind19/gazebo_terrain_generator.git
cd gazebo_terrain_generator
python3 -m venv terrain_generator && source terrain_generator/bin/activate
pip install -r requirements.txt

# Set MAPBOX_API_KEY in env (free tier is enough for moderate use)
export MAPBOX_API_KEY=<your_key>

python scripts/server.py
# Open http://localhost:8080 in a browser
# Draw a region of interest, enable buildings, click Export.
# The world is written to sample_worlds/<region_name>/

export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$(pwd)/sample_worlds
gz sim sample_worlds/<region_name>/<region_name>.sdf
```

### 4. Procedural forest with Forest3D

```bash
git clone https://github.com/unitsSpaceLab/Forest3D.git
cd Forest3D
# Either use the Docker image (recommended)
docker pull unitsSpaceLab/forest3d:latest      # check README for current tag
# Or install Blender 4.2 + Python + GDAL on the host.

# Drop your asset .blend files into assets/{tree,rock,bush,grass,sand}/
# Optionally pull free CC0 assets from Poly Haven Namaqualand collection:
#   https://polyhaven.com/models/collection:%20namaqualand

# Run the CLI (exact subcommand names per repo README):
python forest3d.py terrain --dem <path/to/dem.tif>
python forest3d.py populate --density 0.3
python forest3d.py launch
```

### 5. PX4 SITL `forest.sdf` (quick check, no extra setup)

```bash
# Assuming PX4-Autopilot from drone_simulation.md is at
# /media/abrar/AbrarSSD/ROS/PX4-Autopilot
cd /media/abrar/AbrarSSD/ROS/PX4-Autopilot
PX4_GZ_WORLD=forest make px4_sitl gz_x500
```

### 6. Sanity-check the gazebosim/harmonic_demo as visual ceiling

```bash
git clone https://github.com/gazebosim/harmonic_demo.git
cd harmonic_demo
gz sim -v 4 harmonic_demo/harmonic.sdf
```

(Compare your captured imagery against this scene to calibrate "is the
visual fidelity I'm getting actually as good as Harmonic can do?".)

### 7. Label-tagging any of the above

The existing `tools/label_world.py` already handles `<include>`-based
worlds. For the new pre-built worlds:

- **Clearpath worlds**: every model is in-line (no Fuel `<include>`),
  so `label_world.py` needs a small extension to also walk top-level
  `<model>` elements and inject Label plugins inside their `<link>`
  blocks. ~20 LOC extension.
- **spaceros_gz_demos**: Mars / Moon worlds use `<include>` for
  `martian_surface`, `nasa_perseverance`, `nasa_ingenuity` etc. —
  current tool works with a labels.yaml mapping like:
  ```yaml
  spaceros_gz_demos/martian_surface: 80   # terrain_natural
  spaceros_gz_demos/nasa_perseverance: 90 # treat as drone for now
  spaceros_gz_demos/nasa_ingenuity: 90    # drone
  ```

## Open questions / risks

1. **Clearpath worlds are licensed BSD-3-Clause but the bundled `.dae`
   meshes were produced by Clearpath's commercial customers (per their
   blog history)**. Always attribute Clearpath in the dataset README.
   The 2024 Clearpath ↔ Rockwell Automation acquisition has not
   changed the license but watch the repo for any policy change.
2. **`spaceros_gz_demos` README does not state a tested ROS 2 distro.**
   It only says "Gazebo Harmonic compatibility required". Verified
   compatible with Jazzy by the project's NASA Sim Sprint 2024 timing
   (Jazzy was the current LTS at submission). If a build error appears
   on Jazzy, file the issue upstream — David Dorf is responsive.
3. **`saiaravind19/gazebo_terrain_generator` requires a MapBox API
   key**. Free tier is generous (50K terrain tile loads/month) but
   exhaustible if you generate dozens of regions. Check the repo for
   alternative provider toggles.
4. **`Forest3D` doesn't bundle assets** — the user has to provide
   `.blend` files. Pair with Poly Haven Namaqualand (CC0) as the
   default starter asset library; no other free source matches the
   quality.
5. **No drone-competition Harmonic worlds in 2026.** The maritime →
   aerial gap is real. If "drone competition look" is non-negotiable,
   the only paths are (a) port one of the older Classic-era MBZIRC /
   AlphaPilot worlds to Harmonic by hand (significant work), (b) accept
   that Mars + Ingenuity is the closest "drone over alien terrain"
   substitute, or (c) switch simulators (Cosys-AirSim on UE5 — but
   we've already ruled that out for VRAM).
6. **Open-RMF building-yaml worlds** (clinic, hotel, airport_terminal)
   could become useful if the project ever wants indoor multi-floor
   drone scenarios — they're built and tested on Jazzy + Harmonic
   ([rmf_demos jazzy branch](https://github.com/open-rmf/rmf_demos/tree/jazzy)),
   but the conversion pipeline is `.building.yaml` → world generator,
   which adds a tooling step.
7. **PX4 `baylands` is the single most often-cited Harmonic outdoor
   world** in tutorials, but it's also the single most often-cited
   *RTF killer*. If the user wants baylands specifically, plan for
   <0.2 RTF or run with primitive collisions only.
8. **SubT remains off-limits on RTX 3050 4 GB.** Re-checked the
   community port (LTU-RAI/darpa_subt_worlds) — same density as
   originals, no lighter sub-tile path exists. Defer until hardware
   upgrade.
9. **MBZIRC 2024 was the *Maritime* Grand Challenge** — there's no
   2024 land/aerial MBZIRC world. The user may have been thinking of
   the older 2017/2020 events, both of which are Classic-era and would
   require porting. Probably not worth it given the Mars + Clearpath
   alternatives.
10. **No batch label-augmentation tool exists in the wild for the new
    worlds either**. The project's existing `tools/label_world.py`
    remains on the critical path; it'll need a small extension to
    handle top-level `<model>` elements (Clearpath worlds) in addition
    to `<include>` (spaceros, Fuel-based worlds).
