---
name: px4-gazebo
description: Comprehensive PX4-Autopilot SITL + Gazebo Harmonic + ROS 2 Jazzy reference (architecture, lockstep, gz_bridge, every gz_* make target, every stock world, custom airframes/models/worlds, FPV tuning, uXRCE-DDS topic catalog with QoS, offboard takeoff template, full FailsafeFlags decoder, EKF2 "missing data" diagnosis tree, lockstep-starvation recipe). Use whenever the user is working with PX4 SITL on this machine — `make px4_sitl gz_*`, the `pxh>` console (`commander`, `listener`, `param`), x500 / x500_depth / x500_vision / x500_lidar_* airframes, the PX4 `gz_bridge` module (NOT `ros_gz_bridge`), `MicroXRCEAgent`, `/fmu/in/*` and `/fmu/out/*` topics, `px4_msgs` / `px4_ros_com`, offboard control, NED/FRD vs ENU/FLU frame conversion, `failsafe_flags`, "Arming denied: Resolve system health failures first", `Interrupted system call`, `vehicle_imu timestamp error`, ekf2 missing data, or building a landing controller for a moving target.
---

# PX4 SITL + Gazebo Harmonic + ROS 2 Jazzy — comprehensive reference

This skill is an opinionated index over the PX4 v1.16 + Gazebo Harmonic
+ ROS 2 Jazzy stack as installed on this machine
(`/media/abrar/AbrarSSD/ROS/PX4-Autopilot/`,
`/opt/ros/jazzy/`, Gazebo Harmonic vendored under
`/opt/ros/jazzy/opt/gz_*`). The deep content is split into 8 reference
files under `reference/`. **Read the relevant reference file before
reaching for `WebFetch` against `docs.px4.io`** — the summaries already
include the commands, env vars, parameter names, topic names, and
gotchas you would otherwise re-derive.

## How to use this skill

1. Find the topic in the index below.
2. `Read` the corresponding `reference/NN_*.md` file (each is dense and
   self-contained for that topic).
3. Only `WebFetch` the canonical URL when the reference file flags
   "see canonical doc for …" or when you need the exhaustive
   parameter-by-parameter reference.
4. For ROS 2 wiring questions, the [`ros`](../ros/SKILL.md) skill is
   the companion reference. This skill assumes you already know
   `ros_gz_bridge` exists; what's covered here is PX4's *separate*
   in-tree `gz_bridge` module (different thing, same word).

## Project-locked defaults

- **PX4 version**: `v1.16.0` (tag), built at
  `/media/abrar/AbrarSSD/ROS/PX4-Autopilot/build/px4_sitl_default/`.
- **Simulator**: Gazebo Harmonic (`gz-sim8`, `gz-transport13`). **Not**
  Gazebo Classic, not Garden. The `make px4_sitl gz_*` targets all use
  Harmonic on this machine.
- **ROS 2 distribution**: Jazzy Jalisco at `/opt/ros/jazzy/`. Always
  `source /opt/ros/jazzy/setup.bash` AND `export GZ_DISTRO=harmonic`
  before invoking `make` against PX4 — without these the `gz_bridge`
  module fails to find gz-transport / gz-sim. See
  [reference/01_architecture.md](reference/01_architecture.md) and
  the project CLAUDE.md.
- **Hardware ceiling**: RTX 3050 Mobile (4 GB VRAM), i5-11300H. **Always
  run with `HEADLESS=1`** for SITL; the OGRE 2 GUI starves lockstep on
  this iGPU and the symptoms are unmistakable (`Interrupted system
  call`, `vehicle_imu timestamp error`, `ekf2 missing data`). See
  [reference/08_troubleshooting.md](reference/08_troubleshooting.md).
- **uXRCE-DDS over MAVROS**: new code uses `MicroXRCEAgent` (port 8888) +
  `/fmu/in/*` `/fmu/out/*` topics with `px4_msgs`. MAVROS is install-
  able but legacy.
- **Frames**: PX4 is **NED + FRD**, ROS 2 is **ENU + FLU**. Z is *down*
  in PX4. `position = {0, 0, -5}` in a `TrajectorySetpoint` means
  5 m **above** the EKF origin. See
  [reference/06_ros2_uxrce_dds.md](reference/06_ros2_uxrce_dds.md).

## Quick-start launch (this project)

```bash
# In every fresh terminal:
source /opt/ros/jazzy/setup.bash
export GZ_DISTRO=harmonic
cd /media/abrar/AbrarSSD/ROS/PX4-Autopilot

# Default x500 in the empty world, headless (mandatory on this hardware):
HEADLESS=1 make px4_sitl gz_x500
```

When `pxh>` appears, **wait 10–15 seconds** for EKF2 to converge before
arming. Then:

```
pxh> commander check                     # see what's blocking
pxh> listener failsafe_flags             # raw blocker bits
pxh> commander takeoff                   # auto-takeoff
pxh> commander land
pxh> shutdown
```

## Reference index

| # | File | Coverage |
|---|------|----------|
| 01 | [Architecture & lockstep](reference/01_architecture.md) | Process model (PX4 binary + gz sim), `gz_bridge` PX4 module vs `ros_gz_bridge` ROS package, sensor flow Gazebo→PX4 (IMU/GPS/baro/mag), actuator flow PX4→Gazebo, **lockstep simulation** (what it is, how it breaks, build-time disable), the `Tools/simulation/gz/server.config` system-plugins file. |
| 02 | [Launching & the pxh> console](reference/02_launching_and_console.md) | All `make px4_sitl gz_*` targets + `SYS_AUTOSTART` IDs; every env var (`HEADLESS`, `PX4_GZ_WORLD`, `PX4_GZ_MODEL_POSE`, `PX4_GZ_STANDALONE`, `PX4_GZ_SIM_RENDER_ENGINE`, `PX4_HOME_LAT/LON/ALT`, `GZ_SIM_RESOURCE_PATH`); standalone-Gazebo + multi-vehicle pattern; full `pxh>` command list (`commander`, `listener`, `param`, `uorb top`, `dmesg`). |
| 03 | [Stock vehicles & worlds](reference/03_vehicles_and_worlds.md) | Full table of every `gz_*` make target on disk (x500 + every sensor variant, advanced_plane, rc_cessna, all VTOLs, all rovers, omnicopter, lawnmower, spacecraft); full table of every world SDF (default/aruco/baylands/forest/lawn/moving_platform/rover/walls/windy/frictionless); recommendation for the project's "drone follows car, lands on car" use case. |
| 04 | [Custom airframes, models, worlds](reference/04_custom_airframes_models_worlds.md) | Adding a new `init.d-posix/airframes/<id>_<name>` script; the three model.sdf composition patterns (base + payload merge include, base + motor plugins, base_link with the four canonical sensors); **the hardcoded sensor names** `gz_bridge` requires (`imu_sensor`, `magnetometer_sensor`, `air_pressure_sensor`, `navsat_sensor` on `base_link`); adding stereo / depth / segmentation cameras; world SDF requirements + `<spherical_coordinates>` GPS origin; spawning extra entities (target vehicles) via `<include>`, `gz service /world/<name>/create`, and the `gz-sim-trajectory-follower-system` plugin. |
| 05 | [FPV tuning (TWR, rate loop, Acro)](reference/05_fpv_tuning.md) | Increasing TWR via `<motorConstant>` and `<maxRotVelocity>` in the model SDF (and matching `MPC_THR_HOVER`); the multicopter rate-controller PID parameter family (`MC_ROLLRATE_*`, `MC_PITCHRATE_*`, `MC_YAWRATE_*`); attitude limits; gyro filtering (`IMU_GYRO_CUTOFF`, `IMU_GYRO_NF*`, `IMU_DGYRO_CUTOFF`); Acro mode (`MC_ACRO_*` expo curves); position-mode behaviour for an FPV airframe (`MPC_MAN_TILT_MAX`, `MPC_XY_VEL_MAX`, `MPC_ACC_HOR_MAX`). |
| 06 | [ROS 2 ↔ PX4 via uXRCE-DDS + offboard](reference/06_ros2_uxrce_dds.md) | uXRCE-DDS architecture, `MicroXRCEAgent` source build (Jazzy pin = v2.4.3), `px4_msgs` / `px4_ros_com` version pinning, NED↔ENU and FRD↔FLU frame conversion, the full `/fmu/in/*` and `/fmu/out/*` topic catalogue, **the offboard takeoff sequence** (10× pre-streamed setpoints → DO_SET_MODE → ARM_DISARM), the `rmw_qos_profile_sensor_data` QoS recipe (Best Effort + Volatile + KeepLast(5)), MAVLink fallback (QGC) install. |
| 07 | [Parameters & preflight checks](reference/07_parameters_and_preflight.md) | The `pxh>` `param` subsystem (`show`, `set`, `save`, `load`, `compare`, `touch`, `reset`); SITL-relevant params (`COM_RCL_EXCEPT`, `COM_ARM_WO_GPS`, `COM_DISARM_PRFLT`, `NAV_DLL_ACT`, `NAV_RCL_ACT`, `COM_ARM_MAG_STR`, `EKF2_AID_MASK`, `EKF2_HGT_REF`, `EKF2_MAG_TYPE`, `SIM_GZ_EN`, `UXRCE_DDS_PRT`); the **field-by-field FailsafeFlags decoder** (every `mode_req_*`, every `*_invalid`, every link-loss flag, the FD failure-detector flags, geofence/wind/flight-time, what each one means and how to fix it for SITL). |
| 08 | [Troubleshooting](reference/08_troubleshooting.md) | The **lockstep starvation symptom-set** (`Interrupted system call`, `vehicle_imu timestamp error`, `ekf2 missing data`) and its fixes (HEADLESS=1, `PX4_GZ_SIM_RENDER_ENGINE=ogre`, build with `ENABLE_LOCKSTEP_SCHEDULER=no`); the **EKF2 "missing data" diagnosis tree** (8-step ladder from `listener sensor_combined` to `EKF2_AID_MASK`); the **"won't arm" recipe** with the standard SITL `param set` cleanup; the build error "Gazebo simulation dependencies not found"; texture not loading from `model://` URI; orphan `px4` process holding port 8888. |

## Working agreements

- **Always source ROS + set GZ_DISTRO before running `make`.** Without it
  the gz_bridge module fails to compile. See
  [reference/01_architecture.md](reference/01_architecture.md).
- **Always launch with `HEADLESS=1` on this hardware.** The GUI is a
  trap on the 4 GB iGPU. See
  [reference/08_troubleshooting.md](reference/08_troubleshooting.md).
- **`commander check` does not print causes**. The actual blocker is in
  `failsafe_flags` — `listener failsafe_flags` from `pxh>` is the source
  of truth. See
  [reference/07_parameters_and_preflight.md](reference/07_parameters_and_preflight.md).
- **PX4's `gz_bridge` module ≠ `ros_gz_bridge` ROS package.** The first
  is a uORB-side PX4 module (no ROS involvement); the second is the
  ROS 2 ↔ gz-transport bridge. They sit on opposite sides of PX4. See
  [reference/01_architecture.md](reference/01_architecture.md).
- **Default to uXRCE-DDS for new code, not MAVROS.** MAVROS is the ROS 1
  legacy path; uXRCE-DDS is the ROS 2 native bridge that exposes uORB
  directly. See
  [reference/06_ros2_uxrce_dds.md](reference/06_ros2_uxrce_dds.md).
- **px4_msgs branch must match PX4 firmware version**, otherwise topics
  silently mismatch. v1.16 → `release/1.16` branch. See
  [reference/06_ros2_uxrce_dds.md](reference/06_ros2_uxrce_dds.md).
- **For "drone follows car, lands on car"**, the recommended starting
  world is `baylands.sdf` (large outdoor area) or `default.sdf` +
  `<include>` of a Fuel pickup truck with a
  `gz-sim-trajectory-follower-system` plugin. See
  [reference/03_vehicles_and_worlds.md](reference/03_vehicles_and_worlds.md)
  and
  [reference/04_custom_airframes_models_worlds.md](reference/04_custom_airframes_models_worlds.md).

## Canonical upstream sources

The reference files cite primary sources inline, but the recurring URLs:

- PX4 Gazebo simulator: <https://docs.px4.io/main/en/sim_gazebo_gz/>
- PX4 ROS 2 user guide: <https://docs.px4.io/main/en/ros2/user_guide.html>
- PX4 uXRCE-DDS middleware: <https://docs.px4.io/main/en/middleware/uxrce_dds.html>
- PX4 offboard control example: <https://docs.px4.io/main/en/ros2/offboard_control.html>
- PX4 parameter reference: <https://docs.px4.io/main/en/advanced_config/parameter_reference.html>
- PX4 EKF2 tuning: <https://docs.px4.io/main/en/advanced_config/tuning_the_ecl_ekf.html>
- FailsafeFlags message: <https://docs.px4.io/main/en/msg_docs/FailsafeFlags.html>
- PX4-Autopilot source: <https://github.com/PX4/PX4-Autopilot/tree/main>
- px4_msgs: <https://github.com/PX4/px4_msgs>
- px4_ros_com: <https://github.com/PX4/px4_ros_com>
- Micro-XRCE-DDS-Agent: <https://github.com/eProsima/Micro-XRCE-DDS-Agent>
- Gazebo Harmonic plugin API: <https://gazebosim.org/api/sim/8/>
