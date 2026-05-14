# 04 — Custom airframes, models, worlds

How to extend the stock catalogue with your own vehicle / sensor /
world configurations. The "drone with a custom stereo + segmentation
rig flying in a custom outdoor world with a moving car" scenario this
project needs lives entirely in this file.

Pairs with [03_vehicles_and_worlds.md](03_vehicles_and_worlds.md)
(what's stock) and
[05_fpv_tuning.md](05_fpv_tuning.md) (FPV-specific param sets).

## Adding a new airframe

Per <https://docs.px4.io/main/en/dev_airframes/adding_a_new_frame.html>:

1. **Pick an unused `SYS_AUTOSTART` ID.** For PX4 SITL Harmonic, the
   convention is the 40xx block for new gz airframes. Avoid collisions
   with the table in
   [03_vehicles_and_worlds.md](03_vehicles_and_worlds.md). The ID
   becomes the `SYS_AUTOSTART` parameter value AND the leading number of
   the script filename.

2. **Create the init script** at
   `ROMFS/px4fmu_common/init.d-posix/airframes/<ID>_gz_<name>`. Minimum
   skeleton mirroring `4001_gz_x500`:

   ```sh
   #!/bin/sh
   #
   # @name Gazebo x500 FPV
   #
   # @type Quadrotor
   #

   . ${R}etc/init.d/rc.mc_defaults

   PX4_SIMULATOR=${PX4_SIMULATOR:=gz}
   PX4_GZ_WORLD=${PX4_GZ_WORLD:=default}
   PX4_SIM_MODEL=${PX4_SIM_MODEL:=x500_fpv}

   param set-default SIM_GZ_EN 1

   # control allocator (motor geometry)
   param set-default CA_AIRFRAME 0
   param set-default CA_ROTOR_COUNT 4
   param set-default CA_ROTOR0_PX 0.13
   param set-default CA_ROTOR0_PY 0.22
   param set-default CA_ROTOR0_KM 0.05
   # ... rotors 1..3 ...

   # gz_bridge actuator routing (101..104 = motor 1..4)
   param set-default SIM_GZ_EC_FUNC1 101
   param set-default SIM_GZ_EC_FUNC2 102
   param set-default SIM_GZ_EC_FUNC3 103
   param set-default SIM_GZ_EC_FUNC4 104
   param set-default SIM_GZ_EC_MIN1 150
   param set-default SIM_GZ_EC_MAX1 1000
   # ... etc ...

   param set-default MPC_THR_HOVER 0.30   # FPV TWR ~6: hover near 1/6 throttle
   ```

   - `${R}` expands to `etc/`.
   - `. ${R}etc/...` lines source defaults.
   - **`param set-default`** assigns only if user / QGC has not
     overridden; **`param set`** is unconditional. Always prefer
     `set-default` in airframe scripts so user tunes survive.
   - To inherit from another airframe (very common for variants),
     source it: `. ${R}etc/init.d-posix/airframes/4001_gz_x500` —
     see `4002_gz_x500_depth` which is two real lines.

3. **Register in CMakeLists.txt** at
   `ROMFS/px4fmu_common/init.d-posix/airframes/CMakeLists.txt`. Add
   the new filename to the `px4_add_romfs_files(...)` call. **Without
   this the script is not included in the ROMFS image** and the new
   `gz_<name>` make target won't exist.

4. **Rebuild ROMFS / SITL.** A fresh `make px4_sitl gz_<name>` (after
   `make clean` if it's the first build with the new file) regenerates
   ROMFS and registers the new make target.

5. **Select at runtime.** Either `make px4_sitl gz_<name>`, or for
   headless / scripted launches:

   ```bash
   PX4_SYS_AUTOSTART=4099 \
   PX4_SIM_MODEL=x500_fpv \
   PX4_GZ_MODEL_POSE="0,0,0,0,0,0" \
   ./build/px4_sitl_default/bin/px4
   ```

FPV-relevant params to drop into this script are listed in
[05_fpv_tuning.md](05_fpv_tuning.md).

## Adding a new SDF model

### Directory layout

```
Tools/simulation/gz/models/<model_name>/
├── model.config        # tiny manifest pointing at model.sdf
├── model.sdf           # the SDF
└── meshes/             # optional .dae/.stl/textures
```

A minimal `model.config` (from `moving_platform/model.config`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<model>
  <sdf version="1.9">model.sdf</sdf>
</model>
```

### The three composition patterns in PX4

**Pattern A — "base + payload" merge include.** This is how every x500
sensor variant is built. `x500_depth/model.sdf` in full:

```xml
<sdf version='1.9'>
  <model name='x500_depth'>
    <include merge='true'>
      <uri>x500</uri>
    </include>
    <include merge='true'>
      <uri>model://OakD-Lite</uri>
      <pose>.12 .03 .242 0 0 0</pose>
    </include>
    <joint name="CameraJoint" type="fixed">
      <parent>base_link</parent>
      <child>camera_link</child>
      <pose relative_to="base_link">.12 .03 .242 0 0 0</pose>
    </joint>
  </model>
</sdf>
```

`merge='true'` flattens included links / joints / sensors into the
parent rather than nesting. The `<joint>` rigidly attaches the camera
to the airframe.

**Pattern B — base airframe + motor plugins.** The `x500/model.sdf`
wraps `x500_base` and registers four
`gz-sim-multicopter-motor-model-system` plugins. One rotor block:

```xml
<plugin filename="gz-sim-multicopter-motor-model-system" name="gz::sim::systems::MulticopterMotorModel">
  <jointName>rotor_0_joint</jointName>
  <linkName>rotor_0</linkName>
  <turningDirection>ccw</turningDirection>
  <timeConstantUp>0.0125</timeConstantUp>
  <timeConstantDown>0.025</timeConstantDown>
  <maxRotVelocity>1000.0</maxRotVelocity>
  <motorConstant>8.54858e-06</motorConstant>
  <momentConstant>0.016</momentConstant>
  <commandSubTopic>command/motor_speed</commandSubTopic>
  <motorNumber>0</motorNumber>
  <rotorDragCoefficient>8.06428e-05</rotorDragCoefficient>
  <rollingMomentCoefficient>1e-06</rollingMomentCoefficient>
  <rotorVelocitySlowdownSim>10</rotorVelocitySlowdownSim>
  <motorType>velocity</motorType>
</plugin>
```

Per-motor thrust = `motorConstant × maxRotVelocity² × throttle²`. To
tune TWR, scale `motorConstant` (or `maxRotVelocity`) so peak
thrust × 4 = desired TWR × mass × g. See
[05_fpv_tuning.md](05_fpv_tuning.md) for the FPV-specific recipe.

**Pattern C — base link with the four canonical sensors.** This is in
`x500_base/model.sdf:218-310`. The four sensors PX4's `gz_bridge`
expects are declared on `base_link`:

```xml
<sensor name="air_pressure_sensor" type="air_pressure">
  <always_on>1</always_on>
  <update_rate>50</update_rate>
  <air_pressure>
    <pressure><noise type="gaussian"><stddev>3</stddev></noise></pressure>
  </air_pressure>
</sensor>
<sensor name="magnetometer_sensor" type="magnetometer">
  <always_on>1</always_on><update_rate>100</update_rate>
  <magnetometer>... gaussian noise stddev 0.0001 per axis ...</magnetometer>
</sensor>
<sensor name="imu_sensor" type="imu">
  <always_on>1</always_on><update_rate>250</update_rate>
  <imu> ... per-axis gaussian noise ... </imu>
</sensor>
<sensor name="navsat_sensor" type="navsat">
  <always_on>1</always_on><update_rate>30</update_rate>
</sensor>
```

### CRITICAL: hardcoded sensor names

`gz_bridge` (`src/modules/simulation/gz_bridge/GZBridge.cpp`)
hardcodes the topic paths:

```
/world/<world>/model/<model>/link/base_link/sensor/imu_sensor/imu
/world/<world>/model/<model>/link/base_link/sensor/magnetometer_sensor/magnetometer
/world/<world>/model/<model>/link/base_link/sensor/air_pressure_sensor/air_pressure
/world/<world>/model/<model>/link/base_link/sensor/navsat_sensor/navsat
```

So a custom model **must** name its sensors `imu_sensor`,
`magnetometer_sensor`, `air_pressure_sensor`, `navsat_sensor`, and
place them on a link called `base_link`. **Diverging from this
without patching `GZBridge.cpp` will leave PX4 in "sensor missing"
preflight failure forever** — this is the #1 cause of "I built a
custom airframe and EKF2 won't init." See
[08_troubleshooting.md](08_troubleshooting.md) for the diagnosis tree.

The model name itself is matched against `PX4_SIM_MODEL` /
`PX4_GZ_MODEL_NAME`.

### Adding stereo / depth / segmentation cameras

The `OakD-Lite/model.sdf` is the canonical example.

**RGB camera:**

```xml
<sensor name="IMX214" type="camera">
  <pose>0.01233 -0.03 .01878 0 0 0</pose>
  <camera>
    <horizontal_fov>1.204</horizontal_fov>
    <image><width>1920</width><height>1080</height></image>
    <clip><near>0.1</near><far>100</far></clip>
  </camera>
  <always_on>1</always_on><update_rate>30</update_rate>
  <visualize>true</visualize>
</sensor>
```

**Depth camera:**

```xml
<sensor name="StereoOV7251" type="depth_camera">
  <pose>0.01233 -0.03 .01878 0 0 0</pose>
  <camera>
    <horizontal_fov>1.274</horizontal_fov>
    <image><width>640</width><height>480</height><format>R_FLOAT32</format></image>
    <clip><near>0.2</near><far>19.1</far></clip>
  </camera>
  <always_on>1</always_on><update_rate>30</update_rate>
  <topic>depth_camera</topic>
</sensor>
```

**Segmentation camera** (Gazebo Harmonic):

```xml
<sensor name="seg_cam" type="segmentation_camera">
  <camera>
    <segmentation_type>semantic</segmentation_type>
    <horizontal_fov>1.5708</horizontal_fov>
    <image><width>1280</width><height>720</height></image>
  </camera>
  <always_on>1</always_on><update_rate>10</update_rate>
</sensor>
```

Per-visual `gz::sim::systems::Label` plugins assign class IDs — this
is exactly the pattern the project's `tools/label_world.py` uses.

**Stereo:** there is no first-class stereo sensor type in Gazebo —
instantiate two `type="camera"` sensors at known baseline. The
existing `drone_description/models/camera_rig` already does this and
can be merged into a custom `x500_research` model via Pattern A.

### Texture URI resolution

`model://x500_base/meshes/NXP-HGD-CF.dae` style URIs resolve against
`GZ_SIM_RESOURCE_PATH`, which `make px4_sitl gz_*` sets to include
`Tools/simulation/gz/models/`. To add custom textures, drop the model
directory into that path or extend `GZ_SIM_RESOURCE_PATH` before
launch. Fuel URIs (`https://fuel.gazebosim.org/...`) are also valid;
first launch downloads to `~/.gz/fuel/` (which on this project is
symlinked to `data/gz_fuel_cache/`).

## Adding a new world

Drop the SDF into `Tools/simulation/gz/worlds/<name>.sdf`. Selection
at runtime:

```bash
PX4_GZ_WORLD=mycity HEADLESS=1 make px4_sitl gz_x500
```

The `<world name="mycity">` attribute MUST equal the filename stem.

### Required top-level blocks

Mirroring `default.sdf:1-92`:

```xml
<sdf version="1.9">
  <world name="mycity">
    <physics type="ode">
      <max_step_size>0.004</max_step_size>
      <real_time_factor>1.0</real_time_factor>
      <real_time_update_rate>250</real_time_update_rate>
    </physics>
    <gravity>0 0 -9.8</gravity>
    <magnetic_field>6e-06 2.3e-05 -4.2e-05</magnetic_field>
    <atmosphere type="adiabatic"/>
    <scene>
      <grid>false</grid>
      <ambient>0.4 0.4 0.4 1</ambient>
      <background>0.7 0.7 0.7 1</background>
      <shadows>true</shadows>
    </scene>
    <!-- ground_plane and lighting here -->
    <spherical_coordinates>
      <surface_model>EARTH_WGS84</surface_model>
      <world_frame_orientation>ENU</world_frame_orientation>
      <latitude_deg>47.397971057728974</latitude_deg>
      <longitude_deg>8.546163739800146</longitude_deg>
      <elevation>0</elevation>
    </spherical_coordinates>
  </world>
</sdf>
```

### `<spherical_coordinates>` IS the GPS origin

Every stock world declares one. Most use Zürich (47.397971, 8.546164);
`baylands` uses Sunnyvale (37.412, −121.999). The
`gz-sim-navsat-system` plugin uses these to convert ENU world
coordinates to lat/lon, and the resulting GPS samples are what the EKF
locks onto.

`PX4_HOME_LAT/LON/ALT` env vars override the *spawn point* but not the
*world reference frame*. For tight EKF convergence keep them
consistent.

### Plugin block: do NOT add to the world SDF

The world SDF does **not** need `<plugin>` blocks for
`gz-sim-physics-system`, `gz-sim-sensors-system`, etc. — those are
loaded server-side via `Tools/simulation/gz/server.config`. See
[01_architecture.md](01_architecture.md#toolssimulationgzserverconfig--the-system-plugins-file).

### Project recommendation: world for "drone follows car, lands on car"

1. Start from a copy of `default.sdf`.
2. Replace the bare `ground_plane` with `<include>` of a Clearpath
   ground mesh (the project already does this in `orchard_labeled.sdf`
   and `construction_labeled.sdf`).
3. Add an `<include>` of the target vehicle (e.g. `Pickup` from Fuel)
   at a known pose.
4. Wrap the vehicle in a model that adds a
   `gz-sim-trajectory-follower-system` plugin (next section).
5. Keep the `<spherical_coordinates>` block so the drone has working
   GPS.
6. Save to
   `ros2_ws/src/drone_sim_bringup/worlds/landing_test.sdf` and prepend
   that dir to `GZ_SIM_RESOURCE_PATH`.

## Spawning extra entities (target vehicles, programmed motion)

Two ways to add non-PX4 entities to the world:

### A. Static composition via `<include>` in the world SDF

Used everywhere — `forest.sdf` has 100+ `<include>` lines pulling
Pine / Oak trees from Fuel; `baylands.sdf` does it for the entire park.

```xml
<include>
  <uri>https://fuel.gazebosim.org/1.0/OpenRobotics/models/Pickup</uri>
  <name>target_car</name>
  <pose>10 0 0 0 0 0</pose>
</include>
```

The `<name>` must be unique per world. On first launch the model is
downloaded to `~/.gz/fuel/`; subsequent launches use the cache.

### B. Runtime spawn via `gz service`

The world exposes `/world/<name>/create` taking
`gz.msgs.EntityFactory`:

```bash
gz service -s /world/default/create \
  --reqtype gz.msgs.EntityFactory \
  --reptype gz.msgs.Boolean \
  --timeout 1000 \
  --req 'sdf_filename: "/path/to/car/model.sdf",
         name: "target_car",
         pose: {position: {x: 5, y: 0, z: 0}}'
```

This is how the project's existing `dataset_capture.py` teleports the
camera rig — same service pattern, just with `pose` updates via
`/world/<name>/set_pose`.

### Programmed motion of the spawned vehicle

Three options, in order of how this codebase should reach for them:

**1. `gz-sim-trajectory-follower-system`** — declarative, lives in the
model's SDF, no external publishing needed:

```xml
<plugin filename="gz-sim-trajectory-follower-system"
        name="systems::TrajectoryFollower">
  <link_name>base_link</link_name>
  <loop>true</loop>
  <waypoints>
    <waypoint>25 0</waypoint>
    <waypoint>15 10</waypoint>
    <waypoint>0 0</waypoint>
  </waypoints>
  <range_tolerance>0.5</range_tolerance>
  <bearing_tolerance>0.035</bearing_tolerance>
  <force>60</force>
  <torque>50</torque>
</plugin>
```

Operates in 2-D (x, y); applies torque to align with the next
waypoint, then force to drive toward it. **Best for the project's
"car drives a closed loop" scenario** without writing any controller
code. (Source:
<https://gazebosim.org/api/sim/8/classgz_1_1sim_1_1systems_1_1TrajectoryFollower.html>)

**2. `gz topic` velocity command** — to a model carrying
`gz-sim-velocity-control-system` or `gz-sim-ackermann-steering-system`:

```bash
gz topic -t "/model/target_car/cmd_vel" -m gz.msgs.Twist -p "linear: {x: 4.0}"
```

Better than TrajectoryFollower if you need closed-loop control from a
ROS 2 node — bridge `geometry_msgs/Twist ↔ gz.msgs.Twist` over
`ros_gz_bridge` and publish from a small node.

**3. `MovingPlatformController`** — pattern from `moving_platform.sdf`.
Custom C++ plugin (`libMovingPlatformController.so`). Use only if the
trajectory needs to be parameterised in C++ (e.g. accelerations
coupled to drone state).

### For the project: `rover_ackermann` as the target car

The PX4 `rover_ackermann` model already has
`gz-sim-ackermann-steering-system`. Driving from ROS 2 is trivial:
bridge `geometry_msgs/Twist ↔ gz.msgs.Twist` on
`/model/<name>/cmd_vel` and publish from a ROS 2 path-following node.

This avoids running a second PX4 instance for the rover — it's just a
gz-sim entity driven by a ROS 2 publisher.

## Sources

- Adding a new airframe:
  <https://docs.px4.io/main/en/dev_airframes/adding_a_new_frame.html>
- Airframe reference (autostart IDs):
  <https://docs.px4.io/main/en/dev_airframes/airframe_reference.html>
- Gazebo TrajectoryFollower API:
  <https://gazebosim.org/api/sim/8/classgz_1_1sim_1_1systems_1_1TrajectoryFollower.html>
- Gazebo runtime entity spawn:
  <https://gazebosim.org/docs/harmonic/spawn_urdf/>
- On-disk source files cited above:
  - `Tools/simulation/gz/server.config`
  - `Tools/simulation/gz/worlds/{default,baylands,moving_platform,...}.sdf`
  - `Tools/simulation/gz/models/{x500,x500_base,x500_depth,x500_mono_cam,x500_lidar_2d,x500_lidar_front,x500_vision,x500_gimbal,OakD-Lite,mono_cam,moving_platform}/model.sdf`
  - `ROMFS/px4fmu_common/init.d-posix/airframes/4001_gz_x500` (and the variant scripts)
  - `src/modules/simulation/gz_bridge/GZBridge.cpp` (sensor topic naming convention)
