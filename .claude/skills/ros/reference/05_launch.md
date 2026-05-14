# Launch System (ROS 2 Jazzy)

> Sources: Intermediate launch tutorials + launch-related how-to guides

## Creating Launch Files
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Launch/Creating-Launch-Files.html

A ROS 2 launch file describes the configuration of a multi-node system and executes it as one unit. Three formats are supported: **Python (`.launch.py` / `*_launch.py`)**, **XML (`*_launch.xml`)**, and **YAML (`*_launch.yaml`)**. Python is most flexible (full scripting), XML/YAML are simpler for static graphs.

The **Python entrypoint** is a function `generate_launch_description()` returning a `launch.LaunchDescription` whose constructor takes a list of *actions*. The most common action is `launch_ros.actions.Node`, which spawns a ROS node by `package` + `executable`. Common keyword arguments:
- `package` (str): ament package name
- `executable` (str): name of the installed executable
- `name` (str): runtime node name (overrides default)
- `namespace` (str): pushes the node into a namespace
- `parameters` (list of dict|file): parameters to set
- `remappings` (list of `(from, to)` tuples): topic/service remaps
- `arguments` (list of str): full argv passed to the executable, including `--ros-args` if needed
- `ros_arguments` (list of str): ROS-only args (the launcher prepends `--ros-args` for you)
- `output` (str): `screen`, `log`, or `both`
- `respawn` (bool), `respawn_delay` (float)
- `condition`: `IfCondition` / `UnlessCondition`

Two namespaced turtlesim nodes (`turtlesim1`, `turtlesim2`) plus a `mimic` node that bridges them. `arguments=['--ros-args', '--log-level', 'info']` mixes raw argv with ROS args; `ros_arguments=['--log-level', 'warn']` is the cleaner ROS-only equivalent.

Complete Python launch file (`turtlesim_mimic_launch.py`):

```python
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='turtlesim',
            namespace='turtlesim1',
            executable='turtlesim_node',
            name='sim',
            arguments=['--ros-args', '--log-level', 'info']
        ),
        Node(
            package='turtlesim',
            namespace='turtlesim2',
            executable='turtlesim_node',
            name='sim',
            ros_arguments=['--log-level', 'warn']
        ),
        Node(
            package='turtlesim',
            executable='mimic',
            name='mimic',
            remappings=[
                ('/input/pose', '/turtlesim1/turtle1/pose'),
                ('/output/cmd_vel', '/turtlesim2/turtle1/cmd_vel'),
            ]
        )
    ])
```

Equivalent XML:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<launch>
  <node pkg="turtlesim" exec="turtlesim_node" name="sim"
        namespace="turtlesim1" args="--ros-args --log-level info" />
  <node pkg="turtlesim" exec="turtlesim_node" name="sim"
        namespace="turtlesim2" ros_args="--log-level warn" />
  <node pkg="turtlesim" exec="mimic" name="mimic">
    <remap from="/input/pose" to="/turtlesim1/turtle1/pose" />
    <remap from="/output/cmd_vel" to="/turtlesim2/turtle1/cmd_vel" />
  </node>
</launch>
```

Equivalent YAML:

```yaml
%YAML 1.2
---
launch:
  - node:
      pkg: "turtlesim"
      exec: "turtlesim_node"
      name: "sim"
      namespace: "turtlesim1"
      args: "--ros-args --log-level info"
  - node:
      pkg: "turtlesim"
      exec: "turtlesim_node"
      name: "sim"
      namespace: "turtlesim2"
      ros_args: "--log-level warn"
  - node:
      pkg: "turtlesim"
      exec: "mimic"
      name: "mimic"
      remap:
        - from: "/input/pose"
          to: "/turtlesim1/turtle1/pose"
        - from: "/output/cmd_vel"
          to: "/turtlesim2/turtle1/cmd_vel"
```

Run a standalone launch file (no package install):

```bash
mkdir launch
# place file in launch/, then:
cd launch
ros2 launch turtlesim_mimic_launch.py
```

Run an installed package launch file:

```bash
ros2 launch <package_name> <launch_file_name>
```

Trigger mimic behaviour:

```bash
ros2 topic pub -r 1 /turtlesim1/turtle1/cmd_vel \
  geometry_msgs/msg/Twist \
  "{linear: {x: 2.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: -1.8}}"
```

Visualise topology: `ros2 run rqt_graph rqt_graph`. To enable the `ros2 launch` CLI in a package, add `<exec_depend>ros2launch</exec_depend>` in `package.xml`.

---

## Integrating Launch Files into a ROS 2 Package
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Launch/Launch-system.html

Launch files belong in a `launch/` directory at the package root. A Python ament package looks like:

```
src/
  py_launch_example/
    launch/
    package.xml
    py_launch_example/
    resource/
    setup.cfg
    setup.py
    test/
```

A C++ ament package looks like:

```
src/
  cpp_launch_example/
    launch/
    CMakeLists.txt
    package.xml
    src/
```

**Naming conventions** (match the `ros2 launch` autocomplete):
- Python: `*launch.py` (ending in `launch.py` is what enables autocomplete; `_launch.py` is the convention)
- XML: `*_launch.xml`
- YAML: `*_launch.yaml`

### Install targets — Python package (`setup.py`)

```python
import os
from glob import glob
from setuptools import setup

package_name = 'py_launch_example'

setup(
    # ... other parameters ...
    data_files=[
        # ... other data files ...
        # Include all launch files.
        (os.path.join('share', package_name, 'launch'), glob('launch/*'))
    ]
)
```

### Install targets — C++ package (`CMakeLists.txt`)

Add before `ament_package()`:

```cmake
# Install launch files.
install(DIRECTORY
  launch
  DESTINATION share/${PROJECT_NAME}/
)
```

### Minimal example launch files

Python (`my_script_launch.py`):

```python
import launch
import launch_ros.actions

def generate_launch_description():
    return launch.LaunchDescription([
        launch_ros.actions.Node(
            package='demo_nodes_cpp',
            executable='talker',
            name='talker'),
    ])
```

XML (`my_script_launch.xml`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<launch>
  <node pkg="demo_nodes_cpp" exec="talker" name="talker"/>
</launch>
```

YAML (`my_script_launch.yaml`):

```yaml
%YAML 1.2
---
launch:
  - node:
      pkg: "demo_nodes_cpp"
      exec: "talker"
      name: "talker"
```

Build and run:

```bash
colcon build
ros2 launch py_launch_example my_script_launch.py
ros2 launch cpp_launch_example my_script_launch.xml
```

---

## Using Substitutions
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Launch/Using-Substitutions.html

**Substitutions** are placeholders the launch system resolves *at launch time* (deferred), not when the file is parsed. They make launch files reusable and let parent files override child arguments.

### Common substitution classes (Python imports)

| Substitution | Module | Purpose |
|---|---|---|
| `LaunchConfiguration('name')` | `launch.substitutions` | Read value of a declared launch argument |
| `TextSubstitution(text='...')` | `launch.substitutions` | Wrap a literal string when concatenating with substitutions |
| `EnvironmentVariable('NAME')` | `launch.substitutions` | Read an environment variable |
| `PathJoinSubstitution([...])` | `launch.substitutions` | Cross-platform path join, accepts substitutions as parts |
| `PythonExpression([...])` | `launch.substitutions` | Evaluate a Python expression (string concatenation of pieces) |
| `Command([...])` | `launch.substitutions` | Run a shell command, capture stdout (e.g. `xacro`) |
| `FindExecutable(name='ros2')` | `launch.substitutions` | Locate an executable on `PATH` |
| `LocalSubstitution('event.reason')` | `launch.substitutions` | Reference attributes of the local event in handlers |
| `FindPackageShare('pkg')` | `launch_ros.substitutions` | Resolve to a package's `share/` directory |

### Frontend (XML/YAML) substitution syntax

- `$(var argname)` — read a launch argument
- `$(find-pkg-share pkg)` — resolve a package share directory
- `$(eval 'python_expression')` — evaluate Python at launch time
- `$(env VAR)` — environment variable
- `$(find-exec name)` — locate executable

### `DeclareLaunchArgument`

Declares a CLI-visible launch argument with optional `default_value` and `description`. Must be declared before being referenced via `LaunchConfiguration`.

```python
DeclareLaunchArgument(
    'argument_name',
    default_value='default_value',
    description='what this controls'
)
```

CLI override:

```bash
ros2 launch <pkg> <file> argument_name:=value
```

List args of a launch file:

```bash
ros2 launch <pkg> <file> --show-args
```

### Full example — `example_substitutions_launch.py`

Demonstrates `DeclareLaunchArgument`, `LaunchConfiguration`, `PythonExpression`, `IfCondition`, `ExecuteProcess`, and `TimerAction`.

```python
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, TimerAction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node

def generate_launch_description():
    turtlesim_ns = LaunchConfiguration('turtlesim_ns')
    use_provided_red = LaunchConfiguration('use_provided_red')
    new_background_r = LaunchConfiguration('new_background_r')

    return LaunchDescription([
        DeclareLaunchArgument(
            'turtlesim_ns',
            default_value='turtlesim1'
        ),
        DeclareLaunchArgument(
            'use_provided_red',
            default_value='False'
        ),
        DeclareLaunchArgument(
            'new_background_r',
            default_value='200'
        ),
        Node(
            package='turtlesim',
            namespace=turtlesim_ns,
            executable='turtlesim_node',
            name='sim'
        ),
        ExecuteProcess(
            cmd=[[
                'ros2 service call ',
                turtlesim_ns,
                '/spawn ',
                'turtlesim/srv/Spawn ',
                '"{x: 2, y: 2, theta: 0.2}"'
            ]],
            shell=True
        ),
        ExecuteProcess(
            cmd=[[
                'ros2 param set ',
                turtlesim_ns,
                '/sim background_r ',
                '120'
            ]],
            shell=True
        ),
        TimerAction(
            period=2.0,
            actions=[
                ExecuteProcess(
                    condition=IfCondition(
                        PythonExpression([
                            new_background_r,
                            ' == 200',
                            ' and ',
                            use_provided_red
                        ])
                    ),
                    cmd=[[
                        'ros2 param set ',
                        turtlesim_ns,
                        '/sim background_r ',
                        new_background_r
                    ]],
                    shell=True
                ),
            ],
        )
    ])
```

### Including another launch file with arguments

```python
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

IncludeLaunchDescription(
    PythonLaunchDescriptionSource(
        PathJoinSubstitution([
            FindPackageShare('launch_tutorial'),
            'launch',
            'example_substitutions_launch.py'
        ])
    ),
    launch_arguments={
        'turtlesim_ns': 'turtlesim2',
        'use_provided_red': 'True',
        'new_background_r': '200',
    }.items()
)
```

(For XML/YAML children use `FrontendLaunchDescriptionSource` instead of `PythonLaunchDescriptionSource`.)

### XML equivalent

```xml
<?xml version="1.0" encoding="UTF-8"?>
<launch>
  <arg name="turtlesim_ns" default="turtlesim1" />
  <arg name="use_provided_red" default="False" />
  <arg name="new_background_r" default="200" />

  <node pkg="turtlesim" namespace="$(var turtlesim_ns)"
        exec="turtlesim_node" name="sim" />
  <executable cmd="ros2 service call $(var turtlesim_ns)/spawn
                   turtlesim/srv/Spawn '{x: 5, y: 2, theta: 0.2}'" />
  <executable cmd="ros2 param set $(var turtlesim_ns)/sim
                   background_r 120" />
  <timer period="2.0">
    <executable cmd="ros2 param set $(var turtlesim_ns)/sim
                     background_r $(var new_background_r)"
      if="$(eval '$(var new_background_r) == 200 and
           $(var use_provided_red)')" />
  </timer>
</launch>
```

### YAML equivalent

```yaml
%YAML 1.2
---
launch:
  - arg:
      name: "turtlesim_ns"
      default: "turtlesim1"
  - arg:
      name: "use_provided_red"
      default: "False"
  - arg:
      name: "new_background_r"
      default: "200"

  - node:
      pkg: "turtlesim"
      namespace: "$(var turtlesim_ns)"
      exec: "turtlesim_node"
      name: "sim"
  - executable:
      cmd: 'ros2 service call $(var turtlesim_ns)/spawn
            turtlesim/srv/Spawn "{x: 5, y: 2, theta: 0.2}"'
  - executable:
      cmd: "ros2 param set $(var turtlesim_ns)/sim background_r 120"
  - timer:
      period: 2.0
      children:
        - executable:
            cmd: "ros2 param set $(var turtlesim_ns)/sim
                  background_r $(var new_background_r)"
            if: '$(eval "$(var new_background_r) == 200 and
                 $(var use_provided_red)")'
```

### CLI override

```bash
ros2 launch launch_tutorial example_substitutions_launch.py \
  turtlesim_ns:='turtlesim3' \
  use_provided_red:='True' \
  new_background_r:=200
```

---

## Using Event Handlers
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Launch/Using-Event-Handlers.html

Event handlers let you react to lifecycle events of other actions: process started/exited, stdout produced, execution completed, launch shutting down. Handlers are registered with `RegisterEventHandler(<EventHandler>)`.

### Event handler classes (`launch.event_handlers`)

| Handler | Triggered when |
|---|---|
| `OnProcessStart(target_action=..., on_start=[...])` | A target process action begins |
| `OnProcessIO(target_action=..., on_stdout=cb, on_stderr=cb)` | A target writes to stdout/stderr; callback gets a `ProcessIO` event |
| `OnExecutionComplete(target_action=..., on_completion=[...])` | Any action finishes its execution |
| `OnProcessExit(target_action=..., on_exit=[...])` | A process terminates |
| `OnShutdown(on_shutdown=[...])` | The launch system is shutting down |

Lifecycle (`launch_ros.event_handlers.OnStateTransition`) reacts to `lifecycle_msgs` state transitions of a managed node. Common pattern (illustrative):

```python
from launch_ros.event_handlers import OnStateTransition
RegisterEventHandler(OnStateTransition(
    target_lifecycle_node=lc_node,
    goal_state='active',
    entities=[LogInfo(msg='node went active')],
))
```

### Companion action classes

- `LogInfo(msg=...)` — write a console line; `msg` may be a list mixing strings and substitutions.
- `EmitEvent(event=Shutdown(reason='...'))` — push an event into the launch system. `Shutdown` lives in `launch.events`.
- `TimerAction(period=<seconds>, actions=[...])` — defer wrapped actions.
- `ExecuteProcess(cmd=[...], shell=True/False, output='screen', condition=...)` — run an external command.
- `OpaqueFunction(function=fn, args=[], kwargs={})` (from `launch.actions`) — call a Python function with the `LaunchContext`, returning a list of additional actions; useful for logic that needs resolved substitution values.

### Full event-handler example

Demonstrates all five handler types plus `EnvironmentVariable`, `LocalSubstitution('event.reason')` to read the shutdown reason inside `OnShutdown`, and `EmitEvent(event=Shutdown(...))` to terminate the launch from a handler.

```python
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    EmitEvent,
    ExecuteProcess,
    LogInfo,
    RegisterEventHandler,
    TimerAction
)
from launch.conditions import IfCondition
from launch.event_handlers import (
    OnExecutionComplete,
    OnProcessExit,
    OnProcessIO,
    OnProcessStart,
    OnShutdown
)
from launch.events import Shutdown
from launch.substitutions import (
    EnvironmentVariable,
    FindExecutable,
    LaunchConfiguration,
    LocalSubstitution,
    PythonExpression
)
from launch_ros.actions import Node

def generate_launch_description():
    turtlesim_ns = LaunchConfiguration('turtlesim_ns')
    use_provided_red = LaunchConfiguration('use_provided_red')
    new_background_r = LaunchConfiguration('new_background_r')

    turtlesim_ns_launch_arg = DeclareLaunchArgument(
        'turtlesim_ns',
        default_value='turtlesim1'
    )
    use_provided_red_launch_arg = DeclareLaunchArgument(
        'use_provided_red',
        default_value='False'
    )
    new_background_r_launch_arg = DeclareLaunchArgument(
        'new_background_r',
        default_value='200'
    )

    turtlesim_node = Node(
        package='turtlesim',
        namespace=turtlesim_ns,
        executable='turtlesim_node',
        name='sim'
    )
    spawn_turtle = ExecuteProcess(
        cmd=[[
            FindExecutable(name='ros2'),
            ' service call ',
            turtlesim_ns,
            '/spawn ',
            'turtlesim/srv/Spawn ',
            '"{x: 2, y: 2, theta: 0.2}"'
        ]],
        shell=True
    )
    change_background_r = ExecuteProcess(
        cmd=[[
            FindExecutable(name='ros2'),
            ' param set ',
            turtlesim_ns,
            '/sim background_r ',
            '120'
        ]],
        shell=True
    )
    change_background_r_conditioned = ExecuteProcess(
        condition=IfCondition(
            PythonExpression([
                new_background_r,
                ' == 200',
                ' and ',
                use_provided_red
            ])
        ),
        cmd=[[
            FindExecutable(name='ros2'),
            ' param set ',
            turtlesim_ns,
            '/sim background_r ',
            new_background_r
        ]],
        shell=True
    )

    return LaunchDescription([
        turtlesim_ns_launch_arg,
        use_provided_red_launch_arg,
        new_background_r_launch_arg,
        turtlesim_node,
        RegisterEventHandler(
            OnProcessStart(
                target_action=turtlesim_node,
                on_start=[
                    LogInfo(msg='Turtlesim started, spawning turtle'),
                    spawn_turtle
                ]
            )
        ),
        RegisterEventHandler(
            OnProcessIO(
                target_action=spawn_turtle,
                on_stdout=lambda event: LogInfo(
                    msg='Spawn request says "{}"'.format(
                        event.text.decode().strip())
                )
            )
        ),
        RegisterEventHandler(
            OnExecutionComplete(
                target_action=spawn_turtle,
                on_completion=[
                    LogInfo(msg='Spawn finished'),
                    change_background_r,
                    TimerAction(
                        period=2.0,
                        actions=[change_background_r_conditioned],
                    )
                ]
            )
        ),
        RegisterEventHandler(
            OnProcessExit(
                target_action=turtlesim_node,
                on_exit=[
                    LogInfo(msg=(EnvironmentVariable(name='USER'),
                            ' closed the turtlesim window')),
                    EmitEvent(event=Shutdown(
                        reason='Window closed'))
                ]
            )
        ),
        RegisterEventHandler(
            OnShutdown(
                on_shutdown=[LogInfo(
                    msg=['Launch was asked to shutdown: ', LocalSubstitution('event.reason')]
                )]
            )
        ),
    ])
```

Key callback signature notes:
- `on_stdout` / `on_stderr` callbacks receive a `ProcessIO` event with `.text` (bytes). They may return a single action or `None`.
- `on_start`, `on_exit`, `on_completion`, `on_shutdown` accept either a list of actions or a callable returning a list.
- Use `LocalSubstitution('event.<attr>')` to access fields of the triggering event from inside the handler's actions.

---

## Using ROS 2 Launch For Large Projects
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Launch/Using-ROS2-Launch-For-Large-Projects.html

Design principle: top-level launch files should be short and consist mostly of `IncludeLaunchDescription` of subcomponent launch files plus the few parameters that change between deployments. This makes it cheap to swap simulation for hardware, change robot variants, etc.

Reference layout used by the tutorial:

```
launch_tutorial/
├── launch/
│   ├── launch_turtlesim_launch.py
│   ├── turtlesim_world_1_launch.py
│   ├── turtlesim_world_2_launch.py
│   ├── turtlesim_world_3_launch.py
│   ├── broadcaster_listener_launch.py
│   ├── mimic_launch.py
│   ├── fixed_broadcaster_launch.py
│   └── turtlesim_rviz_launch.py
├── config/
│   └── turtlesim.yaml
└── setup.py
```

### Top-level parent launch

```python
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    launch_dir = PathJoinSubstitution([FindPackageShare('launch_tutorial'), 'launch'])
    return LaunchDescription([
        IncludeLaunchDescription(
            PathJoinSubstitution([launch_dir, 'turtlesim_world_1_launch.py'])
        ),
        IncludeLaunchDescription(
            PathJoinSubstitution([launch_dir, 'turtlesim_world_2_launch.py'])
        ),
        IncludeLaunchDescription(
            PathJoinSubstitution([launch_dir, 'broadcaster_listener_launch.py']),
            launch_arguments={'target_frame': 'carrot1'}.items()
        ),
        IncludeLaunchDescription(
            PathJoinSubstitution([launch_dir, 'mimic_launch.py'])
        ),
        IncludeLaunchDescription(
            PathJoinSubstitution([launch_dir, 'fixed_broadcaster_launch.py'])
        ),
        IncludeLaunchDescription(
            PathJoinSubstitution([launch_dir, 'turtlesim_rviz_launch.py'])
        ),
    ])
```

### Inline parameters via `LaunchConfiguration`

```python
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('background_r', default_value='0'),
        DeclareLaunchArgument('background_g', default_value='84'),
        DeclareLaunchArgument('background_b', default_value='122'),
        Node(
            package='turtlesim',
            executable='turtlesim_node',
            name='sim',
            parameters=[{
                'background_r': LaunchConfiguration('background_r'),
                'background_g': LaunchConfiguration('background_g'),
                'background_b': LaunchConfiguration('background_b'),
            }]
        ),
    ])
```

### Parameters from a YAML file

```python
from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='turtlesim',
            executable='turtlesim_node',
            namespace='turtlesim2',
            name='sim',
            parameters=[PathJoinSubstitution([
                FindPackageShare('launch_tutorial'), 'config', 'turtlesim.yaml'])
            ],
        ),
    ])
```

`config/turtlesim.yaml`:

```yaml
/**:
   ros__parameters:
      background_b: 255
      background_g: 86
      background_r: 150
```

The `/**` wildcard applies to every node regardless of namespace/name. Replace with `node_name:` (single token) or `**/node_name:` to scope.

### `GroupAction` + `PushROSNamespace`

`PushROSNamespace` must be the first action inside the group so subsequent actions inherit the namespace.

```python
from launch.actions import GroupAction
from launch_ros.actions import PushROSNamespace

GroupAction(
    actions=[
        PushROSNamespace('turtlesim2'),
        IncludeLaunchDescription(
            PathJoinSubstitution([launch_dir, 'turtlesim_world_2_launch.py'])
        ),
    ]
),
```

`launch_ros.actions.SetParameter` and `launch.actions.SetLaunchConfiguration` are the analogous "scope-wide" setters for parameters and launch configurations respectively when placed inside a `GroupAction`.

### Reusable nodes with arguments

```python
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'target_frame', default_value='turtle1',
            description='Target frame name.',
        ),
        Node(
            package='turtle_tf2_py',
            executable='turtle_tf2_broadcaster',
            name='broadcaster1',
            parameters=[{'turtlename': 'turtle1'}],
        ),
        Node(
            package='turtle_tf2_py',
            executable='turtle_tf2_broadcaster',
            name='broadcaster2',
            parameters=[{'turtlename': 'turtle2'}],
        ),
        Node(
            package='turtle_tf2_py',
            executable='turtle_tf2_listener',
            name='listener',
            parameters=[
                {'target_frame': LaunchConfiguration('target_frame')}
            ],
        ),
    ])
```

### Topic remapping

```python
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='turtlesim',
            executable='mimic',
            name='mimic',
            remappings=[
                ('/input/pose', '/turtle2/pose'),
                ('/output/cmd_vel', '/turtlesim2/turtle1/cmd_vel'),
            ]
        )
    ])
```

### Loading an RViz config

```python
from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', PathJoinSubstitution([
                FindPackageShare('turtle_tf2_py'), 'rviz', 'turtle_rviz.rviz'])],
        ),
    ])
```

### Composing values from `EnvironmentVariable`

`name=` and `default_value=` accept lists that mix substitutions and literals; the launcher concatenates them at runtime.

```python
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import EnvironmentVariable, LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'node_prefix',
            default_value=[EnvironmentVariable('USER'), '_'],
            description='prefix for node name'
        ),
        Node(
            package='turtle_tf2_py',
            executable='fixed_frame_tf2_broadcaster',
            name=[LaunchConfiguration('node_prefix'), 'fixed_broadcaster'],
        ),
    ])
```

### `setup.py` install snippet for launch + config + rviz

```python
import os
from glob import glob
from setuptools import setup

data_files=[
    (os.path.join('share', package_name, 'launch'),
        glob('launch/*')),
    (os.path.join('share', package_name, 'config'),
        glob('config/*.yaml')),
    (os.path.join('share', package_name, 'rviz'),
        glob('config/*.rviz')),
],
```

### URDF / xacro pattern

To feed URDF generated from xacro to `robot_state_publisher`, combine `Command` (run xacro), `FindPackageShare`, and `PathJoinSubstitution`:

```python
from launch import LaunchDescription
from launch.substitutions import Command, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    urdf_file = PathJoinSubstitution([
        FindPackageShare('my_robot_description'), 'urdf', 'robot.urdf.xacro'])
    return LaunchDescription([
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': Command(['xacro ', urdf_file])}],
        ),
    ])
```

---

## Launch File Different Formats (XML / YAML / Python)
**Source**: https://docs.ros.org/en/jazzy/How-To-Guides/Launch-file-different-formats.html

Choice of format is mostly preference, with one important caveat: **use Python whenever you need flexibility you cannot express in XML or YAML** — full scripting, conditional logic via Python, access to launch APIs not exposed by the frontend. The trade-off is that Python files tend to be more verbose.

Equivalent launch files demonstrating arguments, includes (with `push_ros_namespace`), nodes with parameters and remappings, and `--ros-args --log-level` injection.

### XML

```xml
<?xml version="1.0" encoding="UTF-8"?>
<launch>
  <!-- args that can be set from the command line or a default will be used -->
  <arg name="background_r" default="0" />
  <arg name="background_g" default="255" />
  <arg name="background_b" default="0" />
  <arg name="chatter_py_ns" default="chatter/py/ns" />
  <arg name="chatter_xml_ns" default="chatter/xml/ns" />
  <arg name="chatter_yaml_ns" default="chatter/yaml/ns" />

  <!-- include another launch file -->
  <include file="$(find-pkg-share demo_nodes_cpp)/launch/topics/talker_listener_launch.py" />

  <!-- include a Python launch file in the chatter_py_ns namespace-->
  <group>
    <push_ros_namespace namespace="$(var chatter_py_ns)" />
    <include file="$(find-pkg-share demo_nodes_cpp)/launch/topics/talker_listener_launch.py" />
  </group>

  <!-- include an xml launch file in the chatter_xml_ns namespace-->
  <group>
    <push_ros_namespace namespace="$(var chatter_xml_ns)" />
    <include file="$(find-pkg-share demo_nodes_cpp)/launch/topics/talker_listener_launch.xml" />
  </group>

  <!-- include a yaml launch file in the chatter_yaml_ns namespace-->
  <group>
    <push_ros_namespace namespace="$(var chatter_yaml_ns)" />
    <include file="$(find-pkg-share demo_nodes_cpp)/launch/topics/talker_listener_launch.yaml" />
  </group>

  <!-- start a turtlesim_node in the turtlesim1 namespace and use args to set the log level -->
  <node pkg="turtlesim" exec="turtlesim_node" name="sim" namespace="turtlesim1" args="--ros-args --log-level info" />

  <!-- start another turtlesim_node in the turtlesim2 namespace, use ros_args to set the log level, and child elements to set the parameters -->
  <node pkg="turtlesim" exec="turtlesim_node" name="sim" namespace="turtlesim2" ros_args="--log-level warn">
    <param name="background_r" value="$(var background_r)" />
    <param name="background_g" value="$(var background_g)" />
    <param name="background_b" value="$(var background_b)" />
  </node>

  <!-- perform remap so both turtles listen to the same command topic -->
  <node pkg="turtlesim" exec="mimic" name="mimic">
    <remap from="/input/pose" to="/turtlesim1/turtle1/pose" />
    <remap from="/output/cmd_vel" to="/turtlesim2/turtle1/cmd_vel" />
  </node>
</launch>
```

### YAML

```yaml
%YAML 1.2
---
launch:
- arg:
    name: "background_r"
    default: "0"
- arg:
    name: "background_g"
    default: "255"
- arg:
    name: "background_b"
    default: "0"
- arg:
    name: "chatter_py_ns"
    default: "chatter/py/ns"
- arg:
    name: "chatter_xml_ns"
    default: "chatter/xml/ns"
- arg:
    name: "chatter_yaml_ns"
    default: "chatter/yaml/ns"

- include:
    file: "$(find-pkg-share demo_nodes_cpp)/launch/topics/talker_listener_launch.py"

- group:
    - push_ros_namespace:
        namespace: "$(var chatter_py_ns)"
    - include:
        file: "$(find-pkg-share demo_nodes_cpp)/launch/topics/talker_listener_launch.py"

- group:
    - push_ros_namespace:
        namespace: "$(var chatter_xml_ns)"
    - include:
        file: "$(find-pkg-share demo_nodes_cpp)/launch/topics/talker_listener_launch.xml"

- group:
    - push_ros_namespace:
        namespace: "$(var chatter_yaml_ns)"
    - include:
        file: "$(find-pkg-share demo_nodes_cpp)/launch/topics/talker_listener_launch.yaml"

- node:
    pkg: "turtlesim"
    exec: "turtlesim_node"
    name: "sim"
    namespace: "turtlesim1"
    args: "--ros-args --log-level info"

- node:
    pkg: "turtlesim"
    exec: "turtlesim_node"
    name: "sim"
    namespace: "turtlesim2"
    ros_args: "--log-level warn"
    param:
    - name: "background_r"
      value: "$(var background_r)"
    - name: "background_g"
      value: "$(var background_g)"
    - name: "background_b"
      value: "$(var background_b)"

- node:
    pkg: "turtlesim"
    exec: "mimic"
    name: "mimic"
    remap:
    - from: "/input/pose"
      to: "/turtlesim1/turtle1/pose"
    - from: "/output/cmd_vel"
      to: "/turtlesim2/turtle1/cmd_vel"
```

### Python

```python
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node, PushROSNamespace
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    launch_dir = PathJoinSubstitution([FindPackageShare('demo_nodes_cpp'), 'launch', 'topics'])
    return LaunchDescription([
        DeclareLaunchArgument('background_r', default_value='0'),
        DeclareLaunchArgument('background_g', default_value='255'),
        DeclareLaunchArgument('background_b', default_value='0'),
        DeclareLaunchArgument('chatter_py_ns', default_value='chatter/py/ns'),
        DeclareLaunchArgument('chatter_xml_ns', default_value='chatter/xml/ns'),
        DeclareLaunchArgument('chatter_yaml_ns', default_value='chatter/yaml/ns'),

        IncludeLaunchDescription(
            PathJoinSubstitution([launch_dir, 'talker_listener_launch.py'])
        ),

        GroupAction(
            actions=[
                PushROSNamespace('chatter_py_ns'),
                IncludeLaunchDescription(
                    PathJoinSubstitution([launch_dir, 'talker_listener_launch.py'])),
            ]
        ),

        GroupAction(
            actions=[
                PushROSNamespace('chatter_xml_ns'),
                IncludeLaunchDescription(
                    PathJoinSubstitution([launch_dir, 'talker_listener_launch.xml'])),
            ]
        ),

        GroupAction(
            actions=[
                PushROSNamespace('chatter_yaml_ns'),
                IncludeLaunchDescription(
                    PathJoinSubstitution([launch_dir, 'talker_listener_launch.yaml'])),
            ]
        ),

        Node(
            package='turtlesim',
            namespace='turtlesim1',
            executable='turtlesim_node',
            name='sim',
            arguments=['--ros-args', '--log-level', 'info']
        ),

        Node(
            package='turtlesim',
            namespace='turtlesim2',
            executable='turtlesim_node',
            name='sim',
            ros_arguments=['--log-level', 'warn'],
            parameters=[{
                'background_r': LaunchConfiguration('background_r'),
                'background_g': LaunchConfiguration('background_g'),
                'background_b': LaunchConfiguration('background_b'),
            }]
        ),

        Node(
            package='turtlesim',
            executable='mimic',
            name='mimic',
            remappings=[
                ('/input/pose', '/turtlesim1/turtle1/pose'),
                ('/output/cmd_vel', '/turtlesim2/turtle1/cmd_vel'),
            ]
        ),
    ])
```

### Quick syntax cheatsheet

| Feature | XML | YAML | Python |
|---|---|---|---|
| Argument | `<arg name="x" default="y" />` | `- arg: {name: x, default: y}` | `DeclareLaunchArgument('x', default_value='y')` |
| Node | `<node pkg="x" exec="y" name="z" />` | `- node: {pkg: x, exec: y, name: z}` | `Node(package='x', executable='y', name='z')` |
| Parameter | `<param name="x" value="y" />` | `- param: {name: x, value: y}` | `parameters=[{'x': 'y'}]` |
| Remap | `<remap from="x" to="y" />` | `- remap: {from: x, to: y}` | `remappings=[(x, y)]` |
| Push namespace | `<push_ros_namespace namespace="x" />` | `- push_ros_namespace: {namespace: x}` | `PushROSNamespace('x')` |
| Group | `<group>...</group>` | `- group: [...]` | `GroupAction(actions=[...])` |
| Include | `<include file="..." />` | `- include: {file: ...}` | `IncludeLaunchDescription(...)` |
| Conditional | `if="..."` / `unless="..."` | `if:` / `unless:` | `condition=IfCondition(...)` / `UnlessCondition(...)` |
| Read launch arg | `$(var x)` | `$(var x)` | `LaunchConfiguration('x')` |
| Find package | `$(find-pkg-share x)` | `$(find-pkg-share x)` | `FindPackageShare('x')` |
| Eval Python | `$(eval 'expr')` | `$(eval "expr")` | `PythonExpression([...])` |
| Env var | `$(env VAR)` | `$(env VAR)` | `EnvironmentVariable('VAR')` |

CLI override (any format):

```bash
ros2 launch <package_name> <launch_file> background_r:=255
```

---

## Launching Composable Nodes
**Source**: https://docs.ros.org/en/jazzy/How-To-Guides/Launching-composable-nodes.html

Composable nodes run as plugins inside a single host process (the *container*), enabling intra-process zero-copy message passing. Two patterns:

1. **`ComposableNodeContainer`** — declare the container and its initial composable nodes in one shot.
2. **Plain `Node` (a container) + `LoadComposableNodes`** — spin up the container, then load components into it later (or from a separate launch file).

Container executables (in `rclcpp_components`):
- `component_container` — single-threaded executor
- `component_container_mt` — multi-threaded executor (one thread per callback group via the default executor)
- `component_container_isolated` — each composable node gets its own callback executor (isolated)

### `ComposableNodeContainer` — XML

```xml
<?xml version="1.0" encoding="UTF-8"?>
<launch>
  <node_container pkg="rclcpp_components" exec="component_container" name="image_container" namespace="">
    <!-- composable nodes go here -->
  </node_container>
</launch>
```

### `ComposableNodeContainer` — YAML

```yaml
%YAML 1.2
---
launch:
  - node_container:
      pkg: rclcpp_components
      exec: component_container
      name: image_container
      composable_node:
        # composable nodes defined here
```

### `ComposableNodeContainer` — Python

```python
import launch
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode

def generate_launch_description():
    return launch.LaunchDescription([
        ComposableNodeContainer(
            name='image_container',
            namespace='',
            package='rclcpp_components',
            executable='component_container',
            composable_node_descriptions=[
                # ComposableNode instances here
            ],
            output='both',
        ),
    ])
```

### `ComposableNode` description fields

| Field | Meaning |
|---|---|
| `package` | Package providing the component plugin |
| `plugin` | Fully-qualified plugin class (e.g. `image_tools::Cam2Image`) |
| `name` | Node instance name |
| `namespace` | Optional ROS namespace |
| `parameters` | List of dicts or YAML files |
| `remappings` | List of `(from, to)` tuples |
| `extra_arguments` | List of dicts (e.g. `{'use_intra_process_comms': True}`) |

### Single composable node — XML

```xml
<composable_node pkg="image_tools" plugin="image_tools::Cam2Image" name="cam2image">
  <remap from="/image" to="/burgerimage" />
  <param name="width" value="320" />
  <param name="height" value="240" />
  <param name="burger_mode" value="true" />
  <param name="history" value="keep_last" />
  <extra_arg name="use_intra_process_comms" value="true" />
</composable_node>
```

### Single composable node — YAML

```yaml
- pkg: image_tools
  plugin: image_tools::Cam2Image
  name: cam2image
  remap:
    - from: /image
      to: /burgerimage
  param:
    - name: width
      value: 320
    - name: height
      value: 240
    - name: burger_mode
      value: true
    - name: history
      value: keep_last
  extra_arg:
    - name: use_intra_process_comms
      value: true
```

### Single composable node — Python

```python
ComposableNode(
    package='image_tools',
    plugin='image_tools::Cam2Image',
    name='cam2image',
    remappings=[('/image', '/burgerimage')],
    parameters=[{
        'width': 320,
        'height': 240,
        'burger_mode': True,
        'history': 'keep_last'
    }],
    extra_arguments=[{'use_intra_process_comms': True}]
)
```

### Full Python example — container + two components with intra-process comms

```python
import launch
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode

def generate_launch_description():
    """Generate launch description with multiple components."""
    return launch.LaunchDescription([
        ComposableNodeContainer(
            name='image_container',
            namespace='',
            package='rclcpp_components',
            executable='component_container',
            composable_node_descriptions=[
                ComposableNode(
                    package='image_tools',
                    plugin='image_tools::Cam2Image',
                    name='cam2image',
                    remappings=[('/image', '/burgerimage')],
                    parameters=[{
                        'width': 320,
                        'height': 240,
                        'burger_mode': True,
                        'history': 'keep_last'}],
                    extra_arguments=[{'use_intra_process_comms': True}]),
                ComposableNode(
                    package='image_tools',
                    plugin='image_tools::ShowImage',
                    name='showimage',
                    remappings=[('/image', '/burgerimage')],
                    parameters=[{'history': 'keep_last'}],
                    extra_arguments=[{'use_intra_process_comms': True}])
            ],
            output='both',
        ),
    ])
```

### Loading into an existing container — XML

```xml
<?xml version="1.0" encoding="UTF-8"?>
<launch>
  <node pkg="rclcpp_components" exec="component_container" name="image_container" />
  <load_composable_node target="image_container">
    <!-- composable_node definitions here -->
  </load_composable_node>
</launch>
```

### Loading into an existing container — Python

`LoadComposableNodes` calls the container's `~/_container/load_node` service to add components after the container is running. `target_container` is the container's fully-qualified name.

```python
from launch import LaunchDescription
from launch_ros.actions import LoadComposableNodes, Node
from launch_ros.descriptions import ComposableNode

def generate_launch_description():
    return LaunchDescription([
        Node(
            name='image_container',
            package='rclcpp_components',
            executable='component_container',
            output='both',
        ),
        LoadComposableNodes(
            target_container='image_container',
            composable_node_descriptions=[
                ComposableNode(
                    package='image_tools',
                    plugin='image_tools::Cam2Image',
                    name='cam2image',
                    remappings=[('/image', '/burgerimage')],
                    parameters=[
                        {'width': 320, 'height': 240, 'burger_mode': True, 'history': 'keep_last'}
                    ],
                    extra_arguments=[{'use_intra_process_comms': True}],
                ),
                ComposableNode(
                    package='image_tools',
                    plugin='image_tools::ShowImage',
                    name='showimage',
                    remappings=[('/image', '/burgerimage')],
                    parameters=[{'history': 'keep_last'}],
                    extra_arguments=[{'use_intra_process_comms': True}]
                ),
            ],
        )
    ])
```

`use_intra_process_comms: True` enables zero-copy message passing between components in the same process — the main reason to use composition for high-bandwidth pipelines (camera, lidar, point cloud).

---

## Node Arguments (ROS args via the command line)
**Source**: https://docs.ros.org/en/jazzy/How-To-Guides/Node-arguments.html

Every ROS-aware executable accepts a `--ros-args` argv section that is parsed by `rclcpp`/`rclpy` rather than the user code. Anything before `--ros-args` (or after a bare `--`) is treated as user argv.

```bash
ros2 run <pkg> <executable> [user_args] --ros-args [ros_args] [-- more_user_args]
```

### Remapping — `-r from:=to`

`-r`/`--remap` rewrites topic, service, action, node, or namespace names. Magic names:
- `__node` — the node name
- `__ns` — the namespace (must start with `/`)

```bash
ros2 run demo_nodes_cpp talker --ros-args -r __ns:=/demo -r __node:=my_talker -r chatter:=my_topic
```

For multi-node executables (e.g. composition), prefix the remap with the source node name:

```bash
ros2 run composition manual_composition --ros-args -r talker:__node:=my_talker -r my_talker:chatter:=my_topic
```

All remaps are *static* — applied once at startup; no dynamic remap after the node is alive.

### Parameters — `-p name:=value`

```bash
ros2 run demo_nodes_cpp parameter_blackboard --ros-args \
  -p some_int:=42 \
  -p "a_string:=Hello world" \
  -p "some_lists.some_integers:=[1, 2, 3, 4]"
```

Quote whenever the value contains spaces or YAML brackets. Nested keys use dot notation.

### Parameters from YAML — `--params-file`

```bash
ros2 run demo_nodes_cpp parameter_blackboard --ros-args --params-file demo_params.yaml
```

YAML supports per-node sections plus wildcards (`*` = single token, `**` = multiple tokens):

```yaml
parameter_blackboard:
    ros__parameters:
        some_int: 42
        a_string: "Hello world"

/**:
  ros__parameters:
    wildcard_full: "Any namespace and node"
```

### Logging — `--log-level`

Set the default severity for the process or scope per logger name:

```bash
ros2 run demo_nodes_cpp talker --ros-args --log-level debug
ros2 run demo_nodes_cpp talker --ros-args --log-level talker:=debug --log-level rcl:=warn
```

Other logging knobs:
- `--log-file-name <prefix>` — log file prefix
- `--enable-rosout-logs` / `--disable-rosout-logs`
- `--enable-stdout-logs` / `--disable-stdout-logs`

### Node + namespace shortcut

```bash
ros2 run demo_nodes_cpp talker --ros-args -r __node:=my_talker -r __ns:=/demo
```

### Multiple `--ros-args` sections / `--` separator

You can repeat `--ros-args` and use a bare `--` to flip back to user argv:

```bash
ros2 run my_pkg my_node user_arg_1 --ros-args -p foo:=1 -- user_arg_2 --ros-args -p bar:=2
```

### Equivalence inside `Node(...)` in launch files

| CLI form | Launch field |
|---|---|
| `-r from:=to` | `remappings=[('from', 'to')]` |
| `-r __node:=name` | `name='name'` |
| `-r __ns:=/ns` | `namespace='/ns'` |
| `-p key:=value` | `parameters=[{'key': value}]` |
| `--params-file file.yaml` | `parameters=['/abs/path/file.yaml']` |
| `--log-level debug` | `arguments=['--ros-args', '--log-level', 'debug']` or `ros_arguments=['--log-level', 'debug']` |

`ros2 launch` honours the same forwarding: when you put `--ros-args` inside `arguments=[...]` (or use `ros_arguments=[...]`), they are passed through to the executable verbatim. CLI-style overrides at `ros2 launch <pkg> <file> key:=value` set *launch arguments*, not ROS args — to forward to a node use the patterns above.
