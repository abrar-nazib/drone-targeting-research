# Advanced Tutorials (ROS 2 Jazzy)

This file covers the non-simulator, non-security Advanced tutorials. The
Advanced index also lists **Simulators** and **Security** sub-trees, which
are intentionally out of scope here.

## Index of Advanced tutorials
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Advanced.html

The Advanced page links to:

1. Supplementing custom rosdep keys — `Advanced/Supplementing-Custom-Rosdep-Keys.html`
2. Enabling topic statistics (C++) — `Advanced/Topic-Statistics-Tutorial/Topic-Statistics-Tutorial.html`
3. Using Fast DDS Discovery Server as discovery protocol — `Advanced/Discovery-Server/Discovery-Server.html`
4. Implementing a custom memory allocator — `Advanced/Allocator-Template-Tutorial.html`
5. Ament Lint CLI Utilities — `Advanced/Ament-Lint-For-Clean-Code.html`
6. Unlocking the potential of Fast DDS middleware — `Advanced/FastDDS-Configuration.html`
7. Improved Dynamic Discovery — `Advanced/Improved-Dynamic-Discovery.html`
8. Recording a bag from a node (C++) — `Advanced/Recording-A-Bag-From-Your-Own-Node-CPP.html`
9. Recording a bag from a node (Python) — `Advanced/Recording-A-Bag-From-Your-Own-Node-Py.html`
10. Reading from a bag file (C++) — `Advanced/Reading-From-A-Bag-File-CPP.html`
11. Create an rqt_bag Plugin — `Advanced/Create-An-Rqtbag-Plugin.html`
12. How to use ros2_tracing to trace and analyze an application — `Advanced/ROS2-Tracing-Trace-and-Analyze.html`
13. Creating an rmw implementation — `Advanced/Creating-An-RMW-Implementation.html`
14. Simulators (sub-index, out of scope) — `Advanced/Simulators/Simulation-Main.html`
15. Security (sub-index, out of scope) — `Advanced/Security/Security-Main.html`

---

## Supplementing Custom Rosdep Keys
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Advanced/Supplementing-Custom-Rosdep-Keys.html

**What it solves.** When a dependency is not in the official rosdistro
(proprietary lib, niche lib, locally-built ROS package), instead of forking
rosdistro you add an additional rosdep YAML source on top of the defaults.

**How rosdep is wired.** Sources live in `/etc/ros/rosdep/sources.list.d/`.
The default is `/etc/ros/rosdep/sources.list.d/20-default.list`, which has
entries like:

```
yaml https://raw.githubusercontent.com/ros/rosdistro/master/rosdep/base.yaml
yaml https://raw.githubusercontent.com/ros/rosdistro/master/rosdep/python.yaml
```

`rosdep update` compiles all sources into a local cache.

**Step 1 — add a sources file** (sudo). Lower numeric prefix = higher
override priority, so something like `30-custom.list` adds *after* the
default, while `10-custom.list` would override it:

```
yaml file:///etc/ros/rosdep/custom_rules.yaml
```

(Both `file://` and `https://` URLs work. Local absolute paths need three
slashes: `file:///etc/...`.)

**Step 2 — write the YAML** at `/etc/ros/rosdep/custom_rules.yaml`:

```yaml
awesome_library:
  ubuntu: [awesome_library]
that_other_library:
  ubuntu:
    pip:
      packages: [another_library]
```

This defines two keys: `awesome_library` resolves to apt package
`awesome_library`, and `that_other_library` resolves to pip package
`another_library` (both Ubuntu only).

**Step 3 — refresh the cache:**

```bash
rosdep update
```

**Step 4 — verify resolution:**

```bash
rosdep resolve awesome_library
# #apt
# awesome_library

rosdep resolve that_other_library
# #pip
# another_library
```

**Step 5 — use in `package.xml`:**

```xml
<depend>awesome_library</depend>
```

**Caveats.** Rules are not merged across sources for the same OS — they
override completely or are ignored depending on numeric load order.
Third-party APT PPAs / pip indexes still need to be configured
system-wide for the resolved package name to actually install.

---

## Enabling Topic Statistics (C++)
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Advanced/Topic-Statistics-Tutorial/Topic-Statistics-Tutorial.html

**What it does.** Per-subscription, rclcpp can measure message age and
inter-arrival period and publish summary stats to a topic for live
diagnosis of pub/sub performance.

**`SubscriptionOptions::topic_stats_options` fields.**

| Field            | Purpose                              | Default       |
|------------------|--------------------------------------|---------------|
| `state`          | enable / disable collection          | `Disable`     |
| `publish_period` | collection + publish interval        | 1 second      |
| `publish_topic`  | output topic name                    | `/statistics` |

**C++ subscription skeleton:**

```cpp
#include "rclcpp/subscription_options.hpp"

auto options = rclcpp::SubscriptionOptions();
options.topic_stats_options.state =
    rclcpp::TopicStatisticsState::Enable;
options.topic_stats_options.publish_period =
    std::chrono::seconds(10);
// options.topic_stats_options.publish_topic = "/my_stats"; // optional

subscription_ = this->create_subscription<std_msgs::msg::String>(
  "topic", 10, callback, options);
```

**Metrics emitted.** For each of `message_age` (time since the publisher
stamped it) and `message_period` (gap between successive arrivals), the
following `StatisticDataType` values are published:

- 1 = average
- 2 = minimum
- 3 = maximum
- 4 = standard deviation
- 5 = sample count

**Run:**

```bash
colcon build
ros2 run cpp_pubsub listener_with_topic_statistics   # subscriber w/ stats on
ros2 run cpp_pubsub talker                            # publisher
ros2 topic list
ros2 topic echo /statistics                           # YAML stat messages
```

---

## Fast DDS Discovery Server
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Advanced/Discovery-Server/Discovery-Server.html

**Why use it.** Replaces the default Simple Discovery Protocol's
multicast-heavy chatter with a centralized client-server model. Scales
better with node counts, works on flaky-multicast links (WiFi), reduces
discovery-phase traffic.

### `fastdds discovery` CLI

Start a server (id 0, listening on UDP 11811):

```bash
fastdds discovery --server-id 0 --udp-address 127.0.0.1 --udp-port 11811
```

Common flags:
- `--server-id <N>` — unique server identifier (0..255)
- `--udp-address <IP>` — listening interface
- `--udp-port <PORT>` — port (default 11811)
- `--backup` — persist state across restarts

### Client env vars

Linux:

```bash
export ROS_DISCOVERY_SERVER=127.0.0.1:11811
ros2 run demo_nodes_cpp talker --ros-args --remap __node:=talker_discovery_server
ros2 run demo_nodes_cpp listener --ros-args --remap __node:=listener_discovery_server
```

Windows: `set ROS_DISCOVERY_SERVER=127.0.0.1:11811`.

### Multiple servers / partitions

Run two servers in separate terminals:

```bash
fastdds discovery --server-id 0 --udp-address 127.0.0.1 --udp-port 11811
fastdds discovery --server-id 1 --udp-address 127.0.0.1 --udp-port 11888
```

`ROS_DISCOVERY_SERVER` is a semicolon-separated list. **Server id is
determined by the index position (0-based) in the list, not by `--server-id`
above.**

```bash
# redundancy — node sees both
export ROS_DISCOVERY_SERVER="127.0.0.1:11811;127.0.0.1:11888"

# partition — node only on server 0
export ROS_DISCOVERY_SERVER="127.0.0.1:11811"

# partition — node only on server 1 (note empty slot for index 0)
export ROS_DISCOVERY_SERVER=";127.0.0.1:11888"
```

### Super Client (so CLI tools see everything)

Tools like `ros2 topic list`, `rqt_graph`, and the `ros2 daemon` need to
join *all* servers. Configure them as Super Clients via XML, e.g.
`super_client_configuration_file.xml`:

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<dds>
  <profiles xmlns="http://www.eprosima.com/XMLSchemas/fastRTPS_Profiles">
    <participant profile_name="super_client_profile" is_default_profile="true">
      <rtps>
        <builtin>
          <discovery_config>
            <discoveryProtocol>SUPER_CLIENT</discoveryProtocol>
            <discoveryServersList>
              <RemoteServer prefix="44.53.00.5f.45.50.52.4f.53.49.4d.41">
                <metatrafficUnicastLocatorList>
                  <locator>
                    <udpv4>
                      <address>127.0.0.1</address>
                      <port>11811</port>
                    </udpv4>
                  </locator>
                </metatrafficUnicastLocatorList>
              </RemoteServer>
            </discoveryServersList>
          </discovery_config>
        </builtin>
      </rtps>
    </participant>
  </profiles>
</dds>
```

Activate and restart the daemon:

```bash
export FASTRTPS_DEFAULT_PROFILES_FILE=super_client_configuration_file.xml
ros2 daemon stop
ros2 daemon start
ros2 topic list
ros2 run rqt_graph rqt_graph
```

For tools without daemon support: `ros2 topic list --no-daemon`,
`ros2 node info /talker --no-daemon --spin-time 2`.

### Large-scale (100+ participants on a single host)

Bump `mutation_tries` via Fast DDS XML:

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<dds xmlns="http://www.eprosima.com">
  <profiles>
    <participant profile_name="participant_profile" is_default_profile="true">
      <rtps>
        <builtin>
          <mutation_tries>1000</mutation_tries>
        </builtin>
      </rtps>
    </participant>
  </profiles>
</dds>
```

```bash
export FASTDDS_DEFAULT_PROFILES_FILE=large_scale_configuration.xml
```

**Always restart `ros2 daemon` after changing discovery env vars / XML**,
otherwise stale participant info from before the switch persists.

---

## Implementing a Custom Memory Allocator
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Advanced/Allocator-Template-Tutorial.html

**What it's for.** Real-time / deterministic-latency nodes — replace the
default heap allocator on publishers, subscribers, executors, and the
intra-process pipeline with a preallocated pool so std-lib growth doesn't
trigger nondeterministic `malloc`.

**Allocator interface.** Custom allocators must satisfy the C++17
allocator interface; easiest approach is deriving from
`std::pmr::memory_resource`:

```cpp
class CustomMemoryResource : public std::pmr::memory_resource {
 private:
  void * do_allocate(std::size_t bytes, std::size_t alignment) override;
  void   do_deallocate(void * p, std::size_t bytes, std::size_t alignment) override;
  bool   do_is_equal(const std::pmr::memory_resource & other) const noexcept override;
};
```

**Aliases used by the tutorial:**

```cpp
using rclcpp::memory_strategies::allocator_memory_strategy::AllocatorMemoryStrategy;
using Alloc = std::pmr::polymorphic_allocator<void>;
using MessageAllocTraits =
    rclcpp::allocator::AllocRebind<std_msgs::msg::UInt32, Alloc>;
using MessageAlloc    = MessageAllocTraits::allocator_type;
using MessageDeleter  = rclcpp::allocator::Deleter<MessageAlloc, std_msgs::msg::UInt32>;
using MessageUniquePtr = std::unique_ptr<std_msgs::msg::UInt32, MessageDeleter>;
```

**Publisher / subscriber with allocator:**

```cpp
CustomMemoryResource mem_resource{};
auto alloc = std::make_shared<Alloc>(&mem_resource);

rclcpp::PublisherOptionsWithAllocator<Alloc> publisher_options;
publisher_options.allocator = alloc;
auto publisher = node->create_publisher<std_msgs::msg::UInt32>(
  "allocator_tutorial", 10, publisher_options);

rclcpp::SubscriptionOptionsWithAllocator<Alloc> subscription_options;
subscription_options.allocator = alloc;
auto msg_mem_strat = std::make_shared<
  rclcpp::message_memory_strategy::MessageMemoryStrategy<
    std_msgs::msg::UInt32, Alloc>>(alloc);
auto subscriber = node->create_subscription<std_msgs::msg::UInt32>(
  "allocator_tutorial", 10, callback, subscription_options, msg_mem_strat);
```

**Executor with allocator:**

```cpp
std::shared_ptr<rclcpp::memory_strategy::MemoryStrategy> memory_strategy =
  std::make_shared<AllocatorMemoryStrategy<Alloc>>(alloc);

rclcpp::ExecutorOptions options;
options.memory_strategy = memory_strategy;
rclcpp::executors::SingleThreadedExecutor executor(options);
```

**Publish loop with custom deleter:**

```cpp
MessageDeleter message_deleter;
MessageAlloc   message_alloc = *alloc;
rclcpp::allocator::set_allocator_for_deleter(&message_deleter, &message_alloc);

uint32_t i = 0;
while (rclcpp::ok()) {
  auto ptr = MessageAllocTraits::allocate(message_alloc, 1);
  MessageAllocTraits::construct(message_alloc, ptr);
  MessageUniquePtr msg(ptr, message_deleter);
  msg->data = i++;
  publisher->publish(std::move(msg));
  rclcpp::sleep_for(10ms);
  executor.spin_some();
}
```

**Intra-process pipeline.** Construct the node with intra-process comms
on, *then* create publishers / subscribers so the IPC manager picks up
the allocator:

```cpp
auto context = rclcpp::contexts::get_global_default_context();
auto options = rclcpp::NodeOptions()
  .context(context)
  .use_intra_process_comms(true);
auto node = rclcpp::Node::make_shared("allocator_example", options);
```

**Run:**

```bash
ros2 run demo_nodes_cpp allocator_tutorial         # default
ros2 run demo_nodes_cpp allocator_tutorial intra   # intra-process variant
```

Output looks like:

```
Global new was called 15590 times during spin
Allocator new was called 27284 times during spin
```

Remaining "global new" calls usually originate inside the DDS layer.

**TLSF allocator.** ROS 2 ships TLSF (Two Level Segregate Fit) — a
real-time allocator — in `tlsf_cpp`:
- https://github.com/ros2/realtime_support/tree/jazzy/tlsf_cpp
- Example: https://github.com/ros2/realtime_support/blob/jazzy/tlsf_cpp/example/allocator_example.cpp
- Dual GPL/LGPL license.

---

## Ament Lint CLI Utilities
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Advanced/Ament-Lint-For-Clean-Code.html

**Tools shipped with ROS Desktop Full:**

C++:
- `ament_cppcheck` — static analysis
- `ament_cpplint` — Google-style checks
- `ament_uncrustify` — style formatter (the only one that auto-fixes)

Python:
- `ament_flake8` — PEP8 / lint
- `ament_pep257` — docstring style

General:
- `ament_copyright` — copyright / license header check
- `ament_lint_cmake` — CMake style
- `ament_xmllint` — XML validation

**Common CLI options** (consistent across all tools):
- `-h, --help`
- `--exclude [files...]`
- `--xunit-file XUNIT_FILE` — produces xUnit XML for CI

**Examples:**

```bash
ament_copyright --verbose
ament_copyright --add-missing "Copyright Holder" apache2

ament_cppcheck ./src
ament_cppcheck --include_dirs ./include

ament_cpplint ./src ./include
ament_flake8

ament_uncrustify --reformat        # the only one that rewrites files
```

**Notes.** `ament_cppcheck` may be skipped on systems with too-old
cppcheck unless `AMENT_CPPCHECK_ALLOW_SLOW_VERSIONS` is set. The
tutorial focuses on CLI usage; for automatic test integration you
typically add `<test_depend>ament_lint_auto</test_depend>` and
`<test_depend>ament_lint_common</test_depend>` to `package.xml` and
call `ament_lint_auto_find_test_dependencies()` in `CMakeLists.txt`
(covered in earlier tutorials, not this one).

---

## Unlocking the Potential of Fast DDS Middleware
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Advanced/FastDDS-Configuration.html

Drives Fast DDS configuration via XML profiles loaded by `rmw_fastrtps_cpp`.

### Selecting the profile

```bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export RMW_FASTRTPS_USE_QOS_FROM_XML=1     # honor publishMode + historyMemoryPolicy from XML
export FASTRTPS_DEFAULT_PROFILES_FILE=/path/to/profile.xml
```

Without `RMW_FASTRTPS_USE_QOS_FROM_XML=1`, rmw_fastrtps overrides the
XML's `publishMode` and `historyMemoryPolicy` with its defaults.

`FASTDDS_DEFAULT_PROFILES_FILE` is the newer-style equivalent name; both
appear in the discovery / large-scale tutorials.

### QoS priority rule

ROS 2 QoS values from `rmw_qos_profile_t` always win **unless** they are
set to `*_SYSTEM_DEFAULT`. Only then does XML / Fast DDS default kick in.

### Profile XML skeleton

```xml
<?xml version="1.0" encoding="UTF-8"?>
<profiles xmlns="http://www.eprosima.com/XMLSchemas/fastRTPS_Profiles">
  <publisher profile_name="default_publisher" is_default_profile="true">
    <historyMemoryPolicy>DYNAMIC</historyMemoryPolicy>
  </publisher>
  <subscriber profile_name="default_subscriber" is_default_profile="true">
    <historyMemoryPolicy>DYNAMIC</historyMemoryPolicy>
  </subscriber>
</profiles>
```

**Always set `historyMemoryPolicy` to `DYNAMIC`.** Fast DDS's default
`PREALLOCATED` doesn't work with ROS 2 message types.

### Naming conventions

- One default profile per endpoint type (`is_default_profile="true"`).
- Topic-specific profiles use the **ROS 2 topic name** as `profile_name`,
  e.g. `/sync_topic`.
- Service / client endpoints use the reserved profile names
  `service` and `client`.

### Publication mode (sync vs async)

```xml
<publisher profile_name="/sync_topic">
  <historyMemoryPolicy>DYNAMIC</historyMemoryPolicy>
  <qos>
    <publishMode><kind>SYNCHRONOUS</kind></publishMode>
  </qos>
</publisher>

<publisher profile_name="/async_topic">
  <historyMemoryPolicy>DYNAMIC</historyMemoryPolicy>
  <qos>
    <publishMode><kind>ASYNCHRONOUS</kind></publishMode>
  </qos>
</publisher>
```

- SYNCHRONOUS: data sent in user thread (lower latency, can block).
- ASYNCHRONOUS: queued and sent on a background thread (user thread
  returns immediately).

### Limit matched subscribers

```xml
<publisher profile_name="/async_topic">
  <historyMemoryPolicy>DYNAMIC</historyMemoryPolicy>
  <matchedSubscribersAllocation>
    <initial>0</initial>
    <maximum>1</maximum>
    <increment>1</increment>
  </matchedSubscribersAllocation>
</publisher>
```

### Partitions (logical isolation within a topic)

```xml
<publisher profile_name="/sync_topic">
  <historyMemoryPolicy>DYNAMIC</historyMemoryPolicy>
  <qos>
    <publishMode><kind>SYNCHRONOUS</kind></publishMode>
    <partition><names><name>part1</name></names></partition>
  </qos>
</publisher>

<subscriber profile_name="/sync_topic">
  <historyMemoryPolicy>DYNAMIC</historyMemoryPolicy>
  <qos>
    <partition><names><name>part2</name></names></partition>
  </qos>
</subscriber>
```

A pub in `part1` and sub in `part2` will **not** match.

### Service / client profile

ROS 2 services use two internal topics: `/rq/<name>` (request) and
`/rr/<name>` (response). The reserved profile names cover all four
endpoints (service pub/sub + client pub/sub):

```xml
<publisher profile_name="service">
  <historyMemoryPolicy>DYNAMIC</historyMemoryPolicy>
  <qos>
    <publishMode><kind>SYNCHRONOUS</kind></publishMode>
  </qos>
</publisher>
<publisher profile_name="client">
  <historyMemoryPolicy>DYNAMIC</historyMemoryPolicy>
  <qos>
    <publishMode><kind>ASYNCHRONOUS</kind></publishMode>
  </qos>
</publisher>
```

### Other tunables (referenced; full schema upstream)

The tutorial flags but does not exhaustively detail: transport selection
(UDP / TCP / SHM shared memory), discovery config (Simple / Server /
Backup), and large-data handling. Full XML reference:
https://fast-dds.docs.eprosima.com/en/latest/fastdds/xml_configuration/xml_configuration.html

---

## Improved Dynamic Discovery
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Advanced/Improved-Dynamic-Discovery.html

Jazzy adds `ROS_AUTOMATIC_DISCOVERY_RANGE` for restricting the discovery
scope without abandoning multicast everywhere.

### `ROS_AUTOMATIC_DISCOVERY_RANGE`

| Value            | Meaning                                              |
|------------------|------------------------------------------------------|
| `SUBNET`         | discover via multicast on local network (default)    |
| `LOCALHOST`      | only nodes on the same machine                       |
| `OFF`            | no automatic discovery, even local                   |
| `SYSTEM_DEFAULT` | leave whatever the underlying middleware does alone  |

### `ROS_STATIC_PEERS`

Semicolon-separated IPs / hostnames to try as peers explicitly. Useful
to bridge across hosts when you've turned off subnet multicast.

### Examples

Linux:

```bash
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export ROS_STATIC_PEERS='192.168.0.1;remote.com'
```

Windows:

```
set ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
set ROS_STATIC_PEERS=192.168.0.1;remote.com
```

### Discovery matrix (summary)

- Same host: nodes match if both are `LOCALHOST` or `SUBNET`,
  regardless of `ROS_STATIC_PEERS`.
- Different hosts: at least one side must be `SUBNET` **or** both
  sides must list each other in `ROS_STATIC_PEERS`.

### Caveats

- Unaffected by `ROS_DOMAIN_ID` segregation rules — those still apply
  on top.
- Not honored by `rmw_zenoh` — use Zenoh's own config there.

---

## Recording a Bag From Your Own Node (C++)
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Advanced/Recording-A-Bag-From-Your-Own-Node-CPP.html

This is the path you want for capturing simulator runs into bags from
inside a recording node (vs `ros2 bag record` external).

### `package.xml`

```xml
<depend>rclcpp</depend>
<depend>rosbag2_cpp</depend>
<depend>std_msgs</depend>
<depend>example_interfaces</depend>
```

### `CMakeLists.txt`

```cmake
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

find_package(rclcpp REQUIRED)
find_package(rosbag2_cpp REQUIRED)
find_package(std_msgs REQUIRED)

add_executable(simple_bag_recorder src/simple_bag_recorder.cpp)
ament_target_dependencies(simple_bag_recorder rclcpp rosbag2_cpp std_msgs)

install(TARGETS simple_bag_recorder DESTINATION lib/${PROJECT_NAME})
```

### Minimal recorder — write serialized messages directly

```cpp
#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/string.hpp>
#include <rosbag2_cpp/writer.hpp>

class SimpleBagRecorder : public rclcpp::Node {
public:
  SimpleBagRecorder() : Node("simple_bag_recorder") {
    writer_ = std::make_unique<rosbag2_cpp::Writer>();
    writer_->open("my_bag");   // default storage backend (mcap)

    auto callback = [this](std::shared_ptr<const rclcpp::SerializedMessage> msg) {
      rclcpp::Time stamp = this->now();
      writer_->write(msg, "chatter", "std_msgs/msg/String", stamp);
    };

    subscription_ = create_subscription<std_msgs::msg::String>(
      "chatter", 10, callback);
  }

private:
  rclcpp::Subscription<std_msgs::msg::String>::SharedPtr subscription_;
  std::unique_ptr<rosbag2_cpp::Writer> writer_;
};

int main(int argc, char * argv[]) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<SimpleBagRecorder>());
  rclcpp::shutdown();
  return 0;
}
```

The serialized callback signature
(`std::shared_ptr<const rclcpp::SerializedMessage>`) hands you the raw
CDR bytes — no copy through a typed message — and `writer_->write(msg,
topic, type, stamp)` writes them straight to disk.

### Variant — synthetic publisher writing typed messages on a timer

```cpp
#include <chrono>
#include <example_interfaces/msg/int32.hpp>
#include <rclcpp/rclcpp.hpp>
#include <rosbag2_cpp/writer.hpp>

using namespace std::chrono_literals;

class DataGenerator : public rclcpp::Node {
public:
  DataGenerator() : Node("data_generator") {
    data_.data = 0;
    writer_ = std::make_unique<rosbag2_cpp::Writer>();
    writer_->open("timed_synthetic_bag");

    writer_->create_topic({
      0u,
      "synthetic",
      "example_interfaces/msg/Int32",
      rmw_get_serialization_format(),
      {},
      "",
    });

    timer_ = create_wall_timer(1s, [this]() { return this->timer_callback(); });
  }

private:
  void timer_callback() {
    writer_->write(data_, "synthetic", now());
    ++data_.data;
  }

  rclcpp::TimerBase::SharedPtr timer_;
  std::unique_ptr<rosbag2_cpp::Writer> writer_;
  example_interfaces::msg::Int32 data_;
};

int main(int argc, char * argv[]) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<DataGenerator>());
  rclcpp::shutdown();
  return 0;
}
```

Writing typed messages via `writer_->write(data, topic, stamp)`
**requires** a prior `writer_->create_topic({...})` registering the
topic name + type + serialization format.

### Build / run

```bash
colcon build --packages-select bag_recorder_nodes
source install/setup.bash

ros2 run bag_recorder_nodes simple_bag_recorder      # in one terminal
ros2 run demo_nodes_cpp talker                       # in another

ros2 bag info my_bag                                  # inspect
ros2 bag play my_bag                                  # replay
```

### Key API summary

- `writer_ = std::make_unique<rosbag2_cpp::Writer>();`
- `writer_->open("bag_name")` — uses default storage (mcap in Jazzy).
- For full control, call the overload taking `rosbag2_storage::StorageOptions`
  (uri, storage_id e.g. `"mcap"` or `"sqlite3"`, max_bagfile_size, etc.)
  and `rosbag2_cpp::ConverterOptions`
  (input_serialization_format, output_serialization_format — usually `"cdr"`).
- `writer_->create_topic({id, name, type, serialization_format, qos_profiles, type_description_hash})`
  registers a typed topic before writing typed messages.
- `writer_->write(serialized_msg, topic, type, stamp)` — write raw CDR.
- `writer_->write(typed_msg, topic, stamp)` — writer serializes for you
  (topic must be created first).

---

## Recording a Bag From Your Own Node (Python)
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Advanced/Recording-A-Bag-From-Your-Own-Node-Py.html

### Imports

```python
import rclpy
from rclpy.node import Node
from rclpy.serialization import serialize_message
from std_msgs.msg import String
import rosbag2_py
```

### Recorder node

```python
class SimpleBagRecorder(Node):
    def __init__(self):
        super().__init__('simple_bag_recorder')

        self.writer = rosbag2_py.SequentialWriter()
        storage_options = rosbag2_py.StorageOptions(
            uri='my_bag',
            storage_id='mcap')                  # 'sqlite3' also valid
        converter_options = rosbag2_py.ConverterOptions('', '')
        self.writer.open(storage_options, converter_options)

        topic_info = rosbag2_py.TopicMetadata(
            id=0,
            name='chatter',
            type='std_msgs/msg/String',
            serialization_format='cdr')
        self.writer.create_topic(topic_info)

        self.subscription = self.create_subscription(
            String,
            'chatter',
            self.topic_callback,
            10)

    def topic_callback(self, msg):
        self.writer.write(
            'chatter',
            serialize_message(msg),
            self.get_clock().now().nanoseconds)


def main(args=None):
    rclpy.init(args=args)
    node = SimpleBagRecorder()
    rclpy.spin(node)
    rclpy.shutdown()
```

### `package.xml`

```xml
<exec_depend>rclpy</exec_depend>
<exec_depend>rosbag2_py</exec_depend>
<exec_depend>std_msgs</exec_depend>
```

### `setup.py`

```python
entry_points={
    'console_scripts': [
        'simple_bag_recorder = bag_recorder_nodes_py.simple_bag_recorder:main',
    ],
},
```

### Build / run / inspect

```bash
colcon build --packages-select bag_recorder_nodes_py
source install/setup.bash

ros2 run bag_recorder_nodes_py simple_bag_recorder
ros2 run demo_nodes_cpp talker

ros2 bag info my_bag
```

### Key API summary

- `rosbag2_py.SequentialWriter()` — single-threaded writer.
- `StorageOptions(uri, storage_id)` — `storage_id` is `'mcap'` (default
  in Jazzy) or `'sqlite3'`.
- `ConverterOptions(input_serialization_format, output_serialization_format)`
  — pass `('','')` to use the storage backend's native format (CDR).
- `writer.open(storage_options, converter_options)`.
- `writer.create_topic(TopicMetadata(id, name, type, serialization_format))`
  must be called once per topic before writing.
- `writer.write(topic, serialize_message(msg), nanoseconds_int)` —
  Python timestamps are nanoseconds since epoch; use
  `self.get_clock().now().nanoseconds`.

---

## Reading From a Bag File (C++)
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Advanced/Reading-From-A-Bag-File-CPP.html

### Package creation

```bash
ros2 pkg create --build-type ament_cmake --license Apache-2.0 \
  bag_reading_cpp --dependencies rclcpp rosbag2_transport turtlesim
```

### Source — `simple_bag_reader.cpp`

```cpp
#include <chrono>
#include <functional>
#include <iostream>
#include <memory>
#include <string>

#include "rclcpp/rclcpp.hpp"
#include "rclcpp/serialization.hpp"
#include "rosbag2_transport/reader_writer_factory.hpp"
#include "turtlesim/msg/pose.hpp"

using namespace std::chrono_literals;

class PlaybackNode : public rclcpp::Node {
public:
  PlaybackNode(const std::string & bag_filename)
  : Node("playback_node") {
    publisher_ = this->create_publisher<turtlesim::msg::Pose>(
      "/turtle1/pose", 10);

    timer_ = this->create_wall_timer(
      100ms, [this]() { return this->timer_callback(); });

    rosbag2_storage::StorageOptions storage_options;
    storage_options.uri = bag_filename;
    reader_ = rosbag2_transport::ReaderWriterFactory::make_reader(storage_options);
    reader_->open(storage_options);
  }

private:
  void timer_callback() {
    while (reader_->has_next()) {
      rosbag2_storage::SerializedBagMessageSharedPtr msg = reader_->read_next();

      if (msg->topic_name != "/turtle1/pose") {
        continue;
      }

      rclcpp::SerializedMessage serialized_msg(*msg->serialized_data);
      turtlesim::msg::Pose::SharedPtr ros_msg =
        std::make_shared<turtlesim::msg::Pose>();

      serialization_.deserialize_message(&serialized_msg, ros_msg.get());

      publisher_->publish(*ros_msg);
      std::cout << '(' << ros_msg->x << ", " << ros_msg->y << ")\n";
      break;
    }
  }

  rclcpp::TimerBase::SharedPtr timer_;
  rclcpp::Publisher<turtlesim::msg::Pose>::SharedPtr publisher_;
  rclcpp::Serialization<turtlesim::msg::Pose> serialization_;
  std::unique_ptr<rosbag2_cpp::Reader> reader_;
};

int main(int argc, char ** argv) {
  if (argc != 2) {
    std::cerr << "Usage: " << argv[0] << " <bag>" << std::endl;
    return 1;
  }
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<PlaybackNode>(argv[1]));
  rclcpp::shutdown();
  return 0;
}
```

### CMakeLists.txt

```cmake
add_executable(simple_bag_reader src/simple_bag_reader.cpp)
ament_target_dependencies(simple_bag_reader rclcpp rosbag2_transport turtlesim)

install(TARGETS simple_bag_reader DESTINATION lib/${PROJECT_NAME})
```

### Build / run

```bash
colcon build --packages-select bag_reading_cpp
source install/setup.bash
ros2 run bag_reading_cpp simple_bag_reader /path/to/bag
```

### Key API summary

- `rosbag2_transport::ReaderWriterFactory::make_reader(storage_options)`
  picks the right reader for the bag's storage backend (mcap / sqlite3).
- `reader_->open(storage_options)` opens the bag.
- `reader_->has_next()` / `reader_->read_next()` — iterate
  `SerializedBagMessageSharedPtr` (fields: `topic_name`,
  `serialized_data`, `time_stamp`).
- `rclcpp::SerializedMessage serialized_msg(*msg->serialized_data);`
  wraps the raw bytes.
- `rclcpp::Serialization<T> serialization_;
   serialization_.deserialize_message(&serialized_msg, ros_msg.get());`
  decodes into a typed message.

---

## Create an rqt_bag Plugin
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Advanced/Create-An-Rqtbag-Plugin.html

**What it's for.** Custom visualizations inside `rqt_bag` for specific
message types — instead of seeing raw YAML, render diagnostics, paint a
custom timeline, etc.

**Plugin pieces:**

- `TopicMessageView` subclass — Qt panel rendering a single message.
- `TimelineRenderer` subclass — paints onto the timeline strip.
- A `Plugin` class declaring view + renderer + supported message types.

**`Plugin` class methods:**

- `get_view_class()` → your `TopicMessageView` subclass
- `get_renderer_class()` → your `TimelineRenderer` subclass
- `get_message_types()` → e.g. `['diagnostic_msgs/msg/DiagnosticStatus']`

**`TopicMessageView` overrides:**

- `__init__()` — build Qt widgets
- `message_viewed(bag, entry, ros_msg, msg_type_name, topic)` — called
  when a message is selected
- `paintEvent()` — custom QPainter draw

**`TimelineRenderer` overrides:**

- `draw_timeline_segment(painter, topic, start_time, end_time, x, y, width, height)`
  — read messages in the time range and paint a custom representation

**Registration — `plugins.xml`:**

```xml
<library path=".">
  <class name="PluginName"
         type="package_name.module_name.ClassName"
         base_class_type="rqt_bag::Plugin">
    <description>Plugin description</description>
  </class>
</library>
```

**`package.xml`:**

```xml
<exec_depend>rqt_bag</exec_depend>
<export>
  <rqt_bag plugin="${prefix}/plugins.xml"/>
</export>
```

`setup.py` must include `plugins.xml` in `data_files`.

**Test:**

```bash
rqt_bag ~/path/to/BagFile
```

Right-click a topic → choose your custom view; enable "Thumbnails" to
see your timeline renderer.

---

## ROS 2 Tracing — Trace and Analyze
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Advanced/ROS2-Tracing-Trace-and-Analyze.html

**Platform.** Linux only (LTTng userspace + kernel tracing). Recommended
on a real-time kernel for accurate latency analysis but works on stock
distros.

### Install

```bash
sudo apt-get update
sudo apt-get install -y babeltrace ros-jazzy-ros2trace tracetools-analysis
```

(LTTng pieces — `lttng-tools`, `liblttng-ust-dev`, `python3-babeltrace`,
`python3-lttng` — are pulled in transitively by `ros-jazzy-ros2trace`.)

Verify ROS 2 was built with tracing instrumentation enabled:

```bash
source /opt/ros/jazzy/setup.bash
ros2 run tracetools status
```

### Trace via the CLI

Start a session (interactive — prints the trace path, lets you press
Enter to begin):

```bash
ros2 trace --session-name perf-test --list
```

- `--session-name <name>` — labels the session and the output dir.
- `--list` — prints the userspace tracepoints that will be enabled
  before starting.
- `--path <dir>` — override the output path
  (default: `~/.ros/tracing/<session-name>`).

Press Enter once to start; press Enter again to stop. The tutorial uses
the interactive form, but `ros2 trace` also supports `start`, `stop`,
`pause`, `resume` subcommands for non-interactive workflows.

### Run the application under trace

In another terminal, while the session is running:

```bash
./install/performance_test/lib/performance_test/perf_test \
  -c rclcpp-single-threaded-executor -p 1 -s 1 -r 0 \
  -m Array1m --reliability RELIABLE --max-runtime 60
```

Any ROS 2 launch / `ros2 run` works the same way. The `tracetools_launch`
package additionally provides a `Trace` launch action so a launch file
can start/stop a session itself.

### Inspect the raw trace

```bash
babeltrace ~/.ros/tracing/perf-test | less
```

Each line is `timestamp event_name { fields }`. (`babeltrace2` is the
modern binary; the tutorial uses `babeltrace` as the install name.)

### Analyze with `tracetools_analysis`

Python API + Jupyter notebooks. Sample notebook covers callback duration
distribution.

```bash
pip3 install bokeh
jupyter notebook ~/path/to/callback_duration.ipynb
```

In the notebook, point at the trace:

```python
path = '~/.ros/tracing/perf-test'
```

Output is interactive Bokeh plots of callback durations etc. — useful
for spotting outliers and bottlenecks per executor / per callback.

---

## Creating an RMW Implementation
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Advanced/Creating-An-RMW-Implementation.html

**RMW = ROS Middleware.** The C abstraction layer below `rcl` that lets
ROS 2 swap pub/sub backends (Fast DDS, Cyclone DDS, Zenoh, custom).

### API surface to implement

A new RMW must provide the C functions declared in the `rmw` package's
headers, including at least:

- **Init / shutdown** — `rmw_init`, `rmw_shutdown`, `rmw_init_options_init`, ...
- **Nodes** — `rmw_create_node`, `rmw_destroy_node`, `rmw_node_get_graph_guard_condition`
- **Pub/Sub** — `rmw_create_publisher`, `rmw_create_subscription`,
  `rmw_publish`, `rmw_take`, `rmw_take_with_info`, ...
- **Services** — `rmw_create_service`, `rmw_create_client`,
  `rmw_take_request`, `rmw_send_response`, `rmw_take_response`, `rmw_send_request`
- **Waitsets** — `rmw_create_wait_set`, `rmw_wait`
- **Graph introspection** — `rmw_get_node_names`,
  `rmw_get_topic_names_and_types`, `rmw_count_publishers`, `rmw_count_subscribers`
- **Identifier** — `rmw_get_implementation_identifier`

Per the tutorial: "The rmw interface includes function-level
documentation, but there is no higher-level documentation on the
features." → read the headers + reference an existing implementation.

### Selecting an implementation at runtime

```bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp     # or rmw_cyclonedds_cpp, rmw_zenoh_cpp, ...
```

The `rmw_implementation` proxy package does the actual `dlopen` /
`dlsym` lookup to pick the requested impl at startup.

### Package structure

Convention: `rmw_<middleware>_cpp`.

```
rmw_myimpl_cpp/
├── package.xml
├── CMakeLists.txt
└── src/
    └── *.cpp
```

### `package.xml` essentials

- `<depend>rmw</depend>`
- Depend on the typesupport packages you'll handle, e.g.
  `rosidl_typesupport_introspection_c`,
  `rosidl_typesupport_introspection_cpp`.
- Group membership so it's discoverable as an RMW:

  ```xml
  <member_of_group>rmw_implementation_packages</member_of_group>
  ```

### `CMakeLists.txt` essentials

```cmake
find_package(rmw REQUIRED)
find_package(rosidl_typesupport_introspection_c REQUIRED)
find_package(rosidl_typesupport_introspection_cpp REQUIRED)

add_library(${PROJECT_NAME} SHARED ${SRCS})
target_link_libraries(${PROJECT_NAME} rmw::rmw)

configure_rmw_library(${PROJECT_NAME})        # sets symbol visibility etc.

register_rmw_implementation(
  "c:rosidl_typesupport_introspection_c"
  "cpp:rosidl_typesupport_introspection_cpp"
)

install(TARGETS ${PROJECT_NAME} ...)
ament_export_libraries(${PROJECT_NAME})
ament_package()
```

`register_rmw_implementation()` writes the ament-index marker that lets
`get_available_rmw_implementations()` find this package and that lets
`RMW_IMPLEMENTATION=<your-package>` actually resolve.

### Building / testing

Build under `colcon` like any other package. The
`test_rmw_implementation` package supplies the CMake helper
`call_for_each_rmw_implementation()` which re-runs a test set against
each available RMW by setting `RMW_IMPLEMENTATION` per invocation.

Implementation-specific test code can branch on the active RMW via
`rmw_get_implementation_identifier()`.
