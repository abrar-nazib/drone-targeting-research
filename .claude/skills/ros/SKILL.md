---
name: ros
description: Comprehensive ROS 2 Jazzy Jalisco reference (~225 documentation pages summarized) covering installation, the full ros2 CLI, every Beginner/Intermediate/Advanced tutorial, all How-To Guides, every Concept page, the Launch system, tf2, URDF/Xacro, RViz, testing, lifecycle/composition/QoS/executors, Gazebo Harmonic + ros_gz bridge, Webots, MVSim, security, DDS tuning, and the Jazzy release notes. Use whenever the user is working inside a ROS 2 project, asking about ros2 CLI commands, writing/debugging launch files, designing nodes or message flows, wiring a simulator to ROS, or troubleshooting workspace/build issues. Triggered by `ros2 ...`, `colcon`, `rosdep`, `gz sim`, `ros_gz_bridge`, `package.xml`, `CMakeLists.txt` in an ament context, `.launch.py` files, `rclpy`/`rclcpp` imports, URDF/Xacro/SDF files, or any `/opt/ros/jazzy` paths.
---

# ROS 2 Jazzy Jalisco — comprehensive reference

This skill is an opinionated index over the full Jazzy documentation
(<https://docs.ros.org/en/jazzy/>), tailored for a drone perception
research project running on **Ubuntu 24.04** with **Gazebo Harmonic** as
the target simulator. The deep content is split into 17 reference files
under `reference/`. **Read the relevant reference file before reaching
for `WebFetch` against `docs.ros.org`** — the summaries already include
the commands, code patterns, and gotchas you would otherwise re-derive.

## How to use this skill

1. Find the topic in the index below.
2. `Read` the corresponding `reference/NN_*.md` file (each is a few hundred
   lines, fully self-contained for that topic).
3. Only `WebFetch` the canonical URL when the reference file flags
   "see canonical doc for …" (long config schemas, license text,
   Gazebo-side asset gallery URLs, etc.).
4. For non-trivial questions (designing message flows, wiring the Gazebo
   bridge for stereo+segmentation, tuning QoS, debugging missing
   transforms), delegate to the `ros-expert` subagent — it is briefed on
   this project's exact distro pairing and perception-only scope.

## Project-locked defaults

- Distribution: **Jazzy Jalisco** on **Ubuntu 24.04 Noble**. Apt prefix
  is `ros-jazzy-*`. Do not produce commands for Humble, Iron, Foxy, or
  Rolling without explicit user confirmation.
- Simulator: **Gazebo Harmonic** (modern Gazebo, `gz sim` CLI), bridged
  with `ros_gz_bridge`. **Not** Gazebo Classic (`gazebo`, `gazebo_ros`).
  See [reference/11_simulators.md](reference/11_simulators.md).
- Build tool: **colcon** (with `--symlink-install` for Python). Workspace
  layout: `ros2_ws/src/<pkg>`. Always source the underlay first
  (`/opt/ros/jazzy/setup.bash`), then the overlay
  (`install/local_setup.bash`), in a **fresh terminal**.
- Default RMW in Jazzy is **Fast DDS** (`rmw_fastrtps_cpp`). Cyclone DDS,
  RTI Connext, and Zenoh are alternatives — see
  [reference/14_concepts_intermediate_advanced.md](reference/14_concepts_intermediate_advanced.md)
  and [reference/16_howto_runtime.md](reference/16_howto_runtime.md).

## Reference index

| # | File | Coverage |
|---|------|----------|
| 01 | [Installation & Platform Setup](reference/01_installation.md) | Ubuntu deb install, Windows/RHEL/macOS, build-from-source, Raspberry Pi, install troubleshooting (~14 pages). |
| 02 | [Beginner: CLI Tools](reference/02_beginner_cli.md) | `ros2 node/topic/service/param/action`, turtlesim walkthrough, `rqt_console`, multi-node launch, `ros2 bag` (~11 pages). |
| 03 | [Beginner: Client Libraries](reference/03_beginner_client_libraries.md) | colcon, workspace, packages, full pub/sub/service/client skeletons in C++ and Python, custom .msg/.srv/.action, parameters in classes, ros2doctor, pluginlib (~14 pages). |
| 04 | [Intermediate: Misc](reference/04_intermediate_misc.md) | rosdep, custom actions and full action server/client skeletons (C++/Py), composable nodes, composition, NodeInterfaces template, parameter-change monitoring (~10 pages). |
| 05 | [Launch System](reference/05_launch.md) | Python launch files, all action/substitution types, event handlers, large-project structuring, XML/YAML formats, composable-node containers, `--ros-args` syntax (~8 pages). |
| 06 | [tf2 — Coordinate Frames](reference/06_tf2.md) | Concept page + all 14 tf2 tutorials: static/dynamic broadcasters, listeners, lookup_transform, time travel, MessageFilter, debugging, quaternions (~15 pages). **Critical for the drone sensor stack.** |
| 07 | [URDF, Xacro & robot_state_publisher](reference/07_urdf.md) | Visual model, joints, collisions/inertia, Xacro macros, robot_state_publisher launch wiring, exporting from CAD (~7 pages). **Critical for the drone body model and sensor mounts.** |
| 08 | [RViz & Testing](reference/08_rviz_testing.md) | RViz user guide, all built-in displays, MarkerArray patterns, custom Display/Panel plugins; `colcon test`, ament_lint, GTest, pytest, launch_testing (~11 pages). |
| 09 | [Demos](reference/09_demos.md) | QoS in lossy networks, lifecycle (managed) nodes, intra-process comms, real-time programming, dummy robot, logging, content filtering, service introspection, wait-for-ack (~10 pages). |
| 10 | [Advanced Tutorials](reference/10_advanced.md) | Custom rosdep keys, topic statistics, Fast DDS Discovery Server, custom allocators, ament_lint, Fast DDS XML profiles, dynamic discovery, recording/reading bags from code (C++ and Py), rqt_bag plugins, ros2_tracing, custom RMW (~13 pages). |
| 11 | [Simulators](reference/11_simulators.md) | **Gazebo Harmonic deep-dive**: install, `gz sim`/`gz topic`/`gz model`/`gz service` CLIs, SDF world structure, all sensor SDF (camera/depth/rgbd/imu/lidar/segmentation), `ros_gz_bridge` syntax + full message-type pairing table, image_bridge, bridge.launch.py patterns. Plus Webots and MVSim for completeness (~17 pages). **Highest-priority section for this project.** |
| 12 | [Security](reference/12_security.md) | SROS2, keystore, enclaves, multi-machine certs, traffic inspection, access controls, deployment guidelines (~6 pages). Lower priority for single-machine sim. |
| 13 | [Concepts: Basic](reference/13_concepts_basic.md) | Nodes, discovery, interfaces, topics, services, actions, parameters, CLI tools, launch, client libraries — the canonical vocabulary used everywhere else (~11 pages). |
| 14 | [Concepts: Intermediate & Advanced](reference/14_concepts_intermediate_advanced.md) | ROS_DOMAIN_ID, middleware vendors, logging, **QoS profiles full reference**, executors and callback groups, topic statistics, RQt, composition, cross-compilation, security, build system, internal interfaces, RMW (~14 pages). |
| 15 | [How-To: Build & Package](reference/15_howto_build.md) | Developing/documenting a package, ament_cmake and ament_cmake_python full macro reference, ROS 1→ROS 2 migration tables, releasing with bloom, custom debs, building with tracing, cross-compilation, Python packages, variants, custom rosdistro, core maintainer guide, topics-vs-services-vs-actions decision guide (~19 pages). |
| 16 | [How-To: Runtime, Debug & Integration](reference/16_howto_runtime.md) | DDS kernel tuning, QoS overrides for bag playback, multiple RMW implementations, sync-vs-async deadlock fix, callback groups, zero-copy loaned messages, `ros2 param` deep-dive, node CLI args, gdb/coredumps, IDEs, VSCode+Docker, Foxglove, ros1_bridge (~14 pages). |
| 17 | [The ROS 2 Project](reference/17_project.md) | Governance, contributing, roadmap, **full Jazzy Jalisco release notes** (every new feature, breaking change, removal), platform-support tiers, EOL policy, glossary, citations, contact (~15 pages). |

Total: ~17,500 lines / ~625 KB / ~225 doc pages summarized.

## Quick "where do I look" map

| Question                                            | File |
|-----------------------------------------------------|------|
| How do I install ROS 2 Jazzy on this machine?       | 01 |
| What does `ros2 topic echo` (or any `ros2 ...`) do? | 02 |
| How do I write my first publisher/subscriber?       | 03 |
| How do I write an action server?                    | 04 |
| How do I write a launch file?                       | 05 |
| How do I publish a static transform from camera to base_link? | 06 |
| How do I model the drone body in URDF?              | 07 |
| How do I visualize my point cloud / image / tf tree in RViz? | 08 |
| How do I make my node a lifecycle (managed) node?   | 09 |
| How do I record a bag from inside my node?          | 10 |
| How do I install Gazebo Harmonic and bridge `/camera`? | 11 |
| What QoS profile should my camera subscriber use?   | 14 (QoS section) |
| Why does my service call deadlock from a callback?  | 16 (Sync-vs-Async) |
| What are the breaking changes from Iron to Jazzy?   | 17 (Release-Jazzy section) |

## Hard-won gotchas (worth remembering before each session)

1. **Build then source in a fresh shell.** Do not `colcon build` and source
   the overlay in the same terminal — env vars from the build leak in.
2. **Source order**: underlay (`/opt/ros/jazzy/setup.bash`) **before** the
   overlay (`install/local_setup.bash`). The overlay extends the underlay.
3. **`use_sim_time:=true` everywhere** when running with Gazebo, and bridge
   `/clock`. Otherwise tf2 lookups silently fail because nodes use wallclock.
4. **QoS mismatch is the #1 silent subscriber bug.** Camera/lidar topics
   need `SensorDataQoS` (BEST_EFFORT, VOLATILE, depth=5). If `ros2 topic
   echo` works but your subscriber callback never fires, it is QoS.
5. **Modern Gazebo, not Gazebo Classic.** Anything that says
   `gazebo_ros_pkgs`, `roslaunch`, `<gazebo_ros>` plugin tags, or `gazebo`
   (no `gz`) on the CLI is the wrong era for Jazzy.
5b. **`gz` is a ROS-vendored binary on this machine.** `sudo apt install
   ros-jazzy-ros-gz` installs Gazebo Harmonic via vendor packages, **not**
   as the standalone `gz-harmonic` Debian. The `gz` binary lives at
   `/opt/ros/jazzy/opt/gz_tools_vendor/bin/gz` and is only on `$PATH`
   after sourcing `/opt/ros/jazzy/setup.bash`. If `gz sim --version`
   prints nothing or `which gz` is empty, the shell isn't sourced — Gazebo
   is fine. See [reference/11_simulators.md](reference/11_simulators.md)
   "Default install" for the full vendor-package list.
6. **Apt prefix is `ros-jazzy-*`.** A `ros-humble-*` package coexisting in
   the same install will silently break things; check `printenv ROS_DISTRO`
   first.
7. **Files installed via `setup.py data_files` (Python) or `install(...)`
   in `CMakeLists.txt` (C++).** Otherwise launch/config/URDF files are not
   in the install tree after `colcon build` and your launch file fails to
   find them.
8. **GitHub auth on this machine is SSH only** (per global rules). Switch
   any `https://github.com/...` remote to `git@github.com:...` before
   pushing.

## When to escalate to the `ros-expert` agent

The reference files cover Jazzy's documented surface. Reach for the
`ros-expert` subagent when:

- Designing a multi-package architecture for the drone stack.
- Writing or reviewing a non-trivial URDF/SDF or launch composition.
- Wiring `ros_gz_bridge` for a custom sensor combination (stereo + depth
  + segmentation + IMU + clock all at once).
- Debugging a problem that involves more than one of: tf2, QoS,
  use_sim_time, executor/callback-group choice.
- Picking a strategy that requires weighing tradeoffs (lifecycle vs
  plain node, composition vs separate processes, DDS-Security vs
  trusted-network, etc.).
