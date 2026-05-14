# Demos (ROS 2 Jazzy)

This file consolidates the runnable demos shipped with ROS 2 Jazzy. Each section
covers what the demo proves, the exact commands to launch it, the API surface
it exercises, and the gotchas that bite first-time users.

---

## QoS Settings for Lossy Networks
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Demos/Quality-of-Service.html

### What it demonstrates
A camera-style image publisher (`cam2image`) and a viewer subscriber
(`showimage`) communicating over a network that is intentionally degraded with
`tc netem`. The point is to show how the **reliability** axis of QoS changes
behavior under packet loss: `RELIABLE` will resend and starve throughput on a
lossy link; `BEST_EFFORT` drops frames but keeps frame rate up.

### Launch commands
```bash
# Subscriber (default reliable)
ros2 run image_tools showimage

# Publisher with simulated burger images, no real camera
ros2 run image_tools cam2image --ros-args -p burger_mode:=True

# Publisher from a real /dev/video device, with custom resolution
ros2 run image_tools cam2image --ros-args -p width:=640 -p height:=480

# Subscriber with best-effort reliability
ros2 run image_tools showimage --ros-args -p reliability:=best_effort

# Inject 5% loss on the loopback interface, then remove it
sudo tc qdisc add    dev lo root netem loss 5%
sudo tc qdisc delete dev lo root netem loss 5%
```

### QoSProfile — every axis and every value
A `rclcpp::QoS` (or `rclpy.qos.QoSProfile`) carries the following independent
policies. All of these are matched between publisher and subscriber at
discovery time:

| Field                          | Valid values / type                                                                                  | Meaning                                                                                  |
| ------------------------------ | ---------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `history`                      | `KEEP_LAST`, `KEEP_ALL`, `SYSTEM_DEFAULT`                                                            | Whether the middleware keeps only the last N samples or every sample until taken         |
| `depth`                        | `size_t` (queue depth, only meaningful with `KEEP_LAST`)                                             | How many samples to retain                                                               |
| `reliability`                  | `BEST_EFFORT`, `RELIABLE`, `SYSTEM_DEFAULT`                                                          | Whether the middleware retransmits dropped samples                                       |
| `durability`                   | `VOLATILE`, `TRANSIENT_LOCAL`, `SYSTEM_DEFAULT`                                                      | Whether late-joining subscribers get the last published sample(s)                        |
| `deadline`                     | `rclcpp::Duration` (0 = unlimited)                                                                   | Maximum expected period between samples; missed deadline raises a callback               |
| `lifespan`                     | `rclcpp::Duration` (0 = unlimited)                                                                   | Sample is dropped from history if older than this when delivered                         |
| `liveliness`                   | `AUTOMATIC`, `MANUAL_BY_TOPIC`, `SYSTEM_DEFAULT`                                                     | Who asserts that the publisher is alive — DDS itself or the user via `assert_liveliness` |
| `liveliness_lease_duration`    | `rclcpp::Duration` (0 = infinite)                                                                    | Subscriber considers the publisher dead if no liveliness assertion within this window    |
| `avoid_ros_namespace_conventions` | bool                                                                                              | If true, no `rt/`, `rq/`, etc. prefix is prepended to topic names on the wire            |

### Compatibility matrix (publisher vs subscriber)

A publisher and subscriber connect only if the subscriber's request is no
stricter than what the publisher offers. Concretely:

| Policy        | Publisher offers   | Subscriber requests | Compatible? |
| ------------- | ------------------ | ------------------- | ----------- |
| Reliability   | RELIABLE           | RELIABLE            | yes         |
| Reliability   | RELIABLE           | BEST_EFFORT         | yes         |
| Reliability   | BEST_EFFORT        | RELIABLE            | **no**      |
| Reliability   | BEST_EFFORT        | BEST_EFFORT         | yes         |
| Durability    | TRANSIENT_LOCAL    | TRANSIENT_LOCAL     | yes         |
| Durability    | TRANSIENT_LOCAL    | VOLATILE            | yes         |
| Durability    | VOLATILE           | TRANSIENT_LOCAL     | **no**      |
| Durability    | VOLATILE           | VOLATILE            | yes         |
| Deadline      | period `T_p`       | period `T_s`        | yes iff `T_p ≤ T_s` |
| Lifespan      | any                | any                 | always (publisher-side only) |
| Liveliness    | AUTOMATIC          | AUTOMATIC           | yes         |
| Liveliness    | MANUAL_BY_TOPIC    | AUTOMATIC           | yes         |
| Liveliness    | AUTOMATIC          | MANUAL_BY_TOPIC     | **no**      |
| Liveliness lease | publisher `L_p` | subscriber `L_s`    | yes iff `L_p ≤ L_s` |
| History       | n/a — local-only, not matched                                                       |             |

Mismatches don't crash; the connection is silently never established and an
incompatibility event is fired (`on_offered_qos_incompatible` /
`on_requested_qos_incompatible`).

### Preset profiles
- `rclcpp::SystemDefaultsQoS()` — leave each policy as `SYSTEM_DEFAULT`, RMW chooses.
- `rclcpp::SensorDataQoS()` — `KEEP_LAST`, depth 5, `BEST_EFFORT`, `VOLATILE`. Match for high-rate lossy sensor streams.
- `rclcpp::ParametersQoS()` — `KEEP_LAST`, depth 1000, `RELIABLE`, `VOLATILE`. Used for parameter services.
- `rclcpp::ServicesQoS()` — `KEEP_LAST`, depth 10, `RELIABLE`, `VOLATILE`. Default for service request/response.
- `rclcpp::ParameterEventsQoS()` — `KEEP_LAST`, depth 1000, `RELIABLE`, `VOLATILE`. For `/parameter_events`.
- Default for `create_publisher` / `create_subscription` if you pass an int N:
  `KEEP_LAST` depth N, `RELIABLE`, `VOLATILE`.

### Gotchas
- The lossy-network demo does not work with shared-memory transports (Connext,
  Fast DDS) on local connections — `tc netem` only affects the loopback
  interface and shared memory bypasses it.
- A `RELIABLE` subscriber will silently never see a `BEST_EFFORT` publisher.
  Always check `ros2 topic info -v` if a topic appears connected but no
  messages arrive.

---

## Managed Nodes (Lifecycle)
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Demos/Managed-Nodes.html
(plus https://github.com/ros2/demos/blob/jazzy/lifecycle/README.rst, which the
docs page delegates to)

### What it demonstrates
A talker, a listener and a service-client orchestrator showing the managed
lifecycle: the talker is `unconfigured` at startup and refuses to publish
until externally driven through `configure → activate`. This is the pattern
for hardware drivers: open device in `on_configure`, start streaming in
`on_activate`, stop in `on_deactivate`, release in `on_cleanup`.

### State machine
**Primary (steady) states:** `unconfigured`, `inactive`, `active`, `finalized`.
**Transition (intermediate) states:** `configuring`, `activating`,
`deactivating`, `cleaningup`, `shuttingdown`, `errorprocessing`.

| User-triggered transition | From            | Callback         | Success goes to | Failure goes to |
| ------------------------- | --------------- | ---------------- | --------------- | --------------- |
| `configure`               | unconfigured    | `on_configure`   | inactive        | unconfigured    |
| `activate`                | inactive        | `on_activate`    | active          | inactive        |
| `deactivate`              | active          | `on_deactivate`  | inactive        | active          |
| `cleanup`                 | inactive        | `on_cleanup`     | unconfigured    | inactive        |
| `shutdown`                | any             | `on_shutdown`    | finalized       | finalized       |
| (any callback throws / returns ERROR) | any | `on_error`     | unconfigured    | finalized       |

Callback return type: `rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn`
with values `SUCCESS`, `FAILURE`, `ERROR`. (Defined as `TRANSITION_CALLBACK_SUCCESS / _FAILURE / _ERROR` at the C-API layer.)

### Services and topics every lifecycle node exposes
- `/<node>/get_state` — `lifecycle_msgs/srv/GetState`
- `/<node>/change_state` — `lifecycle_msgs/srv/ChangeState` (transition by id or label)
- `/<node>/get_available_states` — `lifecycle_msgs/srv/GetAvailableStates`
- `/<node>/get_available_transitions` — `lifecycle_msgs/srv/GetAvailableTransitions`
- `/<node>/get_transition_graph` — full state machine
- `/<node>/transition_event` (publisher) — `lifecycle_msgs/msg/TransitionEvent` for every state change

### Launch commands
```bash
ros2 run lifecycle lifecycle_talker
ros2 run lifecycle lifecycle_listener
ros2 run lifecycle lifecycle_service_client     # drives the talker through states
# or all at once
ros2 launch lifecycle lifecycle_demo_launch.py

# CLI control
ros2 lifecycle nodes                            # list lifecycle-managed nodes
ros2 lifecycle list /lc_talker                  # available transitions from current state
ros2 lifecycle list /lc_talker -a               # whole graph
ros2 lifecycle get  /lc_talker                  # current state
ros2 lifecycle set  /lc_talker configure
ros2 lifecycle set  /lc_talker activate

# Equivalent raw service call (transition id 1 = configure, 3 = activate, ...)
ros2 service call /lc_talker/change_state \
    lifecycle_msgs/srv/ChangeState "{transition: {id: 1}}"
```

### Minimal C++ skeleton
```cpp
#include "rclcpp_lifecycle/lifecycle_node.hpp"
using CallbackReturn =
  rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn;

class Driver : public rclcpp_lifecycle::LifecycleNode {
public:
  explicit Driver(const rclcpp::NodeOptions & opts)
  : LifecycleNode("driver", opts) {}

  CallbackReturn on_configure(const rclcpp_lifecycle::State &) override {
    pub_ = create_lifecycle_publisher<std_msgs::msg::String>("chatter", 10);
    timer_ = create_wall_timer(500ms, [this]{ /* publish() here is a no-op until active */ });
    return CallbackReturn::SUCCESS;
  }
  CallbackReturn on_activate(const rclcpp_lifecycle::State & s) override {
    LifecycleNode::on_activate(s);   // activates every LifecyclePublisher owned by this node
    return CallbackReturn::SUCCESS;
  }
  CallbackReturn on_deactivate(const rclcpp_lifecycle::State & s) override {
    LifecycleNode::on_deactivate(s);
    return CallbackReturn::SUCCESS;
  }
  CallbackReturn on_cleanup(const rclcpp_lifecycle::State &) override {
    timer_.reset(); pub_.reset();
    return CallbackReturn::SUCCESS;
  }
  CallbackReturn on_shutdown(const rclcpp_lifecycle::State &) override {
    return CallbackReturn::SUCCESS;
  }

private:
  rclcpp_lifecycle::LifecyclePublisher<std_msgs::msg::String>::SharedPtr pub_;
  rclcpp::TimerBase::SharedPtr timer_;
};
```

### Gotchas
- A `LifecyclePublisher::publish()` call in `inactive` does not throw — it
  silently drops the message. The published counter still increments. This is
  by design (timers can keep ticking) but surprises debuggers.
- Plain (non-lifecycle) subscribers will only see messages while the talker is
  in `active`. There is no buffering across deactivate/activate.
- `on_error` defaults to returning `FAILURE`, which sends the node to
  `finalized`. Override it if you want to recover to `unconfigured`.
- A managed node does **not** auto-progress. Something external (a launch
  file, a manager, or `ros2 lifecycle set`) must drive transitions.

---

## Intra-Process Communication
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Demos/Intra-Process-Communication.html

### What it demonstrates
Zero-copy message passing between publisher and subscriber when both live in
the same process and the publisher hands ownership via `std::unique_ptr`. The
demos print the raw pointer address of each message at both ends; the
addresses are identical, proving no copy occurred.

### Launch commands
```bash
ros2 run intra_process_demo two_node_pipeline           # producer → consumer
ros2 run intra_process_demo cyclic_pipeline             # pipe1 ↔ pipe2 ring
ros2 run intra_process_demo image_pipeline_all_in_one
ros2 run intra_process_demo image_pipeline_with_two_image_view
```

### How to enable
Per-node, at construction time:
```cpp
auto node = std::make_shared<MyNode>(
  "my_node",
  rclcpp::NodeOptions().use_intra_process_comms(true));
```
For Python: `rclpy.create_node('my_node', use_intra_process_comms=True)` (via
the equivalent `NodeOptions`).

### Conditions for the zero-copy fast path
1. Publisher and **all** matched subscribers are inside the same process
   (typical via component containers / `ComponentManager`).
2. Both ends were created with `use_intra_process_comms(true)`.
3. QoS uses `history = KEEP_LAST` and `durability = VOLATILE`. `KEEP_ALL` and
   `TRANSIENT_LOCAL` force the fall-back inter-process path.
4. The publisher hands a `std::unique_ptr<MsgT>` (not a `const &` and not a
   `shared_ptr`).
5. Exactly one subscriber owns the message — if multiple intra-process
   subscribers are matched, only one receives the original; the rest receive
   copies.
6. If any inter-process subscriber is also matched, the message is also
   serialized and shipped over the wire (the intra-process subscriber still
   gets the original).

### Code pattern
```cpp
// Publisher
auto msg = std::make_unique<std_msgs::msg::Int32>();
msg->data = ++count_;
printf("Published %d at 0x%" PRIXPTR "\n",
       msg->data, reinterpret_cast<std::uintptr_t>(msg.get()));
pub_->publish(std::move(msg));            // ownership transferred

// Subscriber (note: UniquePtr, not const Ref)
sub_ = create_subscription<std_msgs::msg::Int32>(
  "topic", 10,
  [](std_msgs::msg::Int32::UniquePtr msg) {
    printf("Received %d at 0x%" PRIXPTR "\n",
           msg->data, reinterpret_cast<std::uintptr_t>(msg.get()));
  });
```

### Gotchas
- If the publisher fires before discovery completes, the very first message
  is lost (typical at low rates like 1 Hz). Not specific to intra-process,
  but very visible here.
- Subscribing with `const MsgT &` or `std::shared_ptr<const MsgT>` forces a
  copy even when intra-process is enabled.
- macOS UDP buffers can be too small and produce
  `ddsi_conn_write failed -1`; raise the system `net.inet.udp.maxdgram`.

---

## Recording with the ROS 1 Bridge (rosbag)
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Demos/Rosbag-with-ROS1-Bridge.html

### What it demonstrates
Using `ros1_bridge`'s `dynamic_bridge` to mirror topics between a running ROS 1
master and ROS 2, then recording the bridged topics with the ROS 1 `rosbag`
tool, and conversely playing a ROS 1 bag and consuming it from ROS 2.

### Commands
```bash
# Terminal A (ROS 1)
. /opt/ros/<ros1_distro>/setup.bash
roscore

# Terminal B (bridge — sources both)
. /opt/ros/<ros1_distro>/setup.bash
. /opt/ros/jazzy/setup.bash
export ROS_MASTER_URI=http://localhost:11311
ros2 run ros1_bridge dynamic_bridge --bridge-all-topics

# Terminal C (record from the ROS 1 side)
rosbag record /image /imu_data /odom

# Or playback into ROS 2
rosbag play --loop path/to/bag_file
# and verify on ROS 2 side
ros2 topic list
ros2 topic echo /odom
```

### Gotchas / requirements
- `ros1_bridge` is not a binary release for Jazzy paired with modern ROS 1;
  in practice you must build it from source against both distros.
- `--bridge-all-topics` is needed to get topics whose types do not yet have a
  ROS 2 subscriber/publisher — otherwise the bridge only forwards
  bidirectionally-matched topics.
- ROS 1 namespaces do not always survive the bridge cleanly.
- ROS 1 itself is end-of-life; this demo is mainly useful for migrating
  legacy bag corpora.

---

## Real-Time Programming (pendulum_control)
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Demos/Real-Time-Programming.html

### What it demonstrates
A control loop simulating an inverted pendulum, instrumented with `rttest` to
measure jitter, page faults, and missed deadlines. The point is to show the
techniques required to make a ROS 2 node deterministic enough for hard
real-time loops.

### Commands
```bash
source ./install/setup.bash
ros2 run pendulum_control pendulum_demo

# With a logger that subscribes to runtime stats
ros2 run pendulum_control pendulum_logger
ros2 run pendulum_control pendulum_demo

# Save raw results, then plot
ros2 run pendulum_control pendulum_demo -f pendulum_demo_results
ros2 run rttest        rttest_plot pendulum_demo_results
```
Useful pendulum_demo flags: `-i <iterations>` (default 1000), `-u <period>`
(default `1ms`, accepts `s|ms|us|ns`), `-f <output_file>`.

### Real-time techniques in the demo
- **`mlockall(MCL_CURRENT | MCL_FUTURE)`** to pin the entire address space in
  RAM, preventing page faults from blocking on disk I/O.
- **TLSF allocator** (`tlsf_cpp`) wired in via `rclcpp::allocator::AllocatorMemoryStrategy`
  so message construction is bounded-time instead of going through `malloc`.
- **`SCHED_FIFO`** with priority 98 via `pthread_setschedparam`. Requires
  `<user> - rtprio 98` (and a generous `memlock`) in `/etc/security/limits.conf`.
- **Pre-allocated message pools** so no allocation happens inside the loop.
- **ConnextDDS as the only middleware** in the original demo because of its
  static / pre-allocatable APIs.
- Verify your kernel: `uname -a` should mention `PREEMPT_RT` (or `PREEMPT RT`).

### Reported metrics
For each run, `rttest` prints minimum / maximum / mean / std-dev latency in
nanoseconds, plus minor and major page-fault counts.

### Platform requirements / gotchas
- Linux only. Don't try this on macOS or Windows.
- A vanilla kernel without `PREEMPT_RT` will produce huge tail latencies and
  defeat the demo.
- Need ≥ 8 GB of free RAM because `mlockall` disables swap.
- Running without proper `limits.conf` entries yields
  `Couldn't set scheduling priority` and the loop falls back to `SCHED_OTHER`.
- Failed `mlockall` does not abort; it is recorded as page-fault noise.

---

## Dummy Robot Demo
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Demos/dummy-robot-demo.html

### What it demonstrates
A minimal end-to-end scene: a fake URDF robot ("RRbot"), a fake joint-state
publisher, a fake laser scan, and a fake static map, all glued together by
`robot_state_publisher` so TF resolves and RViz can render the model.

### Commands
```bash
ros2 launch dummy_robot_bringup dummy_robot_bringup_launch.py
# in another terminal
rviz2
# In RViz: set Fixed Frame = "world", add the TF and RobotModel displays
```

### Nodes the launch file starts
- `dummy_map_server` — publishes an empty `nav_msgs/OccupancyGrid` periodically.
- `dummy_laser` — publishes synthetic `sensor_msgs/LaserScan`.
- `dummy_joint_states` — publishes `sensor_msgs/JointState` for the two joints.
- `robot_state_publisher` — parses the URDF, consumes the joint states, and
  broadcasts the resulting `tf`/`tf_static`.

### Gotchas
- If the RobotModel display shows nothing, the global frame in RViz is
  probably set to a frame the URDF doesn't define — switch to `world`.
- `robot_state_publisher` only republishes TF when a new joint state arrives.
  If `dummy_joint_states` is not running, TF goes stale.

---

## Logging and Logger Configuration
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Demos/Logging-and-logger-configuration.html

### What it demonstrates
The `logging_demo` package shows the `RCLCPP_*` macro family, the
`rclpy.Logger` API, runtime per-node level changes via the `set_logger_levels`
service, and the rcutils environment-variable knobs.

### Severity levels
`DEBUG < INFO < WARN < ERROR < FATAL`. Setting a logger to `WARN` suppresses
DEBUG and INFO; `set_logger_level("rcl", DEBUG)` floods the console with
middleware traces.

### C++ macros (header `rclcpp/logging.hpp`)
For each severity `X` ∈ `{DEBUG, INFO, WARN, ERROR, FATAL}`:

| Macro                                                                       | Purpose                                              |
| --------------------------------------------------------------------------- | ---------------------------------------------------- |
| `RCLCPP_X(logger, fmt, ...)`                                                | printf-style                                         |
| `RCLCPP_X_STREAM(logger, stream_expr)`                                      | C++ ostream-style                                    |
| `RCLCPP_X_ONCE(logger, ...)`                                                | log only the first time the line is hit              |
| `RCLCPP_X_SKIPFIRST(logger, ...)`                                           | skip the first hit, then always log                  |
| `RCLCPP_X_THROTTLE(logger, clock, duration_ms, ...)`                        | log no more than once per `duration_ms`              |
| `RCLCPP_X_SKIPFIRST_THROTTLE(logger, clock, duration_ms, ...)`              | combination                                          |
| `RCLCPP_X_EXPRESSION(logger, bool_expr, ...)`                               | log only when `bool_expr` is true                    |
| `RCLCPP_X_FUNCTION(logger, predicate_fn, ...)`                              | log only when `predicate_fn()` returns true          |
| `RCLCPP_X_STREAM_ONCE / _SKIPFIRST / _THROTTLE / ...`                       | every variant exists in stream form too              |

Python equivalents are method calls on `node.get_logger()`, which take the
keyword arguments `once=True`, `skip_first=True`, `throttle_duration_sec=…`,
`throttle_time_source_type=…`.

### Named / child loggers
- `node->get_logger()` returns a logger named after the fully-qualified node name.
- `node->get_logger().get_child("submodule")` returns a logger whose name is
  `<node>.submodule`. Levels can be set independently per child.
- Free-standing loggers: `rclcpp::get_logger("my_lib")`.

### Setting levels
```bash
# At launch, default level for all unnamed loggers
ros2 run logging_demo logging_demo_main --ros-args --log-level DEBUG

# Per-logger
ros2 run logging_demo logging_demo_main --ros-args \
    --log-level my_node:=DEBUG --log-level my_node.subsystem:=WARN

# At runtime via service (only when node was constructed with enable_logger_service=True)
ros2 service call /my_node/set_logger_levels \
    rcl_interfaces/srv/SetLoggerLevels \
    "{levels: [{name: 'my_node.subsystem', level: 10}]}"   # 10=DEBUG, 20=INFO, ...
ros2 service call /my_node/get_logger_levels rcl_interfaces/srv/GetLoggerLevels
```

Programmatic:
```cpp
auto ret = rcutils_logging_set_logger_level(
    logger.get_name(), RCUTILS_LOG_SEVERITY_DEBUG);
```

### Log file location
Resolved in this order:
1. `$ROS_LOG_DIR` if set and non-empty.
2. `$ROS_HOME/log` if `$ROS_HOME` is set.
3. `~/.ros/log/` otherwise.
Each launch creates a timestamped subdirectory; `--log-file-name <prefix>`
overrides the per-node file prefix.

### Environment variables
| Variable                          | Effect                                                                         |
| --------------------------------- | ------------------------------------------------------------------------------ |
| `RCUTILS_LOGGING_USE_STDOUT=1`    | route everything to stdout (default: DEBUG/INFO → stdout, WARN+ → stderr)      |
| `RCUTILS_COLORIZED_OUTPUT=0/1`    | force-disable / force-enable ANSI colors (default: auto-detect TTY)            |
| `RCUTILS_CONSOLE_OUTPUT_FORMAT`   | template using `{severity}`, `{name}`, `{message}`, `{time}`, `{time_as_nanoseconds}`, `{file_name}`, `{function_name}`, `{line_number}` |
| `RCUTILS_LOGGING_BUFFERED_STREAM=1` | buffered I/O instead of unbuffered                                             |
| `ROS_LOG_DIR` / `ROS_HOME`        | see "Log file location" above                                                  |

### Code snippets
```cpp
auto logger = node->get_logger();
RCLCPP_INFO(logger, "started, pid=%d", getpid());
RCLCPP_INFO_STREAM(logger, "tracking " << n << " features");
RCLCPP_DEBUG_THROTTLE(logger, *node->get_clock(), 1000,
                      "loop running at %f Hz", hz);
RCLCPP_WARN_ONCE(logger.get_child("calib"), "no calibration file found");
```
```python
node = rclpy.create_node('NodeWithLoggerService', enable_logger_service=True)
node.get_logger().info('hello %d' % 42)
node.get_logger().warn('rate-limited', throttle_duration_sec=1.0)
```

### Gotchas
- `get_logger_levels` / `set_logger_levels` are **not thread-safe**; only
  call them from one thread.
- The logging macros append a newline automatically — don't add `\n`.
- Under `ros2 launch`, color is off by default because the child stdout is
  not a TTY. Either set `RCUTILS_COLORIZED_OUTPUT=1` in the environment
  block or pass `emulate_tty=True` to the `Node` action.
- Setting the empty-name (root) logger to a level does **not** override
  loggers that have been individually configured.

---

## Content Filtering Subscription
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Demos/Content-Filtering-Subscription.html

### What it demonstrates
A subscriber that asks the DDS layer to deliver only messages matching a
SQL-like predicate. The example publishes temperatures from -100 to 150 in
10° steps once per second; the subscriber receives only values
`< -30` or `> 100`.

### Commands
```bash
ros2 run demo_nodes_cpp content_filtering_publisher
ros2 run demo_nodes_cpp content_filtering_subscriber

# Show the silent-fallback behavior under an unsupported RMW
RMW_IMPLEMENTATION=rmw_cyclonedds_cpp \
    ros2 run demo_nodes_cpp content_filtering_subscriber
```

### API
```cpp
rclcpp::SubscriptionOptions sub_options;
sub_options.content_filter_options.filter_expression =
    "data < %0 OR data > %1";                       // DDS spec, Annex B
sub_options.content_filter_options.expression_parameters =
    {"-30.0", "100.0"};                             // bind %0, %1

sub_ = create_subscription<std_msgs::msg::Float32>(
    "temperature", 10, callback, sub_options);

if (!sub_->is_cft_enabled()) {
  RCLCPP_WARN(get_logger(),
              "Content filter NOT active — RMW does not support it");
}
```
The filter expression is a small SQL fragment over the message fields
(comparison operators, `AND`/`OR`/`NOT`, parentheses); parameters are
positional `%0`, `%1`, …

### RMW support
| RMW                  | Content filtering |
| -------------------- | ----------------- |
| `rmw_fastrtps_cpp`   | yes               |
| `rmw_connextdds`     | yes               |
| `rmw_cyclonedds_cpp` | no                |
| `rmw_zenoh_cpp`      | no                |

### Gotchas
- On an RMW that does not support content filtering, `create_subscription`
  silently produces a normal subscriber that receives **every** message.
  Always check `is_cft_enabled()` if filtering is load-bearing.
- The filter is evaluated by the publisher-side DDS reader where possible
  (saves bandwidth) but this is implementation-defined.

---

## Service Introspection
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Demos/Service-Introspection.html

### What it demonstrates
Each service / client can be told to publish a `service_msgs/msg/ServiceEventInfo`
(plus optionally the request/response payload) on a sibling topic
`/<service_name>/_service_event`. This makes the otherwise-opaque request /
response interaction observable with the same tools as topics.

### Commands
```bash
ros2 run demo_nodes_cpp introspection_service
ros2 run demo_nodes_cpp introspection_client

# Toggle introspection level via parameters
ros2 param set /introspection_service service_configure_introspection contents
ros2 param set /introspection_client  client_configure_introspection  metadata

# Watch the events
ros2 service echo --flow-style /add_two_ints
# or as a plain topic
ros2 topic echo /add_two_ints/_service_event
```

### Introspection levels
| Level                              | What gets published                                |
| ---------------------------------- | -------------------------------------------------- |
| `RCL_SERVICE_INTROSPECTION_OFF`      | nothing (default)                                  |
| `RCL_SERVICE_INTROSPECTION_METADATA` | event type + timestamp + client GID + sequence num |
| `RCL_SERVICE_INTROSPECTION_CONTENTS` | metadata **plus** the request and response bodies  |

### Event types
`REQUEST_SENT`, `REQUEST_RECEIVED`, `RESPONSE_SENT`, `RESPONSE_RECEIVED`. The
client typically emits the SENT/RECEIVED pair for the request leg, and the
server emits the RECEIVED/SENT pair.

### API
```cpp
this->srv_->configure_introspection(
    this->get_clock(),
    rclcpp::SystemDefaultsQoS(),
    RCL_SERVICE_INTROSPECTION_CONTENTS);

this->client_->configure_introspection(
    this->get_clock(),
    rclcpp::SystemDefaultsQoS(),
    RCL_SERVICE_INTROSPECTION_METADATA);
```

### Gotchas
- Introspection is off by default; nothing appears on `_service_event` until
  enabled on at least one side.
- Client and server may run at different levels; an event coming from the
  client at `METADATA` will have empty `request`/`response` fields even if
  the server is at `CONTENTS`.
- The QoS on the introspection publisher matters — using `SystemDefaultsQoS`
  is the safe choice for `ros2 topic echo` to pick it up.

---

## Wait for Acknowledgment
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Demos/Wait-for-Acknowledgment.html

### What it demonstrates
A publisher that, before shutting down, blocks until every matched
`RELIABLE` subscriber has acknowledged delivery of all in-flight messages.
This is the safe pattern for "send last command, then exit" scenarios.

### Commands
```bash
ros2 run examples_rclcpp_minimal_subscriber subscriber_member_function
ros2 run examples_rclcpp_minimal_publisher  publisher_wait_for_all_acked
# Ctrl-C the publisher; it prints either
#   "All subscribers acknowledge messages."
# or a timeout failure.
```

### API
```cpp
// pub_ must have been created with reliability = RELIABLE
auto timeout = std::chrono::seconds(2);
bool ok = pub_->wait_for_all_acked(timeout);
if (!ok) {
  RCLCPP_WARN(get_logger(), "Some subscribers did not ack within timeout");
}
```
Pass `std::chrono::milliseconds(-1)` (or `rclcpp::Duration(-1, 0)`) for an
unbounded wait.

### Gotchas
- Only meaningful with `RELIABLE` reliability. With `BEST_EFFORT` the call
  returns immediately as success because the protocol has no acks to wait
  for.
- `wait_for_all_acked` returns `true` immediately if there are no matched
  subscribers — "everyone has acked" is vacuously true.
- A subscriber that connects then disappears mid-flight can cause a timeout
  even though no live consumer is waiting for the data.
