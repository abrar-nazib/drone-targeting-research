# Drone Simulation Stack — Research Findings

Scope: pick the drone model + physics + control stack the project will use to
capture a stereo / segmentation perception dataset on Gazebo Harmonic + ROS 2
Jazzy + RTX 3050 (3.96 GB VRAM), with a longer-term path toward FPV-style
flight dynamics for the control phase.

## TL;DR

For the **perception phase**, build the dataset with a **kinematic camera
rig** — a static SDF model with stereo + segmentation cameras that you
teleport along scripted trajectories via `gz topic` / a small ROS 2 node.
Skip dynamics entirely for capture; it's faster, deterministic, and avoids
having to fight an autopilot just to position the camera. For the **control
phase**, switch to **PX4-Autopilot main (≥ v1.16) SITL with the stock
`gz_x500` model on Gazebo Harmonic**, retuned for FPV characteristics
(higher `motorConstant` / `maxRotVelocity`, lower mass, higher rate
controller limits) and flown in **Acro mode** via Offboard rate setpoints
from a ROS 2 controller node. PX4 v1.16 is the first PX4 release that
explicitly switches its supported sim to Gazebo Harmonic LTS, which lines
up cleanly with REP-2000's Jazzy ↔ Harmonic pairing.
([PX4 v1.16 release
notes](https://docs.px4.io/main/en/releases/1.16))
The most surprising finding: `MulticopterVelocityControl` (the stock
gz-sim 8 controller) **explicitly cannot do attitude-rate / acro control**
— it's velocity-only with a built-in stabilizer
([source](https://github.com/gazebosim/gz-sim/blob/gz-sim8/src/systems/multicopter_control/MulticopterVelocityControl.cc)),
so the "no-autopilot" path is only viable if you bring your own rate
controller. Don't use ArduPilot's `ardupilot_gz` for this project: as of
May 2026 its `ros2_gz.repos` still pins everything to **ROS 2 Humble
branches**, which forces a Humble overlay on a Jazzy system.
([ros2_gz.repos source](https://github.com/ArduPilot/ardupilot_gz/blob/main/ros2_gz.repos))

## What makes FPV drones hard to simulate

A 5" FPV racing / freestyle quad differs from an "autonomous research
quad" (DJI M-series, x500, Iris) along several axes that compound:

- **Thrust-to-weight 4:1 to 12:1.** A typical 5" miniquad has TWR ~7.6:1
  vs. ~2:1 for a survey drone
  ([oscarliang.com](https://oscarliang.com/rate-acro-horizon-flight-mode-level/),
  ["miniquads"
  reference](https://oscarliang.com/betaflight-modes/)).
  The PX4 stock `x500` is mass 2.0 kg (+ ~0.064 kg rotors),
  `motorConstant` 8.55e-6 N·s²/rad², `maxRotVelocity` 1000 rad/s, giving
  per-rotor thrust = `8.55e-6 × 1000² = 8.55 N` and total thrust
  `~34.2 N` against weight `~20.3 N` — TWR **≈ 1.69:1**
  ([x500 SDF](https://github.com/PX4/PX4-gazebo-models/blob/main/models/x500/model.sdf),
  [x500_base
  SDF](https://github.com/PX4/PX4-gazebo-models/blob/main/models/x500_base/model.sdf)).
  `px4vision` (1.5 kg, momentConstant 0.06 — same maxRot, same motorConstant)
  reaches TWR **≈ 2.3:1**
  ([px4vision SDF](https://github.com/PX4/PX4-gazebo-models/blob/main/models/px4vision/model.sdf)).
  Neither is FPV. To hit a real FPV TWR you need to push `motorConstant`
  ~3-5×, drop mass, and raise `maxRotVelocity` (real 2207 / 2306 brushless
  motors on 6S spin to ~30000 RPM ≈ 3140 rad/s).

- **Brushless motor + ESC dynamics.** Thrust does not jump — there's a
  first-order spool-up with separate up/down time constants (motors lose
  RPM faster than they gain it because the airframe inertia + prop drag
  brake the prop). gz-sim's `MulticopterMotorModel` models exactly this
  with `timeConstantUp` / `timeConstantDown` via an exponential-ZoH
  first-order filter — defaults are 12.5 ms up / 25 ms down — directly
  ported from the RotorS `FirstOrderFilter`
  ([gz-sim multicopter motor model
  source](https://github.com/gazebosim/gz-sim/blob/gz-sim8/src/systems/multicopter_motor_model/MulticopterMotorModel.cc)).
  These defaults are reasonable for a 920 KV / 10" survey prop but slow
  for a 1700 KV / 5" race motor, where time constants are closer to 3-5
  ms. There is no ESC commutation / BLDC field-oriented-control model;
  ESC is treated as a transparent velocity-loop wrapper. For RL or
  bidirectional DShot work this is a known gap.

- **Battery sag.** Real LiPo voltage drops under high current draw (a 6S
  pack hits 22.2 V resting, sags to ~18-19 V at high throttle), reducing
  available RPM. gz-sim's plugin has no battery model; thrust is ideal at
  any throttle. This means your simulated craft will not "punch out" then
  visibly weaken — a defining characteristic of FPV punchouts.

- **Propeller aerodynamics.** Real props show:
  (a) **rotor drag** (linear thrust loss with translational speed,
  ~0.1× thrust at 30 m/s),
  (b) **rolling moment / blade flapping** (induced roll/pitch under
  forward flight),
  (c) **prop wash** (turbulent recirculation just after a fast yaw or
  flip, causing oscillation).
  gz-sim's plugin has `rotorDragCoefficient` and `rollingMomentCoefficient`
  parameters that capture (a) and (b) as static linear coefficients but
  ignore unsteady wake effects. Prop wash is not modeled — it's a Navier-
  Stokes phenomenon, you will not get this from any rigid-body sim.

- **Ground effect.** Real quads show ~10-30% extra thrust below ~1.5 ×
  rotor diameter from the floor. Not modeled by gz-sim's stock plugins.
  Some PX4 `LiftDrag` plugin work simulates this on fixed-wing but not
  multi-rotor.

- **IMU noise.** Real Bosch BMI270 / ICM42688 gyros have ~0.005 °/s/√Hz
  noise plus drift. Gazebo's IMU sensor supports configurable Gaussian
  noise + bias drift via the `<noise>` block — fidelity here is
  acceptable for control work
  ([gz IMU sensor docs](https://gazebosim.org/libs/sensors/)).

- **Control loop rate.** A real Betaflight FC closes the rate loop at 4-8
  kHz; PX4 closes it at 1 kHz; gz-sim physics defaults to 1 kHz
  (max_step_size 0.001 s in the example
  [quadcopter.sdf](https://github.com/gazebosim/gz-sim/blob/gz-sim8/examples/worlds/quadcopter.sdf)).
  For perception this is irrelevant. For acro / freestyle replication you
  notice it as fewer high-frequency corrections — the sim feels "muted"
  vs. a real freestyle quad.

- **Motor mixing / ESC saturation.** Real ESCs clip at full throttle and
  cause asymmetric thrust under aggressive flips. gz-sim's plugin clamps
  `refMotorInput` to `maxRotVelocity` (no overshoot, no saturation
  artifacts). PX4's mixer + control allocation handles this in
  software, so this is reasonably faithful when PX4 is in the loop.

For a perception dataset, almost none of these matter. For RL freestyle
control, **none of the available open-source sims model all of them** —
this is a fundamental limit, not a Gazebo-specific one. The state-of-the-
art for high-fidelity FPV is custom GPU sims (Aerial Gym, Flightmare),
none of which run on Harmonic.
([Aerial Gym Simulator paper](https://arxiv.org/html/2503.01471v1),
[Aerial Gym site](https://ntnu-arl.github.io/aerial_gym_simulator/))

## Gazebo Harmonic multicopter physics — current state

The vendor install at `/opt/ros/jazzy/opt/gz_tools_vendor` ships these
multicopter-relevant plugins (verified by listing
`*.so` under the gz-sim8 plugin path):

- `libgz-sim8-multicopter-motor-model-system.so` — applies thrust + drag
  + rolling moment per rotor.
- `libgz-sim8-multicopter-control-system.so` — Lee-style velocity
  controller.
- `libgz-sim8-lift-drag-system.so` — fixed-wing surface aerodynamics.
- `libgz-sim8-advanced-lift-drag-system.so` — improved AoA + stall model.
- `libgz-sim8-thruster-system.so` — generic thruster (water/air).
- `libgz-sim8-spacecraft-thruster-model-system.so` — RCS-style on/off
  thruster.

### `MulticopterMotorModel` — what it actually models

From the source
([MulticopterMotorModel.cc, gz-sim8](https://github.com/gazebosim/gz-sim/blob/gz-sim8/src/systems/multicopter_motor_model/MulticopterMotorModel.cc),
header comments quoted verbatim in the file):

| Parameter            | Default     | Models                                      |
|----------------------|-------------|---------------------------------------------|
| `motorConstant`      | 8.54858e-6  | `F = motorConstant × ω²` (N per (rad/s)²)   |
| `momentConstant`     | 0.016       | yaw torque from prop drag (N·m per N)       |
| `maxRotVelocity`     | 838.0 rad/s | hard saturation, no overshoot               |
| `timeConstantUp`     | 0.0125 s    | first-order lag on spool-up                 |
| `timeConstantDown`   | 0.025 s     | first-order lag on spool-down               |
| `rotorDragCoefficient` | 1e-4      | linear drag opposing translational velocity |
| `rollingMomentCoefficient` | 1e-6  | induced roll moment from forward flight     |
| `turningDirection`   | cw / ccw    | sign of yaw torque                          |
| `motorType`          | velocity    | command interpretation                      |

The header carries an explicit comment that the implementation is
"from rotors_gazebo_plugins/include/rotors_gazebo_plugins/common.h" —
this is **the same physical model as RotorS, ported to gz-sim**. So you
get RotorS-grade fidelity (which is the academic reference) but on a
maintained sim.

What it does **not** model: BLDC commutation, ESC saturation, battery
voltage / sag, ground effect, prop wash / unsteady wake, blade flapping
dynamics, motor temperature derating.

### `MulticopterVelocityControl` — what it actually does

From the source
([MulticopterVelocityControl.cc, gz-sim8](https://github.com/gazebosim/gz-sim/blob/gz-sim8/src/systems/multicopter_control/MulticopterVelocityControl.cc)):

- Cascaded velocity → attitude → rate → rotor-velocity controller in the
  style of the Lee Position Controller (RotorS lineage), but stripped to
  velocity-only.
- Subscribes to `geometry_msgs::Twist` on `<robotNamespace>/cmd_vel`,
  publishes per-rotor velocities consumed by `MulticopterMotorModel`.
- **Cannot accept attitude or rate setpoints** (no acro mode equivalent).
  Only `linear.{x,y,z}` body-frame velocities and `angular.z` (yaw rate)
  are honored.
- Uses ground-truth pose / velocity from the ECM by default; a
  `<linearVelocityNoise>` and `<angularVelocityNoise>` block can inject
  Gaussian noise to mimic estimator error.
- Configurable `velocityGain`, `attitudeGain`, `angularRateGain`
  (per-axis), and `maxLinearAcceleration` / `maximumLinearVelocity` /
  `maximumAngularVelocity` clamps.
- Requires ≥ 4 rotors and a `<rotorConfiguration>` block enumerating
  joint names + force constants + directions.

This is fine as a "fly the camera around at scripted velocities" tool. It
is **not** a substitute for an FPV flight controller.

### Gaps for FPV specifically

1. No rate / acro control out of the box.
2. No battery sag.
3. Default motor parameters are tuned for a slow ~2 kg autonomous quad.
4. No model of the high-frequency PID loop dynamics that define FPV
   "feel".
5. No prop wash, blade flap, or unsteady wake.

Items 1, 3 are easily fixed in SDF + by bringing your own controller (PX4
in Acro mode is the path — see below). Items 2, 4, 5 are gaps inherent to
rigid-body sim and are accepted limits.

## Control stack options

### PX4 SITL + Gazebo Harmonic

**Maturity on Harmonic + Jazzy.** PX4 v1.16 (the current LTS line as of
May 2026) "switches to Gazebo Harmonic LTS for more reliable simulation"
— per the official release notes
([PX4 v1.16 release notes](https://docs.px4.io/main/en/releases/1.16),
[PX4 v1.16 announcement
post](https://px4.io/px4-autopilot-release-v1-16-what-you-need-to-know/)).
PX4 main also has a CI workflow targeting Ubuntu 24.04
([same release notes, ci entry](https://docs.px4.io/main/en/releases/1.16)).
However the **official ROS 2 user guide still lists Humble as the
supported pairing**, with no Jazzy mention
([PX4 ROS 2 user guide](https://docs.px4.io/main/en/ros2/user_guide.html)).
A reported (but closed-as-stale) bug
[PX4 issue #24159](https://github.com/PX4/PX4-Autopilot/issues/24159)
hit `ERROR [gz_bridge] timed out waiting for clock message` and
`time jump detected` warnings on the alpha2 of v1.16; users on stable
v1.16+ have not reported the same. Practical implication: use PX4 stable
≥ v1.16 (not main, not alphas) and expect to deal with one or two
sharp edges around the gz_bridge clock topic.

**FPV / acro fidelity.** PX4 ships an explicit Acro mode for multirotors
(roll/pitch/yaw sticks → body rate setpoint, throttle → direct
allocation) with default max rates 100 °/s, configurable up to ~720 °/s
roll/pitch + 540 °/s yaw — within the range experienced FPV pilots use
([PX4 Acro mode docs](https://docs.px4.io/main/en/flight_modes_mc/acro.html)).
This is the closest PX4 gets to Betaflight feel, and it is exercisable in
SITL via either a simulated joystick over MAVLink (QGroundControl) or
Offboard `VehicleRatesSetpoint` messages over uXRCE-DDS from a ROS 2
node. The stock airframes are tuned for autonomous flight, but you can
load a different rate-controller PID profile per airframe.

**ROS 2 integration.** Two paths:

- **uXRCE-DDS** (modern, recommended): PX4 contains the client; you run
  `MicroXRCEAgent` on the host. Topics flow as native PX4 message types
  via the `px4_msgs` package
  ([PX4 uXRCE-DDS docs](https://docs.px4.io/main/en/middleware/uxrce_dds)).
  `px4_msgs` builds cleanly on Jazzy in practice (it's pure ROS 2 IDL);
  the build is just a `colcon build --packages-select px4_msgs`.
- **MAVROS** (legacy): MAVLink ↔ ROS 2 bridge. More overhead, more
  type translation, but battle-tested. Use only if uXRCE-DDS proves
  flaky on Jazzy.

**Install (Jazzy + Harmonic + Ubuntu 24.04).** See the verbatim block
under "Setup commands" below.

**Known issues.** Wayland breaks Gazebo Harmonic on 24.04 — must launch
under X11 (`GDK_BACKEND=x11` or set the session to Xorg)
([discuss.px4.io
thread](https://discuss.px4.io/t/running-gazebo-harmonic-in-24-04-wayland/40801)).
Sensor timeouts (accel/mag) appear in some Docker setups
([PX4 issue #25089](https://github.com/PX4/PX4-Autopilot/issues/25089))
— not seen on bare metal.

### ArduPilot SITL + Gazebo Harmonic

**Maturity on Harmonic + Jazzy.** The `ardupilot_gazebo` plugin proper
(physics plugin only, no ROS) supports Harmonic and is the recommended
pair on Ubuntu 22.04
([ardupilot_gazebo README](https://github.com/ArduPilot/ardupilot_gazebo)).
The ROS 2 bringup repo `ardupilot_gz` is **the problem**: as of May 2026
its `ros2_gz.repos` file pins `micro_ros_agent`, `ros_gz`, and
`sdformat_urdf` to the **`humble` branch**
([ros2_gz.repos
contents](https://github.com/ArduPilot/ardupilot_gz/blob/main/ros2_gz.repos)).
The official ROS 2 + Gazebo guide
([ardupilot.org/dev/docs/ros2-gazebo.html](https://ardupilot.org/dev/docs/ros2-gazebo.html))
sources Humble and never mentions Jazzy. You can hand-port (`vcs import`
with a hand-edited repos file pointing at `jazzy` branches), but you'll
hit at least the `micro_ros_agent` Jazzy branch difference.

**FPV / acro fidelity.** ArduCopter has a real Acro mode with
configurable rates and rate-loop tuning, comparable to PX4
([ArduPilot Acro mode docs](https://ardupilot.org/copter/docs/acro-mode.html)).
The flight model uses the same gz-sim multicopter physics under the hood
(same RotorS-derived motor model), so physical fidelity is on par with
PX4.

**ROS 2 integration.** ArduPilot's `ardupilot_dds` over micro-ROS gives a
DDS bridge similar to PX4's uXRCE-DDS, but with a smaller user base on
Jazzy specifically.

**Verdict for this project.** Skip unless the user has a specific
preference for ArduCopter. PX4 has better Jazzy alignment in v1.16.

### Direct motor control (no autopilot, for RL)

Use `MulticopterMotorModel` directly without `MulticopterVelocityControl`
or any autopilot. Publish `gz.msgs.Actuators` messages on
`<robotNamespace>/command/motor_speed` with one velocity per rotor. The
controller is up to you (RL policy, hand-written rate PID, MPC).

**FPV fidelity.** As high as the motor SDF parameters and your control
loop. The motor model is RotorS-equivalent; if you tune
`motorConstant`, `momentConstant`, time constants, and inertia for a
real 5" motor + prop, the rigid-body dynamics will match a real quad to
within the limits noted in "What makes FPV drones hard". This is the
academic standard path
([RotorS 2017 reference paper, ResearchGate](https://www.researchgate.net/publication/309291237_RotorS_-_A_Modular_Gazebo_MAV_Simulator_Framework)).

**ROS 2 integration.** Bridge `gz.msgs.Actuators` ↔ ROS 2 via
`ros_gz_bridge`. Or skip ROS for control and write a Python node that
uses `gz-transport13` Python bindings directly for the tightest loop.

**When to use.** When you want full control of the controller (RL, custom
MPC, learning-based rate loops) and don't need PX4's mode logic.

### Betaflight SITL (if viable)

This is the **most realistic FPV controller in simulation** — Betaflight
runs the same firmware that lives on real FCs, in acro mode by default,
with the same PID rate loop tuning system real pilots use. The
`betaloop` project (Aeroloop GitHub) provides exactly this plus a Gazebo
bridge. The Betaflight project documents an "Autopilot Testing Gazebo"
flow on Ubuntu 24.04 with Gazebo Harmonic
([Betaflight SITL Autopilot Testing
docs](https://betaflight.com/docs/development/autopilot/SITL_Autopilot_Testing_Gazebo)).

**Architecture.** Betaflight FC compiled as a native x86_64 binary;
external sim communicates over UDP:
- port 9002 SITL → Gazebo (motor commands 0.0–1.0)
- port 9003 Gazebo → SITL (FDM packet: IMU, GPS, baro)
- port 9004 external → SITL (RC channels)
- port 5761 (TCP) Configurator over websockify proxy.
The Gazebo bridge plugin reads motor commands and applies forces to a
quadcopter SDF using PID-based velocity control; the model used in the
docs is `betaloop_iris_with_standoffs` in
`betaloop_iris_betaflight_demo_harmonic.sdf`.

**FPV fidelity.** Highest available open-source. Rate loop is real
Betaflight code at the same loop frequency it would run on hardware.

**Maturity.** The Aeroloop / `betaloop` project is recent and small, but
the Betaflight upstream docs treat it as a real testing target. The
documented path runs against Gazebo Harmonic + Ubuntu 24.04.

**ROS 2 integration.** **None.** No ROS 2 bridge exists. The bridge is
UDP-only, intended for HSITL testing. To use this with ROS 2 you would
write your own bridge (UDP RC channel injection ↔ ROS 2 cmd topic, plus
`ros_gz_bridge` for sensors / poses).

**Verdict.** Park for later — if the control phase truly needs Betaflight-
grade rate-loop fidelity, plan a Phase-3 effort. For dataset capture and
even initial control, PX4 Acro is sufficient.

## Available drone models / SDFs / URDFs

| Model | Repo / path | Mass | Per-rotor max thrust | TWR | Best for |
|---|---|---|---|---|---|
| **`x500`** (PX4 stock) | `PX4/PX4-gazebo-models/models/x500/model.sdf` | 2.0 kg | 8.55 N | ~1.69:1 | Default autonomous quad, NOT FPV |
| **`x500_depth`** (front-facing depth cam) | same repo, `x500_depth/` | ~2.05 kg | 8.55 N | ~1.65:1 | Perception-on-PX4 baseline |
| **`x500_vision`** (vision odometry) | same repo, `x500_vision/` | ~2.05 kg | 8.55 N | ~1.65:1 | VIO experiments |
| **`x500_lidar_2d` / `lidar_down` / `lidar_front`** | same repo | ~2.05 kg | 8.55 N | ~1.65:1 | LIDAR research |
| **`x500_gimbal`** | same repo | ~2.5 kg | 8.55 N | ~1.4:1 | Gimbal cam (slow real-time-factor — heavy collision mesh) |
| **`px4vision`** | `PX4/PX4-gazebo-models/models/px4vision/` | 1.5 kg | 8.55 N | ~2.3:1 | Closest stock to "vision drone" |
| **`omnicopter` / `omniquad`** | `PX4/PX4-gazebo-models/models/omni*` | varies | varies | varies | Over-actuated research |
| **`quadtailsitter`** | `PX4/PX4-gazebo-models/models/quadtailsitter/` | — | — | — | VTOL tailsitter |
| **`X3`** quadcopter (gz-sim example) | `gazebosim/gz-sim/examples/worlds/quadcopter.sdf` | — | 6.84 N (motorConst 8.55e-6, ω 800) | — | Bare gz-sim demo, no autopilot needed |
| **Iris** (ArduPilot) | `ArduPilot/ardupilot_gazebo/models/iris_with_*/` | ~1.5 kg | — | ~2:1 | Default ArduCopter SITL — same RotorS lineage |
| **Iris with standoffs** (Betaloop) | `Aeroloop/betaloop` | — | — | — | Betaflight SITL world |
| **`vehicle_blue` / `vehicle.sdf`** in `ros_gz_sim_demos` | `gazebosim/ros_gz/ros_gz_sim_demos` | — | — | — | Differential-drive ground vehicle, **not** a multicopter — irrelevant for this project |
| Aerial Gym Simulator models | `ntnu-arl/aerial_gym_simulator` | — | — | — | **Isaac Gym only**, not Gazebo. Useful as a reference for parameter values for FPV-style frames |
| `gym-pybullet-drones` Crazyflie / Bebop | `utiasDSL/gym-pybullet-drones` | nano | low | low | PyBullet, not Gazebo. Tiny indoor quads |

**Bottom line on stock models:** none of them are tuned for FPV. The
practical move is to copy `x500/model.sdf`, rename it `fpv5inch`, drop
mass to ~0.65 kg, raise `motorConstant` to ~3e-5, raise `maxRotVelocity`
to ~3000, shrink time constants to ~0.005 s, and adjust inertia (~ 0.003
kg·m² ixx/iyy, 0.005 izz). That gives ~270 N total thrust against ~6.5 N
weight = TWR ~40:1 (way too high — back off `motorConstant` until you
land in the 6-8:1 band you want).

## Recommendation for THIS project

Two phases, two stacks.

### Phase 1 — Perception dataset capture: kinematic camera rig

For capturing labelled stereo + segmentation frames from "drone
viewpoints", **do not run a flight stack at all**. Build a minimal SDF
with:

- One link (the "drone" body — visual is optional, can be invisible).
- A stereo camera sensor pair (`<sensor type="camera">` + matching pair,
  baseline ~0.10 m).
- A `<sensor type="segmentation">` (semantic, panoptic, or both — gz-sim 8
  supports both via the segmentation camera released in Harmonic
  ([Harmonic release post](https://www.openrobotics.org/blog/2023/9/26/gazebo-harmonic-released))).
- An optional depth camera for ground-truth depth.

Then position-control the rig from a Python ROS 2 node that publishes
`gz.msgs.Pose` updates on `/world/<world>/set_pose` (Gazebo Transport),
or by attaching the rig to a parent kinematic frame whose pose you set
directly. Walk the rig along scripted trajectories (Bezier curves at
representative drone speeds; helical orbits around target objects;
straight passes through urban canyons). For each pose, capture
synchronised RGB-L, RGB-R, depth, and segmentation frames. Save with
the pose as part of the metadata.

**Why this and not "fly the autopilot":**

1. **Determinism.** Reproducible captures = reproducible model training.
   With dynamics in the loop, two captures of the same trajectory diverge.
2. **Speed.** No physics step-cost ⇒ you cap dataset capture by the
   rendering pipeline only. On a 3.96 GB RTX 3050 the camera + depth +
   segmentation render is your bottleneck regardless.
3. **No autopilot tuning detour.** PX4 needs to be commanded to follow
   trajectories; that's a Phase-2 problem. Don't conflate.
4. **No "FPV-realism" tax.** None of the FPV-specific physics (battery
   sag, prop wash, etc.) affect a stereo-depth or segmentation training
   set. Motion blur and IMU-correlated ego-motion can be added at
   training-augmentation time.

**Tradeoff acknowledged:** if the eventual perception pipeline relies on
**rolling-shutter motion-blur correlated with real ego-motion** (some
event-camera or IMU-camera fusion work does), kinematic capture loses
that. For depth + segmentation it does not.

### Phase 2 — Control / target-following: PX4 + Harmonic, FPV-tuned x500

When the project moves to closed-loop control, switch to:

- **PX4-Autopilot stable v1.16 SITL** (current stable, switched its
  sim to Harmonic LTS).
- **Custom airframe**: copy `x500` model, retune the four
  `MulticopterMotorModel` blocks to FPV parameters (start: `motorConstant
  = 1.7e-5`, `maxRotVelocity = 2000`, `timeConstantUp = 0.005`,
  `timeConstantDown = 0.008`, mass 0.65 kg), then iterate.
- **Acro mode** flown from a ROS 2 Offboard node sending
  `VehicleRatesSetpoint` over **uXRCE-DDS** via `px4_msgs`.
  ([PX4 Acro mode](https://docs.px4.io/main/en/flight_modes_mc/acro.html))
- **Stereo + segmentation cameras** as in Phase 1, attached to the SDF.

Park ArduPilot, Betaflight SITL, and Aerial Gym for now.

## Performance expectations on RTX 3050

Hard data on RTX 3050 + Harmonic is sparse, but adjacent reports give a
reasonable envelope:

- Iris + ArduPilot in `iris_runway` (no gimbal) on i7-12650H + RTX 3060,
  32 GB: **~90% real-time factor**
  ([ArduPilot Discourse
  thread](https://discuss.ardupilot.org/t/gazebo-harmonic-slow-real-time-factor-on-baylands-world/125284)).
- Iris + gimbal in `baylands` (large world + heavy collision mesh):
  **~5% RTF** — the gimbal's high-poly collision mesh dominates; CPU
  utilisation only 40%, so it's a physics single-thread bottleneck, not
  GPU. Replacing with primitive collision recovers performance.

Translating to RTX 3050 + the user's likely setup (assuming a recent
mobile i5/i7 / Ryzen-class CPU):

- **Empty world + stereo (640×480) + segmentation + a 2 kg quad**:
  expect RTF 0.7–1.0.
- **Urban world (cars, humans, houses, hundreds of meshes) + stereo +
  segmentation**: expect RTF 0.3–0.7. GPU VRAM is the risk — 3.96 GB is
  tight for a complex urban world with PBR materials. Disable shadows on
  non-essential lights, drop visual mesh LODs, and avoid high-poly
  collision meshes (use box / cylinder primitives).
- **Forest world**: trees are heavy. Use instanced mesh references
  (Gazebo Fuel collections) and simplify collision to a vertical
  cylinder per trunk.
- **Two cameras + depth + segmentation @ 30 Hz** is feasible at 640×480
  per camera on a 3050. Pushing to 1280×720 with all four streams will
  saturate the GPU.

**Knobs to turn if it's too slow:**

1. Use **`<sensor> <update_rate>`** — capture at 10 Hz, not 60.
2. Set **`<headless>`** on launch (`gz sim -s -r world.sdf`) — runs the
   server only, no GUI. Saves ~30% GPU.
3. **Lockstep simulation**: in PX4, `PX4_SIM_SPEED_FACTOR=0.5` slows
   wall-clock to give physics + rendering more time per step. Useful
   when capturing.
4. Replace mesh collisions with primitives (`<collision><geometry>
   <box/>`).
5. Drop shadow casting on non-key lights.
6. Use **panoptic_segmentation** instead of two separate segmentation
   sensors if you need both semantic + instance — it's one render pass.

## Setup commands (verbatim, copy-pasteable)

The user already has Jazzy + Harmonic via `ros-jazzy-ros-gz`. These
commands assume that, plus an SSD-resident workspace at
`/media/abrar/AbrarSSD/ROS/ros2_ws`. Substitute paths if different.

### One-time host prep

```bash
# Force X11 for the Gazebo session (Wayland breaks Harmonic on 24.04)
# Add to ~/.bashrc or wrap the launch command:
export GDK_BACKEND=x11
export QT_QPA_PLATFORM=xcb

# Confirm the vendor gz binary is on PATH
ls /opt/ros/jazzy/opt/gz_tools_vendor/bin/gz
# If 'gz' is not on PATH, add:
export PATH=/opt/ros/jazzy/opt/gz_tools_vendor/bin:$PATH
```

### Phase 1 — Kinematic camera rig (no autopilot, no PX4)

```bash
# Workspace
mkdir -p /media/abrar/AbrarSSD/ROS/ros2_ws/src
cd /media/abrar/AbrarSSD/ROS/ros2_ws

# Source the underlay in a fresh shell
source /opt/ros/jazzy/setup.bash

# Nothing to install beyond ros-jazzy-ros-gz (already done).
# You write the SDF and a small ROS 2 node that publishes pose updates.
# See gz-sim examples for the segmentation-camera reference SDF:
#   https://github.com/gazebosim/gz-sim/tree/gz-sim8/examples/worlds
# The relevant world is examples/worlds/segmentation_camera.sdf
```

### Phase 2 — PX4 stable v1.16 SITL + Harmonic + ROS 2 (uXRCE-DDS)

```bash
# 1) PX4 firmware (on the SSD to save root partition space)
cd /media/abrar/AbrarSSD/ROS
git clone --recursive --branch release/1.16 \
  https://github.com/PX4/PX4-Autopilot.git
cd PX4-Autopilot
bash ./Tools/setup/ubuntu.sh                  # installs PX4 toolchain deps

# 2) Build SITL with the Gazebo Harmonic x500 target
make px4_sitl gz_x500                         # first build will take ~15 min

# 3) micro-XRCE-DDS Agent (the ROS 2 ↔ PX4 bridge)
cd /media/abrar/AbrarSSD/ROS
git clone --branch v2.4.3 \
  https://github.com/eProsima/Micro-XRCE-DDS-Agent.git
cd Micro-XRCE-DDS-Agent
mkdir build && cd build
cmake ..
make -j"$(nproc)"
sudo make install
sudo ldconfig

# 4) px4_msgs in your ROS 2 workspace
cd /media/abrar/AbrarSSD/ROS/ros2_ws/src
git clone --branch release/1.16 https://github.com/PX4/px4_msgs.git
cd /media/abrar/AbrarSSD/ROS/ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --packages-select px4_msgs

# 5) Launch order (each in its own terminal, all sourced from
#    /opt/ros/jazzy/setup.bash + the workspace overlay)
# Terminal A — Gazebo + PX4 SITL:
cd /media/abrar/AbrarSSD/ROS/PX4-Autopilot
make px4_sitl gz_x500
# Terminal B — micro-XRCE-DDS Agent:
MicroXRCEAgent udp4 -p 8888
# Terminal C — ROS 2 listener test:
ros2 topic list | grep /fmu/
ros2 topic echo /fmu/out/vehicle_status
```

### Phase 2 (later) — FPV-retuned airframe

```bash
# Copy the stock x500 SDF and edit it. Models live at:
#   /media/abrar/AbrarSSD/ROS/PX4-Autopilot/Tools/simulation/gz/models/
# Or pulled from PX4-gazebo-models repo. Edit:
#   - <mass> on x500_base/model.sdf base_link  → 0.65
#   - <inertia> ixx, iyy ~ 0.003 ; izz ~ 0.005
#   - per-rotor <motorConstant> 1.7e-5
#   - per-rotor <maxRotVelocity> 2000
#   - per-rotor <timeConstantUp> 0.005
#   - per-rotor <timeConstantDown> 0.008
# Then add a new airframe config under
#   PX4-Autopilot/ROMFS/px4fmu_common/init.d-posix/airframes/
# and rebuild with: make px4_sitl gz_<your_airframe_name>
```

## Open questions / risks

1. **Jazzy is not officially blessed by PX4's ROS 2 user guide** as of
   May 2026 — Humble is. The Jazzy + Harmonic + PX4 v1.16 path works in
   practice for many users but isn't covered by upstream CI for the
   ROS 2 bridge. If `px4_msgs` ABI breaks under Jazzy, the workaround is
   pinning to the commit matching PX4 v1.16's message definitions.
   ([PX4 ROS 2 user
   guide](https://docs.px4.io/main/en/ros2/user_guide.html))

2. **VRAM ceiling on RTX 3050.** 3.96 GB is enough for the perception
   capture itself, but not enough to host the perception capture **and**
   train the depth/segmentation model on the same machine simultaneously.
   Plan to capture, then train (per the user's global GPU rule, the
   training run wants ≥ 85% of the 3.96 GB to itself).

3. **No Betaflight-grade rate-loop fidelity in the recommended stack.**
   PX4 Acro is good but is not bit-for-bit Betaflight. If the eventual
   target is sim-to-real on a real Betaflight FC, plan a Phase-3 swap
   to `betaloop` and accept losing the ROS 2 bridge.

4. **`MulticopterVelocityControl` cannot do rate / acro commands.**
   Documented above. Don't accidentally rely on it for FPV-style flight
   testing — it will silently produce a docile, stabilised craft.
   ([gz-sim source](https://github.com/gazebosim/gz-sim/blob/gz-sim8/src/systems/multicopter_control/MulticopterVelocityControl.cc))

5. **ArduPilot's Jazzy story is weaker than PX4's.** `ardupilot_gz`
   pulls Humble branches of `ros_gz`, `micro_ros_agent`,
   `sdformat_urdf`. Hand-porting is possible but not a one-liner.
   ([ros2_gz.repos source](https://github.com/ArduPilot/ardupilot_gz/blob/main/ros2_gz.repos))

6. **Gazebo Wayland incompatibility on 24.04.** Documented above. If
   the user is on a Wayland session by default (KDE / GNOME on 24.04),
   they need to either log into an X11 session or run
   `GDK_BACKEND=x11 QT_QPA_PLATFORM=xcb gz sim ...`
   ([discuss.px4.io
   thread](https://discuss.px4.io/t/running-gazebo-harmonic-in-24-04-wayland/40801)).

7. **RotorS is dead.** Last commit July 2021
   (verified via the GitHub commits API). Listed here only because most
   academic literature on multirotor sim cites it; the gz-sim Multicopter
   plugins are the maintained successor and use the same physical model.
   ([RotorS repo](https://github.com/ethz-asl/rotors_simulator))

8. **Aerial Gym Simulator is a tempting alternative for the control
   phase**, especially for RL on a budget GPU — it parallelises thousands
   of multirotors on one GPU and ships geometric controllers + custom
   ray-cast rendering — but it is **Isaac Gym based, not Gazebo**, and
   IsaacGym is being deprecated in favour of Isaac Lab. It also wants a
   bigger GPU than the 3050 (paper reports training in ~1 h on a 3090).
   ([Aerial Gym paper](https://arxiv.org/html/2503.01471v1),
   [project site](https://ntnu-arl.github.io/aerial_gym_simulator/))
