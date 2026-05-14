# Beginner: Client Libraries (ROS 2 Jazzy Tutorials)

> Source index: https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries.html

This section covers everything needed to write your own ROS 2 nodes in C++ and Python: workspace setup, the colcon build tool, package creation, publisher/subscriber and service/client patterns, custom interface generation, parameters, diagnostics, and pluginlib for loadable C++ classes.

The 13 tutorials in order:

1. Using `colcon` to build packages
2. Creating a workspace
3. Creating a package
4. Writing a simple publisher and subscriber (C++)
5. Writing a simple publisher and subscriber (Python)
6. Writing a simple service and client (C++)
7. Writing a simple service and client (Python)
8. Creating custom msg and srv files
9. Implementing custom interfaces (single package defines and uses)
10. Using parameters in a class (C++)
11. Using parameters in a class (Python)
12. Using `ros2doctor` to identify issues
13. Creating and using plugins (C++) — pluginlib

---

## Using `colcon` to build packages
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Colcon-Tutorial.html

`colcon` is the iteration on `catkin_make`, `catkin_make_isolated`, `catkin_tools` and `ament_tools`. It's the standard build tool for ROS 2 workspaces.

### Install

```bash
# Ubuntu / Debian
sudo apt install python3-colcon-common-extensions

# macOS / Windows
python3 -m pip install colcon-common-extensions
```

### Workspace layout produced

```
ros2_ws/
├── src/      # source code (you write/clone here)
├── build/    # intermediate build artefacts (created by colcon)
├── install/  # compiled packages, setup scripts (created by colcon)
└── log/      # build logs
```

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws
```

### Build commands

```bash
# Standard Linux/macOS build (Python edits picked up without rebuild)
colcon build --symlink-install

# Windows: avoid path-length issues
colcon build --merge-install
```

Useful flags:

- `--packages-select <PKG>` — build only specific packages
- `--packages-up-to <PKG>` — build a package and all of its dependencies
- `--event-handlers console_direct+` — stream build output live to the console
- `--cmake-args -DBUILD_TESTING=0` — skip test configuration in CMake
- `--executor sequential` — build one package at a time (low-RAM machines, e.g. Pi)

### Source the environment

```bash
# Linux/macOS — covers the package and its dependencies
source install/setup.bash

# Local-only variant: configures THIS workspace's packages only,
# leaves dependency setup alone. Use when you've already sourced an underlay.
source install/local_setup.bash

# Windows
call install\setup.bat
install\setup.ps1   # PowerShell
```

`install/setup` vs `install/local_setup`: the former applies the entire dependency chain; the latter applies only this overlay's packages. When you've already sourced `/opt/ros/jazzy/setup.bash` as the underlay, prefer `local_setup.bash` for the overlay.

### Tests

```bash
colcon test
colcon test --packages-select <PKG> --ctest-args -R <TEST_NAME>
```

### Underlay vs overlay

The **underlay** is your existing ROS 2 install (e.g. `/opt/ros/jazzy`). Your workspace becomes an **overlay** layered on top — its `install/` is prepended to `AMENT_PREFIX_PATH`/`PATH`, so packages in the overlay shadow the underlay versions. Always source the underlay before building the overlay.

### Misc

- Place an empty `COLCON_IGNORE` file inside any package directory to skip it.
- Quick navigation: `colcon_cd <pkg>`.
- Mixins for canned arg sets:
  ```bash
  colcon mixin add default https://raw.githubusercontent.com/colcon/colcon-mixin-repository/master/index.yaml
  colcon mixin update default
  colcon build --mixin debug
  ```

### Common errors

- "Command 'colcon' not found" → `apt install python3-colcon-common-extensions` was missed.
- Long path errors on Windows → use `--merge-install`.
- Stale Python edits not reflected → rebuild without `--symlink-install` or simply re-source.

---

## Creating a workspace
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Creating-A-Workspace/Creating-A-Workspace.html

Walks through making a workspace as an overlay over your installed ROS 2.

### Steps

```bash
# 1. Source the underlay
source /opt/ros/jazzy/setup.bash    # Linux
# . ~/ros2_install/ros2-osx/setup.bash   # macOS
# call C:\dev\ros2\local_setup.bat       # Windows

# 2. Create workspace structure
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src

# 3. Clone an example repo to have something to build
git clone https://github.com/ros/ros_tutorials.git -b jazzy

# 4. Resolve dependencies (Linux only)
cd ~/ros2_ws
rosdep install -i --from-path src --rosdistro jazzy -y

# 5. Build the overlay
colcon build --symlink-install
# Windows: colcon build --merge-install

# 6. In a NEW terminal, source underlay then overlay
source /opt/ros/jazzy/setup.bash
cd ~/ros2_ws
source install/local_setup.bash

# 7. Verify by running an overlay node
ros2 run turtlesim turtlesim_node
```

### Key concepts

- The overlay's environment entries are **prepended** to `PATH`/`AMENT_PREFIX_PATH`, so the same-named package in the overlay takes precedence.
- Modify code in `src/`, then `colcon build` (or just re-`source install/local_setup.bash` if you used `--symlink-install` for Python).
- `rosdep` doesn't run on macOS/Windows; install dependencies manually there.

---

## Creating a package
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Creating-Your-First-ROS2-Package.html

A **package** is the unit of organisation for ROS 2 code (compilable, installable, shareable). ROS 2 packages use the `ament` build system; you compile them with `colcon`. Two flavours: `ament_cmake` (C/C++) and `ament_python` (pure Python).

### Required layout

**ament_cmake (C++)**:
```
my_package/
├── CMakeLists.txt
├── include/my_package/
├── package.xml
└── src/
```

**ament_python**:
```
my_package/
├── package.xml
├── resource/my_package        # marker file
├── setup.cfg
├── setup.py
└── my_package/
    └── __init__.py
```

A workspace can mix both build types in `src/`. Don't nest packages.

### Create commands

```bash
cd ~/ros2_ws/src

# C++
ros2 pkg create --build-type ament_cmake --license Apache-2.0 \
    --node-name my_node my_package

# Python
ros2 pkg create --build-type ament_python --license Apache-2.0 \
    --node-name my_node my_package
```

Flag reference:

- `--build-type ament_cmake | ament_python`
- `--license Apache-2.0` (or `BSD-3-Clause`, `MIT`, …)
- `--node-name <name>` — also generates a hello-world executable
- `--dependencies rclcpp std_msgs ...` — pre-fill `package.xml` deps
- `--library-name <name>` — generate a library skeleton (used by pluginlib)

### Build & run

```bash
cd ~/ros2_ws
colcon build                              # everything
colcon build --packages-select my_package # just this one
# Windows: append --merge-install

# new terminal
source install/local_setup.bash           # or call install/local_setup.bat
ros2 run my_package my_node
```

### `package.xml` essentials

```xml
<name>my_package</name>
<version>0.0.0</version>
<description>Beginner client libraries tutorials practice package</description>
<maintainer email="user@example.com">Your Name</maintainer>
<license>Apache-2.0</license>
```

Replace the `TODO` defaults before releasing. Dependencies sit below the license tag using `*_depend` tags (`buildtool_depend`, `depend`, `exec_depend`, `test_depend`).

### Python `setup.py` matching

For Python packages, `setup.py` must mirror `package.xml` for `name`, `version`, `maintainer`, `maintainer_email`, `description`, `license`.

---

## Writing a simple publisher and subscriber (C++)
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Cpp-Publisher-And-Subscriber.html

Builds two nodes (`talker`, `listener`) in a `cpp_pubsub` package that exchange `std_msgs/msg/String` over the topic `topic`.

### Create the package

```bash
cd ~/ros2_ws/src
ros2 pkg create --build-type ament_cmake --license Apache-2.0 \
    --dependencies rclcpp std_msgs cpp_pubsub
```

### `src/publisher_lambda_function.cpp`

```cpp
#include <chrono>
#include <memory>
#include <string>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

using namespace std::chrono_literals;

class MinimalPublisher : public rclcpp::Node
{
public:
  MinimalPublisher()
  : Node("minimal_publisher"), count_(0)
  {
    publisher_ = this->create_publisher<std_msgs::msg::String>("topic", 10);
    auto timer_callback =
      [this]() -> void {
        auto message = std_msgs::msg::String();
        message.data = "Hello, world! " + std::to_string(this->count_++);
        RCLCPP_INFO(this->get_logger(), "Publishing: '%s'", message.data.c_str());
        this->publisher_->publish(message);
      };
    timer_ = this->create_wall_timer(500ms, timer_callback);
  }

private:
  rclcpp::TimerBase::SharedPtr timer_;
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr publisher_;
  size_t count_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<MinimalPublisher>());
  rclcpp::shutdown();
  return 0;
}
```

### `src/subscriber_lambda_function.cpp`

```cpp
#include <memory>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

class MinimalSubscriber : public rclcpp::Node
{
public:
  MinimalSubscriber()
  : Node("minimal_subscriber")
  {
    auto topic_callback =
      [this](std_msgs::msg::String::UniquePtr msg) -> void {
        RCLCPP_INFO(this->get_logger(), "I heard: '%s'", msg->data.c_str());
      };
    subscription_ =
      this->create_subscription<std_msgs::msg::String>("topic", 10, topic_callback);
  }

private:
  rclcpp::Subscription<std_msgs::msg::String>::SharedPtr subscription_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<MinimalSubscriber>());
  rclcpp::shutdown();
  return 0;
}
```

### `package.xml`

```xml
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>cpp_pubsub</name>
  <version>0.0.0</version>
  <description>Examples of minimal publisher/subscriber using rclcpp</description>
  <maintainer email="you@email.com">Your Name</maintainer>
  <license>Apache-2.0</license>

  <buildtool_depend>ament_cmake</buildtool_depend>
  <depend>rclcpp</depend>
  <depend>std_msgs</depend>

  <export>
    <build_type>ament_cmake</build_type>
  </export>
</package>
```

### `CMakeLists.txt`

```cmake
cmake_minimum_required(VERSION 3.5)
project(cpp_pubsub)

# Default to C++14
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)

add_executable(talker src/publisher_lambda_function.cpp)
ament_target_dependencies(talker rclcpp std_msgs)

add_executable(listener src/subscriber_lambda_function.cpp)
ament_target_dependencies(listener rclcpp std_msgs)

install(TARGETS
  talker
  listener
  DESTINATION lib/${PROJECT_NAME})

ament_package()
```

### Build & run

```bash
cd ~/ros2_ws
rosdep install -i --from-path src --rosdistro jazzy -y
colcon build --packages-select cpp_pubsub
. install/setup.bash

# terminal 1
ros2 run cpp_pubsub talker

# terminal 2
ros2 run cpp_pubsub listener
```

Topic name AND message type must match between publisher and subscriber.

### Common errors

- "package 'rclcpp' not found" → forgot `find_package(rclcpp REQUIRED)` or `<depend>rclcpp</depend>`.
- Executable not found by `ros2 run` → missing `install(TARGETS ... DESTINATION lib/${PROJECT_NAME})`.
- Stale build → delete `build/ install/ log/` and rebuild.

---

## Writing a simple publisher and subscriber (Python)
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Py-Publisher-And-Subscriber.html

Same scenario as C++, in `py_pubsub`.

### Create the package

```bash
cd ~/ros2_ws/src
ros2 pkg create --build-type ament_python --license Apache-2.0 \
    --dependencies rclpy std_msgs py_pubsub
```

### `py_pubsub/publisher_member_function.py`

```python
import rclpy
from rclpy.node import Node

from std_msgs.msg import String


class MinimalPublisher(Node):

    def __init__(self):
        super().__init__('minimal_publisher')
        self.publisher_ = self.create_publisher(String, 'topic', 10)
        timer_period = 0.5  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.i = 0

    def timer_callback(self):
        msg = String()
        msg.data = 'Hello World: %d' % self.i
        self.publisher_.publish(msg)
        self.get_logger().info('Publishing: "%s"' % msg.data)
        self.i += 1


def main(args=None):
    rclpy.init(args=args)

    minimal_publisher = MinimalPublisher()

    rclpy.spin(minimal_publisher)

    minimal_publisher.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### `py_pubsub/subscriber_member_function.py`

```python
import rclpy
from rclpy.node import Node

from std_msgs.msg import String


class MinimalSubscriber(Node):

    def __init__(self):
        super().__init__('minimal_subscriber')
        self.subscription = self.create_subscription(
            String,
            'topic',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning

    def listener_callback(self, msg):
        self.get_logger().info('I heard: "%s"' % msg.data)


def main(args=None):
    rclpy.init(args=args)

    minimal_subscriber = MinimalSubscriber()

    rclpy.spin(minimal_subscriber)

    minimal_subscriber.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### `package.xml`

```xml
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>py_pubsub</name>
  <version>0.0.0</version>
  <description>Examples of minimal publisher/subscriber using rclpy</description>
  <maintainer email="you@email.com">Your Name</maintainer>
  <license>Apache-2.0</license>

  <test_depend>ament_copyright</test_depend>
  <test_depend>ament_flake8</test_depend>
  <test_depend>ament_pep257</test_depend>
  <test_depend>python3-pytest</test_depend>

  <exec_depend>rclpy</exec_depend>
  <exec_depend>std_msgs</exec_depend>
</package>
```

### `setup.py`

```python
from setuptools import setup

package_name = 'py_pubsub'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='YourName',
    maintainer_email='you@email.com',
    description='Examples of minimal publisher/subscriber using rclpy',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'talker = py_pubsub.publisher_member_function:main',
            'listener = py_pubsub.subscriber_member_function:main',
        ],
    },
)
```

### `setup.cfg`

```ini
[develop]
script_dir=$base/lib/py_pubsub
[install]
install_scripts=$base/lib/py_pubsub
```

### Build & run

```bash
cd ~/ros2_ws
rosdep install -i --from-path src --rosdistro jazzy -y
colcon build --packages-select py_pubsub
source install/setup.bash

ros2 run py_pubsub talker
ros2 run py_pubsub listener
```

### Common errors

- `ros2 run` can't find script → forgot to add an entry in `entry_points={'console_scripts': [...]}` OR forgot to rebuild.
- "ModuleNotFoundError: py_pubsub" → file isn't inside the `py_pubsub/` python package directory, or `__init__.py` is missing.
- Edits not reflected → use `colcon build --symlink-install` so Python file edits are picked up without rebuild.

---

## Writing a simple service and client (C++)
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Cpp-Service-And-Client.html

Builds `add_two_ints_server` and `add_two_ints_client` using `example_interfaces/srv/AddTwoInts`.

### Create the package

```bash
cd ~/ros2_ws/src
ros2 pkg create --build-type ament_cmake --license Apache-2.0 \
    --dependencies rclcpp example_interfaces cpp_srvcli
```

### `src/add_two_ints_server.cpp`

```cpp
#include "rclcpp/rclcpp.hpp"
#include "example_interfaces/srv/add_two_ints.hpp"

#include <memory>

void add(const std::shared_ptr<example_interfaces::srv::AddTwoInts::Request> request,
          std::shared_ptr<example_interfaces::srv::AddTwoInts::Response>      response)
{
  response->sum = request->a + request->b;
  RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Incoming request\na: %ld" " b: %ld",
                request->a, request->b);
  RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "sending back response: [%ld]", (long int)response->sum);
}

int main(int argc, char **argv)
{
  rclcpp::init(argc, argv);

  std::shared_ptr<rclcpp::Node> node = rclcpp::Node::make_shared("add_two_ints_server");

  rclcpp::Service<example_interfaces::srv::AddTwoInts>::SharedPtr service =
    node->create_service<example_interfaces::srv::AddTwoInts>("add_two_ints", &add);

  RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Ready to add two ints.");

  rclcpp::spin(node);
  rclcpp::shutdown();
}
```

### `src/add_two_ints_client.cpp`

```cpp
#include "rclcpp/rclcpp.hpp"
#include "example_interfaces/srv/add_two_ints.hpp"

#include <chrono>
#include <cstdlib>
#include <memory>

using namespace std::chrono_literals;

int main(int argc, char **argv)
{
  rclcpp::init(argc, argv);

  if (argc != 3) {
      RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "usage: add_two_ints_client X Y");
      return 1;
  }

  std::shared_ptr<rclcpp::Node> node = rclcpp::Node::make_shared("add_two_ints_client");
  rclcpp::Client<example_interfaces::srv::AddTwoInts>::SharedPtr client =
    node->create_client<example_interfaces::srv::AddTwoInts>("add_two_ints");

  auto request = std::make_shared<example_interfaces::srv::AddTwoInts::Request>();
  request->a = atoll(argv[1]);
  request->b = atoll(argv[2]);

  while (!client->wait_for_service(1s)) {
    if (!rclcpp::ok()) {
      RCLCPP_ERROR(rclcpp::get_logger("rclcpp"), "Interrupted while waiting for the service. Exiting.");
      return 0;
    }
    RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "service not available, waiting again...");
  }

  auto result = client->async_send_request(request);
  // Wait for the result.
  if (rclcpp::spin_until_future_complete(node, result) ==
    rclcpp::FutureReturnCode::SUCCESS)
  {
    RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Sum: %ld", result.get()->sum);
  } else {
    RCLCPP_ERROR(rclcpp::get_logger("rclcpp"), "Failed to call service add_two_ints");
  }

  rclcpp::shutdown();
  return 0;
}
```

### `package.xml`

```xml
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>cpp_srvcli</name>
  <version>0.0.0</version>
  <description>C++ client server tutorial</description>
  <maintainer email="you@email.com">Your Name</maintainer>
  <license>Apache-2.0</license>

  <buildtool_depend>ament_cmake</buildtool_depend>

  <depend>rclcpp</depend>
  <depend>example_interfaces</depend>
</package>
```

### `CMakeLists.txt`

```cmake
cmake_minimum_required(VERSION 3.5)
project(cpp_srvcli)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(example_interfaces REQUIRED)

add_executable(server src/add_two_ints_server.cpp)
ament_target_dependencies(server rclcpp example_interfaces)

add_executable(client src/add_two_ints_client.cpp)
ament_target_dependencies(client rclcpp example_interfaces)

install(TARGETS
  server
  client
  DESTINATION lib/${PROJECT_NAME})

ament_package()
```

### Build & run

```bash
cd ~/ros2_ws
colcon build --packages-select cpp_srvcli
source install/setup.bash

# terminal 1
ros2 run cpp_srvcli server

# terminal 2
ros2 run cpp_srvcli client 2 3
# -> Sum: 5
```

### Common errors

- "Failed to call service add_two_ints" → the server isn't running, or service names don't match.
- Hang on `wait_for_service` → mismatched namespace, or wrong service type.
- Header not found `example_interfaces/srv/add_two_ints.hpp` → forgot `find_package(example_interfaces REQUIRED)` and `<depend>example_interfaces</depend>`.

---

## Writing a simple service and client (Python)
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Py-Service-And-Client.html

Same `AddTwoInts` example, in `py_srvcli`.

### Create the package

```bash
cd ~/ros2_ws/src
ros2 pkg create --build-type ament_python --license Apache-2.0 \
    --dependencies rclpy example_interfaces py_srvcli
```

### `py_srvcli/service_member_function.py`

```python
from example_interfaces.srv import AddTwoInts

import rclpy
from rclpy.node import Node


class MinimalService(Node):

    def __init__(self):
        super().__init__('minimal_service')
        self.srv = self.create_service(AddTwoInts, 'add_two_ints', self.add_two_ints_callback)

    def add_two_ints_callback(self, request, response):
        response.sum = request.a + request.b
        self.get_logger().info('Incoming request\na: %d b: %d' % (request.a, request.b))

        return response


def main():
    rclpy.init()

    minimal_service = MinimalService()

    rclpy.spin(minimal_service)

    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### `py_srvcli/client_member_function.py`

```python
import sys

from example_interfaces.srv import AddTwoInts
import rclpy
from rclpy.node import Node


class MinimalClientAsync(Node):

    def __init__(self):
        super().__init__('minimal_client_async')
        self.cli = self.create_client(AddTwoInts, 'add_two_ints')
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('service not available, waiting again...')
        self.req = AddTwoInts.Request()

    def send_request(self, a, b):
        self.req.a = a
        self.req.b = b
        return self.cli.call_async(self.req)


def main():
    rclpy.init()

    minimal_client = MinimalClientAsync()
    future = minimal_client.send_request(int(sys.argv[1]), int(sys.argv[2]))
    rclpy.spin_until_future_complete(minimal_client, future)
    response = future.result()
    minimal_client.get_logger().info(
        'Result of add_two_ints: for %d + %d = %d' %
        (int(sys.argv[1]), int(sys.argv[2]), response.sum))

    minimal_client.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### `package.xml`

```xml
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>py_srvcli</name>
  <version>0.0.0</version>
  <description>Python client server tutorial</description>
  <maintainer email="you@email.com">Your Name</maintainer>
  <license>Apache-2.0</license>

  <depend>rclpy</depend>
  <depend>example_interfaces</depend>

  <test_depend>ament_copyright</test_depend>
  <test_depend>ament_flake8</test_depend>
  <test_depend>ament_pep257</test_depend>
  <test_depend>python3-pytest</test_depend>

  <export>
    <build_type>ament_python</build_type>
  </export>
</package>
```

### `setup.py`

```python
from setuptools import setup

package_name = 'py_srvcli'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='you@email.com',
    description='Python client server tutorial',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'service = py_srvcli.service_member_function:main',
            'client = py_srvcli.client_member_function:main',
        ],
    },
)
```

### Build & run

```bash
cd ~/ros2_ws
colcon build --packages-select py_srvcli
source install/setup.bash

ros2 run py_srvcli service
ros2 run py_srvcli client 2 3
# -> Result of add_two_ints: for 2 + 3 = 5
```

### Common errors

- `IndexError: list index out of range` → forgot to pass arguments after `client`.
- `TypeError: response.sum` assignment → set the field on the **passed-in** response object and `return response`.
- Service timeout loop forever → server not running or topic-name mismatch (services share namespace rules with topics).

---

## Creating custom msg and srv files
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Custom-ROS2-Interfaces.html

Defines new `.msg` and `.srv` types in their own `tutorial_interfaces` package, then generates language bindings via `rosidl_generate_interfaces`.

### Create package and dirs

```bash
cd ~/ros2_ws/src
ros2 pkg create --build-type ament_cmake --license Apache-2.0 tutorial_interfaces
cd tutorial_interfaces
mkdir msg srv
```

Custom interfaces should currently be defined in a `CMake` package even if the consumers are Python — `ament_python` packages can't run rosidl generation directly.

### Definition files

`msg/Num.msg`:
```
int64 num
```

`msg/Sphere.msg`:
```
geometry_msgs/Point center
float64 radius
```

`srv/AddThreeInts.srv`:
```
int64 a
int64 b
int64 c
---
int64 sum
```

### `CMakeLists.txt` additions

```cmake
find_package(geometry_msgs REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/Num.msg"
  "msg/Sphere.msg"
  "srv/AddThreeInts.srv"
  DEPENDENCIES geometry_msgs
)
```

### `package.xml` additions (inside `<package>`)

```xml
<depend>geometry_msgs</depend>
<buildtool_depend>rosidl_default_generators</buildtool_depend>
<exec_depend>rosidl_default_runtime</exec_depend>
<member_of_group>rosidl_interface_packages</member_of_group>
```

### Build & verify

```bash
cd ~/ros2_ws
colcon build --packages-select tutorial_interfaces
source install/setup.bash

ros2 interface show tutorial_interfaces/msg/Num
ros2 interface show tutorial_interfaces/msg/Sphere
ros2 interface show tutorial_interfaces/srv/AddThreeInts
```

### Common errors

- "No definition of [...] for IDL type" → forgot `DEPENDENCIES geometry_msgs` or the matching `<depend>` in `package.xml`.
- `rosidl_generate_interfaces` macro not found → missing `find_package(rosidl_default_generators REQUIRED)`.
- Can't import the new type from another package → the consuming package needs `<depend>tutorial_interfaces</depend>` and (for C++) `find_package(tutorial_interfaces REQUIRED)` + `ament_target_dependencies(<exec> tutorial_interfaces)`.

---

## Implementing custom interfaces (single package defines and uses)
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Single-Package-Define-And-Use-Interface.html

Shows how to define an interface AND use it in the same `ament_cmake` package — useful when the message is tightly coupled to one node and you don't want a separate `*_interfaces` package.

### Create package & message dir

```bash
cd ~/ros2_ws/src
ros2 pkg create --build-type ament_cmake --license Apache-2.0 more_interfaces
mkdir more_interfaces/msg
```

### `msg/AddressBook.msg`

```
uint8 PHONE_TYPE_HOME=0
uint8 PHONE_TYPE_WORK=1
uint8 PHONE_TYPE_MOBILE=2

string first_name
string last_name
string phone_number
uint8 phone_type
```

### `src/publish_address_book.cpp`

```cpp
#include <chrono>
#include <memory>

#include "rclcpp/rclcpp.hpp"
#include "more_interfaces/msg/address_book.hpp"

using namespace std::chrono_literals;

class AddressBookPublisher : public rclcpp::Node
{
public:
  AddressBookPublisher()
  : Node("address_book_publisher")
  {
    address_book_publisher_ =
      this->create_publisher<more_interfaces::msg::AddressBook>(
        "address_book", 10);

    auto publish_msg = [this]() -> void {
        auto message = more_interfaces::msg::AddressBook();

        message.first_name = "John";
        message.last_name = "Doe";
        message.phone_number = "1234567890";
        message.phone_type = message.PHONE_TYPE_MOBILE;

        std::cout << "Publishing Contact\nFirst:" << message.first_name <<
          "  Last:" << message.last_name << std::endl;

        this->address_book_publisher_->publish(message);
      };
    timer_ = this->create_wall_timer(1s, publish_msg);
  }

private:
  rclcpp::Publisher<more_interfaces::msg::AddressBook>::SharedPtr
    address_book_publisher_;
  rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<AddressBookPublisher>());
  rclcpp::shutdown();

  return 0;
}
```

### `package.xml`

```xml
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd"
  schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>more_interfaces</name>
  <version>0.0.0</version>
  <description>Custom interfaces in same package</description>
  <maintainer email="user@example.com">user</maintainer>
  <license>Apache-2.0</license>

  <buildtool_depend>ament_cmake</buildtool_depend>
  <buildtool_depend>rosidl_default_generators</buildtool_depend>

  <depend>rclcpp</depend>
  <exec_depend>rosidl_default_runtime</exec_depend>

  <member_of_group>rosidl_interface_packages</member_of_group>

  <export>
    <build_type>ament_cmake</build_type>
  </export>
</package>
```

### `CMakeLists.txt`

```cmake
cmake_minimum_required(VERSION 3.16)
project(more_interfaces)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rosidl_default_generators REQUIRED)

set(msg_files
  "msg/AddressBook.msg"
)

rosidl_generate_interfaces(${PROJECT_NAME}
  ${msg_files}
)

add_executable(publish_address_book src/publish_address_book.cpp)
ament_target_dependencies(publish_address_book rclcpp)

# Link the executable against the typesupport target produced
# by rosidl_generate_interfaces in the SAME package.
rosidl_get_typesupport_target(cpp_typesupport_target
  ${PROJECT_NAME} rosidl_typesupport_cpp)

target_link_libraries(publish_address_book "${cpp_typesupport_target}")

install(TARGETS
    publish_address_book
  DESTINATION lib/${PROJECT_NAME})

ament_export_dependencies(rosidl_default_runtime)

ament_package()
```

The critical move: when the IDL is generated in the **same** package as the executable, you can't use `ament_target_dependencies(<exec> more_interfaces)` (the package isn't installed yet). Instead, link against the typesupport target via `rosidl_get_typesupport_target`.

### Build, source, run

```bash
cd ~/ros2_ws
colcon build --packages-up-to more_interfaces
source install/local_setup.bash
ros2 run more_interfaces publish_address_book

# verify in another terminal
source install/setup.bash
ros2 topic echo /address_book
```

Windows: substitute `--merge-install` and `call install\local_setup.bat`.

### Common errors

- `more_interfaces/msg/address_book.hpp: No such file or directory` → missing the `rosidl_get_typesupport_target` + `target_link_libraries` block, or you forgot to put `rosidl_generate_interfaces` BEFORE `add_executable`.
- Linker errors about `_typesupport_` symbols → same fix: add the `rosidl_get_typesupport_target` link.
- Runtime "package not found" for the message → forgot `ament_export_dependencies(rosidl_default_runtime)`.

---

## Using parameters in a class (C++)
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Using-Parameters-In-A-Class-CPP.html

Builds `cpp_parameters` package with one node that declares a string parameter, reads it on a 1 Hz timer, logs it, and re-sets it.

### Create the package

```bash
ros2 pkg create --build-type ament_cmake --license Apache-2.0 \
    --dependencies rclcpp cpp_parameters
```

### `src/cpp_parameters_node.cpp`

```cpp
#include <chrono>
#include <functional>
#include <string>

#include <rclcpp/rclcpp.hpp>

using namespace std::chrono_literals;

class MinimalParam : public rclcpp::Node
{
public:
  MinimalParam()
  : Node("minimal_param_node")
  {
    this->declare_parameter("my_parameter", "world");

    auto timer_callback = [this](){
      std::string my_param = this->get_parameter("my_parameter").as_string();

      RCLCPP_INFO(this->get_logger(), "Hello %s!", my_param.c_str());

      std::vector<rclcpp::Parameter> all_new_parameters{rclcpp::Parameter("my_parameter", "world")};
      this->set_parameters(all_new_parameters);
    };
    timer_ = this->create_wall_timer(1000ms, timer_callback);
  }

private:
  rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<MinimalParam>());
  rclcpp::shutdown();
  return 0;
}
```

### `CMakeLists.txt`

```cmake
cmake_minimum_required(VERSION 3.8)
project(cpp_parameters)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)

add_executable(minimal_param_node src/cpp_parameters_node.cpp)
ament_target_dependencies(minimal_param_node rclcpp)

install(TARGETS
    minimal_param_node
  DESTINATION lib/${PROJECT_NAME}
)

install(
  DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
```

### `package.xml`

```xml
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>cpp_parameters</name>
  <version>0.0.0</version>
  <description>C++ parameter tutorial</description>
  <maintainer email="you@email.com">Your Name</maintainer>
  <license>Apache-2.0</license>

  <buildtool_depend>ament_cmake</buildtool_depend>
  <depend>rclcpp</depend>
</package>
```

### `launch/cpp_parameters_launch.py`

```python
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='cpp_parameters',
            executable='minimal_param_node',
            name='custom_minimal_param_node',
            output='screen',
            emulate_tty=True,
            parameters=[
                {'my_parameter': 'earth'}
            ]
        )
    ])
```

### Build & exercise

```bash
cd ~/ros2_ws
rosdep install -i --from-path src --rosdistro jazzy -y
colcon build --packages-select cpp_parameters
source install/setup.bash

ros2 run cpp_parameters minimal_param_node
# -> Hello world!

# in another terminal
ros2 param set /minimal_param_node my_parameter earth
# next tick the node logs: Hello earth!  (then resets to "world")

# Or via launch with parameter override
ros2 launch cpp_parameters cpp_parameters_launch.py
```

### Common errors

- "Parameter 'my_parameter' is not declared" → forgot `declare_parameter` in the constructor before `get_parameter`.
- Set succeeds but value never changes → the timer callback resets it; remove the trailing `set_parameters` block to make `param set` stick.
- Launch override ignored → wrong `name=` (must match the node name the executable creates) or the parameter dict isn't a list.

---

## Using parameters in a class (Python)
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Using-Parameters-In-A-Class-Python.html

Same scenario, in `python_parameters`.

### Create the package

```bash
ros2 pkg create --build-type ament_python --license Apache-2.0 \
    --dependencies rclpy python_parameters
```

### `python_parameters/python_parameters_node.py`

```python
import rclpy
import rclpy.node
from rclpy.node import Node


class MinimalParam(Node):
    def __init__(self):
        super().__init__('minimal_param_node')

        self.declare_parameter('my_parameter', 'world')

        self.timer = self.create_timer(1, self.timer_callback)

    def timer_callback(self):
        my_param = self.get_parameter('my_parameter').get_parameter_value().string_value

        self.get_logger().info('Hello %s!' % my_param)

        my_new_param = rclpy.parameter.Parameter(
            'my_parameter',
            rclpy.Parameter.Type.STRING,
            'world'
        )
        all_new_parameters = [my_new_param]
        self.set_parameters(all_new_parameters)


def main():
    rclpy.init()
    node = MinimalParam()
    rclpy.spin(node)


if __name__ == '__main__':
    main()
```

### `setup.py`

```python
from setuptools import setup
import os
from glob import glob

package_name = 'python_parameters'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        (os.path.join('share', package_name), ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='YourName',
    maintainer_email='you@email.com',
    description='Python parameter tutorial',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'minimal_param_node = python_parameters.python_parameters_node:main',
        ],
    },
)
```

### `package.xml`

```xml
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>python_parameters</name>
  <version>0.0.0</version>
  <description>Python parameter tutorial</description>
  <maintainer email="you@email.com">Your Name</maintainer>
  <license>Apache-2.0</license>

  <depend>rclpy</depend>

  <test_depend>ament_copyright</test_depend>
  <test_depend>ament_flake8</test_depend>
  <test_depend>ament_pep257</test_depend>
  <test_depend>python3-pytest</test_depend>
</package>
```

### `launch/python_parameters_launch.py`

```python
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='python_parameters',
            executable='minimal_param_node',
            name='custom_minimal_param_node',
            output='screen',
            emulate_tty=True,
            parameters=[
                {'my_parameter': 'earth'}
            ]
        )
    ])
```

### Build & exercise

```bash
colcon build --packages-select python_parameters
source install/setup.bash

ros2 run python_parameters minimal_param_node
ros2 param set /minimal_param_node my_parameter earth
ros2 launch python_parameters python_parameters_launch.py
```

### Common errors

- `ParameterNotDeclaredException` → call `self.declare_parameter(...)` before `get_parameter(...)`.
- `TypeError` building `rclpy.parameter.Parameter(...)` → second arg must be a `rclpy.Parameter.Type` value, third arg the literal value.
- Launch overrides ignored → again, `name=` in the launch must match the node's runtime name.

---

## Using `ros2doctor` to identify issues
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Getting-Started-With-Ros2doctor.html

`ros2doctor` inspects all aspects of your ROS 2 install: platform, version, network, environment, and any running system. It's a configuration sanity tool — not a code debugger.

### Commands

```bash
# Run all checks
ros2 doctor

# Healthy output
# All <n> checks passed

# Detailed report (non-test, just data dump)
ros2 doctor --report
```

`--report` prints five sections:

- `NETWORK CONFIGURATION`
- `PLATFORM INFORMATION`
- `RMW MIDDLEWARE`
- `ROS 2 INFORMATION`
- `TOPIC LIST`

Other useful flags (alias `ros2 wtf`):

- `--include-warnings` — show passed checks that emitted warnings
- `--report-failed` — only print failed-module reports

### Output examples

Warning (non-fatal):
```
UserWarning: Publisher without subscriber detected on /turtle1/color_sensor.
```

Failure summary:
```
1/3 checks failed
Failed modules: network
```

### Hello / network test

```bash
ros2 doctor hello
```

Sends a multicast/test message and listens — exercises that your DDS discovery works between hosts. Useful when nodes on the same LAN can't see each other.

### Interpretation

- **Warnings** mean "suboptimal but functional" (e.g. no subscriber for a topic, prerelease distribution).
- **Errors** mean a critical setting (network, RMW) is missing.
- Pub/sub mismatch warnings are normal during startup; investigate only if persistent.

### Limitations

ros2doctor is **not a debugger** — it won't help you find logic errors, race conditions, or QoS-incompatibility crashes inside your nodes.

---

## Creating and using plugins (C++) — pluginlib
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Pluginlib.html

`pluginlib` is a C++ library for loading/unloading runtime classes from shared libraries without compile-time linkage. Two packages are involved: a **base** package that defines the abstract interface and the loader application, and a **plugins** package that provides concrete implementations.

### Create both packages

```bash
cd ~/ros2_ws/src

# Base / interface package (also hosts the area_node app)
ros2 pkg create --build-type ament_cmake --license Apache-2.0 \
    --dependencies pluginlib --node-name area_node polygon_base

# Plugin implementations package
ros2 pkg create --build-type ament_cmake --license Apache-2.0 \
    --dependencies polygon_base pluginlib \
    --library-name polygon_plugins polygon_plugins
```

### Base abstract class — `polygon_base/include/polygon_base/regular_polygon.hpp`

```cpp
#ifndef POLYGON_BASE_REGULAR_POLYGON_HPP
#define POLYGON_BASE_REGULAR_POLYGON_HPP

namespace polygon_base
{
  class RegularPolygon
  {
    public:
      virtual void initialize(double side_length) = 0;
      virtual double area() = 0;
      virtual ~RegularPolygon(){}

    protected:
      RegularPolygon(){}
  };
}  // namespace polygon_base

#endif  // POLYGON_BASE_REGULAR_POLYGON_HPP
```

### Plugin implementations — `polygon_plugins/src/polygon_plugins.cpp`

```cpp
#include <polygon_base/regular_polygon.hpp>
#include <cmath>

namespace polygon_plugins
{
  class Square : public polygon_base::RegularPolygon
  {
    public:
      void initialize(double side_length) override
      {
        side_length_ = side_length;
      }

      double area() override
      {
        return side_length_ * side_length_;
      }

    protected:
      double side_length_;
  };

  class Triangle : public polygon_base::RegularPolygon
  {
    public:
      void initialize(double side_length) override
      {
        side_length_ = side_length;
      }

      double area() override
      {
        return 0.5 * side_length_ * getHeight();
      }

      double getHeight()
      {
        return sqrt((side_length_ * side_length_) - ((side_length_ / 2) * (side_length_ / 2)));
      }

    protected:
      double side_length_;
  };
}

#include <pluginlib/class_list_macros.hpp>

PLUGINLIB_EXPORT_CLASS(polygon_plugins::Square, polygon_base::RegularPolygon)
PLUGINLIB_EXPORT_CLASS(polygon_plugins::Triangle, polygon_base::RegularPolygon)
```

### Plugin manifest — `polygon_plugins/plugins.xml`

```xml
<library path="polygon_plugins">
  <class type="polygon_plugins::Square" base_class_type="polygon_base::RegularPolygon">
    <description>This is a square plugin.</description>
  </class>
  <class type="polygon_plugins::Triangle" base_class_type="polygon_base::RegularPolygon" name="awesome_triangle">
    <description>This is a triangle plugin.</description>
  </class>
</library>
```

The optional `name="awesome_triangle"` allows loading the plugin by friendly name instead of the fully-qualified C++ type.

### `polygon_plugins/CMakeLists.txt`

```cmake
cmake_minimum_required(VERSION 3.16)
project(polygon_plugins)

find_package(ament_cmake REQUIRED)
find_package(polygon_base REQUIRED)
find_package(pluginlib REQUIRED)

# Tells the build system to install plugins.xml so the loader can find it
pluginlib_export_plugin_description_file(polygon_base plugins.xml)

add_library(${PROJECT_NAME} src/polygon_plugins.cpp)
ament_target_dependencies(${PROJECT_NAME} polygon_base pluginlib)

install(TARGETS ${PROJECT_NAME}
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

ament_package()
```

### `polygon_base/CMakeLists.txt` (interface library + loader app)

```cmake
cmake_minimum_required(VERSION 3.16)
project(polygon_base)

find_package(ament_cmake REQUIRED)
find_package(pluginlib REQUIRED)

# Header-only INTERFACE library exposing the abstract base
add_library(${PROJECT_NAME} INTERFACE)
add_library(${PROJECT_NAME}::${PROJECT_NAME} ALIAS ${PROJECT_NAME})
target_compile_features(${PROJECT_NAME} INTERFACE c_std_99 cxx_std_17)
target_include_directories(${PROJECT_NAME} INTERFACE
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include/${PROJECT_NAME}>
)
target_link_libraries(${PROJECT_NAME} INTERFACE ${pluginlib_TARGETS})

install(DIRECTORY include/
  DESTINATION include/${PROJECT_NAME}
)

install(TARGETS ${PROJECT_NAME}
  EXPORT export_${PROJECT_NAME}
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)
install(EXPORT export_${PROJECT_NAME}
  NAMESPACE ${PROJECT_NAME}::
  DESTINATION share/${PROJECT_NAME}/cmake
)

ament_export_include_directories(include)
ament_export_targets(export_${PROJECT_NAME})

ament_package()
```

### Loader application — `polygon_base/src/area_node.cpp`

```cpp
#include <pluginlib/class_loader.hpp>
#include <polygon_base/regular_polygon.hpp>

int main(int argc, char** argv)
{
  // To avoid unused parameter warnings
  (void) argc;
  (void) argv;

  pluginlib::ClassLoader<polygon_base::RegularPolygon> poly_loader(
      "polygon_base", "polygon_base::RegularPolygon");

  try
  {
    std::shared_ptr<polygon_base::RegularPolygon> triangle =
        poly_loader.createSharedInstance("awesome_triangle");
    triangle->initialize(10.0);

    std::shared_ptr<polygon_base::RegularPolygon> square =
        poly_loader.createSharedInstance("polygon_plugins::Square");
    square->initialize(10.0);

    printf("Triangle area: %.2f\n", triangle->area());
    printf("Square area: %.2f\n", square->area());
  }
  catch(pluginlib::PluginlibException& ex)
  {
    printf("The plugin failed to load for some reason. Error: %s\n", ex.what());
  }

  return 0;
}
```

### `polygon_plugins/package.xml` essentials

```xml
<package format="3">
  <name>polygon_plugins</name>
  ...
  <buildtool_depend>ament_cmake</buildtool_depend>
  <depend>polygon_base</depend>
  <depend>pluginlib</depend>

  <export>
    <build_type>ament_cmake</build_type>
  </export>
</package>
```

### Build & run

```bash
cd ~/ros2_ws
colcon build --packages-select polygon_base polygon_plugins
source install/setup.bash

# Sanity-check that pluginlib found your declarations
ros2 plugin list

ros2 run polygon_base area_node
# Triangle area: 43.30
# Square area: 100.00
```

### Common errors

- "Failed to load library [...] polygon_plugins" → forgot `pluginlib_export_plugin_description_file(polygon_base plugins.xml)`, or the `<library path="polygon_plugins">` doesn't match the installed library name.
- "Could not find class …" → mismatch between `PLUGINLIB_EXPORT_CLASS(...)` arguments and the `class type=` attribute in `plugins.xml`. Both must use identical fully-qualified names.
- Linking errors from the plugin lib → missing `ament_target_dependencies(${PROJECT_NAME} polygon_base pluginlib)`.
- `createSharedInstance("awesome_triangle")` throws → the friendly `name=` attribute is missing from `plugins.xml` for that class.
