# Simulators (ROS 2 Jazzy)

> Note: For this project, **Gazebo Harmonic** is the target. Webots and MVSim are alternatives included for completeness. The `ros_gz` bridge with Gazebo Harmonic is the canonical pairing for ROS 2 Jazzy.

---

## Gazebo Harmonic

### Installing Gazebo with ROS

**Source**: https://gazebosim.org/docs/harmonic/ros_installation

The Gazebo project recommends new users install the latest LTS combination: **Ubuntu Noble 24.04 + ROS 2 Jazzy Jalisco + Gazebo Harmonic**. Gazebo Harmonic is the LTS Gazebo paired with Jazzy by REP-2000.

**Compatibility matrix** (legend: `OK` = recommended, `~` = possible with caution, `X` = incompatible):

| ROS 2 distro       | GZ Fortress | GZ Harmonic | GZ Ionic | GZ Jetty |
|--------------------|-------------|-------------|----------|----------|
| Rolling            | X           | ~           | ~        | OK       |
| Lyrical (LTS)      | X           | ~           | ~        | OK       |
| Kilted             | X           | ~           | OK       | X        |
| **Jazzy (LTS)**    | X           | **OK**      | X        | X        |
| Humble (LTS)       | OK          | ~           | X        | X        |

**Default install (Jazzy + Harmonic) — recommended, no extra apt repo needed:**

```bash
sudo apt-get update
sudo apt-get install ros-jazzy-ros-gz
```

This metapackage pulls in all the bridge subpackages (`ros-jazzy-ros-gz-bridge`, `ros-jazzy-ros-gz-image`, `ros-jazzy-ros-gz-sim`, `ros-jazzy-ros-gz-sim-demos`, `ros-jazzy-ros-gz-interfaces`) **and** the Gazebo Harmonic libraries — but bundled inside ROS-namespaced **vendor packages** rather than as standalone Debian packages. The vendor mechanism is what avoids the OSRF apt repo step entirely.

**Where the `gz` CLI actually lives after this install** (this is the part that bites people):

```
/opt/ros/jazzy/opt/gz_tools_vendor/bin/gz
```

It is **not** in `/usr/bin`. It is only on `$PATH` after sourcing `/opt/ros/jazzy/setup.bash`. Same for the Gazebo libraries (under `/opt/ros/jazzy/opt/gz_*_vendor/lib/`) — they're loaded via the ROS env, not the system linker cache. So:

- `which gz` in a non-sourced shell → empty / "command not found".
- `gz sim --version` printing nothing usually means the shell wasn't sourced; it does not mean Gazebo is broken.
- After sourcing, `gz sim --version` prints `Gazebo Sim, version 8.x.y` (Harmonic is the 8.x series).

The vendor packages installed by `ros-jazzy-ros-gz` are: `gz-cmake-vendor`, `gz-common-vendor`, `gz-fuel-tools-vendor`, `gz-gui-vendor`, `gz-launch-vendor`, `gz-math-vendor`, `gz-msgs-vendor`, `gz-physics-vendor`, `gz-plugin-vendor`, `gz-rendering-vendor`, `gz-sensors-vendor`, `gz-sim-vendor`, `gz-tools-vendor`, `gz-transport-vendor`, `gz-utils-vendor`, `sdformat-vendor`. Each lives under `/opt/ros/jazzy/opt/<name>/`.

**Alternative — standalone Gazebo Harmonic via the OSRF apt repo** (only needed if you want a system-wide `/usr/bin/gz`, e.g. to use Gazebo without sourcing ROS, or to pin a specific Gazebo patch version independent of the ROS release):

```bash
sudo apt-get install lsb-release wget gnupg
sudo wget https://packages.osrfoundation.org/gazebo.gpg -O /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null
sudo apt-get update
sudo apt-get install gz-harmonic
```

Do not mix the two install paths in the same workspace unless you know what you're doing — you can end up with two different `gz` binaries on PATH and library mismatches between Gazebo and the ros_gz bridge.

**Non-default pairing (Harmonic + Humble):**

```bash
sudo apt-get install ros-humble-ros-gzharmonic
```

> The doc warns: *"These packages conflict with `ros-humble-ros-gz*` packages (Humble officially supports Gazebo Fortress)."* Do not mix.

**Verify (Jazzy):**

```bash
source /opt/ros/jazzy/setup.bash    # ESSENTIAL — gz vendor binary is sourced from ROS
which gz                             # should print /opt/ros/jazzy/opt/gz_tools_vendor/bin/gz
gz sim --version                     # should print "Gazebo Sim, version 8.x.y"
gz sim                               # opens the world chooser GUI
```

---

### Getting Started with Gazebo Harmonic

**Source**: https://gazebosim.org/docs/harmonic/getstarted

Gazebo Harmonic is supported through **September 2028** (LTS).

**Core CLI commands:**

```bash
gz sim shapes.sdf            # launch a world (GUI + server)
gz sim shapes.sdf -v 4       # verbose level 4 (debug)
gz sim -s shapes.sdf -v 4    # server-only (headless)
gz sim -g                    # GUI only (connects to existing server)
gz sim -r shapes.sdf         # start unpaused (run on launch)
```

On macOS, the server and GUI must always run in separate terminals.

**Other important `gz` CLIs** (not shown on the getstarted page but standard tooling):

```bash
# Topics
gz topic -l                                    # list all topics
gz topic -i -t /world/default/clock            # info about a topic
gz topic -e -t /imu                            # echo messages
gz topic -p "linear: {x: 0.5}" -t /cmd_vel \
    -m gz.msgs.Twist                           # publish

# Models
gz model --list                                # list spawned models
gz model -m my_robot --pose                    # query model pose
gz model -m my_robot --info                    # full info

# Services
gz service -l                                  # list services
gz service -s /world/default/control \
    --reqtype gz.msgs.WorldControl \
    --reptype gz.msgs.Boolean --timeout 1000 \
    --req "pause: false"                       # call service

# Sim control via service (pause/play/step)
gz service -s /world/default/control \
    --reqtype gz.msgs.WorldControl \
    --reptype gz.msgs.Boolean --timeout 300 \
    --req 'pause: true'
```

**Models** come from Gazebo Fuel: https://app.gazebosim.org/fuel — drag-and-drop into the GUI or `<include><uri>https://fuel.gazebosim.org/1.0/<owner>/models/<name></uri></include>` in SDF.

---

### SDF Worlds

**Source**: https://gazebosim.org/docs/harmonic/sdf_worlds

Every Gazebo world is an SDF (Simulation Description Format) file.

**Skeleton:**

```xml
<?xml version="1.0" ?>
<sdf version="1.8">
  <world name="world_demo">
    <!-- physics, plugins, light, models go here -->
  </world>
</sdf>
```

**Physics block:**

```xml
<physics name="1ms" type="ignored">
    <max_step_size>0.001</max_step_size>
    <real_time_factor>1.0</real_time_factor>
</physics>
```

- `max_step_size` — physics integration step (smaller = more accurate, slower)
- `real_time_factor` — target ratio of sim time to wall-clock time (1.0 = real time)

**Essential system plugins** (must be present in every world that needs the standard features):

```xml
<plugin filename="gz-sim-physics-system"
        name="gz::sim::systems::Physics">
</plugin>
<plugin filename="gz-sim-user-commands-system"
        name="gz::sim::systems::UserCommands">
</plugin>
<plugin filename="gz-sim-scene-broadcaster-system"
        name="gz::sim::systems::SceneBroadcaster">
</plugin>
<plugin filename="gz-sim-sensors-system"
        name="gz::sim::systems::Sensors">
    <render_engine>ogre2</render_engine>
</plugin>
```

| Plugin | Role |
|--------|------|
| `gz-sim-physics-system` | Steps physics |
| `gz-sim-user-commands-system` | Spawning / deleting models at runtime, GUI commands |
| `gz-sim-scene-broadcaster-system` | Publishes scene state for the GUI client / rendering |
| `gz-sim-sensors-system` | Drives camera/lidar/depth sensors (needs `<render_engine>` chosen) |
| `gz-sim-imu-system` | Drives IMU sensors |
| `gz-sim-contact-system` | Drives contact sensors |
| `gz-sim-label-system` | Tags entities with semantic labels for segmentation |
| `gz-sim-diff-drive-system` | Differential drive command/odom |
| `gz-sim-joint-state-publisher-system` | Publishes `joint_state` |
| `gz-sim-pose-publisher-system` | Publishes link/model poses |

**Light:**

```xml
<light type="directional" name="sun">
    <cast_shadows>true</cast_shadows>
    <pose>0 0 10 0 0 0</pose>
    <diffuse>0.8 0.8 0.8 1</diffuse>
    <specular>0.2 0.2 0.2 1</specular>
    <attenuation>
        <range>1000</range>
        <constant>0.9</constant>
        <linear>0.01</linear>
        <quadratic>0.001</quadratic>
    </attenuation>
    <direction>-0.5 0.1 -0.9</direction>
</light>
```

**Including a model from Fuel:**

```xml
<include>
    <uri>https://fuel.gazebosim.org/1.0/OpenRobotics/models/Coke</uri>
    <name>my_coke</name>
    <pose>1 2 0 0 0 0</pose>
</include>
```

**Model / Link / Joint hierarchy:**

```xml
<model name="my_robot">
  <pose>0 0 0 0 0 0</pose>
  <link name="base_link">
    <inertial>
      <mass>1.0</mass>
      <inertia> <ixx>0.1</ixx> <iyy>0.1</iyy> <izz>0.1</izz> </inertia>
    </inertial>
    <collision name="collision">
      <geometry><box><size>0.5 0.5 0.2</size></box></geometry>
    </collision>
    <visual name="visual">
      <geometry><box><size>0.5 0.5 0.2</size></box></geometry>
      <material><ambient>0.2 0.4 0.8 1</ambient></material>
    </visual>
  </link>

  <link name="wheel_left"> ... </link>

  <joint name="left_wheel_joint" type="revolute">
    <parent>base_link</parent>
    <child>wheel_left</child>
    <axis><xyz>0 1 0</xyz></axis>
  </joint>
</model>
```

---

### Gazebo Sensors

**Source**: https://gazebosim.org/docs/harmonic/sensors

The on-page tutorial covers IMU, Contact, and Lidar in detail. Camera-family sensors (camera, depth_camera, rgbd_camera, segmentation, thermal, boundingbox) are documented in `gz-sensors` and demonstrated in `gz-sim/examples/worlds/`. SDF examples below come from the canonical example worlds in the `gz-sim8` branch (Harmonic).

#### IMU sensor

Plugin (must be in `<world>`):

```xml
<plugin filename="gz-sim-imu-system" name="gz::sim::systems::Imu">
</plugin>
```

Sensor (inside a `<link>`):

```xml
<sensor name="imu_sensor" type="imu">
    <always_on>1</always_on>
    <update_rate>1</update_rate>
    <visualize>true</visualize>
    <topic>imu</topic>
</sensor>
```

Outputs `gz.msgs.IMU` containing orientation (quaternion), angular_velocity (X/Y/Z), and linear_acceleration (X/Y/Z).

#### Contact sensor

```xml
<plugin filename="gz-sim-contact-system" name="gz::sim::systems::Contact">
</plugin>
```

```xml
<sensor name='sensor_contact' type='contact'>
    <contact>
        <collision>collision</collision>
    </contact>
</sensor>
```

#### GPU Lidar (recommended over CPU `lidar`)

Requires the sensors-system plugin in the world. Then in a link:

```xml
<sensor name='gpu_lidar' type='gpu_lidar'>
    <pose relative_to='lidar_frame'>0 0 0 0 0 0</pose>
    <topic>lidar</topic>
    <update_rate>10</update_rate>
    <ray>
        <scan>
            <horizontal>
                <samples>640</samples>
                <resolution>1</resolution>
                <min_angle>-1.396263</min_angle>
                <max_angle>1.396263</max_angle>
            </horizontal>
            <vertical>
                <samples>1</samples>
                <resolution>0.01</resolution>
                <min_angle>0</min_angle>
                <max_angle>0</max_angle>
            </vertical>
        </scan>
        <range>
            <min>0.08</min>
            <max>10.0</max>
            <resolution>0.01</resolution>
        </range>
    </ray>
    <always_on>1</always_on>
    <visualize>true</visualize>
</sensor>
```

For 3D lidar, raise `<vertical><samples>` (e.g. 16 or 32) and widen the vertical angle range.

#### RGB camera

```xml
<sensor name="camera" type="camera">
  <camera>
    <horizontal_fov>1.047</horizontal_fov>
    <image>
      <width>320</width>
      <height>240</height>
    </image>
    <clip>
      <near>0.1</near>
      <far>100</far>
    </clip>
  </camera>
  <always_on>1</always_on>
  <update_rate>30</update_rate>
  <visualize>true</visualize>
  <topic>camera</topic>
</sensor>
```

Publishes:
- `<topic>` -> `gz.msgs.Image`
- `<topic>/camera_info` -> `gz.msgs.CameraInfo`

#### Depth camera

```xml
<sensor name="depth_camera1" type="depth_camera">
  <update_rate>10</update_rate>
  <topic>depth_camera</topic>
  <camera>
    <horizontal_fov>1.05</horizontal_fov>
    <image>
      <width>256</width>
      <height>256</height>
      <format>R_FLOAT32</format>
    </image>
    <clip>
      <near>0.1</near>
      <far>10.0</far>
    </clip>
  </camera>
</sensor>
```

`R_FLOAT32` packs depth in metres into a single-channel float image. Bridges to `sensor_msgs/Image`.

#### RGBD camera

`rgbd_camera` is essentially a fused camera that publishes BOTH an RGB image AND a depth image AND a point cloud on a topic stem. Sensor block is the same as a camera, but `type="rgbd_camera"` and Gazebo will publish:

```
<topic>/image          gz.msgs.Image          (RGB)
<topic>/depth_image    gz.msgs.Image          (depth, R_FLOAT32)
<topic>/points         gz.msgs.PointCloudPacked (XYZ + RGB)
<topic>/camera_info    gz.msgs.CameraInfo
```

```xml
<sensor name="rgbd" type="rgbd_camera">
  <update_rate>30</update_rate>
  <topic>rgbd</topic>
  <camera>
    <horizontal_fov>1.047</horizontal_fov>
    <image>
      <width>640</width>
      <height>480</height>
    </image>
    <clip>
      <near>0.1</near>
      <far>10.0</far>
    </clip>
  </camera>
</sensor>
```

#### Stereo camera

There is no dedicated `stereo` sensor type. A stereo rig is two `camera` sensors on the same link separated by the baseline (typically along Y), with matched intrinsics. Bridge each camera's `image` and `camera_info` separately, then run `image_proc`/`stereo_image_proc` to compute disparity.

```xml
<link name="stereo_link">
  <sensor name="left_camera" type="camera">
    <pose>0 0.06 0 0 0 0</pose>
    <topic>stereo/left</topic>
    <camera>
      <horizontal_fov>1.047</horizontal_fov>
      <image><width>640</width><height>480</height></image>
      <clip><near>0.1</near><far>100</far></clip>
    </camera>
    <update_rate>30</update_rate>
    <always_on>1</always_on>
  </sensor>
  <sensor name="right_camera" type="camera">
    <pose>0 -0.06 0 0 0 0</pose>
    <topic>stereo/right</topic>
    <camera>
      <horizontal_fov>1.047</horizontal_fov>
      <image><width>640</width><height>480</height></image>
      <clip><near>0.1</near><far>100</far></clip>
    </camera>
    <update_rate>30</update_rate>
    <always_on>1</always_on>
  </sensor>
</link>
```

#### Segmentation camera

Two flavours — `semantic` (class label per pixel) and `instance` / `panoptic` (instance ID + class). Both use sensor type `segmentation`.

Plugin (required):

```xml
<plugin filename="gz-sim-sensors-system"
        name="gz::sim::systems::Sensors">
    <render_engine>ogre2</render_engine>
</plugin>
```

Each scene object is given a label via the **label-system plugin**:

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

Instance / panoptic camera:

```xml
<sensor name="instance_segmentation_camera" type="segmentation">
  <topic>panoptic</topic>
  <camera>
    <segmentation_type>instance</segmentation_type>
    <horizontal_fov>1.57</horizontal_fov>
    <image>
      <width>800</width>
      <height>600</height>
    </image>
    <clip>
      <near>0.1</near>
      <far>100</far>
    </clip>
    <!-- optional: dump frames to disk
    <save enabled="true">
      <path>segmentation_data/instance_camera</path>
    </save>
    -->
  </camera>
  <always_on>1</always_on>
  <update_rate>30</update_rate>
  <visualize>true</visualize>
</sensor>
```

Semantic-only camera:

```xml
<sensor name="semantic_segmentation_camera" type="segmentation">
  <topic>semantic</topic>
  <camera>
    <segmentation_type>semantic</segmentation_type>
    <horizontal_fov>1.57</horizontal_fov>
    <image>
      <width>800</width>
      <height>600</height>
    </image>
    <clip>
      <near>0.1</near>
      <far>100</far>
    </clip>
  </camera>
  <always_on>1</always_on>
  <update_rate>30</update_rate>
  <visualize>true</visualize>
</sensor>
```

Topics published per segmentation sensor (with `<topic>foo</topic>`):

| Topic | Content |
|-------|---------|
| `foo/colored_map`  | RGB visualisation (one colour per label / instance) |
| `foo/labels_map`   | Raw label image (uint16 / uint8 per pixel)         |

Both bridge as `sensor_msgs/Image` on the ROS side.

---

## ros_gz Bridge & Integration

**Source**: https://gazebosim.org/docs/harmonic/ros2_integration

The `ros_gz_bridge` package provides bidirectional message passing between ROS 2 topics and Gazebo Transport topics. The metapackage `ros-jazzy-ros-gz` ships:

| Package | Purpose |
|---------|---------|
| `ros_gz_sim` | Launch Gazebo from ROS, spawn entities (`create` action), `gz_server.launch.py` |
| `ros_gz_bridge` | Generic `parameter_bridge` for any supported message type |
| `ros_gz_image` | Specialised `image_bridge` (uses image_transport, more efficient than parameter_bridge for streams) |
| `ros_gz_interfaces` | ROS message/service definitions that map to Gazebo-specific protobufs (entity, contacts, etc.) |
| `ros_gz_sim_demos` | Reference demo launch files (`sdf_parser`, `diff_drive`, `gpu_lidar`, …) |

### parameter_bridge syntax

Format: `/TOPIC@ROS_MSG@GZ_MSG` with the middle character indicating direction.

| Symbol | Direction               |
|--------|-------------------------|
| `@`    | Bidirectional           |
| `[`    | Gazebo -> ROS only      |
| `]`    | ROS -> Gazebo only      |

Example (one-shot CLI bridge):

```bash
ros2 run ros_gz_bridge parameter_bridge \
  /scan@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan
```

Multiple topics in one process:

```bash
ros2 run ros_gz_bridge parameter_bridge \
  /clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock \
  /cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist \
  /odom@nav_msgs/msg/Odometry[gz.msgs.Odometry \
  /imu@sensor_msgs/msg/Imu[gz.msgs.IMU \
  /scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan \
  /tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V
```

Note the direction characters above:
- `[gz.msgs.Clock` reads clock from Gazebo into ROS only.
- `]gz.msgs.Twist` pushes Twist from ROS into Gazebo only.

### YAML config (preferred for >2 topics)

Per-pair fields:

| Field | Meaning |
|-------|---------|
| `ros_topic_name`   | ROS-side topic |
| `gz_topic_name`    | Gazebo-side topic |
| `ros_type_name`    | ROS msg type, e.g. `sensor_msgs/msg/Image` |
| `gz_type_name`     | Gazebo msg type, e.g. `gz.msgs.Image` |
| `subscriber_queue` | ROS subscriber queue depth |
| `publisher_queue`  | ROS publisher queue depth |
| `lazy`             | `true` to subscribe lazily (no traffic until something is connected) |
| `direction`        | `GZ_TO_ROS`, `ROS_TO_GZ`, or `BIDIRECTIONAL` |

Example `bridge.yaml`:

```yaml
- ros_topic_name: "clock"
  gz_topic_name: "/clock"
  ros_type_name: "rosgraph_msgs/msg/Clock"
  gz_type_name: "gz.msgs.Clock"
  direction: GZ_TO_ROS

- ros_topic_name: "scan"
  gz_topic_name: "/lidar"
  ros_type_name: "sensor_msgs/msg/LaserScan"
  gz_type_name: "gz.msgs.LaserScan"
  direction: GZ_TO_ROS

- ros_topic_name: "cmd_vel"
  gz_topic_name: "/model/my_robot/cmd_vel"
  ros_type_name: "geometry_msgs/msg/Twist"
  gz_type_name: "gz.msgs.Twist"
  direction: ROS_TO_GZ

- ros_topic_name: "odom"
  gz_topic_name: "/model/my_robot/odometry"
  ros_type_name: "nav_msgs/msg/Odometry"
  gz_type_name: "gz.msgs.Odometry"
  direction: GZ_TO_ROS

- ros_topic_name: "imu"
  gz_topic_name: "/world/default/model/my_robot/link/imu_link/sensor/imu_sensor/imu"
  ros_type_name: "sensor_msgs/msg/Imu"
  gz_type_name: "gz.msgs.IMU"
  direction: GZ_TO_ROS

- ros_topic_name: "tf"
  gz_topic_name: "/model/my_robot/pose"
  ros_type_name: "tf2_msgs/msg/TFMessage"
  gz_type_name: "gz.msgs.Pose_V"
  direction: GZ_TO_ROS

- ros_topic_name: "camera/image"
  gz_topic_name: "/camera"
  ros_type_name: "sensor_msgs/msg/Image"
  gz_type_name: "gz.msgs.Image"
  direction: GZ_TO_ROS
  lazy: true

- ros_topic_name: "camera/camera_info"
  gz_topic_name: "/camera_info"
  ros_type_name: "sensor_msgs/msg/CameraInfo"
  gz_type_name: "gz.msgs.CameraInfo"
  direction: GZ_TO_ROS
```

### Launching the bridge

Standard:

```bash
ros2 launch ros_gz_bridge ros_gz_bridge.launch.py \
    bridge_name:=ros_gz_bridge \
    config_file:=<path_to_your_YAML_file>
```

With composition (faster — single process):

```bash
ros2 launch ros_gz_bridge ros_gz_bridge.launch.py \
    bridge_name:=ros_gz_bridge \
    config_file:=<path_to_your_YAML_file> \
    use_composition:=True \
    create_own_container:=True
```

With QoS overrides (forces transient_local on a topic):

```bash
ros2 launch ros_gz_bridge ros_gz_bridge.launch.py \
    bridge_name:=ros_gz_bridge \
    config_file:=<path_to_your_YAML_file> \
    bridge_params:={'qos_overrides./topic_name.publisher.durability': 'transient_local'}
```

### image_bridge

For high-rate image streams, prefer `image_bridge` over `parameter_bridge` — it uses `image_transport` so downstream subscribers can request compressed transports:

```bash
ros2 run ros_gz_image image_bridge /camera /depth_camera /rgbd/image
```

Each Gazebo image topic listed becomes a ROS topic of the same name publishing `sensor_msgs/Image` plus the matching `<topic>/camera_info` (CameraInfo) automatically.

### Complete message-type mapping

| ROS 2 type                       | Gazebo type                |
|----------------------------------|----------------------------|
| `sensor_msgs/msg/Image`          | `gz.msgs.Image`            |
| `sensor_msgs/msg/CameraInfo`     | `gz.msgs.CameraInfo`       |
| `sensor_msgs/msg/Imu`            | `gz.msgs.IMU`              |
| `sensor_msgs/msg/LaserScan`      | `gz.msgs.LaserScan`        |
| `sensor_msgs/msg/PointCloud2`    | `gz.msgs.PointCloudPacked` |
| `sensor_msgs/msg/JointState`     | `gz.msgs.Model`            |
| `sensor_msgs/msg/MagneticField`  | `gz.msgs.Magnetometer`     |
| `sensor_msgs/msg/FluidPressure`  | `gz.msgs.FluidPressure`    |
| `sensor_msgs/msg/NavSatFix`      | `gz.msgs.NavSat`           |
| `geometry_msgs/msg/Twist`        | `gz.msgs.Twist`            |
| `geometry_msgs/msg/TwistStamped` | `gz.msgs.Twist`            |
| `geometry_msgs/msg/Pose`         | `gz.msgs.Pose`             |
| `geometry_msgs/msg/PoseStamped`  | `gz.msgs.Pose`             |
| `geometry_msgs/msg/PoseArray`    | `gz.msgs.Pose_V`           |
| `geometry_msgs/msg/Vector3`      | `gz.msgs.Vector3d`         |
| `geometry_msgs/msg/Wrench`       | `gz.msgs.Wrench`           |
| `nav_msgs/msg/Odometry`          | `gz.msgs.Odometry`         |
| `rosgraph_msgs/msg/Clock`        | `gz.msgs.Clock`            |
| `tf2_msgs/msg/TFMessage`         | `gz.msgs.Pose_V`           |
| `std_msgs/msg/Bool`              | `gz.msgs.Boolean`          |
| `std_msgs/msg/Float32`           | `gz.msgs.Float`            |
| `std_msgs/msg/Float64`           | `gz.msgs.Double`           |
| `std_msgs/msg/Int32`             | `gz.msgs.Int32`            |
| `std_msgs/msg/UInt32`            | `gz.msgs.UInt32`           |
| `std_msgs/msg/String`            | `gz.msgs.StringMsg`        |
| `std_msgs/msg/Header`            | `gz.msgs.Header`           |
| `std_msgs/msg/ColorRGBA`         | `gz.msgs.Color`            |
| `actuator_msgs/msg/Actuators`    | `gz.msgs.Actuators`        |
| `vision_msgs/msg/Detection2D`    | `gz.msgs.AnnotatedAxisAligned2DBox` |
| `vision_msgs/msg/Detection3D`    | `gz.msgs.AnnotatedOriented3DBox`    |
| `ros_gz_interfaces/msg/Contacts` | `gz.msgs.Contacts`         |
| `ros_gz_interfaces/msg/Entity`   | `gz.msgs.Entity`           |
| `ros_gz_interfaces/msg/JointWrench` | `gz.msgs.JointWrench`   |

### Common topics for a sensor-equipped drone

Standard topic names Gazebo emits given a robot model named `drone` with the listed plugins / sensors (replace `default` with your world name):

| Purpose            | Gazebo topic                                                                | Bridge to ROS         | ROS type                |
|--------------------|-----------------------------------------------------------------------------|-----------------------|-------------------------|
| Sim clock          | `/clock`                                                                    | GZ -> ROS             | `rosgraph_msgs/Clock`   |
| Cmd velocity       | `/model/drone/cmd_vel`                                                      | ROS -> GZ             | `geometry_msgs/Twist`   |
| Odometry           | `/model/drone/odometry`                                                     | GZ -> ROS             | `nav_msgs/Odometry`     |
| TF                 | `/model/drone/pose` or `/model/drone/tf`                                    | GZ -> ROS             | `tf2_msgs/TFMessage`    |
| Joint state        | `/world/default/model/drone/joint_state`                                    | GZ -> ROS             | `sensor_msgs/JointState`|
| IMU                | `/world/default/model/drone/link/base_link/sensor/imu_sensor/imu`           | GZ -> ROS             | `sensor_msgs/Imu`       |
| GPU lidar          | `/world/default/model/drone/link/lidar_link/sensor/gpu_lidar/scan`          | GZ -> ROS             | `sensor_msgs/LaserScan` |
| RGB camera         | `/world/default/model/drone/link/cam_link/sensor/camera/image`              | GZ -> ROS (image_bridge) | `sensor_msgs/Image`  |
| Camera info        | `/world/default/model/drone/.../sensor/camera/camera_info`                  | GZ -> ROS             | `sensor_msgs/CameraInfo`|
| Depth (RGBD)       | `<topic>/depth_image`                                                       | GZ -> ROS             | `sensor_msgs/Image`     |
| RGBD point cloud   | `<topic>/points`                                                            | GZ -> ROS             | `sensor_msgs/PointCloud2`|
| Segmentation map   | `<topic>/labels_map`, `<topic>/colored_map`                                 | GZ -> ROS             | `sensor_msgs/Image`     |

### Spawning a robot from ROS

```bash
ros2 run ros_gz_sim create -file my_robot.sdf -name drone -x 0 -y 0 -z 1
```

Or in a launch file:

```python
from launch import LaunchDescription
from launch_ros.actions import Node

return LaunchDescription([
    Node(
        package='ros_gz_sim', executable='create',
        arguments=['-file', '/path/to/drone.sdf',
                   '-name', 'drone',
                   '-x', '0', '-y', '0', '-z', '1.0'],
        output='screen'),
])
```

### Reference launch pattern (`bridge.launch.py`-style)

```python
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    pkg = get_package_share_directory('my_drone_sim')
    bridge_yaml = os.path.join(pkg, 'config', 'bridge.yaml')
    world_sdf  = os.path.join(pkg, 'worlds', 'default.sdf')

    gz_sim = ExecuteProcess(
        cmd=['gz', 'sim', '-r', '-v', '4', world_sdf],
        output='screen')

    bridge = Node(
        package='ros_gz_bridge', executable='parameter_bridge',
        parameters=[{'config_file': bridge_yaml,
                     'qos_overrides./tf.publisher.durability': 'transient_local'}],
        output='screen')

    image_bridge = Node(
        package='ros_gz_image', executable='image_bridge',
        arguments=['/camera', '/depth_camera'],
        output='screen')

    return LaunchDescription([gz_sim, bridge, image_bridge])
```

### ROS 2 Simulation Interfaces

The bridge exposes standardised services for spawning/deleting entities, controlling sim state (pause/play/step), and querying entities. These let nodes manipulate the simulation programmatically without bespoke Gazebo Transport calls.

---

### Setting up a robot simulation (Gazebo) — ROS 2 Tutorial

**Source**: https://docs.ros.org/en/jazzy/Tutorials/Advanced/Simulators/Gazebo/Gazebo.html

The Jazzy tutorial page is short — it confirms that "Gazebo" here means modern Gazebo (formerly Ignition), **not Gazebo Classic**, and points readers at:

- REP-2000 for the official Gazebo↔ROS pairing per distro
- The Gazebo compatibility table at https://gazebosim.org/docs/harmonic/ros_installation
- The Gazebo tutorials at gazebosim.org for everything beyond installation

It explicitly says: *"Move to the Gazebo tutorials to try out building your own robot."* Verification step: `gz sim` should launch a chooser GUI.

---

## Webots

> Webots is the alternative open-source simulator officially supported by ROS 2 via `webots_ros2`. The bridge is implemented as Python/C++ **plugins** loaded into the simulator via a URDF tag, rather than a generic transport bridge.

### Installation (Ubuntu)

**Source**: https://docs.ros.org/en/jazzy/Tutorials/Advanced/Simulators/Webots/Installation-Ubuntu.html

**Released package (recommended):**

```bash
sudo apt-get install ros-jazzy-webots-ros2
```

**From source:**

```bash
mkdir -p ~/ros2_ws/src
source /opt/ros/jazzy/setup.bash
cd ~/ros2_ws
git clone --recurse-submodules https://github.com/cyberbotics/webots_ros2.git src/webots_ros2
sudo apt install python3-pip python3-rosdep python3-colcon-common-extensions
sudo rosdep init && rosdep update
rosdep install --from-paths src --ignore-src --rosdistro jazzy
colcon build
source install/local_setup.bash
```

**Webots discovery order** (first match wins):

1. `$ROS2_WEBOTS_HOME`
2. `$WEBOTS_HOME`
3. `/usr/local/webots` or `/snap/webots/current/usr/share/webots`

```bash
export WEBOTS_HOME=/usr/local/webots
```

**Run a demo:**

```bash
ros2 launch webots_ros2_universal_robot multirobot_launch.py
```

---

### Installation (Windows)

**Source**: https://docs.ros.org/en/jazzy/Tutorials/Advanced/Simulators/Webots/Installation-Windows.html

Setup goes through **WSL2** with Ubuntu inside. Steps:

1. Install WSL2 + a ROS-compatible Ubuntu.
2. Install ROS 2 Jazzy in the WSL Ubuntu via the standard deb method.
3. Install `webots_ros2` (apt or source as on Ubuntu).
4. Webots itself is installed natively on Windows; tell the Linux side where it lives:

```bash
export WEBOTS_HOME=/mnt/c/Program\ Files/Webots
ros2 launch webots_ros2_universal_robot multirobot_launch.py
```

Discovery order on Windows: `$ROS2_WEBOTS_HOME`, `$WEBOTS_HOME`, `C:\Program Files\Webots`, then auto-download.

RViz works natively on recent WSL2; on older versions enable X11 via VcXsrv and set `DISPLAY`.

---

### Installation (macOS)

**Source**: https://docs.ros.org/en/jazzy/Tutorials/Advanced/Simulators/Webots/Installation-MacOS.html

ROS 2 cannot run natively well on macOS, so the official path is: **Webots native on macOS, ROS in a Linux UTM VM**, talking via a TCP shared-folder protocol.

1. Install UTM, create a virtualised Ubuntu 22.04 VM.
2. Configure a shared directory on the host (e.g. `/Users/<you>/shared`).
3. In the VM:

   ```bash
   mkdir /home/ubuntu/shared
   sudo mount -t 9p -o trans=virtio share /home/ubuntu/shared -oversion=9p2000.L
   ```

   For autostart in `/etc/fstab`:

   ```
   share /home/ubuntu/shared 9p trans=virtio,version=9p2000.L,rw,_netdev,nofail 0 0
   ```

4. Set the bridge env var inside the VM (host_path:vm_path):

   ```bash
   export WEBOTS_SHARED_FOLDER=/Users/username/shared:/home/ubuntu/shared
   ```

5. Install `webots_ros2` in the VM (apt or source).
6. On the macOS host, run the local TCP simulation server:

   ```bash
   export WEBOTS_HOME=/Applications/Webots.app
   python3 local_simulation_server.py
   ```

7. Inside the VM, launch a demo:

   ```bash
   ros2 launch webots_ros2_universal_robot multirobot_launch.py
   ```

Caveats: Webots must be native on macOS for GPU acceleration; the VM intentionally has hardware acceleration off; the shared folder is colon-separated `<host>:<vm>`.

---

### Setting up a robot simulation (Basic)

**Source**: https://docs.ros.org/en/jazzy/Tutorials/Advanced/Simulators/Webots/Setting-Up-Simulation-Webots-Basic.html

Tutorial duration ~30 min. Goal: build a custom Webots controller wired to ROS 2 via `webots_ros2_driver`.

**Package layout:**

```
my_package/
├── launch/
├── worlds/
├── resource/
└── my_package/
    └── my_robot_driver.py
```

**Custom plugin pattern (Python).** The driver class implements three methods that `webots_ros2_driver` calls:

- `init(self, webots_node, properties)` — get motor handles and create the ROS subscription:
  ```python
  self.__node.create_subscription(Twist, 'cmd_vel', self.__cmd_vel_callback, 1)
  ```
- `step()` — called each Webots timestep. Reads the latest `cmd_vel` and uses differential-drive kinematics (`wheel_radius=0.025 m`, `wheel_separation=0.09 m`) to compute left/right wheel speeds.
- The `__cmd_vel_callback` simply caches the incoming `Twist`.

The C++ equivalent uses namespace `my_robot_driver::MyRobotDriver`.

**URDF declares the plugin:**

```xml
<robot name="my_robot">
  <webots>
    <plugin type="my_package.my_robot_driver.MyRobotDriver"/>
  </webots>
</robot>
```

**Launch file** composes Webots + the controller with a graceful shutdown so closing Webots also stops the ROS node:

```python
from launch import LaunchDescription
from webots_ros2_driver.webots_launcher import WebotsLauncher
from webots_ros2_driver.webots_controller import WebotsController

def generate_launch_description():
    webots = WebotsLauncher(world='my_world.wbt')
    driver = WebotsController(robot_name='my_robot',
                              parameters=[{'robot_description': '/path/to/robot.urdf'}])
    return LaunchDescription([webots, driver])
```

**Verify:**

```bash
ros2 topic pub /cmd_vel geometry_msgs/Twist "linear: { x: 0.1 }"
```

---

### Setting up a robot simulation (Advanced)

**Source**: https://docs.ros.org/en/jazzy/Tutorials/Advanced/Simulators/Webots/Setting-Up-Simulation-Webots-Advanced.html

Extends the Basic tutorial with **sensors and obstacle avoidance**.

**Sensor declaration in URDF** uses `<device>` to map Webots devices into ROS topics:

```xml
<device reference="ds0" type="DistanceSensor">
  <ros>
    <topicName>/left_sensor</topicName>
  </ros>
</device>
```

`reference` is the Webots device name; `<ros>` configures topic name and update rate.

**Obstacle avoider node** subscribes to two `sensor_msgs/Range` topics and republishes `geometry_msgs/Twist`:

```cpp
if (left_sensor_value < 0.9 * MAX_RANGE ||
    right_sensor_value < 0.9 * MAX_RANGE) {
    command_message->angular.z = -2.0;
}
```

**Launch file** composes three components in one `LaunchDescription`: Webots, the driver controller, and the obstacle avoider node.

Requires `webots_ros2 >= 2023.1.0` and Webots R2023b.

---

### Setting up a Reset Handler

**Source**: https://docs.ros.org/en/jazzy/Tutorials/Advanced/Simulators/Webots/Simulation-Reset-Handler.html

Webots' built-in **Reset** button reverts the world but does not restart ROS controllers — they hang. Three patterns to fix this:

1. **Driver-only restart:** add `respawn=True` to the `WebotsController` launch action.
2. **Multi-node restart without shutdown:** use an `OnProcessExit` event handler that respawns dependent nodes when the driver exits.

   ```python
   reset_handler = launch.actions.RegisterEventHandler(
       event_handler=launch.event_handlers.OnProcessExit(
           target_action=robot_driver,
           on_exit=get_ros2_control_spawners,
       )
   )
   ```

3. **Full shutdown pattern:** split into two launch files — one for Webots, one for everything else (Nav2, RViz, …). The second file installs a shutdown handler that `EmitEvent(Shutdown)` when the driver exits, requiring manual restart after a reset.

---

### The Ros2Supervisor Node

**Source**: https://docs.ros.org/en/jazzy/Tutorials/Advanced/Simulators/Webots/Simulation-Supervisor.html

`Ros2Supervisor` is a Webots Robot with **supervisor privileges** that exposes ROS services/topics for sim-level control.

Capabilities:

- Publishes `/clock` (use with `use_sim_time:=true` consumers).
- Spawn nodes at runtime via `/Ros2Supervisor/spawn_node_from_string` (takes an SDF/Webots node string).
- Remove spawned nodes via `/Ros2Supervisor/remove_node`.
- Animation recording via start/stop services that take an HTML5 output path.

**Enable in launch:**

```python
webots = WebotsLauncher(
    world=PathJoinSubstitution([package_dir, 'worlds', world]),
    mode=mode,
    ros2_supervisor=True
)

return LaunchDescription([
    webots,
    webots._supervisor,
    # ... event handlers
])
```

**Spawn a robot at runtime:**

```bash
ros2 service call /Ros2Supervisor/spawn_node_from_string \
  webots_ros2_msgs/srv/SpawnNodeFromString \
  "data: Robot { name \"robot_name\" }"
```

**Start an animation recording:**

```bash
ros2 service call /Ros2Supervisor/animation_start_recording \
  webots_ros2_msgs/srv/SetString "{value: \"/path/to/index.html\"}"
```

---

## MVSim

> MVSim (MultiVehicle Simulator from MRPT) is a lightweight 2D/3D simulator that integrates natively with ROS 2. Useful for ground robots, multi-robot demos, and anything where Gazebo's overhead is unwanted. Not directly applicable to a quadrotor sim but listed for completeness.

### Installation (Ubuntu)

**Source**: https://docs.ros.org/en/jazzy/Tutorials/Advanced/Simulators/MVSim/Installation-Ubuntu.html

**Binary:**

```bash
sudo apt install ros-jazzy-mvsim
```

**From source:**

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
git clone https://github.com/MRPT/mvsim.git --recursive
cd ..
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release
source install/setup.bash
```

**Verify:**

```bash
mvsim --version
ros2 launch mvsim demo_warehouse.launch.py
```

Two executables ship: `mvsim` (CLI) and `mvsim_node` (the ROS 2 wrapper).

---

### Getting started with MVSim

**Source**: https://docs.ros.org/en/jazzy/Tutorials/Advanced/Simulators/MVSim/Getting-Started-MVSim.html

**Launch demos** standalone:

```bash
mvsim launch ~/ros2_ws/src/mvsim/mvsim_tutorial/demo_warehouse.world.xml
```

**Launch demos** via ROS 2:

```bash
ros2 launch mvsim demo_warehouse.launch.py
ros2 launch mvsim demo_warehouse.launch.py use_rviz:=True
ros2 launch mvsim demo_warehouse.launch.py headless:=True
```

**Drive the robot:**

```bash
ros2 topic pub /robot1/cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.5}, angular: {z: 0.3}}"

ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -r cmd_vel:=/robot1/cmd_vel
```

Demo worlds available: warehouse, TurtleBot3 classic, multi-robot navigation, terrain elevation, procedurally generated greenhouse.

---

### Defining worlds, robots, and sensors

**Source**: https://docs.ros.org/en/jazzy/Tutorials/Advanced/Simulators/MVSim/Defining-Worlds-MVSim.html

**Top-level XML:**

```xml
<mvsim_world version="1.0">
  <simul_timestep>0.01</simul_timestep>
  <gui> ... </gui>
  <!-- ground, vehicles, sensors -->
</mvsim_world>
```

**World element types:**

| Element             | Purpose                                            |
|---------------------|----------------------------------------------------|
| Occupancy grid      | Load obstacle maps from images                     |
| Elevation map       | Terrain heights from grayscale image               |
| Textured plane      | Visual ground surface                              |
| Block               | Static or dynamic rigid-body obstacle              |

**Vehicle dynamics models:**

- Differential drive (two-wheel)
- Ackermann (car steering)
- Ackermann drivetrain (with realistic transmission)

Motor controllers include `twist_pid`, which accepts `geometry_msgs/msg/Twist` directly — making MVSim a drop-in for ROS 2 cmd_vel pipelines.

**Predefined assets** (XML includes): TurtleBot3, Jackal UGV, pickup truck, plus 2D/3D LiDAR, cameras, IMU, GNSS sensors.

**Sensor noise** is configurable per-sensor (gyro/accel/range), enabling realistic perception evaluation.

Per-vehicle ROS 2 namespaces are automatic, so multi-robot scenarios bridge cleanly.

> Highlight from the MRPT docs: *"Very lightweight: low CPU and memory usage, fast startup times."* Compared to Gazebo, MVSim is ideal for fleet-scale runs but lacks photoreal rendering and a sophisticated physics engine — not appropriate for a vision-driven drone perception project.
