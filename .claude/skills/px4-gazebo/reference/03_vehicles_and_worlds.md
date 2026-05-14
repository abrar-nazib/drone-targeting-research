# 03 — Stock vehicles & worlds

Full catalogue of what's available out-of-the-box. For *adding* a new
vehicle / world, see
[04_custom_airframes_models_worlds.md](04_custom_airframes_models_worlds.md).
For tuning a stock x500 into an FPV airframe, see
[05_fpv_tuning.md](05_fpv_tuning.md).

## Stock SITL vehicles

Generated from the as-installed directory
`ROMFS/px4fmu_common/init.d-posix/airframes/` and
`Tools/simulation/gz/models/` at
`/media/abrar/AbrarSSD/ROS/PX4-Autopilot/`. The full airframes/
directory contains 65 init scripts — gazebo-classic legacy (1010-series),
JSBSim (3000s), SiH (10040s), and the modern Gazebo Harmonic block
(4001–4021, 8011, 71002). Only the `gz_*` IDs are relevant for SITL
on Harmonic.

| Make target | `SYS_AUTOSTART` | Init script | `PX4_SIM_MODEL` | Default world | Sensors / payload |
|---|---|---|---|---|---|
| `gz_x500` | **4001** | `4001_gz_x500` | `x500` | `default` | IMU, mag, baro, GPS (navsat). 4× rotors, 2.0 kg. **Baseline quadrotor.** |
| `gz_x500_depth` | 4002 | `4002_gz_x500_depth` (sources 4001) | `x500_depth` | `default` | x500 + `OakD-Lite`: 1920×1080 RGB camera (hfov 1.204) + 640×480 stereo depth (R_FLOAT32, hfov 1.274, near 0.2 / far 19.1, topic `depth_camera`). |
| `gz_x500_vision` | 4005 | `4005_gz_x500_vision` (sources 4001) | `x500_vision` | `default` | x500 + `gz-sim-odometry-publisher-system` plugin (publishes ground-truth odometry as a stand-in for VIO). |
| `gz_x500_mono_cam` | 4010 | `4010_gz_x500_mono_cam` (sources 4001) | `x500_mono_cam` | `default` | x500 + `mono_cam` (1280×960 RGB, hfov 1.74 ≈ 100°, far 3000 m). Forward-facing at `(.12, .03, .242)`. |
| `gz_x500_mono_cam_down` | 4014 | `4014_gz_x500_mono_cam_down` (sources 4001) | `x500_mono_cam_down` | `default` (or `aruco` for prec-land) | Downward `mono_cam`. Pairs with `aruco.sdf` for precision-landing tests. |
| `gz_x500_lidar_2d` | 4013 | `4013_gz_x500_lidar_2d` (sources 4001) | `x500_lidar_2d` | `default` | x500 + `lidar_2d_v2` (gpu_lidar, 0.1–30 m, 270° arc per docs). |
| `gz_x500_lidar_down` | 4016 | `4016_gz_x500_lidar_down` (sources 4001) | `x500_lidar_down` | `default` | x500 + downward 1-D rangefinder (`LW20`, 0.1–100 m). |
| `gz_x500_lidar_front` | 4017 | `4017_gz_x500_lidar_front` (sources 4001) | `x500_lidar_front` | `default` | x500 + forward `LW20` 1-D lidar (`gpu_lidar`, 0.1–100 m, 1×1 ray). For collision prevention. |
| `gz_x500_gimbal` | 4019 | `4019_gz_x500_gimbal` (sources 4001 + sets `MNT_*`) | `x500_gimbal` | `default` | x500 + `gimbal` model with cgo3-style 3-axis gimbal; 115° H × 50.7° V FOV. |
| `gz_x500_flow` | 4021 | `4021_gz_x500_flow` (sources 4001, disables GPS) | `x500_flow` | `default` | Downward optical-flow + distance sensor, GPS off (`SYS_HAS_GPS 0`, `EKF2_GPS_CTRL 0`). |
| `gz_advanced_plane` | 4008 | `4008_gz_advanced_plane` | `advanced_plane` | `default` | Fixed-wing using `gz-sim-advanced-lift-drag-system` (better aero than the stock plane). |
| `gz_rc_cessna` | 4003 | `4003_gz_rc_cessna` | `rc_cessna` | `default` | RC Cessna fixed-wing, 6 control surfaces, throttle on EC channel 1. |
| `gz_standard_vtol` | 4004 | `4004_gz_standard_vtol` | `standard_vtol` | `default` | Quadplane VTOL. |
| `gz_quadtailsitter` | 4018 | `4018_gz_quadtailsitter` | `quadtailsitter` | `default` | Quad-motor tailsitter VTOL. |
| `gz_tiltrotor` | 4020 | `4020_gz_tiltrotor` | `tiltrotor` | `default` | Tiltrotor VTOL — front 2 motors tilt during transition. |
| `gz_r1_rover` | 4009 | `4009_gz_r1_rover` | `r1_rover` | **`rover`** | Aion R1 differential-drive rover (`rc.rover_differential_defaults`). |
| `gz_r1_rover_mecanum` | 4015 | `4015_gz_r1_rover_mecanum` | `r1_rover_mecanum` | **`rover`** | Same chassis with mecanum kinematics (`rc.rover_mecanum_defaults`). |
| `gz_rover_ackermann` | 4012 | `4012_gz_rover_ackermann` | `rover_ackermann` | **`rover`** | **Ackermann-steering rover** (`rc.rover_ackermann_defaults`, wheel base 0.321 m, max steer 0.524 rad). **Best fit for the project's "car to land on" scenario** — has realistic car kinematics, can be driven over ROS 2 by bridging `cmd_vel`. |
| `gz_lawnmower` | 4011 | `4011_gz_lawnmower` | `lawnmower` | `default` | Differential-drive mower; 0.9 m wheel track, 8 m/s top speed, multi-servo demo. |
| `gz_omnicopter` | 8011 | `8011_gz_omnicopter` | `omnicopter` | `default` | 8-rotor fully-actuated platform. |
| `gz_px4vision` | 4006 | `4006_gz_px4vision` | `px4vision` | `default` | NXP PX4Vision dev kit airframe. |
| `gz_spacecraft_2d` | 71002 | `71002_gz_spacecraft_2d` | `spacecraft_2d` | `frictionless` | 2-D thruster spacecraft. |

(Sources: <https://docs.px4.io/main/en/sim_gazebo_gz/vehicles.html>;
on-disk init.d-posix/airframes/ listing;
`Tools/simulation/gz/models/{x500_depth,x500_mono_cam,x500_lidar_front,x500_vision,x500_gimbal}/model.sdf`.)

### Picking a vehicle for the project

For the drone-targeting research project (FPV-style multicopter that
follows + lands on a moving car):

- **Drone**: start from `gz_x500` (baseline) or `gz_x500_depth` (if
  you want stereo depth ground truth from the OakD-Lite). Retune to FPV
  dynamics per [05_fpv_tuning.md](05_fpv_tuning.md). Add the project's
  stereo + segmentation rig as additional sensors per
  [04_custom_airframes_models_worlds.md](04_custom_airframes_models_worlds.md).
- **Target car**: use `rover_ackermann` (model name) but **without a
  PX4 instance** — the rover doesn't need its own autopilot. Drive it
  with `gz-sim-trajectory-follower-system` (declarative path) or by
  publishing `cmd_vel` over `ros_gz_bridge`. See
  [04_custom_airframes_models_worlds.md](04_custom_airframes_models_worlds.md)
  for the spawning patterns.

## Stock SITL worlds

From `Tools/simulation/gz/worlds/`:

| File | World name | Contents | Best for |
|---|---|---|---|
| `default.sdf` | `default` | Grey ground plane (500×500), ENU at lat 47.397971, lon 8.546164 (Zürich), one directional sun light. No obstacles. | Baseline / smoke tests. |
| `aruco.sdf` | `aruco` | `default` + an ArUco marker model at known pose. | Precision-landing tests; pairs with `gz_x500_mono_cam_down`. |
| `baylands.sdf` | `baylands` | `<include>` of `OpenRobotics/baylands` (large coastal park) + `Coast Water`. Lat 37.412, lon −121.999 (Sunnyvale). Sky with clouds enabled. | **Largest stock outdoor world.** Best baseline for car-following / landing. First run requires Fuel access for the include. |
| `forest.sdf` | `forest` | Densely populated `<include>`s of Pine/Oak trees + grasspatches (≥ 100 includes). Heavy on draw calls. | Forest navigation. Heavy for 4 GB iGPU. |
| `frictionless.sdf` | `frictionless` | Special low-friction surface for spacecraft / 2-D dynamics. | `gz_spacecraft_2d` only. |
| `lawn.sdf` | `lawn` | Green flat plane (400×400) with sky / clouds. PX4 docs flag it as low FPS. | Aesthetic ground for tests. |
| `moving_platform.sdf` | `moving_platform` | `default` + `flat_platform` (5×5 m platform at z=2 m) driven by `libMovingPlatformController.so`. | Ship-deck / **moving-target landing prototypes**. |
| `rover.sdf` | `rover` | Grid-marked ground tuned for rover physics. | Default world for `gz_r1_rover` / `gz_rover_ackermann`. |
| `walls.sdf` | `walls` | Obstacle walls. | Collision-prevention testing (pairs with `x500_lidar_*`). |
| `windy.sdf` | `windy` | `default` + a `WindEffects` plugin block with non-zero wind. | Disturbance-rejection testing. |

(Sources: <https://docs.px4.io/main/en/sim_gazebo_gz/worlds.html>;
on-disk SDF inspection.)

### Picking a world for "drone follows car, lands on car"

In priority order:

1. **`baylands.sdf`** — large (the `park` model is hundreds of metres
   across), real outdoor look, navsat origin set in California. Best
   stock outdoor world for the use case. **Recommended starting point.**
2. **`moving_platform.sdf`** — already has a programmed-motion target.
   Quick prototyping shortcut: replace the `flat_platform` model with a
   car model and you have a moving landing target without writing any
   trajectory code. Useful for the *first* end-to-end landing test
   before the full car simulation.
3. **`default.sdf` + `<include>` of a car + a trajectory follower** —
   if visuals don't matter, this is the lowest-overhead path. Add
   Fuel-cached cars with a `gz-sim-trajectory-follower-system` plugin.
   See
   [04_custom_airframes_models_worlds.md](04_custom_airframes_models_worlds.md)
   for the SDF snippets.
4. **Project's existing labeled worlds** —
   `orchard_labeled.sdf` and `construction_labeled.sdf` from
   `ros2_ws/src/drone_sim_bringup/worlds/`. These were built for the
   perception-capture phase; the orchard (48×38 m) is large enough for
   a car loop + landing run if you need photo-textured ground for
   downstream perception.

### Critical: world SDFs do NOT embed system plugins

The stock world SDFs do **not** contain `<plugin>` blocks for
`gz-sim-physics-system`, `gz-sim-sensors-system`, etc. Those are
loaded server-side via `Tools/simulation/gz/server.config`. See
[01_architecture.md](01_architecture.md#toolssimulationgzserverconfig--the-system-plugins-file)
for the full XML.

**Implication**: if you launch `gz sim` directly *without*
`--server-config`, sensors silently never publish. Always launch
through `make px4_sitl gz_*` or pass the server config explicitly.

## Sources

- PX4 vehicles list:
  <https://docs.px4.io/main/en/sim_gazebo_gz/vehicles.html>
- PX4 worlds list:
  <https://docs.px4.io/main/en/sim_gazebo_gz/worlds.html>
- Airframe ID conventions:
  <https://docs.px4.io/main/en/dev_airframes/airframe_reference.html>
- On-disk source listings (this PX4 checkout):
  - `ROMFS/px4fmu_common/init.d-posix/airframes/`
  - `Tools/simulation/gz/models/`
  - `Tools/simulation/gz/worlds/`
