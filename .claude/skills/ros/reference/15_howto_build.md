# How-To Guides — Build, Package & Release (ROS 2 Jazzy)

This reference covers the build-system, packaging, release, tracing, cross-compilation, migration, and core-maintainer how-to guides for ROS 2 Jazzy. Material that the Jazzy migration page only links out to (the ROS 1 → ROS 2 sub-pages) has been pulled in directly so the equivalency tables are usable without further fetches.

---

## How-To Guides — Index
**Source**: <https://docs.ros.org/en/jazzy/How-To-Guides.html>

The Jazzy How-To Guides index groups roughly thirty guides into the following categories. This file covers the items in the **Core Development**, **Migration**, **Release / Build / Packaging**, and **Maintainer** sections; other categories (launch syntax, DDS tuning, RMW, callback groups, Docker, RPi, IDEs, debugging) live in the other reference files.

- **Core Development**: Installation troubleshooting, Developing a ROS 2 package, Documenting a ROS 2 package, ament_cmake user documentation, ament_cmake_python user documentation.
- **Migration & Compatibility**: Migrating from ROS 1 to ROS 2, Using ros1_bridge with upstream ROS on Ubuntu 22.04.
- **Launch & Configuration**: XML/YAML/Python launch files, composable nodes, CLI ROS args, `ros2 param`.
- **Middleware & Communication**: sync vs async service clients, DDS tuning, multiple RMW, Topics vs Services vs Actions, Zero Copy Loaned Messages.
- **Specialized Topics**: Cross-compilation, Releasing a Package, Using Python Packages, Building a custom deb, Building ROS 2 with tracing, rosbag2 QoS overrides, Using variants, Callback Groups.
- **Deployment & Tools**: Docker, Raspberry Pi, Foxglove, Core Maintainer Guide, IDEs/Debugging, VSCode+Docker, Backtraces, Custom Rosdistro Version.

---

## Developing a ROS 2 Package
**Source**: <https://docs.ros.org/en/jazzy/How-To-Guides/Developing-a-ROS-2-Package.html>

**When to use it.** First-time package authoring, adding executables/libraries/launch files/messages/tests to an existing package, or setting up a mixed C++/Python project.

### Prerequisites
- ROS 2 installed and sourced.
- `colcon` available.
- Workspace tree, typically `~/ros2_ws/src`.

### Creating a package
The single canonical command:
```bash
ros2 pkg create --license Apache-2.0 <pkg-name> --dependencies <dep1> <dep2> ...
```

Build-type variants (selected with `--build-type`):

| Build type           | Use case                                        |
|----------------------|-------------------------------------------------|
| `ament_cmake`        | Pure C/C++ packages.                             |
| `ament_python`       | Pure Python packages.                            |
| `ament_cmake_python` | Mixed C++/Python (preferred over two packages). |
| `cmake`              | Plain CMake — no ament integration.              |

C++ example:
```bash
ros2 pkg create --build-type ament_cmake --license Apache-2.0 my_cpp_pkg \
  --dependencies rclcpp std_msgs
```

Python example:
```bash
ros2 pkg create --build-type ament_python --license Apache-2.0 my_py_pkg \
  --dependencies rclpy std_msgs
```

### `package.xml` essentials
- `<name>`, `<version>`, `<description>`, `<maintainer>`, `<license>`.
- Dependency tags:
  - `<build_depend>` — compile-time only.
  - `<exec_depend>` — runtime only (Python deps, dlopen, plugin loaders).
  - `<depend>` — both build and exec (the common case for C++ libraries).
  - `<test_depend>` — only when `BUILD_TESTING=ON`.
- `<export><build_type>ament_cmake</build_type></export>` (or `ament_python`/`ament_cmake_python`).

### `CMakeLists.txt` (ament_cmake)
Minimum executable wiring:
```cmake
add_executable(my_node src/my_node.cpp)
ament_target_dependencies(my_node rclcpp std_msgs)

install(TARGETS my_node
  DESTINATION lib/${PROJECT_NAME})

install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME})
```

### `setup.py` (ament_python)
```python
from setuptools import find_packages, setup

setup(
    name='my_package',
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/my_package']),
        (os.path.join('share', 'my_package'), ['package.xml']),
        (os.path.join('share', 'my_package', 'launch'), glob('launch/*')),
    ],
    install_requires=['setuptools'],
    entry_points={
        'console_scripts': [
            'my_script = my_package.my_script:main',
        ],
    },
)
```
Companion `setup.cfg`:
```ini
[develop]
script_dir=$base/lib/<package-name>
[install]
install_scripts=$base/lib/<package-name>
```

### Failure modes
- Missing `install(TARGETS …)` → `ros2 run` cannot find the executable.
- Missing `<exec_depend>` for a Python module → works in dev shell, breaks in clean install.
- Mixing `rosidl_generate_interfaces` with `ament_python_install_package` in a single package — explicitly broken (see ament_cmake_python entry).

---

## Documenting a ROS 2 Package
**Source**: <https://docs.ros.org/en/jazzy/How-To-Guides/Documenting-a-ROS-2-Package.html>

**When to use it.** Releasing to the buildfarm, hosting docs at `docs.ros.org/en/<distro>/p/<package>/`, or shipping API docs (Sphinx for Python, Doxygen→Breathe→Exhale for C++).

### Tooling: `rosdoc2`
`rosdoc2` is a wrapper around Sphinx that orchestrates Doxygen + Breathe + Exhale for C++ and `sphinx-apidoc` + `autodoc` for Python.

Install per the [rosdoc2 README](https://github.com/ros-infrastructure/rosdoc2#installation), then:
```bash
rosdoc2 default_config --package-path <package-path>   # generate stub
rosdoc2 build --package-path <package-path>            # build docs
```
Output: `docs_output/<package-name>/index.html`.

### Three-tier configuration

1. **`rosdoc2.yaml`** — main config; reference it in `package.xml`:
   ```xml
   <export>
     <rosdoc2>rosdoc2.yaml</rosdoc2>
   </export>
   ```
2. **`doc/conf.py`** — Sphinx config. Required only for custom pages. Add Python modules to the search path with:
   ```python
   sys.path.insert(0, os.path.abspath('.'))   # '.' is the package root
   ```
3. **`Doxyfile`** — usually left to rosdoc2 defaults; only override if Doxygen needs custom flags.

### Authoring custom Sphinx docs
```bash
cd <package>/doc
sphinx-quickstart        # answer "no" to separate source/build dirs
```
Edit `index.rst`. To expose Python API:
```rst
.. toctree::
   :maxdepth: 2
   :caption: Contents:

   Python Modules <modules>
```
For C++ API, create `cpp_api_docs.rst`:
```rst
C++ API Docs
============

.. toctree::
   :maxdepth: 3

   generated/index
```
…and add `cpp_api_docs` to the root toctree.

### Including `README.md`
Create `readme_include.md`:
````markdown
```{include} ../README.md
:relative-images:
```
````
Reference it from `index.rst`:
```rst
.. include:: readme_include.md
   :parser: myst_parser.sphinx_
```
Add `extensions = ["myst_parser"]` to `conf.py`.

### Buildfarm hosting
`rosdistro/jazzy/distribution.yaml` controls the doc job:
```yaml
<package_name>:
  doc:
    type: git
    url: https://github.com/<github_username>/<package_name>.git
    version: main
```
- Periodic rebuilds; no release tag required.
- Job name on <https://build.ros2.org>: `doc__<package_name>`.

### Failure modes
- Modules not found by autodoc → `sys.path.insert(0, os.path.abspath('.'))` missing.
- Broken README image links → use `:relative-images:`.
- C++ API empty → no Doxygen comments, or check rosdoc2 logs for Doxygen errors.
- Custom `conf.py` ignored → wrong path; rosdoc2 only honours `doc/conf.py`.

---

## ament_cmake User Documentation
**Source**: <https://docs.ros.org/en/jazzy/How-To-Guides/Ament-CMake-Documentation.html>

**When to use it.** Reference for every ament_cmake macro/function exposed to package authors. Reach for it whenever editing a `CMakeLists.txt` for a `ament_cmake` package.

### Project entry point

#### `ament_package([CONFIG_EXTRAS files...] [CONFIG_EXTRAS_POST files...])`
- Must be called **exactly once** and as the **last** command in `CMakeLists.txt`.
- Registers the package in the ament index, installs `package.xml`, generates the CMake config files used by downstream `find_package()`.
- `CONFIG_EXTRAS` — `.cmake`/`.cmake.in` templates exposed to clients (processed before `ament_export_*`).
- `CONFIG_EXTRAS_POST` — same, but processed after `ament_export_*`.
- Equivalent variables: `${PROJECT_NAME}_CONFIG_EXTRAS`, `${PROJECT_NAME}_CONFIG_EXTRAS_POST`.

### Dependency discovery & linking

#### `find_package(<pkg> REQUIRED)`
Standard CMake. Note: never `find_package` a transitive dependency you don't actually use — file a bug instead.

#### `ament_target_dependencies(<target> [PUBLIC|PRIVATE|INTERFACE] <dep1> <dep2> …)`
Recommended over raw `target_link_libraries`. Pulls in include directories, libraries, and transitive deps in one call.
```cmake
find_package(rclcpp REQUIRED)
ament_target_dependencies(my_node PUBLIC rclcpp std_msgs)
```

#### `target_link_libraries(<target> <lib>)`
Use namespaced targets when possible (`Eigen3::Eigen`, `my_pkg::my_lib`).

### Exporting to downstream packages

#### `ament_export_targets(<export-name> [HAS_LIBRARY_TARGET])`
Exports CMake targets so downstream `find_package(<pkg>)` callers can do `target_link_libraries(client PRIVATE my_pkg::my_lib)`. Pass `HAS_LIBRARY_TARGET` whenever the export set contains a library — adds the runtime library directory to env hooks.

#### `ament_export_dependencies(<dep1> <dep2> …)`
Re-exports dependencies so downstream packages don't need their own `find_package()` for them.

#### `ament_export_include_directories(<dir>…)` *(legacy)*
Marks include directories. Superseded by `ament_export_targets` for modern target-based installs.

#### `ament_export_libraries(<lib>…)` *(legacy)*
Replaced by `HAS_LIBRARY_TARGET` on `ament_export_targets`.

### Installation

Standard CMake `install()` is used; canonical patterns:
```cmake
install(DIRECTORY include/
  DESTINATION include/${PROJECT_NAME})

install(TARGETS my_library
  EXPORT export_${PROJECT_NAME}
  LIBRARY DESTINATION lib
  ARCHIVE DESTINATION lib
  RUNTIME DESTINATION bin
  INCLUDES DESTINATION include)

install(TARGETS my_executable
  DESTINATION lib/${PROJECT_NAME})
```
- `RUNTIME DESTINATION` is mandatory — Windows DLLs are runtime artifacts.
- The `EXPORT` name must match what `ament_export_targets` was called with.
- All paths are relative to `CMAKE_INSTALL_PREFIX`.

### Testing

Wrap test code in `if(BUILD_TESTING) … endif()`.

#### `ament_add_gtest(<name> <sources>… [APPEND_ENV …] [APPEND_LIBRARY_DIRS …] [ENV …] [TIMEOUT <s>] [SKIP_TEST] [SKIP_LINKING_MAIN_LIBRARIES] [WORKING_DIRECTORY <dir>])`
Creates a GoogleTest target.
```cmake
find_package(ament_cmake_gtest REQUIRED)
ament_add_gtest(some_test test/test_something.cpp TIMEOUT 120)
```
- `APPEND_ENV PATH=…` — append to env vars.
- `APPEND_LIBRARY_DIRS` — platform-agnostic library path setup.
- `ENV …` — override env vars.
- `TIMEOUT <s>` — default 60 s.
- `SKIP_TEST` — registers but skips (reports pass).
- `SKIP_LINKING_MAIN_LIBRARIES` — don't auto-link gtest_main.
- `WORKING_DIRECTORY <dir>` — defaults to `CMAKE_CURRENT_BINARY_DIR`.

#### `ament_add_gmock(<name> <sources>… …)`
Same options as `ament_add_gtest`; pulls in GMock too.

#### `ament_add_pytest_test(<name> <test-folder-or-file> …)`
Wraps `pytest`. Used by `ament_python` and mixed packages.

#### `ament_add_test(<name> COMMAND <cmd> [TIMEOUT <s>] [WORKING_DIRECTORY <dir>] [ENV …])`
Generic test runner — wrap any executable.

#### `ament_lint_auto_find_test_dependencies()`
Pairs with `find_package(ament_lint_auto REQUIRED)`. Discovers and runs every linter declared in `package.xml` (typically as `<test_depend>` of `ament_lint_common`).

#### `ament_lint_common`
Convenience metapackage exposing the standard linter set (cpplint, cppcheck, uncrustify, lint_cmake, xmllint, copyright, flake8, pep257…). Add as `<test_depend>` and call `ament_lint_auto_find_test_dependencies()`.

### Build-automation helpers

#### `target_include_directories(<target> PUBLIC "$<BUILD_INTERFACE:…>" "$<INSTALL_INTERFACE:…>")`
Standard CMake idiom for header-only / library headers.

#### `add_compile_options(...)`
Recommended boilerplate:
```cmake
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic -Wshadow)
endif()
```

### Extension points

#### `ament_register_extension(<extension_point> <package> <cmake_file>)`
Hooks a CMake script into an ament extension point (e.g., `rosidl_generate_interfaces`).
```cmake
ament_register_extension(
  "rosidl_generate_interfaces"
  "rosidl_generator_cpp"
  "rosidl_generator_cpp_generate_interfaces.cmake")
```

#### `ament_execute_extensions(<extension_point>)`
Runs all callbacks registered for the named extension point.

### Resource indexing

#### `ament_index_register_resource(<name> [CONTENT <str>] [CONTENT_FILE <path>] [PACKAGE_NAME <pkg>] [AMENT_INDEX_BINARY_DIR <dir>] [SKIP_INSTALL])`
Marker file in the ament index. `CONTENT` and `CONTENT_FILE` are mutually exclusive.
```cmake
ament_index_register_resource(rviz_ogre_media_exports
  CONTENT ${OGRE_MEDIA_RESOURCE_FILE})
```

#### `ament_index_has_resource(<var> <type> <name>)`
Sets `<var>` to `FALSE` or to the prefix path.

#### `ament_index_get_resource(<var> <type> <name> <prefix_path>)`
Fetches marker contents; errors if missing — guard with `ament_index_has_resource` first.

#### `ament_index_get_resources(<var> <type> <prefix_path>)`
Lists all packages registering the type.

### Environment hooks

#### `ament_environment_hooks(<file1.sh.in> <file2.dsv.in> …)`
Registers shell scripts run when a workspace is sourced.
- `.sh.in` — sh/bash/zsh; runtime evaluated.
- `.dsv.in` — machine-readable, faster colcon parse.
Example `.sh.in`:
```bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export FASTRTPS_DEFAULT_PROFILES_FILE="$COLCON_CURRENT_PREFIX/profile.xml"
```
Example `.dsv.in`:
```
set;RMW_IMPLEMENTATION;rmw_fastrtps_cpp
set;FASTRTPS_DEFAULT_PROFILES_FILE;profile.xml
```

### Versioning

#### `ament_generate_version_header(<target> [HEADER_PATH <path>])`
Requires `find_package(ament_cmake_gen_version_h REQUIRED)`. Generates a header containing macros driven by `package.xml` version. Example for `rclcpp`:
- `RCLCPP_VERSION_MAJOR`, `RCLCPP_VERSION_MINOR`, `RCLCPP_VERSION_PATCH`
- `RCLCPP_VERSION` — `major*10000 + minor*100 + patch`
- `RCLCPP_VERSION_STR` — `"1.2.3"`
- `RCLCPP_VERSION_GTE(major, minor, patch)`

Default output: `<build_dir>/<package_name>/version.h`. C/C++ only.

### Standard project layout
```
my_package/
├── CMakeLists.txt
├── package.xml
├── include/my_package/    # public headers
├── src/                   # private .cpp + private headers
├── test/                  # gtest / pytest
└── hooks/                 # environment hooks
```

### Boilerplate
```cmake
cmake_minimum_required(VERSION 3.8)
project(my_project)

if(NOT CMAKE_C_STANDARD)
  set(CMAKE_C_STANDARD 99)
endif()
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)

# … target definitions …

if(BUILD_TESTING)
  find_package(ament_cmake_gtest REQUIRED)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
  ament_add_gtest(my_test test/my_test.cpp)
endif()

ament_package()
```

### Quick reference

| Function                         | Purpose                                  | Scope                       |
|----------------------------------|------------------------------------------|------------------------------|
| `ament_target_dependencies()`    | Link + include for current target        | Current package build        |
| `ament_export_dependencies()`    | Re-export deps to downstream             | Downstream packages          |
| `ament_export_targets()`         | Export targets for `find_package()`      | Downstream `find_package()`  |
| `find_package()`                 | Locate a build dependency                | Build-time discovery         |
| `install()`                      | Deploy artifacts                         | Install phase                |

---

## ament_cmake_python User Documentation
**Source**: <https://docs.ros.org/en/jazzy/How-To-Guides/Ament-CMake-Python-Documentation.html>

**When to use it.** Mixed C++/Python packages built with `ament_cmake_python`, or any `ament_cmake` package shipping Python modules alongside C++ code.

### Macros documented

#### `ament_python_install_package(<dir>)`
Installs a Python package directory living next to `CMakeLists.txt`.
```cmake
find_package(ament_cmake_python REQUIRED)
ament_python_install_package(${PROJECT_NAME})
```
The argument is the directory name (typically `${PROJECT_NAME}`) containing `__init__.py` and the Python sources.

Other macros referenced (without full signatures in the Jazzy page):
- `ament_add_pytest_test(<name> <test-folder>)` — registers pytest tests via `ament_cmake_pytest`.
- `ament_python_install_module(<module>)` — install a single module file.
- `ament_get_python_install_dir(<var>)` — fetch the resolved Python site-packages dir.

### Console-script equivalent
For executables exposed by Python modules in an `ament_cmake_python` package, install the script via standard CMake `install(PROGRAMS …)`:
```cmake
install(PROGRAMS scripts/my_node.py
  DESTINATION lib/${PROJECT_NAME})
```

### Hard limitation
> Calling `rosidl_generate_interfaces` and `ament_python_install_package` in the same CMake project does not work.

Workaround: split message generation into a sibling `ament_cmake` package that the Python-bearing package depends on.

---

## Migrating from ROS 1 to ROS 2 (master entry)
**Source**: <https://docs.ros.org/en/jazzy/How-To-Guides/Migrating-from-ROS1.html>

**When to use it.** Porting an existing ROS 1 codebase to ROS 2 Jazzy. The master page is an index; the equivalency tables live in the C++ / Python / Launch / Parameters sub-pages and are reproduced below.

### Sub-guides
- Migrating Packages
- Migrating package.xml to format 2
- Migrating Interfaces
- Migrating C++ Package Example / Reference
- Migrating Python Package Example / Reference
- Migrating Launch Files
- Migrating Parameters
- Migrating Scripts

### Automated tools mentioned
- **Magical ROS 2 Conversion Tool**
- **AWS ROS2 Launch File Migrator**
- **AWS labs porting tools**
- **rospy2** — automatic `rospy` → `rclpy` converter

---

## ROS 1 → ROS 2: C++ Migration
**Source**: <https://docs.ros.org/en/jazzy/How-To-Guides/Migrating-from-ROS1/Migrating-CPP-Packages.html>

### Header file mapping
| ROS 1                                  | ROS 2                                            |
|----------------------------------------|--------------------------------------------------|
| `#include <ros/ros.h>`                 | `#include <rclcpp/rclcpp.hpp>`                   |
| `#include "std_msgs/String.h"`         | `#include "std_msgs/msg/string.hpp"`             |
| `#include "geometry_msgs/Twist.h"`     | `#include "geometry_msgs/msg/twist.hpp"`         |
| `#include "geometry_msgs/PointStamped.h"` | `#include "geometry_msgs/msg/point_stamped.hpp"` |
| `#include "nav_msgs/GetMap.h"`         | `#include "nav_msgs/srv/get_map.hpp"`            |
| `#include "std_msgs/time.h"`           | `#include "builtin_interfaces/msg/time.hpp"`     |

Pattern: insert the `msg` / `srv` / `action` subfolder, switch CamelCase → snake_case, swap `.h` → `.hpp`.

### Class & object mapping
| ROS 1                       | ROS 2                                            |
|-----------------------------|--------------------------------------------------|
| `ros::NodeHandle`           | `rclcpp::Node`                                   |
| `ros::Publisher`            | `rclcpp::Publisher<MessageType>`                 |
| `ros::Subscriber`           | `rclcpp::Subscription<MessageType>`              |
| `ros::ServiceClient`        | `rclcpp::Client<ServiceType>`                    |
| `ros::ServiceServer`        | `rclcpp::Service<ServiceType>`                   |
| `ros::Time`                 | `rclcpp::Time`                                   |
| `ros::Duration`             | `rclcpp::Duration`                               |
| `ros::Rate`                 | `rclcpp::Rate`                                   |

### Message / service namespacing (key change)
| ROS 1                            | ROS 2                                            |
|----------------------------------|--------------------------------------------------|
| `geometry_msgs::Twist`           | `geometry_msgs::msg::Twist`                      |
| `geometry_msgs::PointStamped`    | `geometry_msgs::msg::PointStamped`               |
| `nav_msgs::GetMap::Request`      | `nav_msgs::srv::GetMap::Request`                 |
| `std_msgs::Time`                 | `builtin_interfaces::msg::Time`                  |

> The namespace of ROS 2 messages, services, and actions uses a sub-namespace (`msg`, `srv`, or `action`) after the package name.

### Subsystem mapping
| ROS 1                | ROS 2                                                  |
|----------------------|--------------------------------------------------------|
| `roscpp`             | `rclcpp`                                               |
| `rospy`              | `rclpy`                                                |
| `roslaunch` (XML)    | `launch` / `launch_ros` (Python, plus XML/YAML)        |
| `rosbag`             | `rosbag2`                                              |
| `tf`                 | `tf2_ros` (use `tf2`/`tf2_ros` directly; `tf` removed) |
| `dynamic_reconfigure`| `ros2 param` + `add_on_set_parameters_callback`        |
| `nodelet`            | `rclcpp_components` (Component) / `ComponentManager`   |
| `actionlib`          | `rclcpp_action` (C++) / `rclpy.action` (Python)        |

### Boost → std
| ROS 1                                   | ROS 2                                |
|-----------------------------------------|--------------------------------------|
| `#include <boost/shared_ptr.hpp>`       | `#include <memory>`                  |
| `boost::shared_ptr<T>`                  | `std::shared_ptr<T>`                 |
| `#include <boost/thread/mutex.hpp>`     | `#include <mutex>`                   |
| `boost::mutex`                          | `std::mutex`                         |
| `boost::mutex::scoped_lock`             | `std::unique_lock<std::mutex>`       |
| `#include <boost/unordered_map.hpp>`    | `#include <unordered_map>`           |
| `boost::unordered_map`                  | `std::unordered_map`                 |
| `#include <boost/function.hpp>`         | `#include <functional>`              |
| `boost::function`                       | `std::function`                      |

Generated message types expose `MyMessage::SharedPtr` and `MyMessage::ConstSharedPtr`.

### Logging
| ROS 1            | ROS 2                                |
|------------------|--------------------------------------|
| `ROS_INFO(...)`  | `RCLCPP_INFO(node->get_logger(), …)` |
| `ROS_ERROR(...)` | `RCLCPP_ERROR(...)`                  |
| `ROS_WARN(...)`  | `RCLCPP_WARN(...)`                   |
| `ROS_DEBUG(...)` | `RCLCPP_DEBUG(...)`                  |

### Spinning
| ROS 1             | ROS 2                                                     |
|-------------------|-----------------------------------------------------------|
| `ros::spin()`     | `rclcpp::spin(node)`                                      |
| `ros::spinOnce()` | `executor.spin_some()` (use `SingleThreadedExecutor` etc.)|

### Service callback signature
ROS 1:
```cpp
bool service_callback(
  nav_msgs::GetMap::Request & request,
  nav_msgs::GetMap::Response & response);
```
ROS 2:
```cpp
void service_callback(
  const std::shared_ptr<nav_msgs::srv::GetMap::Request> request,
  std::shared_ptr<nav_msgs::srv::GetMap::Response> response);
```
No bool return — failures are signalled via thrown exceptions.

### Time fields
| ROS 1                          | ROS 2                                |
|--------------------------------|--------------------------------------|
| `std_msgs::Time`               | `builtin_interfaces::msg::Time`      |
| `.nsec` field                  | `.nanosec` field                     |

### Build system mapping
| ROS 1                                          | ROS 2                                            |
|------------------------------------------------|--------------------------------------------------|
| `find_package(catkin REQUIRED COMPONENTS …)`   | One `find_package()` per dep                     |
| `catkin_package(...)`                          | `ament_package()`                                |
| `catkin_add_gtest(...)`                        | `ament_add_gtest(...)`                           |
| `CATKIN_ENABLE_TESTING`                        | `BUILD_TESTING`                                  |
| `include_directories(...)`                     | `target_include_directories(...)`                |
| `add_message_files()` + `generate_messages()`  | `rosidl_generate_interfaces()`                   |
| `CATKIN_GLOBAL_BIN_DESTINATION`                | `bin`                                            |
| `CATKIN_PACKAGE_LIB_DESTINATION`               | `lib`                                            |
| `CATKIN_PACKAGE_INCLUDE_DESTINATION`           | `include/${PROJECT_NAME}`                        |
| `catkin_make` / `catkin build`                 | `colcon build`                                   |

### `package.xml`
| ROS 1                                                   | ROS 2                                                                   |
|---------------------------------------------------------|-------------------------------------------------------------------------|
| `<buildtool_depend>catkin</buildtool_depend>`           | `<buildtool_depend>ament_cmake_ros</buildtool_depend>`                  |
| (none)                                                   | `<export><build_type>ament_cmake</build_type></export>`                 |
| (msg packages: none)                                     | `<buildtool_depend>rosidl_default_generators</buildtool_depend>`        |

### Pub/sub example
ROS 1:
```cpp
#include <ros/ros.h>
#include <std_msgs/String.h>

ros::NodeHandle nh;
ros::Publisher pub = nh.advertise<std_msgs::String>("topic", 10);
std_msgs::String msg;
pub.publish(msg);
```
ROS 2:
```cpp
#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/string.hpp>

auto node = std::make_shared<rclcpp::Node>("node_name");
auto pub = node->create_publisher<std_msgs::msg::String>("topic", 10);
std_msgs::msg::String msg;
pub->publish(msg);
```

---

## ROS 1 → ROS 2: Python Migration
**Source**: <https://docs.ros.org/en/jazzy/How-To-Guides/Migrating-from-ROS1/Migrating-Python-Packages.html>

### Initialisation
```python
# ROS 1
rospy.init_node('node_name')
rospy.loginfo('hello')

# ROS 2
rclpy.init(args=sys.argv)
node = rclpy.create_node('node_name')
node.get_logger().info('hello')
```

### Parameters
```python
# ROS 1
port     = rospy.get_param('port', '/dev/ttyUSB0')
baudrate = rospy.get_param('baudrate', 115200)

# ROS 2
port     = node.declare_parameter('port', '/dev/ttyUSB0').value
baudrate = node.declare_parameter('baudrate', 115200).value
```

### Publishers / Subscribers
```python
# ROS 1
pub = rospy.Publisher('chatter', String, queue_size=10)
sub = rospy.Subscriber('chatter', String, callback, queue_size=10)

# ROS 2
pub = node.create_publisher(String, 'chatter', 10)
sub = node.create_subscription(String, 'chatter', callback, 10)
```
Note: argument order changes — type comes first; `queue_size` becomes a positional QoS depth.

### Services
```python
# ROS 1
srv = rospy.Service('add_two_ints', AddTwoInts, callback)

# ROS 2
srv = node.create_service(AddTwoInts, 'add_two_ints', callback)
```

### Service clients
```python
# ROS 1
rospy.wait_for_service('add_two_ints')
client = rospy.ServiceProxy('add_two_ints', AddTwoInts)
resp = client(req)

# ROS 2
client = node.create_client(AddTwoInts, 'add_two_ints')
while not client.wait_for_service(timeout_sec=1.0):
    node.get_logger().info('waiting...')
future = client.call_async(req)
rclpy.spin_until_future_complete(node, future)
```
Calls are async by default; sync semantics require explicit spinning.

### Logging
| ROS 1               | ROS 2                              |
|---------------------|------------------------------------|
| `rospy.loginfo()`   | `node.get_logger().info()`         |
| `rospy.logwarn()`   | `node.get_logger().warn()`         |
| `rospy.logerr()`    | `node.get_logger().error()`        |
| `rospy.logdebug()`  | `node.get_logger().debug()`        |

### Build configuration
- Python-only packages now use `setup.py` with `<export><build_type>ament_python</build_type></export>` in `package.xml`.
- Python 3 only.

### Message imports
The Python import path changes to mirror the C++ namespace shift — e.g. `from geometry_msgs.msg import Twist` (Python’s `.msg` subpackage matches the C++ `msg::` sub-namespace and the on-the-wire `geometry_msgs/msg/Twist` type name).

---

## ROS 1 → ROS 2: Launch File Migration
**Source**: <https://docs.ros.org/en/jazzy/How-To-Guides/Migrating-from-ROS1/Migrating-Launch-Files.html>

### `<node>` tag
| ROS 1                                | ROS 2                                                |
|--------------------------------------|------------------------------------------------------|
| `type="talker"`                      | `exec="talker"`                                      |
| `ns="my_ns"`                         | `namespace="my_ns"`                                  |
| `required="true"`                    | `on_exit="shutdown"`                                 |
| `machine`, `respawn_delay`, `clear_params` | removed                                       |

### Parameters
```xml
<!-- ROS 1 -->
<param name="foo" value="5" type="int"/>

<!-- ROS 2 -->
<param name="foo" value="5"/>
```
Type inference: `1` int, `1.0` float, `asd` string, `'1'` quoted string. Lists: `value="1,2,3" value-sep=","`. Hierarchical names: `group1.group2.my_param`.

### Remap (unchanged syntax, scoped per node)
```xml
<node pkg="demo_nodes_cpp" exec="talker">
  <remap from="chatter" to="my_topic"/>
</node>
```

### Include
```xml
<!-- ROS 1 -->
<include file="another.launch" ns="my_namespace"/>

<!-- ROS 2 -->
<group>
  <push_ros_namespace namespace="my_namespace"/>
  <include file="another.launch"/>
</group>
```
Arguments inside includes use `<let name="arg1" value="value1"/>` instead of `<arg>`.

### Arguments
```xml
<!-- ROS 1 -->
<arg name="topic_name" default="chatter" doc="The topic name"/>

<!-- ROS 2 -->
<arg name="topic_name" default="chatter" description="The topic name"/>
```
CLI: `ros2 launch mylaunch.xml topic_name:=custom_topic_name`.

### Environment
```xml
<set_env name="MY_ENV_VAR" value="MY_VALUE"/>
<node pkg="pkg" exec="exec">
  <env name="NODE_ENV_VAR" value="SOME_VALUE"/>
</node>
<unset_env name="MY_ENV_VAR"/>
```

### New tags
- `<let name="foo" value="asd"/>` — set a launch configuration value.
- `<push_ros_namespace namespace="ns"/>` — namespace a group.
- `<executable cmd="ls -las" cwd="/var/log" name="my_exec" shell="true"> … </executable>` — run any binary.

### Substitutions
| ROS 1            | ROS 2                                       |
|------------------|---------------------------------------------|
| `$(find pkg)`    | `$(find-pkg-share pkg)`                     |
| `$(env VAR)`     | `$(env VAR)` (errors if missing)            |
| `$(optenv VAR)`  | `$(env VAR '')`                             |
| `$(arg name)`    | `$(var name)`                               |
| —                | `$(exec-in-pkg exec_name pkg)`              |

### Python launch
```python
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='demo_nodes_cpp',
            executable='talker',
            name='my_talker',
            namespace='my_ns',
            remappings=[('chatter', 'my_topic')],
            parameters=[{'foo': 5}],
        ),
        Node(
            package='demo_nodes_cpp',
            executable='listener',
            remappings=[('chatter', 'my_topic')],
        ),
    ])
```

### Behavioural differences
1. Included files' arguments propagate **outward** automatically.
2. No global parameters — all parameters nest under nodes.
3. `machine` attribute unsupported.
4. `<test>` tag not currently supported.
5. Stricter attribute type checking.

### Group enhancements
```xml
<group scoped="true" forwarding="true">
  <let name="launch-prefix" value="time" if="$(var condition)"/>
  <node pkg="pkg" exec="exec"/>
</group>
```

---

## ROS 1 → ROS 2: Parameter Migration
**Source**: <https://docs.ros.org/en/jazzy/How-To-Guides/Migrating-from-ROS1/Migrating-Parameters.html>

### Architectural change
- ROS 1: central parameter server in `roscore`.
- ROS 2: per-node parameters served via ROS services. No `roscore` equivalent.
- For shared parameters, run the demo `parameter_blackboard` node.

### YAML format
ROS 1:
```yaml
lidar_name: foo
lidar_id: 10
ports: [11312, 11311, 21311]
debug: true
```
ROS 2:
```yaml
/lidar_ns:
  lidar_node_name:
    ros__parameters:
      lidar_name: foo
      id: 10
imu:
  ros__parameters:
    ports: [2438, 2439, 2440]
/**:
  ros__parameters:
    debug: true
```
- Scoped under fully-qualified node names.
- `ros__parameters` keyword required.
- `/**` wildcard targets all nodes.

### Replacing `dynamic_reconfigure`
- ROS 1’s `dynamic_reconfigure` updates a parameter group atomically.
- ROS 2’s `set_parameters` service updates each parameter individually.
- For atomic semantics, call `set_parameters_atomically` — one validation, all-or-nothing application.
- Hook into changes with `add_on_set_parameters_callback(...)` (C++) or `add_on_set_parameters_callback` on the Python `Node` — return a `SetParametersResult` per change.

### Known limitations
- Mixed-type lists not supported.
- `deg`/`rad` unit substitutions not supported.

---

## Releasing a Package — Index
**Source**: <https://docs.ros.org/en/jazzy/How-To-Guides/Releasing/Releasing-a-Package.html>

**When to use it.** Publishing a package to the official ROS 2 buildfarm so users can `apt install ros-jazzy-<pkg>`. Three workflows exist:
1. **Index your packages** — first-time entry into `rosdistro`.
2. **First-time release** — first bloom-release of an indexed package.
3. **Subsequent releases** — bumping versions of an already-released package.

The detailed commands for each step live in the sub-pages summarised below.

---

## Releasing — Indexing Your Packages
**Source**: <https://docs.ros.org/en/jazzy/How-To-Guides/Releasing/Index-Your-Packages.html>

### Prerequisites
- Public git repository (GitHub recommended).
- OSI-approved licence with SPDX identifier in each `package.xml`.
- Names compliant with REP 144.
- GitHub account.

### Procedure
1. **Fork** <https://github.com/ros/rosdistro> on GitHub.
2. **Clone** the fork:
   ```bash
   git clone git@github.com:YOUR-USERNAME/rosdistro.git
   cd rosdistro
   ```
3. **Pick distros** (typically Rolling at minimum, plus the current LTS such as Jazzy).
4. **Edit `<distro>/distribution.yaml`** to add:
   ```yaml
   YOUR-REPO-NAME:
     source:
       type: git
       url: https://YOUR-GIT-REPO-URL.git
       version: YOUR-BRANCH-NAME
     status: maintained        # or "developed" — see REP 141
   ```
5. **Optional doc job**:
   ```yaml
     doc:
       type: git
       url: https://YOUR-DOC-REPO-URL.git
       version: YOUR-DOC-BRANCH
   ```
6. **Validate**:
   ```bash
   python3 -m rosdistro.verify_rosdistro .
   ```
7. **PR** the branch against `ros/rosdistro`. Maintainers review per the REVIEW_GUIDELINES.

### Validation checklist
- Public HTTPS-accessible repo.
- OSI licence + SPDX in `package.xml`.
- REP 144 names.
- Git URL ends in `.git`.
- Specified branch exists.
- Valid YAML, no indentation errors.
- `status` matches REP 141.

---

## Releasing — First-Time Release
**Source**: <https://docs.ros.org/en/jazzy/How-To-Guides/Releasing/First-Time-Release.html>

### Install tooling
```bash
# Ubuntu/Debian
sudo apt install python3-bloom python3-catkin-pkg
# Fedora/RHEL
sudo dnf install python3-bloom python3-catkin_pkg
# Other
pip3 install -U bloom catkin_pkg

sudo rosdep init
rosdep update
```

### GitHub auth (`~/.config/bloom`)
Generate a Personal Access Token with `public_repo` and `workflow` scopes:
```json
{
  "github_user": "<username>",
  "oauth_token": "<your-token>"
}
```

### Release steps
1. **Generate changelog** (creates / updates `CHANGELOG.rst` per package):
   ```bash
   catkin_generate_changelog --all
   ```
   Edit each `CHANGELOG.rst`, then commit.
2. **Bump version, tag, push**:
   ```bash
   catkin_prepare_release
   ```
   Increments patch by default, replaces "Forthcoming" with the version + date, tags, and pushes.
3. **Bloom release** (new track):
   ```bash
   bloom-release --new-track --rosdistro jazzy --track jazzy my_repo
   ```
   Bloom prompts for: release-repository URL, upstream URI, upstream branch (e.g. `main`).

Post-release: bloom auto-opens a PR against `ros/rosdistro`. Once merged, packages reach `ros-testing` within 24–48 h, then sync to the main repo every 2–4 weeks.

---

## Releasing — Subsequent Releases
**Source**: <https://docs.ros.org/en/jazzy/How-To-Guides/Releasing/Subsequent-Releases.html>

### Prerequisites
Same tooling as first-time release. Configure git credentials for the `ros2-gbp` org if you opted for GBP-style remotes.

### Steps
1. **Update changelog**:
   ```bash
   catkin_generate_changelog
   ```
   Keep the "Forthcoming" header during edits, then commit.
2. **Bump + tag**:
   ```bash
   catkin_prepare_release [--bump minor|major]
   ```
   Increments the chosen segment in `package.xml`, replaces "Forthcoming", commits, tags, and pushes.
   - If the repo enforces "Require a pull request before merging", manually re-tag after the merge.
3. **Bloom release** (existing track):
   ```bash
   bloom-release --rosdistro jazzy my_repo
   ```
   Bloom raises the rosdistro PR automatically.

Same downstream timing: PR merged in 1–2 days, ros-testing within 24–48 h, sync every 2–4 weeks.

### Failure modes (common)
- Missing PAT scopes → bloom can't open PR.
- Unsigned-off commits → DCO bot blocks the PR.
- Release tracks misconfigured → use `--new-track` only the first time per distro.

---

## Building a Custom Deb Package
**Source**: <https://docs.ros.org/en/jazzy/How-To-Guides/Building-a-Custom-Deb-Package.html>

**When to use it.** Producing a `.deb` for a single ROS 2 package (private builds, CI artefacts, embedded deployments) without going through the buildfarm.

### Prerequisites
- All deps available locally or via rosdep.
- `package.xml` declares deps correctly.

### Install tools
```bash
sudo apt install python3-bloom python3-rosdep fakeroot debhelper dh-python
```

### Initialise rosdep
```bash
sudo rosdep init   # safe to ignore "already initialised"
sudo rosdep update
```

### Build
```bash
cd /path/to/pkg_source     # contains package.xml
bloom-generate rosdebian   # writes debian/ packaging files
fakeroot debian/rules binary
```

### Output
A `.deb` appears in the parent directory. Install with `sudo apt install ./<pkg>.deb` or `sudo dpkg -i`.

### Failure modes
- Missing local/rosdep deps.
- Compilation errors during the `binary` step.
- Incomplete dependency declarations in `package.xml`.

---

## Building ROS 2 with Tracing
**Source**: <https://docs.ros.org/en/jazzy/How-To-Guides/Building-ROS-2-with-Tracing.html>

**When to use it.** Performance analysis with LTTng. Tracing instrumentation ships in the ROS 2 source; on Linux installs the LTTng tracer is already a dependency.

### Build configurations

**Strip tracepoints only** (rebuild `tracetools`):
```bash
colcon build --packages-select tracetools --cmake-clean-cache \
  --cmake-args -DTRACETOOLS_TRACEPOINTS_EXCLUDED=ON
```

**Strip all instrumentation** (rebuild ROS 2):
```bash
colcon build --cmake-args -DTRACETOOLS_DISABLED=ON --no-warn-unused-cli
```

### Validate
```bash
ros2 run tracetools status
```
Expect `Tracing disabled` or `Tracing disabled through configuration`.

### Notes / failure modes
- Linux only.
- The page references <https://github.com/ros2/ros2_tracing> for `ros2 trace start/stop/pause`, recording locations, and analysis tools (e.g. babeltrace, trace-analysis); follow that repo for runtime usage.

---

## Cross-Compilation
**Source**: <https://docs.ros.org/en/jazzy/How-To-Guides/Cross-compilation.html>

**Status:** the legacy [`cross_compile`](https://github.com/ros-tooling/cross_compile) tool is **no longer supported** for Jazzy.

**Recommended alternative:** build multi-platform Docker images with `docker buildx`:
- See <https://github.com/docker/buildx#building-multi-platform-images>.
- Lets you target `linux/arm64`, `linux/arm/v7`, etc., without manual sysroot, QEMU, or binfmt setup.

**When to use:** producing aarch64/armhf binaries from an x86_64 dev machine for embedded targets (Jetson, RPi, etc.). Older docs about `ros_cross_compile --arch aarch64 --os ubuntu --rosdistro jazzy` no longer apply.

---

## Using Python Packages with ROS 2
**Source**: <https://docs.ros.org/en/jazzy/How-To-Guides/Using-Python-Packages.html>

**When to use it.** Pulling third-party Python deps (`numpy`, `pyserial`, `gtsam`…) into a ROS 2 workspace cleanly.

### Three install paths

**1. rosdep (preferred for releaseable packages).** Look up the key in `base.yaml` / `python.yaml` of the rosdep repos, declare it in `package.xml`, then:
```bash
rosdep install -yr --from-paths ./path/to/your/workspace
```

**2. System / pip:**
```bash
sudo apt install python3-serial                  # apt
python3 -m pip install -U pyserial               # pip global
python3 -m pip install -U --user pyserial        # pip user
```

**3. virtualenv (for isolated experimentation):**
```bash
mkdir -p ~/colcon_venv/src
cd ~/colcon_venv
virtualenv -p python3 ./venv
source ./venv/bin/activate
touch ./venv/COLCON_IGNORE          # stop colcon from descending into it
python3 -m pip install gtsam pyserial
colcon build
```

### Critical compatibility warning
The Python interpreter must match the one used to build your ROS 2 binaries. Implications:
- virtualenv / pipenv: use the **system** interpreter.
- conda: typically incompatible with binary ROS 2 due to interpreter mismatch.

### Recommended hierarchy
1. rosdep keys.
2. apt.
3. virtualenv backed by system Python (only if you need isolation).

---

## Using Variants
**Source**: <https://docs.ros.org/en/jazzy/How-To-Guides/Using-Variants.html>

**What.** Variants are official metapackages bundling related packages for one-shot install (`ros_base`, `desktop`, `desktop_full`, `perception`, etc.). Metapackages provide no software directly — they only `<exec_depend>` on the constituent packages.

**Specifications:**
- **REP 2001** — official variants list.
- **REP 108** — institution / robot-specific variants outside REP 2001.

### Authoring a project-private variant

`package.xml`:
```xml
<package format="2">
  <name>my_project_variant</name>
  <exec_depend>package_one</exec_depend>
  <exec_depend>package_two</exec_depend>
  <export>
    <build_type>ament_cmake</build_type>
  </export>
  <buildtool_depend>ament_cmake</buildtool_depend>
</package>
```

`CMakeLists.txt`:
```cmake
cmake_minimum_required(VERSION 3.5)
project(my_project_variant NONE)
find_package(ament_cmake REQUIRED)
ament_package()
```

### Platform-native alternative
On Debian/Ubuntu, `equivs` can synthesise a metapackage from existing apt packages — simpler than ROS tooling when no ROS-aware behaviour is needed.

### Contributing a public variant
PR REP 2001 in `openrobotics/reps`. Institution / robot variants don't require REP changes.

---

## Using a Custom Rosdistro
**Source**: <https://docs.ros.org/en/jazzy/How-To-Guides/Using-Custom-Rosdistro.html>

**When to use.** Pinning to a historical rosdistro snapshot to dodge a regression in `rolling`, or pointing CI at a private rosdistro fork.

### Files / env vars
- Default sources list: `/etc/ros/rosdep/sources.list.d/20-default.list`.
- Cache: `~/.ros/rosdep/sources.cache` (don't edit manually).
- `ROSDISTRO_INDEX_URL` overrides the URL of `index-v4.yaml`.

### Steps
1. **Pick a tag** in <https://github.com/ros/rosdistro> (e.g. `rolling/2024-02-28`).
2. **Patch the default sources list:**
   ```bash
   sed -i "s|ros\/rosdistro\/master|ros\/rosdistro\/rolling\/2024-02-28|" \
     /etc/ros/rosdep/sources.list.d/20-default.list
   ```
3. **Export the index URL:**
   ```bash
   export ROSDISTRO_INDEX_URL=https://raw.githubusercontent.com/ros/rosdistro/rolling/2024-02-28/index-v4.yaml
   ```
   Use `index-v4.yaml`, not the legacy formats.
4. **Refresh:**
   ```bash
   rosdep update
   ```
5. (Optional) persist by adding the export to `~/.bashrc`.

Custom forks: substitute the org/repo path freely.

### Real-world examples
Nav2's CircleCI and `ros_gz`'s GitHub Actions use this pattern to bypass temporary Rolling outages.

### Failure modes
- Wrong index version (older than v4) → resolution failures.
- Index schema drift on a fork → silent missing keys.
- Stale cache after a switch → `rosdep update` again.

---

## ROS 2 Core Maintainer Guide
**Source**: <https://docs.ros.org/en/jazzy/How-To-Guides/Core-maintainer-guide.html>

**When to use.** You maintain a core ROS 2 package or have just been added to `@ros/team`.

### Responsibilities
- Code review, CI management, releases, issue triage, package health.

### Code-review criteria
- Suitability in the package, correct implementation, conforms to developer guidelines.
- Adds tests for the bug/feature; documentation for new features.
- Clean CI run.
- Targets the default branch (usually `rolling`).
- ≥ 1 maintainer approval (not the author).

### CI surface
- **PR builds** (build.ros2.org) — automatic per-PR, Linux only, repo-local.
- **CI builds** (ci.ros2.org) — manually triggered, all platforms (Linux, macOS, Windows), can build deps.
- Use `--packages-up-to` / `--packages-select` to scope colcon CI runs.

### Merge checklist
- DCO bot passes.
- PR build green.
- CI green on all platforms.
- ≥ 1 maintainer approval.

### Release flow
1. `catkin_generate_changelog`
2. `catkin_prepare_release`
3. `bloom-release --track <distro> --rosdistro <distro> <repo>`

### Backporting
- All changes land on the development branch first.
- Backports must not break API or ABI on a released distro.

### Issue triage
- Redirect questions to Robotics Stack Exchange.
- Transfer off-topic issues.
- Tag feature requests `help-wanted`.
- Reproduce bugs before fixing.

### CI dashboards
- <https://ci.ros2.org/view/nightly>
- <https://ci.ros2.org/view/packaging>
- <https://build.ros2.org/view/Rci>
- <https://build.ros2.org/view/Rdev>

### Escalation
Tag `@ros/team` for help on tricky issues.

---

## Topics vs Services vs Actions
**Source**: <https://docs.ros.org/en/jazzy/How-To-Guides/Topics-Services-Actions.html>

**When to use it.** Choosing the right communication primitive when designing a new node.

### Topics
- **For:** continuous data streams (sensor data, robot state, …).
- Asynchronous, many-to-many, publisher-controlled timing, callback-driven.
- **Use cases:** sensor streams (LiDAR, camera), state broadcasts, status updates.
- **Anti-pattern:** confirmed-delivery semantics — use a service or action.

### Services
- **For:** RPCs that terminate quickly — node-state queries, IK calculations.
- Synchronous request/response, single client per call.
- **Don't use for:** long-running work, work that may need pre-emption, state that affects other nodes.
- **Anti-pattern:** anything that may need to be cancelled mid-execution.

### Actions
- **For:** discrete behaviours that move a robot or run for a while with feedback.
- Non-blocking, **pre-emptable** (clean cancellation is mandatory in the server), parallel goals each with their own state, periodic feedback + final result.
- **Use cases:** navigation goals, manipulation, slow perception routines, switching control modes.
- **Anti-pattern:** quick lookups (use a service) or unbounded streams (use a topic).

### Comparison matrix

| Dimension          | Topics              | Services            | Actions                         |
|--------------------|---------------------|---------------------|---------------------------------|
| Timing             | Continuous          | Synchronous, quick  | Async, longer duration          |
| Blocking           | Non-blocking        | Blocking            | Non-blocking                    |
| Cancellation       | N/A                 | Not supported       | Supported (pre-emption)         |
| Data flow          | Many-to-many        | One-to-one          | One-to-many parallel goals      |
| Feedback           | Streaming updates   | Single response     | Feedback + result               |
| State              | Per-topic           | Stateless ideal     | Per-goal state                  |

### Decision tree
1. Continuous data? → **Topic**.
2. Quick query/response? → **Service**.
3. Cancellable / longer execution / needs progress? → **Action**.
