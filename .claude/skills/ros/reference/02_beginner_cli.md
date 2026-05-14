# Beginner: CLI Tools (ROS 2 Jazzy Tutorials)

> Source index: https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools.html

This document summarizes the entire **Beginner: CLI Tools** tutorial track for ROS 2 Jazzy. The goal is that the workflow can be reproduced from this file alone, only opening the original page if a deeper diagram is needed.

## Section Index
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools.html

The Beginner: CLI Tools section provides foundational ROS 2 command-line interface skills for newcomers. It targets ROS 2 Jazzy (with newer "Kilted" release noted as latest alternative). All tutorials emphasize CLI proficiency before progressing to client libraries.

Tutorial sequence (in order):
1. Configuring environment - shell environment setup
2. Using `turtlesim`, `ros2`, and `rqt` - simulator and GUI introduction
3. Understanding nodes - fundamental computational building blocks
4. Understanding topics - publish/subscribe communication
5. Understanding services - request/response communication
6. Understanding parameters - runtime configuration management
7. Understanding actions - long-running task execution
8. Using `rqt_console` to view logs - log visualization/debugging
9. Launching nodes - deploying multiple nodes simultaneously
10. Recording and playing back data - `ros2 bag` workflow

Prerequisite: ROS 2 Jazzy installed (binary or from source). Each tutorial assumes the previous one was completed.

---

## 1. Configuring Environment
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools/Configuring-ROS2-Environment.html

Teaches how to source the ROS 2 install so that `ros2` commands and packages are discoverable in every new shell, plus how to scope discovery via `ROS_DOMAIN_ID` and `ROS_AUTOMATIC_DISCOVERY_RANGE`.

### Source the setup files (per-shell)
Linux (bash):
```bash
source /opt/ros/jazzy/setup.bash
```
macOS:
```bash
. ~/ros2_install/ros2-osx/setup.bash
```
Windows (cmd):
```bat
call C:\dev\ros2\local_setup.bat
```
For zsh/sh swap the `.bash` extension as needed (`setup.sh`, `setup.zsh`).

### Auto-source on every new shell
Linux/macOS bash:
```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
```
macOS bash profile:
```bash
echo "source ~/ros2_install/ros2-osx/setup.bash" >> ~/.bash_profile
```
Windows PowerShell — create `C:\Users\<You>\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1` containing:
```powershell
C:\dev\ros2_jazzy\local_setup.ps1
```
Then unblock execution:
```powershell
Unblock-File C:\dev\ros2_jazzy\local_setup.ps1
```

### Verify environment variables
Linux/macOS:
```bash
printenv | grep -i ROS
```
Windows:
```cmd
set | findstr -i ROS
```
Expected variables include:
```
ROS_VERSION=2
ROS_PYTHON_VERSION=3
ROS_DISTRO=jazzy
```

### `ROS_DOMAIN_ID` (isolate ROS graph)
Temporary (current shell):
```bash
export ROS_DOMAIN_ID=<your_domain_id>
```
Persist (Linux/macOS):
```bash
echo "export ROS_DOMAIN_ID=<your_domain_id>" >> ~/.bashrc
```
Windows:
```cmd
set ROS_DOMAIN_ID=<your_domain_id>
setx ROS_DOMAIN_ID <your_domain_id>
```
Recommended range: 0-101 (avoiding ephemeral port collisions).

### `ROS_AUTOMATIC_DISCOVERY_RANGE`
Limits which peers can discover each other (e.g. `LOCALHOST`, `SUBNET`, `OFF`, `SYSTEM_DEFAULT`). Useful in classroom or shared-network environments to avoid cross-talk between students/robots.

Common error: forgetting to source ROS in a new terminal — `ros2: command not found`. Fix by sourcing or adding to `~/.bashrc`.

---

## 2. Using turtlesim, ros2, and rqt
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools/Introducing-Turtlesim/Introducing-Turtlesim.html

Installs the `turtlesim` package (a lightweight 2-D simulator) and `rqt` (a GUI for ROS introspection), then demonstrates running nodes and calling services.

### Install turtlesim and rqt (Ubuntu)
```bash
sudo apt update
sudo apt install ros-jazzy-turtlesim
```
```bash
sudo apt update
sudo apt install ros-jazzy-rqt ros-jazzy-rqt-common-plugins
```

### Inspect a package's executables
```bash
ros2 pkg executables turtlesim
```
Output lists: `draw_square`, `mimic`, `turtle_teleop_key`, `turtlesim_node`.

### Run the simulator and teleop
Terminal 1:
```bash
ros2 run turtlesim turtlesim_node
```
Opens a blue window with `turtle1` in the center. The console prints the turtle's name and starting pose.

Terminal 2:
```bash
ros2 run turtlesim turtle_teleop_key
```
Use arrow keys / `G|B|V|C|D|E|R|T` to drive `turtle1`. Console shows key bindings.

### List the running graph
```bash
ros2 node list
ros2 topic list
ros2 service list
ros2 action list
```

### rqt
```bash
rqt
```
If plugins don't appear:
```bash
rqt --force-discover
```
Navigate to **Plugins > Services > Service Caller** to call any active service from a GUI.

### Key services exercised
- `/spawn` (`turtlesim/srv/Spawn`): create a new turtle at `(x, y, theta)` with a chosen name (e.g. `turtle2`). Returns the assigned name.
- `/turtle1/set_pen` (`turtlesim/srv/SetPen`): change pen color (`r`, `g`, `b` 0-255), `width`, and `off` (0/1).

### Drive the spawned `turtle2` by remapping
```bash
ros2 run turtlesim turtle_teleop_key --ros-args --remap turtle1/cmd_vel:=turtle2/cmd_vel --remap turtle1/rotate_absolute:=turtle2/rotate_absolute
```

### Shutdown
- `Ctrl+C` in the simulator terminal to stop `turtlesim_node`.
- `q` in the teleop terminal to exit `turtle_teleop_key`.

---

## 3. Understanding Nodes
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools/Understanding-ROS2-Nodes/Understanding-ROS2-Nodes.html

Defines a *node* as a single-purpose process that communicates via topics, services, actions, and parameters. Introduces `ros2 run`, `ros2 node list`, `ros2 node info`, and node-name remapping.

### `ros2 run` — start an executable from a package
```
ros2 run <package_name> <executable_name>
```
Examples:
```bash
ros2 run turtlesim turtlesim_node
ros2 run turtlesim turtle_teleop_key
```

### `ros2 node list` — list active node names
```bash
ros2 node list
```
Initial output (turtlesim only): `/turtlesim`.
After teleop also runs: `/turtlesim` and `/teleop_turtle`.

### Remap the node name at startup
```bash
ros2 run turtlesim turtlesim_node --ros-args --remap __node:=my_turtle
```
`ros2 node list` then shows `/my_turtle`, `/turtlesim`, `/teleop_turtle` (multiple turtlesim nodes can coexist if their node names differ).

### `ros2 node info` — inspect a node
```
ros2 node info <node_name>
```
Example:
```bash
ros2 node info /my_turtle
```
Returns the node's Subscribers, Publishers, Service Servers, Service Clients, Action Servers, and Action Clients (with the corresponding interface types).

### Concept callouts
- "Each node should be responsible for a single, modular purpose."
- The `__node:=` special remap renames a node; topic remaps use `topic1:=topic2` form.
- Namespace behavior: `ros2 run ... --ros-args -r __ns:=/<ns>` puts the node and its relative topics under `/<ns>`.

---

## 4. Understanding Topics
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools/Understanding-ROS2-Topics/Understanding-ROS2-Topics.html

Covers the publish/subscribe transport: introspection (`list`, `info`, `echo`, `hz`, `bw`, `find`), publishing from CLI (`pub`), message inspection (`interface show`), and `rqt_graph` visualization.

### Visualize the graph
Inside `rqt`: **Plugins > Introspection > Node Graph**, or:
```bash
ros2 run rqt_graph rqt_graph
```
Uncheck "Debug" / "Hide" boxes to see hidden topics and nodes.

### `ros2 topic list`
```bash
ros2 topic list
```
With types:
```bash
ros2 topic list -t
# /turtle1/cmd_vel [geometry_msgs/msg/Twist]
```

### `ros2 topic echo`
```bash
ros2 topic echo <topic_name>
# e.g.
ros2 topic echo /turtle1/cmd_vel
```
Streams the data as YAML in real time.

### `ros2 topic info` (counts) and `--verbose` / `-v` (QoS)
```bash
ros2 topic info /turtle1/cmd_vel
ros2 topic info /turtle1/cmd_vel --verbose
```
Verbose output enumerates each endpoint's node name, namespace, GID, and full QoS profile (reliability, history depth, durability, lifespan, deadline, liveliness).

### `ros2 topic hz` and `ros2 topic bw`
```bash
ros2 topic hz /turtle1/pose
# average rate: 59.354
ros2 topic bw /turtle1/pose
# 1.51 KB/s from 62 messages
```

### `ros2 topic find`
```bash
ros2 topic find geometry_msgs/msg/Twist
# /turtle1/cmd_vel
```

### `ros2 interface show` — inspect a message type
```bash
ros2 interface show geometry_msgs/msg/Twist
```
Shows nested `Vector3 linear` and `Vector3 angular`, each with `float64 x y z`.

### `ros2 topic pub` — publish from the CLI
General form:
```
ros2 topic pub <topic_name> <msg_type> '<args (YAML)>'
```
Drive the turtle:
```bash
ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 2.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 1.8}}"
```
Continuous at 1 Hz:
```bash
ros2 topic pub --rate 1 /turtle1/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 2.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 1.8}}"
```
Empty/default message at 1 Hz:
```bash
ros2 topic pub /turtle1/cmd_vel geometry_msgs/msg/Twist
```
Useful flags:
- `--once` — publish exactly one message and exit.
- `-w <N>` — wait for N matched subscriptions before publishing.
- `--rate <Hz>` — publish at the given rate.
- `--keep-alive` — hold the publisher open after the last message.
- `--qos-reliability {reliable|best_effort}`, `--qos-durability {volatile|transient_local}`, `--qos-history {keep_last|keep_all}`, `--qos-depth <N>` — override QoS at publish time.

### Auto-timestamp shortcuts
Use `header: "auto"` for any `std_msgs/msg/Header` field and the literal `"now"` for any `builtin_interfaces/msg/Time` field. Example:
```bash
ros2 topic pub /pose geometry_msgs/msg/PoseStamped '{header: "auto", pose: {position: {x: 1.0, y: 2.0, z: 3.0}}}'
```

### Message types referenced
- `geometry_msgs/msg/Twist`
- `turtlesim/msg/Pose`
- `geometry_msgs/msg/PoseStamped` (for the auto-timestamp example)

---

## 5. Understanding Services
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools/Understanding-ROS2-Services/Understanding-ROS2-Services.html

Services are synchronous request/response calls. The tutorial shows discovery (`list`, `type`, `find`, `info`), introspection (`interface show`), and invocation (`call`, optional `echo`).

### `ros2 service list`
```bash
ros2 service list
```
With types:
```bash
ros2 service list -t
# /clear [std_srvs/srv/Empty]
# /kill [turtlesim/srv/Kill]
# /spawn [turtlesim/srv/Spawn]
# /turtle1/set_pen [turtlesim/srv/SetPen]
# /turtle1/teleport_absolute [turtlesim/srv/TeleportAbsolute]
# /turtle1/teleport_relative [turtlesim/srv/TeleportRelative]
```

### `ros2 service type`
```bash
ros2 service type /clear
# std_srvs/srv/Empty
```

### `ros2 service info`
```bash
ros2 service info /clear
# Type: std_srvs/srv/Empty
# Clients count: 0
# Services count: 1
```

### `ros2 service find`
```bash
ros2 service find std_srvs/srv/Empty
# /clear
# /reset
```

### `ros2 interface show` for services
```bash
ros2 interface show std_srvs/srv/Empty
# (request)
# ---
# (response)

ros2 interface show turtlesim/srv/Spawn
# float32 x
# float32 y
# float32 theta
# string name
# ---
# string name
```
The `---` separates request fields (above) from response fields (below).

### `ros2 service call`
General form:
```
ros2 service call <service_name> <service_type> "<request args (YAML)>"
```
No-arg call:
```bash
ros2 service call /clear std_srvs/srv/Empty
```
With args:
```bash
ros2 service call /spawn turtlesim/srv/Spawn "{x: 2, y: 2, theta: 0.2, name: ''}"
# response:
# turtlesim.srv.Spawn_Response(name='turtle2')
```

### `ros2 service echo` (introspection)
```bash
ros2 service echo /add_two_ints
```
Streams request/response pairs when service introspection is enabled on the server.

### Service types referenced
- `std_srvs/srv/Empty`
- `turtlesim/srv/Spawn`, `turtlesim/srv/Kill`, `turtlesim/srv/SetPen`, `turtlesim/srv/TeleportAbsolute`, `turtlesim/srv/TeleportRelative`
- `example_interfaces/srv/AddTwoInts` (echo example)

---

## 6. Understanding Parameters
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools/Understanding-ROS2-Parameters/Understanding-ROS2-Parameters.html

Parameters are per-node configuration values (typed: bool, int, float, string, arrays). The tutorial covers listing, getting, setting, describing, dumping, and loading them, plus how to seed them at node launch via `--params-file`.

### `ros2 param list`
```bash
ros2 param list
```
Shows parameters grouped by node, e.g. under `/turtlesim`: `background_b`, `background_g`, `background_r`, `qos_overrides./parameter_events.publisher.depth`, `use_sim_time`, etc.

### `ros2 param get`
```
ros2 param get <node_name> <parameter_name>
```
Example:
```bash
ros2 param get /turtlesim background_g
# Integer value is: 86
```

### `ros2 param set`
```
ros2 param set <node_name> <parameter_name> <value>
```
Example (changes the canvas to red on the next /clear):
```bash
ros2 param set /turtlesim background_r 150
```
Set values are session-only; they revert when the node restarts.

### `ros2 param describe`
```bash
ros2 param describe /turtlesim background_r
```
Returns the parameter descriptor (type, description, range, read-only flag).

### `ros2 param dump` — snapshot a node's params to YAML
```bash
ros2 param dump /turtlesim
ros2 param dump /turtlesim > turtlesim.yaml
```
The YAML structure is:
```yaml
/turtlesim:
  ros__parameters:
    background_b: 255
    background_g: 86
    background_r: 150
    use_sim_time: false
```
Optional flag: `--output-dir <dir>` to write the file to a specific directory.

### `ros2 param load` — apply a YAML file to a running node
```bash
ros2 param load /turtlesim turtlesim.yaml
```
Read-only parameters (e.g. `qos_overrides.*`) cannot be changed after node startup, only at launch.

### Seed parameters at node startup
```bash
ros2 run <package> <executable> --ros-args --params-file <file_name>
```
Example:
```bash
ros2 run turtlesim turtlesim_node --ros-args --params-file turtlesim.yaml
```
This is the only way to set read-only parameters.

### Notable parameters
- Common: `use_sim_time`, `qos_overrides.*` (read-only).
- `/turtlesim`: `background_r`, `background_g`, `background_b` (RGB 0-255).
- `/teleop_turtle`: `scale_linear`, `scale_angular`.

---

## 7. Understanding Actions
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools/Understanding-ROS2-Actions/Understanding-ROS2-Actions.html

Actions are long-running, cancelable, feedback-emitting tasks (goal -> feedback stream -> result). Built on top of topics and services. The tutorial uses `/turtle1/rotate_absolute`.

### Discover the action via `ros2 node info`
For the server (`/turtlesim`) and client (`/teleop_turtle`):
```bash
ros2 node info /turtlesim
# ...
# Action Servers:
#   /turtle1/rotate_absolute: turtlesim/action/RotateAbsolute

ros2 node info /teleop_turtle
# ...
# Action Clients:
#   /turtle1/rotate_absolute: turtlesim/action/RotateAbsolute
```

### `ros2 action list`
```bash
ros2 action list
# /turtle1/rotate_absolute
```
With types:
```bash
ros2 action list -t
# /turtle1/rotate_absolute [turtlesim/action/RotateAbsolute]
```

### `ros2 action type`
```bash
ros2 action type /turtle1/rotate_absolute
# turtlesim/action/RotateAbsolute
```

### `ros2 action info`
```bash
ros2 action info /turtle1/rotate_absolute
# Action: /turtle1/rotate_absolute
# Action clients: 1
#     /teleop_turtle
# Action servers: 1
#     /turtlesim
```

### `ros2 interface show` for actions
```bash
ros2 interface show turtlesim/action/RotateAbsolute
# # The desired heading in radians
# float32 theta
# ---
# # The angular displacement in radians to the starting position
# float32 delta
# ---
# # The remaining rotation in radians
# float32 remaining
```
Three sections, separated by `---`: **goal**, **result**, **feedback**.

### `ros2 action send_goal`
General form:
```
ros2 action send_goal <action_name> <action_type> "<goal args (YAML)>"
```
Basic call:
```bash
ros2 action send_goal /turtle1/rotate_absolute turtlesim/action/RotateAbsolute "{theta: 1.57}"
# Waiting for an action server to become available...
# Sending goal:
#    theta: 1.57
# Goal accepted with ID: f8db8f44410849eaa93d3feb747dd444
# Result:
#   delta: -1.568000316619873
# Goal finished with status: SUCCEEDED
```
With live feedback:
```bash
ros2 action send_goal /turtle1/rotate_absolute turtlesim/action/RotateAbsolute "{theta: -1.57}" --feedback
# Sending goal:
#    theta: -1.57
# Goal accepted with ID: e6092c831f994afda92f0086f220da27
# Feedback:
#   remaining: -3.1268222332000732
# Feedback:
#   remaining: -3.1108222007751465
# Result:
#   delta: 3.1200008392333984
# Goal finished with status: SUCCEEDED
```

### Concepts called out
- Action types are written `package_name/action/ActionName`.
- Goal arguments use YAML, exactly like topics/services.
- Each goal gets a unique UUID.
- Goals can be canceled (in `turtle_teleop_key`, the `F` key cancels). Servers may also abort goals.
- Feedback streams continuously until the result is delivered.

---

## 8. Using rqt_console to View Logs
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools/Using-Rqt-Console/Using-Rqt-Console.html

`rqt_console` is a GUI for inspecting log messages. The tutorial shows how to drive a turtle into a wall to generate `WARN` messages, then how to filter and re-launch the node at a different log level.

### Launch the console
```bash
ros2 run rqt_console rqt_console
```
Three panes: the upper area lists log messages; the middle area applies severity exclusions (use `+` to add filters); the lower area highlights messages whose text matches a query.

### Generate logs
Start the simulator (Terminal 1):
```bash
ros2 run turtlesim turtlesim_node
```
Drive the turtle into a wall (Terminal 2):
```bash
ros2 topic pub -r 1 /turtle1/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 2.0, y: 0.0, z: 0.0}, angular: {x: 0.0,y: 0.0,z: 0.0}}"
```
Repeated `Warn` messages appear in `rqt_console`.

### Severity levels (lowest verbosity at the top)
1. **Fatal** — process will terminate.
2. **Error** — significant malfunction.
3. **Warn** — unexpected/non-ideal but recoverable behavior.
4. **Info** — normal operational events (default level shown).
5. **Debug** — step-by-step execution detail.

By default `rqt_console` (and ROS in general) displays `Info` and higher.

### Set log level at launch
```bash
ros2 run turtlesim turtlesim_node --ros-args --log-level WARN
```
The simulator no longer prints `INFO` messages; only `WARN` and above appear in the console.

---

## 9. Launching Nodes
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools/Launching-Multiple-Nodes/Launching-Multiple-Nodes.html

Launch files start and configure several nodes from a single command, eliminating per-terminal `ros2 run` calls. The example uses `turtlesim/multisim.launch.py`, which spawns two `turtlesim_node` processes in separate namespaces.

### Run the launch file
```bash
ros2 launch turtlesim multisim.launch.py
```
Two `turtlesim` windows open. The launch file places one node under namespace `turtlesim1` and the other under `turtlesim2`, both with `output='screen'`.

### Drive each turtle (separate terminals)
Terminal 2 — first turtle (counter-clockwise circle):
```bash
ros2 topic pub /turtlesim1/turtle1/cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 2.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 1.8}}"
```
Terminal 3 — second turtle (clockwise circle):
```bash
ros2 topic pub /turtlesim2/turtle1/cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 2.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: -1.8}}"
```

### Concept callouts
- Each node lives in its own namespace, so default topics like `/turtle1/cmd_vel` become `/<ns>/turtle1/cmd_vel`.
- Launch files are Python (also XML/YAML supported in later tutorials) and can configure remappings, parameters, namespaces, and lifecycle behavior in one place.

---

## 10. Recording and Playing Back Data
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools/Recording-And-Playing-Back-Data/Recording-And-Playing-Back-Data.html

`ros2 bag` records topic traffic (and optionally services) to disk and replays it later. Useful for capturing real-robot data and replaying it offline.

### Install (if not present)
```bash
sudo apt install ros-jazzy-ros2bag \
                 ros-jazzy-rosbag2-storage-default-plugins \
                 ros-jazzy-rosbag2-storage-mcap \
                 sqlite3
```
Default storage is `mcap` on Jazzy; `sqlite3` is also available.

### Set up a working directory
```bash
mkdir bag_files
cd bag_files
```
All bags are written into the current directory unless `-o` is given.

### Record a single topic
With `turtlesim_node` and `turtle_teleop_key` already running:
```bash
ros2 bag record /turtle1/cmd_vel
```
Console prints something like `Opened database 'rosbag2_2019_10_11-05_18_45'` and reports each subscription. Stop with `Ctrl+C`.

### Record multiple topics, custom name
```bash
ros2 bag record -o subset /turtle1/cmd_vel /turtle1/pose
```
`-o subset` -> the bag directory is named `subset` (file inside is e.g. `subset.mcap`).

### Record all topics
```bash
ros2 bag record -a
# or
ros2 bag record --all
```

### Record services
```bash
ros2 bag record --service /add_two_ints
ros2 bag record --all-services
```

### Choose a storage backend
```bash
ros2 bag record --storage mcap /turtle1/cmd_vel
ros2 bag record --storage sqlite3 /turtle1/cmd_vel
```

### Inspect a bag
```bash
ros2 bag info <bag_directory>
ros2 bag info subset
```
Output includes `Files: subset.mcap`, `Storage id`, `Duration: 48.47s`, `Messages: 3013`, start/end timestamps, and a per-topic breakdown (count, type, serialization format).

### Play a bag
First close the teleop node so the recorded `cmd_vel` messages drive the simulator without competition, then:
```bash
ros2 bag play subset
```
Replay services as well:
```bash
ros2 bag play --publish-service-requests <bag_directory>
```

### Verify with topic/service tools
```bash
ros2 topic echo /turtle1/cmd_vel
ros2 topic hz /turtle1/pose
ros2 service echo --flow-style /add_two_ints
```

### Topics/types referenced
- `/turtle1/cmd_vel` (`geometry_msgs/msg/Twist`)
- `/turtle1/pose` (`turtlesim/msg/Pose`)
- `/add_two_ints` (`example_interfaces/srv/AddTwoInts`)
