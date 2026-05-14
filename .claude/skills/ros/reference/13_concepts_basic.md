# Basic Concepts (ROS 2 Jazzy)

> Source index: https://docs.ros.org/en/jazzy/Concepts/Basic.html

These pages establish the canonical vocabulary used throughout the rest of the
ROS 2 documentation. Every term, mental model, and architectural assumption
elsewhere in the docs (and in `rclcpp`/`rclpy` API reference) is grounded in
the definitions on these eleven pages. Read this file first when a higher-level
doc references "the ROS graph", "discovery", "QoS-driven delivery", "the goal
state machine", "declared parameters", etc., and the meaning is unclear.

---

## Concepts (umbrella index)
**Source**: https://docs.ros.org/en/jazzy/Concepts.html

The Concepts hub frames "Conceptual overviews provide relatively high-level,
general background information about key aspects of ROS 2." It is organized
into three difficulty tiers, each a directory of focused subpages:

- **Basic Concepts** — Nodes, Discovery, Interfaces, Topics, Services,
  Actions, Parameters, Introspection with command line tools, Launch, Client
  libraries. (Covered in this file.)
- **Intermediate Concepts** — `ROS_DOMAIN_ID`, Different ROS 2 middleware
  vendors, Logging and logger configuration, Quality of Service settings,
  Executors, Topic statistics, Overview and usage of RQt, Composition,
  Cross-compilation, ROS 2 Security, Tf2.
- **Advanced Concepts** — The build system, Internal ROS 2 interfaces, ROS 2
  middleware implementations.

The page also points at the **ROS 2 citations** section (`Citations.html`) for
academic-style references to deeper material.

---

## Basic Concepts (index)
**Source**: https://docs.ros.org/en/jazzy/Concepts/Basic.html

This index opens with the canonical one-liner definition of ROS 2: a
middleware "based on a strongly-typed, anonymous publish/subscribe mechanism
that allows for message passing between different processes." Two ideas are
emphasized:

1. **Strong typing** — every channel carries a fixed message type and the
   middleware refuses to connect peers whose types don't match.
2. **Anonymous pub/sub** — publishers and subscribers find each other through
   topic names; neither needs to know the other's identity, which is what
   enables hot-swapping nodes at runtime.

The page then notes that the **ROS graph** — the live network of running nodes
and the connections between them — is the central object of study, and
enumerates the nine (effectively ten, counting the launch + client libraries
split) basic-concept subpages: Nodes, Discovery, Interfaces, Topics, Services,
Actions, Parameters, Introspection with command line tools, Launch, Client
libraries.

---

## About Nodes
**Source**: https://docs.ros.org/en/jazzy/Concepts/Basic/About-Nodes.html

**Mental model.** A node is the basic computational unit of ROS 2 — one
participant in the distributed graph that performs a single logical function
(e.g., "drive the LIDAR", "fuse odometry", "run the planner"). Nodes are
strictly *graph participants*, not OS-level objects: a node uses a client
library to communicate with peer nodes, but the node itself is independent of
whatever process / executable / thread is hosting it.

**Defined terms.**
- **Node** — a participant in the ROS 2 graph that uses a client library to
  communicate with other nodes.
- **Client library** — the language-specific API (rclcpp, rclpy, ...) that
  lets user code create a node and own publishers/subscribers/clients/etc.
- **ROS 2 graph** — the collective of all live nodes and the channels
  (topics, services, actions, parameter services) connecting them.
- **Topic / Service / Action / Parameter** — the four communication
  primitives a node can expose; each has its own concept page.
- **Discovery** — the distributed handshake that brings nodes into each
  other's view of the graph.

**Node ↔ executable ↔ process ↔ graph.** The page is deliberate that nodes
"can communicate with other nodes within the same process, in a different
process, or on a different machine." This is the ROS 2 invariant that:

- one process may host **many** nodes (this is what *Composition* in the
  Intermediate concepts is about),
- one machine may host many processes,
- the graph spans machines transparently once discovery succeeds.

A typical node is described as "a complex combination of publishers,
subscribers, service servers, service clients, action servers, and action
clients, all at the same time." There is no expectation that a node owns only
one publisher or only one subscriber.

**Lifecycle.** The basic page does not introduce managed/lifecycle nodes
(state machine: unconfigured → inactive → active → finalized); that lives
under intermediate/advanced material and `ros2 lifecycle`. A plain node is
"alive" from `create_node` to destruction.

**No CLI examples on this page** — it is purely conceptual. Cross-references
go to the sibling pages: About-Client-Libraries, About-Topics, About-Services,
About-Actions, About-Parameters, About-Discovery, About-Command-Line-Tools.

---

## About Discovery
**Source**: https://docs.ros.org/en/jazzy/Concepts/Basic/About-Discovery.html

**Mental model.** Discovery is the *automatic, continuous* process by which
nodes learn of one another's existence so the middleware can wire up
publishers to subscribers (and clients to servers). It runs in three phases:

1. When a node comes up, it advertises its presence to every other node in
   the same ROS domain.
2. It periodically re-advertises so it can be picked up by nodes that came
   online later.
3. When it goes down, it notifies the others so connections can be torn
   down cleanly.

**Defined / referenced terms.**
- **ROS domain** — the logical group of nodes that can see each other,
  selected via `ROS_DOMAIN_ID` (default 0). Two nodes on different domain
  IDs are mutually invisible regardless of network reachability.
- **QoS compatibility** — even after discovery, "nodes will only establish
  connections with other nodes if they have compatible Quality of Service
  settings." Mismatched QoS (e.g., a `RELIABLE` subscriber against a
  `BEST_EFFORT` publisher) is silent failure: the connection simply never
  forms. (Details live on the Intermediate QoS page.)

**What this page deliberately does not cover.** The basic page is a
high-level summary and explicitly defers to other material for:

- The Simple Discovery Protocol (SDP) — the default DDS-level mechanism that
  rides UDP multicast.
- `ROS_AUTOMATIC_DISCOVERY_RANGE` (e.g., `OFF`, `LOCALHOST`, `SUBNET`,
  `SYSTEM_DEFAULT`) and its interaction with multicast vs. unicast.
- Static peer lists and discovery-server configurations used to bypass
  multicast on locked-down networks.
- Firewall implications (multicast must not be blocked between hosts; if it
  is, you fall back to a discovery server or static peers).

These are covered by the Intermediate **`ROS_DOMAIN_ID`** page and the
middleware-vendor pages; this concept page just establishes that discovery
exists, that it's domain-scoped, and that QoS compatibility is the second
gate.

**References from the page.** Links out to the QoS tutorial, the
talker–listener demo, and the Ubuntu development setup guide (for verifying
that multicast works on the host).

---

## About Interfaces
**Source**: https://docs.ros.org/en/jazzy/Concepts/Basic/About-Interfaces.html

**Mental model.** An *interface* is a strongly-typed contract written in a
small IDL and compiled by `rosidl` into language-specific structs/classes,
so that any two nodes — regardless of language — can exchange the same
binary payload. ROS applications "typically communicate through interfaces
of one of three types: topics, services, or actions", each backed by its
own file extension.

**The three interface files.**

- **`.msg`** — one-way data carried over a topic. Body is just a list of
  fields:
  ```
  int32 my_int
  string my_string
  geometry_msgs/PoseStamped pose
  ```
- **`.srv`** — request/response carried over a service. Two `.msg`-shaped
  blocks separated by `---`:
  ```
  int8 FOO=1
  int8 foobar
  ---
  uint32 SECRET=123456
  uint32 result
  ```
- **`.action`** — goal/result/feedback for a long-running action. Three
  blocks separated by `---`:
  ```
  int32 order
  ---
  int32[] sequence
  ---
  int32[] sequence
  ```
  (The Fibonacci example.)

**Primitive built-in types** and their language mappings:

| ROS IDL    | C++                | Python | DDS              |
|------------|--------------------|--------|------------------|
| `bool`     | `bool`             | `bool` | `boolean`        |
| `byte`     | `uint8_t`          | `bytes`| `octet`          |
| `char`     | `char`             | `int`  | `char`           |
| `float32`  | `float`            | `float`| `float`          |
| `float64`  | `double`           | `float`| `double`         |
| `int8/16/32/64`  | signed variants | `int` | `octet`/`short`/`long`/`long long` |
| `uint8/16/32/64` | unsigned variants| `int` | unsigned variants |
| `string`   | `std::string`      | `str`  | `string`         |
| `wstring`  | `std::u16string`   | `str`  | `wstring`        |

**Array types.**
- Unbounded dynamic: `int32[]`
- Fixed-size: `int32[5]`
- Bounded dynamic: `int32[<=5]`

**String variants.**
- Unbounded: `string my_string`
- Bounded: `string<=10 short_string`
- Bounded array of bounded strings: `string<=10[<=5] limited_array`

**Default values.** Field default goes as the third token:
```
uint8 x 42
string name "John Doe"
int32[] samples [-200, -100, 0]
```
Defaults are *not* supported on string arrays or on nested/composite-type
fields.

**Constants.** Uppercase name with `=` and a literal:
```
int32 X=123
string FOO="foo"
```
Constants are immutable and exposed as language-level constants on the
generated class.

**Composite / nested.** A field can be another message either by
fully-qualified `package/Type` or, if same package, by bare `Type`. Messages
can nest messages. Actions can nest messages. **Services cannot nest other
services.**

**Field naming rules.** Lowercase alphanumeric + underscores, must start with
a letter, no trailing or consecutive underscores.

**Code-generation flow.** A package declares its interfaces in
`CMakeLists.txt` via `rosidl_generate_interfaces(<target> <files...>
DEPENDENCIES ...)`. The `rosidl` pipeline then:
1. parses each `.msg`/`.srv`/`.action`,
2. emits language-agnostic IDL,
3. dispatches to per-language type-support generators (rosidl_typesupport_*),
4. produces C structs, C++ classes, Python modules, and the DDS type-support
   shims that the `rmw` layer hands to the underlying DDS.

The page references the C++ and Python interface-mapping design documents
on `design.ros2.org` and the DDS type-mapping article for full details.

**Tutorial cross-refs.** "Creating custom msg and srv files" and the action
creation tutorials in the Beginner / Intermediate Client Libraries trees.

---

## About Topics
**Source**: https://docs.ros.org/en/jazzy/Concepts/Basic/About-Topics.html

**Mental model.** A topic is a named bus. Any node may attach a *publisher*
on the topic name; any node may attach a *subscriber*. Once both ends exist
and have compatible types and QoS, every message a publisher emits is
delivered to every subscriber. Publishers and subscribers do not know each
other's identities — communication is *anonymous* — which is what makes
swapping a sensor driver for a simulator (or vice versa) a configuration
change rather than a code change.

**Defined terms.**
- **Publisher** — the producing endpoint; calls `publish(msg)`.
- **Subscriber** — the consuming endpoint; runs a callback on each message.
- **Topic** — the named channel; resolves through namespace remapping just
  like node names do.
- **Message** — a strongly-typed value defined by a `.msg` file.
- **Anonymous** — endpoints don't address each other by node name; they
  meet on the topic name.

**Many-to-many semantics.** A topic supports zero-or-more publishers and
zero-or-more subscribers simultaneously. When *any* publisher emits, *all*
matched subscribers receive — there is no leader, no broker process, and no
required ordering between publishers. This is what allows e.g. multiple
"velocity command" sources to coexist (with a mux downstream selecting one),
or multiple loggers to attach to the same sensor stream without affecting
the producer.

**Type matching.** Type matching is enforced at *both* the structural
("is this `sensor_msgs/Imu` on both sides?") and semantic ("the angular
velocity field is rad/s, the orientation is the standard quaternion") levels.
The structural check is at the middleware layer; the semantic conventions
are enforced socially through the `rep-103` / common-msg conventions.

**QoS-driven delivery.** Topics carry a QoS profile (history, depth,
reliability, durability, deadline, lifespan, liveliness). The middleware
will only connect a publisher and a subscriber whose QoS profiles are
*compatible*; mismatches result in silent non-delivery, not an error.
(Details on the Intermediate QoS page.)

**No CLI examples on this page itself**, but the standard introspection
verbs are `ros2 topic list`, `ros2 topic info`, `ros2 topic echo
<topic>`, `ros2 topic pub <topic> <type> '<yaml>'`, and `ros2 topic hz`.
The page links to the QoS concept page, the talker–listener demo, and the
"Understanding topics" beginner tutorial.

---

## About Services
**Source**: https://docs.ros.org/en/jazzy/Concepts/Basic/About-Services.html

**Mental model.** A service is a remote-procedure call between two nodes:
a **client** sends a typed request, a **server** computes a response, and
the client gets it back. Unlike topics, the addressing is one-to-one *for
that call*, and the client expects to receive exactly one response per
request.

**Defined terms.**
- **Service** — a named RPC channel.
- **Service server** — the unique node that implements the service at that
  name and answers requests.
- **Service client** — any node that calls into the service.
- **Request / Response** — the two `.msg`-like halves of a `.srv` file,
  separated by `---`.

**Synchronous semantics.** The client conceptually "waits for the result".
In practice rclcpp/rclpy expose both a synchronous wrapper (`call`) and an
asynchronous future-based call (`async_send_request`), and *the async form
is the one you should use from anywhere that runs inside an executor*.

**Why services can deadlock.** Because callbacks share the executor's
threads, calling `call()` (the blocking form) from inside a subscription
callback or a timer callback occupies a thread that the same executor needs
to *receive* the response on. The most common failure mode is calling a
service from a single-threaded executor's timer: the timer callback blocks
waiting for the response, the executor cannot dispatch the response, and
the call times out (or hangs). The page accordingly steers users toward
**asynchronous** clients and toward **actions** for any operation that
takes nontrivial time.

**One server, many clients.** Each service name must have exactly one
server — the page calls multi-server behavior "undefined". Any number of
clients on the same service name is fine.

**Long-running work.** The page explicitly recommends actions instead of
services for "longer running processes" because actions support feedback
and cancellation; services don't.

**CLI** (referenced but not exemplified on this page): `ros2 service list`,
`ros2 service type <name>`, `ros2 service call <name> <type> '<yaml>'`.
Cross-refs go to the actions concept page and to the
"Understanding services" beginner tutorial.

---

## About Actions
**Source**: https://docs.ros.org/en/jazzy/Concepts/Basic/About-Actions.html

**Mental model.** An action is a long-running RPC with two extras over a
service: (1) periodic **feedback** while it runs, and (2) the ability to
**cancel or preempt** it. Use it for "navigate to pose", "execute
trajectory", "scan the room" — anything that takes meaningfully longer than
one tick of the executor.

**Defined terms.**
- **Action** — the long-running RPC pattern.
- **Goal** (a.k.a. request) — the parameters of the operation, sent by the
  client.
- **Result** (a.k.a. response) — the final outcome, returned once.
- **Feedback** — intermediate progress messages emitted while the action
  runs.
- **Action server** — the unique node that accepts goals and executes
  them. There must be exactly one server per action name, same constraint
  as services.
- **Action client** — any node that sends goals; multiple clients are
  fine.
- **Goal handle** — the client-side and server-side objects representing
  one accepted goal; used to query state, request cancellation, and
  retrieve the result.

**The `.action` file** (three sections):
```
# Goal
int32 request
---
# Result
int32 response
---
# Feedback
int32 feedback
```

**Underlying implementation.** Although the basic page does not enumerate
them, the canonical action interface is built from **two services + three
topics**:

- service `send_goal` — client → server, returns goal acceptance.
- service `cancel_goal` — client → server, requests cancellation.
- topic `feedback` — server → all clients of that goal, periodic.
- topic `status` — server → all, the current state of every active goal.
- service / topic `get_result` — client retrieves the final result once
  the goal terminates (wrapped as a service with a deferred response in
  the rclcpp/rclpy APIs).

This is why `ros2 topic list` will show extra `_action/...` topics around
any active action server, and why action discovery follows the same rules
as topic + service discovery combined.

**Goal state machine.** Every accepted goal moves through a small state
machine on the server side:
- **ACCEPTED** — the server's `goal_callback` has approved the goal but
  execution has not started.
- **EXECUTING** — the server is actively working on the goal.
- **CANCELING** — a cancel request has been received and accepted; the
  server is winding down.
- **SUCCEEDED** — terminal; the goal completed normally.
- **CANCELED** — terminal; the goal was canceled before completion.
- **ABORTED** — terminal; the server gave up on its own (error condition).

Newer goals can **preempt** older ones if the server's policy allows
multiple concurrent goals; preemption is implemented as a cancel of the
previous goal followed by acceptance of the new one.

**Cancellation flow.** Client invokes `cancel_goal` on the goal handle →
server's `cancel_callback` returns ACCEPT or REJECT → on accept, the
server's execution coroutine is expected to notice and exit, transitioning
the goal to CANCELED. The middleware does not forcibly stop user code;
cooperative cancellation is the contract.

**CLI.** `ros2 action list`, `ros2 action info <name>`, `ros2 action
send_goal <name> <type> '<yaml>' --feedback`. Page cross-refs go to the
services concept page, the parameters concept page, and the "Creating an
action" + "Writing an action server and client" intermediate tutorials in
both C++ and Python.

---

## About Parameters
**Source**: https://docs.ros.org/en/jazzy/Concepts/Basic/About-Parameters.html

**Mental model.** Parameters are *per-node, typed, named configuration
values*, settable at startup and (usually) mutable at runtime. They are how
you tell a node "this is the camera topic", "this is the gain", "this is
the path to a model file" — without rebuilding it.

**Per-node, not global.** Unlike ROS 1's central parameter server, ROS 2
parameters live on the owning node. Each node automatically exposes a
small set of services for managing its own parameters; `ros2 param`
verbs talk to those services.

**Parameter types.** Each parameter has one of:
`bool`, `int64`, `float64`, `string`, `byte[]`, `bool[]`, `int64[]`,
`float64[]`, `string[]`. (In code these correspond to
`PARAMETER_BOOL`, `PARAMETER_INTEGER`, `PARAMETER_DOUBLE`,
`PARAMETER_STRING`, `PARAMETER_BYTE_ARRAY`, `PARAMETER_BOOL_ARRAY`,
`PARAMETER_INTEGER_ARRAY`, `PARAMETER_DOUBLE_ARRAY`,
`PARAMETER_STRING_ARRAY`, plus `PARAMETER_NOT_SET` for the default.)

**Descriptors.** Every parameter carries a key, a value, and an optional
**descriptor** (`ParameterDescriptor`). The descriptor can record:
- a human description string,
- a type,
- numeric ranges (`floating_point_range`, `integer_range`) with min/max
  and optional step,
- a `read_only` flag,
- additional constraint metadata.

Descriptors default to empty; populating them is what makes a parameter
self-documenting and protects against bad sets at runtime.

**Declared vs undeclared.** Default behavior is **declared parameters
only**: a node calls `declare_parameter("name", default, descriptor)` at
startup, the type is fixed, and any later `set` of the wrong type is
rejected. A node may opt in to `allow_undeclared_parameters: true`, in
which case any client may set any parameter on it dynamically. Type
enforcement can also be loosened per-parameter by setting
`dynamic_typing: true` on the descriptor.

**Callbacks.** Three callback hooks let user code react to parameter
changes:
- **pre-set** — runs before the proposed change is committed; can edit
  the parameter list before it is validated.
- **set** (the validation callback) — must return success/failure for the
  proposed change. This is the gate for "this gain must be > 0" type
  rules. Callbacks here must have **no side effects** (the change isn't
  yet committed).
- **post-set** — runs after a successfully accepted change; this is
  where you re-allocate the camera buffer or rebuild the controller.

**Parameter event topic.** Every change emits an event on the global
parameter event topic, so monitoring tools (e.g., RQt's parameter plugin)
can show parameter changes across the entire graph.

**Per-node service API.** Each node automatically hosts:
- `describe_parameters` — fetch descriptors,
- `get_parameter_types` — fetch types only,
- `get_parameters` — fetch values,
- `list_parameters` — enumerate by prefix,
- `set_parameters` — set one or more, fail-individually,
- `set_parameters_atomically` — set one or more, all-or-nothing.

**How parameters are populated.** At startup via:
- `--ros-args -p name:=value` on the command line,
- `--ros-args --params-file path.yaml` for a YAML file,
- `parameters=[{...}, ...]` on a launch `Node` action.

At runtime via the `ros2 param` CLI (`list`, `get`, `set`, `describe`,
`dump`, `delete`, `load`) or programmatically through `rclcpp::Parameter`
APIs in C++ and `rclpy.Parameter` in Python.

**Tutorial cross-refs.** "Understanding parameters" (Beginner CLI),
"Using parameters in a class (C++)" / "(Python)" (Beginner Client
Libraries), and the ROS 1 parameter migration guide.

---

## About Command-Line Tools
**Source**: https://docs.ros.org/en/jazzy/Concepts/Basic/About-Command-Line-Tools.html

**Mental model.** `ros2` is a single umbrella binary that dispatches to a
suite of *verbs*. Each verb is implemented as a Python entry point
discovered at runtime via setuptools — there is no central switch table.
Installing a package that registers a `ros2cli` entry point automatically
adds the verb to `ros2 --help`. This is how, e.g., installing `sros2` adds
`ros2 security`, and installing `ros2bag` adds `ros2 bag`.

**The verbs.** All shipping verbs as of Jazzy:
- **`node`** — list / info on running nodes (`ros2 node list`,
  `ros2 node info /node`).
- **`topic`** — list / info / echo / publish / hz / bw / delay
  (`ros2 topic list`, `echo`, `pub`, `hz`).
- **`service`** — list / type / call (`ros2 service call /name pkg/Srv
  '<yaml>'`).
- **`action`** — list / info / send_goal (`--feedback`).
- **`param`** — list / get / set / describe / dump / load / delete.
- **`run`** — execute a node from a package (`ros2 run pkg exe`).
- **`launch`** — run a launch file (`ros2 launch pkg file.launch.py
  arg:=value`).
- **`bag`** — record / play / info / convert / reindex rosbags.
- **`pkg`** — list / prefix / xml / executables / create — package
  introspection and skeletons.
- **`lifecycle`** — list / get / set transitions on managed nodes.
- **`component`** — load / unload / list nodes inside a component
  container.
- **`daemon`** — status / start / stop the background discovery cache
  daemon.
- **`doctor`** (alias **`wtf`**) — health check of the local ROS
  installation, environment, and middleware.
- **`interface`** — show / list / package / packages — `.msg`/`.srv`/
  `.action` definitions known to the system.
- **`plugin`** — introspect the `ros2cli` plugin set itself.
- **`security`** — keystore / enclave management (added by `sros2`).
- **`test`** — run launch_testing test files.
- **`trace`** — LTTng tracing wrappers (Linux only).
- **`multicast`** — send / receive multicast packets, used to debug
  discovery on a host.

**The daemon.** Most introspection verbs talk to a per-domain background
daemon that maintains a cached view of the ROS graph; this is what makes
`ros2 node list` fast even on a busy graph. The daemon is started
on first use, communicates over localhost only, and uses
`ROS_DOMAIN_ID` as a port offset so multiple domains coexist on one
machine. `ros2 daemon stop / start / status` controls it explicitly.

**Worked example.** The page demonstrates the canonical talker-listener
flow with `ros2 topic pub` (to publish from the CLI) and `ros2 topic
echo` (to read), as a sanity check that pub/sub + discovery + QoS are
all working.

**Source.** All verbs live in https://github.com/ros2/ros2cli; new verbs
are added by writing a Python entry point in your own package.

---

## About Launch
**Source**: https://docs.ros.org/en/jazzy/Concepts/Basic/About-Launch.html

**Mental model.** A real ROS 2 system "consists of many nodes running
across many different processes (and even different machines)." The
launch system is what turns "many nodes, many configs, many machines"
into a *single command*: `ros2 launch <pkg> <file>`. A launch file is a
declarative + scriptable description of *what to run, where, with what
parameters, with what remappings, in what namespace, conditional on
what*.

**Three file formats.** Launch files can be written in:
- **Python** (`*.launch.py`) — the *default and most powerful* format.
  Python is preferred because launch needs full control flow:
  conditional inclusion, dynamic argument computation, event handlers
  that respond to one process exiting by starting another, etc. Static
  formats can't express these naturally.
- **XML** (`*.launch.xml`) — concise, good for "just start these five
  nodes with these args"; the format ROS 1 users will recognize.
- **YAML** (`*.launch.yaml`) — same target audience as XML, different
  syntax.

All three are loaded by the same `ros2 launch` runtime and can include
each other.

**Responsibilities.** The launch system handles:
- choosing which executables to run and where (`Node`, `ExecuteProcess`,
  `LifecycleNode`),
- passing parameters and arguments (with substitutions like
  `LaunchConfiguration`, `PathJoinSubstitution`,
  `FindPackageShare`),
- applying ROS conventions (namespace, remappings, QoS overrides),
- monitoring process state and reacting to events (`OnProcessExit`,
  `OnProcessStart`, `OnShutdown`),
- composing larger systems out of smaller launch files via
  `IncludeLaunchDescription`.

**Differences from ROS 1's `roslaunch`.** Although the basic concept page
does not enumerate them, the practical differences are: ROS 2 launch is
Python-first (roslaunch was XML-only with limited eval), supports
event-driven flow (roslaunch was static), can manage non-ROS processes
as first-class citizens (`ExecuteProcess`), and has no `roscore`
dependency because there is no master.

**Defined sub-concepts (referenced, expanded in the tutorials).**
- **Launch description** — the tree of actions returned by
  `generate_launch_description()`.
- **Launch context** — runtime state shared by all actions in a launch.
- **Substitutions** — lazy-evaluated expressions
  (`LaunchConfiguration("rate")`, `EnvironmentVariable("HOME")`,
  `Command(["echo", "hi"])`) resolved at launch time, not at
  Python-import time.
- **Event handlers** — `RegisterEventHandler(OnProcessExit(...))`,
  `OnExecutionComplete`, etc.
- **Conditions** — `IfCondition` / `UnlessCondition` for conditional
  actions.

**CLI.** `ros2 launch <pkg> <file> arg:=value` is the only entry point.
Cross-refs go to the launch tutorials in the Beginner / Intermediate
Tutorials trees and to the dedicated launch reference at
docs.ros.org/en/jazzy/p/launch/.

---

## About Client Libraries
**Source**: https://docs.ros.org/en/jazzy/Concepts/Basic/About-Client-Libraries.html

**Mental model.** A *client library* is the language-specific API a user
writes ROS 2 code against. Rather than re-implement the full ROS 2 stack
in every language, the project factors out the language-agnostic logic
into a shared C library — **`rcl`** — and each language library is a
relatively thin wrapper over `rcl`. Underneath `rcl` sits **`rmw`**, the
middleware abstraction layer that talks to whichever DDS vendor is
selected.

**The layer cake** (bottom to top):
1. **`rmw`** — ROS middleware interface; pluggable, with implementations
   for Fast DDS (`rmw_fastrtps_cpp`, the default), Cyclone DDS
   (`rmw_cyclonedds_cpp`), Connext, Zenoh, etc.
2. **`rcl`** — the common C client library. Owns nodes, executors,
   contexts, parameter logic, name validation, time, lifecycle. Language
   libraries delegate to it for everything that is not language-specific.
3. **Language libraries** — `rclcpp` (C++), `rclpy` (Python), `rclc`
   (microcontroller C, complementary not on top of `rcl`), and
   community bindings.

**`rclcpp`** — the canonical C++17 API. Provides nodes, publishers /
subscribers, service servers / clients, action servers / clients,
parameters, timers, callback groups, and executors. Heavy use of
templates for type-safe interfaces; spawned via `rclcpp::init` /
`rclcpp::spin` / `rclcpp::shutdown`.

**`rclpy`** — the Python counterpart. "Idiomatic Python experience that
uses native Python types and patterns." Threads under the hood; converts
between Python objects and C messages on every publish/receive.
Initialized with `rclpy.init()` / `rclpy.spin(node)` / `rclpy.shutdown()`.

**`rclc`** — community-maintained C client library "for microcontroller
applications". Sits *beside* `rcl`, not on top of it; designed for
constrained environments (no dynamic allocation in hot paths,
deterministic memory). The micro-ROS stack uses it.

**Executors.** Although the basic page only references the concept, the
mental model needed elsewhere is: an executor owns one or more callback
groups and dispatches incoming work (subscriptions firing, timers
expiring, service requests arriving, action callbacks, parameter
callbacks) onto threads. The two standard executors are
**SingleThreadedExecutor** (one thread, callbacks run sequentially —
this is the default and the source of most "service deadlocked from
inside a timer" pitfalls) and **MultiThreadedExecutor** (a thread pool;
callbacks in different *callback groups* can run concurrently). The
Intermediate Executors page covers this in depth.

**Generic clients / generic publishers.** Both `rclcpp` and `rclpy`
expose typed APIs by default, but also a *generic* family
(`rclcpp::GenericPublisher`, `rclcpp::GenericSubscription`,
`rclpy.node.Node.create_generic_publisher`) that lets a node carry
serialized payloads of types not known at compile time. This is what
`ros2 bag record` is built on.

**Community bindings (mentioned).** Ada, Java/Android, .NET/C#, Node.js,
Rust, Flutter/Dart. Older / unmaintained: a different C# binding,
Objective-C, Zig. These are not part of core ROS 2 releases.

**API references** linked from the page:
- `rclcpp` — https://docs.ros.org/en/jazzy/p/rclcpp/
- `rclpy` — https://docs.ros.org/en/jazzy/p/rclpy/
- `rcl`   — https://docs.ros.org/en/jazzy/p/rcl/
- Source: https://github.com/ros2/rclcpp, https://github.com/ros2/rclpy

**Tutorial cross-refs.** Beginner Client Libraries (publishers,
subscribers, services, custom interfaces, parameters in a class) and
Intermediate Composition (multiple nodes per process via component
containers).
