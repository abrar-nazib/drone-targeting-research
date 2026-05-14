# Intermediate & Advanced Concepts (ROS 2 Jazzy)

> Indexes: Concepts/Intermediate.html, Concepts/Advanced.html

## Intermediate

### Intermediate Concepts (index)
**Source**: https://docs.ros.org/en/jazzy/Concepts/Intermediate.html

Index page listing eleven intermediate-level topics that build on the beginner
material:

1. The `ROS_DOMAIN_ID` — DDS domain isolation.
2. Different ROS 2 middleware vendors — choosing an RMW.
3. Logging and logger configuration.
4. Quality of Service settings.
5. Executors — callback scheduling.
6. Topic statistics — runtime telemetry on subscriptions.
7. Overview and usage of RQt — the Qt-based introspection framework.
8. Composition — running multiple nodes in one process.
9. Cross-compilation — building for non-host architectures.
10. ROS 2 Security — SROS2 / DDS-Security.
11. Tf2 — coordinate transforms (covered in `06_tf2.md`, skipped here).

### About the ROS_DOMAIN_ID
**Source**: https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Domain-ID.html

`ROS_DOMAIN_ID` is the DDS mechanism that creates logically isolated networks
on top of shared physical infrastructure. Two ROS 2 nodes on the same domain
ID discover and communicate freely; nodes on different domains cannot see
each other at all (no discovery, no traffic). The default is `0`.

**Range**: integers `0` to `232` are valid in principle, but practical limits
are tighter because each DDS participant maps the domain ID onto two pairs of
UDP ports (multicast + unicast), and the ports must not collide with the OS's
ephemeral port range:

- Linux ephemeral range is `32768–60999` → safe domain IDs are `0–101` and
  `215–232`.
- macOS / Windows ephemeral range is `49152–65535` → safe domain IDs are
  `0–166`.

**UDP port mapping** (the formula RTI documents): each domain ID `D` reserves
two multicast ports and a pair of unicast ports per process on the host. For
domain `1`, multicast ports are `7650` and `7651`; the first process on the
host gets unicast `7660`/`7661`, the second gets `7662`/`7663`, and so on.
Lots of processes on one host can therefore exhaust the participant slots
quickly.

**Setting it**:

```bash
export ROS_DOMAIN_ID=42      # all ROS 2 processes in this shell now use 42
```

**Discovery range** (Jazzy, replacing the older `ROS_LOCALHOST_ONLY` knob,
which is deprecated):

`ROS_AUTOMATIC_DISCOVERY_RANGE` controls *where* discovery traffic is sent
on top of the domain ID:

- `SUBNET` — discover on the local subnet (default behaviour for most setups).
- `LOCALHOST` — discover only over loopback; equivalent to the old
  `ROS_LOCALHOST_ONLY=1`.
- `OFF` — disable automatic discovery entirely (use static peers).
- `SYSTEM_DEFAULT` — defer to the underlying RMW implementation's default.

Use `LOCALHOST` for fully self-contained dev machines and `SUBNET` for normal
multi-machine setups. Combine with `ROS_STATIC_PEERS` when you need to reach
hosts beyond the subnet.

### About Different Middleware Vendors
**Source**: https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Different-Middleware-Vendors.html

ROS 2 abstracts the middleware behind the `rmw` interface so the underlying
transport can be swapped without changing application code. DDS is an industry
standard with several conforming implementations, each with different
licensing, footprint, and platform support; ROS 2 also supports a non-DDS
backend (Zenoh).

**Implementations** (Jazzy):

| Vendor                | RMW package           | License        | Status in Jazzy                              |
|-----------------------|-----------------------|----------------|----------------------------------------------|
| eProsima Fast DDS     | `rmw_fastrtps_cpp`    | Apache 2.0     | **Default**, bundled with binary install     |
| Eclipse Cyclone DDS   | `rmw_cyclonedds_cpp`  | EPL v2.0       | Tier-1, available via `apt`                  |
| RTI Connext DDS       | `rmw_connextdds`      | Commercial     | Tier-1, separate install                     |
| GurumNetworks GurumDDS| `rmw_gurumdds_cpp`    | Commercial     | Community-supported, separate install        |
| Eclipse Zenoh         | `rmw_zenoh_cpp`       | EPL/Apache     | Available, non-DDS, increasingly recommended |

**Switching at runtime** — set `RMW_IMPLEMENTATION` before launching nodes:

```bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ros2 run demo_nodes_cpp talker
```

If `RMW_IMPLEMENTATION` is unset and Fast DDS is installed, Fast DDS is used.
Otherwise the alphabetically first installed RMW is selected.

**Tradeoffs**:
- Fast DDS — default, broad platform coverage, decent performance.
- Cyclone DDS — small, fast, good multicast story; popular in autoware/Nav2.
- Connext — commercial-grade tooling, certifiable variants for safety; not
  free for production use.
- Zenoh — wide-area / lossy-network friendly, optional non-DDS pub/sub.

**Interoperability caveat**: every node in a system must use the same ROS
distribution **and** the same RMW. Cross-vendor wire-format compatibility is
not guaranteed and there are known gaps (e.g. `WString` between Fast DDS and
Connext on macOS).

### About Logging and Logger Configuration
**Source**: https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Logging.html

ROS 2 logging is a layered stack: `rcutils` formats and dispatches; the
`rcl_logging_spdlog` backend writes to disk; `rcl` routes; and `rclcpp` /
`rclpy` expose the user-facing API. Every log call fans out to up to three
sinks — console, on-disk file, and the `/rosout` topic — each independently
controllable per node.

**Severity hierarchy** (ascending):

```
DEBUG < INFO < WARN < ERROR < FATAL
```

A logger only emits messages at or above its configured threshold.

**Per-logger levels**: logger names are dotted hierarchies. A child like
`my_node.transport` inherits its parent `my_node`'s level unless it has its
own explicit setting. Set levels via:

```bash
ros2 run my_pkg my_node --ros-args \
  --log-level WARN \
  --log-level my_node:=DEBUG \
  --log-level my_node.transport:=INFO
```

**Disable specific sinks** (per-node CLI):

```bash
--disable-stdout-logs       # no console output
--disable-rosout-logs       # don't publish to /rosout
--disable-external-lib-logs # silence transitively-included libs
```

**Log file location**: files go under `$ROS_LOG_DIR`. If unset, it defaults
to `$ROS_HOME/log`, where `$ROS_HOME` defaults to `~/.ros`. Net result:
`~/.ros/log/<launch-or-pid-tag>/` for most setups.

**Output formatting and behaviour env vars**:

| Env var                          | Effect                                                 |
|----------------------------------|--------------------------------------------------------|
| `RCUTILS_LOGGING_USE_STDOUT`     | `1` = stdout, `0` (default) = stderr                   |
| `RCUTILS_LOGGING_BUFFERED_STREAM`| `0` = unbuffered, `1` = line-buffered                  |
| `RCUTILS_COLORIZED_OUTPUT`       | `1` / `0` to force ANSI colors on or off               |
| `RCUTILS_CONSOLE_OUTPUT_FORMAT`  | Custom message template (see tokens below)             |

Format tokens available in `RCUTILS_CONSOLE_OUTPUT_FORMAT` include
`{severity}`, `{name}`, `{message}`, `{time}`, `{time_as_nanoseconds}`,
`{file_name}`, `{function_name}`, `{line_number}`. Default is roughly:

```
[{severity}] [{time}] [{name}]: {message}
```

Example for debugging timing:

```bash
export RCUTILS_CONSOLE_OUTPUT_FORMAT="[{severity}] {time_as_nanoseconds} {name}@{file_name}:{line_number}: {message}"
export RCUTILS_LOGGING_BUFFERED_STREAM=0   # see logs immediately
```

### About Quality of Service Settings
**Source**: https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Quality-of-Service-Settings.html

QoS profiles let publishers and subscribers (and service clients/servers)
negotiate delivery semantics. A connection is established only if every
policy is *compatible* between the two endpoints; one mismatch silently
prevents messages from flowing.

**Policy axes**:

| Policy                       | Values                                              | Meaning                                              |
|------------------------------|-----------------------------------------------------|------------------------------------------------------|
| `history`                    | `KEEP_LAST`, `KEEP_ALL`                             | What to retain in the queue                          |
| `depth`                      | unsigned int                                        | Queue size when `history = KEEP_LAST`                |
| `reliability`                | `BEST_EFFORT`, `RELIABLE`                           | UDP-like vs. ack/retransmit                          |
| `durability`                 | `VOLATILE`, `TRANSIENT_LOCAL`                       | Whether late joiners get past samples                |
| `deadline`                   | `Duration`                                          | Max expected period between messages                 |
| `lifespan`                   | `Duration`                                          | Max age of a message before it expires               |
| `liveliness`                 | `AUTOMATIC`, `MANUAL_BY_TOPIC`                      | Who asserts that the publisher is alive              |
| `liveliness_lease_duration`  | `Duration`                                          | Window after which a silent publisher is "dead"      |

**Predefined profiles** (in `rclcpp::QoS` / `rclpy.qos`):

| Profile             | Reliability   | Durability         | History       | Depth | Use case                                           |
|---------------------|---------------|--------------------|---------------|-------|----------------------------------------------------|
| `default`           | RELIABLE      | VOLATILE           | KEEP_LAST     | 10    | General-purpose, ROS 1-like behaviour              |
| `sensor_data`       | BEST_EFFORT   | VOLATILE           | KEEP_LAST     | 5     | High-rate sensors where freshness > completeness   |
| `services`          | RELIABLE      | VOLATILE           | KEEP_LAST     | 10    | Service request/response                           |
| `parameters`        | RELIABLE      | VOLATILE           | KEEP_LAST     | 1000  | Parameter set/get                                  |
| `parameter_events`  | RELIABLE      | VOLATILE           | KEEP_LAST     | 1000  | Broadcast of parameter changes                     |
| `system_default`    | RMW default   | RMW default        | RMW default   | RMW   | Defer everything to the underlying middleware      |

**Reliability compatibility** (checkmark = messages flow):

| Publisher    | Subscriber    | Compatible |
|--------------|---------------|------------|
| BEST_EFFORT  | BEST_EFFORT   | yes        |
| BEST_EFFORT  | RELIABLE      | **no**     |
| RELIABLE     | BEST_EFFORT   | yes        |
| RELIABLE     | RELIABLE      | yes        |

**Durability compatibility**:

| Publisher        | Subscriber       | Compatible | Behaviour for late joiners              |
|------------------|------------------|------------|-----------------------------------------|
| VOLATILE         | VOLATILE         | yes        | Only new messages                       |
| VOLATILE         | TRANSIENT_LOCAL  | **no**     | Fails the durability check              |
| TRANSIENT_LOCAL  | VOLATILE         | yes        | Only new messages                       |
| TRANSIENT_LOCAL  | TRANSIENT_LOCAL  | yes        | Late joiners receive the cached samples |

The asymmetric rules are: a subscriber can ask for *less* than the publisher
offers, but never *more*. The same logic applies on `deadline`, `lifespan`,
and `liveliness_lease_duration` (subscribers tolerate publishers that promise
tighter guarantees).

### About Executors
**Source**: https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Executors.html

An *executor* is what actually drives a node — it pulls work (subscription
callbacks, timers, service handlers, action callbacks) out of the middleware
and dispatches it to OS threads. ROS 2 ships three concrete executors and a
callback-group abstraction to control parallelism.

**Executor types**:

- `SingleThreadedExecutor` — one OS thread services every callback in
  round-robin order. Simplest, predictable, default in `rclcpp::spin(node)`.
- `MultiThreadedExecutor` — pool of threads (configurable size) drains the
  ready queue in parallel; actual concurrency is gated by callback groups.
- `StaticSingleThreadedExecutor` — same threading model as
  `SingleThreadedExecutor` but scans the node's entities (subs/timers/etc.)
  *once* at setup, so per-spin overhead is much lower. Suitable when
  callbacks are not added/removed at runtime.

**Spin methods** (on any executor):

- `spin()` — block forever, processing callbacks until shutdown.
- `spin_some()` — process all currently-ready callbacks once and return
  (good for integrating with another event loop).
- `spin_until_future_complete(future)` — spin until the supplied future
  resolves or a timeout elapses; the canonical way to wait on a service
  call response without a full event loop.
- `spin_once()` — process at most one callback, then return.

**Basic usage** (C++):

```cpp
rclcpp::executors::SingleThreadedExecutor executor;
executor.add_node(node);
executor.spin();
```

**Callback groups** decide which callbacks may run concurrently:

- `MutuallyExclusive` (default) — at most one callback in the group runs at
  a time. Use for handlers that share unguarded state.
- `Reentrant` — callbacks may run in parallel. Use for stateless or
  internally-synchronized handlers, and when you need a service callback to
  invoke another service on the same node without deadlock.

```cpp
auto cb_group = node->create_callback_group(
    rclcpp::CallbackGroupType::Reentrant);

rclcpp::SubscriptionOptions opts;
opts.callback_group = cb_group;
auto sub = node->create_subscription<MsgT>(
    "topic", rclcpp::QoS(10), &handler, opts);
```

Different groups always run in parallel under `MultiThreadedExecutor`.
A common pattern for drone/perception nodes: heavy image callback in a
`Reentrant` group, and a `MutuallyExclusive` group for state-mutating
service handlers.

### About Topic Statistics
**Source**: https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Topic-Statistics.html

Topic statistics is an opt-in subscription feature that reports two
runtime metrics about incoming messages. It is **disabled by default** and
is currently rclcpp-only.

**What gets measured** (per subscription, in milliseconds):

1. `received_message_period` — wall-clock interval between consecutive
   messages.
2. `received_message_age` — `now - msg.header.stamp` at the moment of
   reception (requires the message to have a `std_msgs/Header`).

For each metric the system keeps a rolling window and reports
**average, max, min, standard deviation, and sample count** as a
`statistics_msgs/msg/MetricsMessage`.

**Publication**: stats are published to `/statistics` (configurable) once per
collection window (default 1 second). The window length doubles as the
publishing period.

**Edge cases**:
- A message without a `Header` produces NaN for `message_age` rather than
  being dropped — by design, "absence of signal" is itself a signal.
- The very first sample in a new window can't yield a `period` value (no
  prior arrival to subtract from).

**How to enable** (rclcpp):

```cpp
rclcpp::SubscriptionOptions opts;
opts.topic_stats_options.state =
    rclcpp::TopicStatisticsState::Enable;
opts.topic_stats_options.publish_topic = "/my_node/sub_stats";
opts.topic_stats_options.publish_period = std::chrono::seconds(1);

auto sub = node->create_subscription<sensor_msgs::msg::Image>(
    "/camera/image_raw", rclcpp::SensorDataQoS(), cb, opts);
```

Useful for quantifying camera/IMU jitter on a drone without a custom
profiler.

### About RQt
**Source**: https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-RQt.html

RQt is the Qt-based introspection framework. It hosts each tool as a
*plugin* that can be docked into a single window or run standalone. Two
metapackages provide the surface area:

- `rqt` — the framework itself (plugin loading, perspectives, dock layout).
- `rqt_common_plugins` — bundle of the everyday debugging plugins.

Discover installed plugins with `ros2 pkg list | grep ^rqt_`. Common ones
shipped in the common-plugins bundle:

| Plugin                | Purpose                                                          |
|-----------------------|------------------------------------------------------------------|
| `rqt_graph`           | Node/topic graph visualization (replaces `rosgraph`).            |
| `rqt_console`         | Live filterable view of `/rosout` log messages.                  |
| `rqt_plot`            | XY/time plot of numeric topic fields.                            |
| `rqt_reconfigure`     | GUI client for `rcl_interfaces` parameters.                      |
| `rqt_topic`           | Inspect topic metadata, frequency, sample data.                  |
| `rqt_service_caller`  | Form-based service request invocation.                           |
| `rqt_image_view`      | Stream camera/`sensor_msgs/Image` topics with throttling.        |
| `rqt_bag`             | Visual `ros2 bag` browser, scrub/playback control.               |
| `rqt_tf_tree`         | Render the live TF tree as a graphviz diagram.                   |
| `rqt_publisher`       | Publish hand-crafted messages from a form.                       |
| `rqt_action`          | Inspect / call action servers.                                   |
| `rqt_msg`, `rqt_srv`  | Browse installed message and service definitions.                |
| `rqt_shell`           | A simple shell embedded in the dock.                             |

Launch the all-in-one window with `rqt`, or open a single plugin via
`ros2 run rqt_<name> rqt_<name>` (e.g. `ros2 run rqt_graph rqt_graph`).
"Perspectives" save a particular dock layout for re-use.

### About Composition
**Source**: https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Composition.html

Composition unifies the old ROS 1 split between "nodes" (separate
processes) and "nodelets" (shared-process, zero-copy). In ROS 2 every node
*is* a component class; you decide *at deployment time* whether to give it
its own process or co-locate it with others.

**Trade-off**:
- Separate processes — better fault isolation, simpler debugging, easier to
  apply OS-level sandboxing.
- Shared process — lower overhead, enables true zero-copy intra-process
  pub/sub for big payloads (point clouds, images).

**Manual composition patterns** (four forms, escalating in dynamism):

1. **Compile-time composition** — build a single executable that
   `#include`s and instantiates the components directly; their identities
   are baked in at compile time.
2. **Link-time composition** — components live in shared libraries linked
   into a custom executable at link time.
3. **Run-time composition** — start a generic *container* process and load
   shared-library components into it via the `load_node` service or the
   `ros2 component` CLI.
4. **`dlopen`-time composition** — a custom executable iterates over
   shared-library paths at startup and `dlopen`s each one to instantiate
   the contained components, without involving the container's load
   service.

**Component registration** — components are shared libraries with no
`main()`; they expose a `rclcpp::Node` subclass and are registered in CMake:

```cmake
# Single component + a thin standalone executable for it
rclcpp_components_register_node(
    my_lib
    PLUGIN "my_pkg::TalkerComponent"
    EXECUTABLE talker_node)

# Pure component (load-only)
rclcpp_components_register_nodes(my_lib "my_pkg::ListenerComponent")
```

The runtime entry point is the macro `RCLCPP_COMPONENTS_REGISTER_NODE(cls)`
in the component's `.cpp`:

```cpp
#include "rclcpp_components/register_node_macro.hpp"
RCLCPP_COMPONENTS_REGISTER_NODE(my_pkg::TalkerComponent)
```

**Container nodes** (generic processes that host loaded components):

- `component_container` — single-threaded executor.
- `component_container_mt` — multi-threaded executor.
- `component_container_isolated` — one executor per loaded component.

**CLI**:

```bash
ros2 run rclcpp_components component_container_mt &
ros2 component load /ComponentManager my_pkg my_pkg::TalkerComponent
ros2 component list
ros2 component unload /ComponentManager 1
ros2 component types        # list installed component classes
```

In launch files, `ComposableNodeContainer` + `ComposableNode` declarations
do the same wiring without manual CLI calls.

### About Cross-Compilation
**Source**: https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Cross-Compilation.html

Cross-compilation builds artefacts for a target architecture different from
the host (e.g. amd64 dev box → aarch64 drone companion computer). The
documentation frames the problem rather than prescribing one tool, and
flags three sources of complexity:

1. Code that is conditionally compiled per architecture must be cleanly
   isolated.
2. Every dependency in the stack must already be cross-compiled (or
   available as a pre-built target binary) before the dependent package
   builds.
3. The build tools themselves must understand cross-compilation (handle
   sysroots, toolchain files, target triples).

**Key concepts**:

- **Target triple** — `<arch>-<vendor>-<os>-<abi>`, e.g.
  `aarch64-linux-gnu`, used to select the cross toolchain.
- **Sysroot** — a directory tree mirroring the target's `/usr`, `/lib`,
  etc., so headers and shared objects resolve against the target rather
  than the host.
- **Toolchain file** — CMake (`CMAKE_TOOLCHAIN_FILE`) and colcon
  (`--cmake-args`) entry point that points at the cross compiler and
  sysroot.

**Workflow** — the historical ROS 2 path is the
[`ros-cross-compile`](https://github.com/ros-tooling/cross_compile) tool,
which wraps `colcon` inside a QEMU-emulated Docker container of the target
distro. Typical invocation:

```bash
pip install ros-cross-compile
ros-cross-compile ./ws \
    --arch aarch64 \
    --os ubuntu \
    --rosdistro jazzy
```

Targets commonly built this way: `aarch64` (RPi 4/5, Jetson, most ARM
SBCs) and `armhf` (32-bit ARM, older boards).

**Alternative**: build multi-arch images with `docker buildx` and let QEMU
emulate the target during a normal `colcon build` inside the container —
slower per-package, but avoids maintaining a separate cross toolchain.

### About ROS 2 Security
**Source**: https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Security.html

ROS 2 secures node-to-node communication by leveraging the **DDS-Security**
specification through `sros2` (the SROS2 tool suite). Three orthogonal
plugins cover the security domains:

- **Authentication** — verify that each participant is who it claims to be
  (via X.509 certificates).
- **Access control** — enforce per-topic / per-service permissions via
  signed XML policies.
- **Cryptography** — encrypt and sign on the wire.

**Security enclaves** are the unit of policy. An enclave is a directory
containing six files that together identify a process and authorize what
it may publish, subscribe, call, etc.:

| File                         | Role                                                         |
|------------------------------|--------------------------------------------------------------|
| `identity_ca.cert.pem`       | Trust anchor for participant identity (CA certificate)       |
| `cert.pem`                   | This enclave's identity certificate                          |
| `key.pem`                    | This enclave's private key                                   |
| `permissions_ca.cert.pem`    | Trust anchor for permission grants                           |
| `governance.p7s`             | Domain-wide policy (signed XML) — encryption, discovery, etc.|
| `permissions.p7s`            | Per-enclave allow/deny list (signed XML)                     |

Enclaves are bound to processes (and therefore nodes) at runtime; one
enclave may cover several nodes that share a security posture.

**Enabling SROS2** — two environment variables drive the runtime:

| Env var                     | Purpose                                                  |
|-----------------------------|----------------------------------------------------------|
| `ROS_SECURITY_ENABLE`       | `true` to turn on the security plugins                   |
| `ROS_SECURITY_STRATEGY`     | `Enforce` (require valid enclave) or `Permissive`        |
| `ROS_SECURITY_KEYSTORE`     | Path to the keystore root containing all enclaves        |

A keystore is created and populated with `ros2 security` subcommands
(`create_keystore`, `create_enclave`, `generate_artifacts`), then nodes
launched with `--enclave /path/within/keystore` pick up the right files.
For drone deployments where the airframe and the GCS run on different
hosts, secure-by-default with `Enforce` is the right posture; use
`Permissive` only during migration.

## Advanced

### Advanced Concepts (index)
**Source**: https://docs.ros.org/en/jazzy/Concepts/Advanced.html

These pages target developers who plan to **modify or contribute to ROS 2
core**, not application authors. Three sub-topics:

1. The Build System — how `ament_*`, `colcon`, and `package.xml` fit together.
2. Internal ROS 2 Interfaces — the `rcl`, `rmw`, `rosidl`, `rcutils`,
   `rcpputils` layer cake.
3. ROS 2 Middleware Implementations — what an RMW package actually contains
   and how vendor support is structured.

### About the Build System
**Source**: https://docs.ros.org/en/jazzy/Concepts/Advanced/About-Build-System.html

The ROS 2 build system has three layers:

1. **Build tool** — handles a *single* package: typically CMake (for C++)
   or setuptools (for Python).
2. **Build helpers** — the `ament_*` packages that add ROS-aware
   conventions on top of the build tool.
3. **Meta-build tool** — `colcon`, which topologically orders packages by
   their declared dependencies and invokes the build tool on each.

**Build helpers (`ament_*`)**:

- `ament_package` — common utilities (env hooks, `package.xml` parsing via
  `catkin_pkg`).
- `ament_cmake` — umbrella for CMake-side ament infrastructure:
  - `ament_cmake_core` — environment hooks, resource indexing.
  - `ament_cmake_auto` — convenience macros that derive `target_*` calls
    from `package.xml` deps.
  - `ament_cmake_python` — install Python modules from a CMake package.
  - `ament_cmake_test` — gtest/gmock/nosetests integration.
- `ament_lint` — uncrustify (C++), pep8 (Python), copyright checker, etc.
- `ament_python` — pure-Python package support (uses setuptools).

**Build types** — declared in `package.xml`:

```xml
<export>
  <build_type>ament_cmake</build_type>   <!-- C++/CMake package -->
  <!-- or -->
  <build_type>ament_python</build_type>  <!-- Python-only package -->
</export>
```

**`package.xml` formats**: ROS 2 supports formats **2** and **3**
(REPs 140 and 149). Format 3 adds the *condition* attribute and
*member_of_group* / *group_depend* tags.

**Dependency tags**:

| Tag             | When the dep is required                                     |
|-----------------|--------------------------------------------------------------|
| `<build_depend>`| At compile/generate time only                                |
| `<exec_depend>` | At runtime only                                              |
| `<depend>`      | Shorthand for `build_depend` + `exec_depend` + `build_export_depend` |
| `<test_depend>` | Only when running tests                                      |
| `<doc_depend>`  | Only when building docs                                      |
| `<buildtool_depend>` | Tools needed to *run* the build (e.g. `ament_cmake`)    |
| `<build_export_depend>` | Headers exposed to downstream packages                |

**`condition` attribute** (format 3) — gates a dep on env-var values:

```xml
<depend condition="$ROS_DISTRO == jazzy">rclcpp</depend>
```

**Groups** — `group_depend` declares a *named* dependency group, and any
package can advertise itself as a member with `member_of_group`. Used for
plugin / pluginlib-style discovery (e.g. all controllers are members of
`controller_interface`).

**Other**: the ament *resource index* (under each install prefix) is how
`ament_index_cpp` / `ament_index_python` find packages, plugins, and
launch files at runtime — the modern replacement for ROS 1's `rospack`
crawl. `colcon build` produces `install/` (no separate "devel" space);
sourcing `install/setup.bash` exports the env hooks defined by every
package.

### About Internal Interfaces
**Source**: https://docs.ros.org/en/jazzy/Concepts/Advanced/About-Internal-Interfaces.html

ROS 2 is structured as a deliberately layered stack so that user code is
insulated from the underlying middleware. From bottom to top:

```
+---------------------------+
|   rclcpp     |   rclpy    |  <- user-facing client libs (C++, Python)
+---------------------------+
|            rcl            |  <- ROS Client Library (C, middleware-agnostic)
+---------------------------+
|            rmw            |  <- ROS Middleware abstraction (C)
+---------------------------+
|   Fast DDS / Cyclone /    |  <- vendor implementation (DDS, Zenoh, ...)
|   Connext / Zenoh / ...   |
+---------------------------+
```

**Layer responsibilities**:

- **`rcutils`** — base C utilities: error reporting, logging primitives,
  command-line parsing, allocator wrappers, string ops. Used by every
  layer above.
- **`rcpputils`** — C++ counterpart: thread-safe helpers, file-system
  helpers, scope guards, semantic version utilities.
- **`rosidl`** — interface definition language. Parses `.msg`, `.srv`,
  `.action` files and runs language-specific generators
  (`rosidl_generator_c`, `rosidl_generator_cpp`, `rosidl_generator_py`)
  plus type-support generators per RMW.
- **`rmw`** — the *minimal* C API every middleware vendor must implement:
  participants, publishers, subscriptions, clients, services, waitsets,
  graph events. Vendor packages live in separate repos
  (`rmw_fastrtps_cpp`, `rmw_cyclonedds_cpp`, `rmw_connextdds`,
  `rmw_zenoh_cpp`).
- **`rcl`** — slightly higher-level C API on top of `rmw`. Implements
  ROS-flavoured concepts like nodes, parameters, time sources, logging
  routing, lifecycle, and graph queries. Client libraries call into `rcl`
  rather than `rmw` directly.
- **`rclcpp` / `rclpy`** — idiomatic per-language wrappers: executors,
  callback groups, lifecycle nodes, action servers/clients, smart-pointer
  lifetimes, pythonic `Node` subclassing.

This separation is what makes `RMW_IMPLEMENTATION` swapping work without
recompiling user code.

### About Middleware Implementations
**Source**: https://docs.ros.org/en/jazzy/Concepts/Advanced/About-Middleware-Implementations.html

A "middleware implementation" in ROS 2 is the concrete plug-in that fills
in the `rmw` and `rosidl` typesupport hooks for a particular wire
protocol. All officially-supported implementations except Zenoh are based
on DDS.

**Supported vendors / repos** (Jazzy):

- eProsima **Fast DDS** — `ros2/rmw_fastrtps_cpp` (default).
- Eclipse **Cyclone DDS** — `ros2/rmw_cyclonedds`.
- RTI **Connext DDS** — `ros2/rmw_connextdds` (commercial; certifiable
  variants like Connext Cert exist for safety-critical use).
- GurumNetworks **GurumDDS** — `ros2/rmw_gurumdds` (community-supported).
- Eclipse **Zenoh** — `ros2/rmw_zenoh` (non-DDS, increasingly featured).

**Standard package structure** — each implementation typically ships
three packages:

1. `<impl>_cmake_module` — CMake helpers that locate the vendor's
   libraries on disk.
2. `rmw_<impl>_<lang>` — the actual `rmw` API implementation.
3. `rosidl_typesupport_<impl>_<lang>` — generates vendor-specific type
   support code so messages defined in `.msg` files can be serialized over
   that vendor's transport.

`rosidl_generator_dds_idl` is shared infrastructure that converts ROS
`.msg` files into DDS-flavoured `.idl` files, which the per-vendor
typesupport packages then consume. Implementations may either generate
static type-support code at build time, or consume the IDL at runtime via
DDS X-Types Dynamic Data.

**Selection at runtime**: `RMW_IMPLEMENTATION=rmw_xxx_cpp` chooses the
implementation when each ROS process starts. If unset, Fast DDS is used
when present; otherwise the alphabetically-first installed RMW is
selected. Every node in a single ROS graph **must** use the same RMW —
cross-vendor wire compatibility is best-effort and not guaranteed.

**Certification status**: most vendors offer the open-source/community
build for general use, with certifiable safety-critical variants
available commercially (notably RTI Connext Cert and Apex.AI's Cyclone
DDS derivative for ISO 26262 / DO-178C contexts). The standard ROS 2
binary packages are *not* themselves certified.
