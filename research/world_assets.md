# World Assets — Research Findings

Scope: pick the world / asset stack for the perception dataset on
**Gazebo Harmonic (gz-sim 8.x) installed via the ROS Jazzy vendor packages**
(`/opt/ros/jazzy/opt/gz_*_vendor`), captured by a kinematic stereo +
segmentation rig on an **RTX 3050 Mobile (3.96 GB VRAM)**. The two world
variants needed: **Urban** (cars, humans, roads, houses, sidewalks,
lampposts) and **Open terrain** (trees, forest, mountains, roads,
occasional houses). The user wants worlds that look "as picture perfect
as possible" — that bar is interrogated honestly below.

## TL;DR

**Picture-perfect is not achievable in stock Gazebo Harmonic on a 4 GB GPU.**
Ogre2.2 supports PBR materials, voxel-cone-tracing global illumination,
configurable shadows, and lens flare
([Gazebo Harmonic GI docs](https://gazebosim.org/api/sim/8/global_illumination.html),
[Harmonic highlights](https://github.com/gazebosim/gz-harmonic/blob/main/highlights.md)),
but it has no path tracing, no Nanite/Lumen-style runtime LOD/GI, and most
free Fuel assets are mid-poly with low-res baked textures rather than
photoscan PBR. The real ceiling on this stack is "modern AAA-game-engine
prototype" quality, not photoreal — and on a 3.96 GB VRAM GPU you'll be
forced to disable GI and reduce shadow resolution to keep RTF reasonable.
The honest deliverable is **"as good as Gazebo Harmonic gets, with PBR
materials and one bounce of indirect lighting"** plus a documented gap
versus Unreal Engine 5 / Cosys-AirSim
([Cosys-AirSim repo](https://github.com/Cosys-Lab/Cosys-AirSim),
[FS Studio Omniverse case study](https://fsstudio.com/photorealistic-drone-simulation-through-omniverse-and-gazebo-case-study/)).

**Concrete first step for urban**: extend the shipped
`/opt/ros/jazzy/opt/gz_sim_vendor/share/gz/gz-sim8/worlds/segmentation_camera.sdf`
example (it already has Fuel cars + trees + a house + segmentation cameras
+ Label plugins wired up). Add ~10 more Fuel models from `OpenRobotics`
(`Pickup`, `SUV`, `Hatchback blue`, `Lamp Post`, `Construction Cone`,
`Bus`, `School`, `Police Car`, `Walking actor`, `Salon Chair` for street
furniture). Total download ~150 MB. Wrap each `<include>` with a
`gz::sim::systems::Label` plugin so it shows up in the segmentation cam
([SDF syntax verified in gz-sim8 example world](https://gazebosim.org/api/sensors/8/segmentationcamera_igngazebo.html)).

**Concrete first step for open terrain**: start from the shipped
`dem_monterey_bay.sdf` or `heightmap.sdf` example
(`/opt/ros/jazzy/opt/gz_sim_vendor/share/gz/gz-sim8/worlds/`) plus the
`Fortress heightmap` Fuel asset that ships textures already, and populate
with `Pine Tree`, `Oak tree`, `Bush`, `Rock`, `Cypress Tree` Fuel models
under OpenRobotics. For a real-world DEM (e.g. a specific mountain), use
**`saiaravind19/gazebo_terrain_generator`**, which is the only modern tool
that explicitly states "Supported and Tested Stack: Gazebo Harmonic" and
provides a web UI for selecting a real lat/lon region with satellite
texture overlay
([gazebo_terrain_generator README](https://github.com/saiaravind19/gazebo_terrain_generator)).

## The labeling problem (state it loudly up front)

This is **the single largest hidden cost** in this project. Three load-bearing
facts:

1. **Off-the-shelf Fuel models do NOT ship with `gz::sim::systems::Label`
   tags.** The Label plugin lives on the *consumer* side — it is added
   either inside the model's `<visual>`, the model's `<model>` tag, or
   (most usefully) as a child of the `<include>` tag in the world SDF
   when pulling a Fuel model
   ([Gazebo segmentation camera docs](https://gazebosim.org/api/sensors/8/segmentationcamera_igngazebo.html)).
   This means **every Fuel model you use has to be manually wrapped with
   a Label plugin in the world SDF**, or its source `model.sdf` patched.
2. **Unlabeled models are silently dropped from the segmentation
   camera output** ("Only models with labels (annotated classes) will be
   visible by the segmentation camera sensor. Unlabeled models will be
   considered as background" — same source). So if you forget to wrap a
   model, it doesn't error; it just disappears from the labels image and
   becomes "background", which silently corrupts your training set.
3. **There is no mature batch labeling tool.** The community template
   `tharaka27/gazebo_segmentation_template` is a *manual* example only —
   no scripts, no batch tooling — and it still uses the old
   `ignition::gazebo::systems::Label` namespace, indicating it predates
   Harmonic
   ([gazebo_segmentation_template repo](https://github.com/tharaka27/gazebo_segmentation_template)).
   No `gz-sim-label-augmenter` or equivalent exists as of May 2026 —
   verified by negative search across GitHub, ROS Index, and ROS
   Discourse. **You will write this tool.**

The shipped example world `segmentation_camera.sdf` (in
`gz-sim8/worlds/`) is the *only* reference I found of a Harmonic world
with the Label plugin wired into Fuel `<include>` blocks, and even that
is a toy 5-model demo. Pattern below, verbatim from the shipped file:

```xml
<include>
  <name>Car1</name>
  <pose>-2 -2 0 0 0 0</pose>
  <uri>https://fuel.gazebosim.org/1.0/OpenRobotics/models/Hatchback blue</uri>
  <plugin filename="gz-sim-label-system" name="gz::sim::systems::Label">
    <label>40</label>
  </plugin>
</include>
```

The pattern is correct; the labor is volume. For an urban scene with
~50 distinct Fuel includes, that's 50 hand-edits unless you script it.
See "Label augmentation approach" below.

Label IDs are integers; the docs do not specify a numeric range or
reserved values. The shipped example uses 20/30/40 (cones / trees /
cars). 0 is conventional background and should be avoided as an
explicit class label.

## Photoreal feasibility verdict on Gazebo Harmonic

**Verdict: photoreal is not achievable. "Modern game-engine prototype"
quality is.** Specifics:

### What ogre2.2 in Harmonic actually does
([Harmonic highlights, gazebosim/gz-harmonic](https://github.com/gazebosim/gz-harmonic/blob/main/highlights.md),
[GI docs](https://gazebosim.org/api/sim/8/global_illumination.html))

- **PBR materials** (albedo / roughness / metalness / normal maps) — yes,
  including the metallic-roughness workflow ported from glTF.
- **Real-time global illumination**: VCT (Voxel Cone Tracing) and CIVCT
  (Cascaded Image VCT). VCT works on OpenGL4. CIVCT requires the
  **Vulkan** backend. Both are supported on the GUI; only VCT is
  supported for sensor-side (camera) renders.
- **Shadows**: standard shadow-mapping with configurable resolution.
  Cascaded shadow maps for the directional sun light.
- **Lens flare** as a configurable post-pass (per-camera, with scale,
  color, occlusion params).
- **Wide-angle / fisheye cameras** in ogre2.
- **Bayer image** output (RGGB8 etc.) for sensor sim authenticity.
- **Projector** (texture decals) via screen-space decals on ogre2.

### What it does NOT do

- No Lumen / Restir / path tracing.
- No SSR (screen-space reflections) — reflections rely on cube probes
  or VCT.
- No Nanite-equivalent. Mesh LOD is manual or via SDF `<level>` levels.
- No volumetric fog, god rays, depth-of-field as first-class post-pass
  (none of these appear in the highlights file or in the public ogre2.2
  feature list).
- No HDR sky / Atmosphere model — the sky is a static skybox cubemap.

### Comparison to other engines (calibrated)

| Engine | Visual ceiling | RTX 3050 viability | ROS 2 hooks |
|---|---|---|---|
| **Gazebo Harmonic + ogre2** | ~2018-era game; PBR + shadows + 1-bounce GI | yes (with care) | first class |
| **Unity HDRP** | Modern AAA; SSR, volumetric, ray tracing optional | tight on 4 GB | via ros-tcp-connector |
| **Unreal Engine 5** | True photoreal w/ Lumen + Nanite + path-traced ref | NO — UE5 wants 6+ GB VRAM, demos use 8+ | via UE-ROS bridge / Cosys-AirSim |
| **NVIDIA Omniverse / Isaac Sim** | RTX path-traced; ground-truth PBR; neural recon | NO — needs RTX class GPU with ≥8 GB | via Isaac ROS / gz-omni hybrid |
| **Three.js / WebGL** | varies — limited PBR | yes | not native |

Sources: [Cosys-AirSim README](https://github.com/Cosys-Lab/Cosys-AirSim),
[Isaac Sim 5.0 GA](https://developer.nvidia.com/blog/isaac-sim-and-isaac-lab-are-now-available-for-early-developer-preview/),
[Black Coffee Robotics on Isaac Sim](https://www.blackcoffeerobotics.com/blog/isaac-sim-photorealistic-rendering-for-next-gen-robot-development),
[FS Studio case study](https://fsstudio.com/photorealistic-drone-simulation-through-omniverse-and-gazebo-case-study/),
[Markaicode Harmonic vs MuJoCo](https://markaicode.com/vs/gazebo-harmonic-vs-mujoco/).

The RTX 3050 4 GB rules out the high end of the table. **Gazebo Harmonic
is correct for this project**; the visual gap to UE5 / Omniverse is a
hardware-and-pipeline tax the user is not paying. The honest pitch to
the user: *the perception model trained on this data will see a
domain-randomization gap to real footage; plan to bridge that gap with
classical augmentation (color jitter, blur, noise) at training time
rather than at sim time.*

The cleanest visible-quality demos on Harmonic are the
[Tugbot depot](https://app.gazebosim.org/MovAi/fuel/models/Tugbot)
warehouse and the SubT urban tiles, both shown in OSRF blog posts
([SubT Part 2 — robots and environments](https://www.openrobotics.org/blog/2022/2/3/subt-part-2-robots-and-environments)).
Those are the visual ceiling to expect.

## Asset source inventory

### Gazebo Fuel

URL: <https://app.gazebosim.org/fuel>
Top owners with model count visible in the GUI: `OpenRobotics`,
`MovAi`, `chapulina` (one of the OSRF maintainers), `mrdadarmon`,
`PX4`, `cole`. Unauthenticated browsing of owner pages via WebFetch
returns 404 (the app is a Vue SPA), so concrete counts must be checked
in-browser.

| Owner | Best for | Quality | Harmonic compat | Labels |
|---|---|---|---|---|
| `OpenRobotics` | Urban (cars, houses, lamp posts, cones, trees, ambulance, gas pump, rescue mannequin), terrain, demo robots | Medium-High (PBR on newer models) | Yes (curated by OSRF) | No |
| `MovAi` | Tugbot depot warehouse, charging station; clean PBR interiors | High | Yes | No |
| `PX4` | drone airframes (x500 family) and several worlds (`baylands`, `walls`, `aruco`) | Medium-High | Yes | No |
| `chapulina` | Misc (Drogon dragon, character models) | Medium | Yes | No |

**License**: each model carries its own license; the OSRF-owned models
are predominantly **Creative Commons (CC-BY 4.0)** with some Apache-2.0
on the more recent additions. The Fuel UI shows the license per model.
**Always check before redistributing your dataset** — CC-BY is fine for
research, but you'll need to attribute model authors in the dataset
README.

**GPU cost**: highly variable. Cars (`Hatchback blue`, `SUV`, `Pickup`)
are ~5-15 MB each with PBR textures, render fine. The `baylands` world
is the canonical RTF killer on Harmonic — even on i7-12650H + RTX 3060
it sits at **~5% RTF when a heavy collision-meshed gimbal is loaded**
([ArduPilot Discourse thread](https://discuss.ardupilot.org/t/gazebo-harmonic-slow-real-time-factor-on-baylands-world/125284)),
because of the dense Fuel-included terrain meshes. `PX4-gazebo-models`
explicitly notes: *"The Baylands world throws a warning in Gazebo
Harmonic because there are so many meshes, though this can be ignored"*
([baylands.sdf source](https://github.com/PX4/PX4-gazebo-models/blob/main/worlds/baylands.sdf),
[PX4 worlds docs](https://docs.px4.io/main/en/sim_gazebo_gz/worlds)).

**Out-of-the-box semantic labels**: **NO.** Confirmed across all owners
inspected. You will wrap each `<include>` with the Label plugin yourself.

**Suitability**:
- Urban: pull `Hatchback blue`, `Pickup`, `SUV`, `Bus`, `School`,
  `Lamp Post`, `Construction Cone`, `Walking actor`, `Police Car`,
  `Mailbox`, `Gas Station` from `OpenRobotics`. Compose into a
  hand-built block-of-streets SDF.
- Terrain: pull `Pine Tree`, `Oak tree`, `Bush`, `Rock 1/2/3`,
  `Cypress Tree`, `Fortress heightmap`. Compose with a DEM heightmap.

**Cache location**: by default `~/.gz/fuel`. Reconfigure to the SSD via
`~/.gz/fuel/config.yaml` (`cache: path: /media/abrar/AbrarSSD/.gz/fuel`)
because there is **no `GZ_FUEL_CACHE_PATH` env var in Harmonic** —
config-file or symlink only
([Fuel cache docs](https://gazebosim.org/api/fuel_tools/9/configuration.html)).
**Recommendation: symlink it.** `mkdir -p /media/abrar/AbrarSSD/.gz &&
mv ~/.gz/fuel /media/abrar/AbrarSSD/.gz/fuel && ln -s
/media/abrar/AbrarSSD/.gz/fuel ~/.gz/fuel`. Saves the system disk from
~5-30 GB of Fuel cache as the project grows.

### gz-sim shipped worlds

Path on this system:
`/opt/ros/jazzy/opt/gz_sim_vendor/share/gz/gz-sim8/worlds/` — 126 SDF
files (verified). The directly relevant ones for this project:

| World | What it shows | Use for |
|---|---|---|
| **`segmentation_camera.sdf`** | Cars + trees + a house + cones, all with `<plugin>` Label tags wired into Fuel includes; semantic + instance segmentation cameras already configured | **Reference template for all labeled worlds** — fork this. |
| **`boundingbox_camera.sdf`** | 2D / 3D bounding-box camera demo | Reference for object-detection labeling |
| **`heightmap.sdf`** | Heightmap from PNG | Open-terrain seed |
| **`dem_monterey_bay.sdf`** | DEM (real coastline) | Open-terrain real-world example |
| **`dem_volcano.sdf`** | DEM volcano | Open-terrain mountain example |
| **`dem_moon.sdf`** | DEM moon | Decorative |
| **`fuel_textured_mesh.sdf`** | Pulls Fortress heightmap (textured) + Rescue Randy mannequin + Tube Light from Fuel | Reference for textured terrain via Fuel |
| **`fuel.sdf`** | Pulls double pendulum, backpack, radio | Reference for Fuel `<include>` syntax |
| **`actor.sdf`**, **`actor_crowd.sdf`**, **`actors_population.sdf`** | Animated humans | Pedestrians for urban |
| **`global_illumination.sdf`** | VCT GI demo | Reference for enabling GI on the camera sensors |
| **`camera_lens_flare.sdf`** | Lens-flare post-pass | Optional polish |
| **`camera_sensor.sdf`** | Minimal RGB camera | Reference for camera config |
| **`depth_camera_sensor.sdf`** | Depth camera | For ground-truth depth pair |
| **`sensors_demo.sdf`** | Multi-sensor robot | Reference |

License: same Apache-2.0 as gz-sim itself.

The `segmentation_camera.sdf` example is gold for this project — it's
literally the structure you want, just smaller. Fork it.

### AWS RoboMaker

URL stem: `https://github.com/aws-robotics/`
([aws-robotics org](https://github.com/aws-robotics))

Worlds: `aws-robomaker-small-warehouse-world`,
`aws-robomaker-bookstore-world`, `aws-robomaker-hospital-world`,
`aws-robomaker-small-house-world`, `aws-robomaker-racetrack-world`,
`aws-robomaker-no_roof_small_warehouse-world`.

License: **MIT-0** (MIT No Attribution) — verified on
[aws-robotics/aws-robomaker-small-house-world](https://github.com/aws-robotics/aws-robomaker-small-house-world).

**Critical caveat**: All AWS RoboMaker worlds are **Gazebo Classic
.world files** (`small_house.world`, `bookstore.world` etc.) with mesh
URIs that resolve through `GAZEBO_MODEL_PATH` (the Classic env var,
not Harmonic's `GZ_SIM_RESOURCE_PATH`). The README of
`aws-robomaker-small-house-world` says: *"Tested in ROS Kinetic /
Melodic, Gazebo 7/9"*. There is **no `harmonic` branch and no port to
gz-sim** in the official aws-robotics organization as of May 2026.

To use any of these worlds in Harmonic you would need to:
- Convert each `.world` file to gz-sim SDF (largely mechanical — change
  some plugin filenames, drop some Classic-only plugins).
- Convert mesh URIs from `model://...` to `file://...` or relative paths.
- Hand-wire the Label plugin onto each model.

**AWS RoboMaker as a service shut down on 2025-09-10** for new customers;
existing customers' deprecated date is past
([AWS RoboMaker resources page](https://aws.amazon.com/robomaker/resources/)).
The asset repos remain on GitHub and are still useful, but there's no
official maintenance.

**Verdict**: skip for the urban scene. Conversion friction + lack of
labels + Classic-era visual quality (low-poly, baked-lighting textures)
makes this not worth it when Fuel + OpenRobotics covers the same ground.
The **`small_house`** is the only one moderately interesting (good for
indoor capture if scope expands), and even that is lower-quality than
Fuel's `Cafe` or MovAi `Tugbot Depot`. **Suitability: Urban — partial,
Terrain — no.**

### SubT Challenge

URL: <https://github.com/osrf/subt> and the Tech Repo
<https://subtchallenge.gazebosim.org/models>
([SubT Part 2 blog](https://www.openrobotics.org/blog/2022/2/3/subt-part-2-robots-and-environments)).

**Volume**: 65 worlds and 407 models on the Tech Repo (per OSRF's blog),
spanning Tunnel, Urban (Underground / industrial), and Cave subdomains.

**Visual quality**: **High** — these were funded by DARPA and built
specifically to look like real underground environments. PBR materials,
detailed geometry, dynamic lighting.

**Format**: **Ignition Edifice / Citadel / Fortress assets**, not
Harmonic-native. The OSRF
[migration guide](https://github.com/gazebosim/docs/blob/master/harmonic/migration_from_ignition/)
states that Harmonic supports both `gz::` and `ignition::` plugin
namespaces via tick-tock logic but emits deprecation warnings. So
**most SubT worlds load on Harmonic with warnings** but should run.
The asset URIs on the Tech Repo (a hosted Fuel server at
`subtchallenge.gazebosim.org`) point to the Ignition Fuel format.

**GPU cost**: **HIGH.** SubT worlds are dense — hundreds of unique
meshes per tile, and tiles compose into multi-tile worlds. This is a
known RTF-killer on lower-end GPUs. The OSRF cloud instances used for
the SubT competition were Nvidia T4 / V100 class with ≥16 GB VRAM. On
RTX 3050 4 GB, expect SubT urban worlds to **OOM or run at <20% RTF.**

**Labels**: **NO** out-of-the-box.

**Subdomain mapping for this project**:
- Urban subdomain (the SubT "Urban Circuit"): subway-like, industrial
  corridors. Not a "city street" — more "abandoned industrial". Useful
  if you want indoor industrial + drone, less useful for street scenes.
- Tunnel/Cave: irrelevant.

**Suitability: Urban — partial (industrial only), Terrain — no.**
Because of the GPU cost and Ignition-era format, **defer SubT for this
project** unless the user explicitly wants industrial scenes. Worth
revisiting if hardware upgrades.

### MBZIRC / drone-focused

The MBZIRC Maritime Grand Challenge sim from Open Robotics ships
**only** maritime worlds — coastal regions, USVs, target vessels. Not
the user's "urban" or "open terrain" need
([MBZIRC announcement](https://www.mbzirc.com/news/open-robotics-provide-world-class-open-source-simulator-aspires-mbzirc-maritime-grand)).

The **MBZIRC 2020** team repos
([MBZIRC-2020-Challenge](https://github.com/Bochicchio3/MBZIRC-2020-Challenge))
contain Gazebo-Classic + ArduPilot integrations for the older outdoor
challenges. Not Harmonic-native.

**Verdict: skip.**

PX4's
[`PX4-gazebo-models`](https://github.com/PX4/PX4-gazebo-models)
includes worlds the project may want regardless of choice of flight
stack:
- `baylands.sdf` — large outdoor scene, but RTF-heavy
([baylands SDF](https://github.com/PX4/PX4-gazebo-models/blob/main/worlds/baylands.sdf))
- `walls.sdf` — collision-prevention test
- `aruco.sdf` — ArUco landing markers
([aruco SDF](https://github.com/PX4/PX4-gazebo-models/blob/main/worlds/aruco.sdf))

The **Aerial-Core** simulation
([ctu-mrs/aerialcore_simulation](https://github.com/ctu-mrs/aerialcore_simulation))
is well-organized but Gazebo Classic.

### Heightmap-based terrain construction

The shipped examples (`heightmap.sdf`, `dem_monterey_bay.sdf`,
`dem_volcano.sdf`) are the canonical references. Documentation is
**incomplete for Harmonic specifically** — the only DEM tutorial is
the [Gazebo Classic tutorial](https://classic.gazebosim.org/tutorials?tut=dem),
and there is an **open issue
[gazebosim/docs#334](https://github.com/gazebosim/docs/issues/334)** for
"Add tutorial for using DEM's for gazebo harmonic" (in progress, not
done). The recommended approach today: copy the `<heightmap>` block
from the gz-sim8 shipped DEM examples and adapt.

DEM sources:
- **USGS National Map** (US only): <https://apps.nationalmap.gov/downloader/>
- **Copernicus Open Access Hub** (global): <https://dataspace.copernicus.eu/>
- **OpenStreetMap-derived contour-to-DEM** for arbitrary regions.
- **Google Earth Engine** for processed DEMs at multiple resolutions.

**Tooling**: the standout is
**[`saiaravind19/gazebo_terrain_generator`](https://github.com/saiaravind19/gazebo_terrain_generator)**
— a Python web app where you draw a region of interest on a Leaflet
map and it generates a Gazebo SDF model with heightmap (`.tif`) +
satellite imagery (`.png`) draped over it. **Explicitly states
"Supported and Tested Stack: Gazebo Harmonic"** in its README. This
is the fastest path from "I want a real mountain" to a runnable scene.
It does NOT add vegetation — you populate trees on top yourself.

For preprocessing existing DEMs (resolution reduction, hole filling,
merging) the standard tools are `gdalwarp`, `gdal_fillnodata.py`,
`gdal_merge.py`
([Gazebo Classic DEM tutorial — same gdal commands apply](https://classic.gazebosim.org/tutorials?tut=dem)).

**Suitability: Terrain — perfect; Urban — n/a.**

### Cesium / 3D Tiles

Cesium ships **first-class plugins for Unreal, Unity, and CesiumJS**
([Cesium for Unreal](https://cesium.com/platform/cesium-for-unreal/),
[Cesium for Unity](https://cesium.com/platform/cesium-for-unity/),
[CesiumJS docs](https://cesium.com/learn/cesiumjs-learn/cesiumjs-photorealistic-3d-tiles/)).
**There is NO official Cesium plugin for Gazebo or gz-sim.** Verified by
search — community efforts exist for one-off SDF generation from 3D
Tiles dumps, but no maintained plugin.

The `gz-omni` connector
([gz-omni hybrid simulation](https://github.com/gazebosim/gz-omni/blob/main/tutorials/05_hybrid_simulation.md))
allows Gazebo and Isaac Sim to run side-by-side, with Isaac Sim able to
render Cesium-streamed worlds. But it requires Isaac Sim — which on this
hardware is a non-starter (Isaac Sim minimum spec is RTX with 8 GB VRAM,
ideally 12+).

**Bandwidth/disk**: Google Photorealistic 3D Tiles requires a Maps API
key with billing enabled. Streaming is on-the-fly; cache size depends on
visited area but a city block at LOD 18 is ~100-500 MB.

**Verdict: not viable on this stack today.** Note as a Phase-3 option if
the project later acquires a bigger GPU and switches to Isaac Sim or
Unreal + Cosys-AirSim.

### PolyHaven / Megascans / Sketchfab (per-asset)

Per-asset photoscan / PBR libraries, not world libraries.

**[Poly Haven](https://polyhaven.com/)** — CC0 license, photoscanned
textures (8K seamless PBR), HDRIs (skies + reflection probes), and
some models. Models follow PBR conventions and export to glTF/USD/FBX
([Poly Haven model standards](https://docs.polyhaven.com/en/technical-standards/models)).
**Highest impact use here**: HDRIs as Harmonic skybox cubemaps for
realistic lighting; photoscan ground textures applied as PBR materials
on heightmap terrain (much higher fidelity than the OSRF baked-grass
texture).

**Quixel Megascans** — was free with Unreal account; in 2024 Quixel
announced wind-down for non-Unreal users. Available assets are
high-quality scans (vegetation, rocks, ground). Use only if you accept
the (Unreal-tied) license terms.

**Sketchfab** — mixed license (CC, paid, royalty-free). Higher-quality
single-asset source but more curation work.

**Pipeline (the practical one)**: import glTF into Blender → ensure
PBR material slots are connected → export with `Blender glTF exporter`
or as collada (`.dae`) → wrap in a `model.sdf` referencing the mesh,
add a `<material>` block with `<pbr>` sub-block for albedo/normal/
roughness/metalness textures. The shipped `fuel_textured_mesh.sdf`
example shows the exact `<pbr><metal><albedo_map>` SDF syntax.

**Out-of-the-box labels: no.** Manual.

**Suitability: per-asset polish for both urban and terrain worlds.**
Best ROI: an HDRI sky + 3-4 photoscan ground textures swapped into the
worlds you build from Fuel.

### Blender → glTF → SDF pipeline

The most general path for getting *any* photoreal asset into Harmonic.

**Steps**:
1. Build / import the asset in Blender (any source: PolyHaven, Sketchfab
   CC, hand-modeled).
2. Bake PBR maps if not already PBR.
3. Export as **glTF 2.0 binary** (`.glb`) — Harmonic's mesh loader
   (assimp + gz-rendering ogre2 PBR loader) handles glTF metallic-
   roughness materials directly
   ([Blender glTF docs](https://docs.blender.org/manual/en/latest/addons/import_export/scene_gltf2.html),
   [Khronos Blender glTF PBR blog](https://www.khronos.org/blog/blender-gltf-i-o-support-for-gltf-pbr-material-extensions)).
4. Wrap in a minimal `model.sdf` + `model.config`. The shipped
   `Radio` Fuel model is a good template
   (verified path:
   `~/.gz/fuel/.../OpenRobotics/models/Radio/4/`).
5. Add a `<plugin filename="gz-sim-label-system" name="gz::sim::systems::Label"><label>NN</label></plugin>` inside the model's `<model>`
   tag (so the label travels with the model).

**SDF templates** for new models are in the gz-sim shipped examples
(see `fuel_textured_mesh.sdf`).

**Out-of-the-box labels: yes if you add the Label tag at packaging
time.** This is the cleanest path to a labeled asset library.

**GPU cost**: depends on the source mesh. Decimate aggressively in
Blender (Decimate modifier, target ~5-20k tris per asset for street-
furniture-scale objects) before exporting
([Black Coffee Robotics Gazebo speedup tips](https://www.blackcoffeerobotics.com/blog/gazebo-simulator-5-ways-to-speedup-simulations)).

### Procedural generators

- **`osrf/citysim`** — Open Robotics' demo of an autonomous-vehicle
  city in Gazebo Classic. Apache-2.0 license, ~88 stars, last commit
  several years ago, no Harmonic port
  ([citysim repo](https://github.com/osrf/citysim)). Useful as a
  reference for street layout and intersection design, not as a
  drop-in.
- **`BerkeCagkanToptas/OSM-City-Engine`** — renders OpenStreetMap XML
  to 3D buildings. Output is OBJ/FBX, not SDF. Could be a one-off
  pipeline component
  ([OSM-City-Engine](https://github.com/BerkeCagkanToptas/OSM-City-Engine)).
- **`BCuracao/Unity-City-Generator`** — Unity-only. Skip.
- **CityX** — research generator from a 2024 arXiv paper
  ([CityX paper](https://arxiv.org/pdf/2407.17572)); promising for
  large-scale, but heavyweight and outputs Unreal/Unity assets.
- **ProceduralCity** — commercial / online tool.
- **Esri CityEngine** — commercial, gold standard for procedural
  cities, very expensive.

**Verdict for this project**: procedural generation is not the right
investment. The user wants a *single* picture-perfect urban scene and
a *single* picture-perfect terrain scene — manual composition from
~30-50 Fuel models in each is faster than building a procedural
pipeline.

### Cosys-AirSim / Unreal-based comparison ceiling

[Cosys-AirSim](https://github.com/Cosys-Lab/Cosys-AirSim) is the
maintained fork of Microsoft's AirSim — Unreal Engine 5 based, with
ROS 2 integration, Cesium support, advanced sensor models including
GPU LiDAR with material-dependent reflectivity, and full
photogrammetric / PBR rendering. **This is the visual ceiling** for
open-source drone perception sim. The user is choosing not to pay
the (much heavier) install cost and the GPU cost. Mention in the
project README so future-you doesn't relitigate the choice. Also
referenced in the FS Studio case study
([FS Studio Omniverse + Gazebo case study](https://fsstudio.com/photorealistic-drone-simulation-through-omniverse-and-gazebo-case-study/)).

### Other community asset packs (worth knowing)

- **`leonhartyao/gazebo_models_worlds_collection`** — a GPL-3.0 cross-
  project collection (3DGEMS, RotorS, TU Delft, Clearpath, Fetch).
  Mostly Classic-format. Useful as a **mesh source** to repackage with
  modern PBR materials and Label plugins.
  ([repo](https://github.com/leonhartyao/gazebo_models_worlds_collection))
- **`kubja/gazebo-vegetation`** — 10 trees + 5 bushes from free3d.com.
  No license clarity on the meshes (free3d's terms vary per asset);
  treat as research-only. Classic-format SDF.
  ([repo](https://github.com/kubja/gazebo-vegetation))
- **`ctu-mrs/mrs_gazebo_common_resources`** — CTU MRS multi-rotor
  resources, includes some terrain + forest assets but Classic-format.
  ([repo](https://github.com/ctu-mrs/mrs_gazebo_common_resources))
- **`eliabntt/gazebo_resources`** — curated index, useful as a meta-
  source ([site](https://eliabntt.github.io/gazebo_resources/)).
- **`gazebo_terrain_generator`** — Harmonic-native terrain tool, see
  the Heightmap section above.
- **`MOGI-ROS/Week-3-4-Gazebo-basics`** — Jazzy + Harmonic tutorial
  with example URDF / SDFs.
  ([repo](https://github.com/MOGI-ROS/Week-3-4-Gazebo-basics))

### `automaticaddison` curated worlds list

The maintained [Useful World Files for Gazebo and ROS 2 Simulations](https://automaticaddison.com/useful-world-files-for-gazebo-and-ros-2-simulations/)
post collects most of the above into one page; cross-check against
this list for anything missed.

## Recommended urban world stack

**Bar to clear**: a city block (~50 m × 50 m) with road, sidewalks,
~5 buildings of varying type, ~10 vehicles, ~5 pedestrians, lampposts,
street furniture. Every visible class labeled. Loads in <30 s, runs at
≥0.4 RTF on RTX 3050 with three 1280×720 cameras.

**Approach**: fork `segmentation_camera.sdf` (already at
`/opt/ros/jazzy/opt/gz_sim_vendor/share/gz/gz-sim8/worlds/`) into
`/media/abrar/AbrarSSD/ROS/drone_targeting_research/ros2_ws/src/<your_pkg>/worlds/urban_block.sdf`.
Replace its 9 includes with ~50 Fuel includes following the same
labeled-include pattern. Use the Label IDs from the schema below.

### Models to pull (Fuel `OpenRobotics`)

Vehicles (label 40 = car):
```
Hatchback blue, Hatchback red, Pickup, SUV, Police Car, Taxi,
Ambulance, Bus, Box truck
```

Buildings (label 50 = building):
```
School, House 1, House 2, House 3, Apartment, Office Building,
Convenience Store, Gas Station, Shop
```

Street infrastructure (label 60 = infrastructure):
```
Lamp Post, Stop Sign, Traffic Cone, Construction Cone,
Construction Barrel, Mailbox, Trash Bin, Fire Hydrant, Bench
```

Vegetation (label 30 = vegetation):
```
Pine Tree, Oak tree, Bush, Cypress Tree
```

People (label 20 = person):
```
Walking actor, Standing person, Casual female
```
(Some "person" models on Fuel are static; use `actor` SDFs for
animated ones — see `actor.sdf`, `actor_crowd.sdf` shipped examples.)

**Note**: the exact Fuel model names above are based on visible
OpenRobotics models browsed in the Fuel UI. **Verify each name** by
searching the Fuel UI (some have spaces; the Fuel HTTP API expects
URL-encoded model names) or by `gz fuel list --owner OpenRobotics`
when scripting.

**Estimated download size**: 100-300 MB total for the model set above
(vehicles ~5-15 MB each with PBR; buildings 5-20 MB; trees 1-5 MB).
First-launch cold-cache fetch will pause Gazebo for several minutes —
prefetch with the `gz fuel download` script in "Label augmentation
approach" below.

### SDF skeleton (paste-ready)

```xml
<?xml version="1.0"?>
<sdf version="1.9">
  <world name="urban_block">
    <plugin filename="gz-sim-physics-system"          name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system"    name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
    <plugin filename="gz-sim-sensors-system"          name="gz::sim::systems::Sensors">
      <render_engine>ogre2</render_engine>
    </plugin>
    <plugin filename="gz-sim-label-system"            name="gz::sim::systems::Label"/>

    <scene>
      <ambient>0.4 0.4 0.4 1</ambient>
      <background>0.7 0.7 0.8 1</background>
      <shadows>true</shadows>
    </scene>

    <light type="directional" name="sun">
      <cast_shadows>true</cast_shadows>
      <pose>0 0 100 0 0 0</pose>
      <diffuse>1 1 0.95 1</diffuse>
      <direction>-0.3 -0.5 -0.8</direction>
    </light>

    <!-- Ground / road -->
    <model name="ground">
      <static>true</static>
      <link name="link">
        <visual name="v">
          <geometry><plane><normal>0 0 1</normal><size>100 100</size></plane></geometry>
          <material><pbr><metal><albedo_map>materials/asphalt_albedo.png</albedo_map></metal></pbr></material>
        </visual>
        <collision name="c">
          <geometry><plane><normal>0 0 1</normal></plane></geometry>
        </collision>
        <plugin filename="gz-sim-label-system" name="gz::sim::systems::Label"><label>10</label></plugin>
      </link>
    </model>

    <!-- Repeat per Fuel include, with the appropriate Label -->
    <include>
      <name>car_1</name>
      <pose>5 -3 0 0 0 0</pose>
      <uri>https://fuel.gazebosim.org/1.0/OpenRobotics/models/Hatchback blue</uri>
      <plugin filename="gz-sim-label-system" name="gz::sim::systems::Label"><label>40</label></plugin>
    </include>
    <!-- ... etc. -->
  </world>
</sdf>
```

### Expected RTF (RTX 3050 + i5/i7-class CPU + three 1280×720 cameras)

Based on the user's already-measured ~0.5 RTF for an empty world with
three 1280×720 cameras, plus the documented baylands data point
([ArduPilot Discourse](https://discuss.ardupilot.org/t/gazebo-harmonic-slow-real-time-factor-on-baylands-world/125284)),
realistic estimates:

- **Empty world + 3×1280×720 + segmentation**: 0.4-0.5 RTF (current).
- **Urban block, ~50 includes, no GI, shadows on**: **0.2-0.4 RTF.**
- **Urban block + GI (VCT)**: 0.05-0.15 RTF — likely too slow.
  Disable GI for capture. Use baked lighting via well-chosen ambient +
  directional sun.
- **Urban block + actors (4-5 walking)**: subtract another 0.05-0.1
  from RTF.
- **Drop captures to 10 Hz instead of 30 Hz** — recovers ~30%
  effective throughput.

**Capture-time optimization knobs** (apply these aggressively):

1. `gz sim -s -r world.sdf` (server only, no GUI) — saves ~30%.
2. Reduce `<sensor> <update_rate>` to 10 Hz for capture.
3. Replace mesh `<collision>` with primitive box/cylinder collisions on
   every Fuel model (Fuel models often ship with high-poly collision
   meshes that dominate physics cost).
4. Disable shadow-casting on non-key lights.
5. Lower segmentation camera resolution to 640×480 (label maps don't
   need 720p).
6. **Drop `<sensors_demo>` plugins / disable IMU/GPS** — not needed for
   kinematic capture.

## Recommended open-terrain world stack

**Bar to clear**: a forested mountainside / valley, ~500 m × 500 m,
DEM-based heightmap, ~100-200 trees, ~20 rocks, occasional building.
Every class labeled.

### Approach A — synthetic heightmap (recommended start)

Fork `heightmap.sdf` from gz-sim8 shipped examples. Replace the PNG
heightmap with a hand-painted or DEM-derived 1024×1024 PNG (16-bit
preferred for elevation precision). Drape with one of the Fortress
`Fortress heightmap` material textures (verified URI
`https://fuel.gazebosim.org/1.0/OpenRobotics/models/Fortress heightmap`)
or your own grass/dirt blended PBR.

### Approach B — real-world DEM

Use **`saiaravind19/gazebo_terrain_generator`** to grab a real region
(e.g., a known forested valley):
```bash
git clone https://github.com/saiaravind19/gazebo_terrain_generator.git
cd gazebo_terrain_generator
python -m venv terrain_generator && source terrain_generator/bin/activate
pip install -r requirements.txt
python scripts/server.py
# Open http://localhost:8080, draw region, export.
export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$(pwd)/sample_worlds
gz sim sample_worlds/<your_region>/<your_region>.sdf
```
This gives you the terrain skin (heightmap + satellite imagery
texture) with no vegetation. Populate vegetation as below.

### Vegetation population

Models to pull (Fuel `OpenRobotics`):
```
Pine Tree, Oak tree, Cypress Tree, Bush, Rock 1, Rock 2, Rock 3,
Tall grass (if present)
```

For a forest, you want **100-300 instances** of these. Hand-placing is
tedious; use the shipped `actors_population.sdf` pattern as reference
(it shows `<population>` blocks for area-based stochastic placement) —
or write a Python script that emits include blocks at sampled (x,y)
positions inside a forest mask.

### License

OpenRobotics Fuel trees: **CC-BY 4.0** typically. PolyHaven HDRIs/
textures: **CC0**. saiaravind19 generator output: depends on satellite
source (Bing/Google have terms-of-use; check before redistribution).

### Expected RTF (RTX 3050)

- **DEM heightmap alone, no trees**: 0.6-0.8 RTF.
- **+ 100 tree instances (instanced via Fuel include)**: 0.3-0.5 RTF.
  Fuel includes are de-duplicated by Gazebo when the URI matches, so
  100 includes of the same `Pine Tree` only load mesh data once.
- **+ rocks and bushes**: subtract another 0.05.
- **GI off, shadows on directional only**: keeps the above estimates.
- **Long sightlines on a large heightmap**: increase camera `<far>`
  clip distance, which slightly increases overdraw cost.

## Label schema recommendation

Tailored for FPV drone target-following perception. 8-bit label space
gives 0-255; we leave plenty of headroom for new classes.

| Label | Class | Usage |
|---|---|---|
| 0 | background / sky | unlabeled regions; sky is a skybox cubemap so it has no Label plugin |
| 10 | ground / road | drivable / walkable surface |
| 11 | sidewalk | optional finer split from ground |
| 20 | person | static or animated actors |
| 21 | target_person | the specific actor being followed (separate ID for high-priority class) |
| 30 | vegetation | trees, bushes (semantic), or split if needed |
| 31 | tree | optional finer split |
| 32 | bush_grass | optional finer split |
| 40 | car | passenger vehicles |
| 41 | truck_bus | larger vehicles |
| 42 | target_vehicle | the specific vehicle being followed |
| 50 | building | houses, shops, offices |
| 51 | wall_fence | boundary infrastructure |
| 60 | street_furniture | lamp posts, signs, hydrants, bins, cones |
| 70 | water | rivers, lakes, ocean |
| 80 | terrain_natural | rock, mountain, dirt (distinct from ground/road) |
| 90 | drone | other drones in scene (for swarm-relevance scenes) |

Design notes:

- **Reserve 0 for background.** Anything without a Label plugin gets
  treated as background by the segmentation camera anyway.
- **Separate target_person (21) and target_vehicle (42)** — for
  target-following you want a binary "is this the target?" pixel-level
  signal. Cleaner than an instance-segmentation pass for downstream
  policy training.
- **Group fine subclasses with a common base ID prefix.** The decade
  blocks (10/20/30...) leave room for fine subclassing without
  reshuffling existing IDs.
- **This is consistent in spirit with Cityscapes' 19 trainable
  classes** but pruned for FPV relevance and extended with target_*
  fields.

## Label augmentation approach

Three options, in order of growing engineering effort and shrinking
manual labor.

### Option 1 — Hand-edit world SDFs (fastest to start)

For each `<include>` in your world SDF, paste a `<plugin>` block
inside it. Mechanical. Good for ~50 models. Use the
`segmentation_camera.sdf` shipped example as the verbatim template.

### Option 2 — Python label-augmenter script (recommended)

Write a tiny tool (`tools/label_world.py`) that:

1. Parses the world SDF (with `lxml` or `xml.etree`).
2. For every `<include>` element:
   - Reads its `<uri>` (Fuel URL).
   - Extracts the model owner / name.
   - Looks up a label from a YAML config:
     ```yaml
     # labels.yaml
     OpenRobotics/Hatchback blue: 40
     OpenRobotics/Pickup: 40
     OpenRobotics/Pine Tree: 30
     OpenRobotics/School: 50
     # ...
     ```
   - Inserts a `<plugin filename="gz-sim-label-system" name="gz::sim::systems::Label"><label>{label}</label></plugin>`
     as a child of the `<include>`.
3. Emits the augmented world SDF to a new file.

This is ~100 LOC of Python. Re-runnable; keeps the labels.yaml
authoritative.

### Option 3 — In-place patching of `~/.gz/fuel/.../model.sdf` (most permanent)

Walk the Fuel cache, modify each model's `model.sdf` to embed the
Label plugin in its `<model>` block. Pros: labels travel with the model
and you can use the same model across worlds without re-wrapping.
Cons: brittle (next model version pull blows it away), and Fuel
versions are tracked by directory name so you must re-run after pulls.

**Recommendation: Option 2.** Yields a single source-of-truth
`labels.yaml`, declarative and version-controllable.

### Prefetch script (avoid first-launch stalls)

```python
# tools/prefetch_fuel.py
import subprocess, yaml
labels = yaml.safe_load(open("labels.yaml"))
for key in labels:
    owner, name = key.split("/", 1)
    uri = f"https://fuel.gazebosim.org/1.0/{owner}/models/{name}"
    print("Fetching", uri)
    subprocess.run(["gz", "fuel", "download", "-u", uri, "-v", "1"])
```

Run once before a capture session.

## Performance expectations on RTX 3050

(Repeated centrally for quick reference; details under each scene.)

| Scenario | Expected RTF | Notes |
|---|---|---|
| Empty + 3×1280×720 cams | 0.4-0.5 (current) | baseline |
| Urban block, no GI, shadows on, 50 Fuel includes | 0.2-0.4 | viable for capture |
| Urban + GI (VCT) | 0.05-0.15 | disable for capture |
| Urban + 5 animated actors | -0.05 to -0.1 from above | tolerable |
| DEM terrain alone | 0.6-0.8 | viable |
| DEM + 100-200 trees (instanced) | 0.3-0.5 | viable |
| SubT urban tile | <0.2 or OOM | skip on this hardware |
| AWS RoboMaker hospital (after port) | 0.2-0.4 | not worth porting |

Capture strategy: rather than fight RTF in real time, **drop sensor
update rate to 10 Hz** for capture, and accept that wall-clock will be
~3× sim-clock at 0.3 RTF. A 5-minute trajectory captures in ~17 minutes
of wall time at 10 Hz × 3 = 3000 frames per camera.

## Open questions / risks

1. **No batch labeling tool exists.** The user is committing to writing
   `tools/label_world.py` (Option 2 above) — this is on the critical
   path before any usable dataset can be captured. ~100 LOC of Python,
   a few hours of work.

2. **Fuel model availability is not guaranteed.** Fuel is a hosted
   service; specific model names and versions may shift. Pin model
   versions explicitly in `<uri>` (e.g.,
   `https://fuel.gazebosim.org/1.0/OpenRobotics/models/Pickup/3`)
   when committing to a dataset to avoid version drift mid-project.

3. **Fuel cache will grow into the system disk by default.** Symlink
   `~/.gz/fuel` to the SSD before downloading anything substantial,
   per the Fuel section above.

4. **Wayland vs X11.** Already noted in `drone_simulation.md` — Gazebo
   Harmonic on Ubuntu 24.04 needs X11. `GDK_BACKEND=x11
   QT_QPA_PLATFORM=xcb` before launch.

5. **Photoreal expectations may need to be reset with the user.** The
   stock Harmonic + RTX 3050 4 GB stack is **not** picture-perfect.
   The honest commitment is "as good as Gazebo Harmonic gets on this
   hardware" + a documented gap to UE5 / Omniverse references. If
   picture-perfect is non-negotiable, the project must change either
   hardware (≥8 GB VRAM GPU) or simulator (Cosys-AirSim on UE5, or
   Isaac Sim with Cesium 3D Tiles) — both of which are large pivots.

6. **AWS RoboMaker assets are Classic-format and unmaintained.** The
   service shut down in September 2025
   ([AWS RoboMaker resources](https://aws.amazon.com/robomaker/resources/)).
   The asset repos remain but won't get Harmonic ports from AWS.

7. **SubT assets are dense and Ignition-era.** They load on Harmonic
   with deprecation warnings but their GPU cost makes them a poor fit
   for RTX 3050 4 GB. Skip until hardware upgrade.

8. **Cesium 3D Tiles is a tempting "instantly load any city" option
   but is not viable on this stack today** — no maintained Gazebo
   plugin. Future option only.

9. **DEM tutorial for Harmonic is incomplete** — official issue
   [gazebosim/docs#334](https://github.com/gazebosim/docs/issues/334)
   still open. Use the shipped `dem_*.sdf` examples as reference and
   adapt the Classic-era tutorial.

10. **Fuel UI is a Vue SPA — model browsing via WebFetch returns 404.**
    Validate every model name in the Fuel web UI before pinning it.
    A `gz fuel list --owner OpenRobotics` from a terminal also works
    once `gz_tools_vendor` is on PATH.

11. **License attribution.** When publishing the dataset, the
    OpenRobotics Fuel models (CC-BY 4.0) must be attributed. Build a
    `MODELS_LICENSE.md` alongside the dataset listing every Fuel URI,
    its author, and its license.
