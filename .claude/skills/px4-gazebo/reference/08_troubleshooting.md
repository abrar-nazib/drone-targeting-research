# 08 — Troubleshooting

The recurring SITL failure modes on this hardware, with diagnosis
recipes. Pairs with
[07_parameters_and_preflight.md](07_parameters_and_preflight.md)
(field decoder) and [01_architecture.md](01_architecture.md)
(why these failures happen).

## Symptom 1 — lockstep starvation (`Interrupted system call` flood)

**Symptoms** in the `pxh>` console:

```
NodeShared::Publish() Error: Interrupted system call
ERROR [vehicle_imu] 0 - gyro 1310988 timestamp error timestamp_sample: ...
ERROR [vehicle_imu] 0 - accel 1310988 timestamp error timestamp_sample: ...
WARN  [health_and_arming_checks] Preflight Fail: ekf2 missing data
```

— possibly thousands of lines per second.

**Root cause**: the Gazebo OGRE 2 GUI render loop is starving the
physics step. Lockstep falls behind, gz-transport publish syscalls get
interrupted by signals, IMU samples arrive with timestamps PX4 rejects,
EKF2 never receives consistent data.

**On this project's RTX 3050 4 GB iGPU this is expected, not a bug**.
The fix ladder, in order of preference:

1. **Restart with `HEADLESS=1`** — kills the GUI client entirely. Server
   still renders sensors (cameras still work via uXRCE-DDS). This is
   the project default and resolves the issue completely.

   ```bash
   shutdown                                         # in pxh>
   source /opt/ros/jazzy/setup.bash
   export GZ_DISTRO=harmonic
   HEADLESS=1 make px4_sitl gz_x500
   ```

2. **`PX4_GZ_SIM_RENDER_ENGINE=ogre`** — fall back from OGRE 2 to OGRE
   1 if you actually need the GUI. Older renderer, lower demands. Used
   on weak iGPUs and VMs.

3. **Build PX4 with lockstep disabled** — the heavy hammer. Edit
   `boards/px4/sitl/default.px4board`:
   ```
   set(ENABLE_LOCKSTEP_SCHEDULER no)
   ```
   Then `make distclean && make px4_sitl gz_x500`. PX4 runs against the
   POSIX scheduler in real time. Trade-off: lose accelerated time
   (`PX4_SIM_SPEED_FACTOR > 1.0` no longer works) and bit-exact
   reproducibility.

There is no runtime toggle for lockstep — it's a compile-time scheduler
choice.

## Symptom 2 — "Arming denied: Resolve system health failures first"

**Symptom** at the `pxh>` console after `commander arm` or
`commander takeoff`:

```
INFO  [tone_alarm] notify negative
WARN  [commander] Arming denied: Resolve system health failures first
```

`commander check` returns just `Preflight check: FAILED` without
listing the cause.

**Cause**: one or more `FailsafeFlags` fields is set. The console log
suppresses details; you have to subscribe to the topic to see them.

### Diagnosis recipe

```
pxh> listener failsafe_flags
```

Then look at every **non-zero** field and cross-reference with the
[FailsafeFlags decoder](07_parameters_and_preflight.md#failsafeflags-decoder).
The most common SITL blockers and their fixes:

| Non-zero field | Fix |
|---|---|
| `manual_control_signal_lost: True` (and you want OFFBOARD) | `param set COM_RCL_EXCEPT 4; param save` |
| `gcs_connection_lost: True` | Either start QGC OR `param set NAV_DLL_ACT 0; param save` |
| `local_position_invalid: True` | Wait longer for GPS / EKF2; if persists, see EKF2 tree below |
| `attitude_invalid: True` | Wait longer; if persists, IMU isn't reaching PX4 — see EKF2 tree |
| `home_position_invalid: True` | GPS hasn't locked. Wait, or `commander set_ekf_origin <lat> <lon> <alt>` |
| `battery_warning: 1` | `param set BAT_LOW_THR 0.05; param set BAT_CRIT_THR 0.02; param save` |

### One-shot SITL "stop complaining" param block

```
param set COM_RCL_EXCEPT 4
param set COM_ARM_WO_GPS 1
param set NAV_DLL_ACT 0
param set NAV_RCL_ACT 0
param set COM_ARM_MAG_STR 0
param set COM_DISARM_PRFLT -1
param save
```

These are safe for the rest of SITL bring-up. Re-run `commander check`
afterward.

### Last-resort: bypass preflight

```
commander arm -f         # arm even if preflight failed
```

**Use only when you understand why it failed** — bypassing a real bug
just delays the crash.

## Symptom 3 — EKF2 "missing data" (diagnosis tree)

**Symptom**: `vehicle_local_position.xy_valid` and `z_valid` stay
`false`, `failsafe_flags.local_position_invalid=true` indefinitely.

Diagnosis order, top-to-bottom — stop at the first failing rung.

### Step 1 — are the raw simulator sensor topics arriving in PX4?

```
listener sensor_combined        # IMU at ~250 Hz expected
listener sensor_gps             # GPS at 5 Hz expected  (note: type SensorGps)
listener vehicle_magnetometer   # mag at 50 Hz expected
listener vehicle_air_data       # baro at 50 Hz expected
```

If any say `never published`, the **gz_bridge** isn't forwarding that
sensor. Check the model SDF (`Tools/simulation/gz/models/<name>/model.sdf`)
has `<sensor type="...">` entries with the **hardcoded names** PX4
requires (`imu_sensor`, `magnetometer_sensor`, `air_pressure_sensor`,
`navsat_sensor` on `base_link`). Many community-modified SDFs strip
sensors accidentally; EKF2 then waits forever. See
[04_custom_airframes_models_worlds.md](04_custom_airframes_models_worlds.md).

### Step 2 — is gz_bridge running?

```
gz_bridge status
```

If "not running": `param set SIM_GZ_EN 1; param save; reboot`.

### Step 3 — are sensor publication rates above EKF2 minimums?

EKF2 minimums per
<https://docs.px4.io/main/en/advanced_config/tuning_the_ecl_ekf.html>:

- IMU ≥ 100 Hz
- Mag ≥ 5 Hz
- Height source ≥ 5 Hz

If gz_bridge publishes IMU at 50 Hz (some custom worlds slow physics),
EKF2 silently rejects. Check the sensor `<update_rate>` in the model
SDF — should be 250 for IMU.

### Step 4 — has EKF2 itself initialized?

```
ekf2 status
listener estimator_status
```

`estimator_status.pre_flt_fail_innov_*` flags tell you which fusion
gate is rejecting samples (typically mag heading at boot if model is
spawned at a yaw the mag plugin disagrees with).

### Step 5 — is GPS origin set?

```
listener vehicle_gps_position
```

If `fix_type < 3` (no 3D fix) for more than ~30 s → either NavSat
plugin isn't in the SDF, or `SIM_GPS_USED` is set to 0. Force it:
`param set SIM_GPS_USED 10; param save`.

### Step 6 — is the EKF2 fusion mask asking for sensors you don't have?

```
param show EKF2_AID_MASK
```

Bits: 1=GPS, 2=optical flow, 4=ext vision pos, 8=ext vision yaw,
16=ext vision vel, 128=GPS yaw. If a bit is set for a sensor that
doesn't exist in this world, EKF2 stalls. Default `1` (GPS only) is
correct for stock SITL.

### Step 7 — is the magnetometer fighting?

```
param set EKF2_MAG_TYPE 5
param save
```

Disables mag entirely (heading from GPS only). Useful when an outdoor
SITL world has wonky mag declination.

### Step 8 — is the EKF height reference wrong?

```
param show EKF2_HGT_REF        # 0=Baro, 1=GNSS, 2=Range, 3=Vision
param set EKF2_HGT_REF 0       # fall back to baro if GPS alt is bad
param save
```

### Empirical convergence times

With all sensors healthy, EKF2 reaches `xy_valid=true` and
`pre_flight_checks_pass=true` in **6–12 s** after sim start. Anything
> 30 s indicates a real problem — start at step 1.

## Symptom 4 — build error: "Gazebo simulation dependencies not found"

**Symptom** during `make px4_sitl gz_x500`:

```
CMake Error at src/modules/simulation/gz_bridge/CMakeLists.txt:
  Gazebo simulation dependencies not found!
```

**Cause**: PX4's CMake can't find `gz-transport13` / `gz-sim8`. Either
ROS isn't sourced or `GZ_DISTRO` isn't set.

**Fix**:

```bash
source /opt/ros/jazzy/setup.bash
export GZ_DISTRO=harmonic
make px4_sitl gz_x500
```

**If a stale CMake cache remains** from a prior failed attempt, refresh
it before retrying:

```bash
cd build/px4_sitl_default
cmake .                         # re-detect with new env
cd -
make px4_sitl gz_x500
```

(The cache will have `gz-transport_DIR-NOTFOUND` from the failed run;
`cmake .` re-runs detection with the new env vars in scope.)

## Symptom 5 — texture not loading from `model://` URI

**Symptom**: model spawns but appears in solid grey / pink (the
default-material fallback). Console may show:

```
[Err] [SystemPaths.cc] Could not resolve URI [model://NAME/meshes/foo.png]
```

**Cause**: `model://` URI doesn't resolve in `GZ_SIM_RESOURCE_PATH`.
Common with old OpenRobotics car models from Fuel.

**Fix** (already implemented in the project's
`tools/fix_fuel_textures.py`):

1. Symlink texture files into the `meshes/` directory.
2. Patch `.mtl` files to strip `model://NAME/` URI prefixes, leaving
   bare basenames.

```bash
cd ~/.gz/fuel/.../<model>/meshes
ln -sf ../materials/textures/*.png .
sed -i 's|model://[^/]*/meshes/||g' *.mtl
```

For new models, just run `tools/fix_fuel_textures.py` after Fuel
download.

## Symptom 6 — orphan `px4` process holding port 8888

**Symptom**: second SITL launch fails with

```
ERROR [uxrce_dds_client] init failed, error: bind: Address already in use
```

or `MicroXRCEAgent` reports `Address already in use` on port 8888.

**Cause**: a previous `px4` process didn't clean up.

**Fix**:

```bash
pkill -9 px4
pkill -9 gz
pkill -9 ruby                    # gz spawns ruby helpers
ss -ulpn | grep 8888             # confirm nothing is bound
```

Then retry the launch.

## Symptom 7 — "Vertical position estimate timeout" mid-flight

**Symptom**: drone is flying, then suddenly:

```
ERROR [mc_pos_control] Vertical position estimate timeout
```

and PX4 enters failsafe (descent / land / RTL).

**Cause**: same root cause as Symptom 1 — gz-sim is stalling
mid-flight, often because the GUI is choking on a high-poly model
that came into view (Fuel buildings, dense forest).

**Fix**: either run headless (always, on this hardware), or simplify
the world (fewer Fuel includes, lower sensor update rates,
`PX4_SIM_SPEED_FACTOR=0.5` to give physics breathing room).

## Symptom 8 — `commander takeoff` succeeds but drone immediately lands

**Symptom**: takeoff command accepted, drone lifts a few cm, then
auto-lands. Console:

```
INFO  [vehicle_land_detected] Landing detected
```

**Cause**: the land detector triggered on the spawn — usually because
the airframe spawned slightly inside / on top of an obstacle, or the
physics inertia tensor is unrealistic for the scaled mass.

**Fix**: spawn at a known clear pose with explicit altitude:

```bash
PX4_GZ_MODEL_POSE="0,0,0.5,0,0,0" HEADLESS=1 make px4_sitl gz_x500
```

(0.5 m above ground.) Or relax the land detector params:
`param set LNDMC_TRIG_TIME 5.0` (default 0.3 s).

## Quick-reference index of failure → fix

| Failure mode | First thing to try |
|---|---|
| `Interrupted system call` flood | Restart with `HEADLESS=1` |
| `Arming denied` after takeoff command | `listener failsafe_flags` then [decoder](07_parameters_and_preflight.md#failsafeflags-decoder) |
| `ekf2 missing data` after 30 s | [EKF2 diagnosis tree](#symptom-3--ekf2-missing-data-diagnosis-tree) above |
| `Gazebo simulation dependencies not found` | Source ROS + `export GZ_DISTRO=harmonic` |
| Pink / grey textures | Run `tools/fix_fuel_textures.py` |
| `Address already in use` on port 8888 | `pkill -9 px4 gz` |
| Vertical position estimate timeout mid-flight | `HEADLESS=1`, simplify world |
| Drone takes off and immediately lands | Spawn at z=0.5+, raise `LNDMC_TRIG_TIME` |

## Sources

- EKF2 tuning (fusion mask, height source, sensor minimums):
  <https://docs.px4.io/main/en/advanced_config/tuning_the_ecl_ekf.html>
- Pre-arm checks:
  <https://docs.px4.io/main/en/advanced_config/prearm_arm_disarm.html>
- FailsafeFlags message:
  <https://docs.px4.io/main/en/msg_docs/FailsafeFlags.html>
- Land detector params:
  <https://docs.px4.io/main/en/advanced_config/parameter_reference.html#land-detector>
- Lockstep references in PX4 source:
  `boards/px4/sitl/default.px4board` (`ENABLE_LOCKSTEP_SCHEDULER`)
