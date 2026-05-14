# 01 — Architecture & lockstep

How PX4 SITL + Gazebo Harmonic actually fit together. Read this before
[02_launching_and_console.md](02_launching_and_console.md) — the launch
mechanics make sense once the process model is clear.

## Process model

PX4 SITL with Gazebo Harmonic runs as **two independent OS processes**
that communicate over **gz-transport** (NOT MAVLink, NOT ROS):

1. **PX4 SITL process** — `build/px4_sitl_default/bin/px4`. The full
   PX4 flight stack compiled for POSIX. Same firmware that runs on a
   Pixhawk; the HAL is substituted for a Linux scheduler and the in-tree
   **`gz_bridge`** module is loaded in place of a real sensor / IO
   stack. The startup file
   `ROMFS/px4fmu_common/init.d-posix/rcS` is the entry script;
   airframe-specific scripts live alongside it as numbered files (e.g.
   `4001_gz_x500`, `4002_gz_x500_depth`, `10000_airplane`) and are
   selected by `PX4_SYS_AUTOSTART`. Modules are exposed as
   `px4-<module>` symlinks plus an `alias <module>=px4-<module>` shim
   from `bin/px4-alias.sh`, which is what lets you type `commander arm`
   at the `pxh>` prompt instead of `px4-commander arm`.
   (Source: <https://docs.px4.io/main/en/concept/system_startup.html>)

2. **Gazebo simulator process** — `gz sim` (Harmonic uses `gz-sim8`).
   Runs the world SDF, physics (DART by default), rendering (OGRE 2 by
   default), and exposes sensors (IMU, GPS, baro, mag, depth/RGB
   cameras) plus joint / thrust effectors over **gz-transport** topics.

The `make px4_sitl gz_x500` invocation starts both processes — PX4
forks `gz sim` as a child (unless `PX4_GZ_STANDALONE=1`).

## `gz_bridge`: the in-tree PX4 module (NOT `ros_gz_bridge`)

The bridge between the two processes is the **`gz_bridge` PX4 module**
(`src/modules/simulation/gz_bridge`). This is **NOT** the same as
`ros_gz_bridge`:

| Bridge | Lives in | What it bridges |
|---|---|---|
| `gz_bridge` (this skill's subject) | PX4-Autopilot tree, compiled into the `px4` binary | gz-transport topics ↔ PX4 uORB topics |
| `ros_gz_bridge` (the ROS package) | `ros-jazzy-ros-gz-bridge` apt package | gz-transport topics ↔ ROS 2 DDS topics |

They sit on opposite sides of PX4. `ros_gz_bridge` is irrelevant to
PX4 SITL itself; if you want ROS 2 ↔ PX4 you go through
[**uXRCE-DDS**](06_ros2_uxrce_dds.md), not `ros_gz_bridge`.

`gz_bridge` is a PX4 work-queue module with sub-components for
different I/O classes:

- **`GZBridge`** — sensors + IMU sync (the bulk of the work).
- **`GZGimbal`** — gimbal control.
- **`GZMixingInterfaceEsc`** — multicopter / advanced-plane motor outputs.
- **`GZMixingInterfaceServo`** — fixed-wing / VTOL servo outputs.
- **`GZMixingInterfaceWheel`** — rover wheel drives.

(Source:
<https://github.com/PX4/PX4-Autopilot/tree/main/src/modules/simulation/gz_bridge>)

## Sensor flow (Gazebo → PX4)

```
Gazebo IMU sensor   → gz topic /world/<world>/model/<model>/link/base_link/sensor/imu_sensor/imu
                    → gz_bridge GZBridge subscriber
                    → uORB topic sensor_combined / sensor_accel / sensor_gyro
GPS                 → /world/.../navsat_sensor/navsat       → vehicle_gps_position
Magnetometer        → /world/.../magnetometer_sensor/magnetometer → sensor_mag
Barometer           → /world/.../air_pressure_sensor/air_pressure → sensor_baro
```

These uORB topics drive **EKF2** (the default state estimator), which
produces `vehicle_local_position`, `vehicle_global_position`, and
`estimator_status`.
(Source: <https://docs.px4.io/main/en/middleware/uorb.html>)

**The sensor names matter.** `gz_bridge` hardcodes the topic paths
expecting sensors named `imu_sensor`, `magnetometer_sensor`,
`air_pressure_sensor`, `navsat_sensor`, all on a link called
`base_link`. A custom model that diverges from these names without
patching `GZBridge.cpp` will leave PX4 in "sensor missing" preflight
failure forever. See
[04_custom_airframes_models_worlds.md](04_custom_airframes_models_worlds.md)
for the model.sdf naming requirements.

## Actuator flow (PX4 → Gazebo)

```
control_allocator → actuator_motors / actuator_servos uORB
                  → gz_bridge mixing interface (ESC / Servo / Wheel)
                  → gz topic /<model>/command/motor_speed (or analogous joint cmd)
                  → Gazebo physics applies thrust / joint torque
```

Routing of which `actuator_motors` channel maps to which gz topic is
controlled by airframe-side params: `SIM_GZ_EC_FUNC1..N` (ESC channels),
`SIM_GZ_EC_MIN1..N` and `SIM_GZ_EC_MAX1..N` (PWM range), `SIM_GZ_SV_FUNC*`
(servos). These are normally set in the airframe init script — see the
example in
[04_custom_airframes_models_worlds.md](04_custom_airframes_models_worlds.md).

## Lockstep simulation

Both processes run in **lockstep**: gz-sim publishes a sensor frame,
PX4 consumes it, runs one scheduler tick, emits actuator commands, and
the simulator waits for those before stepping physics again. This is
what:

- Lets `PX4_SIM_SPEED_FACTOR` exceed 1.0 — wall clock is decoupled from
  the simulated clock.
- Makes the simulation deterministic across runs.
- Means the simulator visibly stalls if PX4 is paused under a debugger.

Official line: the simulators "are locked to run at the same speed,
and therefore can react appropriately to sensor and actuator
messages." (Source: <https://docs.px4.io/main/en/simulation/>)

### Lockstep starvation — the failure mode you'll actually hit

When lockstep breaks, the symptoms are unambiguous and recurring:

```
WARN  [px4]               Interrupted system call
ERROR [vehicle_imu] 0 - gyro 1310988 timestamp error timestamp_sample: ...
ERROR [vehicle_imu] 0 - accel 1310988 timestamp error timestamp_sample: ...
WARN  [health_and_arming_checks] Preflight Fail: ekf2 missing data
ERROR [tone_alarm] open /dev/tty failed
ERROR [mc_pos_control] Vertical position estimate timeout
```

`estimator_status.timeout_flags != 0`;
`vehicle_local_position.xy_valid == false`; `commander arm` returns
"preflight check failed" with `local_position_invalid` set in
`failsafe_flags`.

**On this project's RTX 3050 4 GB iGPU**, the cause is the OGRE 2
renderer starving the physics step. **This is expected — not a bug**.
Fixes, in priority order:

1. **`HEADLESS=1`** — skip the OGRE GUI client entirely. This is the
   default mode for this project. Headless still runs the gz-sim server
   (with sensor rendering, since `gz-sim-sensors-system` is server-side)
   so cameras still work.
2. **`PX4_GZ_SIM_RENDER_ENGINE=ogre`** — fall back from OGRE 2 to OGRE 1
   if you need the GUI. Older renderer, lower demands. Used on weak
   iGPUs and VMs.
3. **Build with lockstep disabled** — the heavy hammer. Set
   `ENABLE_LOCKSTEP_SCHEDULER=no` in `boards/px4/sitl/default.px4board`
   (or via `-DENABLE_LOCKSTEP_SCHEDULER=no`), `make distclean`, rebuild.
   PX4 then runs against the standard POSIX scheduler in real time.
   Trade-off: you lose accelerated time and bit-exact reproducibility.

There is no runtime toggle for lockstep — it's a compile-time scheduler
choice. The official docs page
`simulation/simulation-debugging.html` returns 404 on current docs;
the canonical knowledge lives in the PX4 source and the discuss forum.

See [08_troubleshooting.md](08_troubleshooting.md) for the full
troubleshooting recipe.

## `Tools/simulation/gz/server.config` — the system-plugins file

The world SDFs in `Tools/simulation/gz/worlds/` do **not** embed
`<plugin>` blocks for `gz-sim-physics-system`, `gz-sim-sensors-system`,
etc. Those are loaded server-side via
`Tools/simulation/gz/server.config`:

```xml
<server_config>
  <plugins>
    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
    <plugin filename="gz-sim-contact-system" name="gz::sim::systems::Contact"/>
    <plugin filename="gz-sim-imu-system" name="gz::sim::systems::Imu"/>
    <plugin filename="gz-sim-air-pressure-system" name="gz::sim::systems::AirPressure"/>
    <plugin filename="gz-sim-air-speed-system" name="gz::sim::systems::AirSpeed"/>
    <plugin filename="gz-sim-apply-link-wrench-system" name="gz::sim::systems::ApplyLinkWrench"/>
    <plugin filename="gz-sim-navsat-system" name="gz::sim::systems::NavSat"/>
    <plugin filename="gz-sim-magnetometer-system" name="gz::sim::systems::Magnetometer"/>
    <plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors">
      <render_engine>ogre2</render_engine>
    </plugin>
    <plugin filename="libOpticalFlowSystem.so" name="custom::OpticalFlowSystem"/>
    <plugin filename="libGstCameraSystem.so" name="custom::GstCameraSystem"/>
  </plugins>
</server_config>
```

**Implication:** if you launch `gz sim` directly *without*
`--server-config Tools/simulation/gz/server.config`, your sensors
silently never publish (no `gz-sim-sensors-system`), the IMU /baro /mag
/navsat plugins are absent, and PX4 sits waiting on
`/world/.../imu_sensor/imu` forever.

`make px4_sitl gz_*` handles this for you. If you launch the world by
hand (e.g. for the multi-vehicle pattern), pass the server config.

## The build-time gotcha

Building PX4 SITL with the `gz_*` targets requires that **CMake can
find gz-transport13 and gz-sim8**. Without them the build fails at
configure time:

```
CMake Error at src/modules/simulation/gz_bridge/CMakeLists.txt:
  Gazebo simulation dependencies not found!
```

The fix is two env vars before invoking `make`:

```bash
source /opt/ros/jazzy/setup.bash      # puts gz-transport / gz-sim on CMake's prefix path
export GZ_DISTRO=harmonic             # tells PX4 which Gazebo distribution to look for
make px4_sitl gz_x500
```

If a stale CMake cache from a prior failed build is around, refresh it:

```bash
cd build/px4_sitl_default
cmake .                                # re-detect with the new env
cd -
make px4_sitl gz_x500
```

This is recorded in the project CLAUDE.md as a "build gotcha learned
the hard way."

## Sources

- PX4 system startup, `rcS`, `init.d-posix/`, `PX4_SYS_AUTOSTART`,
  `px4-alias.sh`: <https://docs.px4.io/main/en/concept/system_startup.html>
- PX4 simulation overview, lockstep concept:
  <https://docs.px4.io/main/en/simulation/>
- PX4 sim Gazebo overview, env vars, render engine fallback:
  <https://docs.px4.io/main/en/sim_gazebo_gz/>
- PX4 simulation modules (`gz_bridge` listing):
  <https://github.com/PX4/PX4-Autopilot/tree/main/src/modules/simulation/gz_bridge>
- uORB middleware:
  <https://docs.px4.io/main/en/middleware/uorb.html>
