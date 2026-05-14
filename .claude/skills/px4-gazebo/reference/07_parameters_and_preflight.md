# 07 — Parameters & preflight checks

The PX4 parameter system, the SITL-specific param recipe, and the
**field-by-field FailsafeFlags decoder** that turns "Arming denied:
Resolve system health failures first" into a 30-second fix.

For the troubleshooting *recipe* (what to run, in what order), see
[08_troubleshooting.md](08_troubleshooting.md).

## The `pxh>` `param` subsystem

| Command | Action |
|---|---|
| `param show <NAME>` | print current value |
| `param show <PATTERN>` | glob (e.g. `param show COM_*`) |
| `param show -c` | only params changed from default |
| `param set <NAME> <VAL>` | set in RAM only |
| `param save` | persist to backing store (in SITL: `eeprom/parameters_<id>` under `build/px4_sitl_default/rootfs/`) |
| `param load <file>` | load full param dump |
| `param compare <NAME> <VAL>` | exit code 0 if equal — useful in startup scripts |
| `param touch <NAME>` | mark used (forces export to dds_topics) |
| `param reset <NAME>` | reset single param to default |
| `param reset_all` | nuke RAM state |
| `param status` | param subsystem stats |

(Source: <https://docs.px4.io/main/en/advanced_config/parameters.html>)

GUI access through QGroundControl (Vehicle Setup → Parameters) gives
you search + per-group browsing; useful when you don't know the exact
param name.

## SITL-relevant parameter set

Defaults assume real hardware, which is why SITL trips many checks
that don't matter without RC, GCS link, or a real battery.

| Param | Set to | Why |
|---|---|---|
| `COM_RCL_EXCEPT` | `4` (or `7`) | Bitmask: 1=Mission, 2=Hold, 4=Offboard. **Set bit 4 so OFFBOARD does not require RC link.** This is the #1 SITL parameter. |
| `COM_ARM_WO_GPS` | `1` | Allow arming without GPS lock (SITL GPS may be slow to converge in custom worlds). |
| `COM_DISARM_PRFLT` | `-1` | Disable auto-disarm when preflight checks regress. Useful while iterating. |
| `COM_ARM_MAG_STR` | `0` | Disable mag-strength check (SITL magnetometer is synthetic). |
| `COM_OBL_RC_ACT` | `0` (Position) or `2` (Land) | Action when offboard signal lost AND no RC. |
| `COM_OF_LOSS_T` | `1.0` (default) | Seconds before declaring offboard timeout. |
| `NAV_DLL_ACT` | `0` | Data-link-loss action = none (no auto-RTL on GCS disconnect). |
| `NAV_RCL_ACT` | `0` | RC-link-loss action = none. |
| `EKF2_AID_MASK` | bitmask, default `1` (GPS) | Sensor-fusion enable bits. Default fine in SITL with synthetic GPS. Bits: 1=GPS, 2=optical flow, 4=ext vision pos, 8=ext vision yaw, 16=ext vision vel, 128=GPS yaw. |
| `EKF2_HGT_REF` | `1` (GNSS) | Height source. Switch to `0` (Baro) if simulated GPS altitude is noisy. |
| `EKF2_GPS_CTRL` | `7` (default) | GPS pos+vel+heading fusion bits. |
| `EKF2_BARO_CTRL` | `1` | Barometer fusion enable. |
| `EKF2_MAG_TYPE` | `0` (auto) | `5` = disable mag entirely (use heading from GPS). Useful when an outdoor SITL world has wonky mag declination. |
| `SIM_GZ_EN` | `1` | Enable Gazebo gz_bridge module. Set in airframe init script. |
| `MAV_0_CONFIG` | `101` (default for SITL, TELEM1=14550) | MAVLink instance for QGC. Set to `0` to disable if it conflicts. |
| `UXRCE_DDS_CFG` | `0` (off-Eth, on-localhost in SITL) | Selects the comm port for the client. |
| `UXRCE_DDS_PRT` | `8888` | UDP port matching `MicroXRCEAgent udp4 -p 8888`. |
| `BAT_LOW_THR`, `BAT_CRIT_THR` | lower (e.g. 0.05, 0.02) | Silence simulated battery warnings if SITL battery model fires false positives. |
| `GF_ACTION` | `0` | Disable geofence action for SITL. |
| `COM_ARM_ODID` | `0` | Disable Open Drone ID requirement. |

(Sources:
<https://docs.px4.io/main/en/advanced_config/parameter_reference.html>;
<https://docs.px4.io/main/en/middleware/uxrce_dds.html>;
<https://docs.px4.io/main/en/advanced_config/tuning_the_ecl_ekf.html>;
<https://docs.px4.io/main/en/advanced_config/prearm_arm_disarm.html>)

### Standard "make SITL stop complaining" recipe

```sh
param set COM_RCL_EXCEPT 4         # OFFBOARD bypasses RC requirement
param set COM_ARM_WO_GPS 1         # arm even if GPS slow
param set NAV_DLL_ACT 0            # ignore GCS link loss
param set NAV_RCL_ACT 0            # ignore RC link loss
param set COM_ARM_MAG_STR 0        # mag-strength check off
param set COM_DISARM_PRFLT -1      # don't auto-disarm on preflight regression
param save
```

These are safe to apply once and persist for the rest of SITL bring-up.

## FailsafeFlags decoder

When `pxh>` says **`Arming denied: Resolve system health failures
first`**, the actual reason is in the **`FailsafeFlags`** message
published on `/fmu/out/failsafe_flags`. From `pxh>`:

```
listener failsafe_flags
```

(Source: <https://docs.px4.io/main/en/msg_docs/FailsafeFlags.html>)

### Mode-requirement bitmasks — *"this mode requires X but X is missing"*

These are `uint32` bitmasks indexed by `nav_state`. Bit `n` set means
"mode `n` cannot be entered because of this requirement." A non-zero
value is informational unless the user is trying to enter that mode.

| Field | Means | Common SITL fix |
|---|---|---|
| `mode_req_angular_velocity` | Needs gyro / IMU | Wait for IMU; check `sensor_combined` is publishing |
| `mode_req_attitude` | Needs valid attitude | See `attitude_invalid` below |
| `mode_req_local_alt` | Needs valid Z | Baro must report; check `EKF2_HGT_REF` |
| `mode_req_local_position` | Needs `xy_valid` | Most common OFFBOARD blocker. GPS lock OR external odom on `/fmu/in/vehicle_visual_odometry` |
| `mode_req_local_position_relaxed` | OFFBOARD with velocity-only is OK with relaxed estimate | |
| `mode_req_global_position` | Mission/RTL need global pos | |
| `mode_req_mission` | Need uploaded mission | |
| `mode_req_offboard_signal` | OFFBOARD-specific: setpoint stream must be alive at mode-switch time | Pre-stream 10 setpoints before DO_SET_MODE |
| `mode_req_home_position` | Need `home_position` set; usually requires GPS lock | |
| `mode_req_manual_control` | RC stick or `manual_control_input` must be live | `param set COM_RCL_EXCEPT 4` for OFFBOARD |
| `mode_req_prevent_arming` | This mode itself blocks arming | |
| `mode_req_wind_and_flight_time_compliance` | Wind / flight-time limits violated | |

### Hard validity flags — *"the EKF says this state is bad"*

**These are the ones that block arming when set.**

| Field | Cause | SITL fix |
|---|---|---|
| `attitude_invalid` | EKF2 hasn't converged on quaternion | Wait 5–15 s after sim spawn; check `sensor_combined` is publishing |
| `local_altitude_invalid` | Z estimate not valid | Baro plugin missing in SDF; check `EKF2_BARO_CTRL` |
| `local_position_invalid` | xy estimate dead | GPS plugin missing; or `EKF2_AID_MASK` excludes everything; or no external odom |
| `local_position_invalid_relaxed` | Even relaxed xy is dead | Same as above but harder |
| `local_velocity_invalid` | vx/vy invalid | Same root cause as local_position |
| `global_position_invalid` | No WGS84 fix | GPS not converged; `param set SIM_GPS_USED` to a sane satellite count |
| `global_position_invalid_relaxed` | Even relaxed | Hard GPS failure |
| `angular_velocity_invalid` | Gyro dead | IMU plugin missing in SDF |

### External-link flags

| Field | Cause | SITL fix |
|---|---|---|
| `manual_control_signal_lost` | No RC, no MAVLink RC override, no `manual_control_input` topic | `param set COM_RCL_EXCEPT 4` |
| `gcs_connection_lost` | QGC heartbeat absent (>5 s) | Either start QGC (port 14550) or `param set NAV_DLL_ACT 0` |
| `offboard_control_signal_lost` | Setpoints stopped streaming | Check publisher is at ≥ 2 Hz; restart your ROS 2 node |

### Battery / failure-detector flags

| Field | Cause | SITL fix |
|---|---|---|
| `battery_warning > 0` | Battery sim warning | `param set BAT_LOW_THR 0.05; param set BAT_CRIT_THR 0.02` |
| `battery_unhealthy` | Battery instance reporting fault | Adjust BAT_* thresholds |
| `battery_low_remaining_time` | Remaining-time estimator | Lower BAT_* thresholds |
| `fd_critical_failure` | Attitude limit exceeded (FD = failure detector) | Reset world; tilt limit `FD_FAIL_P` exceeded during spawn glitch |
| `fd_esc_arming_failure` | DShot ESCs failed to arm | Not relevant to SITL |
| `fd_imbalanced_prop`, `fd_motor_failure` | Detected fault | Disable with `FD_*` params if a SITL artefact |

### Mission / nav

| Field | Cause |
|---|---|
| `auto_mission_missing` | RTL/Mission selected but no mission |
| `home_position_invalid` | Home not set; usually GPS not yet locked |
| `mission_failure` | Mission item rejected |
| `navigator_failure` | Navigator state machine stuck |

### Other

| Field | Notes |
|---|---|
| `geofence_breached` | Disable with `param set GF_ACTION 0` for SITL |
| `wind_limit_exceeded` | Synthetic wind in Gazebo wind plugin |
| `flight_time_limit_exceeded` | `COM_FLT_TIME_MAX` exceeded |
| `position_accuracy_low` | EKF EPH/EPV crossed threshold but not invalid yet |
| `gnss_lost` | GNSS counts dropped below `SYS_HAS_NUM_GNSS` |
| `parachute_unhealthy` | Only relevant if `COM_PARACHUTE=1` |
| `remote_id_unhealthy` | Open Drone ID — disable with `COM_ARM_ODID=0` |
| `vtol_fixed_wing_system_failure` | VTOL only |

## How to use this decoder

When SITL refuses to arm:

1. From `pxh>`: `listener failsafe_flags`.
2. Read the output. Find every **non-zero** field.
3. Cross-reference with the tables above.
4. Apply the SITL fix or wait for the EKF-converged condition.
5. Retry `commander arm` or `commander takeoff`.

If you keep hitting the same blocker after applying the fix, escalate
to the [EKF2 missing data diagnosis tree](08_troubleshooting.md#ekf2-missing-data--diagnosis-tree) — it walks you up
the sensor pipeline from "is the IMU even arriving?" to "is GPS
origin set?".

## Sources

- Parameter reference (canonical):
  <https://docs.px4.io/main/en/advanced_config/parameter_reference.html>
- Param management UI / persistence:
  <https://docs.px4.io/main/en/advanced_config/parameters.html>
- Pre-arm / arming preflight checks:
  <https://docs.px4.io/main/en/advanced_config/prearm_arm_disarm.html>
- EKF2 tuning (sensor fusion mask, height source):
  <https://docs.px4.io/main/en/advanced_config/tuning_the_ecl_ekf.html>
- FailsafeFlags message (canonical field list):
  <https://docs.px4.io/main/en/msg_docs/FailsafeFlags.html>
