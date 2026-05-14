# How-To Guides — Runtime, Debug & Integration (ROS 2 Jazzy)

This reference compiles the runtime, debugging, and integration How-To Guides
for ROS 2 Jazzy. It covers DDS / RMW tuning, QoS overrides for rosbag, callback
groups and async patterns, zero-copy loaned messages, parameter and node
argument plumbing, debugging with gdb, IDE / Docker / Foxglove setup, and the
ros1_bridge for legacy interop.

---

## DDS Tuning

**Source**: https://docs.ros.org/en/jazzy/How-To-Guides/DDS-tuning.html

### Problem this guide solves
DDS-based middlewares (Cyclone DDS, Fast DDS, RTI Connext) frequently exhibit
two symptoms on a stock Linux install:

1. **Lossy networks (WiFi, congested switches)** drop UDP fragments. The kernel
   reassembly buffer fills and stalls for ~30 seconds while it waits for the
   missing pieces, after which the partial datagram is discarded. Reliable QoS
   then retransmits, but the publisher has already been blocked.
2. **Large messages on reliable QoS** (typical for high-resolution images,
   point clouds, or multi-MB serialized blobs) overrun the per-socket receive
   buffer. The receiver's kernel drops them before the DDS reader sees them,
   even on wired Gigabit links.

### Cross-vendor mitigations

**Switch to best-effort QoS** when the application can tolerate occasional
loss. This eliminates ACK traffic and the publisher-side retransmit pressure.

**Reduce IP fragment reassembly timeout** (kernel default 30 s, drop to 3 s):
```bash
sudo sysctl net.ipv4.ipfrag_time=3
```

**Increase the IP fragment reassembly threshold** (default 256 KB, raise to
128 MB):
```bash
sudo sysctl net.ipv4.ipfrag_high_thresh=134217728
```

**Avoid large heterogeneous arrays** in custom messages. `sensor_msgs/PointCloud2`
is the canonical pattern: instead of one array of structs, define multiple
parallel arrays of primitives. Serialization cost on big nested arrays is
disproportionate.

### Cyclone DDS — large reliable messages

Bump the kernel max receive buffer to 2 GiB (one-shot):
```bash
sudo sysctl -w net.core.rmem_max=2147483647
```

Persist across reboots in `/etc/sysctl.d/10-cyclone-max.conf`:
```
net.core.rmem_max=2147483647
```

Tell Cyclone to actually use a large socket via XML profile (e.g.
`cyclone-config.xml`):
```xml
<?xml version="1.0" encoding="UTF-8" ?>
<CycloneDDS xmlns="https://cdds.io/config"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="https://cdds.io/config
  https://raw.githubusercontent.com/eclipse-cyclonedds/cyclonedds/master/etc/cyclonedds.xsd">
    <Domain id="any">
        <Internal>
            <SocketReceiveBufferSize min="10MB"/>
        </Internal>
    </Domain>
</CycloneDDS>
```

Activate with an absolute file URI (relative paths and shell-relative
`~` will not work):
```bash
export CYCLONEDDS_URI=file:///absolute/path/to/cyclone-config.xml
```

### RTI Connext — large reliable messages

Smaller kernel buffer is sufficient:
```bash
sudo sysctl -w net.core.rmem_max=4194304
```

Apply a flow-controlled QoS profile (the upstream example
`ROS2TEST_QOS_PROFILES.xml` ships three flow controllers — slow, medium, fast;
the medium controller is the usual sweet spot). Connext consumes XML profiles
via `NDDS_QOS_PROFILES`; for ROS 2 the equivalent env var is
`RMW_CONNEXT_INITIAL_PEERS` and the `<participant_qos>` profile loaded from
disk.

### Fast DDS profile loading

Fast DDS uses `FASTRTPS_DEFAULT_PROFILES_FILE` (note: legacy name retained
even after the rename to Fast DDS):
```bash
export FASTRTPS_DEFAULT_PROFILES_FILE=/absolute/path/to/fastdds_profile.xml
```

The XML uses `<profiles>...<participant>...<rtps>...<sendSocketBufferSize>` and
`<listenSocketBufferSize>` to mirror the Cyclone settings.

### Success criteria

A correctly tuned multi-machine setup over 1 GbE should deliver large messages
with ~371-700 ms latency and zero drops at sustained reliable rates. If you
still see 30 s stalls after applying the above, the cause is almost always
that the env var path is wrong (silent failure — no warning is logged) or that
`net.core.rmem_max` was set but the DDS profile did not request the larger
socket.

### Edge cases / platform notes
- Kernel sysctls are global. They affect every process on the box, not just
  ROS, so set them on dev / robot machines, not on shared servers.
- `CYCLONEDDS_URI` and `FASTRTPS_DEFAULT_PROFILES_FILE` are only read at
  process start. You must restart any node (and `ros2 daemon stop`) after
  changing them.
- The recommended values are starting points. Iterate based on message size
  and topology.

---

## Overriding QoS Policies for Recording and Playback

**Source**: https://docs.ros.org/en/jazzy/How-To-Guides/Overriding-QoS-Policies-For-Recording-And-Playback.html

### Problem this guide solves
`ros2 bag record` and `ros2 bag play` create their own subscribers / publishers
with default QoS. If the original publisher used `transient_local` durability
or `keep_all` history, the bag's default `volatile` / `keep_last` subscriber
will silently miss latched messages, or the bag's playback publisher will fail
to satisfy a downstream `transient_local` subscriber. Only the
**reliability** and **durability** policies actually decide compatibility, but
the others matter for buffer behavior.

### YAML schema for `--qos-profile-overrides-path`

The file is a flat map keyed by topic name. Each topic gets a subset of the
QoS fields:
```yaml
/topic_name:
  history: keep_all          # keep_all | keep_last
  depth: 10                  # int, only meaningful for keep_last
  reliability: reliable      # system_default | reliable | best_effort | unknown
  durability: transient_local # system_default | transient_local | volatile | unknown
  deadline:
    sec: 0
    nsec: 0
  lifespan:
    sec: 0
    nsec: 0
  liveliness: automatic      # system_default | automatic | manual_by_topic | unknown
  liveliness_lease_duration:
    sec: 0
    nsec: 0
  avoid_ros_namespace_conventions: false
```

Any field omitted falls back to the rosbag2 default for that topic.

### CLI usage

Record with overrides:
```bash
ros2 bag record -a -o my_bag --qos-profile-overrides-path overrides.yaml
```

Play back with overrides:
```bash
ros2 bag play --qos-profile-overrides-path overrides.yaml my_bag
```

### Worked example — capture a latched topic

The `/talker` topic publishes once with `transient_local`. Default rosbag
record would arrive after the publish and miss it. Use:

`durability_override.yaml`:
```yaml
/talker:
  durability: transient_local
  history: keep_all
```

```bash
ros2 bag record -a -o my_bag --qos-profile-overrides-path durability_override.yaml
```

### Edge cases
- Duration policies (`deadline`, `lifespan`, `liveliness_lease_duration`)
  always need both `sec` and `nsec`; missing one parses as zero and may
  unintentionally enable a deadline.
- Override files are per-topic, not per-namespace. Wildcards are not supported
  in this YAML — list each topic explicitly.
- Distinct override files for record vs. playback are normal. Record
  typically widens history/durability; playback typically matches downstream
  expectations.

---

## Working with Multiple RMW Implementations

**Source**: https://docs.ros.org/en/jazzy/How-To-Guides/Working-with-multiple-RMW-implementations.html

### Problem this guide solves
ROS 2 abstracts the middleware behind RMW. Different DDS vendors (and Zenoh)
have different performance and discovery characteristics, and the same
process must pick exactly one. This guide explains how to install several
side-by-side and select per-invocation.

### Selecting an RMW

Set `RMW_IMPLEMENTATION` before launching:
```bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ros2 run demo_nodes_cpp talker
```

Or per-command:
```bash
RMW_IMPLEMENTATION=rmw_connextdds ros2 run demo_nodes_cpp talker
```

On Windows:
```cmd
set RMW_IMPLEMENTATION=rmw_connextdds
ros2 run demo_nodes_cpp talker
```

### Available implementations on Jazzy

| Identifier             | Vendor / project                |
| ---------------------- | ------------------------------- |
| `rmw_fastrtps_cpp`     | eProsima Fast DDS (Jazzy default) |
| `rmw_cyclonedds_cpp`   | Eclipse Cyclone DDS             |
| `rmw_connextdds`       | RTI Connext DDS                 |
| `rmw_gurumdds_cpp`     | GurumNetworks GurumDDS          |
| `rmw_zenoh_cpp`        | Zenoh (Eclipse)                 |

Install side-by-side via apt:
```bash
sudo apt install ros-jazzy-rmw-cyclonedds-cpp \
                 ros-jazzy-rmw-fastrtps-cpp \
                 ros-jazzy-rmw-zenoh-cpp
```

### Inspecting the active RMW
```bash
printenv RMW_IMPLEMENTATION
```
If empty, the distro default (`rmw_fastrtps_cpp` for Jazzy per REP-2000) is
used.

### Switching cleanly

The `ros2 daemon` process caches the RMW it was started with. Always restart
it when changing RMW:
```bash
ros2 daemon stop
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ros2 daemon start  # optional; auto-starts on next ros2 cli command
```

### Rebuilding to pick up a new RMW

If you installed a new RMW after building your workspace, force CMake to
re-detect it:
```bash
colcon build --cmake-clean-cache
```

### Troubleshooting

- **Missing implementation error**: `RMW_IMPLEMENTATION` was set to a name not
  installed. Check `apt list --installed | grep rmw`.
- **Daemon mismatch**: Symptom is `ros2 topic list` returning empty when nodes
  are clearly running. Cause is the daemon was started with a different RMW.
  Run `ros2 daemon stop` and rerun.
- **RTI Connext on macOS shared-memory errors**:
  ```bash
  sudo sysctl -w kern.sysv.shmmax=419430400
  sudo sysctl -w kern.sysv.shmmin=1
  sudo sysctl -w kern.sysv.shmmni=128
  sudo sysctl -w kern.sysv.shmseg=1024
  sudo sysctl -w kern.sysv.shmall=262144
  ```
  For persistence put these in `/etc/sysctl.conf` and reboot.
- **Cross-vendor interop**: Different RMW vendors do interoperate over RTPS
  on the wire, but only for reliability/durability combinations both vendors
  implement identically. For mixed deployments standardize on one vendor.

---

## Synchronous vs Asynchronous Service Clients

**Source**: https://docs.ros.org/en/jazzy/How-To-Guides/Sync-Vs-Async.html

### Problem this guide solves
Calling a service synchronously (`client.call()`) from inside a callback
deadlocks the executor. The deadlock is silent — no exception, no warning.

### The deadlock pattern

```python
# Inside a subscription / timer / service callback:
response = self.client.call(req)   # BLOCKS forever
```

The single-threaded executor running this callback is also the executor that
must dispatch the service response. Because the callback is blocked waiting
for the response, the executor cannot run the response handler, and the call
never completes. From the docs: *"Deadlock occurs because `rclpy.spin` will
not preempt the callback with the `send_request` call."*

### The supported workarounds

**Preferred: use `call_async()`** — returns a `Future` immediately, safe to
call from any context (callback or main thread):
```python
future = self.client.call_async(req)
future.add_done_callback(self._on_response)
```

**Spin in a separate thread**, only when you absolutely must block:
```python
from threading import Thread
spin_thread = Thread(target=rclpy.spin, args=(node,))
spin_thread.start()
response = client.call(req)        # safe: spin lives on another thread
```

**Spin until future complete** (top-level main code only, not inside a
callback):
```python
future = client.call_async(req)
rclpy.spin_until_future_complete(node, future)
response = future.result()
```

### C++ note
C++ (`rclcpp`) only exposes async (`async_send_request`). The same callback
deadlock exists if the timer and the client share a single mutually-exclusive
callback group — see the callback-groups guide for the fix.

### Edge cases
- Inside a callback, even `call_async()` + `spin_until_future_complete()` will
  deadlock unless the calling callback is in a different group than the
  client's response callback. The async future itself is safe; calling
  `spin_until_future_complete` from inside a callback is not.
- The single-thread vs multi-thread executor distinction matters: the deadlock
  also occurs on `MultiThreadedExecutor` if both timer and client share the
  same `MutuallyExclusive` group.

---

## Using Callback Groups

**Source**: https://docs.ros.org/en/jazzy/How-To-Guides/Using-callback-groups.html

### Problem this guide solves
The default executor model serializes every callback. To get parallel
execution — and to avoid the silent deadlock above — you assign callbacks to
explicit callback groups and run a `MultiThreadedExecutor`.

### The two group types

**`MutuallyExclusive`** — at most one callback from this group runs at a time.
Behaves as if it had its own `SingleThreadedExecutor`. Use for shared mutable
state (e.g. a control loop), or any non-thread-safe code.

**`Reentrant`** — any number of callbacks from this group can run in parallel,
including multiple invocations of the same callback. Use for action servers
that handle independent requests, or any I/O-bound work that scales with
concurrency.

Cross-group callbacks always run in parallel, regardless of either group's
type.

### Default behaviour
Every node has an implicit default `MutuallyExclusive` group. Anything you
create without specifying `callback_group=` lands there, so by default an
unconfigured `MultiThreadedExecutor` behaves like a single-threaded one.

### Assigning entities to a group

C++ (`rclcpp`):
```cpp
auto cb_group = create_callback_group(
    rclcpp::CallbackGroupType::MutuallyExclusive);  // or Reentrant

rclcpp::SubscriptionOptions options;
options.callback_group = cb_group;

auto sub = create_subscription<std_msgs::msg::Int32>(
    "/topic", rclcpp::SensorDataQoS(), callback, options);

// Timer:
auto timer = create_wall_timer(100ms, timer_cb, cb_group);

// Service / Client:
auto srv = create_service<MyService>("srv", srv_cb,
    rmw_qos_profile_services_default, cb_group);
auto cli = create_client<MyService>("srv",
    rmw_qos_profile_services_default, cb_group);
```

Python (`rclpy`):
```python
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup, ReentrantCallbackGroup

cb_group = MutuallyExclusiveCallbackGroup()
self.create_subscription(Int32, "/topic", self.cb,
                         qos_profile=1, callback_group=cb_group)
self.create_timer(0.1, self.tick, callback_group=cb_group)
self.create_service(MyService, "srv", self.srv_cb, callback_group=cb_group)
self.create_client(MyService, "srv", callback_group=cb_group)
```

### The deadlock fix for sync service calls

Symptom: a timer that synchronously calls a service hangs on the first call.

Fix: put the timer and the client in **different** `MutuallyExclusive` groups,
or in a `Reentrant` group:
```cpp
client_cb_group_ = create_callback_group(
    rclcpp::CallbackGroupType::MutuallyExclusive);
timer_cb_group_ = create_callback_group(
    rclcpp::CallbackGroupType::MutuallyExclusive);
```

The general rule from the docs: *"If you make a synchronous call in any type
of a callback, this callback and the client making the call need to belong to
different callback groups (of any type), or a Reentrant Callback Group."*

### TF lookups
A common pattern is to put `tf2_ros::Buffer::lookupTransform` (which can
block briefly waiting for a transform) into a separate `MutuallyExclusive`
group. This prevents a slow lookup from starving timer / subscriber callbacks
on the main group.

### Driving the executor
```python
from rclpy.executors import MultiThreadedExecutor
executor = MultiThreadedExecutor(num_threads=4)
executor.add_node(node)
executor.spin()
```
Defaults to `os.cpu_count()` threads if `num_threads` is unset. Without
distinct callback groups the extra threads stay idle.

### Big-picture reminder
Almost every ROS 2 entity (subscriptions, timers, services, action handlers,
parameter callbacks, future done callbacks) is a callback under the executor.
Group assignment matters for all of them.

---

## Configure Zero-Copy Loaned Messages

**Source**: https://docs.ros.org/en/jazzy/How-To-Guides/Configure-ZeroCopy-loaned-messages.html

### Problem this guide solves
Standard publish copies the user's message into the middleware's transport
buffer. For multi-MB messages on a fast loop this dominates CPU and latency.
Loaned messages let the publisher write directly into a buffer the middleware
already owns; if the subscriber lives in the same process / shared-memory
segment, no copy occurs.

### RMW support matrix

| RMW              | Loaned messages |
| ---------------- | --------------- |
| `rmw_fastrtps`   | Yes             |
| `rmw_cyclonedds` | No              |
| `rmw_connextdds` | No              |

For cross-process zero-copy with Fast DDS, follow the upstream
[Enable Zero Copy Data Sharing](https://github.com/ros2/rmw_fastrtps?tab=readme-ov-file#enable-zero-copy-data-sharing)
recipe (uses Fast DDS data-sharing delivery, optionally backed by Iceoryx
shared memory).

### Default behavior
Publishers loan automatically when the RMW supports it.
Subscriptions have known safety issues (the loan can outlive the
subscription's view of it), so loaned message reception is **disabled by
default**.

### Disabling / enabling loans
Disable loans on publishers (useful when debugging):
```bash
export ROS_DISABLE_LOANED_MESSAGES=1
```
Enable loans on subscriptions (opt-in, knowing the lifetime caveat):
```bash
export ROS_DISABLE_LOANED_MESSAGES=0
```

### Fast DDS XML configuration
Zero-copy data sharing requires Fast DDS to read its profile from XML so the
data-sharing transport can be enabled at participant level:
```bash
export RMW_FASTRTPS_USE_QOS_FROM_XML=1
export FASTRTPS_DEFAULT_PROFILES_FILE=/abs/path/zero_copy_profile.xml
```

A minimal XML enabling data sharing for one topic:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<profiles xmlns="http://www.eprosima.com/XMLSchemas/fastRTPS_Profiles">
  <data_writer profile_name="zero_copy_writer" is_default_profile="true">
    <qos>
      <data_sharing>
        <kind>AUTOMATIC</kind>
      </data_sharing>
    </qos>
  </data_writer>
  <data_reader profile_name="zero_copy_reader" is_default_profile="true">
    <qos>
      <data_sharing>
        <kind>AUTOMATIC</kind>
      </data_sharing>
    </qos>
  </data_reader>
</profiles>
```

### C++ Loaned Messages API
```cpp
auto pub = create_publisher<MyMsg>("/topic", rclcpp::SensorDataQoS());

// Borrow:
auto loaned = pub->borrow_loaned_message();
loaned.get().data = ...;        // fill in place
pub->publish(std::move(loaned)); // ownership returns to middleware
// loaned is invalid after publish.
```

### Python equivalent
```python
pub = node.create_publisher(MyMsg, "/topic", 10)
loaned = pub.borrow_loaned_message()
loaned.message.data = ...
pub.publish_loaned_message(loaned)
```

### Limitations / message types
- Plain Old Data (fixed-size, no dynamic fields like strings or unbounded
  arrays) is what loans guarantee. Non-POD messages fall back to heap
  allocation transparently.
- Loans only deliver true zero-copy when subscriber and publisher share a
  data-sharing transport (intra-process or Iceoryx-backed shared memory).
  Across hosts, the API still works but data is serialized normally.

---

## Using `ros2 param`

**Source**: https://docs.ros.org/en/jazzy/How-To-Guides/Using-ros2-param.html

### Problem this guide solves
Inspecting and changing node parameters at runtime, plus snapshotting and
restoring full parameter sets via YAML files.

### `ros2 param list`
List parameters of one node, or all nodes:
```bash
ros2 param list /my_node
ros2 param list
```

### `ros2 param get`
```bash
ros2 param get /my_node use_sim_time
```

### `ros2 param set`
```bash
ros2 param set /my_node use_sim_time false
```

The value is parsed as YAML, which means `off`, `on`, `yes`, `no` become
booleans, and a bare `1.0` becomes a double. To force a string, use the
explicit YAML tag:
```bash
ros2 param set /my_node my_string '!!str off'
```
Heterogeneous lists are not supported — a mixed-type YAML array is coerced to
a string list.

### `ros2 param delete`
Removes a dynamic parameter (one not declared by the node):
```bash
ros2 param delete /my_node my_string
```
Cannot delete a parameter the node declared via `declare_parameter`.

### `ros2 param describe`
```bash
ros2 param describe /my_node use_sim_time
```
Prints type, description, and constraints (e.g. integer range or
`additional_constraints` strings).

### `ros2 param dump`
Snapshot all of a node's parameters to YAML:
```bash
ros2 param dump /my_node
# writes ./my_node.yaml in the current directory
```
Output format:
```yaml
/my_node:
  ros__parameters:
    use_sim_time: false
    foo: 42
```

### `ros2 param load`
Reload parameters into a running node:
```bash
ros2 param load /my_node my_node.yaml
```
Pairs naturally with `dump` for snapshot-and-restore workflows.

### YAML file format with wildcards
The same file format works as a launch-time `--params-file`. Wildcards:
- `/**` — zero or more namespace tokens
- `/*`  — exactly one token
```yaml
/my_node:
  ros__parameters:
    explicit_value: 1

/**:
  ros__parameters:
    wildcard_full: "applies to every node"

/**/parameter_blackboard:
  ros__parameters:
    wildcard_namespace: "any namespace, this node name"

/*:
  ros__parameters:
    wildcard_root_only: "any node directly under /"
```

---

## Node Arguments (`--ros-args`)

**Source**: https://docs.ros.org/en/jazzy/How-To-Guides/Node-arguments.html

### Problem this guide solves
Passing remappings, parameters, and logging configuration to a node from the
command line, and forwarding them through composition and launch.

### Argument structure
All ROS-specific arguments live after `--ros-args`. Anything before is passed
to the program as ordinary `argv`.

### Remapping (`-r`)
Generic form: `-r <old>:=<new>`. Special keys for node identity:
- `-r __node:=<new_node_name>`
- `-r __ns:=<new_namespace>`

Example — rename node, set namespace, remap topic:
```bash
ros2 run demo_nodes_cpp talker --ros-args \
  -r __ns:=/demo \
  -r __node:=my_talker \
  -r chatter:=my_topic
```
Result: node `/demo/my_talker` publishes to `/demo/my_topic`.

### Composition: prefix with the node name
For container processes hosting multiple nodes, scope each remap with the
sub-node's name:
```bash
ros2 run composition manual_composition --ros-args \
  -r talker:__node:=my_talker \
  -r my_talker:chatter:=my_topic \
  -r listener:__node:=my_listener \
  -r my_listener:chatter:=my_topic
```

### Parameters

Inline (`-p`):
```bash
ros2 run demo_nodes_cpp parameter_blackboard --ros-args \
  -p some_int:=42 \
  -p "a_string:=Hello world" \
  -p "some_lists.some_integers:=[1, 2, 3, 4]" \
  -p "some_lists.some_doubles:=[3.14, 2.718]"
```
Note: nested parameters use dot syntax (`a.b.c`).

From a YAML file (`--params-file`):
```yaml
parameter_blackboard:
  ros__parameters:
    some_int: 42
    a_string: "Hello world"
    some_lists:
      some_integers: [1, 2, 3, 4]
      some_doubles: [3.14, 2.718]
```
```bash
ros2 run demo_nodes_cpp parameter_blackboard \
  --ros-args --params-file demo_params.yaml
```
Wildcards (`/**`, `/*`) work in the YAML file as in `ros2 param`.

### Logging
- `--log-level <name>:=<level>` — per-logger level (e.g.
  `--log-level rcl:=DEBUG` or `--log-level my_node:=INFO`).
- `--log-level <level>` (no `:=`) sets the default level for all loggers.
- `--log-file-name <prefix>` — prefix for the log file written under
  `ROS_LOG_DIR`.

### Other flags
- `--enclave <path>` — pick the SROS 2 security enclave for this process.
- `--disable-external-lib-logs`, `--enable-rosout-logs`, etc. (see
  `ros2 run --help` for the full list).

### Forwarding through `ros2 launch`
A launch file converts these into `Node(arguments=...)` and `parameters=...`
fields. To pass a `--params-file` from the CLI, use launch arguments:
```bash
ros2 launch my_pkg my_launch.py params_file:=/path/to/params.yaml
```
Then in the launch file:
```python
Node(
    package='my_pkg', executable='my_node',
    parameters=[LaunchConfiguration('params_file')],
    remappings=[('chatter', 'my_topic')],
    arguments=['--ros-args', '--log-level', 'INFO'],
)
```

---

## Getting Backtraces in ROS 2

**Source**: https://docs.ros.org/en/jazzy/How-To-Guides/Getting-Backtraces-in-ROS-2.html

### Problem this guide solves
A node crashes (SIGSEGV, abort, uncaught exception) and you need to find the
call stack — typically with debug symbols and gdb, sometimes via core dumps
or sanitizers.

### Build with debug symbols first
Without `-g` / `-O0` you get bare addresses and inlined frames. Build the
target package in Debug:
```bash
colcon build --packages-up-to <package_name> \
  --cmake-args -DCMAKE_BUILD_TYPE=Debug
```
Or per-target via `target_compile_options(<tgt> PRIVATE -g)` in CMakeLists.

### Run a node under gdb (`--prefix`)
The simplest pattern uses `ros2 run`'s `--prefix`:
```bash
ros2 run --prefix 'gdb -ex run --args' <pkg> <node>
```
gdb starts, immediately runs the program, and drops you into a prompt only on
crash. Then:
```
(gdb) backtrace
(gdb) quit
```

### Reading the trace
Frames are listed deepest first (`#0` is where the program died). Walk
upward until you hit a frame inside your own code; that is usually the
proximate cause.

### Launch files with gdb
Inside `launch_ros.actions.Node`, use the `prefix` argument.

With a GUI (separate xterm window so you keep your launch logs visible):
```python
prefix=['xterm -e gdb -ex run --args']
```

Headless / SSH:
```python
prefix=['gdb -ex run --args']
```

### Isolating one node from a big launch
If you cannot easily run the bad node alone, it's usually fastest to:
1. Comment out unrelated nodes in the launch file.
2. Rebuild the suspect package in Debug.
3. Start it standalone in another terminal under gdb, passing parameters via
   `--ros-args -r __node:=<name> --params-file /path/to/params.yaml` so it
   matches what the launch file would have produced.

### Debugging C++ tests
```bash
colcon build --cmake-clean-cache --mixin debug
source install/setup.bash
gdb -ex run ./build/<pkg>/test/<test_binary>
```
To stop on uncaught exceptions before gtest swallows them:
```
(gdb) catch throw
(gdb) run
```

### Automatic backtraces on crash — `backward_ros`
The `backward_cpp` library (wrapped as `backward_ros`) prints a formatted
trace whenever a process crashes. Add it as a depend in `package.xml` and
`find_package(backward_ros REQUIRED)` in CMakeLists; it injects itself into
all executables/libraries built afterwards. Useful in production / CI where
you want a trace without re-running under gdb.

### Beyond what the guide covers
Standard Linux mechanisms not detailed in the guide but used in practice:
- **Core dumps**: `ulimit -c unlimited`, then crash, then
  `gdb /path/to/exe /path/to/core`. Configure where cores go via
  `/proc/sys/kernel/core_pattern`.
- **Attach to running process**: `gdb -p <pid>` after `pgrep -f <node>`.
- **Sanitizers**: build with
  `--cmake-args -DCMAKE_CXX_FLAGS=-fsanitize=address` (ASan) or
  `-fsanitize=undefined` (UBSan), or `-fsanitize=thread` (TSan; not
  combinable with ASan). Run with `ASAN_OPTIONS=detect_leaks=1` etc.
- **`ROS_LOG_DIR`**: defaults to `~/.ros/log` (or `$ROS_HOME/log`); each
  process gets a timestamped subdirectory. Check stderr/stdout there when
  stdout is captured by launch.

---

## ROS 2 IDEs

**Source**: https://docs.ros.org/en/jazzy/How-To-Guides/ROS-2-IDEs.html

### Problem this guide solves
Getting an IDE to (a) find ROS 2 + workspace headers and Python modules,
(b) run/debug nodes, and (c) cope with the symlink/copy split between
`src/` and `install/`.

This is a community-contributed page; only **VSCode** and **PyCharm** are
explicitly covered. CLion, QtCreator, etc., are not.

### VSCode

Source the environment first, then launch VSCode from the *same* shell so it
inherits everything:
```bash
source /opt/ros/jazzy/setup.bash
cd ~/dev_ws
source ./install/setup.bash
/usr/bin/code ./src/my_node/
```
Quote from the guide: *"VSCode and any terminal created inside VSCode will
correctly inherit from the parent environment and should have ROS and
installed package available."*

Practical config:
- Bottom-right corner — confirm the Python interpreter is the same one the
  ROS 2 install uses (`/usr/bin/python3` on Ubuntu).
- If using a pre-sourced terminal, disable the Python extension's automatic
  venv activation — it can clobber `PYTHONPATH`.
- Debug configurations in `launch.json` should run the Python file directly
  (`module: my_pkg.my_node` or `program: ${workspaceFolder}/src/...`),
  **not** `ros2 run`. The latter spawns a child and gdb/python debug attach
  loses the breakpoints.

Caveat: *"After adding packages or making major changes you might need to
source your install again. The simplest way to do this is to close VSCode and
restart it."*

### PyCharm (Python only)

On Windows, manually point the interpreter at ROS:
1. Add the ROS Python executable.
2. In "Show Interpreter Paths", add the ROS bin and `Lib/site-packages`
   directories so PyCharm resolves `rclpy`, `geometry_msgs`, etc.

Two debug paths:
1. **Attach to a running process**: launch the node via `ros2 run`, then
   "Run" → "Attach to Process…" in PyCharm.
2. **Run/Debug Configuration**: override `PATH` in the configuration. Note:
   *"It is currently not supported to extend the existing PATH, so we need
   to override it."*

Caveat that bites everyone: code in `src/` may not match what runs, because
ament copies Python files into `install/` at build time. Either build with
`colcon build --symlink-install` so `install/` symlinks back to `src/`, or
open files from `install/<pkg>/lib/python3.X/site-packages/<pkg>/`.

### Other IDEs
The page explicitly says ROS 2 *"is not made around a specific development
environment"* — CLion / QtCreator / Vim users assemble their own setup,
typically by exporting `compile_commands.json` (build with
`--cmake-args -DCMAKE_EXPORT_COMPILE_COMMANDS=ON`) and pointing clangd /
ccls at it.

---

## Setup ROS 2 with VSCode and Docker Container (devcontainers)

**Source**: https://docs.ros.org/en/jazzy/How-To-Guides/Setup-ROS-2-with-VSCode-and-Docker-Container.html

### Problem this guide solves
Develop ROS 2 in a reproducible container while still using VSCode's editor,
debugger, and integrated terminals. Solves the "works on my machine" problem
and lets multiple developers share an exact toolchain.

### Prerequisites

```bash
sudo apt install docker.io git python3-pip
pip3 install vcstool
echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
```
Verify: `docker run hello-world`.
If the daemon isn't up: `sudo systemctl start docker`.

VSCode + Remote Development extension pack:
```bash
sudo apt update
sudo apt install software-properties-common apt-transport-https wget -y
wget -q https://packages.microsoft.com/keys/microsoft.asc -O- | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://packages.microsoft.com/repos/vscode stable main"
sudo apt install code
```
Then install "Remote Development" via Extensions (Ctrl+Shift+X).

### Workspace layout
```
ws/
├── .devcontainer/
│   ├── devcontainer.json
│   └── Dockerfile
└── src/
    ├── package1
    └── package2
```

### `.devcontainer/devcontainer.json`
Replace `YOUR_USERNAME` with the host username (`echo $USERNAME`). Replace
`ROS_DISTRO` references with `jazzy` for this project.
```json
{
    "name": "ROS 2 Development Container",
    "privileged": true,
    "remoteUser": "YOUR_USERNAME",
    "build": {
        "dockerfile": "Dockerfile",
        "args": { "USERNAME": "YOUR_USERNAME" }
    },
    "workspaceFolder": "/home/ws",
    "workspaceMount": "source=${localWorkspaceFolder},target=/home/ws,type=bind",
    "customizations": {
        "vscode": {
            "extensions": [
                "ms-vscode.cpptools",
                "ms-vscode.cpptools-themes",
                "twxs.cmake",
                "donjayamanne.python-extension-pack",
                "eamodio.gitlens",
                "ms-iot.vscode-ros"
            ]
        }
    },
    "containerEnv": {
        "DISPLAY": "unix:0",
        "ROS_AUTOMATIC_DISCOVERY_RANGE": "LOCALHOST",
        "ROS_DOMAIN_ID": "42"
    },
    "runArgs": [
        "--net=host",
        "--pid=host",
        "--ipc=host",
        "-e", "DISPLAY=${env:DISPLAY}"
    ],
    "mounts": [
       "source=/tmp/.X11-unix,target=/tmp/.X11-unix,type=bind,consistency=cached",
       "source=/dev/dri,target=/dev/dri,type=bind,consistency=cached"
    ],
    "postCreateCommand": "sudo rosdep update && sudo rosdep install --from-paths src --ignore-src -y && sudo chown -R $(whoami) /home/ws/"
}
```
Notable bits:
- `--net=host` is required for DDS multicast discovery to cross the
  container boundary.
- `/tmp/.X11-unix` and `/dev/dri` mounts plus `DISPLAY=unix:0` give X11 +
  GPU rendering for rviz / rqt.
- `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` keeps DDS off the LAN.

### `.devcontainer/Dockerfile`
Replace `ROS_DISTRO` with `jazzy`:
```dockerfile
FROM ros:ROS_DISTRO
ARG USERNAME=USERNAME
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Delete the user if it exists in the base image (Ubuntu Noble ships 'ubuntu')
RUN if id -u $USER_UID ; then userdel `id -un $USER_UID` ; fi

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y python3-pip
ENV SHELL /bin/bash
USER $USERNAME
CMD ["/bin/bash"]
```
The `osrf/ros:jazzy-desktop-full` image is a heavier alternative pre-loaded
with rviz and demo packages.

### Bringing up the container
Ctrl+Shift+P → "Dev Containers: Reopen in Container". VSCode builds the
image, mounts the workspace, and reconnects.

Verify:
```bash
sudo apt install ros-$ROS_DISTRO-rviz2 -y
source /opt/ros/$ROS_DISTRO/setup.bash
rviz2
```

### `launch.json` / `tasks.json` patterns
Although the official guide doesn't list them, the standard pair is:

`tasks.json`:
```json
{
    "version": "2.0.0",
    "tasks": [{
        "label": "colcon: build (Debug)",
        "type": "shell",
        "command": "colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Debug",
        "group": { "kind": "build", "isDefault": true },
        "options": { "cwd": "${workspaceFolder}" }
    }]
}
```

`launch.json` (C++ node under gdb):
```json
{
    "version": "0.2.0",
    "configurations": [{
        "name": "Debug my_node (gdb)",
        "type": "cppdbg",
        "request": "launch",
        "program": "${workspaceFolder}/install/my_pkg/lib/my_pkg/my_node",
        "cwd": "${workspaceFolder}",
        "MIMode": "gdb",
        "preLaunchTask": "colcon: build (Debug)",
        "setupCommands": [
            { "text": "source ${workspaceFolder}/install/setup.bash" }
        ]
    }]
}
```

### X11 troubleshooting
If rviz fails with "cannot connect to X server":
```bash
xhost +local:<USERNAME>
```
If `echo $DISPLAY` returns `1` inside the container, persist it:
```
echo "export DISPLAY=unix:1" >> /etc/bash.bashrc
```
and rebuild the container.

---

## Run 2 Nodes in Single or Separate Docker Containers

**Source**: https://docs.ros.org/en/jazzy/How-To-Guides/Run-2-nodes-in-single-or-separate-docker-containers.html

### Problem this guide solves
Walks through the simplest docker compositions for ROS 2: two nodes in one
container, two nodes in two containers, and the same with `docker compose`.

### Both nodes inside one container
```bash
docker pull osrf/ros:jazzy-desktop
docker run -it osrf/ros:jazzy-desktop
```
Then in the container shell:
```bash
ros2 run demo_nodes_cpp listener &
ros2 run demo_nodes_cpp talker
```
The listener and talker share the container's loopback, so DDS discovers
trivially.

### Two containers, manual

Terminal 1:
```bash
docker run -it --rm osrf/ros:jazzy-desktop ros2 run demo_nodes_cpp talker
```
Terminal 2:
```bash
docker run -it --rm osrf/ros:jazzy-desktop ros2 run demo_nodes_cpp listener
```

### Two containers, `docker compose`
`docker-compose.yml`:
```yaml
version: '2'

services:
  talker:
    image: osrf/ros:jazzy-desktop
    command: ros2 run demo_nodes_cpp talker
  listener:
    image: osrf/ros:jazzy-desktop
    command: ros2 run demo_nodes_cpp listener
    depends_on:
      - talker
```
```bash
docker compose up
# Ctrl+C to terminate
```

### Cross-container discovery (the bit the guide skips over)
Docker's default bridge network blocks UDP multicast, so DDS discovery does
not work between two `docker run` commands without help. Two practical
fixes:

1. **`--network=host`** on each `docker run`, which puts the container in the
   host's network namespace. Then they discover each other identically to two
   processes on the host:
   ```bash
   docker run -it --rm --network=host osrf/ros:jazzy-desktop \
     ros2 run demo_nodes_cpp talker
   ```
   In `docker-compose.yml`:
   ```yaml
   services:
     talker:
       image: osrf/ros:jazzy-desktop
       network_mode: "host"
       command: ros2 run demo_nodes_cpp talker
   ```

2. **Static peers / unicast discovery** via Fast DDS XML, useful when host
   networking is undesirable. Provide a profile with explicit peers and
   set `FASTRTPS_DEFAULT_PROFILES_FILE=/path/inside/container.xml` plus a
   shared `ROS_DOMAIN_ID`:
   ```bash
   docker run -it --rm \
     -e ROS_DOMAIN_ID=42 \
     -e FASTRTPS_DEFAULT_PROFILES_FILE=/cfg/peers.xml \
     -v $PWD/peers.xml:/cfg/peers.xml \
     osrf/ros:jazzy-desktop ros2 run demo_nodes_cpp talker
   ```

### Notes
- Always set `ROS_DOMAIN_ID` consistently across containers to avoid leaking
  topics across teams sharing the same host.
- For GUI nodes (rviz, rqt) inside containers, mount `/tmp/.X11-unix` and
  pass `DISPLAY` as in the devcontainer guide.

---

## Visualizing ROS 2 Data with Foxglove Studio

**Source**: https://docs.ros.org/en/jazzy/How-To-Guides/Visualizing-ROS-2-Data-With-Foxglove-Studio.html

### Problem this guide solves
RViz2 covers most cases, but Foxglove Studio offers a richer panel layout,
cross-platform desktop and web access, plot/teleop/diagnostic panels, and
direct MCAP / `.db3` playback. This guide explains how to feed it live ROS 2
data.

### Two ways to use Foxglove
- Web app at `https://studio.foxglove.dev` (Chrome).
- Desktop app from `https://foxglove.dev/download` (Linux, macOS, Windows).

### Live connection — the `foxglove_bridge` package
Install:
```bash
sudo apt install ros-jazzy-foxglove-bridge
```

Run with the provided launch file (defaults to `ws://localhost:8765`):
```bash
ros2 launch foxglove_bridge foxglove_bridge_launch.xml
```

Common parameters:
- `port:=8765` (default)
- `address:=0.0.0.0` (bind all interfaces, needed for remote Foxglove web)
- `tls:=false`
- `topic_whitelist:=['.*']`
- `service_whitelist:=['.*']`
- `param_whitelist:=['.*']`
- `send_buffer_limit:=10000000`
- `use_sim_time:=false`

Example with non-default port and whitelists:
```bash
ros2 run foxglove_bridge foxglove_bridge \
  --ros-args -p port:=8766 \
  -p topic_whitelist:='["/camera/.*", "/imu/.*"]'
```

### Connecting Foxglove
In Studio: **Open connection** → **Foxglove WebSocket** tab → enter
`ws://<host>:8765` → Connect. (The doc text says "Rosbridge (ROS 1 & 2)" tab;
Foxglove rebranded the protocol-native option to "Foxglove WebSocket" — both
work, the native option supports schemas and parameter editing where
rosbridge does not.)

### Schema autodiscovery
`foxglove_bridge` advertises message definitions for every published topic to
the client. Standard `std_msgs`, `sensor_msgs`, `geometry_msgs`, `nav_msgs`,
`tf2_msgs`, etc. are recognized by Studio's panels (3D, Image, Plot,
Diagnostics, Log, Map, ...). Custom messages also work — schemas are
extracted from the running node graph at connect time.

### Recorded data
Studio also opens local files directly:
- Drag-and-drop a `.db3` rosbag2 SQLite file (with the `metadata.yaml` next
  to it).
- Drag-and-drop an `.mcap` file. MCAP is the recommended bag format because
  it embeds message schemas, so Studio doesn't need separate `.msg`
  definitions to render custom messages.

To convert: `ros2 bag convert -i my_bag -o convert.yaml` with `mcap` storage,
or use the `mcap` CLI.

### Edge cases / gotchas
- If you're running both `rosbridge_server` and `foxglove_bridge`, keep them
  on different ports.
- Foxglove web (browsers) can't connect to `ws://` from a `https://` page in
  Chrome unless mixed content is allowed. Use the desktop app or run
  `foxglove_bridge` with TLS.
- `--network=host` Docker containers expose 8765 directly; bridged
  containers need `-p 8765:8765`.

---

## Using `ros1_bridge` (Jammy upstream)

**Source**: https://docs.ros.org/en/jazzy/How-To-Guides/Using-ros1_bridge-Jammy-upstream.html

### When this matters
Only relevant if you are interoperating with **ROS 1 Noetic** from a ROS 2
host. Noetic targets Ubuntu 20.04 Focal officially; this guide explains how
to bridge from Ubuntu 22.04 Jammy (the Humble baseline; the same recipe
applies on Jazzy via Noble or Jammy ROS 2 source builds, with the obvious
caveat that this is a steadily-decreasing-relevance topic since Noetic EOL
arrived in May 2025). For a greenfield drone perception project on Jazzy, you
almost certainly do not need this.

### Build constraint that bites everyone
The official ROS 2 apt repository ships a `python3-catkin-pkg-modules`
that conflicts with the Ubuntu-distributed ROS 1 packages on Jammy.
Consequence: **you cannot have both `apt`-installed ROS 1 and
`apt`-installed ROS 2 on the same Jammy machine.**

The supported workaround per the doc: *"Building ROS 2 from source is the
only configuration that works for ROS 2 on Ubuntu Jammy."*

### Setting up the dev environment (no ROS 2 apt repo!)
```bash
sudo apt update && sudo apt install -y \
  build-essential cmake git \
  python3-flake8 python3-flake8-blind-except python3-flake8-builtins \
  python3-flake8-class-newline python3-flake8-comprehensions \
  python3-flake8-deprecated python3-flake8-docstrings \
  python3-flake8-import-order python3-flake8-quotes \
  python3-pip python3-pytest python3-pytest-cov \
  python3-pytest-repeat python3-pytest-rerunfailures \
  python3-rosdep python3-setuptools wget

python3 -m pip install -U colcon-common-extensions vcstool
```
Note `colcon` is installed via pip, not apt, to avoid pulling in the
conflicting repo.

### Install ROS 1 from upstream Ubuntu
```bash
sudo apt update && sudo apt install -y ros-core-dev
```
(`ros-core-dev` is the upstream Debian metapackage that gives you `roscpp`,
`std_msgs`, `rosmsg`, etc., without the official `ros-noetic-*` repo.)

### Build ROS 2 from source
Follow the standard ROS 2 source-install guide into e.g. `~/ros2_humble`.
For Jazzy, replace with the Jazzy source manifest and target directory.

### Build the bridge
```bash
mkdir -p ~/ros1_bridge/src
cd ~/ros1_bridge/src
git clone https://github.com/ros2/ros1_bridge
cd ~/ros1_bridge
. ~/ros2_humble/install/local_setup.bash   # source ROS 2 only here
colcon build
```
The bridge package's CMake detects whichever ROS 1 message packages are on
the prefix path and generates conversion code per type.

### Running the bridge
Source both sides at runtime:
```bash
source /opt/ros/noetic/setup.bash         # or upstream ros-core-dev paths
source ~/ros2_humble/install/local_setup.bash
source ~/ros1_bridge/install/local_setup.bash
```

Then launch the dynamic bridge (auto-creates ROS1<->ROS2 mappings for any
matching topic):
```bash
ros2 run ros1_bridge dynamic_bridge
```
Or run only the topics the bridge already knows about on both sides:
```bash
ros2 run ros1_bridge dynamic_bridge --bridge-all-topics
```

For static, hand-defined mappings:
```bash
ros2 run ros1_bridge static_bridge
```

### Build constraints to remember
- **Source builds of both** are required for full custom-message support; if
  you bridge a topic whose `.msg` exists only on one side, the bridge can't
  generate the conversion stub.
- **Must be rebuilt** whenever you add a new `.msg` package to either side
  (`colcon build --packages-select ros1_bridge --cmake-force-configure`).
- **Memory**: the bridge build is heavy (every type pair = a separate
  template instantiation). Expect 8+ GB RAM use during compile.

### Why this is mostly historical for Jazzy
Noetic reached EOL in May 2025. New robotics work targets ROS 2 natively.
Keep this page bookmarked only if you must integrate with a legacy ROS 1
asset (e.g. an existing perception stack you can't port). For a fresh drone
perception research project on Jazzy, skip the bridge entirely.

---
