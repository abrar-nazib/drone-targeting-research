# Photoreal Options for Stereo + Segmentation + Drone Perception

Scope: the user has rejected the visual fidelity of Gazebo Harmonic's
hand-built worlds for training a stereo depth + semantic segmentation
model on a drone. Hardware ceiling is **RTX 3050 Mobile, 3.96 GB VRAM**,
on Ubuntu 24.04 (KDE Neon) with ROS 2 Jazzy + Gazebo Harmonic already
wired for capture. The target perception model is **stereo depth +
semantic segmentation** for drone target-following in urban /
open-terrain scenes.

## TL;DR

**Stop trying to make a photoreal interactive sim run on a 4 GB card —
it cannot.** CARLA 0.10 (UE5.5) recommends **16 GB VRAM** as the
minimum and explicitly cannot load Town10 below ~12 GB
([CARLA UE5 quickstart](https://carla-ue5.readthedocs.io/en/latest/start_quickstart/),
[CARLA UE5 OOM issue #8964](https://github.com/carla-simulator/carla/issues/8964));
Cosys-AirSim's "Open World" environment wants 8 GB, and the Modular
Neighborhood Pack wants 4 GB minimum just to load
([microsoft/AirSim FAQ](https://microsoft.github.io/AirSim/faq/));
Isaac Sim 4.5/5.x lists **RTX 3070 as the minimum** GPU
([Isaac Sim requirements](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/requirements.html)).
The realistic plan for THIS user is:

1. **Train on free UE-rendered synthetic datasets that already exist on
   disk** — primarily **TartanAir V2** (drone trajectories, stereo +
   depth + segmentation, UE-based) and **Virtual KITTI 2** (urban
   stereo) for the "photoreal training distribution".
2. **Fine-tune / validate on real driving stereo** — **DrivingStereo**
   (the user's own reference) and **KITTI** for sim-to-real
   adaptation.
3. **Keep Gazebo Harmonic as the *deployment-side* sim** — it's where
   the drone control loop will live (already wired), but it is
   *not* the training data source.
4. **Use a pretrained stereo foundation model** (FoundationStereo,
   CVPR 2025 Best Paper Nomination, NVlabs) for strong zero-shot depth
   to bootstrap the project before any custom training, even on
   the 3050 (inference-only).
   ([FoundationStereo repo](https://github.com/NVlabs/FoundationStereo),
   [paper](https://openaccess.thecvf.com/content/CVPR2025/papers/Wen_FoundationStereo_Zero-Shot_Stereo_Matching_CVPR_2025_paper.pdf))

The most surprising finding: **the dominant 2025 sim-to-real strategy
in stereo depth is "1M synthetic pairs + foundation-model side-tuning",
not "domain-randomized GAN translation"** — meaning the right move on a
4 GB card is to consume someone else's 1M-pair UE-rendered training
set, not generate your own.

## The honest constraint

**Why you cannot get UE-quality visuals out of Gazebo Harmonic.**
Gazebo Harmonic's rendering engine is `ogre2` (Ogre-Next 2.x), not
Unreal. Ogre2 supports PBR materials in principle, but the Gazebo
integration ships with known issues — PBR textures load dimly with
washed colors due to lighting integration limitations
([gz-rendering issue #885](https://github.com/gazebosim/gz-rendering/issues/885))
— and there is no Lumen, no Nanite, no virtual shadow maps, no path
tracing, no temporal-AA. The visual ceiling of Gazebo Harmonic is
roughly the official `gazebosim/harmonic_demo` "Lake House" scene
([repo](https://github.com/gazebosim/harmonic_demo)), which is a
PBR-textured interior with cubemap sky — substantially below what UE5
produces with default settings on the same content.

**Why you cannot run UE5-class interactive sims on 4 GB.**
- **CARLA 0.10 (Dec 2024)** — UE5.5, Lumen, Nanite. Explicitly
  recommends **NVIDIA RTX 3000-series with at least 16 GB VRAM**;
  Town10 default map fails to load with <12 GB
  ([CARLA UE5 quickstart](https://carla-ue5.readthedocs.io/en/latest/start_quickstart/),
  [CARLA 0.10.0 release blog](https://carla.org/2024/12/19/release-0.10.0/),
  [CARLA UE5 OOM issue](https://github.com/carla-simulator/carla/issues/8964)).
- **CARLA 0.9.15 (Nov 2023)** — last UE 4.26 release. Documented
  baseline: GTX 1080 Ti minimum, RTX 3080+ recommended, **8 GB VRAM
  minimum**, 16 GB recommended
  ([CARLA build_faq](https://carla.readthedocs.io/en/latest/build_faq/)).
  4 GB users have hit OOM even on this older version
  ([discussion #4671](https://github.com/carla-simulator/carla/discussions/4671)).
- **Cosys-AirSim** (UE5.2 LTS / 5.5 main) — same Unreal lineage as
  AirSim. The AirSim FAQ states: Blocks demo runs on "typical laptops",
  Modular Neighborhood Pack needs 4 GB GPU, Open World needs 8 GB
  ([AirSim FAQ](https://microsoft.github.io/AirSim/faq/)).
  Cosys-AirSim README does not document its own minimum VRAM
  ([Cosys-AirSim README](https://github.com/Cosys-Lab/Cosys-AirSim/blob/main/README.md)).
- **Isaac Sim 5.x** — minimum GPU **RTX 3070**, with the docs noting
  that "due to VRAM constraints, some tutorials and benchmarks may not
  run on GPU below the minimum specifications"
  ([Isaac Sim requirements](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/requirements.html)).

The honest implication: **on this hardware, the path forward is
*datasets*, not a *new interactive sim*.** UE-rendered datasets capture
the photorealism the user wants; they're free; they fit on the 387 GB
SSD; and they don't require any GPU at training time beyond what the
3050 already provides for the model itself.

## UE-based interactive simulators

### CARLA

**Status (May 2026):** Two parallel branches.

- **CARLA 0.10.0** (released 2024-12-19) — UE 5.5, Lumen + Nanite. Maps
  rebuilt in UE5; Town10 default. Ubuntu 22.04 / Win11 minimum. 130 GB
  disk
  ([release blog](https://carla.org/2024/12/19/release-0.10.0/),
  [UE5 quickstart](https://carla-ue5.readthedocs.io/en/latest/start_quickstart/)).
  Hardware: **RTX 3000-series, 16 GB VRAM minimum recommended.**
- **CARLA 0.9.15** (released 2023-11-10) — last UE 4.26 release.
  Documented baseline: 8 GB VRAM minimum, 16 GB recommended
  ([0.9.15 release blog](https://carla.org/2023/11/10/release-0.9.15/),
  [build FAQ](https://carla.readthedocs.io/en/latest/build_faq/)).

**Hardware fit on RTX 3050 4 GB.** **Not viable for UE5 (0.10).**
**Marginal at best for 0.9.15** — multiple user reports of OOM with
4 GB cards even on smaller maps like Town01/Town02
([discussion #4671](https://github.com/carla-simulator/carla/discussions/4671)).
There is no documented "low-quality" mode that lowers the VRAM
requirement below 8 GB on 0.9.15 or 16 GB on 0.10.0.

**ROS 2 Jazzy bridge status.** Official `carla-simulator/ros-bridge`
does **not** publish a Jazzy distro release
([ros.index Jazzy lookup](https://index.ros.org/r/carla_ros_bridge/)).
Community fork `ttgamage/carla-ros-bridge` targets Humble + CARLA
0.9.15
([repo](https://github.com/ttgamage/carla-ros-bridge),
[guide on learnopencv](https://learnopencv.com/ros2-and-carla-setup-guide/)).
Issue [#9551 in carla-simulator/carla](https://github.com/carla-simulator/carla/issues/9551)
documents the FastDDS version mismatch (CARLA links 2.11.2, Jazzy
ships 2.14.5); after upgrading FastDDS to 2.14.5 communication does
not stall, but this is a hand-port, not a supported path.

**Maps available.** Town01–Town12 plus Town10HD. Town10 / Town10HD are
the showcases (UE5 in 0.10) but also the heaviest. Town01, Town02,
Town04 are smaller and load on 0.9.15 with 6–8 GB VRAM in user
reports.

**Drone fit.** CARLA is car-centric. There is no native multirotor
vehicle in CARLA. There is a free-camera "spectator" actor that can be
positioned arbitrarily — usable as a "kinematic camera rig" approach
for drone-style perception captures, but you give up CARLA's primary
value (its agent ecosystem) and you still pay the full GPU cost.

**Per-pixel depth + semantic segmentation.** Yes. CARLA exposes both
as sensor types via `carla.SensorType.DepthCamera` and
`carla.SensorType.SemanticSegmentationCamera`, with Cityscapes-style
class IDs.

**Verdict for THIS user:** **Skip.** Even on 0.9.15 the 4 GB ceiling
is too tight for reliable capture, and the ROS 2 Jazzy bridge is a
community hand-port. If the user upgrades to ≥ 8 GB VRAM, revisit
0.9.15 + the ttgamage Humble bridge running under a Jazzy overlay.

### Cosys-AirSim

**Status (May 2026):** Active. Main branch tracks Unreal 5.5, with
Unreal 5.2.1 maintained as long-term support
([Cosys-AirSim README](https://github.com/Cosys-Lab/Cosys-AirSim/blob/main/README.md),
[CHANGELOG](https://github.com/Cosys-Lab/Cosys-AirSim/blob/main/CHANGELOG.md)).
GitHub Issues tracker shows activity through Aug, Sept, Oct, Dec 2025
— the project is genuinely maintained, unlike upstream Microsoft
AirSim.

**Hardware fit on RTX 3050 4 GB.** No documented minimum on Cosys-AirSim
itself ([README](https://github.com/Cosys-Lab/Cosys-AirSim/blob/main/README.md)
contains no VRAM line). Inheriting from upstream AirSim FAQ
([microsoft.github.io/AirSim/faq](https://microsoft.github.io/AirSim/faq/)):
**Blocks** environment runs on typical laptops; **Modular Neighborhood
Pack** wants 4 GB minimum; **Open World** wants 8 GB. So the **Blocks
demo is the only environment that fits comfortably**, and Blocks is
not photoreal — it's the "engineering test" environment Microsoft
shipped specifically for low-spec hardware.

**ROS 2 wrapper.** A C++ ROS2 wrapper is included, supports all
Cosys-AirSim sensor extensions (annotation cameras, GPU LiDAR, echo
sensor)
([Cosys-AirSim docs](https://cosys-lab.github.io/Cosys-AirSim/)).
**Tested ROS 2 distro is not stated** in the README or docs.
Cosys-AirSim is developed at University of Antwerp; their own builds
imply Ubuntu 22.04 + Humble. ROS 2 Jazzy support is plausible (the
wrapper is pure C++ + ROS 2 standard messages) but not advertised.

**Sensors for stereo + depth + segmentation.** All three available.
- **Stereo:** define two cameras with a horizontal offset in `settings.json`.
- **Depth:** `Depth`, `DepthPlanar`, `DepthPerspective`, `DepthVis`
  image types
  ([Cosys-AirSim image API docs](https://cosys-lab.github.io/Cosys-AirSim/)).
- **Segmentation:** `Segmentation` and `Annotation` cameras —
  Cosys-AirSim's annotation system is its standout feature
  vs upstream AirSim, with **multi-layer object-instance and class
  labels**.

**Drone fit.** AirSim's home turf — quadrotor with stereo + depth +
segmentation is the canonical use case, supported out of the box. PX4
HITL/SITL also supported.

**Verdict for THIS user:** **Skip on 4 GB.** Blocks is too plain to
solve the user's "photoreal" complaint. Modular Neighborhood Pack and
Open World are the photoreal environments and they need 4–8 GB
minimum, leaving zero headroom for a perception model on the same
card. If the user upgrades to ≥ 8 GB, Cosys-AirSim becomes the
strongest pick for a drone-specific stereo + segmentation capture
pipeline.

### Microsoft AirSim (deprecated, here for completeness)

**Status (May 2026):** **Deprecated.** Microsoft archived active
development mid-2022; last release `v1.8.1` continues to compile but
no further updates from Microsoft
([microsoft/AirSim issue #5025 / Project AirSim announcement](https://github.com/microsoft/AirSim/issues/5025)).
Pin to UE 4.27 — UE 5.x is unsupported in upstream Microsoft AirSim
([build instructions](https://microsoft.github.io/AirSim/build_windows/)).

**Project AirSim** (the Microsoft successor, now spun out as `iamaisim`)
supports UE 5.2 and 5.7 only and is a complete rewrite
([iamaisim/ProjectAirSim](https://github.com/iamaisim/ProjectAirSim),
[system specs doc](https://github.com/iamaisim/ProjectAirSim/blob/main/docs/system_specs.md)).
System specs document defers GPU sizing to "your specific Unreal
environment complexity" — i.e. the same 4 GB / 8 GB tiering as
upstream AirSim.

**ROS 2 Jazzy.** Not documented for either the upstream Microsoft
AirSim or Project AirSim.

**Verdict for THIS user:** **Skip both.** Microsoft AirSim is dead;
Project AirSim is alive but doesn't change the hardware story. Use
Cosys-AirSim if you want anything in the AirSim lineage.

### NVIDIA Isaac Sim

**Status (May 2026):** **5.x line** is current, built on Omniverse
Kit. Isaac Sim ships per-pixel depth, semantic / instance
segmentation, stereo cameras as native sensor types and has the
strongest ROS 2 bridge of any commercial sim
([Isaac Sim ROS 2 install](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/install_ros.html)).

**Hardware fit on RTX 3050 4 GB.** **Will not run.** Documented
minimum is RTX 3070 (8 GB VRAM)
([Isaac Sim 5.1 requirements](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/requirements.html)),
with explicit warnings: "due to VRAM constraints, some tutorials and
benchmarks may not run on GPU below the minimum specifications" and
"8 GB VRAM is insufficient to run a complex scene rendering more than
16 MP per frame". A 3050 4 GB is a full tier below the listed minimum.
There is no documented "low-quality mode" that lowers the floor.

**ROS 2 Jazzy bridge.** Mature — first-party support, lower friction
than CARLA's bridge.

**Verdict for THIS user:** **Skip.** Off the table on this hardware.
Even hardware accelerated multi-GPU "training fleet" Isaac Lab
deployments assume ≥ 8 GB cards.

### Other UE / Unity sims worth knowing

- **Project Anywhere** (DRL Sim, Drone Racing League) — closed-source,
  proprietary trainer. Not usable here ([drl.io](https://www.drl.io/drl-sim)).
- **Flightmare** (UZH Robotics & Perception Group) — Unity-based drone
  sim with photoreal environments, used for AlphaPilot 2019. Active
  but not ROS 2 native ([Flightmare paper](https://arxiv.org/abs/2009.00563)).
  Skip — Unity tooling overhead vs. Gazebo for a one-person project.
- **AirGen** (Imperial / IROS 2024) — uses Cosys-AirSim plus generative
  scene assets. Same hardware envelope. Skip.
- **Aerial Gym Simulator** (NTNU) — NVIDIA Isaac Gym based, **3090-class
  GPU** assumed in the paper
  ([arxiv 2503.01471](https://arxiv.org/html/2503.01471v1)). Skip on
  4 GB.
- **MetaDrive** (CMU + UMich) — procedural driving sim. Lightweight
  rendering; not photoreal, comparable visual fidelity to Gazebo.
  Doesn't solve the user's problem.

## UE-rendered static synthetic datasets

These are the *primary* recommendation surface for THIS user. All
listed below were generated via Unreal Engine (or comparable
photoreal pipelines) and shipped as on-disk image + depth +
segmentation tuples that you load with a normal PyTorch DataLoader —
**zero runtime GPU cost beyond the training step itself**.

### TartanAir / TartanAir V2 — **★ primary pick for drone perception**

**Source:** Carnegie Mellon AirLab, 2020 (V1) / 2024+ (V2)
([V1 site](https://theairlab.org/tartanair-dataset/),
[V2 site](https://tartanair.org/),
[V1 paper IROS 2020](https://arxiv.org/abs/2003.14338),
[GitHub tools repo](https://github.com/castacks/tartanair_tools),
[V2 spatial AI lab page](https://sairlab.org/datasets/tartanair)).

**Modalities (V1 + V2):** Stereo RGB, depth, semantic segmentation,
optical flow, simulated LiDAR points, simulated IMU readings, camera
poses. V2 adds: **event cameras**, customizable lens (pinhole /
fisheye / equirectangular).

**Volume:** V1 = 30 photo-realistic UE environments × multiple
trajectories per scene, with stereo RGB at standard resolution. V2
extends this with new environments and the **TartanGround** subset
specifically for ground robot perception.

**Drone fit:** **The dataset is *built* for drone trajectories** —
virtual cameras follow flight-style paths through the UE
environments, with weather/lighting variation. Among UE-based static
datasets, this is **the closest to a "drone target-following"
training distribution**.

**Stereo for stereo-depth model training:** Native — ground-truth
stereo disparity is part of the V1 release.

**License:** V1 = BSD (CMU); V2 = Creative Commons Attribution 4.0
International + MIT toolkit
([V2 docs landing](https://tartanair.org/)).

**Download:** `pip install tartanair`; data hosted on AirLab server
(US) plus HuggingFace mirror. Toolkit at
[castacks/tartanair_tools](https://github.com/castacks/tartanair_tools)
and [castacks/tartanairpy](https://github.com/castacks/tartanairpy).

**Estimated total size:** Multi-TB for the full dataset; selectable
per-environment download supported via the toolkit. Plan for **at
least 200 GB** if you take a representative subset across
environments. Fits on the SSD's 387 GB.

**Citation:**
```
@inproceedings{wang2020tartanair,
  title={TartanAir: A Dataset to Push the Limits of Visual SLAM},
  author={Wang, Wenshan and Zhu, Delong and Wang, Xiangwei and others},
  booktitle={IROS},
  year={2020}
}
```

### Virtual KITTI 2 — **★ primary pick for urban stereo**

**Source:** Naver Labs Europe, 2020
([blog](https://europe.naverlabs.com/blog/announcing-virtual-kitti-2/),
[paper PDF](https://europe.naverlabs.com/wp-content/uploads/2020/01/vkitti2.pdf),
[arxiv 2001.10773](https://arxiv.org/abs/2001.10773),
[download / Proxy Virtual Worlds page](https://europe.naverlabs.com/proxy-virtual-worlds-vkitti-2/)).

**Note on engine:** VKITTI 2 is rendered in **Unity**, not Unreal. The
user's framing was "Unreal-engine-quality"; VKITTI 2 hits the same
visual-fidelity tier (Naver Labs explicitly upgraded the engine for
photorealism in v2). Treat it as UE-quality for the purposes of this
research.

**Modalities:** Stereo RGB (camera 1 = 0.5327 m to the right of
camera 0), per-pixel depth, class segmentation, instance segmentation,
**forward + backward optical flow**, **forward + backward scene flow**
— all rendered for both cameras.

**Volume:** 5 scene clones from the KITTI tracking benchmark, each in
multiple variants: clear, **fog**, **rain**, sunset, sunrise, morning,
overcast, **camera rotated 15°**, etc. ~21,000 frames per camera per
clone × 5 clones × ~10 variants. RGB JPG, depth PNG16
(1 intensity unit = 1 cm).

**License:** Creative Commons Attribution-NonCommercial-ShareAlike 3.0
— **research-only**.

**Download:**
[europe.naverlabs.com/Research/Computer-Vision/Proxy-Virtual-Worlds](https://europe.naverlabs.com/Research/Computer-Vision/Proxy-Virtual-Worlds/).
Total: ~50 GB for the full dataset (estimated from Naver mirrors;
exact number not published).

**Citation:** Cabon, Murray, Humenberger 2020.

### Synscapes

**Source:** 7D Labs (formerly part of FOI Sweden), 2018
([dataset site](https://synscapes.on.liu.se/),
[7DLabs overview](https://7dlabs.com/synscapes-overview),
[paper PDF](https://www.researchgate.net/publication/328446314_Synscapes_A_Photorealistic_Synthetic_Dataset_for_Street_Scene_Parsing)).

**Modalities:** RGB (1440×720 native; 2048×1024 upscaled in
`img/rgb-2k`), per-pixel **class segmentation** (Cityscapes 19-class),
**instance segmentation**, **depth**, JSON metadata per frame
(scene + camera + per-instance metadata).

**Volume:** 25,000 procedurally-generated unique scenes (one image per
scene — not a video sequence). **No stereo pair.** The Cityscapes
class IDs are honored, so this is the canonical "synthetic training
buddy" for Cityscapes-style models.

**License:** Free for non-commercial research; obtain via per-request
form on the dataset site.

**Download size:** ~80 GB (per the per-image-set distribution).

**Verdict for THIS user:** Useful for the **segmentation head** of
the stereo-+-segmentation model, paired with VKITTI 2 for the stereo
head.

### Mid-Air

**Source:** University of Liège, 2019
([dataset site](https://midair.ulg.ac.be/),
[paper PDF](https://openaccess.thecvf.com/content_CVPRW_2019/papers/UAVision/Fonder_Mid-Air_A_Multi-Modal_Dataset_for_Extremely_Low_Altitude_Drone_Flights_CVPRW_2019_paper.pdf),
[tech specs](https://midair.ulg.ac.be/tech_specs.html),
[download page](https://midair.ulg.ac.be/download.html)).

**Modalities:** **Stereo RGB** (left, right, downward), **depth**,
**semantic segmentation** (13 classes), **stereo disparity**, surface
normals, occlusion masks, IMU + GPS at flight-controller rates (IMU
100 Hz, GPS 1 Hz). Visual data at 25 Hz, FOV 90°.

**Volume:** **54 trajectories, ~420,000 frames** across multiple
weather conditions per trajectory (Kite environment: 30 trajectories
× 4 weather; PLE environment: 24 trajectories × 3 seasons).

**Engine:** Unreal Engine, with a custom enhanced-deferred-shading
pipeline.

**License:** Creative Commons Attribution-NonCommercial-ShareAlike 4.0
International — research only, attribution required.

**Download:** Form-driven; user selects desired modalities, receives
a config file with `wget` archive links. **Total size not published**
on the dataset site; based on per-modality archive sizes from the
download page, plan for ~150 GB if you take all weather variants of
both environments at all modalities.

**Verdict for THIS user:** **★ second-strongest drone-specific
candidate after TartanAir**, especially because of the explicit
low-altitude UAV framing — closer to the user's project than TartanAir's
SLAM-benchmark framing.

### SHIFT

**Source:** ETH Zurich + Google + MPI 2022
([CVPR 2022 paper](https://openaccess.thecvf.com/content/CVPR2022/papers/Sun_SHIFT_A_Synthetic_Driving_Dataset_for_Continuous_Multi-Task_Domain_Adaptation_CVPR_2022_paper.pdf),
[dataset site](https://www.vis.xyz/shift/),
[arxiv 2206.08367](https://arxiv.org/abs/2206.08367)).

**Engine:** **CARLA** (which is UE4-based).

**Modalities:** Multi-view RGB (Front, Front-Left, Left/Right ±45°,
Left/Right ±90°), **stereo RGB** (50 cm horizontal baseline), depth
maps for all views at 10 fps, semantic + instance segmentation,
2D + 3D bounding boxes, optical flow, LiDAR.

**Continuous shifts:** Cloudiness, rain intensity, fog, time-of-day,
vehicle + pedestrian density — **per-trajectory continuous variation**,
which is rare. Designed for continuous domain adaptation experiments.

**License:** Free for research.

**Download:** Per-modality from the dataset site; total ~2.5 TB for
the full release. **Won't fit on the SSD if you take the whole thing**
— pick modality + view subsets.

**Verdict for THIS user:** Strong urban-driving stereo + segmentation
data for fine-tuning, but a **3050 will not train on the full SHIFT in
finite time**. Take the discrete-shift subset (50 GB) for tractable
training.

### UrbanSyn — **most photoreal urban synthetic of 2024**

**Source:** UAB Barcelona / Eurecat / 7DLabs lineage, 2024
([dataset site](https://www.urbansyn.org/),
[arxiv 2312.12176](https://arxiv.org/abs/2312.12176),
[HuggingFace mirror](https://huggingface.co/datasets/UrbanSyn/UrbanSyn)).

**Modalities:** RGB (2048×1024), **depth**, **semantic segmentation**
(Cityscapes 19-class), **panoptic instance segmentation**, 2D
bounding boxes. **No native stereo pair** in the v1 release.

**Volume:** 7,539 unique unbiased-path-tracing rendered images
(generated with industry-standard offline path tracer + AI denoising —
*not* a video-game engine pipeline).

**License:** **CC-BY-SA 4.0 (commercial use allowed!)** — almost
unique among photoreal synthetic urban datasets.

**Verdict for THIS user:** Use it as a **segmentation distribution
booster** alongside Synscapes + Virtual KITTI 2. Skip for stereo (no
native stereo pair).

### DDOS — drone-specific UE synthetic, CVPR 2024

**Source:** Imperial College London, CVPR 2024 Workshop on Vision-based
Drone Understanding
([paper](https://openaccess.thecvf.com/content/CVPR2024W/VDU/papers/Kolbeinsson_DDOS_The_Drone_Depth_and_Obstacle_Segmentation_Dataset_CVPRW_2024_paper.pdf),
[arxiv 2312.12494](https://arxiv.org/abs/2312.12494),
[HuggingFace dataset](https://huggingface.co/datasets/benediktkol/DDOS)).

**Modalities:** RGB, depth, **pixel-wise semantic segmentation**
(10 classes including ultra-thin / thin / mesh wires — designed for
*obstacle avoidance for drones*), optical flow, surface normals.

**Volume:** 340 unique simulated drone flights → 30 K training images,
2 K validation, 2 K testing. Synthetic UE-based.

**License:** See HuggingFace page (typically CC-BY for these CVPRW
releases).

**Verdict for THIS user:** Niche — the class taxonomy is specifically
for *obstacle avoidance* (wires, mesh, vegetation), not target
following. **Useful as auxiliary data** if drone collision avoidance
ever enters scope; not the primary training set.

### Forest Inspection Dataset (Mariotti 2024)

**Source:** Mariotti et al., 2024
([arxiv 2403.06621](https://arxiv.org/html/2403.06621v1),
[Nature Scientific Data 2026](https://www.nature.com/articles/s41597-026-06665-x)).
UE5-based forest aerial views with semantic segmentation + depth.
Open-terrain coverage that complements TartanAir's mixed environments.

### GTA5 Playing-for-Data — older, but huge

**Source:** Richter et al., ECCV 2016
([paper](https://download.visinf.tu-darmstadt.de/data/from_games/data/eccv-2016-richter-playing_for_data.pdf),
[download](https://download.visinf.tu-darmstadt.de/data/from_games/),
[arxiv 1608.02192](https://arxiv.org/abs/1608.02192)).

**Modalities:** RGB (1914×1052) + **semantic segmentation only**
(19 classes Cityscapes-compatible). **No depth, no stereo.**

**Volume:** 24,966 images.

**License:** Per the project page, research-use; tied to GTA5 EULA so
**cannot be redistributed**.

**Verdict for THIS user:** Useful as a *segmentation* augmentation
distribution. Skip for stereo / depth.

### AirSim Drone Racing Lab dataset (NeurIPS 2019)

**Source:** Madaan et al. 2020 (Microsoft Research)
([paper](https://msl.stanford.edu/papers/madaan_airsim_2020.pdf),
[arxiv 2003.05654](https://arxiv.org/pdf/2003.05654),
[binaries on GitHub](https://github.com/microsoft/AirSim-NeurIPS2019-Drone-Racing)).

**Three UE environments**: Soccer Field, ZhangJiaJie, MSR Building 99,
nine racing tracks. Modalities: monocular, depth, neuromorphic events,
optical flow.

**Volume:** Limited — designed for the competition, not as a general
training set.

**Verdict for THIS user:** Skip for primary training; useful as *gate
detection* eval if drone-racing ever enters scope.

### Other UE / synthetic datasets briefly

- **VEIS, SYNTHIA-RAND, GTAV-Synthia** — older synthetic urban
  datasets, mostly Cityscapes-class segmentation. Lower visual fidelity
  than UrbanSyn / Synscapes — **skip in favor of newer datasets**.
- **AirSim City Environment / Mountain Environment** demo binaries —
  free Microsoft binaries from 2018, no companion dataset, intended
  for users to capture their own. **Skip — captures need the sim
  itself running, which the user can't.**
- **MetaDrive procedural** — lightweight visuals, not photoreal. Skip.
- **ParallelDomain** — commercial. Free public PD-tier datasets are
  small evaluation slices (`PD-LIDAR-1024`, `PD-Maps-1024`). Skip.
- **ApolloScape Synthetic** — Baidu, **synthetic stereo** + segmentation,
  ~140 K frames. Older, Cityscapes-class. Useful but not better than
  Virtual KITTI 2 for the user's needs.

## Real-world datasets for stereo / drone perception

### DrivingStereo — **★ user's reference, primary real-stereo set**

**Source:** Tsinghua + The Chinese University of Hong Kong, CVPR 2019
([dataset site](https://drivingstereo-dataset.github.io/),
[paper](https://openaccess.thecvf.com/content_CVPR_2019/papers/Yang_DrivingStereo_A_Large-Scale_Dataset_for_Stereo_Matching_in_Autonomous_Driving_CVPR_2019_paper.pdf)).

**Modalities:** Stereo RGB, **disparity (model-guided LiDAR fusion,
not raw LiDAR)**.

**Volume:** **174,437 training + 7,751 testing pairs**, 38 / 4 video
sequences, ~180 K total. Hundreds of times larger than KITTI Stereo.

**Coverage:** **Beijing urban + suburban + highway + elevated +
country roads**, **sunny / rainy / cloudy / foggy / dusky**.

**License:** Research-only (per dataset page).

**Verdict for THIS user:** **★ this is the user's named reference, and
it is the right pick** as the primary real-world stereo training set.
Larger than KITTI stereo, weather-diverse, urban + suburban content
matches the project's "follow target through urban scene" framing.

### KITTI Stereo (KITTI 2015 / KITTI 2012)

**Source:** Karlsruhe, IJCV 2013
([benchmark site](https://www.cvlibs.net/datasets/kitti/eval_scene_flow.php?benchmark=stereo)).

**Volume:** Tiny by 2026 standards — 200 training pairs (KITTI 2015),
194 (KITTI 2012). The reason it remains relevant is **it is the
canonical stereo benchmark**, and every paper reports on it.

**Verdict for THIS user:** **Use as evaluation, not training.** Train
on DrivingStereo + synthetic; evaluate on KITTI Stereo to compare
against the published leaderboard.

### KITTI-360

**Source:** MPI / Karlsruhe, PAMI 2022
([site](https://autonomousvision.github.io/kitti-360/),
[arxiv 2109.13410](https://arxiv.org/abs/2109.13410),
[paper PDF](https://www.cvlibs.net/publications/Liao2022PAMI.pdf)).

**Modalities:** 360° stereo (perspective + fisheye), pushbroom LiDAR,
**dense 2D + 3D semantic + instance annotations** across 150 K frames
+ 1B 3D points. Suburban Karlsruhe.

**Verdict for THIS user:** Heavy. Take only the perspective-stereo
subset for stereo-depth training. Useful for **panoptic segmentation**
as an evaluation set.

### Cityscapes

**Source:** Daimler / TU Darmstadt 2016 ([cityscapes-dataset.com](https://www.cityscapes-dataset.com/)).

**Modalities:** Stereo RGB (rectified pair) + 19-class semantic
segmentation. Real urban driving.

**Volume:** 5,000 finely-annotated + 20,000 coarsely-annotated
European urban scenes.

**Verdict for THIS user:** **Standard real-world segmentation
training set**. Pair with Synscapes + UrbanSyn (synthetic) for
multi-source training.

### VisDrone

**Source:** Tianjin University AISKYEYE 2018
([dataset](https://github.com/VisDrone/VisDrone-Dataset),
[ultralytics docs](https://docs.ultralytics.com/datasets/detect/visdrone)).

**Volume:** 288 video clips / 261,908 frames + 10,209 static images,
real drone-mounted captures, mostly Chinese urban scenes.

**Annotations:** Bounding boxes for 10 classes + tracking. **No
semantic segmentation, no depth.**

**Verdict for THIS user:** Useful **only for the eventual target-
following / tracking head** if the project gets there. Not for stereo
depth or semantic segmentation training.

### UAVDT

**Source:** Du et al. 2018
([dataset](https://sites.google.com/view/grli-uavdt)).

**Volume:** ~80,000 annotated frames, 14 attributes, urban locations
(squares, highways, intersections). Detection + tracking only — **no
segmentation, no depth.**

**Verdict for THIS user:** Skip — detection-only, not perception.

### UAVid — **★ best real-world drone semantic seg**

**Source:** Lyu et al., ISPRS 2020
([arxiv 1810.10438](https://arxiv.org/abs/1810.10438),
[dataset site](https://uavid.nl/)).

**Volume:** 30 video sequences × 4K resolution, 300 densely-labeled
frames, 8 classes (buildings, roads, static vehicles, trees, low
vegetation, people, moving vehicles, clutter).

**Verdict for THIS user:** **★ Best real-world drone semantic seg
dataset** of practical size, slanted views (matches FPV drone
viewpoint better than top-down aerial datasets).

### VDD — Varied Drone Dataset

**Source:** Cai et al., JVCI 2024
([arxiv 2305.13608](https://arxiv.org/html/2305.13608v3),
[GitHub](https://github.com/RussRobin/VDD)).

**Volume:** 400 high-resolution images, 7 classes (Wall, Roof, Road,
Water, Vehicle, Vegetation, Others). Urban + industrial + rural +
natural.

**Verdict for THIS user:** Augmentation for UAVid; small but diverse.

### UDD — Urban Drone Dataset

**Source:** PKU PRCV 2018
([GitHub](https://github.com/MarcWong/UDD)).

**Volume:** 141 images, 6 classes, 60–100 m altitude. Tiny.

**Verdict for THIS user:** Augmentation only.

### AU-AIR

**Source:** Bozcan & Kayacan, ICRA 2020
([arxiv 2001.11737](https://ar5iv.labs.arxiv.org/html/2001.11737),
[Python API](https://github.com/sunw71/auairdataset)).

**Modalities:** Real drone visual + GPS + IMU + altitude + velocity,
8 video streams, 1920×1080 @ 30 fps from Aarhus traffic surveillance.
**No semantic segmentation, no depth maps** — bounding boxes only.

**Verdict for THIS user:** Skip — does not give you depth or
segmentation.

### Stanford Drone Dataset

**Source:** Robicquet et al., ECCV 2016
([SDD page](https://cvgl.stanford.edu/projects/uav_data/)).

**Modalities:** Top-down drone footage of pedestrians + vehicles in
the Stanford campus, **bounding-box trajectories only — no segmentation,
no depth, no stereo**.

**Verdict for THIS user:** Skip for perception training.

### Aerial Image Segmentation Dataset (AISD)

**Source:** University of Toronto + Google AI 2017
([paperswithcode entry](https://paperswithcode.com/dataset/aerial-image-segmentation-dataset)).

**Volume:** 80 high-resolution aerial photos with road segmentation
(road / non-road). Top-down only, single class.

**Verdict for THIS user:** Skip — too narrow.

### MESSI / Forest Inspection / others

- **MESSI** ([arxiv 2505.08589](https://arxiv.org/html/2505.08589v1)) —
  multi-elevation urban semantic seg, 2025. Worth tracking.
- **Aerial Image Dataset (AID)** — scene classification, not seg.
- **iSAID** — instance seg on satellite imagery, top-down only.

## UE → Gazebo / USD → Gazebo asset pipelines (status)

**Honest verdict: there is no production pipeline.** What does exist:

1. **Unreal's built-in glTF Exporter** (UE 5.1+) — exports
   selected actors, assets, or full levels to glTF / glb
   ([docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/exporting-unreal-engine-content-to-gltf),
   [bulk export community plugin](https://github.com/kalrach/unreal2gltf)).
   The output is glTF, which **Gazebo Harmonic loads via gz-rendering's
   PBR-capable mesh loader**. You still have to wrap each glTF in a
   `<model.sdf>` and assemble a world.

   **Catch:** Lumen / Nanite / virtual shadow maps **do not survive
   the glTF roundtrip**. You get the static geometry + base PBR
   materials and lose the dynamic-GI lighting that makes UE5 look
   "right". The visual fidelity drop is significant — what looks
   photoreal in UE looks "ok PBR" in Gazebo.

2. **USD → glTF → SDF** — possible via Blender (with Pixar's USD
   plugin) → glTF export → hand-wrap. **No automated pipeline.**
   NVIDIA's MeshConverter goes glTF → USD (the *wrong* direction)
   ([Isaac Lab import-asset doc](https://isaac-sim.github.io/IsaacLab/main/source/how-to/import_new_asset.html)).

3. **Heightmap + texture only** — works fine. Tools like
   `saiaravind19/gazebo_terrain_generator` already do
   satellite-imagery + DEM → SDF; OSM2World does OSM → glTF (with PBR)
   → wrap → SDF. These are the **realistic** "import a real-world
   place into Gazebo" paths and they're already documented in the
   project's `prebuilt_worlds.md`.

4. **No Cesium for Gazebo, no Isaac asset converter to glTF/SDF**
   exists as a maintained tool — confirmed by the Open Robotics
   Discourse asset-import workflow thread
   ([link](https://discourse.openrobotics.org/t/improving-asset-import-workflow-for-external-models-with-textures-fbx-gltf-glb-usdz-etc/54622)).

**Implication for THIS user:** **Don't try to "import UE5 assets into
Gazebo".** Even the actors that survive the export will look worse in
Gazebo than they did in UE because the lighting model is different.
The *right* lever is "use a UE-rendered *dataset*", which captures the
UE lighting at render time and ships it as PNGs.

## Hybrid training approaches (recent papers)

The dominant 2024–2026 patterns for stereo + segmentation with mixed
real + synthetic data:

### 1. Massive synthetic pretraining + small real fine-tune (current SOTA for stereo)

**FoundationStereo** (NVlabs, **CVPR 2025 Best Paper Nomination**)
([repo](https://github.com/NVlabs/FoundationStereo),
[paper PDF](https://openaccess.thecvf.com/content/CVPR2025/papers/Wen_FoundationStereo_Zero-Shot_Stereo_Matching_CVPR_2025_paper.pdf)).
- Trains on **1M synthetic stereo pairs** with high diversity + high
  photorealism + automatic self-curation.
- Side-tunes a vision-foundation-model backbone (DINOv2-class) to
  bring monocular priors into the stereo cost-volume.
- Achieves **strong zero-shot generalization** — releases pretrained
  models that work on real-world data **without task-specific
  fine-tuning**.
- **Fast-FoundationStereo** is the CVPR 2026 follow-on
  ([repo](https://github.com/NVlabs/Fast-FoundationStereo)) — real-time
  zero-shot, designed for deployment.

**DEFOM-Stereo** (CVPR 2025) — distills Depth Anything V2 into a
stereo matcher
([paper](https://openaccess.thecvf.com/content/CVPR2025/papers/Jiang_DEFOM-Stereo_Depth_Foundation_Model_Based_Stereo_Matching_CVPR_2025_paper.pdf)).

**Stereo Anywhere** (CVPR 2025 Oral) — robust zero-shot deep stereo
even where stereo or mono fails individually
([CVPR poster](https://cvpr.thecvf.com/virtual/2025/poster/32466)).

**Depth Pro** (Apple, ICLR 2025) — combines real + synthetic for
metric depth
([paper PDF](https://proceedings.iclr.cc/paper_files/paper/2025/file/bc8b2058fd96978a4146f18298cb2d39-Paper-Conference.pdf)).

**Operational implication for THIS user:** The realistic 2026 path
for stereo depth on this hardware is **"download FoundationStereo
weights, run inference"**, not "train your own from scratch". For
custom adaptation: take the FoundationStereo backbone, add a small
LoRA / side-tune on the user's domain, train on a small real subset
(DrivingStereo) — **this fits in 4 GB**.

### 2. Synthetic → real domain adaptation (semantic seg)

**UrbanSyn → Cityscapes** (UrbanSyn paper, 2024)
([arxiv 2312.12176](https://arxiv.org/abs/2312.12176)) reports SOTA
unsupervised domain adaptation by combining **GTA5 + Synscapes +
UrbanSyn** as the synthetic source — three-source synthetic blends
beat any single-source.

**Vision-language adaptation** (NeurIPS 2024)
([Generalize or Detect paper](https://proceedings.neurips.cc/paper_files/paper/2024/file/5d3b57e06e3fc45f077eb5c9f28156d4-Paper-Conference.pdf))
— EVA02-L gives +10.0 mIoU vs standard encoders on Cityscapes when
fine-tuned from synthetic.

**SHIFT continuous shift** (ETH 2022) shows that multi-task training
on (semantic seg + depth + instance) **improves robustness under
weather/lighting shift** vs single-task training
([SHIFT paper](https://openaccess.thecvf.com/content/CVPR2022/papers/Sun_SHIFT_A_Synthetic_Driving_Dataset_for_Continuous_Multi-Task_Domain_Adaptation_CVPR_2022_paper.pdf)).
**Implication:** train one head for depth + one for segmentation
sharing a backbone — not two separate models — to amortize the
4 GB VRAM budget.

### 3. Domain randomization (older, increasingly obsolete)

Texture randomization (LTR / GTR; Pubmed 2021) and CycleGAN-style
sim2real translations were the 2017–2021 standard but have been
**displaced by foundation-model pretraining** in 2024–2026 work. Don't
build a new pipeline around CycleGAN today — use a foundation backbone
instead.

## Recommendation for THIS user

**One concrete primary path:**

> **Train on TartanAir V2 + Virtual KITTI 2 + Synscapes (synthetic, all
> UE/Unity-rendered) → fine-tune on DrivingStereo + Cityscapes (real)
> → deploy in Gazebo Harmonic for closed-loop control.**

Specifically:

1. **Bootstrap immediately with FoundationStereo pretrained weights**
   ([NVlabs/FoundationStereo](https://github.com/NVlabs/FoundationStereo))
   — get a working stereo depth model in days, not months. It's
   trained on 1M synthetic stereo pairs already and generalizes
   zero-shot. The 3050 4 GB will run *inference* on it; training the
   full model on it would not fit, but you don't need to.

2. **For semantic segmentation**, fine-tune a Cityscapes-pretrained
   small backbone (Segformer-B0 / DINOv2-S frozen) on:
   - **Cityscapes** (real, 5K fine-annotated) as the anchor
     distribution.
   - **Synscapes + UrbanSyn** as the synthetic boosters (both are
     Cityscapes-class compatible — drop-in mixing).
   - **UAVid** (real drone, slanted view) for the *drone-perspective*
     fine-tune to bridge the camera angle gap from car-view
     Cityscapes to drone-view targets.
   This stack matches the SOTA "multi-source synthetic + real" recipe
   from UrbanSyn 2024 and the NeurIPS 2024 vision-language adaptation
   work.

3. **For drone-specific stereo distribution**, augment with subsets of
   **TartanAir V2** (drone trajectories, UE-based, native stereo +
   depth + segmentation). Pull only 2–3 environments to keep disk
   under 100 GB.

4. **Keep Gazebo Harmonic for the control / target-following loop**
   per `drone_simulation.md`. Capture stereo + segmentation labels in
   Gazebo only when the model is good enough to evaluate; **do not
   try to use Gazebo as the photoreal training distribution**.
   Use Gazebo's photoreal-ish worlds (Clearpath `office_construction`,
   `orchard`; Mars + Ingenuity from `spaceros_gz_demos`; Forest3D for
   procedural forests) as the *deployment* environment for the trained
   model — i.e., as a sim-to-deployment proxy, not as training data.

**Why this is the best fit:**

- **Solves the user's "Gazebo isn't photoreal enough" complaint** —
  the *training* distribution is now UE-rendered (TartanAir V2,
  Virtual KITTI 2, UrbanSyn, Synscapes are all rendered with offline
  PBR or path-tracing pipelines that hit higher fidelity than any
  realtime Gazebo could give).
- **Fits the 4 GB hardware ceiling** — no UE5 simulator runs at
  capture-time. Training is offline PyTorch, sized to the 3050.
- **Keeps the existing Gazebo + ROS 2 Jazzy stack as the deployment
  surface** — sunk-cost preservation.
- **Lines up with 2025–2026 SOTA** — FoundationStereo + multi-source
  synthetic + small real fine-tune is the published winning recipe for
  stereo and segmentation on small hardware.
- **Avoids tooling rabbit holes** — no carla-ros-bridge hand-port to
  Jazzy, no UE5 install, no Cosys-AirSim build. The user keeps shipping.

**What this gives up:**

- **No drone-perspective training data with full UE5 lighting** unless
  the user accepts TartanAir V2's UE-rendered drone trajectories as
  "close enough" (they are — the AirLab puts real engineering effort
  into the photorealism).
- **No closed-loop sim-to-real evaluation of the trained model in a
  UE-class environment** — the deployment-side validation is in
  Gazebo, which is not as photoreal as the training data. Domain shift
  Gazebo → real world is a known gap; the user must validate on real
  data eventually.
- **No bespoke target objects** — if the project later needs the drone
  to follow a specific costume / vehicle / object that's not in
  TartanAir / Cityscapes / DrivingStereo, that data has to come from
  somewhere else. Gazebo capture (the existing pipeline) becomes the
  fallback for these custom targets.

## Setup instructions for the recommended path

### 0. Disk planning — fits comfortably on the 387 GB SSD

```
/media/abrar/AbrarSSD/ROS/drone_targeting_research/
└── data/
    ├── synthetic/
    │   ├── tartanair_v2/         # ~100 GB — pull 2-3 environments
    │   ├── virtual_kitti_2/      # ~50 GB — full release
    │   ├── synscapes/            # ~80 GB — full release
    │   ├── urbansyn/             # ~30 GB — full release
    │   └── mid_air/              # ~50 GB — Kite environment only
    ├── real/
    │   ├── drivingstereo/        # ~150 GB — full training
    │   ├── kitti_stereo_2015/    # ~20 GB — eval only
    │   ├── cityscapes/           # ~20 GB — full fine-annotated
    │   └── uavid/                # ~10 GB
    └── checkpoints/
        ├── foundationstereo/     # ~2 GB pretrained weights
        └── segformer_b0/         # ~50 MB pretrained
```

Total: ~510 GB if everything taken; ~250 GB if you trim to TartanAir
V2 (50 GB) + VKITTI2 + Synscapes + DrivingStereo + Cityscapes.

### 1. FoundationStereo (immediate baseline — works zero-shot)

```bash
mkdir -p /media/abrar/AbrarSSD/ROS/drone_targeting_research/data/checkpoints
cd /media/abrar/AbrarSSD/ROS/drone_targeting_research
git clone https://github.com/NVlabs/FoundationStereo.git
cd FoundationStereo
# Install per the README (PyTorch + xformers + a few utilities)
pip install -r requirements.txt
# Download pretrained weights (link in README — currently HuggingFace mirror)
# Run zero-shot inference on a stereo pair you already have from Gazebo:
python scripts/run_demo.py --left <left.png> --right <right.png> \
    --intrinsic_file <K.txt> --out_dir results/
```

Confirm a baseline stereo depth pipeline works **before** any
training. This is the fastest way to validate the project's perception
target on the user's existing Gazebo captures.

### 2. TartanAir V2 download

```bash
pip install tartanair
mkdir -p /media/abrar/AbrarSSD/ROS/drone_targeting_research/data/synthetic/tartanair_v2
cd /media/abrar/AbrarSSD/ROS/drone_targeting_research/data/synthetic/tartanair_v2
python -c "
import tartanair as ta
ta.init('.', verbose=True)
# Pull just two environments for an MVP (each ~30-50 GB)
ta.download(env=['CarWelding', 'Downtown'],
            modality=['image', 'depth', 'seg'],
            camera_name=['lcam_front', 'rcam_front'])
"
```

Per the [TartanAir V2 site](https://tartanair.org/) and
[GitHub tools](https://github.com/castacks/tartanair_tools).

### 3. Virtual KITTI 2 download

```bash
mkdir -p /media/abrar/AbrarSSD/ROS/drone_targeting_research/data/synthetic/virtual_kitti_2
cd /media/abrar/AbrarSSD/ROS/drone_targeting_research/data/synthetic/virtual_kitti_2
# Download tarballs from
#   https://europe.naverlabs.com/proxy-virtual-worlds-vkitti-2/
# Required: vkitti_2.0.3_rgb.tar, vkitti_2.0.3_depth.tar,
#           vkitti_2.0.3_classSegmentation.tar, vkitti_2.0.3_textgt.tar
# Each tarball is split per-scene; full release ~50 GB.
for f in *.tar; do tar xf "$f"; done
```

### 4. Synscapes — request access via form

```bash
# Visit https://synscapes.on.liu.se/ and submit the access form.
# You receive a download URL by email. Sample fetch:
mkdir -p /media/abrar/AbrarSSD/ROS/drone_targeting_research/data/synthetic/synscapes
cd /media/abrar/AbrarSSD/ROS/drone_targeting_research/data/synthetic/synscapes
wget -c <URL_FROM_EMAIL>
unzip synscapes.zip
```

### 5. UrbanSyn (no form, public)

```bash
mkdir -p /media/abrar/AbrarSSD/ROS/drone_targeting_research/data/synthetic/urbansyn
cd /media/abrar/AbrarSSD/ROS/drone_targeting_research/data/synthetic/urbansyn
# Either via HuggingFace
pip install datasets
python -c "
from datasets import load_dataset
ds = load_dataset('UrbanSyn/UrbanSyn',
                  cache_dir='/media/abrar/AbrarSSD/ROS/drone_targeting_research/data/synthetic/urbansyn')
print(ds)
"
# Or from https://www.urbansyn.org/
```

### 6. DrivingStereo (the user's named reference)

```bash
mkdir -p /media/abrar/AbrarSSD/ROS/drone_targeting_research/data/real/drivingstereo
cd /media/abrar/AbrarSSD/ROS/drone_targeting_research/data/real/drivingstereo
# Per https://drivingstereo-dataset.github.io/ — train_left.zip,
# train_right.zip, train_disparity.zip, plus the smaller test_*.zip
# Each is ~30-50 GB. Plan ~150 GB total.
for f in train_left train_right train_disparity test_left test_right test_disparity; do
    wget -c "https://drivingstereo-dataset.github.io/data/${f}.zip"
    unzip "${f}.zip"
done
```

### 7. Cityscapes (real semantic seg anchor)

```bash
mkdir -p /media/abrar/AbrarSSD/ROS/drone_targeting_research/data/real/cityscapes
cd /media/abrar/AbrarSSD/ROS/drone_targeting_research/data/real/cityscapes
# Cityscapes requires registration at https://www.cityscapes-dataset.com/
# Then:
pip install cityscapesscripts
csDownload -d . leftImg8bit_trainvaltest.zip
csDownload -d . gtFine_trainvaltest.zip
csDownload -d . rightImg8bit_trainvaltest.zip
unzip leftImg8bit_trainvaltest.zip gtFine_trainvaltest.zip rightImg8bit_trainvaltest.zip
```

### 8. UAVid (drone semantic seg)

```bash
mkdir -p /media/abrar/AbrarSSD/ROS/drone_targeting_research/data/real/uavid
cd /media/abrar/AbrarSSD/ROS/drone_targeting_research/data/real/uavid
# Per https://uavid.nl/  — request, receive download link.
```

### 9. Training recipe (4 GB-aware)

Per the user's global GPU rule (≥85% of 3.96 GB at chosen batch /
resolution):

```python
# Dummy sketch — adapt to actual model
import torch
total = torch.cuda.get_device_properties(0).total_memory  # ~4.26 GB observed
target = int(0.85 * total)                                 # ~3.62 GB peak

# Stereo at 384x768 with FoundationStereo's small variant + LoRA
# fits in ~3.5 GB at batch=2. Push to batch=3 if dry-run shows headroom.

# Segmentation: Segformer-B0 at 512x1024 fits ~3.7 GB at batch=4.
# B1/B2 will spill — stay on B0 unless using gradient checkpointing.
```

Concrete training plan:

1. Stereo: **freeze FoundationStereo backbone, attach a tiny disparity
   refinement head, train head only on TartanAir V2 + Virtual KITTI 2
   + DrivingStereo at 384×768, batch=2-3.** Eval on KITTI 2015.
2. Semantic seg: **Segformer-B0 from `nvidia/mit-b0`, train on
   Cityscapes + Synscapes + UrbanSyn + UAVid blended with class-balanced
   sampling, at 512×1024, batch=4.** Eval on Cityscapes val + UAVid val.
3. Joint refinement (optional, Phase 2): **shared encoder, two heads
   (depth + seg)** — multi-task per the SHIFT paper's findings on
   robustness. Will require gradient checkpointing on 4 GB.

### 10. Deployment validation in Gazebo

Use the Gazebo capture pipeline already in the project's
`drone_simulation.md` and `prebuilt_worlds.md` to:
- Capture stereo pairs from the kinematic camera rig in
  `clearpath_simulator/orchard.sdf`,
  `clearpath_simulator/office_construction.sdf`,
  `spaceros_gz_demos/mars.sdf`.
- Run the trained stereo + seg models on those captures.
- Compare against the Gazebo-produced ground-truth depth + seg labels.
- Publish a sim-validation report. **This is the only place Gazebo is
  in the perception loop**; it's not in the training loop.

## Open questions / risks

1. **TartanAir V2 file size is not officially published.** Plan
   ~30–50 GB per environment; budget conservatively. The pip toolkit
   (`tartanair`) supports per-environment + per-modality downloads, so
   you control disk consumption — see
   [tartanair.org](https://tartanair.org/) installation page.

2. **Synscapes and Mid-Air require access requests** (form / email).
   Allow 1–3 days for response before counting on these. **UrbanSyn,
   UrbanSyn, Virtual KITTI 2, DrivingStereo, GTA5-PfD, KITTI, and
   TartanAir are publicly downloadable without forms** — start with
   those.

3. **VRAM at training time on a 3050.** The recipe above is *believed*
   to fit, but **do a dry-run before committing to a long run** per
   the user's global GPU rule. FoundationStereo's full model is too
   big to train end-to-end at 4 GB; the *side-tuning / LoRA* path is
   the only viable training mode here. If training hits OOM, drop to
   gradient checkpointing first, batch size second, resolution third
   — in that order.

4. **Sim-to-real gap remains the main scientific risk.** Even with
   multi-source synthetic + real fine-tuning, the model *will* show
   degradation on a real drone deployment. The recommended path here
   minimizes that gap with current SOTA techniques but does not
   eliminate it. Plan to capture a small (100-image) real validation
   set with a real stereo camera at deployment time.

5. **No "drone target-following" training set exists** as a single
   published dataset — there are detection (VisDrone, UAVDT) and
   tracking (Stanford Drone, OTB-aerial) datasets but none that pair
   real stereo + semantic seg + tracking ground truth. The control /
   target-following phase (Phase 2 of the project per `CLAUDE.md`) will
   need its own data plan; this research is scoped to the perception
   phase.

6. **CARLA ROS 2 Jazzy bridge is community-maintained, not official.**
   If the user's hardware ever supports CARLA, expect to hand-port the
   ttgamage / AlexanderRex Humble bridge to Jazzy — see
   [carla issue #9551](https://github.com/carla-simulator/carla/issues/9551)
   for the FastDDS version-mismatch workaround.

7. **Cosys-AirSim's ROS 2 Jazzy story is undocumented.** The README
   and docs site mention "C++ ROS2 implementation" without naming a
   tested distro. Plausibly works on Jazzy (no ABI-breaking changes
   in standard messages), but you'd be the one verifying.

8. **License compliance** for distributed model artifacts: GTA5-PfD is
   tied to the GTA5 EULA and **cannot be redistributed** with model
   weights derived from it. Cityscapes and Synscapes are research-only.
   DrivingStereo, KITTI, KITTI-360, UAVid are research-only.
   UrbanSyn is **CC-BY-SA 4.0 (commercial use allowed)** — the most
   permissive on this list. If the project ever goes commercial, the
   licensing audit narrows the data choices significantly.

9. **Foundation-model hardware**: even *inference* with FoundationStereo
   on a 3050 may need fp16 + reduced max disparity (192 px → 96 px) to
   stay under 4 GB. Test this early; the `Fast-FoundationStereo` CVPR
   2026 follow-on is built specifically for this constraint
   ([repo](https://github.com/NVlabs/Fast-FoundationStereo)).

10. **The "interactive UE simulator" path is not closed forever** — it
    is closed *given current hardware*. If the user upgrades to ≥ 8 GB
    VRAM (e.g. RTX 4060/4070 mobile), **Cosys-AirSim becomes the
    strongest pick** for a drone-specific photoreal sim with native
    stereo + segmentation + Cityscapes-class labels — a much better fit
    than CARLA (which has no native multirotor) or Isaac Sim
    (which is overkill and still wants 8 GB minimum). Revisit at
    that hardware threshold.
