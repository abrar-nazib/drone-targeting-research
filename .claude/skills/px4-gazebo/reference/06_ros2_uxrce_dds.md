# 06 — ROS 2 ↔ PX4 via uXRCE-DDS + offboard control

The ROS 2 native bridge to PX4 (replaces MAVROS for new code), the
`/fmu/in/*` and `/fmu/out/*` topic catalogue, the offboard-takeoff
sequence, and the QoS recipe that catches everyone the first time.

Companion to [01_architecture.md](01_architecture.md) (which explains
why `gz_bridge` ≠ `ros_gz_bridge` ≠ uXRCE-DDS — three different
bridges, all separate).

## Architecture

uXRCE-DDS is the **ROS 2-native replacement for MAVROS** that has been
the recommended PX4 ↔ ROS 2 bridge since PX4 v1.14. Two cooperating
processes:

- **Client** — `uxrce_dds_client`, a uORB-side module **built into
  PX4 firmware by default**. Runs inside the autopilot (or SITL) and
  both publishes selected uORB topics outward AND subscribes to inbound
  topics. (Source:
  <https://docs.px4.io/main/en/middleware/uxrce_dds.html>)
- **Agent** — `MicroXRCEAgent`, an eProsima binary that runs on the
  companion / dev computer. Speaks the XRCE-DDS protocol on one side
  and ordinary DDS on the other, so its published topics become
  first-class ROS 2 topics on whatever DDS implementation ROS 2 is
  using (CycloneDDS / FastDDS). (Source:
  <https://docs.px4.io/main/en/ros2/user_guide.html>)

The link is **bidirectional and runs over UDP, serial, TCP, or a
custom transport**. **In SITL the simulator auto-starts the client on
localhost UDP port 8888** — you'll see this line in the boot log:

```
INFO  [uxrce_dds_client] init UDP agent IP:127.0.0.1, port:8888
```

uORB topics chosen for export are listed in
`src/modules/uxrce_dds_client/dds_topics.yaml` inside PX4-Autopilot.
They project into ROS 2 under two namespaces:

- `/fmu/out/*` — uORB topics published by PX4 (state, sensors, status).
- `/fmu/in/*` — uORB topics PX4 subscribes to (commands, setpoints,
  external odometry).

**Mapping rule**: snake_case uORB → CamelCase ROS 2 type. Examples:
`vehicle_local_position` → `px4_msgs/msg/VehicleLocalPosition`,
`trajectory_setpoint` → `px4_msgs/msg/TrajectorySetpoint`.
(Source:
<https://github.com/PX4/PX4-Autopilot/blob/main/src/modules/uxrce_dds_client/dds_topics.yaml>)

### Why uXRCE-DDS over MAVROS

- MAVROS was ROS 1; the ROS 2 backport always lagged. uXRCE-DDS is
  ROS 2-first.
- MAVLink imposes message translation
  (`vehicle_local_position` → `mavlink LOCAL_POSITION_NED` →
  `geometry_msgs/PoseStamped`) with lossy mapping. uXRCE-DDS exposes
  uORB **directly** as `px4_msgs` — the structural fidelity (e.g. the
  `xy_valid`, `z_valid` flags on `VehicleLocalPosition`) is preserved.
- Bridge runs at full uORB rates (100 Hz default per topic in
  `dds_topics.yaml`); MAVLink is rate-throttled.
- **Both can coexist** — recommended setup is uXRCE-DDS for code,
  QGroundControl over MAVLink for UX.

## Installing the agent on Ubuntu 24.04

There is **no apt package** for the agent on Ubuntu 24.04 / Jazzy in
the open ROS 2 repos at the time of writing
(`apt-cache search micro-xrce-dds` returns nothing). Canonical install
is **source build, pinned to v2.4.3 for Jazzy** (Foxy / Humble pin to
v2.4.2). (Source:
<https://docs.px4.io/main/en/middleware/uxrce_dds.html>)

```bash
git clone -b v2.4.3 https://github.com/eProsima/Micro-XRCE-DDS-Agent.git
cd Micro-XRCE-DDS-Agent
mkdir build && cd build
cmake ..
make -j$(nproc)
sudo make install
sudo ldconfig /usr/local/lib/
```

A snap is also available (`sudo snap install micro-xrce-dds-agent
--edge`) but the snap binary is invoked as `micro-xrce-dds-agent`
(hyphenated), not `MicroXRCEAgent`.

**Launch**:

```bash
MicroXRCEAgent udp4 -p 8888
```

`udp4` selects IPv4 UDP transport; `-p 8888` matches the PX4-side
default `UXRCE_DDS_PRT=8888`. You should immediately see
`create_client` and `create_participant` log lines once SITL boots.

## px4_msgs / px4_ros_com — version pinning

Two repos go in your colcon workspace `src/`:

- `git clone https://github.com/PX4/px4_msgs.git` — bare ROS 2
  message definitions auto-mirrored from `PX4-Autopilot/msg/`.
- `git clone https://github.com/PX4/px4_ros_com.git` —
  `frame_transforms` library (NED↔ENU helpers), example offboard
  nodes.

**The version pin is the single biggest footgun.** From the docs:
*"You should use a version of the px4_msgs package with the same
message definitions as the PX4 firmware you have installed."*

| Your PX4 | px4_msgs branch |
|---|---|
| `main` (HEAD) | `main` |
| **`v1.16.x`** | **`release/1.16`** ← this project |
| `v1.15.x` | `release/1.15` |
| `v1.14.x` | `release/1.14` |

If they drift you get **silent type-hash mismatches** — the agent
reports the topic but ROS 2 subscribers see nothing (or `rclcpp`
raises `TypeSignatureError`). Fix: check out the matching branch on
`px4_msgs` and rebuild.

PX4 v1.16 introduced a **message-versioning system** — message struct
definitions now carry a version, and a separate **Message Translation
Node** can be deployed to bridge between firmware versions and ROS 2
client versions. For our v1.16 SITL ↔ release/1.16 px4_msgs setup it
isn't needed.

Build:

```bash
source /opt/ros/jazzy/setup.bash
cd ~/ros2_ws
colcon build --packages-select px4_msgs px4_ros_com
source install/local_setup.bash
```

Constraint from the px4_msgs README: *"The ROS 2 message generation
pipeline requires all messages to be directly under `msg/` and doesn't
support sub-directories."*

## Frame conventions (NED↔ENU, FRD↔FLU)

PX4 internally uses two right-handed frames; ROS 2 conventionally
uses two **different** right-handed frames:

| Axis use | PX4 | ROS 2 (REP-103) |
|---|---|---|
| World frame | **NED** — X=North, Y=East, Z=**Down** | **ENU** — X=East, Y=North, Z=**Up** |
| Body frame | **FRD** — X=Forward, Y=Right, Z=Down | **FLU** — X=Forward, Y=Left, Z=Up |

From the docs: *"There is no implicit conversion between frame types
when topics are published or subscribed!"*
(<https://docs.px4.io/main/en/ros2/offboard_control.html>)

**Implications for offboard code:**

- A `TrajectorySetpoint` with `position = {0, 0, -5}` means **5 metres
  above** the EKF origin. Z is *down* in NED. **This is the single most
  common source of "drone flew into the ground" bugs.**
- `vehicle_local_position.heading` is a NED yaw (0 = North,
  π/2 = East), not an ENU yaw (0 = East).
- `vehicle_attitude.q` is the rotation from FRD body into the NED earth
  frame, in `[w, x, y, z]` order.

Conversion helpers live in
`px4_ros_com/include/px4_ros_com/frame_transforms.h` — call
`ned_to_enu_local_frame(...)` or `px4_to_ros_orientation(...)`
whenever you cross the boundary.

## Key topics — control side (`/fmu/in/*`)

These are the writable inputs you publish from your ROS 2 node.
Default `dds_topics.yaml` exposes all of these:

| Topic | Type | Purpose |
|---|---|---|
| `/fmu/in/offboard_control_mode` | `OffboardControlMode` | **Required heartbeat** — declares which axis layer is being commanded (position / velocity / accel / attitude / body_rate / thrust+torque / direct actuator). Stream at ≥ 2 Hz. |
| `/fmu/in/trajectory_setpoint` | `TrajectorySetpoint` | NED setpoint with `position[3]`, `velocity[3]`, `acceleration[3]`, `jerk[3]`, `yaw`, `yawspeed`. **NaN on a field = "don't control this axis"**. |
| `/fmu/in/vehicle_attitude_setpoint` | `VehicleAttitudeSetpoint` | When `OffboardControlMode.attitude=true`. Quaternion + thrust. |
| `/fmu/in/vehicle_rates_setpoint` | `VehicleRatesSetpoint` | When `OffboardControlMode.body_rate=true`. |
| `/fmu/in/vehicle_thrust_setpoint`, `/fmu/in/vehicle_torque_setpoint` | `VehicleThrustSetpoint` / `VehicleTorqueSetpoint` | When `thrust_and_torque=true`. |
| `/fmu/in/actuator_motors`, `/fmu/in/actuator_servos` | `ActuatorMotors` / `ActuatorServos` | When `direct_actuator=true`. PWM-level. |
| `/fmu/in/vehicle_command` | `VehicleCommand` | The "do anything" channel — mode change, arm/disarm, takeoff, land, RTL. Mirrors MAVLink `COMMAND_LONG`. |
| `/fmu/in/manual_control_input` | `ManualControlSetpoint` | Synthetic RC stick input for autonomous arming flows. |
| `/fmu/in/vehicle_visual_odometry`, `/fmu/in/vehicle_mocap_odometry` | `VehicleOdometry` | External pose into EKF2. |
| `/fmu/in/distance_sensor`, `/fmu/in/sensor_optical_flow`, `/fmu/in/obstacle_distance` | various | External sensor injection. |
| `/fmu/in/goto_setpoint` | `GotoSetpoint` | Higher-level "go here" alternative to TrajectorySetpoint. |

## Key topics — state side (`/fmu/out/*`)

| Topic | Type | What you read it for |
|---|---|---|
| `/fmu/out/vehicle_local_position` | `VehicleLocalPosition` | NED `x,y,z` from EKF2 + validity flags `xy_valid`, `z_valid`, `v_xy_valid`, `v_z_valid`, plus `heading`, `ref_lat`, `ref_lon`, `ref_alt`, `dist_bottom`. **Origin is the EKF2 init point**, not GPS home. |
| `/fmu/out/vehicle_global_position` | `VehicleGlobalPosition` | WGS84 lat/lon/alt. |
| `/fmu/out/vehicle_attitude` | `VehicleAttitude` | Quaternion FRD→NED. |
| `/fmu/out/vehicle_status` | `VehicleStatus` | `arming_state` (1=DISARMED, 2=ARMED), `nav_state` (14=OFFBOARD, 17=AUTO_TAKEOFF, 18=AUTO_LAND, 5=AUTO_RTL, 0=MANUAL, 2=POSCTL, 3=AUTO_MISSION), `pre_flight_checks_pass`, `failsafe`. |
| `/fmu/out/vehicle_control_mode` | `VehicleControlMode` | What controllers are currently active. |
| `/fmu/out/failsafe_flags` | `FailsafeFlags` | **The single most useful debug topic** — full decoder in [07_parameters_and_preflight.md](07_parameters_and_preflight.md). |
| `/fmu/out/estimator_status_flags` | `EstimatorStatusFlags` | EKF2 inner-state flags. |
| `/fmu/out/sensor_combined` | `SensorCombined` | SI-unit IMU at the EKF input rate. |
| `/fmu/out/vehicle_gps_position` | `SensorGps` | GPS sample (note the type is `SensorGps`, not a GPS-specific msg). |
| `/fmu/out/vehicle_odometry` | `VehicleOdometry` | Full state for downstream consumers. |
| `/fmu/out/battery_status` | `BatteryStatus` | |
| `/fmu/out/vehicle_land_detected` | `VehicleLandDetected` | Critical for landing-on-target — fires when contact detected. |
| `/fmu/out/home_position` | `HomePosition` | Set when GPS lock + arm-home is captured. |
| `/fmu/out/vehicle_command_ack` | `VehicleCommandAck` | The ack for every `vehicle_command` you sent. **Always subscribe to this** — it tells you whether `DO_SET_MODE` was rejected and why. |
| `/fmu/out/timesync_status` | `TimesyncStatus` | |

(Canonical list:
<https://github.com/PX4/PX4-Autopilot/blob/main/src/modules/uxrce_dds_client/dds_topics.yaml>)

## Offboard mode — takeoff sequence

The PX4 reference example uses a **100 ms timer** (10 Hz, well above
the 2 Hz floor) and gates the mode-switch + arm on having streamed at
least 10 setpoints first. Verbatim core (from
<https://docs.px4.io/main/en/ros2/offboard_control.html>):

```cpp
auto timer_callback = [this]() -> void {
    if (offboard_setpoint_counter_ == 10) {
        // 1) AFTER 10 setpoints have been streamed (~1 s of pre-buffer):
        //    Switch to OFFBOARD: param1=1 (custom), param2=6 (PX4 mode = OFFBOARD)
        publish_vehicle_command(VehicleCommand::VEHICLE_CMD_DO_SET_MODE, 1, 6);
        // 2) Then arm: ARM_DISARM with param1=1
        arm();
    }
    // Always stream both, every cycle:
    publish_offboard_control_mode();   // {position=true, velocity=false, ...}
    publish_trajectory_setpoint();     // {position={0,0,-5}, yaw=-PI}
    if (offboard_setpoint_counter_ < 11) offboard_setpoint_counter_++;
};
```

`publish_vehicle_command` builds a `VehicleCommand`. For arming:

```cpp
VehicleCommand msg{};
msg.command = VehicleCommand::VEHICLE_CMD_COMPONENT_ARM_DISARM; // 400
msg.param1 = 1.0f;  // 1=arm, 0=disarm
msg.target_system = 1; msg.target_component = 1;
msg.source_system = 1; msg.source_component = 1;
msg.from_external = true;
msg.timestamp = this->get_clock()->now().nanoseconds() / 1000;
```

`VehicleCommand` constants relevant here:

| Constant | ID | Use |
|---|---|---|
| `VEHICLE_CMD_DO_SET_MODE` | 176 | Mode change. `param1=1`, `param2=6` → OFFBOARD. `param2=4` → AUTO. |
| `VEHICLE_CMD_COMPONENT_ARM_DISARM` | 400 | `param1=1` arm / `0` disarm; `param2=21196` is the magic "force" cookie. |
| `VEHICLE_CMD_NAV_TAKEOFF` | 22 | `param7=alt`. Used in AUTO mode, **not** OFFBOARD. |
| `VEHICLE_CMD_NAV_LAND` | 21 | |
| `VEHICLE_CMD_NAV_RETURN_TO_LAUNCH` | 20 | |

(Source: <https://docs.px4.io/main/en/msg_docs/VehicleCommand.html>)

### Failure modes the docs explicitly call out

- *"Maintain ≥ 2 Hz publication rate or vehicle exits offboard mode"*
  — if your ROS 2 node hangs for > 500 ms PX4 drops out of OFFBOARD
  into the failsafe configured by `COM_OBL_RC_ACT` / `COM_OF_LOSS_T`.
  (Source:
  <https://docs.px4.io/main/en/flight_modes_mc/offboard.html>)
- *"DO_SET_MODE rejected because no setpoints streaming"* — PX4
  refuses to enter OFFBOARD until setpoints have been arriving for
  ~1 s. This is why the example pre-streams 10 of them.
- **Arming denied silently** if `pre_flight_checks_pass=false` on
  `VehicleStatus`. Always check `VehicleCommandAck` for the result.

## QoS profile — the silent-failure trap

PX4's `/fmu/out/*` publishers use the DDS *sensor data* QoS profile.
ROS 2 subscribers must match or **they will silently receive nothing**
(mismatched reliability is not a fatal-but-loud failure in DDS).

```cpp
#include <rclcpp/qos.hpp>

rmw_qos_profile_t qos_profile = rmw_qos_profile_sensor_data;
auto qos = rclcpp::QoS(
    rclcpp::QoSInitialization(qos_profile.history, 5),
    qos_profile);

auto sub = create_subscription<px4_msgs::msg::VehicleLocalPosition>(
    "/fmu/out/vehicle_local_position", qos,
    [](px4_msgs::msg::VehicleLocalPosition::SharedPtr m){ /* ... */ });
```

Expands to:

- **Reliability**: Best Effort (drop allowed; no retransmit).
- **Durability**: Volatile (no late-joiner replay).
- **History**: Keep Last, depth 5.

**Symptom of getting this wrong**:
`ros2 topic echo /fmu/out/vehicle_status` in the terminal works (the
CLI defaults to BestEffort fallback), but your C++/Python subscriber
callback never fires. Always wrap in the sensor-data QoS.

`/fmu/in/*` publishing from ROS 2 → PX4 is more lenient; standard
`rclcpp::QoS(10)` (default Reliable) generally works, but mirroring
sensor-data QoS on the publisher side is the safe default.

## MAVLink fallback (QGroundControl) for SITL UX

uXRCE-DDS and MAVLink coexist on the same PX4 instance. SITL by
default opens MAVLink on:

- **UDP 14550** — the QGC discovery port.
- **UDP 14580** — the offboard port.

You can therefore:

- Run your control logic over uXRCE-DDS (port 8888).
- Run QGroundControl in parallel on UDP 14550 for a map view, manual
  arm/disarm button, parameter editor, and live MAVLink telemetry.

**QGC install on Ubuntu 24.04**
(<https://docs.qgroundcontrol.com/master/en/qgc-user-guide/getting_started/download_and_install.html>):

```bash
sudo usermod -aG dialout "$(id -un)"
sudo systemctl mask --now ModemManager.service   # optional but common
sudo apt install gstreamer1.0-plugins-bad gstreamer1.0-libav gstreamer1.0-gl -y
sudo apt install python3-gi python3-gst-1.0 -y
sudo apt install libfuse2 -y
sudo apt install libxcb-xinerama0 libxkbcommon-x11-0 libxcb-cursor-dev -y

wget https://d176tv9ibo4jno.cloudfront.net/latest/QGroundControl-x86_64.AppImage
chmod +x QGroundControl-x86_64.AppImage
./QGroundControl-x86_64.AppImage
```

(Re-login after `usermod` so dialout membership takes effect.)

QGC autodetects SITL on UDP 14550 within seconds of `make px4_sitl
gz_x500` running. Use it during early bring-up as the manual-override
path: arm via the GUI, set OFFBOARD via the GUI's flight-mode dropdown,
watch your ROS 2 setpoints take over.

**MAVROS** (`sudo apt install ros-jazzy-mavros ros-jazzy-mavros-extras`)
is install-able but **not recommended for new code** — uXRCE-DDS
supersedes it.

## Sources

- PX4 ROS 2 user guide: <https://docs.px4.io/main/en/ros2/user_guide.html>
- uXRCE-DDS middleware: <https://docs.px4.io/main/en/middleware/uxrce_dds.html>
- Offboard control example: <https://docs.px4.io/main/en/ros2/offboard_control.html>
- Multicopter offboard mode: <https://docs.px4.io/main/en/flight_modes_mc/offboard.html>
- Flight modes catalog: <https://docs.px4.io/main/en/getting_started/flight_modes.html>
- dds_topics.yaml (canonical topic list):
  <https://github.com/PX4/PX4-Autopilot/blob/main/src/modules/uxrce_dds_client/dds_topics.yaml>
- Message references:
  - VehicleStatus: <https://docs.px4.io/main/en/msg_docs/VehicleStatus.html>
  - VehicleCommand: <https://docs.px4.io/main/en/msg_docs/VehicleCommand.html>
  - OffboardControlMode: <https://docs.px4.io/main/en/msg_docs/OffboardControlMode.html>
  - TrajectorySetpoint: <https://docs.px4.io/main/en/msg_docs/TrajectorySetpoint.html>
  - VehicleLocalPosition: <https://docs.px4.io/main/en/msg_docs/VehicleLocalPosition.html>
  - FailsafeFlags: <https://docs.px4.io/main/en/msg_docs/FailsafeFlags.html>
- Repos:
  - <https://github.com/PX4/px4_msgs>
  - <https://github.com/PX4/px4_ros_com>
  - <https://github.com/eProsima/Micro-XRCE-DDS-Agent>
- QGroundControl install:
  <https://docs.qgroundcontrol.com/master/en/qgc-user-guide/getting_started/download_and_install.html>
- MAVROS (legacy): <https://docs.px4.io/main/en/ros/mavros_installation.html>
