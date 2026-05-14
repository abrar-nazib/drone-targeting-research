# RViz & Testing (ROS 2 Jazzy)

## RViz

### RViz User Guide
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Intermediate/RViz/RViz-User-Guide/RViz-User-Guide.html

RViz is the standard ROS 2 3D visualization tool. Launch it after sourcing the
overlay:

```bash
source /opt/ros/jazzy/setup.bash
ros2 run rviz2 rviz2
# or with a saved config:
ros2 run rviz2 rviz2 -d my_config.rviz
```

**Window layout** (panels can be docked, hidden, or floated via the Panels menu):

- **3D View** - central viewport that renders all enabled displays.
- **Displays panel** (left) - tree of active Display instances with property
  editors and a status indicator (green = OK, yellow = warning, red = error,
  grey = disabled). The root node is **Global Options** (Fixed Frame,
  Background Color, Frame Rate, Default Light) plus Global Status.
- **Tool panel / toolbar** (top) - buttons for the active interaction tool.
- **Tool Properties** - per-tool settings (e.g. topic for 2D Pose Estimate).
- **Views panel** (right) - selects the View Controller and edits its pose.
- **Time panel** (bottom) - ROS Time, ROS Elapsed, Wall Time, Wall Elapsed,
  with a Reset button that clears caches and time-related state. Mostly used
  in simulation.
- **Selection panel** - properties of objects picked with the Select tool.

**Adding displays.** Click "Add" under the Displays panel to either pick a
display by type or "By topic" (RViz auto-suggests displays compatible with
each live topic). Each display exposes a common set of QoS-related properties
(Topic, Reliability Policy, Durability Policy, History Policy, Depth) plus
type-specific options.

**Built-in display types** (the Jazzy `rviz_default_plugins` set):

| Display | Purpose |
|---|---|
| **Axes** | Renders an XYZ triad for a chosen TF frame. |
| **Camera** | Renders a `sensor_msgs/Image` with the matching `CameraInfo` so it can overlay 3D content with correct intrinsics. |
| **DepthCloud** | Builds a point cloud from a depth Image + CameraInfo (and optional RGB). |
| **Effort** | Per-joint effort from `sensor_msgs/JointState`. |
| **FluidPressure / Illuminance / Temperature / RelativeHumidity** | Scalar `sensor_msgs` displays drawn at the sensor frame. |
| **Grid** | Reference grid plane (cell count, cell size, plane offset). |
| **GridCells** | `nav_msgs/GridCells` (sparse 2D cells, often costmap obstacles). |
| **Image** | Raw `sensor_msgs/Image` in a 2D window, no calibration. |
| **InteractiveMarkers** | 3D widgets the user can drag/click; subscribes to `visualization_msgs/InteractiveMarkerUpdate`. |
| **LaserScan** | `sensor_msgs/LaserScan` with selectable Style (Points/Squares/Flat Squares/Spheres/Boxes), Color Transformer (Intensity/AxisColor/FlatColor), Decay Time, Size. |
| **Map** | `nav_msgs/OccupancyGrid` rendered as a textured plane. |
| **Marker** | `visualization_msgs/Marker` primitives (see below). |
| **MarkerArray** | `visualization_msgs/MarkerArray` (batched markers, more efficient). |
| **Odometry** | History of `nav_msgs/Odometry` poses with covariance ellipses. |
| **Path** | `nav_msgs/Path` polyline. |
| **PointCloud** / **PointCloud2** | `sensor_msgs/PointCloud[2]` with the same Style/Transformer/Decay options as LaserScan. |
| **PointStamped** | Single `geometry_msgs/PointStamped`. |
| **Polygon** | `geometry_msgs/PolygonStamped` outline. |
| **Pose** / **PoseArray** / **PoseWithCovariance** | Single or batched `geometry_msgs` poses with arrow/axes shape options. |
| **Range** | Sonar/IR cone from `sensor_msgs/Range`. |
| **RobotModel** | URDF visual meshes posed by TF; reads description from a parameter or topic (`robot_description`). |
| **TF** | Visualizes the entire TF tree with frame axes and parent-child arrows. |
| **WrenchStamped** / **TwistStamped** / **AccelStamped** | Force/torque or velocity/acceleration arrows at a frame. |

**Global Options.** `Fixed Frame` is the world frame the renderer assumes is
not moving (typically `map` or `odom`); displays are transformed into this
frame each redraw. `Background Color`, `Frame Rate`, and `Default Light`
configure the viewport.

**Toolbar tools** (default keyboard shortcuts):

| Tool | Shortcut | Action |
|---|---|---|
| Move Camera | `m` | Drag to orbit/pan/zoom (default tool). |
| Interact | `i` | Click and drag interactive markers. |
| Select | `s` | Box/click pick of rendered objects (Shift adds, Ctrl removes). |
| Focus Camera | `f` (or `c`) | Reorients the camera to look at a clicked point. |
| Measure | `n` | Click two points to read their Euclidean distance. |
| 2D Pose Estimate | `p` | Publishes a `PoseWithCovarianceStamped` on `/initialpose` (AMCL seed). |
| 2D Goal Pose | `g` | Publishes `PoseStamped` on `/goal_pose` (Nav2). |
| Publish Point | `u` | Publishes `geometry_msgs/PointStamped` on `/clicked_point`. |

**View controllers** (Views panel): `Orbit` (default; orbit a focal point),
`FPS` (yaw/pitch from camera position), `XYOrbit` (focal point pinned to the
ground plane), `TopDownOrtho` (orthographic Z-down map view), and
`ThirdPersonFollower` (orbits a Target Frame and follows it). Each controller
exposes editable Distance, Focal Point, Yaw, Pitch fields and a
`Target Frame` pulldown.

**Configurations.** File > Save Config (or Save Config As) writes a `.rviz`
YAML file storing: enabled displays and all their properties, the active
tool and its properties, all view controllers and the current view, panel
geometry, and global options. Load with File > Open Config or by passing
`-d path/to.rviz` to `rviz2`. RViz remembers the last config in
`~/.rviz2/`.

**Status indicators.** Each display has a Status sub-tree with detailed
diagnostics; hover or expand to see why a display is yellow/red (common
causes: missing TF transform, no messages received, mismatched QoS).

---

### Markers: Sending Basic Shapes
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Intermediate/RViz/Marker-Sending-Basic-Shapes/Marker-Sending-Basic-Shapes.html

`visualization_msgs/msg/Marker` is RViz's general-purpose primitive. A single
`Marker` is identified by the `(ns, id)` pair - publishing a new marker with
the same pair replaces the previous one, which is how you animate / update
visualizations.

**Message fields:**

| Field | Type | Notes |
|---|---|---|
| `header` | `std_msgs/Header` | `frame_id` is the TF frame the pose is expressed in; `stamp` is the time used by TF. |
| `ns` | string | Namespace; combines with `id` for uniqueness. |
| `id` | int32 | Per-namespace marker id. |
| `type` | int32 | One of the type enum values below. |
| `action` | int32 | `ADD = 0` (also MODIFY), `DELETE = 2`, `DELETEALL = 3`. |
| `pose` | `geometry_msgs/Pose` | Position + orientation (quaternion). |
| `scale` | `geometry_msgs/Vector3` | Meaning depends on `type` (1.0 = 1 m). |
| `color` | `std_msgs/ColorRGBA` | RGBA in [0, 1]; `a = 0` makes the marker invisible. |
| `lifetime` | `builtin_interfaces/Duration` | 0 = forever. |
| `frame_locked` | bool | If true, marker is re-transformed every render even if no new message arrives (it "sticks" to a moving frame). |
| `points` | `geometry_msgs/Point[]` | Used by LINE_*, *_LIST, POINTS, TRIANGLE_LIST. |
| `colors` | `std_msgs/ColorRGBA[]` | Per-vertex colors that override `color` when non-empty. |
| `text` | string | Body for `TEXT_VIEW_FACING`. |
| `mesh_resource` | string | URI for `MESH_RESOURCE` (e.g. `package://my_pkg/meshes/x.dae`). |
| `mesh_use_embedded_materials` | bool | If true, use the mesh's own materials instead of `color`. |

**Type enum:**

```
ARROW = 0
CUBE = 1
SPHERE = 2
CYLINDER = 3
LINE_STRIP = 4
LINE_LIST = 5
CUBE_LIST = 6
SPHERE_LIST = 7
POINTS = 8
TEXT_VIEW_FACING = 9
MESH_RESOURCE = 10
TRIANGLE_LIST = 11
```

**Minimal C++ publisher** (cycles through CUBE -> SPHERE -> ARROW -> CYLINDER):

```cpp
#include <memory>
#include "rclcpp/rclcpp.hpp"
#include "visualization_msgs/msg/marker.hpp"

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  auto node = rclcpp::Node::make_shared("basic_shapes");
  auto marker_pub = node->create_publisher<visualization_msgs::msg::Marker>(
    "visualization_marker", 1);
  rclcpp::Rate loop_rate(1);

  uint32_t shape = visualization_msgs::msg::Marker::CUBE;

  while (rclcpp::ok()) {
    visualization_msgs::msg::Marker marker;
    marker.header.frame_id = "my_frame";
    marker.header.stamp = node->now();
    marker.ns = "basic_shapes";
    marker.id = 0;
    marker.type = shape;
    marker.action = visualization_msgs::msg::Marker::ADD;

    marker.pose.position.x = 0;
    marker.pose.position.y = 0;
    marker.pose.position.z = 0;
    marker.pose.orientation.x = 0.0;
    marker.pose.orientation.y = 0.0;
    marker.pose.orientation.z = 0.0;
    marker.pose.orientation.w = 1.0;

    marker.scale.x = 1.0;
    marker.scale.y = 1.0;
    marker.scale.z = 1.0;

    marker.color.r = 0.0f;
    marker.color.g = 1.0f;
    marker.color.b = 0.0f;
    marker.color.a = 1.0;

    marker.lifetime = rclcpp::Duration::from_nanoseconds(0);

    marker_pub->publish(marker);

    switch (shape) {
      case visualization_msgs::msg::Marker::CUBE:
        shape = visualization_msgs::msg::Marker::SPHERE; break;
      case visualization_msgs::msg::Marker::SPHERE:
        shape = visualization_msgs::msg::Marker::ARROW; break;
      case visualization_msgs::msg::Marker::ARROW:
        shape = visualization_msgs::msg::Marker::CYLINDER; break;
      case visualization_msgs::msg::Marker::CYLINDER:
        shape = visualization_msgs::msg::Marker::CUBE; break;
    }
    loop_rate.sleep();
  }
  rclcpp::shutdown();
  return 0;
}
```

**To view:** `ros2 run rviz2 rviz2`, set Fixed Frame to `my_frame`, Add a
**Marker** display (default topic `visualization_marker`).

---

### Markers: Points and Lines
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Intermediate/RViz/Marker-Points-and-Lines/Marker-Points-and-Lines.html

Three types use the `points` array instead of a single pose:

- `POINTS` - one rendered point per `points[i]`. Width is `scale.x`, height
  is `scale.y`.
- `LINE_STRIP` - polyline connecting `points[0]-points[1]-points[2]-...`.
  Line width is `scale.x` only (`scale.y` and `scale.z` are ignored).
- `LINE_LIST` - independent segments from each consecutive pair: `0-1`, `2-3`,
  `4-5`, .... Requires an even number of points. Width is `scale.x`.

The `colors[]` array, when populated, gives per-vertex color (overrides
`color`). Typical loop:

```cpp
visualization_msgs::msg::Marker points, line_strip, line_list;
// ... set header/ns/id/type/action/pose/color/scale ...
for (uint32_t i = 0; i < 100; ++i) {
  float y = 5.0f * std::sin(0.1f * i);
  float z = 5.0f * std::cos(0.1f * i);
  geometry_msgs::msg::Point p;
  p.x = static_cast<int32_t>(i) - 50;
  p.y = y;
  p.z = z;
  points.points.push_back(p);
  line_strip.points.push_back(p);
  // The line list needs two points per segment:
  line_list.points.push_back(p);
  p.z += 1.0;
  line_list.points.push_back(p);
}
```

A single marker with many points is far cheaper than many one-point markers.

---

### Marker Display Types
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Intermediate/RViz/Marker-Display-types/Marker-Display-types.html

Reference for how RViz interprets each marker `type` and what `scale` and the
auxiliary fields mean.

| Type | Required fields | Scale meaning |
|---|---|---|
| `ARROW` | `pose` (and optional shaft/head sizes) **or** two entries in `points` for tail and tip | If pose form: `scale.x` = length, `scale.y` = arrow shaft diameter, `scale.z` = arrow head diameter. If points form: `scale.x` = shaft diameter, `scale.y` = head diameter, `scale.z` = head length (0 -> default). |
| `CUBE` | `pose` | `scale.{x,y,z}` are side lengths; pivot at the center. |
| `SPHERE` | `pose` | `scale.{x,y,z}` are diameters along each axis (set differently for an ellipsoid). |
| `CYLINDER` | `pose` | `scale.x`, `scale.y` are base diameters, `scale.z` is height. |
| `LINE_STRIP` | `points` | `scale.x` is line width. |
| `LINE_LIST` | `points` (paired) | `scale.x` is line width. |
| `CUBE_LIST` | `points`, optional `colors` | All cubes share `scale.{x,y,z}`; one cube per point. Much faster than many `CUBE` markers. |
| `SPHERE_LIST` | `points`, optional `colors` | All spheres share `scale.{x,y,z}`. |
| `POINTS` | `points`, optional `colors` | `scale.x` = point width, `scale.y` = point height. |
| `TEXT_VIEW_FACING` | `text`, `pose` | Only `scale.z` matters - the height of an uppercase A in meters. The text always faces the camera. |
| `MESH_RESOURCE` | `mesh_resource`, `pose` | `scale.{x,y,z}` multiplies the mesh's natural size. Set `mesh_use_embedded_materials = true` to use the mesh's materials (otherwise `color` tints it). URIs use `package://pkg/path` or `file://`. |
| `TRIANGLE_LIST` | `points` in groups of 3, optional `colors` (per-vertex) | `scale.{x,y,z}` scales the resulting mesh; pivot at `pose`. |

Performance: prefer `CUBE_LIST` / `SPHERE_LIST` / `POINTS` / `TRIANGLE_LIST`
over thousands of individual markers.

---

### Building a Custom RViz Display
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Intermediate/RViz/RViz-Custom-Display/RViz-Custom-Display.html

Two base classes:

- `rviz_common::Display` - the most general; you handle subscriptions and
  rendering yourself.
- `rviz_common::MessageFilterDisplay<MsgT>` - convenience template for
  messages with a `std_msgs/Header`. Handles topic subscription, QoS
  properties, and TF-based message filtering (waits for the transform from
  `header.frame_id` to the Fixed Frame before delivering the message).

**Virtual functions to override:**

| Override | When to use |
|---|---|
| `onInitialize()` | Called once after `scene_manager_` and `scene_node_` are valid. Construct Ogre nodes / visual objects here, NOT in the constructor. |
| `reset()` | Called when the user clicks Reset; clear cached state and visual objects. |
| `onEnable()` / `onDisable()` | Called when the display checkbox is toggled. Recreate / destroy subscriptions or visuals. |
| `update(wall_dt, ros_dt)` | Per-frame tick; do animation or polling work that doesn't depend on a new message. |
| `processMessage(MsgT::ConstSharedPtr msg)` | (MessageFilterDisplay only) Called once a message has a valid TF transform; update your scene node here. |

**Properties** are added in the constructor and live as children of the
display in the Displays panel:

```cpp
color_property_ = new rviz_common::properties::ColorProperty(
  "Color", QColor(204, 51, 204), "Marker color.",
  this, SLOT(updateStyle()));
alpha_property_ = new rviz_common::properties::FloatProperty(
  "Alpha", 1.0f, "0..1", this, SLOT(updateStyle()));
```

Other property types: `BoolProperty`, `IntProperty`, `EnumProperty`,
`StringProperty`, `RosTopicProperty`, `TfFrameProperty`, `VectorProperty`.

**Pluginlib registration** at the bottom of the source file:

```cpp
#include <pluginlib/class_list_macros.hpp>
PLUGINLIB_EXPORT_CLASS(my_pkg::MyDisplay, rviz_common::Display)
```

**plugins_description.xml** (any name, referenced by package.xml):

```xml
<library path="my_pkg_plugin">
  <class name="my_pkg/MyDisplay"
         type="my_pkg::MyDisplay"
         base_class_type="rviz_common::Display">
    <description>One-line description shown in the Add dialog.</description>
    <message_type>my_pkg/msg/MyMessage</message_type>
  </class>
</library>
```

**package.xml** export tag:

```xml
<export>
  <build_type>ament_cmake</build_type>
  <rviz_common plugin="${prefix}/plugins_description.xml"/>
</export>
```

Plus `<depend>` entries for `rviz_common`, `rviz_default_plugins`,
`rviz_rendering`, `pluginlib`, the message package, and Qt
(`<depend>qtbase5-dev</depend>` or `qt6` on Jazzy depending on your platform).

**CMakeLists.txt sketch:**

```cmake
find_package(ament_cmake REQUIRED)
find_package(rviz_common REQUIRED)
find_package(rviz_default_plugins REQUIRED)
find_package(rviz_rendering REQUIRED)
find_package(pluginlib REQUIRED)
find_package(Qt5 REQUIRED COMPONENTS Widgets)   # or Qt6 on Jazzy
find_package(my_msgs REQUIRED)

set(CMAKE_AUTOMOC ON)
qt5_wrap_cpp(MOC_FILES include/my_pkg/my_display.hpp)

add_library(my_pkg_plugin SHARED
  src/my_display.cpp
  ${MOC_FILES})

target_include_directories(my_pkg_plugin PUBLIC include)
ament_target_dependencies(my_pkg_plugin
  rviz_common rviz_default_plugins rviz_rendering pluginlib my_msgs)
target_link_libraries(my_pkg_plugin Qt5::Widgets)

pluginlib_export_plugin_description_file(rviz_common plugins_description.xml)

install(TARGETS my_pkg_plugin
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin)
install(DIRECTORY include/ DESTINATION include)
install(FILES plugins_description.xml DESTINATION share/${PROJECT_NAME})

ament_export_include_directories(include)
ament_export_libraries(my_pkg_plugin)
ament_package()
```

After `colcon build` the new display appears under "Add > By display type"
in RViz.

---

### Building a Custom RViz Panel
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Intermediate/RViz/RViz-Custom-Panel/RViz-Custom-Panel.html

A panel is a Qt widget docked into the RViz main window (think "control
surface" rather than a 3D visual). Subclass `rviz_common::Panel`:

```cpp
class MyPanel : public rviz_common::Panel
{
  Q_OBJECT
public:
  explicit MyPanel(QWidget * parent = nullptr);

  // Lifecycle
  void onInitialize() override;     // get the ROS node abstraction
  void load(const rviz_common::Config & config) override;
  void save(rviz_common::Config config) const override;

protected:
  // Optional
  void onEnable();
  void onDisable();

private Q_SLOTS:
  void onButtonClicked();

private:
  std::shared_ptr<rviz_common::ros_integration::RosNodeAbstractionIface> node_;
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr pub_;
  QPushButton * button_;
  QLabel * label_;
};
```

**Key points:**

- Always declare `Q_OBJECT` so Qt's `moc` generates signal/slot glue.
- Build the QWidget UI (layouts, buttons, labels) in the constructor; wire
  Qt signals to slots with `QObject::connect(button_, &QPushButton::clicked,
  this, &MyPanel::onButtonClicked);`.
- In `onInitialize()`, call
  `getDisplayContext()->getRosNodeAbstraction().lock()` to get a
  `RosNodeAbstractionIface`; from there
  `node_->get_raw_node()` returns the `rclcpp::Node::SharedPtr` you can use
  to create publishers, subscribers, parameter clients, service clients.
- `load()` / `save()` persist panel state into the `.rviz` config file.

**Pluginlib registration** in the .cpp:

```cpp
#include <pluginlib/class_list_macros.hpp>
PLUGINLIB_EXPORT_CLASS(my_pkg::MyPanel, rviz_common::Panel)
```

**plugin_description.xml:**

```xml
<library path="my_pkg_panel">
  <class name="my_pkg/MyPanel"
         type="my_pkg::MyPanel"
         base_class_type="rviz_common::Panel">
    <description>Short description shown in the Add New Panel dialog.</description>
  </class>
</library>
```

**package.xml** export (same pattern as displays):

```xml
<export>
  <build_type>ament_cmake</build_type>
  <rviz_common plugin="${prefix}/plugin_description.xml"/>
</export>
```

**CMakeLists.txt:**

```cmake
find_package(rviz_common REQUIRED)
find_package(pluginlib REQUIRED)
find_package(Qt5 REQUIRED COMPONENTS Widgets)
find_package(rclcpp REQUIRED)

set(CMAKE_AUTOMOC ON)

add_library(my_pkg_panel SHARED src/my_panel.cpp)
target_include_directories(my_pkg_panel PUBLIC include)
ament_target_dependencies(my_pkg_panel rviz_common pluginlib rclcpp)
target_link_libraries(my_pkg_panel Qt5::Widgets)

pluginlib_export_plugin_description_file(rviz_common plugin_description.xml)

install(TARGETS my_pkg_panel LIBRARY DESTINATION lib)
install(FILES plugin_description.xml DESTINATION share/${PROJECT_NAME})
ament_package()
```

In RViz, open via **Panels > Add New Panel** and pick your class from the
list. The panel docks like the built-in Displays/Tool/Views panels and is
saved into the active `.rviz` config.

---

## Testing

### CLI Tools for Testing
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Testing/CLI.html

**Build first**, then test (or build and test in one step):

```bash
colcon build --packages-select my_pkg
colcon test  --packages-select my_pkg --event-handlers console_cohesion+
colcon test-result --verbose
```

Useful flags:

| Command/flag | Purpose |
|---|---|
| `colcon test` | Runs all test targets registered through `ament_add_*` / `add_test` (no need to source the workspace - colcon sets up the env). |
| `--packages-select <pkg> [...]` | Only test the listed packages. |
| `--packages-up-to <pkg>` | Test the package and its recursive dependencies. |
| `--event-handlers console_cohesion+` | Print test stdout/stderr live (otherwise it's captured into the log files). |
| `--ctest-args -R <regex>` | Filter ctest test names by regex. |
| `--pytest-args -k <expr>` | Filter pytest tests by expression. |
| `--return-code-on-test-failure` | Make `colcon test` exit non-zero if any test fails (useful for CI). |
| `colcon test-result` | Summary of pass/fail per package. |
| `colcon test-result --verbose` | Prints failing test cases with their assertion messages. |
| `colcon test-result --all` | Lists every JUnit XML, even passing ones. |

Test artifacts land in `build/<pkg>/test_results/<pkg>/*.xml` (JUnit XML
format); colcon parses these to produce its summary, and CI systems
(Jenkins / GitHub Actions) consume them directly.

**Standard linters** added by `ament_lint_auto` + `ament_lint_common`:

| Linter | What it checks |
|---|---|
| `ament_cppcheck` | Static analysis on C/C++ code. |
| `ament_cpplint` | Google C++ style guide. |
| `ament_uncrustify` | C++ code formatting. |
| `ament_lint_cmake` | CMake style. |
| `ament_xmllint` | XML well-formedness (package.xml, plugin xml, URDF). |
| `ament_copyright` | All source files have a copyright/license header. |
| `ament_flake8` | Python style (PEP 8 + Flake8 plugins). |
| `ament_pep257` | Python docstring conventions. |

Wire them in once with:

```cmake
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()
```

and in `package.xml`:

```xml
<test_depend>ament_lint_auto</test_depend>
<test_depend>ament_lint_common</test_depend>
```

`ament_lint_common` pulls in the eight linters above as test dependencies;
`ament_lint_auto_find_test_dependencies()` finds them at configure time and
adds one CTest target per linter.

---

### Writing Basic Tests in C++ (GTest)
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Testing/Cpp.html

ROS 2 wraps GoogleTest with `ament_cmake_gtest`, which both adds the test
executable and registers it with CTest so `colcon test` will run it.

**package.xml:**

```xml
<test_depend>ament_cmake_gtest</test_depend>
<test_depend>ament_lint_auto</test_depend>
<test_depend>ament_lint_common</test_depend>
```

**CMakeLists.txt:**

```cmake
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()

  find_package(ament_cmake_gtest REQUIRED)
  ament_add_gtest(${PROJECT_NAME}_tutorial_test test/tutorial_test.cpp)
  target_include_directories(${PROJECT_NAME}_tutorial_test PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>)
  target_link_libraries(${PROJECT_NAME}_tutorial_test
    ${PROJECT_NAME})  # link in your library
  ament_target_dependencies(${PROJECT_NAME}_tutorial_test
    rclcpp std_msgs)  # extra ROS deps
endif()
```

`ament_add_gtest` behaves like `add_executable` plus it sets up gtest
linkage and a JUnit XML output path.

**Minimal test file** (`test/tutorial_test.cpp`):

```cpp
#include <gtest/gtest.h>

TEST(MyMath, Adds)
{
  ASSERT_EQ(4, 2 + 2);
  EXPECT_TRUE(2 + 2 == 4);
  EXPECT_FLOAT_EQ(0.1f + 0.2f, 0.3f);
}

int main(int argc, char ** argv)
{
  testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
```

`ASSERT_*` aborts the test on failure, `EXPECT_*` records the failure but
keeps going. Common assertions: `EQ/NE/LT/LE/GT/GE`, `TRUE/FALSE`,
`STREQ/STRNE`, `FLOAT_EQ/DOUBLE_EQ`, `NEAR(a, b, eps)`, `THROW(stmt, type)`.

**Fixtures** with shared setup/teardown:

```cpp
class NodeFixture : public testing::Test
{
protected:
  void SetUp() override {
    rclcpp::init(0, nullptr);
    node_ = std::make_shared<rclcpp::Node>("test_node");
  }
  void TearDown() override { rclcpp::shutdown(); }
  rclcpp::Node::SharedPtr node_;
};

TEST_F(NodeFixture, PublishesOnce)
{
  auto pub = node_->create_publisher<std_msgs::msg::String>("/t", 10);
  EXPECT_EQ(pub->get_subscription_count(), 0u);
}
```

Use `TEST_F(Fixture, name)` to get a fresh fixture instance per test, or
`TEST_P` + `INSTANTIATE_TEST_SUITE_P` for parameterized tests.

---

### Writing Basic Tests in Python (pytest)
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Testing/Python.html

ROS 2 uses `pytest` for Python tests in both `ament_python` and `ament_cmake`
packages.

**ament_python package layout:**

```
my_pkg/
  package.xml
  setup.py
  setup.cfg
  my_pkg/__init__.py
  my_pkg/node.py
  test/
    test_basic.py
```

`setup.py` declares pytest as a test requirement:

```python
setup(
  ...
  tests_require=['pytest'],
  ...
)
```

The `test/` directory is automatically discovered by `colcon test` when
running `pytest` against the package.

**Test file** (filenames must match `test_*.py`; functions must start with
`test_`):

```python
import pytest
from my_pkg.math import add

def test_basic():
    assert add(2, 2) == 4

@pytest.mark.parametrize("a,b,expected", [(1, 1, 2), (2, 3, 5)])
def test_param(a, b, expected):
    assert add(a, b) == expected

@pytest.fixture
def some_state():
    return {"counter": 0}

def test_uses_fixture(some_state):
    some_state["counter"] += 1
    assert some_state["counter"] == 1
```

Class-based tests are also picked up if the class is named `Test*` and
methods start with `test_`.

**ament_cmake package** that needs to ship Python tests uses
`ament_cmake_pytest`:

```xml
<test_depend>ament_cmake_pytest</test_depend>
```

```cmake
if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(my_python_tests test/test_basic.py)
endif()
```

**Useful invocations:**

```bash
colcon test --packages-select my_pkg
colcon test --packages-select my_pkg --pytest-args -k test_basic
colcon test --packages-select my_pkg --pytest-args -s   # show prints
colcon test-result --verbose
```

---

### Writing Basic Integration Tests with launch_testing
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Testing/Integration.html

`launch_testing` runs a `LaunchDescription` (one or more nodes / processes)
and lets you assert on their stdout/stderr, on topic data, and finally on
their exit codes after they shut down. Tests are typically run isolated on
their own ROS_DOMAIN_ID so parallel runs don't cross-talk.

**package.xml:**

```xml
<test_depend>launch_testing</test_depend>
<test_depend>launch_testing_ament_cmake</test_depend>
<test_depend>launch_testing_ros</test_depend>  <!-- optional, ROS helpers -->
<test_depend>launch_ros</test_depend>
<test_depend>rclpy</test_depend>
```

**CMakeLists.txt** - register the launch test (use the isolated runner so
each test gets its own DDS domain):

```cmake
if(BUILD_TESTING)
  find_package(ament_cmake_ros REQUIRED)
  find_package(launch_testing_ament_cmake REQUIRED)

  function(add_ros_isolated_launch_test path)
    set(RUNNER "${ament_cmake_ros_DIR}/run_test_isolated.py")
    add_launch_test("${path}" RUNNER "${RUNNER}" ${ARGN})
  endfunction()

  add_ros_isolated_launch_test(test/test_integration.py)
endif()
```

`add_launch_test` is provided by `launch_testing_ament_cmake`; without the
isolated runner the basic form is `add_launch_test(test/test_xxx.py)`.

**Test file structure** (`test/test_integration.py`):

```python
import unittest
import pytest
import launch
import launch_ros.actions
import launch_testing
import launch_testing.actions
import launch_testing.asserts


@pytest.mark.launch_test
def generate_test_description():
    talker = launch_ros.actions.Node(
        package='demo_nodes_cpp', executable='talker', name='talker')

    return launch.LaunchDescription([
        talker,
        # Give nodes a moment to come up, then signal that the
        # active tests below should start running.
        launch.actions.TimerAction(
            period=0.5,
            actions=[launch_testing.actions.ReadyToTest()]),
    ]), {'talker': talker}


# Active tests run while the launched processes are alive.
class TestTalkerOutput(unittest.TestCase):

    def test_talker_prints_hello(self, proc_output, talker):
        proc_output.assertWaitFor(
            'Publishing', process=talker, timeout=10, stream='stdout')


# Post-shutdown tests run after every process has exited.
@launch_testing.post_shutdown_test()
class TestProcessOutput(unittest.TestCase):

    def test_exit_codes(self, proc_info):
        launch_testing.asserts.assertExitCodes(proc_info)
```

**Key concepts:**

- `generate_test_description()` must return either a `LaunchDescription` or
  the tuple `(LaunchDescription, context_dict)`. Names in the context dict
  (e.g. `talker`) become arguments your test methods can request by name.
- `launch_testing.actions.ReadyToTest()` is the explicit signal that all
  setup is done; the active test class only starts after this action runs.
  Wrap it in a `TimerAction` to give nodes time to reach steady state.
- The active test class subclasses `unittest.TestCase` (no decorator). It
  has access to `proc_output`, `proc_info`, and any names from the context
  dict. Common assertions:
  - `proc_output.assertWaitFor('text', process=p, timeout=5, stream='stdout')`
  - `launch_testing.tools.process.assertInStdout(proc_output, 'text', node)`
  - regular `unittest` asserts on data captured by your own subscribers
- The post-shutdown class is decorated with
  `@launch_testing.post_shutdown_test()` and runs once the launch finishes.
  Typical asserts:
  - `launch_testing.asserts.assertExitCodes(proc_info)` - all processes
    returned 0 (or the codes you specify per process).
  - `launch_testing.asserts.assertSequentialStdout(proc_output, p, ['a', 'b'])`
  - inspect `proc_info[node].returncode` directly.

`launch_testing_ros` adds ROS-aware helpers, e.g.
`launch_testing_ros.WaitForTopics(['/chatter'], timeout=10.0)` for
condition-based readiness.

Run with `colcon test`; pytest-launch produces the same JUnit XML output as
unit tests, so `colcon test-result --verbose` works on it too.

---

### Build Farm Testing
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Testing/BuildFarmTesting.html

Covers the prerequisites for running your repository's tests on
`build.ros2.org` (Open Robotics' Jenkins-based CI) before merging a pull
request, rather than the internals of the build farm itself.

**Requirements to enable PR testing:**

1. **Bot access.** Grant the `@ros-pull-request-builder` GitHub user read
   access to your repository (or the org that owns it). Without it the
   build farm cannot fetch your branch.
2. **Webhook.** Configure a GitHub webhook on the repo (or org) pointing at
   `https://build.ros2.org/ghprbhook/`, with delivery of `Pull request` and
   `Issue comment` events. Comments like `please test this` from a
   maintainer will then re-run the job.
3. **Indexed in rosdistro.** The package must already be present in
   `ros/rosdistro` (a `source` entry pointing at your repo for the matching
   distro, e.g. `jazzy/distribution.yaml`).
4. **`test_pull_requests` flag enabled.** Set this on the source entry in
   `rosdistro` (the `bloom-release` tooling normally writes this entry for
   you on first release). It tells the build farm to spin up a per-PR job.

Once those are in place every PR opened against the repo gets a Jenkins
job that builds the package against the configured target ROS 2
distribution(s), runs the same `colcon test` suite you would run locally,
and reports back into the PR conversation. The job's JUnit XML and console
log are linked from the PR check, the same way `colcon test-result` would
display them locally.

The build farm dashboard is `https://build.ros2.org`; per-package devel and
release job pages live under that URL and surface test counts, warnings,
and ABI changes for downstream consumers.
