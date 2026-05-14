# Intermediate Tutorials — Misc (ROS 2 Jazzy)

> Source index: https://docs.ros.org/en/jazzy/Tutorials/Intermediate.html

The Intermediate index links to the following groups (this file covers the
"Main" group only — Launch, tf2, Testing, URDF, and RViz are documented
in their own reference files):

- **Main:** Rosdep, Creating an action, Action server/client (C++ and Python),
  Writing a Composable Node (C++), Composing multiple nodes in a single
  process, Using the Node Interfaces Template Class (C++), Monitoring for
  parameter changes (C++ and Python).
- **Launch subsection:** Creating a launch file, Integrating launch files
  into ROS 2 packages, Using substitutions, Using event handlers, Managing
  large projects.
- **tf2 subsection:** Introducing tf2, static/dynamic broadcasters & listener
  in C++/Python, Adding a frame, Using time, Time travel, Debugging,
  Quaternion fundamentals, Using stamped datatypes with `tf2_ros::MessageFilter`.
- **Testing subsection:** Running tests from CLI, GTest in C++, Python tests,
  `launch_testing` integration tests, Build Farm testing.
- **URDF subsection:** Visual model, Movable model, Physical/collision
  properties, Xacro, robot_state_publisher (C++/Python), Generating URDF.
- **RViz subsection:** RViz user guide, Marker basic shapes, Marker points
  & lines, Marker display types, Custom RViz Display, Custom RViz Panel.

---

## Managing Dependencies with rosdep
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Rosdep.html

`rosdep` is a meta-package manager: it does **not** install software itself,
it identifies dependencies declared in each package's `package.xml` and
delegates installation to the system's native package manager (apt, dnf,
brew, …). Linux and macOS only — Windows is not supported. Can be used on
non-ROS projects when installed standalone.

**`package.xml` dependency tags** (these are the rosdep keys):

| Tag | Purpose |
|-----|---------|
| `<depend>` | Build + runtime (use for C++ when uncertain) |
| `<build_depend>` | Build-time only |
| `<build_export_depend>` | Build deps exported via headers |
| `<exec_depend>` | Runtime only (use for pure Python) |
| `<test_depend>` | Tests only |

**Finding rosdep keys.** For released ROS packages, the package name is the
key (verify in `rosdistro/<distro>/distribution.yaml`). For system libraries
search `rosdep/base.yaml` (system) and `rosdep/python.yaml` (Python) in the
rosdistro repo. A key like `doxygen` resolves to different OS package names
per platform.

**One-time setup:**
```bash
sudo rosdep init
rosdep update
```

**Install all deps for a workspace:**
```bash
cd ~/ros2_ws
rosdep install --from-paths src -y --ignore-src
```
Flags: `--from-paths src` scans for `package.xml` files; `-y` auto-accepts
prompts; `--ignore-src` skips packages already present in the workspace
source tree (so you don't try to apt-install them).

**Gotchas.**
- On Debian/Ubuntu, remove `python3-rosdep2` before installing
  `python3-rosdep` to avoid the conflict.
- If your library isn't in rosdistro: PR it (usually merged within a
  week), fork rosdistro, or maintain a local supplementary keys file.

---

## Creating an action
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Creating-an-Action.html

**Goal.** Define a custom action interface that an action server/client can
later use. Best practice: put interface definitions (`.msg`, `.srv`,
`.action`) in their own dedicated package — never in the same package as
the C++/Python implementation, because mixed-language interface generation
breaks otherwise.

**Create the interface package:**
```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
ros2 pkg create --build-type ament_cmake --license Apache-2.0 \
    custom_action_interfaces
```

**`.action` file format.** Three sections separated by `---` lines:
```
# Goal (request)
---
# Result (final response)
---
# Feedback (intermediate updates)
```

**`custom_action_interfaces/action/Fibonacci.action`:**
```
int32 order
---
int32[] sequence
---
int32[] partial_sequence
```

**`CMakeLists.txt` additions** (before `ament_package()`):
```cmake
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "action/Fibonacci.action"
  DEPENDENCIES action_msgs
)
```

**`package.xml` additions:**
```xml
<buildtool_depend>rosidl_default_generators</buildtool_depend>
<depend>action_msgs</depend>
<member_of_group>rosidl_interface_packages</member_of_group>
```

**Build & verify:**
```bash
cd ~/ros2_ws
colcon build
source install/local_setup.bash
ros2 interface show custom_action_interfaces/action/Fibonacci
```

The action is referenced everywhere downstream as
`custom_action_interfaces/action/Fibonacci`.

---

## Writing an action server and client (C++)
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Writing-an-Action-Server-Client/Cpp.html

Implements server/client for the `Fibonacci` action defined above. Uses
`rclcpp_action` and registers the resulting node as a composable component.

**Create implementation package:**
```bash
ros2 pkg create --dependencies custom_action_interfaces rclcpp \
    rclcpp_action rclcpp_components --license Apache-2.0 \
    -- custom_action_cpp
```

Add `include/custom_action_cpp/visibility_control.h` with the standard
Windows/Linux DLL-export macros (so the shared library can be loaded as a
component on Windows).

### Action server skeleton

```cpp
#include <functional>
#include <memory>
#include <thread>

#include "custom_action_interfaces/action/fibonacci.hpp"
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "rclcpp_components/register_node_macro.hpp"

#include "custom_action_cpp/visibility_control.h"

namespace custom_action_cpp
{
class FibonacciActionServer : public rclcpp::Node
{
public:
  using Fibonacci = custom_action_interfaces::action::Fibonacci;
  using GoalHandleFibonacci = rclcpp_action::ServerGoalHandle<Fibonacci>;

  CUSTOM_ACTION_CPP_PUBLIC
  explicit FibonacciActionServer(
      const rclcpp::NodeOptions & options = rclcpp::NodeOptions())
  : Node("fibonacci_action_server", options)
  {
    using namespace std::placeholders;

    this->action_server_ = rclcpp_action::create_server<Fibonacci>(
      this,
      "fibonacci",
      std::bind(&FibonacciActionServer::handle_goal,    this, _1, _2),
      std::bind(&FibonacciActionServer::handle_cancel,  this, _1),
      std::bind(&FibonacciActionServer::handle_accepted,this, _1));
  }

private:
  rclcpp_action::Server<Fibonacci>::SharedPtr action_server_;

  rclcpp_action::GoalResponse handle_goal(
      const rclcpp_action::GoalUUID & uuid,
      std::shared_ptr<const Fibonacci::Goal> goal)
  {
    RCLCPP_INFO(this->get_logger(),
                "Received goal request with order %d", goal->order);
    (void)uuid;
    return rclcpp_action::GoalResponse::ACCEPT_AND_EXECUTE;
  }

  rclcpp_action::CancelResponse handle_cancel(
      const std::shared_ptr<GoalHandleFibonacci> goal_handle)
  {
    RCLCPP_INFO(this->get_logger(), "Received cancel request");
    (void)goal_handle;
    return rclcpp_action::CancelResponse::ACCEPT;
  }

  void handle_accepted(const std::shared_ptr<GoalHandleFibonacci> goal_handle)
  {
    using namespace std::placeholders;
    // Execute in a new thread so the executor is not blocked.
    std::thread{std::bind(&FibonacciActionServer::execute, this, _1),
                goal_handle}.detach();
  }

  void execute(const std::shared_ptr<GoalHandleFibonacci> goal_handle)
  {
    RCLCPP_INFO(this->get_logger(), "Executing goal");
    rclcpp::Rate loop_rate(1);
    const auto goal = goal_handle->get_goal();
    auto feedback = std::make_shared<Fibonacci::Feedback>();
    auto & sequence = feedback->partial_sequence;
    sequence.push_back(0);
    sequence.push_back(1);
    auto result = std::make_shared<Fibonacci::Result>();

    for (int i = 1; (i < goal->order) && rclcpp::ok(); ++i) {
      if (goal_handle->is_canceling()) {
        result->sequence = sequence;
        goal_handle->canceled(result);
        RCLCPP_INFO(this->get_logger(), "Goal canceled");
        return;
      }
      sequence.push_back(sequence[i] + sequence[i - 1]);
      goal_handle->publish_feedback(feedback);
      RCLCPP_INFO(this->get_logger(), "Publish feedback");
      loop_rate.sleep();
    }

    if (rclcpp::ok()) {
      result->sequence = sequence;
      goal_handle->succeed(result);
      RCLCPP_INFO(this->get_logger(), "Goal succeeded");
    }
  }
};   // class FibonacciActionServer
}    // namespace custom_action_cpp

RCLCPP_COMPONENTS_REGISTER_NODE(custom_action_cpp::FibonacciActionServer)
```

### Action client skeleton

```cpp
#include <functional>
#include <future>
#include <memory>
#include <string>
#include <sstream>

#include "custom_action_interfaces/action/fibonacci.hpp"
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "rclcpp_components/register_node_macro.hpp"

#include "custom_action_cpp/visibility_control.h"

namespace custom_action_cpp
{
class FibonacciActionClient : public rclcpp::Node
{
public:
  using Fibonacci = custom_action_interfaces::action::Fibonacci;
  using GoalHandleFibonacci = rclcpp_action::ClientGoalHandle<Fibonacci>;

  CUSTOM_ACTION_CPP_PUBLIC
  explicit FibonacciActionClient(
      const rclcpp::NodeOptions & options = rclcpp::NodeOptions())
  : Node("fibonacci_action_client", options)
  {
    this->client_ptr_ = rclcpp_action::create_client<Fibonacci>(
      this, "fibonacci");

    this->timer_ = this->create_wall_timer(
      std::chrono::milliseconds(500),
      std::bind(&FibonacciActionClient::send_goal, this));
  }

  void send_goal()
  {
    using namespace std::placeholders;
    this->timer_->cancel();

    if (!this->client_ptr_->wait_for_action_server(std::chrono::seconds(10))) {
      RCLCPP_ERROR(this->get_logger(),
                   "Action server not available after waiting");
      rclcpp::shutdown();
      return;
    }

    auto goal_msg = Fibonacci::Goal();
    goal_msg.order = 10;

    RCLCPP_INFO(this->get_logger(), "Sending goal");

    auto send_goal_options =
        rclcpp_action::Client<Fibonacci>::SendGoalOptions();
    send_goal_options.goal_response_callback =
        std::bind(&FibonacciActionClient::goal_response_callback, this, _1);
    send_goal_options.feedback_callback =
        std::bind(&FibonacciActionClient::feedback_callback, this, _1, _2);
    send_goal_options.result_callback =
        std::bind(&FibonacciActionClient::result_callback, this, _1);

    this->client_ptr_->async_send_goal(goal_msg, send_goal_options);
  }

private:
  rclcpp_action::Client<Fibonacci>::SharedPtr client_ptr_;
  rclcpp::TimerBase::SharedPtr timer_;

  void goal_response_callback(
      const GoalHandleFibonacci::SharedPtr & goal_handle)
  {
    if (!goal_handle) {
      RCLCPP_ERROR(this->get_logger(), "Goal was rejected by server");
    } else {
      RCLCPP_INFO(this->get_logger(),
                  "Goal accepted by server, waiting for result");
    }
  }

  void feedback_callback(
      GoalHandleFibonacci::SharedPtr,
      const std::shared_ptr<const Fibonacci::Feedback> feedback)
  {
    std::stringstream ss;
    ss << "Next number in sequence received: ";
    for (auto number : feedback->partial_sequence) {
      ss << number << " ";
    }
    RCLCPP_INFO(this->get_logger(), ss.str().c_str());
  }

  void result_callback(const GoalHandleFibonacci::WrappedResult & result)
  {
    switch (result.code) {
      case rclcpp_action::ResultCode::SUCCEEDED:                  break;
      case rclcpp_action::ResultCode::ABORTED:
        RCLCPP_ERROR(this->get_logger(), "Goal was aborted");     return;
      case rclcpp_action::ResultCode::CANCELED:
        RCLCPP_ERROR(this->get_logger(), "Goal was canceled");    return;
      default:
        RCLCPP_ERROR(this->get_logger(), "Unknown result code");  return;
    }
    std::stringstream ss;
    ss << "Result received: ";
    for (auto number : result.result->sequence) {
      ss << number << " ";
    }
    RCLCPP_INFO(this->get_logger(), ss.str().c_str());
    rclcpp::shutdown();
  }
};   // class FibonacciActionClient
}    // namespace custom_action_cpp

RCLCPP_COMPONENTS_REGISTER_NODE(custom_action_cpp::FibonacciActionClient)
```

### CMakeLists.txt additions

```cmake
find_package(custom_action_interfaces REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_action REQUIRED)
find_package(rclcpp_components REQUIRED)

add_library(action_server SHARED src/fibonacci_action_server.cpp)
target_include_directories(action_server PRIVATE
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>)
target_compile_definitions(action_server
  PRIVATE "CUSTOM_ACTION_CPP_BUILDING_DLL")
ament_target_dependencies(action_server
  "custom_action_interfaces" "rclcpp" "rclcpp_action" "rclcpp_components")
rclcpp_components_register_node(action_server
  PLUGIN     "custom_action_cpp::FibonacciActionServer"
  EXECUTABLE fibonacci_action_server)
install(TARGETS action_server
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin)

add_library(action_client SHARED src/fibonacci_action_client.cpp)
target_include_directories(action_client PRIVATE
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>)
target_compile_definitions(action_client
  PRIVATE "CUSTOM_ACTION_CPP_BUILDING_DLL")
ament_target_dependencies(action_client
  "custom_action_interfaces" "rclcpp" "rclcpp_action" "rclcpp_components")
rclcpp_components_register_node(action_client
  PLUGIN     "custom_action_cpp::FibonacciActionClient"
  EXECUTABLE fibonacci_action_client)
install(TARGETS action_client
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin)
```

### package.xml depends

```xml
<depend>custom_action_interfaces</depend>
<depend>rclcpp</depend>
<depend>rclcpp_action</depend>
<depend>rclcpp_components</depend>
```

### Run

```bash
cd ~/ros2_ws && colcon build && source install/setup.bash
# Terminal 1
ros2 run custom_action_cpp fibonacci_action_server
# Terminal 2
ros2 run custom_action_cpp fibonacci_action_client
```

The client requests order=10, prints feedback every second, then prints the
final 10-number sequence and shuts down.

**Gotchas.**
- The `execute()` method must run on a separate thread (detached in
  `handle_accepted`) so the executor is not blocked.
- Always check `rclcpp::ok()` and `goal_handle->is_canceling()` inside
  the loop — otherwise the action cannot be cancelled and Ctrl-C will
  abandon a running goal.
- If you forget `RCLCPP_COMPONENTS_REGISTER_NODE`, the executable
  generated by `rclcpp_components_register_node` will link but produce no
  node at runtime.

---

## Writing an action server and client (Python)
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Writing-an-Action-Server-Client/Py.html

Same `Fibonacci` action, in `rclpy`. Put implementation in its own package
(e.g. `action_tutorials_py`) — interfaces stay in
`custom_action_interfaces`.

### Action server skeleton

```python
import time

import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node

from custom_action_interfaces.action import Fibonacci


class FibonacciActionServer(Node):

    def __init__(self):
        super().__init__('fibonacci_action_server')
        self._action_server = ActionServer(
            self,
            Fibonacci,
            'fibonacci',
            self.execute_callback)

    def execute_callback(self, goal_handle):
        self.get_logger().info('Executing goal...')

        feedback_msg = Fibonacci.Feedback()
        feedback_msg.partial_sequence = [0, 1]

        for i in range(1, goal_handle.request.order):
            feedback_msg.partial_sequence.append(
                feedback_msg.partial_sequence[i] +
                feedback_msg.partial_sequence[i - 1])
            self.get_logger().info(
                f'Feedback: {feedback_msg.partial_sequence}')
            goal_handle.publish_feedback(feedback_msg)
            time.sleep(1)

        goal_handle.succeed()

        result = Fibonacci.Result()
        result.sequence = feedback_msg.partial_sequence
        return result


def main(args=None):
    rclpy.init(args=args)
    fibonacci_action_server = FibonacciActionServer()
    rclpy.spin(fibonacci_action_server)


if __name__ == '__main__':
    main()
```

The execute callback **must** call `goal_handle.succeed()` (or `abort()` /
`canceled()`) and **must** return a `Fibonacci.Result()` instance.
`goal_callback`/`cancel_callback` are optional — when omitted the server
accepts every goal and every cancel request.

### Action client skeleton

```python
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from custom_action_interfaces.action import Fibonacci


class FibonacciActionClient(Node):

    def __init__(self):
        super().__init__('fibonacci_action_client')
        self._action_client = ActionClient(self, Fibonacci, 'fibonacci')

    def send_goal(self, order):
        goal_msg = Fibonacci.Goal()
        goal_msg.order = order

        self._action_client.wait_for_server()

        self._send_goal_future = self._action_client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback)

        self._send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info('Goal rejected :(')
            return

        self.get_logger().info('Goal accepted :)')
        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        result = future.result().result
        self.get_logger().info(f'Result: {result.sequence}')
        rclpy.shutdown()

    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        self.get_logger().info(
            f'Received feedback: {feedback.partial_sequence}')


def main(args=None):
    rclpy.init(args=args)
    action_client = FibonacciActionClient()
    action_client.send_goal(10)
    rclpy.spin(action_client)


if __name__ == '__main__':
    main()
```

Note the two chained futures: `send_goal_async` → `goal_response_callback`,
then `get_result_async` → `get_result_callback`. Each future is registered
with `add_done_callback`. `feedback_callback` arrives directly on the
`send_goal_async` call.

### setup.py entry_points

```python
entry_points={
    'console_scripts': [
        'fibonacci_action_server = '
            'action_tutorials_py.fibonacci_action_server:main',
        'fibonacci_action_client = '
            'action_tutorials_py.fibonacci_action_client:main',
    ],
},
```

### package.xml depends

```xml
<depend>rclpy</depend>
<depend>custom_action_interfaces</depend>
```

### Run

```bash
ros2 run action_tutorials_py fibonacci_action_server
ros2 run action_tutorials_py fibonacci_action_client
# or via CLI without writing a client:
ros2 action send_goal --feedback fibonacci \
    custom_action_interfaces/action/Fibonacci "{order: 5}"
```

---

## Writing a Composable Node (C++)
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Writing-a-Composable-Node.html

A composable node is a regular `rclcpp::Node` subclass packaged as a
**shared library** (not an executable) so multiple nodes can be loaded into
the same OS process. The composition machinery is provided by
`rclcpp_components`.

### Class definition

```cpp
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_components/register_node_macro.hpp"

namespace palomino
{
class VincentDriver : public rclcpp::Node
{
public:
  explicit VincentDriver(const rclcpp::NodeOptions & options)
  : Node("vincent_driver", options)
  {
    // pub/sub/timer setup as usual
  }
};
}  // namespace palomino

RCLCPP_COMPONENTS_REGISTER_NODE(palomino::VincentDriver)
```

Two non-negotiable requirements:

1. **Constructor must take `const rclcpp::NodeOptions &`** — the container
   passes namespace, remappings, intra-process flags through it.
2. **No `main()`** — the composition container provides one. Replace
   `main` with the `RCLCPP_COMPONENTS_REGISTER_NODE` macro at file scope
   so pluginlib can discover the class by its fully-qualified name.

### package.xml

```xml
<depend>rclcpp</depend>
<depend>rclcpp_components</depend>
```

### CMakeLists.txt

```cmake
find_package(rclcpp REQUIRED)
find_package(rclcpp_components REQUIRED)

add_library(vincent_driver_component SHARED src/vincent_driver.cpp)
ament_target_dependencies(vincent_driver_component rclcpp rclcpp_components)

# This generates a thin executable that loads the component standalone.
rclcpp_components_register_nodes(vincent_driver_component
    "palomino::VincentDriver")

# Or generate a named executable with PLUGIN/EXECUTABLE form:
rclcpp_components_register_node(
    vincent_driver_component
    PLUGIN     "palomino::VincentDriver"
    EXECUTABLE vincent_driver
)

ament_export_targets(export_vincent_driver_component)
install(TARGETS vincent_driver_component
        EXPORT  export_vincent_driver_component
        ARCHIVE DESTINATION lib
        LIBRARY DESTINATION lib
        RUNTIME DESTINATION bin)
```

`rclcpp_components_register_nodes` (plural) registers the plugin name(s)
with pluginlib so the container can find them. `rclcpp_components_register_node`
(singular, with `PLUGIN`/`EXECUTABLE`) additionally generates a thin
standalone executable that wraps the component in a single-node container.

### Running

```bash
# Run as a standalone (single-component) executable
ros2 run palomino vincent_driver

# Or load into a generic container at runtime
ros2 run rclcpp_components component_container          # terminal A
ros2 component load /ComponentManager palomino \
    palomino::VincentDriver                              # terminal B
```

### Loading via launch

```python
from launch import LaunchDescription
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode

def generate_launch_description():
    return LaunchDescription([
        ComposableNodeContainer(
            name='container_name',
            namespace='',
            package='rclcpp_components',
            executable='component_container',           # or _mt
            composable_node_descriptions=[
                ComposableNode(
                    package='palomino',
                    plugin='palomino::VincentDriver',
                    name='vincent_driver',
                    extra_arguments=[{'use_intra_process_comms': True}],
                ),
            ],
        ),
    ])
```

Use `component_container_mt` when nodes need real concurrency
(multi-threaded executor); otherwise the default single-threaded
`component_container` is fine.

---

## Composing multiple nodes in a single process
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Composition.html

Three ways to compose:

1. **Runtime composition (services).** Start a generic container, load
   components on demand via `ros2 component load`. Useful for debugging
   and for hot-swapping nodes in a running system.
2. **Compile-time composition.** Hand-write a `main()` that constructs
   each node and adds them to one executor. The resulting binary is a
   single executable with all nodes baked in. These nodes do **not**
   appear in `ros2 component list` (no ComponentManager).
3. **Launch-based composition.** Use `ComposableNodeContainer` /
   `ComposableNode` from `launch_ros` (Python or XML) to start the
   container and pre-load components atomically.

### CLI

```bash
ros2 component types                                   # list registered components
ros2 component list                                    # list loaded components
ros2 component load /ComponentManager <pkg> <plugin>   # load
ros2 component unload /ComponentManager <unique_id>    # unload
```

Useful flags for `ros2 component load`:

```bash
# Rename / namespace the loaded node
ros2 component load /ComponentManager composition composition::Talker \
    --node-name talker2 --node-namespace /ns
# Pass parameters
ros2 component load /ComponentManager image_tools image_tools::Cam2Image \
    -p burger_mode:=true
# Pass extra arguments (forward_global_arguments, use_intra_process_comms)
ros2 component load /ComponentManager composition composition::Talker \
    -e use_intra_process_comms:=true
```

### Container variants

| Executable | Behavior |
|------------|----------|
| `component_container` | Single-threaded executor |
| `component_container_mt` | Multi-threaded executor (configurable `thread_num`) |
| `component_container_isolated` | Separate multi-threaded executor per component |

### Manual composition skeleton

```cpp
#include "rclcpp/rclcpp.hpp"
#include "composition/talker_component.hpp"
#include "composition/listener_component.hpp"

int main(int argc, char * argv[])
{
  setvbuf(stdout, NULL, _IONBF, BUFSIZ);
  rclcpp::init(argc, argv);

  rclcpp::executors::SingleThreadedExecutor exec;
  rclcpp::NodeOptions options;

  auto talker   = std::make_shared<composition::Talker>(options);
  auto listener = std::make_shared<composition::Listener>(options);
  exec.add_node(talker);
  exec.add_node(listener);

  exec.spin();

  rclcpp::shutdown();
  return 0;
}
```

### Launch (Python)

```python
from launch import LaunchDescription
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode

def generate_launch_description():
    container = ComposableNodeContainer(
        name='my_container',
        namespace='',
        package='rclcpp_components',
        executable='component_container',
        composable_node_descriptions=[
            ComposableNode(package='composition',
                           plugin='composition::Talker',
                           name='talker'),
            ComposableNode(package='composition',
                           plugin='composition::Listener',
                           name='listener'),
        ],
        output='screen',
    )
    return LaunchDescription([container])
```

### Launch (XML)

```xml
<launch>
  <node_container pkg="rclcpp_components" exec="component_container"
                  name="my_container" namespace="">
    <composable_node pkg="composition" plugin="composition::Talker"
                     name="talker"/>
    <composable_node pkg="composition" plugin="composition::Listener"
                     name="listener"/>
  </node_container>
</launch>
```

**Gotchas.**
- Manual-composition nodes are invisible to `ros2 component list` — there
  is no ComponentManager service to query.
- Remapping the **container's** name/namespace does NOT propagate to the
  loaded components. Remap each component individually.
- A non-Node-derived component class must define a constructor taking
  `rclcpp::NodeOptions` and implement `get_node_base_interface()` so the
  container can add it to its executor.

---

## Using the Node Interfaces Template Class (C++)
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Using-Node-Interfaces-Template-Class.html

`rclcpp::Node` and `rclcpp_lifecycle::LifecycleNode` deliberately do
**not** share an inheritance tree. Functions written against
`SharedPtr<rclcpp::Node>` therefore cannot accept a `LifecycleNode`. Two
historical workarounds — pass several individual interface pointers, or
template the function on the node type — are clumsy. `NodeInterfaces<...>`
solves this with a single, type-safe handle that can be implicitly built
from either node kind.

### Template syntax

```cpp
#include "rclcpp/rclcpp.hpp"
#include "rclcpp/node_interfaces/node_interfaces.hpp"

using rclcpp::node_interfaces::NodeInterfaces;
using rclcpp::node_interfaces::NodeBaseInterface;
using rclcpp::node_interfaces::NodeLoggingInterface;

using MyNodeInterfaces = NodeInterfaces<
  NodeBaseInterface,
  NodeLoggingInterface
>;
```

Common interfaces: `NodeBaseInterface`, `NodeClockInterface`,
`NodeLoggingInterface`, `NodeTopicsInterface`, `NodeServicesInterface`,
`NodeTimersInterface`, `NodeParametersInterface`, `NodeWaitablesInterface`,
`NodeGraphInterface`, `NodeTimeSourceInterface`.

### Function accepting NodeInterfaces

```cpp
void node_info(MyNodeInterfaces interfaces)
{
  auto base    = interfaces.get<NodeBaseInterface>();
  // (equivalent shorthand)
  auto logging = interfaces.get_node_logging_interface();

  RCLCPP_INFO(logging->get_logger(),
              "Node name: %s", base->get_name());
}
```

### Caller side — works for both node kinds

```cpp
auto node    = std::make_shared<SimpleNode>("Simple_Node");
auto lc_node = std::make_shared<LifecycleTalker>("Simple_LifeCycle_Node");

node_info(*node);     // standard rclcpp::Node
node_info(*lc_node);  // rclcpp_lifecycle::LifecycleNode
```

The `*node` dereference is required — `NodeInterfaces` is constructed from
a node reference, not a `SharedPtr`.

### Why bother

- **Decoupling for tests.** Functions depend on capability interfaces
  (logger, clock, topics) instead of a concrete node, making it
  straightforward to substitute mocks.
- **Composition.** The same helper works against ordinary nodes, lifecycle
  nodes, and any future node variants that satisfy the requested
  interfaces — no template explosion in the call sites.
- **Compactness.** One parameter replaces several interface pointers.

---

## Monitoring for parameter changes (C++)
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Monitoring-For-Parameter-Changes-CPP.html

`rclcpp::ParameterEventHandler` lets a node react **after** a parameter
has changed (its own, or another node's). For pre-change validation use
`add_on_set_parameters_callback` instead — they solve different problems.

### Setup in the node

```cpp
#include "rclcpp/rclcpp.hpp"

class SampleNodeWithParameters : public rclcpp::Node
{
public:
  SampleNodeWithParameters() : Node("node_with_parameters")
  {
    this->declare_parameter("an_int_param", 0);

    // Subscriber owns the lifetime of all callbacks.
    param_subscriber_ = std::make_shared<rclcpp::ParameterEventHandler>(this);

    // Local-parameter callback.
    auto cb = [this](const rclcpp::Parameter & p) {
      RCLCPP_INFO(this->get_logger(),
        "cb: Received an update to parameter \"%s\" of type %s: \"%ld\"",
        p.get_name().c_str(),
        p.get_type_name().c_str(),
        p.as_int());
    };
    cb_handle_ = param_subscriber_->add_parameter_callback("an_int_param", cb);
  }

private:
  std::shared_ptr<rclcpp::ParameterEventHandler> param_subscriber_;
  std::shared_ptr<rclcpp::ParameterCallbackHandle> cb_handle_;
};
```

**Critical:** keep the returned `ParameterCallbackHandle` (or
`ParameterEventCallbackHandle`) alive as a member. When it goes out of
scope the callback is silently unregistered.

### Monitoring a remote node's parameter

```cpp
cb_handle2_ = param_subscriber_->add_parameter_callback(
    "param_name", cb, "remote_node_name");
```

### Monitoring all parameter events

```cpp
auto event_cb = [this](const rcl_interfaces::msg::ParameterEvent & event) {
  RCLCPP_INFO(this->get_logger(),
              "Event from node \"%s\"", event.node.c_str());
  for (const auto & p : event.changed_parameters) {
    RCLCPP_INFO(this->get_logger(),
                "\"%s\" changed", p.name.c_str());
  }
};
event_handle_ = param_subscriber_->add_parameter_event_callback(event_cb);
```

`rcl_interfaces::msg::ParameterEvent` carries `new_parameters`,
`changed_parameters`, `deleted_parameters`, and the originating `node`
field.

### Build configuration

```cmake
add_executable(parameter_event_handler src/parameter_event_handler.cpp)
ament_target_dependencies(parameter_event_handler rclcpp)
install(TARGETS parameter_event_handler
        DESTINATION lib/${PROJECT_NAME})
```

```xml
<depend>rclcpp</depend>
```

### vs. add_on_set_parameters_callback

| Feature | `add_on_set_parameters_callback` | `ParameterEventHandler` |
|---------|----------------------------------|-------------------------|
| Fires | Before the change is applied | After the change is applied |
| Can reject | Yes (return `successful=false`) | No |
| Watches other nodes | No (own node only) | Yes (per-parameter or global event) |
| Use case | Validation / coupled-parameter constraints | Reactive logic, dashboards, observers |

---

## Monitoring for parameter changes (Python)
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Monitoring-For-Parameter-Changes-Python.html

Python equivalent. Lives in `rclpy.parameter_event_handler`.

### Minimal node

```python
import rclpy
from rclpy.node import Node
import rclpy.parameter
from rclpy.parameter_event_handler import ParameterEventHandler


class SampleNodeWithParameters(Node):
    def __init__(self):
        super().__init__('node_with_parameters')
        self.declare_parameter('an_int_param', 0)

        # The event handler must outlive any callback it registers.
        self.handler = ParameterEventHandler(self)

        # Per-parameter callback. KEEP the returned handle as an
        # attribute; otherwise the callback is silently dropped.
        self.callback_handle = self.handler.add_parameter_callback(
            parameter_name='an_int_param',
            node_name='node_with_parameters',
            callback=self.callback,
        )

    def callback(self, p: rclpy.parameter.Parameter) -> None:
        value = rclpy.parameter.parameter_value_to_python(p.value)
        self.get_logger().info(
            f'Received update: {p.name}: {value}')


def main(args=None):
    rclpy.init(args=args)
    node = SampleNodeWithParameters()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### Global parameter-event callback

```python
self.event_handle = self.handler.add_parameter_event_callback(
    callback=self.event_callback,
)

def event_callback(self, parameter_event):
    self.get_logger().info(f'Event from {parameter_event.node}')
    for p in parameter_event.changed_parameters:
        value = rclpy.parameter.parameter_value_to_python(p.value)
        self.get_logger().info(f'{p.name} -> {value}')
```

The event-callback message is `rcl_interfaces.msg.ParameterEvent`
(`new_parameters`, `changed_parameters`, `deleted_parameters`, `node`).

### Package configuration

`setup.py`:
```python
entry_points={
    'console_scripts': [
        'node_with_parameters = '
            'python_parameter_event_handler.parameter_event_handler:main',
    ],
},
```

`package.xml`:
```xml
<depend>rclpy</depend>
```

### Test

```bash
ros2 run python_parameter_event_handler node_with_parameters
# in another terminal:
ros2 param set node_with_parameters an_int_param 43
```

The callback fires immediately and logs the new value. Same gotchas as the
C++ version: keep the returned handle alive, and remember this fires
**after** the change — use `add_on_set_parameters_callback` (or, in
modern Python, `add_pre_set_parameters_callback`) for validation.
