# URDF, Xacro & robot_state_publisher (ROS 2 Jazzy)

This file consolidates the seven Jazzy URDF tutorials into one reference. The
target consumer is the drone perception pipeline: a URDF describes the airframe,
the stereo-camera mount, the IMU pose, and any other sensor frames. Those frames
are then broadcast on `/tf` by `robot_state_publisher` so that TF2 lookups
(camera_link → base_link → odom → map) all "just work" inside RViz, image
rectification, point-cloud projection, and SLAM.

Quick install for all examples below:

```bash
sudo apt install ros-jazzy-urdf-tutorial ros-jazzy-joint-state-publisher-gui ros-jazzy-robot-state-publisher ros-jazzy-xacro
```

Every `display.launch.py` invocation in the tutorials below relies on the
`urdf_tutorial` package. It loads the URDF as the `robot_description` parameter,
spins up `robot_state_publisher`, spins up `joint_state_publisher_gui` (so any
non-fixed joint gets a slider), and starts `rviz2` with a preset config.

---

## Building a Visual Robot Model with URDF from Scratch
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Intermediate/URDF/Building-a-Visual-Robot-Model-with-URDF-from-Scratch.html

This page introduces the URDF tag set in five progressive examples that build
toward a visual-only R2D2-style robot. The model is not yet movable and has no
inertia/collision data — only `<visual>`.

**URDF root and tag set introduced here**

- `<robot name="...">` — root element. Every URDF has exactly one.
- `<link name="...">` — a rigid body / part of the robot. Holds `<visual>`,
  `<collision>`, `<inertial>` children. The link's name is also the TF frame
  name that `robot_state_publisher` will broadcast.
- `<joint name="..." type="...">` — connects exactly two links. Required
  children: `<parent link="..."/>`, `<child link="..."/>`. Optional:
  `<origin .../>`, `<axis .../>`, `<limit .../>`, `<dynamics .../>`,
  `<calibration .../>`, `<mimic .../>`, `<safety_controller .../>`.
- `<visual>` — what the link looks like in RViz/Gazebo. Contains
  `<geometry>`, optional `<origin>`, optional `<material>`.
- `<geometry>` — wraps exactly one of `<box size="x y z"/>`,
  `<cylinder length="L" radius="R"/>`, `<sphere radius="R"/>`,
  `<mesh filename="package://pkg/path/to/file.dae"/>` (or .stl, .obj).
  Mesh files use the `package://` URI so colcon-installed packages resolve at
  runtime.
- `<origin xyz="x y z" rpy="r p y"/>` — pose offset. On a `<joint>`, it
  positions the child link's frame relative to the parent's frame. On a
  `<visual>` (or `<collision>`/`<inertial>`), it positions the geometry
  relative to the link's own frame. Translation in metres, rotation in radians
  (roll-pitch-yaw, intrinsic ZYX).
- `<material name="...">` — either declared inline once and reused by name, or
  defined inline with `<color rgba="r g b a"/>` (each channel 0-1). Meshes
  (especially `.dae` / Collada) can carry their own colour data, in which case
  `<material>` may be omitted.

**Joint type covered in this page:** only `fixed` (rigid weld between parent
and child — no DoF). Movable types are introduced in the next page.

**Tree structure rule**: the model must form a tree. Exactly one link is the
root (no joint lists it as a child). Every other link is reached by following
`parent → child` joints from the root.

### Example 1 — `01-myfirst.urdf`: a single cylinder

```xml
<?xml version="1.0"?>
<robot name="myfirst">
  <link name="base_link">
    <visual>
      <geometry>
        <cylinder length="0.6" radius="0.2"/>
      </geometry>
    </visual>
  </link>
</robot>
```

### Example 2 — `02-multipleshapes.urdf`: two links joined by a fixed joint

```xml
<?xml version="1.0"?>
<robot name="multipleshapes">
  <link name="base_link">
    <visual>
      <geometry>
        <cylinder length="0.6" radius="0.2"/>
      </geometry>
    </visual>
  </link>

  <link name="right_leg">
    <visual>
      <geometry>
        <box size="0.6 0.1 0.2"/>
      </geometry>
    </visual>
  </link>

  <joint name="base_to_right_leg" type="fixed">
    <parent link="base_link"/>
    <child link="right_leg"/>
  </joint>
</robot>
```

(Without an `<origin>` on the joint, both links share the same origin and
overlap visually.)

### Example 3 — `03-origins.urdf`: position with `<origin>`

```xml
<?xml version="1.0"?>
<robot name="origins">
  <link name="base_link">
    <visual>
      <geometry>
        <cylinder length="0.6" radius="0.2"/>
      </geometry>
    </visual>
  </link>

  <link name="right_leg">
    <visual>
      <geometry>
        <box size="0.6 0.1 0.2"/>
      </geometry>
      <origin rpy="0 1.57075 0" xyz="0 0 -0.3"/>
    </visual>
  </link>

  <joint name="base_to_right_leg" type="fixed">
    <parent link="base_link"/>
    <child link="right_leg"/>
    <origin xyz="0 -0.22 0.25"/>
  </joint>
</robot>
```

The joint's `<origin>` shifts the leg frame to the side and up; the visual's
`<origin>` rotates the box 90° about Y (`pi/2`) and pushes its centre down so
the *top* of the leg sits at the joint, not the centre.

### Example 4 — `04-materials.urdf`: colours

Adds a `<material name="blue">` and `<material name="white">` block at the top
of `<robot>`, then references them by name from each `<visual>`. The same
two-leg structure as example 3 with a left leg added. (See full example 5
below for the exact material syntax.)

### Example 5 — `05-visual.urdf`: full visual R2D2

```xml
<?xml version="1.0"?>
<robot name="visual">

  <material name="blue">
    <color rgba="0 0 0.8 1"/>
  </material>
  <material name="black">
    <color rgba="0 0 0 1"/>
  </material>
  <material name="white">
    <color rgba="1 1 1 1"/>
  </material>

  <link name="base_link">
    <visual>
      <geometry>
        <cylinder length="0.6" radius="0.2"/>
      </geometry>
      <material name="blue"/>
    </visual>
  </link>

  <link name="right_leg">
    <visual>
      <geometry>
        <box size="0.6 0.1 0.2"/>
      </geometry>
      <origin rpy="0 1.57075 0" xyz="0 0 -0.3"/>
      <material name="white"/>
    </visual>
  </link>

  <joint name="base_to_right_leg" type="fixed">
    <parent link="base_link"/>
    <child link="right_leg"/>
    <origin xyz="0 -0.22 0.25"/>
  </joint>

  <link name="right_base">
    <visual>
      <geometry>
        <box size="0.4 0.1 0.1"/>
      </geometry>
      <material name="white"/>
    </visual>
  </link>

  <joint name="right_base_joint" type="fixed">
    <parent link="right_leg"/>
    <child link="right_base"/>
    <origin xyz="0 0 -0.6"/>
  </joint>

  <link name="right_front_wheel">
    <visual>
      <origin rpy="1.57075 0 0" xyz="0 0 0"/>
      <geometry>
        <cylinder length="0.1" radius="0.035"/>
      </geometry>
      <material name="black"/>
    </visual>
  </link>
  <joint name="right_front_wheel_joint" type="fixed">
    <parent link="right_base"/>
    <child link="right_front_wheel"/>
    <origin rpy="0 0 0" xyz="0.133333333333 0 -0.085"/>
  </joint>

  <link name="right_back_wheel">
    <visual>
      <origin rpy="1.57075 0 0" xyz="0 0 0"/>
      <geometry>
        <cylinder length="0.1" radius="0.035"/>
      </geometry>
      <material name="black"/>
    </visual>
  </link>
  <joint name="right_back_wheel_joint" type="fixed">
    <parent link="right_base"/>
    <child link="right_back_wheel"/>
    <origin rpy="0 0 0" xyz="-0.133333333333 0 -0.085"/>
  </joint>

  <link name="left_leg">
    <visual>
      <geometry>
        <box size="0.6 0.1 0.2"/>
      </geometry>
      <origin rpy="0 1.57075 0" xyz="0 0 -0.3"/>
      <material name="white"/>
    </visual>
  </link>

  <joint name="base_to_left_leg" type="fixed">
    <parent link="base_link"/>
    <child link="left_leg"/>
    <origin xyz="0 0.22 0.25"/>
  </joint>

  <link name="left_base">
    <visual>
      <geometry>
        <box size="0.4 0.1 0.1"/>
      </geometry>
      <material name="white"/>
    </visual>
  </link>

  <joint name="left_base_joint" type="fixed">
    <parent link="left_leg"/>
    <child link="left_base"/>
    <origin xyz="0 0 -0.6"/>
  </joint>

  <link name="left_front_wheel">
    <visual>
      <origin rpy="1.57075 0 0" xyz="0 0 0"/>
      <geometry>
        <cylinder length="0.1" radius="0.035"/>
      </geometry>
      <material name="black"/>
    </visual>
  </link>
  <joint name="left_front_wheel_joint" type="fixed">
    <parent link="left_base"/>
    <child link="left_front_wheel"/>
    <origin rpy="0 0 0" xyz="0.133333333333 0 -0.085"/>
  </joint>

  <link name="left_back_wheel">
    <visual>
      <origin rpy="1.57075 0 0" xyz="0 0 0"/>
      <geometry>
        <cylinder length="0.1" radius="0.035"/>
      </geometry>
      <material name="black"/>
    </visual>
  </link>
  <joint name="left_back_wheel_joint" type="fixed">
    <parent link="left_base"/>
    <child link="left_back_wheel"/>
    <origin rpy="0 0 0" xyz="-0.133333333333 0 -0.085"/>
  </joint>

  <joint name="gripper_extension" type="fixed">
    <parent link="base_link"/>
    <child link="gripper_pole"/>
    <origin rpy="0 0 0" xyz="0.19 0 0.2"/>
  </joint>

  <link name="gripper_pole">
    <visual>
      <geometry>
        <cylinder length="0.2" radius="0.01"/>
      </geometry>
      <origin rpy="0 1.57075 0 " xyz="0.1 0 0"/>
    </visual>
  </link>

  <joint name="left_gripper_joint" type="fixed">
    <origin rpy="0 0 0" xyz="0.2 0.01 0"/>
    <parent link="gripper_pole"/>
    <child link="left_gripper"/>
  </joint>

  <link name="left_gripper">
    <visual>
      <origin rpy="0.0 0 0" xyz="0 0 0"/>
      <geometry>
        <mesh filename="package://urdf_tutorial/meshes/l_finger.dae"/>
      </geometry>
    </visual>
  </link>

  <joint name="left_tip_joint" type="fixed">
    <parent link="left_gripper"/>
    <child link="left_tip"/>
  </joint>

  <link name="left_tip">
    <visual>
      <origin rpy="0.0 0 0" xyz="0.09137 0.00495 0"/>
      <geometry>
        <mesh filename="package://urdf_tutorial/meshes/l_finger_tip.dae"/>
      </geometry>
    </visual>
  </link>
  <joint name="right_gripper_joint" type="fixed">
    <origin rpy="0 0 0" xyz="0.2 -0.01 0"/>
    <parent link="gripper_pole"/>
    <child link="right_gripper"/>
  </joint>

  <link name="right_gripper">
    <visual>
      <origin rpy="-3.1415 0 0" xyz="0 0 0"/>
      <geometry>
        <mesh filename="package://urdf_tutorial/meshes/l_finger.dae"/>
      </geometry>
    </visual>
  </link>

  <joint name="right_tip_joint" type="fixed">
    <parent link="right_gripper"/>
    <child link="right_tip"/>
  </joint>

  <link name="right_tip">
    <visual>
      <origin rpy="-3.1415 0 0" xyz="0.09137 0.00495 0"/>
      <geometry>
        <mesh filename="package://urdf_tutorial/meshes/l_finger_tip.dae"/>
      </geometry>
    </visual>
  </link>

  <link name="head">
    <visual>
      <geometry>
        <sphere radius="0.2"/>
      </geometry>
      <material name="white"/>
    </visual>
  </link>
  <joint name="head_swivel" type="fixed">
    <parent link="base_link"/>
    <child link="head"/>
    <origin xyz="0 0 0.3"/>
  </joint>

  <link name="box">
    <visual>
      <geometry>
        <box size="0.08 0.08 0.08"/>
      </geometry>
      <material name="blue"/>
    </visual>
  </link>

  <joint name="tobox" type="fixed">
    <parent link="head"/>
    <child link="box"/>
    <origin xyz="0.1814 0 0.1414"/>
  </joint>
</robot>
```

### CLI: visualize any of the above

```bash
sudo apt install ros-jazzy-urdf-tutorial         # one-time
ros2 launch urdf_tutorial display.launch.py model:=urdf/05-visual.urdf
```

`display.launch.py` runs `robot_state_publisher` (loading the URDF as the
`robot_description` parameter), plus `joint_state_publisher_gui`, plus
`rviz2`. Because every joint here is `fixed`, the GUI shows no sliders.

In RViz, set **Fixed Frame** to `base_link`, then **Add → RobotModel** and
**Add → TF**. The model and frame triads should appear immediately.

---

## Building a Movable Robot Model with URDF
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Intermediate/URDF/Building-a-Movable-Robot-Model-with-URDF.html

This page replaces the all-`fixed` R2D2 from the previous example with a model
(`06-flexible.urdf`) that uses every other joint type. Once any joint becomes
non-fixed, `joint_state_publisher_gui` adds a slider for it; the slider value
flows through `/joint_states` to `robot_state_publisher`, which recomputes the
TF tree.

### The six URDF joint types

| type         | DoF | Bounded? | Notes                                                 |
|--------------|-----|----------|-------------------------------------------------------|
| `fixed`      | 0   | n/a      | Rigid weld. No `<axis>`, no `<limit>`.                |
| `revolute`   | 1   | yes      | Rotation about `<axis>`. `<limit lower upper effort velocity>` mandatory (radians, N·m, rad/s). |
| `continuous` | 1   | no       | Rotation about `<axis>` with no upper/lower bound (e.g. wheels). Still accepts `effort`/`velocity`. |
| `prismatic`  | 1   | yes      | Translation along `<axis>`. Limits in metres, m/s, N. |
| `floating`   | 6   | n/a      | Free 6-DoF — used to attach a base to the world.      |
| `planar`     | 2   | n/a      | Translation in the plane normal to `<axis>`.          |

### Joint sub-elements

- `<axis xyz="x y z"/>` — unit vector in the **child link**'s frame, defining
  the joint's rotation/translation axis. Only meaningful for revolute,
  continuous, prismatic, planar.
- `<limit lower="..." upper="..." effort="..." velocity="..."/>` — required
  for revolute and prismatic. `effort` is max force/torque; `velocity` is max
  speed. `continuous` joints need only `effort`/`velocity`.
- `<dynamics damping="..." friction="..."/>` — viscous damping (N·s/m or
  N·m·s/rad) and static friction (N or N·m). Both default to 0.
- `<calibration rising="..." falling="..."/>` — reference positions for
  joint calibration controllers.
- `<mimic joint="other_joint" multiplier="1.0" offset="0.0"/>` — slave
  this joint's position to another (`pos = multiplier*other_pos + offset`).
  Common for parallel-jaw grippers and four-bar linkages.
- `<safety_controller k_velocity="..." k_position="..." soft_lower_limit="..." soft_upper_limit="..."/>` — soft limits for
  ros_control safety.

### Key snippets

R2D2's head becomes a continuous joint about Z:

```xml
<joint name="head_swivel" type="continuous">
  <parent link="base_link"/>
  <child link="head"/>
  <axis xyz="0 0 1"/>
  <origin xyz="0 0 0.3"/>
</joint>
```

The gripper fingers use revolute joints with bounded angles:

```xml
<joint name="left_gripper_joint" type="revolute">
  <axis xyz="0 0 1"/>
  <limit effort="1000.0" lower="0.0" upper="0.548" velocity="0.5"/>
  <origin rpy="0 0 0" xyz="0.2 0.01 0"/>
  <parent link="gripper_pole"/>
  <child link="left_gripper"/>
</joint>
```

The gripper extension is prismatic — it slides the whole pole in/out:

```xml
<joint name="gripper_extension" type="prismatic">
  <parent link="base_link"/>
  <child link="gripper_pole"/>
  <limit effort="1000.0" lower="-0.38" upper="0" velocity="0.5"/>
  <origin rpy="0 0 0" xyz="0.19 0 0.2"/>
</joint>
```

(Note: the original `06-flexible.urdf` reuses the link/visual definitions from
`05-visual.urdf` and only swaps joint types/adds `<axis>`/`<limit>`.)

### CLI

```bash
ros2 launch urdf_tutorial display.launch.py model:=urdf/06-flexible.urdf
```

A `joint_state_publisher_gui` window opens with one slider per non-fixed joint
(head_swivel, gripper_extension, left_gripper_joint, right_gripper_joint).
Drag the sliders and the RViz model updates in real time. The pipeline:

```
joint_state_publisher_gui  --/joint_states-->  robot_state_publisher
                                              --/tf, /tf_static-->  rviz2
```

### Drone-project takeaway

For an autonomous drone, the airframe itself is usually one rigid body, so
all sensor mounts (stereo baseline, IMU, GPS antenna) are attached to
`base_link` with `fixed` joints. Use `continuous` only for actively spinning
parts you want simulated (gimbal yaw, propeller spin if you care to render
it). Use `revolute` for a 2-axis camera gimbal with mechanical stops. The
`mimic` tag is useful if a 2-axis gimbal has paired servos that must move
together.

---

## Adding Physical and Collision Properties to a URDF Model
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Intermediate/URDF/Adding-Physical-and-Collision-Properties-to-a-URDF-Model.html

To put a URDF into Gazebo (or any physics simulator), each link needs
`<collision>` and `<inertial>`. Without inertia, simulators either refuse to
load the model or treat it as massless and explode numerically.

### `<collision>`

Same level as `<visual>`, same children: `<geometry>` and optional
`<origin>`. The collision shape is what the physics engine actually checks
for contacts; it can be — and usually should be — a coarser approximation of
the visual mesh, both for performance (convex primitives are cheap) and to
add a safety bubble.

```xml
<collision>
  <geometry>
    <cylinder length="0.6" radius="0.2"/>
  </geometry>
</collision>
```

### `<inertial>`

```xml
<inertial>
  <mass value="10"/>
  <inertia ixx="1e-3" ixy="0.0" ixz="0.0"
           iyy="1e-3" iyz="0.0" izz="1e-3"/>
</inertial>
```

- `<mass value="..."/>` — kilograms.
- `<inertia ixx ixy ixz iyy iyz izz/>` — the upper triangle of the symmetric
  3×3 rotational inertia tensor about the link's centre of mass, expressed in
  the link's frame. Units kg·m².
- Optional `<origin xyz rpy/>` inside `<inertial>` shifts the centre of mass
  off the link origin.
- Sample formulas (about the centre, axes aligned with the principal axes of
  the shape):
  - **Solid box** of size (w, d, h): `Ixx = m*(d²+h²)/12`,
    `Iyy = m*(w²+h²)/12`, `Izz = m*(w²+d²)/12`, off-diagonals 0.
  - **Solid cylinder** of radius r, length l, axis Z: `Ixx = Iyy = m*(3r²+l²)/12`,
    `Izz = m*r²/2`.
  - **Solid sphere** of radius r: `Ixx = Iyy = Izz = 2*m*r²/5`.
- Rule of thumb cited by the page: never use literal zeros — values like
  `1e-3` keep mid-sized links numerically stable; very small/zero values
  cause simulators to explode.

### Joint dynamics

Inside any movable joint:

```xml
<dynamics damping="0.7" friction="0.1"/>
```

- `friction` — static friction. N for prismatic, N·m for revolute. Default 0.
- `damping` — viscous damping coefficient. N·s/m for prismatic,
  N·m·s/rad for revolute. Default 0.

### Contact coefficients (Gazebo extension, mentioned in passing)

Gazebo-specific friction / contact stiffness lives outside the URDF spec
proper — typically inside `<gazebo reference="link_name">` blocks with
`<mu1>`, `<mu2>`, `<kp>`, `<kd>` children. See the Gazebo / `<gazebo>`
section below.

### Example: a `base_link` with all three blocks

```xml
<link name="base_link">
  <visual>
    <geometry>
      <cylinder length="0.6" radius="0.2"/>
    </geometry>
    <material name="blue">
      <color rgba="0 0 .8 1"/>
    </material>
  </visual>

  <collision>
    <geometry>
      <cylinder length="0.6" radius="0.2"/>
    </geometry>
  </collision>

  <inertial>
    <mass value="10"/>
    <inertia ixx="1e-3" ixy="0.0" ixz="0.0"
             iyy="1e-3" iyz="0.0" izz="1e-3"/>
  </inertial>
</link>
```

The complete `07-physics.urdf` follows the same template — every link in
`05-visual.urdf` gains a matching `<collision>` (same geometry and origin as
the visual) and an `<inertial>` (mass appropriate to the part).

### CLI

```bash
ros2 launch urdf_tutorial display.launch.py model:=urdf/07-physics.urdf
```

(RViz only renders `<visual>`, so the model looks identical to
`06-flexible.urdf`. The collision/inertial data is what changes once you
launch into Gazebo.)

---

## Using Xacro to Clean Up a URDF File
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Intermediate/URDF/Using-Xacro-to-Clean-Up-a-URDF-File.html

Hand-rolled URDFs become unmaintainable past about 10 links — the same magic
numbers (wheel radius, body length, leg width) get pasted everywhere. Xacro
is an XML preprocessor that adds three things: **constants (properties)**,
**math expressions**, and **macros**. The output is plain URDF.

### Namespace

Every xacro file declares the xacro XML namespace on the root element; the
file extension is `.urdf.xacro` by convention:

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro" name="firefighter">
  ...
</robot>
```

### Properties (constants)

```xml
<xacro:property name="width"   value="0.2"/>
<xacro:property name="bodylen" value="0.6"/>

<link name="base_link">
  <visual>
    <geometry>
      <cylinder radius="${width}" length="${bodylen}"/>
    </geometry>
  </visual>
</link>
```

Properties can hold strings, numbers, or even XML blocks (with `<![CDATA[...]]>`).

### Math expressions

Inside `${...}`, xacro evaluates Python-like arithmetic: `+ - * /`, unary
negation, parentheses, plus the math functions `sin`, `cos`, and the
constant `pi`.

```xml
<cylinder radius="${wheeldiam/2}" length="0.1"/>
<origin xyz="${reflect*(width+.02)} 0 0.25"/>
<origin xyz="0 0 -${leglen/2}" rpy="0 ${pi/2} 0"/>
```

### Simple macros (no parameters)

```xml
<xacro:macro name="default_origin">
  <origin xyz="0 0 0" rpy="0 0 0"/>
</xacro:macro>

<xacro:default_origin/>
```

### Parameterised macros

```xml
<xacro:macro name="default_inertial" params="mass">
  <inertial>
    <mass value="${mass}"/>
    <inertia ixx="1e-3" ixy="0.0" ixz="0.0"
             iyy="1e-3" iyz="0.0"
             izz="1e-3"/>
  </inertial>
</xacro:macro>

<xacro:default_inertial mass="10"/>
```

### Block parameters (`*name`) and `xacro:insert_block`

A parameter prefixed with `*` accepts a chunk of XML rather than a string.
Inside the macro you splice it in with `<xacro:insert_block name="..."/>`.

```xml
<xacro:macro name="blue_shape" params="name *shape">
  <link name="${name}">
    <visual>
      <geometry>
        <xacro:insert_block name="shape"/>
      </geometry>
      <material name="blue"/>
    </visual>
  </link>
</xacro:macro>

<xacro:blue_shape name="base_link">
  <cylinder radius=".42" length=".01"/>
</xacro:blue_shape>
```

### Reflect / prefix idiom (the leg macro)

The canonical xacro trick: one macro generates symmetric pairs by passing a
`reflect` parameter of `+1` / `-1`.

```xml
<xacro:macro name="leg" params="prefix reflect">
  <link name="${prefix}_leg">
    <visual>
      <geometry>
        <box size="${leglen} 0.1 0.2"/>
      </geometry>
      <origin xyz="0 0 -${leglen/2}" rpy="0 ${pi/2} 0"/>
      <material name="white"/>
    </visual>
  </link>
  <joint name="base_to_${prefix}_leg" type="fixed">
    <parent link="base_link"/>
    <child link="${prefix}_leg"/>
    <origin xyz="0 ${reflect*(width+.02)} 0.25"/>
  </joint>
</xacro:macro>

<xacro:leg prefix="right" reflect="1"/>
<xacro:leg prefix="left"  reflect="-1"/>
```

### Includes and conditionals

- `<xacro:include filename="other.xacro"/>` — pulls in another xacro file
  (paths are relative to the current file or absolute via `$(find pkg)`).
- `<xacro:if value="${expr}">...</xacro:if>` — emit the children only if
  `expr` is truthy.
- `<xacro:unless value="${expr}">...</xacro:unless>` — the negation.
- `$(arg name)` and `$(find pkg_name)` — substitution-args (set with
  `xacro arg:=value` on the CLI), and the package-share-path lookup,
  respectively.

### Convert xacro → URDF on the command line

```bash
xacro model.xacro > model.urdf
# or via ros2:
ros2 run xacro xacro model.xacro -o model.urdf
```

You can then validate the result with:

```bash
check_urdf model.urdf      # comes from liburdfdom-tools
```

### Use a xacro directly from a launch file

The recommended pattern (no temp files, xacro re-evaluated on every launch):

```python
import launch_ros
from launch import LaunchDescription
from launch.substitutions import Command
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_path

def generate_launch_description():
    path_to_urdf = get_package_share_path('turtlebot3_description') \
        / 'urdf' / 'turtlebot3_burger.urdf'

    robot_state_publisher_node = launch_ros.actions.Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': ParameterValue(
                Command(['xacro ', str(path_to_urdf)]),
                value_type=str
            )
        }]
    )
    return LaunchDescription([robot_state_publisher_node])
```

Note the trailing space inside `'xacro '` — `Command` joins the list with no
separator, so the space is required to keep `xacro` and the path apart.

### Visualize a xacro file

```bash
ros2 launch urdf_tutorial display.launch.py model:=urdf/08-macroed.urdf.xacro
```

`display.launch.py` from `urdf_tutorial` already understands `.urdf.xacro`
extensions and runs xacro internally. For the `urdf_launch` package, see the
Exporting section below.

---

## Using URDF with robot_state_publisher (C++)
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Intermediate/URDF/Using-URDF-with-Robot-State-Publisher-cpp.html

Drives an R2D2 model around in a circle by publishing `JointState` messages
plus a root `odom → axis` transform. `robot_state_publisher` then walks the
URDF and publishes one TF per joint.

### Package layout

```
urdf_tutorial_cpp/
├── CMakeLists.txt
├── package.xml
├── launch/
│   └── launch.py
├── src/
│   └── urdf_tutorial.cpp
└── urdf/
    ├── r2d2.urdf.xml
    └── r2d2.rviz
```

### `src/urdf_tutorial.cpp`

```cpp
#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/quaternion.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <tf2_ros/transform_broadcaster.h>
#include <tf2_geometry_msgs/tf2_geometry_msgs.hpp>
#include <cmath>
#include <thread>
#include <chrono>

using namespace std::chrono;

class StatePublisher : public rclcpp::Node {
public:
    StatePublisher(rclcpp::NodeOptions options=rclcpp::NodeOptions())
        : Node("state_publisher", options) {
        joint_pub_  = this->create_publisher<sensor_msgs::msg::JointState>("joint_states", 10);
        broadcaster = std::make_shared<tf2_ros::TransformBroadcaster>(this);
        RCLCPP_INFO(this->get_logger(), "Starting state publisher");
        timer_ = this->create_wall_timer(33ms, std::bind(&StatePublisher::publish, this));
    }

private:
    rclcpp::Publisher<sensor_msgs::msg::JointState>::SharedPtr joint_pub_;
    std::shared_ptr<tf2_ros::TransformBroadcaster> broadcaster;
    rclcpp::TimerBase::SharedPtr timer_;

    const double degree = M_PI / 180.0;
    double tilt = 0., tinc = degree;
    double swivel = 0.;
    double angle = 0.;
    double height = 0., hinc = 0.005;

    void publish();
};

void StatePublisher::publish() {
    geometry_msgs::msg::TransformStamped t;
    sensor_msgs::msg::JointState joint_state;

    const auto ts = this->get_clock()->now();
    joint_state.header.stamp = ts;
    joint_state.name     = {"swivel", "tilt", "periscope"};
    joint_state.position = {swivel, tilt, height};

    t.header.stamp    = ts;
    t.header.frame_id = "odom";
    t.child_frame_id  = "axis";

    t.transform.translation.x = cos(angle) * 2;
    t.transform.translation.y = sin(angle) * 2;
    t.transform.translation.z = 0.7;
    tf2::Quaternion q;
    q.setRPY(0, 0, angle + M_PI / 2);
    t.transform.rotation.x = q.x();
    t.transform.rotation.y = q.y();
    t.transform.rotation.z = q.z();
    t.transform.rotation.w = q.w();

    tilt += tinc;
    if (tilt < -0.5 || tilt > 0.0) tinc *= -1;
    height += hinc;
    if (height > 0.2 || height < 0.0) hinc *= -1;
    swivel += degree;
    angle  += degree;

    broadcaster->sendTransform(t);
    joint_pub_->publish(joint_state);

    RCLCPP_INFO_THROTTLE(this->get_logger(), *this->get_clock(), 1000,
                         "Publishing joint state");
}

int main(int argc, char *argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<StatePublisher>());
    rclcpp::shutdown();
    return 0;
}
```

### `launch/launch.py`

```python
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import FileContent, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')

    urdf = FileContent(
        PathJoinSubstitution([FindPackageShare('urdf_tutorial_cpp'), 'urdf', 'r2d2.urdf.xml']))

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time, 'robot_description': urdf}],
            arguments=[urdf]),
        Node(
            package='urdf_tutorial_cpp',
            executable='urdf_tutorial_cpp',
            name='urdf_tutorial_cpp',
            output='screen'),
    ])
```

`FileContent(...)` reads the URDF from disk at launch time and passes the raw
XML string as the `robot_description` parameter — `robot_state_publisher`
parses that string, builds the kinematic tree, subscribes to
`/joint_states`, and republishes one TF per joint at the same rate.

### `CMakeLists.txt`

```cmake
cmake_minimum_required(VERSION 3.8)
project(urdf_tutorial_cpp)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
find_package(rclcpp REQUIRED)

add_executable(urdf_tutorial_cpp src/urdf_tutorial.cpp)

ament_target_dependencies(urdf_tutorial_cpp
  geometry_msgs
  sensor_msgs
  tf2_ros
  tf2_geometry_msgs
  rclcpp
)

install(TARGETS
  urdf_tutorial_cpp
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY
  launch
  DESTINATION share/${PROJECT_NAME}
)

install(DIRECTORY
  urdf
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
```

The two `install(DIRECTORY ...)` rules are the load-bearing piece for any
URDF-shipping package: they put `urdf/` and `launch/` under
`install/<pkg>/share/<pkg>/` so that `FindPackageShare` and the
`package://urdf_tutorial_cpp/...` URIs resolve correctly at runtime.

### Build, run, view

```bash
cd src
ros2 pkg create --build-type ament_cmake --license Apache-2.0 urdf_tutorial_cpp \
  --dependencies rclcpp geometry_msgs sensor_msgs tf2_ros tf2_geometry_msgs
cd urdf_tutorial_cpp
mkdir -p urdf
# (drop r2d2.urdf.xml and r2d2.rviz into urdf/, fill in src/, launch/)
cd ..
colcon build --symlink-install --packages-select urdf_tutorial_cpp
source install/setup.bash
ros2 launch urdf_tutorial_cpp launch.py
# in another terminal:
rviz2 -d install/urdf_tutorial_cpp/share/urdf_tutorial_cpp/urdf/r2d2.rviz
```

In RViz: set **Fixed Frame = odom**, then **Add → RobotModel** (it picks up
the `robot_description` topic / parameter automatically) and **Add → TF**.
The R2D2 should appear and orbit the origin.

### Note on joint_state_publisher

This tutorial does **not** use `joint_state_publisher` — the custom C++ node
publishes `JointState` directly. In setups where you want manual control,
substitute `joint_state_publisher_gui` instead and remove the custom node.

---

## Using URDF with robot_state_publisher (Python)
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Intermediate/URDF/Using-URDF-with-Robot-State-Publisher-py.html

Same demo, Python flavour. `ament_python` installs URDFs and launch files via
`setup.py`'s `data_files`, not via CMake `install(DIRECTORY)`.

### Package layout

```
urdf_tutorial_r2d2/
├── package.xml
├── setup.py
├── setup.cfg
├── resource/
│   └── urdf_tutorial_r2d2
├── launch/
│   └── demo_launch.py
├── urdf/
│   ├── r2d2.urdf.xml
│   └── r2d2.rviz
└── urdf_tutorial_r2d2/
    ├── __init__.py
    └── state_publisher.py
```

### `urdf_tutorial_r2d2/state_publisher.py`

```python
from math import sin, cos, pi
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile
from geometry_msgs.msg import Quaternion
from sensor_msgs.msg import JointState
from tf2_ros import TransformBroadcaster, TransformStamped


class StatePublisher(Node):

    def __init__(self):
        rclpy.init()
        super().__init__('state_publisher')

        qos_profile = QoSProfile(depth=10)
        self.joint_pub  = self.create_publisher(JointState, 'joint_states', qos_profile)
        self.broadcaster = TransformBroadcaster(self, qos=qos_profile)
        self.nodeName = self.get_name()
        self.get_logger().info("{0} started".format(self.nodeName))

        degree = pi / 180.0
        loop_rate = self.create_rate(30)

        # robot state
        tilt   = 0.;    tinc   = degree
        swivel = 0.
        angle  = 0.
        height = 0.;    hinc   = 0.005

        # message declarations
        odom_trans = TransformStamped()
        odom_trans.header.frame_id = 'odom'
        odom_trans.child_frame_id  = 'axis'
        joint_state = JointState()

        try:
            while rclpy.ok():
                rclpy.spin_once(self)

                now = self.get_clock().now()
                joint_state.header.stamp = now.to_msg()
                joint_state.name     = ['swivel', 'tilt', 'periscope']
                joint_state.position = [swivel, tilt, height]

                # moving in a circle of radius 2
                odom_trans.header.stamp = now.to_msg()
                odom_trans.transform.translation.x = cos(angle) * 2
                odom_trans.transform.translation.y = sin(angle) * 2
                odom_trans.transform.translation.z = 0.7
                odom_trans.transform.rotation = \
                    euler_to_quaternion(0, 0, angle + pi / 2)  # roll, pitch, yaw

                self.joint_pub.publish(joint_state)
                self.broadcaster.sendTransform(odom_trans)

                tilt += tinc
                if tilt < -0.5 or tilt > 0.0:
                    tinc *= -1
                height += hinc
                if height > 0.2 or height < 0.0:
                    hinc *= -1
                swivel += degree
                angle  += degree / 4

                loop_rate.sleep()

        except KeyboardInterrupt:
            pass


def euler_to_quaternion(roll, pitch, yaw):
    qx = sin(roll/2)*cos(pitch/2)*cos(yaw/2) - cos(roll/2)*sin(pitch/2)*sin(yaw/2)
    qy = cos(roll/2)*sin(pitch/2)*cos(yaw/2) + sin(roll/2)*cos(pitch/2)*sin(yaw/2)
    qz = cos(roll/2)*cos(pitch/2)*sin(yaw/2) - sin(roll/2)*sin(pitch/2)*cos(yaw/2)
    qw = cos(roll/2)*cos(pitch/2)*cos(yaw/2) + sin(roll/2)*sin(pitch/2)*sin(yaw/2)
    return Quaternion(x=qx, y=qy, z=qz, w=qw)


def main():
    node = StatePublisher()


if __name__ == '__main__':
    main()
```

### `launch/demo_launch.py`

```python
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import FileContent, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    urdf = FileContent(
        PathJoinSubstitution([FindPackageShare('urdf_tutorial_r2d2'), 'r2d2.urdf.xml']))

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time, 'robot_description': urdf}],
            arguments=[urdf]),
        Node(
            package='urdf_tutorial_r2d2',
            executable='state_publisher',
            name='state_publisher',
            output='screen'),
    ])
```

### `setup.py` additions (the load-bearing bits)

```python
import os
from glob import glob
from setuptools import setup, find_packages

package_name = 'urdf_tutorial_r2d2'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # install launch files
        (os.path.join('share', package_name, 'launch'), glob('launch/*')),
        # install URDF / RViz config (referenced via FindPackageShare(pkg))
        (os.path.join('share', package_name), glob('urdf/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    author='you',
    maintainer='you',
    maintainer_email='you@example.com',
    description='URDF + state publisher demo',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'state_publisher = urdf_tutorial_r2d2.state_publisher:main',
        ],
    },
)
```

### Build, run, view

```bash
mkdir -p second_ros2_ws/src
cd second_ros2_ws/src
ros2 pkg create --build-type ament_python --license Apache-2.0 \
    urdf_tutorial_r2d2 --dependencies rclpy
cd urdf_tutorial_r2d2
mkdir -p urdf launch
# drop in r2d2.urdf.xml, r2d2.rviz, demo_launch.py, state_publisher.py;
# edit setup.py as above
cd ../..
colcon build --symlink-install --packages-select urdf_tutorial_r2d2
source install/setup.bash
ros2 launch urdf_tutorial_r2d2 demo_launch.py
# new terminal
rviz2 -d `ros2 pkg prefix urdf_tutorial_r2d2 --share`/r2d2.rviz
```

In RViz: **Fixed Frame = odom**, then **Add → RobotModel** and **Add → TF**.

### Mental model: what each node does

```
state_publisher (your code)
  publishes /joint_states  (sensor_msgs/JointState)
  publishes /tf            (odom -> axis)         via TransformBroadcaster

robot_state_publisher
  reads parameter robot_description  (the URDF text)
  subscribes /joint_states
  publishes /tf            (axis -> base_link -> ... per the URDF)
  publishes /tf_static     (any joint that never changes)

rviz2
  reads /tf, /tf_static
  reads parameter robot_description (or topic /robot_description)
  renders the model in the chosen Fixed Frame
```

For a real drone you replace the custom `state_publisher` with whatever
publishes the world→base transform — e.g. an EKF, VIO node, or a
ground-truth Gazebo plugin — and `robot_state_publisher` handles every
sensor frame downstream of `base_link` for free.

---

## Exporting an URDF File
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Intermediate/URDF/Exporting-an-URDF-File.html

Short index page: ROS core does not ship its own CAD-to-URDF tool, but the
community maintains exporters for every major CAD program. None of these are
maintained by the ROS core team — quality varies, evaluate per project.

### CAD exporters

- **Blender** — phobos: https://github.com/dfki-ric/phobos
- **CREO Parametric** — creo2urdf: https://github.com/icub-tech-iit/creo2urdf
- **FreeCAD** — ROS Workbench (CROSS): https://github.com/galou/freecad.cross
- **FreeCAD** — RobotCAD / OVERCROSS: https://github.com/drfenixion/freecad.overcross
- **FreeCAD → Gazebo** — freecad_to_gazebo: https://github.com/Dave-Elec/freecad_to_gazebo
- **Fusion 360** — dheena2k2/fusion2urdf-ros2: https://github.com/dheena2k2/fusion2urdf-ros2
- **Fusion 360** (with ros2_control + closed loops) — Adriaeik/fusion2URDF: https://github.com/Adriaeik/fusion2URDF
- **Fusion 360 → SDF** — FusionSDF: https://github.com/andreasBihlmaier/FusionSDF
- **OnShape** — onshape-to-robot: https://github.com/Rhoban/onshape-to-robot
- **SolidWorks** — official solidworks_urdf_exporter: https://github.com/ros/solidworks_urdf_exporter
- **Multi-CAD library** (Fusion 360, OnShape, SolidWorks) — ExportURDF: https://github.com/daviddorf2023/ExportURDF

### Other conversion tools

- **SDF → URDF parser (Gazebo)** — sdformat_urdf: https://github.com/ros/sdformat_urdf/tree/jazzy
- **SDF → URDF in Python** — pysdf: https://github.com/andreasBihlmaier/pysdf
- **URDF → Webots** — urdf2webots: https://github.com/cyberbotics/urdf2webots
- **Blender robotics utils** — https://github.com/robotology/blender-robotics-utils/
- **CoppeliaSim URDF exporter** — https://manual.coppeliarobotics.com/en/importExport.htm#urdf
- **NVIDIA Isaac Sim URDF exporter** — https://docs.omniverse.nvidia.com/isaacsim/latest/advanced_tutorials/tutorial_advanced_export_urdf.html

### Viewers / generic launch helpers

- **`urdf_launch`** — reusable launch files for any URDF/Xacro:
  https://github.com/ros/urdf_launch  (use this instead of writing your own
  launch file every time).
- **Web URDF viewer** — https://github.com/gkjohnson/urdf-loaders/ ; live
  demo: https://gkjohnson.github.io/urdf-loaders/javascript/example/bundle/index.html
- **View SDF in RViz** — https://github.com/Yadunund/view_sdf_rviz
- **JupyterLab URDF viewer** — https://github.com/IsabelParedes/jupyterlab-urdf

---

# Appendix A: sensor frames for a drone perception stack

Although not in the tutorials, the rest of the project uses these frames —
keep them straight when authoring the drone URDF.

### REP-103 axis convention

Body frames (i.e. `base_link` and anything fixed to it): **X forward, Y left,
Z up**, RHS. World frames (`map`, `odom`): same convention; `map` Z aligned
with gravity.

### REP-105 frame hierarchy

```
map  --(non-continuous)-->  odom  --(continuous)-->  base_link
```

`base_link` is the canonical robot frame; everything physical (cameras, IMU,
GPS antenna) is a fixed child of `base_link`.

### Camera optical frames

ROS image pipelines (`image_proc`, `depth_image_proc`, AprilTag, ORB-SLAM
ROS wrappers) expect the **optical** frame convention: **Z forward (down the
lens), X right, Y down**. By convention the optical frame is named
`<camera>_optical_frame` and is a fixed child of the body-frame
`<camera>_link` (which uses the standard X-forward body convention). The
fixed offset is a `-pi/2` rotation about the body Z, then `-pi/2` about the
new X — a single rpy of `-1.5708 0 -1.5708`.

```xml
<link name="stereo_left_link"/>
<link name="stereo_left_optical_frame"/>
<joint name="stereo_left_optical_joint" type="fixed">
  <parent link="stereo_left_link"/>
  <child  link="stereo_left_optical_frame"/>
  <origin xyz="0 0 0" rpy="-1.5708 0 -1.5708"/>
</joint>
```

The `camera_info` published on `/stereo/left/camera_info` must list
`frame_id = stereo_left_optical_frame`.

### Stereo baseline

Make `stereo_right_link` a fixed child of `stereo_left_link` offset purely
along Y (left → right baseline), e.g. `xyz="0 -0.12 0"` for a 12 cm
baseline. Add a parallel `stereo_right_optical_frame` with the same
`-1.5708 0 -1.5708` rotation.

### IMU

Mount as a fixed child of `base_link`. The IMU publisher must populate
`Imu.header.frame_id = imu_link` and `robot_state_publisher` will handle the
TF; downstream EKF (`robot_localization`) fuses it in body frame.

---

# Appendix B: `<gazebo>` extensions

URDF doesn't natively model sensors, controllers, or material properties for
simulation — Gazebo extends it via `<gazebo>` blocks that the URDF parser
ignores but the Gazebo URDF→SDF translator picks up. Two flavours:

### Per-link material / contact

```xml
<gazebo reference="base_link">
  <material>Gazebo/Blue</material>
  <mu1>0.2</mu1>
  <mu2>0.2</mu2>
  <kp>1e6</kp>
  <kd>1.0</kd>
  <selfCollide>false</selfCollide>
</gazebo>
```

### Sensors and plugins (camera example)

```xml
<gazebo reference="stereo_left_link">
  <sensor name="left_camera" type="camera">
    <update_rate>30.0</update_rate>
    <camera>
      <horizontal_fov>1.3962634</horizontal_fov>
      <image>
        <width>1280</width>
        <height>720</height>
        <format>R8G8B8</format>
      </image>
      <clip>
        <near>0.1</near>
        <far>100.0</far>
      </clip>
    </camera>
    <plugin name="camera_controller" filename="libgazebo_ros_camera.so">
      <ros>
        <namespace>/stereo/left</namespace>
        <remapping>image_raw:=image_raw</remapping>
        <remapping>camera_info:=camera_info</remapping>
      </ros>
      <camera_name>left</camera_name>
      <frame_name>stereo_left_optical_frame</frame_name>
    </plugin>
  </sensor>
</gazebo>
```

### IMU plugin

```xml
<gazebo reference="imu_link">
  <sensor name="imu_sensor" type="imu">
    <always_on>true</always_on>
    <update_rate>200</update_rate>
    <plugin filename="libgazebo_ros_imu_sensor.so" name="imu_plugin">
      <ros><namespace>/imu</namespace></ros>
      <topic_name>data</topic_name>
      <frame_name>imu_link</frame_name>
    </plugin>
  </sensor>
</gazebo>
```

(Plugin filenames here follow the Gazebo Classic convention; for new Gazebo
(Harmonic / Sim) the plugin names live under `gz-sim-*-system` and are wired
through `<gz>` blocks instead. Check the version of Gazebo you're targeting
before copy-pasting.)

### `<transmission>`

Used by `ros2_control` to bind URDF joints to hardware interfaces. Lives at
the same level as `<joint>`, references the joint by name, and declares the
hardware/transmission type. Not used in the visualisation tutorials but
required as soon as you want `JointTrajectoryController` etc. to actuate the
joint.

```xml
<transmission name="head_swivel_trans">
  <type>transmission_interface/SimpleTransmission</type>
  <joint name="head_swivel"><hardwareInterface>hardware_interface/PositionJointInterface</hardwareInterface></joint>
  <actuator name="head_swivel_motor"><hardwareInterface>hardware_interface/PositionJointInterface</hardwareInterface></actuator>
</transmission>
```
