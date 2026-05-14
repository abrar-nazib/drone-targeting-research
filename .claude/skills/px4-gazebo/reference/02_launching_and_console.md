# 02 — Launching & the `pxh>` console

Build targets, every relevant env var, the headless / world-override /
model-override / standalone-Gazebo / multi-vehicle launch patterns, and
the `pxh>` console command set. Pairs with
[01_architecture.md](01_architecture.md) (which explains *why* these
mechanisms exist) and
[03_vehicles_and_worlds.md](03_vehicles_and_worlds.md) (the catalogue
of what targets and worlds exist).

## Build + launch in one step

```bash
source /opt/ros/jazzy/setup.bash       # required (see 01_architecture.md)
export GZ_DISTRO=harmonic              # required
cd /media/abrar/AbrarSSD/ROS/PX4-Autopilot
make px4_sitl gz_x500
```

The `gz_` prefix on the target is what selects the Gazebo Harmonic
backend; `gz_x500` is one of many airframe-specific targets. See
[03_vehicles_and_worlds.md](03_vehicles_and_worlds.md) for the full
table. (Source: <https://docs.px4.io/main/en/sim_gazebo_gz/>)

**Gotcha**: do **not** append `_default` (e.g. `gz_x500_default`) — the
build will appear to work but PX4 will refuse to launch. Use the bare
`gz_x500` form. If you see `ninja: error: unknown target 'gz_x500'`,
run `make distclean` first.

## Critical environment variables

All of these are set **before** `make` (or before invoking the binary
directly).

| Var | Purpose |
|---|---|
| `HEADLESS=1` | Run gz-sim with no GUI client. Reduces VRAM + CPU; **mandatory on this project's RTX 3050 4 GB**. Sensors still render server-side, so cameras still work. |
| `PX4_SIM_SPEED_FACTOR=N` | Run sim at N× wall-clock. Desktops typically reach 6–10×; laptops 3–4×. |
| `PX4_GZ_WORLD=<name>` | Selects an alternate world (`default`, `aruco`, `baylands`, `lawn`, `walls`, `windy`, `moving_platform`, `rover`, `forest`, `frictionless`). Files live in `Tools/simulation/gz/worlds/`. |
| `PX4_GZ_MODEL_POSE="x,y,z,r,p,y"` | Spawn pose (m, rad). Defaults to all zeros. Format also accepts `"x,y"` for just XY. |
| `PX4_SIM_MODEL=<airframe>` | Tells PX4 to **spawn a new model** into Gazebo. E.g. `x500`, `x500_depth`. Mutually exclusive with `PX4_GZ_MODEL_NAME`. |
| `PX4_GZ_MODEL_NAME=<name>` | Tells PX4 to **bind to an existing model already present** in the running gz world. Mutually exclusive with `PX4_SIM_MODEL`. Required for the project's car-landing pattern (drone + car already in the SDF). |
| `PX4_GZ_STANDALONE=1` | PX4 does **not** start gz-sim; assumes the user has launched it elsewhere. Required for multi-vehicle. |
| `PX4_SYS_AUTOSTART=<id>` | Selects the airframe init script. **Mandatory** for direct binary invocation (see "Direct binary invocation" below). |
| `PX4_SIMULATOR=gz` | Tells PX4 the simulator backend is gz. Normally set inside the airframe file; rarely needed in env. |
| `PX4_GZ_SIM_RENDER_ENGINE=ogre` | Falls back from OGRE 2 (default) to OGRE 1. Use on VMs / weak iGPUs that crash the OGRE 2 path. |
| `PX4_GZ_FOLLOW_OFFSET_X|Y|Z` | Offset of the chase camera (GUI mode only). |
| `GZ_DISTRO=harmonic` | **Required when building** so PX4's CMake finds gz-transport / gz-sim8. Without it `gz_bridge` fails to compile. |
| `GZ_SIM_RESOURCE_PATH=...` | Colon-separated paths gz-sim searches for SDF models / worlds. Append your custom world dirs here so `PX4_GZ_WORLD` can find them. |
| `PX4_HOME_LAT / LON / ALT` | Custom takeoff location. Overrides the spawn point but not the world reference frame in `<spherical_coordinates>`. |
| `PX4_NET_INTERFACE=<iface>` | Pin MAVLink to a specific NIC (containers, multi-NIC). |
| `PX4_GZ_PLATFORM_VEL` / `PX4_GZ_PLATFORM_HEADING_DEG` | Speed / heading for the `moving_platform` world. |

(All sourced from <https://docs.px4.io/main/en/sim_gazebo_gz/>; `GZ_DISTRO`
documented in PX4's CMake.)

### "Model override" vs "world override" — vocabulary clarifier

- **World override** = `PX4_GZ_WORLD=<world>` — change which `.sdf`
  world file gz-sim loads. The vehicle is still the one the make target
  nominally spawns.
- **Model override** has two flavours:
  - **Spawn-a-new-model**: `PX4_SIM_MODEL=x500_depth` — PX4 tells gz to
    add this model into the running world. Used when the world doesn't
    contain the vehicle.
  - **Bind-to-existing-model**: `PX4_GZ_MODEL_NAME=<existing_model>` —
    used when the SDF world already contains the vehicle (or when
    another process already spawned it). Required for the project's
    car-landing pattern: SDF holds drone + car, gz-sim is launched by
    the project's launcher, PX4 binds to the drone.

## Launch patterns

### Default — single x500 in the empty world, with gz GUI

```bash
make px4_sitl gz_x500
```

(On this hardware: don't actually do this — see `HEADLESS=1` below.)

### Headless — sensors + physics still run, no GUI

```bash
HEADLESS=1 make px4_sitl gz_x500
```

**Default mode for this project.** GUI is never needed at the PX4 layer
because all introspection is via uXRCE-DDS topics + RViz on the ROS 2
side.

### Custom world

```bash
PX4_GZ_WORLD=baylands HEADLESS=1 make px4_sitl gz_x500
```

For a project-supplied world, prepend its directory to
`GZ_SIM_RESOURCE_PATH`:

```bash
export GZ_SIM_RESOURCE_PATH=/media/abrar/AbrarSSD/ROS/drone_targeting_research/ros2_ws/src/drone_sim_bringup/worlds:$GZ_SIM_RESOURCE_PATH
PX4_GZ_WORLD=orchard_labeled HEADLESS=1 make px4_sitl gz_x500
```

The world SDF must declare `<world name="orchard_labeled">` matching
the `PX4_GZ_WORLD` value. See
[04_custom_airframes_models_worlds.md](04_custom_airframes_models_worlds.md)
for required SDF blocks.

### Spawn at non-zero pose

```bash
PX4_GZ_MODEL_POSE="2,3,0.5,0,0,1.5708" HEADLESS=1 make px4_sitl gz_x500
```

(2 m east, 3 m north, 0.5 m up, yawed 90°.)

### Direct binary invocation (the form everything decomposes to)

```bash
PX4_SYS_AUTOSTART=4001 PX4_SIM_MODEL=x500 \
  ./build/px4_sitl_default/bin/px4
```

Useful when launching from a script, a launch file, or a debugger.

### Standalone Gazebo (used for multi-vehicle and SDF-controlled scenes)

Terminal 1 — start gz-sim with PX4's helper:

```bash
python /media/abrar/AbrarSSD/ROS/PX4-Autopilot/Tools/simulation/gz/simulation-gazebo
# or directly:
gz sim -r -v 4 default.sdf --server-config /media/abrar/AbrarSSD/ROS/PX4-Autopilot/Tools/simulation/gz/server.config
```

(See [01_architecture.md](01_architecture.md) for why
`--server-config` is mandatory — without it sensors don't publish.)

Terminal 2 — start PX4 attached to it:

```bash
PX4_GZ_STANDALONE=1 HEADLESS=1 make px4_sitl gz_x500
```

PX4 will print a wait-warning until it sees the gz-transport. This
pattern is the foundation for the project's "drone + moving car" world
— you author one SDF with both entities, launch gz-sim from your
project's launcher, then `PX4_GZ_MODEL_NAME=x500` to bind PX4 to the
drone instance.

## Multi-vehicle pattern (overview)

Pattern: **one standalone gz-sim**, **many PX4 binaries**, each
distinguished by `-i <instance>`. When `PX4_SIM_MODEL` is set,
`gz_bridge` auto-suffixes the model name with the instance to avoid
collisions: model becomes `${PX4_SIM_MODEL}_${instance}`. MAVLink
remote ports are allocated sequentially from 14540–14549 per instance;
ground-control connections still arrive on 14550.
(Source: <https://docs.px4.io/main/en/sim_gazebo_gz/multi_vehicle_simulation.html>)

Build once:

```bash
make px4_sitl
```

Terminal 1 — first vehicle, also brings up gz-sim (no `PX4_GZ_STANDALONE`):

```bash
PX4_SYS_AUTOSTART=4001 PX4_SIM_MODEL=x500 \
  ./build/px4_sitl_default/bin/px4 -i 1
```

Terminal 2 — second vehicle, attaches to existing gz-sim:

```bash
PX4_GZ_STANDALONE=1 PX4_SYS_AUTOSTART=4001 PX4_GZ_MODEL_POSE="0,1" \
  PX4_SIM_MODEL=x500 ./build/px4_sitl_default/bin/px4 -i 2
```

Terminal 3 — different airframe (Cessna):

```bash
PX4_GZ_STANDALONE=1 PX4_SYS_AUTOSTART=4003 PX4_GZ_MODEL_POSE="0,2" \
  PX4_SIM_MODEL=rc_cessna ./build/px4_sitl_default/bin/px4 -i 3
```

For the project's drone + rover pattern, instance 1 is the drone (PX4),
the rover doesn't need a PX4 instance at all if it's using
`gz-sim-trajectory-follower-system` or being driven via `gz topic`.

## The `pxh>` console

Once PX4 is up, the controlling terminal becomes the `pxh>` shell —
same shell as a Pixhawk MAVLink console, exposing every loaded module
as a top-level command via `bin/px4-alias.sh`.

### `commander` — state machine, arming, mode switching

Verified against `commander --help` on PX4 v1.16 SITL (gz_x500):

```
commander arm                      # arm (preflight checks must pass)
commander arm -f                   # arm bypassing preflight (DEV ONLY)
commander disarm                   # disarm (rejects if airborne)
commander disarm -f                # disarm even if airborne (kills motors)
commander takeoff                  # auto takeoff to MIS_TAKEOFF_ALT (default 2.5 m)
commander land                     # auto land at current position
commander mode <mode>              # mode ∈ {manual, acro, offboard, stabilized,
                                   #         altctl, posctl, position:slow,
                                   #         auto:mission, auto:loiter, auto:rtl,
                                   #         auto:takeoff, auto:land}
commander check                    # run + report all preflight checks
commander calibrate <type>         # type ∈ {mag, baro, accel, gyro, level, esc, airspeed}
commander lockdown on|off          # latch outputs off (kill switch)
commander set_ekf_origin <lat> <lon> <alt>   # set GPS / EKF origin at runtime
commander transition               # VTOL transition
commander pair                     # bind radio receiver (real HW)
commander status                   # print state info
commander stop                     # stop the commander module
```

**Note**: PX4 mode names use `:` between hierarchy levels (`auto:rtl`,
`position:slow`), not `_`. Earlier drafts of this file (and any
agent-summarised docs you might find) listed `position_slow` /
`auto_takeoff` etc. — those are wrong and the binary will reject them
with `unknown command`.

**Commands explicitly NOT in v1.16's `commander`:**
- `commander set_heading` — does not exist. To rotate the drone from
  `pxh>`, switch to a setpoint-streaming control path (offboard, QGC,
  MAVSDK). There is no built-in pxh> "rotate" command.
- `commander safety on|off` — does not exist. For emergency disarm in
  air use `commander disarm -f`. For latched output cutoff use
  `commander lockdown on`.
- `commander termination on|off` — does not exist. Use `lockdown` for
  the same effect.
- No `goto` / `move-to-position` commands. Movement requires QGC,
  MAVSDK, or ROS 2 offboard.

(Source: `commander --help` from a running PX4 v1.16 SITL session.
The PX4 docs page <https://docs.px4.io/main/en/modules/modules_system.html>
exists but is auto-generated and has been out of sync with the binary
in past releases — when in doubt, run `commander --help` and trust the
binary.)

**`commander check` does not list specific failures** in the v1.16
console output — it just prints `Preflight check: FAILED` or
`PASSED`. To see what's actually failing, use `listener failsafe_flags`
(the actual blocker bits) and the decoder in
[07_parameters_and_preflight.md](07_parameters_and_preflight.md).

### `listener` — print recent messages on a uORB topic

```
listener <topic>                   # one frame
listener <topic> <N>               # N frames
listener sensor_combined 5
listener vehicle_local_position 1
listener failsafe_flags
listener vehicle_status
listener vehicle_gps_position
listener estimator_status
```

(Source: <https://docs.px4.io/main/en/middleware/uorb.html>)

### `param` — runtime parameter introspection / mutation

```
param show                         # all params
param show COM_*                   # filtered (glob)
param show -c                      # only params changed from default
param set COM_RC_IN_MODE 1         # set + persist (param save in flight)
param save                         # explicit persist
param load <file>                  # load full param dump
param compare <NAME> <VAL>         # exit 0 if equal — useful in init scripts
param touch <NAME>                 # mark used (forces export to dds_topics)
param reset <NAME>                 # reset single param to default
param reset_all                    # nuke RAM state
param status                       # subsystem stats
```

(Source: <https://docs.px4.io/main/en/debug/mavlink_shell.html>)

### Other useful built-ins

```
ver                # firmware version + git hash
top                # per-task CPU + stack
dmesg              # boot log; -f to tail
uorb top           # per-topic Hz / lost / queue (essential for sensor flow debugging)
shutdown           # clean exit; PX4 reaps the gz client (if it spawned it)
```

### Where the binary lives

`build/px4_sitl_default/bin/px4`. It executes `etc/init.d-posix/rcS`
from the build's `etc/` directory; `rcS` reads `PX4_SYS_AUTOSTART` and
sources the matching `init.d-posix/airframes/<id>_<name>` script,
which in turn loads `gz_bridge`, EKF2, sensors, mc_*_control /
fw_*_control modules, mavlink instances, etc.
(Source: <https://docs.px4.io/main/en/concept/system_startup.html>)

## Sources

- PX4 sim Gazebo overview, env vars, build targets, worlds:
  <https://docs.px4.io/main/en/sim_gazebo_gz/>
- Multi-vehicle pattern, standalone gz, instance numbering:
  <https://docs.px4.io/main/en/sim_gazebo_gz/multi_vehicle_simulation.html>
- Simulator architecture, lockstep:
  <https://docs.px4.io/main/en/simulation/>
- System startup, `rcS`, `init.d-posix/`, `PX4_SYS_AUTOSTART`,
  `px4-alias.sh`:
  <https://docs.px4.io/main/en/concept/system_startup.html>
- `commander` subcommands and other system utilities:
  <https://docs.px4.io/main/en/modules/modules_system.html>
- uORB, `listener`, `uorb top`:
  <https://docs.px4.io/main/en/middleware/uorb.html>
- MAVLink shell / `pxh>` commands (`ver`, `top`, `dmesg`, `param show/set`):
  <https://docs.px4.io/main/en/debug/mavlink_shell.html>
