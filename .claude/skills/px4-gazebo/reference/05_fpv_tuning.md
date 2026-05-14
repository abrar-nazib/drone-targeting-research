# 05 — FPV tuning (TWR, rate loop, gyro filters, Acro)

Turning the stock x500 (TWR ~1.8 at 2 kg / 4× ~9 N motors) into
something with FPV-class responsiveness (TWR 7–12). PX4's racer guide
is the canonical reference:
<https://docs.px4.io/main/en/config_mc/racer_setup.html>.

For *where* to put these params (airframe init script vs runtime
`param set`), see
[04_custom_airframes_models_worlds.md](04_custom_airframes_models_worlds.md).

## 1. Increase TWR — in the SDF, not just in params

Two knobs in the `gz-sim-multicopter-motor-model-system` plugin (per
rotor block):

- **`<motorConstant>`** — thrust = `motorConstant × maxRotVelocity²`
  per rotor at full throttle. Going from `8.54858e-06` to `~3.5e-05`
  quadruples per-motor thrust at the same RPM, taking the x500 from
  TWR ~1.8 to TWR ~7.
- **`<maxRotVelocity>`** — increase from `1000.0` rad/s to `2500.0` to
  model faster motors instead.

**Reduce the airframe mass** in `x500_base/model.sdf` (currently
`<mass>2.0</mass>`, with diagonal inertia ~0.022 / 0.022 / 0.04). A
600 g FPV frame at TWR 10 with ~1.5 kW motors maps to:

```xml
<mass>0.6</mass>
<inertia>
  <ixx>0.006</ixx>
  <iyy>0.006</iyy>
  <izz>0.012</izz>
  <ixy>0</ixy><ixz>0</ixz><iyz>0</iyz>
</inertia>
```

**Match `MPC_THR_HOVER` to the new TWR.** Hover throttle ≈ 1/TWR.
For TWR 8:

```sh
param set-default MPC_THR_HOVER 0.125
param set-default MPC_USE_HTE 0   # disable hover-throttle estimator so it stays pinned
```

`MPC_USE_HTE` defaults to 1 (EKF-driven learning). Pinning is wise
during initial bring-up; re-enable once flight is stable.

After changing `<motorConstant>` or `<mass>` you **must restart
`gz sim`** (it caches the model on first load).
`make px4_sitl gz_<name>` handles this.

## 2. Rate-controller params

PX4 expresses the rate loop as
`output = K · (P · err + I · ∫err + D · d_err/dt)` where `K` is a
global gain — tuning is normally just `_K` and `_D` after picking
`_P` start values.
(Source:
<https://docs.px4.io/main/en/config_mc/pid_tuning_guide_multicopter_basic.html>)

The full per-axis set:

| Param family | Roll | Pitch | Yaw |
|---|---|---|---|
| Global gain | `MC_ROLLRATE_K` | `MC_PITCHRATE_K` | `MC_YAWRATE_K` |
| P term | `MC_ROLLRATE_P` | `MC_PITCHRATE_P` | `MC_YAWRATE_P` |
| I term | `MC_ROLLRATE_I` | `MC_PITCHRATE_I` | `MC_YAWRATE_I` |
| D term | `MC_ROLLRATE_D` | `MC_PITCHRATE_D` | `MC_YAWRATE_D` |
| Outer (attitude) P | `MC_ROLL_P` | `MC_PITCH_P` | `MC_YAW_P` |
| Rate clamp (Stab/Posctl) | `MC_ROLLRATE_MAX` | `MC_PITCHRATE_MAX` | `MC_YAWRATE_MAX` |

For an **FPV start point**, halve PX4 defaults on `_P` and ramp up:

```sh
param set MC_ROLLRATE_P 0.06
param set MC_PITCHRATE_P 0.06
param set MC_ROLLRATE_D 0.0008
param set MC_PITCHRATE_D 0.0008
# Higher rate clamps (FPV needs 720 deg/s+ on roll/pitch)
param set MC_ROLLRATE_MAX 720
param set MC_PITCHRATE_MAX 720
param set MC_YAWRATE_MAX 360
```

You will retune in the air.

**Throttle PID attenuation** — `MC_TPA_BREAK_*`, `MC_TPA_RATE_*` —
attenuates rate gains at high throttle to suppress motor-saturation
oscillation. Defaults are reasonable for FPV; only touch if you see
high-throttle wobble.

## 3. Gyro filtering

The racer guide is explicit: *"lower latency allows you to increase
the rate P gains, which means better flight performance."* Relevant
params:

| Param | Purpose | FPV value |
|---|---|---|
| `IMU_GYRO_CUTOFF` | Low-pass cutoff in Hz | **60–120** (default ~30) |
| `IMU_GYRO_NF0_FRQ` | First notch filter centre Hz | Match dominant motor harmonic |
| `IMU_GYRO_NF0_BW` | First notch filter BW | ~20 Hz around the centre |
| `IMU_GYRO_NF1_FRQ`, `_NF1_BW` | Second notch (e.g. 2× motor harmonic) | Optional |
| `IMU_DGYRO_CUTOFF` | Derivative-of-gyro cutoff (used by `_D`) | 60–100 |
| `IMU_ACCEL_CUTOFF` | Accel low-pass | Default fine |

**In SITL, vibration is essentially zero**, so you can run with
`IMU_GYRO_CUTOFF 200` and `IMU_DGYRO_CUTOFF 100` to test the rate loop
without filter latency masking the response. This is *not* a real
hardware tune — on hardware, motor noise will fold straight into the D
term and oscillate the airframe.

## 4. Acro mode

The FPV pilot mode — full direct rate control, throttle passes
straight to the mixer. Per
<https://docs.px4.io/main/en/flight_modes_mc/acro.html>:

| Param | Default | FPV value | Notes |
|---|---|---|---|
| `MC_ACRO_R_MAX` | 100 deg/s | **720** | Max roll rate |
| `MC_ACRO_P_MAX` | 100 deg/s | **720** | Max pitch rate |
| `MC_ACRO_Y_MAX` | 100 deg/s | 360–720 | Max yaw rate |
| `MC_ACRO_EXPO` | 0 (linear) | 0.69 (cubic) | Soft centre |
| `MC_ACRO_EXPO_Y` | 0.69 | 0.69 | Yaw expo |
| `MC_ACRO_SUPEXPO` | 0 | 0.69–0.70 | Super-expo (further softens centre) |
| `MC_ACRO_SUPEXPOY` | 0 | 0.69–0.70 | Super-expo yaw |

These give the standard FPV "soft centre, hard outer travel" stick
feel.

**Pair with `MC_AIRMODE 1`** (only after stable flight is verified) so
attitude control still works at zero throttle. Throttle "is passed
directly to control allocation" so it responds instantly to stick.

## 5. Position-mode behaviour for an FPV airframe

Defaults are tuned for a tame multicopter. Crank these for FPV-class
agility while still wanting position control (relevant for the
project's auto-landing — landing controllers run in
Position / Offboard, not Acro):

| Param | Default | FPV-friendly | Purpose |
|---|---|---|---|
| `MPC_MAN_TILT_MAX` | 35° | 60–70° | Max bank in Position / Stabilized |
| `MPC_MANTHR_MIN` | 0.08 | 0 | Min manual throttle (0 for racers per docs) |
| `MPC_XY_VEL_MAX` | 12 | 25 | Max horizontal velocity in pos mode |
| `MPC_Z_VEL_MAX_UP` | 3 | 8 | Climb-rate cap |
| `MPC_Z_VEL_MAX_DN` | 1.5 | 5 | Descent-rate cap |
| `MPC_ACC_HOR_MAX` | 5 | 15 | Horizontal accel cap (FPV TWR-8 sustains > 2 g) |
| `MPC_ACC_UP_MAX` | 4 | 10 | Up-accel cap |
| `MPC_ACC_DOWN_MAX` | 3 | 8 | Down-accel cap |

For the **landing controller** specifically, the descent-rate caps
(`MPC_Z_VEL_MAX_DN`, `MPC_ACC_DOWN_MAX`) are what limit how
aggressively the drone can drop onto the moving target. Default 1.5 m/s
is too slow for a moving-platform landing; bump to 3–5 m/s.

## SITL-specific gotchas

- **`<motorConstant>` / `<mass>` changes need a `gz sim` restart**
  (model cached on first load). `make px4_sitl gz_<name>` does this
  automatically, but standalone-Gazebo workflows need a manual kill +
  restart of `gz sim`.
- **`MPC_THR_HOVER` is learned in flight by default.** To pin it after
  setting, also `param set MPC_USE_HTE 0`, `param save`.
- **The PX4 racer guide's recommendation of DShot + AUX pins** drops
  ~5 ms latency on real hardware. In SITL the motor model is
  `<motorType>velocity</motorType>` with `timeConstantUp 0.0125` — the
  time constant is the only motor-side latency. Drop it to 0.005 for
  a closer FPV ESC model.
- **`COM_RC_IN_MODE`** matters even in Acro — set to 4 (stick input
  disabled) for fully autonomous SITL with no joystick. Set to 1
  (joystick) for QGroundControl manual override.

## Sources

- PX4 racer setup (the canonical FPV tuning guide):
  <https://docs.px4.io/main/en/config_mc/racer_setup.html>
- PX4 multicopter PID tuning:
  <https://docs.px4.io/main/en/config_mc/pid_tuning_guide_multicopter_basic.html>
- PX4 Acro mode reference:
  <https://docs.px4.io/main/en/flight_modes_mc/acro.html>
- PX4 parameter reference (filter for `MC_*`, `MPC_*`, `IMU_*`):
  <https://docs.px4.io/main/en/advanced_config/parameter_reference.html>
