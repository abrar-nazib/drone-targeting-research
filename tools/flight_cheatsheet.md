# Flight cheatsheet — driving the SITL drone around

Three control paths in increasing power. Pick by what you're doing.

| Path | Setup | Best for |
|---|---|---|
| **`pxh>` console** | None — already there | Smoke tests, mode switches, parameter tweaks |
| **QGroundControl** | One AppImage download | Manual flight, click-to-fly, mission upload, parameter GUI |
| **ROS 2 + uXRCE-DDS** | Build agent + `px4_msgs` | The actual research path — programmatic offboard control |

---

## 1. `pxh>` console — what you can do right now

These are the commands available inside PX4's `pxh>` shell after launching with `./tools/run_px4_sitl.sh`. No external setup.

### Arming and basic flight

```
commander arm                   # arm (preflight checks must pass)
commander arm -f                # arm bypassing preflight (DEV ONLY)
commander disarm                # disarm (rejects if airborne)
commander disarm -f             # disarm even if airborne (kills motors)

commander takeoff               # auto takeoff to default 2.5 m
commander land                  # auto land at current position
```

### Flight mode switching

```
commander mode <mode>
```

Verified mode strings (from `commander` `--help`):

| Mode | What it does |
|---|---|
| `auto:takeoff` | Auto takeoff to `MIS_TAKEOFF_ALT` (default 2.5 m) |
| `auto:land` | Auto land at current position |
| `auto:rtl` | Return to launch (fly home, then land) |
| `auto:loiter` | Hold current position (hover) |
| `auto:mission` | Execute uploaded mission |
| `posctl` | Position-hold (sticks command horizontal velocity) |
| `position:slow` | Slow position mode |
| `altctl` | Altitude-hold (sticks command roll/pitch + Z velocity) |
| `stabilized` | Self-leveling (sticks command roll/pitch angle) |
| `acro` | Direct rate control (FPV mode) |
| `manual` | Pass-through |
| `offboard` | External setpoint stream (ROS 2 / MAVSDK takes over) |

Without RC sticks or QGC, only the `auto:*` modes are useful from `pxh>`. The others wait for stick input that doesn't exist.

### Origin (GPS / EKF home)

```
commander set_ekf_origin <lat> <lon> <alt>   # set origin at runtime
```

### What's NOT in `commander`

Verified by `commander --help` on PX4 v1.16:

- **No `set_heading`** — to rotate the drone in place from `pxh>`,
  you can't. Use QGroundControl (drag the heading arrow) or send a
  yaw setpoint via offboard control.
- **No `safety` or `termination`** — for emergency disarm in air use
  `commander disarm -f`. For "kill outputs" use `commander lockdown on`.
- **No goto / move-to-position** commands. See QGC or MAVSDK below.

### Other top-level commands worth knowing

```
commander check                 # run + report all preflight checks
commander calibrate <type>      # type = mag|baro|accel|gyro|level|esc|airspeed
commander lockdown on|off       # latch outputs off (kill switch)
commander pair                  # binding for radio receiver (real HW)
commander status                # print state info
commander stop                  # stop the commander module
```

### State inspection (read-only)

```
listener vehicle_local_position 1    # NED x/y/z, validity flags, heading
listener vehicle_global_position 1   # WGS84 lat/lon/alt
listener vehicle_status              # arming_state, nav_state, failsafe
listener failsafe_flags              # every preflight blocker as a flag
listener sensor_combined 1           # raw fused IMU
listener vehicle_gps_position 1      # GPS fix, sat count
listener estimator_status            # EKF health
listener vehicle_attitude 1          # quaternion FRD->NED
listener battery_status              # sim battery state
uorb top                             # per-topic Hz / lost / queue
```

The `1` suffix prints one frame; omit for a single recent message; pass `N` for N frames.

### Parameter tweaks (most-used during development)

```
param show MIS_TAKEOFF_ALT           # default takeoff altitude (m)
param set MIS_TAKEOFF_ALT 5.0        # change to 5 m
param save                           # persist

param show MPC_*VEL*                 # all velocity-related params
param show COM_RCL_EXCEPT            # which modes bypass RC requirement
```

For the full `pxh>` reference see
[`.claude/skills/px4-gazebo/reference/02_launching_and_console.md`](../.claude/skills/px4-gazebo/reference/02_launching_and_console.md).

### What `pxh>` CANNOT do

- "Go to position (x, y, z)" — no goto command in commander.
- "Fly forward 5 m" — no relative-move command.
- "Strafe / rotate while moving" — needs a setpoint stream.

For these, use QGroundControl (GUI) or the MAVSDK / ROS 2 paths below.

---

## 2. QGroundControl — manual flight + click-to-fly + missions

The fastest way to fly around interactively. Drag the drone on the map, draw missions visually, see telemetry overlays. Works alongside PX4 SITL — no SITL changes needed (PX4 always opens MAVLink on UDP 14550 for QGC).

### Install (one-time, ~150 MB)

```bash
sudo apt install -y libfuse2 libxcb-xinerama0 libxkbcommon-x11-0 libxcb-cursor-dev \
                    gstreamer1.0-plugins-bad gstreamer1.0-libav gstreamer1.0-gl \
                    python3-gi python3-gst-1.0
sudo usermod -aG dialout "$(id -un)"   # one-time; relogin after

cd ~
wget https://d176tv9ibo4jno.cloudfront.net/latest/QGroundControl-x86_64.AppImage
chmod +x QGroundControl-x86_64.AppImage
```

### Run

```bash
# In one terminal:
./tools/run_px4_sitl.sh

# In another terminal:
~/QGroundControl-x86_64.AppImage
```

QGC autodetects the SITL on UDP 14550 within ~5 sec. You'll see the drone on a map (Zürich, since that's our `<spherical_coordinates>` origin).

### Quick actions (on the QGC main map)

- **Slide-to-arm** at the top
- **Takeoff**: click the arming/takeoff toolbar button → slide to confirm
- **Click anywhere on map** → "Go to location" → drone flies there at default altitude
- **Drag drone icon** → drone follows
- **Fly View → Action button** → Land, RTL, Pause, Change Altitude
- **Plan View** (left sidebar) → draw a mission with waypoints, upload, then start
- **Vehicle Setup → Parameters** → search any param, edit, persist

### Virtual joystick

Settings → Application Settings → General → "Virtual Joystick" enable. Two on-screen sticks for manual flight (Acro / Position / Stabilized modes).

---

## 3. MAVSDK Python — quick programmatic control

For "fly this script" without the full ROS 2 stack. MAVSDK is a Python wrapper over MAVLink. Good for prototyping the landing controller before wiring up uXRCE-DDS.

### Install

```bash
pip install --user mavsdk
```

### Example: arm, takeoff, fly a 10×10 m square at 3 m, land

Save as `tools/example_square_flight.py`:

```python
import asyncio
from mavsdk import System

async def fly():
    drone = System()
    await drone.connect(system_address="udp://:14540")  # PX4 SITL onboard

    print("Waiting for connection…")
    async for state in drone.core.connection_state():
        if state.is_connected:
            break

    print("Arming…");        await drone.action.arm()
    print("Taking off…");    await drone.action.set_takeoff_altitude(3.0)
    await drone.action.takeoff()
    await asyncio.sleep(8)

    print("Going to corners…")
    # NED offsets in metres from EKF origin
    for n, e in [(10, 0), (10, 10), (0, 10), (0, 0)]:
        await drone.action.goto_location(
            await _origin_lat_offset(drone, n),
            await _origin_lon_offset(drone, e),
            3.0, 0.0,   # alt MSL, yaw deg
        )
        await asyncio.sleep(8)

    print("Landing…");       await drone.action.land()

asyncio.run(fly())
```

(Helpers omitted for brevity — MAVSDK has a richer `offboard` API for direct setpoint streaming; see <https://mavsdk.mavlink.io/main/en/python/quickstart.html>.)

### Run

```bash
./tools/run_px4_sitl.sh    # in one terminal
python3 tools/example_square_flight.py   # in another
```

PX4 listens for MAVSDK on **UDP 14540** (the offboard port, separate from QGC's 14550). Both can run simultaneously — fly via QGC OR via script, watch in either UI.

---

## 4. ROS 2 + uXRCE-DDS — the research path

For the actual landing controller (the paper contribution), use uXRCE-DDS. This exposes PX4 uORB topics directly as ROS 2 topics under `/fmu/in/*` and `/fmu/out/*`, with full structural fidelity (no MAVLink translation losses). Lower latency, higher rates, native to ROS 2.

Quick orientation:

- **Install agent**: `MicroXRCEAgent` from source (Jazzy pin = v2.4.3). PX4 SITL auto-starts the client on UDP 8888 — you'll see `INFO [uxrce_dds_client] init UDP agent IP:127.0.0.1, port:8888` in `pxh>`.
- **Build `px4_msgs` + `px4_ros_com`** in your colcon workspace, branch `release/1.16` (must match PX4 firmware version).
- **Frame conventions**: PX4 is **NED + FRD**, ROS 2 is **ENU + FLU**. Z is *down* in PX4. `position = {0, 0, -5}` means 5 m **above** origin.
- **QoS**: `rmw_qos_profile_sensor_data` (Best Effort + Volatile + KeepLast(5)) — wrong QoS = silent receive failure.
- **Offboard takeoff**: stream `OffboardControlMode` + `TrajectorySetpoint` at ≥ 10 Hz for ≥ 1 sec, THEN send `VEHICLE_CMD_DO_SET_MODE` (param2=6 = OFFBOARD) + `VEHICLE_CMD_COMPONENT_ARM_DISARM`.

Full step-by-step + topic catalogue + offboard takeoff template + QoS recipe + frame conversion helpers in
[`.claude/skills/px4-gazebo/reference/06_ros2_uxrce_dds.md`](../.claude/skills/px4-gazebo/reference/06_ros2_uxrce_dds.md).

---

## Recommended path through these

1. **Day 1**: Use `pxh>` to verify takeoff/land works in each world. Done.
2. **Now**: Install QGC (15 min). Fly around the orchard with click-to-fly. Get a visual sense of the world scale, where the trees are, where you'd want a car to drive.
3. **This week**: Drop in MAVSDK Python for the first "drone follows a known target" prototype. Quick iteration without ROS rebuild cycles.
4. **Once the controller stabilises**: Migrate to ROS 2 + uXRCE-DDS for the production landing controller. ROS 2 is what you'll cite in the paper and what other researchers will reproduce.

---

## Common gotchas

- **`Arming denied: Resolve system health failures first`** — see [reference/07 FailsafeFlags decoder](../.claude/skills/px4-gazebo/reference/07_parameters_and_preflight.md#failsafeflags-decoder). The standard SITL "stop complaining" recipe is in [reference/08](../.claude/skills/px4-gazebo/reference/08_troubleshooting.md#one-shot-sitl-stop-complaining-param-block) — already applied to your install.
- **Drone yaws continuously after takeoff** — usually CoM offset from added payload mass. See [reference/05 FPV tuning](../.claude/skills/px4-gazebo/reference/05_fpv_tuning.md).
- **Goto failed silently in MAVSDK** — check `vehicle_status.nav_state` is the mode you expect. MAVSDK's high-level actions silently switch modes.
- **OFFBOARD setpoint stream broke → drone enters failsafe** — PX4 drops out of OFFBOARD if setpoints stop for > 0.5 s. Always stream at ≥ 10 Hz.
