# The ROS 2 Project — Governance, Releases, Glossary

## The ROS 2 Project (index)
**Source**: https://docs.ros.org/en/jazzy/The-ROS2-Project.html

Top-level governance/meta hub for ROS 2. Subpages linked from the index:

1. **Contributing** — developer guide, code style, quality guide, ROS build farms, Windows tips, contributing to documentation.
2. **Features Status** — current implementation status of ROS 2 capabilities (404 at `Features-Status.html` URL — content reachable only via index).
3. **Feature Ideas** — proposed enhancements awaiting contributors.
4. **Roadmap** — planned development trajectory.
5. **ROSCon Talks** — recorded conference content.
6. **Project Governance** — OSRA, TGC, ROS PMC structure.
7. **Platform EOL Policy** — when distros drop platforms.
8. **Platform Support Tiers** — Tier 1/2/3 classification.
9. **Release Schedule** — yearly release timing.
10. **Marketing** — branding, art repository, "Why ROS 2?" brochure, Zazzle merch.
11. **Metrics** — project stats.
12. **ROS 2 Adopters** — list of organizations using ROS 2.

---

## Contributing
**Source**: https://docs.ros.org/en/jazzy/The-ROS2-Project/Contributing.html

How to contribute: PRs to https://github.com/ros2 repos; discuss large changes on Open Robotics Discourse first. Find newcomer tasks via GitHub `help wanted` and `good first issue` labels (filtered to `user:ament user:ros2`). Run local tests before submitting (most packages enforce style via tests). Sub-guides:
- Developer Guide — workflow, branching, review process (DCO/CLA details live here).
- Code Style and Language Versions — C++17, Python 3.8+, lint rules.
- Quality Guide — package quality levels.
- Contributing to ROS 2 Documentation — doc PR workflow.

Point contributors here first; deeper details live in linked sub-guides.

---

## Project Governance
**Source**: https://docs.ros.org/en/jazzy/The-ROS2-Project/Governance.html

Since 2024, ROS 2 is governed by the **Open Source Robotics Alliance (OSRA)**.
- **Technical Governance Committee (TGC)** — oversees all OSRA projects (paid members + project leaders + OSRF reps + merit-based members).
- **ROS Project Management Committee (ROS PMC)** — day-to-day operations: Project Leader + voting PMC members + Supporting Individual Rep + TGC Chair. ~15 voting members from Intrinsic, KUKA, Sony, eProsima, Apex.AI, etc., plus ~12 additional committers. Manages ~130 repos.
- **PMC meetings**: Tuesdays 17:00 UTC via Zoom, open to community observation. Agenda items routed through PMC constituents.
- All leaders/committers are selected meritocratically.

---

## Marketing
**Source**: https://docs.ros.org/en/jazzy/The-ROS2-Project/Marketing.html

ROS art repository for official logos/branding. Open Robotics Zazzle storefront for merch (posters, stickers). "Why ROS 2?" brochure (A4 + US Letter, Creative Commons BY-ND 4.0). Use for community outreach or onboarding decks.

---

## Roadmap
**Source**: https://docs.ros.org/en/jazzy/The-ROS2-Project/Roadmap.html

Tracks major upcoming features. Next release: **Lyrical Luth, expected May 2026**, tracked on GitHub Project Board #70 (`github.com/orgs/ros2/projects/70`). Task sizes: small (person-days), medium (person-weeks), large (person-months). Get involved via Contributing guide, `design.ros2.org`, the ros2 GitHub org, Open Robotics Discourse, or `info@openrobotics.org`.

---

## Feature Ideas
**Source**: https://docs.ros.org/en/jazzy/The-ROS2-Project/Feature-Ideas.html

Four categories of contribution opportunities:
- **Design/Concept** — IDL enums/constants, ROS 1→2 migration strategy, node naming uniqueness.
- **Infrastructure & Tools** — consolidate build systems, automate doc rebuilds; deprecate `design.ros2.org` (move content to REPs or `ros2_documentation`).
- **New Features** — logging improvements, time-based ops, executor perf, expanded message generation, manual composition for multi-node executables, real-time-safe services/parameters.
- **Tech Debt** — flaky tests, valgrind/ASAN coverage, API reviews, sync design docs with implementation.

Contact ROS 2 team before major work.

---

## Platform EOL Policy
**Source**: https://docs.ros.org/en/jazzy/The-ROS2-Project/Platform-EOL-Policy.html

When a platform vendor declares EOL, ROS drops support even if the distro is still active (security driver). Existing packages remain available but unmaintained. Maintainers ("ROS Bosses") must: document EOL date, announce 60–90 days ahead, PR to disable build farm jobs, do one final sync, then post an after-EOL announcement.

---

## Platform Support Tiers
**Source**: https://docs.ros.org/en/jazzy/The-ROS2-Project/Platform-Support-Tiers.html

- **Tier 1** — full unit tests, CI, nightly, packaging, perf tests. Bugs block releases.
- **Tier 2** — periodic CI (≥ weekly), public results, best-effort bug fixes; binary packages may not be available.
- **Tier 3** — community-reported as functional; no formal testing; community supports. Requires up-to-date install instructions.

---

## Releases (distro list)
**Source**: https://docs.ros.org/en/jazzy/Releases.html

New ROS 2 distro every May 23rd. Rolling = development branch.

**Currently supported:**
| Distro | Released | EOL |
|---|---|---|
| **Kilted Kaiju** | 2025-05-23 | 2026-12 |
| **Jazzy Jalisco** (LTS) | 2024-05-23 | 2029-05 |
| **Humble Hawksbill** (LTS) | 2022-05-23 | 2027-05 |

**End-of-life:**
| Distro | Released | EOL |
|---|---|---|
| Iron Irwini | 2023-05-23 | 2024-12-04 |
| Galactic Geochelone | 2021-05-23 | 2022-12-09 |
| Foxy Fitzroy (LTS) | 2020-06-05 | 2023-06-20 |
| Eloquent Elusor | 2019-11-22 | 2020-11 |
| Dashing Diademata (LTS) | 2019-05-31 | 2021-05 |
| Crystal Clemmys | 2018-12-14 | 2019-12 |
| Bouncy Bolson | 2018-07-02 | 2019-07 |
| Ardent Apalone | 2017-12-08 | 2018-12 |

**Upcoming:** Lyrical Luth — expected May 2026, EOL May 2031 (LTS).

ROS Boss for Jazzy: Marco A. Gutiérrez. For Humble: Christophe Bédard / Audrow Nash. For Kilted: Scott K Logan.

---

## Release Jazzy Jalisco (full release notes)
**Source**: https://docs.ros.org/en/jazzy/Releases/Release-Jazzy-Jalisco.html

Released **2024-05-23**, supported until **May 2029** (LTS).

### Supported platforms

**Tier 1**
- Ubuntu 24.04 Noble (amd64, arm64)
- Windows 10 with Visual Studio 2019 (amd64)

**Tier 2**
- RHEL 9 (amd64)

**Tier 3**
- macOS (amd64)
- Debian Bookworm (amd64)

**RMW middleware**
- Tier 1: Fast-DDS, Cyclone DDS
- Tier 1–2: Connext DDS, Fast-DDS Dynamic
- Tier 3: GurumDDS

**Language requirements**: C++17, Python 3.8+

### New features (by package)

**common_interfaces**
- New `geometry_msgs/VelocityStamped` message with transformation support.
- New `ARROW_STRIP` marker type in `visualization_msgs/Marker`.

**image_transport**
- Lazy subscriber support.
- Customizable callback group configuration.
- Runtime plugin allowlist filtering.
- Custom QoS for publishers/subscribers.
- `republish` node available as an `rclcpp` component (composable).

**message_filters**
- TypeAdapter support for filtered messages.

**rcl**
- New `~/get_type_description` service per **REP 2016**.
- Timer API exposes actual vs. expected call timing.
- Improved timeout computation and spurious wakeup handling.

**rclcpp**
- `rclcpp::get_service_typesupport_handle` helper.
- Fixed executor data races.
- `rclcpp::WaitSet` integrated into default executors.
- `rclcpp::TimerInfo` with actual vs. expected callback timing.
- Action handle callback improvements after cancellation.

**rclpy**
- New `ParameterEventHandler` class for monitoring parameter changes.
- Enhanced type annotations for static type checkers.
- Improved `declare_parameter` ergonomics.

**ros2cli**
- `--log-file-name` argument for custom log file naming.
- QoS parameter in subscription options for topic statistics.
- Service/client count introspection.
- New `ros2 action type` sub-command.

**rosbag2**
- Service recording/playback.
- `--topic_types` filter.
- Player and Recorder exposed as `rclcpp` components → enables zero-copy intra-process pipelines.
- Option to disable keyboard controls.
- Middleware send/receive timestamps captured (MCAP).
- Compression thread priority configuration.
- Time-based bag splitting via `start_time_ns`/`end_time_ns`.
- Self-contained metadata stored inside bag files.
- `ROS_DISTRO` metadata tracking.
- Python introspection methods for QoS.

**rosidl**
- `@key` annotation support to mark key data members.

**rviz2**
- Regex filtering for TF frames.
- Subscription frequency (Hz) shown in topic status.
- Time-reset via service or keyboard shortcut.
- `point_cloud_transport` plugin support.
- ROS 1 parity: `DepthCloud`, `AccelStamped`, `TwistStamped`, `WrenchStamped`, `Effort` displays.
- `CameraInfo` message visualization.

**rcpputils**
- `tl::expected` (C++23 backport) for error handling.

**rcutils**
- Human-readable date in console output: `{date_time_with_ms}` token in `RCUTILS_CONSOLE_OUTPUT_FORMAT`.

### Breaking changes / removals / deprecations

**rclcpp**
- **Removed** `rclcpp/qos_event.hpp` (was deprecated in Iron).
- **Removed** deprecated subscription signature `void callback(std::shared_ptr<MessageT>)` — must use the `const` variant `void callback(const std::shared_ptr<MessageT>)`.
- **Deprecated** `rclcpp::get_typesupport_handle` — use `rclcpp::get_message_typesupport_handle`.

**geometry2 / tf2**
- **Removed** deprecated `.h` headers — use `.hpp` variants.
- **Changed** `wait_for_transform_async` return type — now returns transform info instead of `bool`.

**rosbag2**
- **Renamed** CLI flag `--exclude` → `--exclude-regex`.
- QoS profile representation in metadata YAML changed to enum / human-readable strings.

**Executors**
- Callback ordering within the same entity is no longer guaranteed to be consistent — code that relied on stable intra-entity ordering must be reviewed.

### Infrastructure changes

- **Gazebo**: recommended version is **Harmonic**. New vendor packages `gz_*_vendor` and `sdformat_vendor` for cleaner dependency management.
- New `~/get_type_description` service (REP 2016) is part of the type description distribution mechanism — relevant for dynamic typing / introspection.

---

## End-of-Life
**Source**: https://docs.ros.org/en/jazzy/Releases/End-of-Life.html

Lists historic ROS 2 distros that are no longer supported: `iron`, `galactic`, `foxy`, `eloquent`, `dashing`, `crystal`, `bouncy`, `ardent`, plus pre-1.0 betas (`r2b3`, `r2b2`, `Asphalt`, alphas). Page is essentially a pointer — see Platform EOL Policy and Releases for dates.

---

## Related Projects (index)
**Source**: https://docs.ros.org/en/jazzy/Related-Projects.html

- **Gazebo** — open-source 3D physics simulator widely used to simulate ROS-based robots (recommended version for Jazzy: Harmonic).
- **ros2_control** — flexible framework for real-time control of robots.
- **Navigation2 (Nav2)** — comprehensive mobile-robot navigation stack.
- **MoveIt 2** — manipulation: kinematics, motion planning, collision detection.
- **micro-ROS** — port of ROS 2 to microcontrollers (< 100 kB RAM).
- **Phantom Bridge** — data visualization and teleoperation.
- **Intel ROS 2 Projects** — subpage (404 at the URLs listed in the task; navigate from this index in current docs).
- **NVIDIA ROS 2 Projects** — Isaac ROS suite (subpage URL 404s; reach via index).
- Hundreds of further packages discoverable via **ROS Index** at https://index.ros.org.

**Note**: Both `Related-Projects/Intel-ROS-2-Projects.html` and `Related-Projects/Nvidia-ROS-2-Projects.html` (and the `-ROS-Projects` variants) returned **404** at fetch time. Future agents should follow the live links from `Related-Projects.html` rather than guessing the slug.

---

## Glossary
**Source**: https://docs.ros.org/en/jazzy/Glossary.html

- **API** — interface provided by an "application", here usually a shared library.
- **client_library** — API that exposes the ROS graph using primitives like Topics, Services, Actions.
- **package** — single unit of software: source, build files, docs, tests, resources.
- **REP** — *Robotics Enhancement Proposal*; document describing an enhancement, standardization, or convention for the ROS community.
- **VCS** — Version Control System (git, mercurial, svn, cvs, …).
- **rclcpp** — C++-specific Client Library for ROS, including middleware APIs and C++ message generation.
- **repository** — collection of packages managed in a VCS, typically hosted on GitHub/BitBucket.

(The Jazzy glossary is intentionally short — most ROS 2 jargon is defined inline in the relevant concept pages.)

---

## Citations
**Source**: https://docs.ros.org/en/jazzy/Citations.html

**Primary citation** (general ROS 2 work): Macenski, Foote, Gerkey, Lalancette, Woodall — *"Robot Operating System 2: Design, architecture, and uses in the wild"*, Science Robotics 7(66), May 2022. DOI `10.1126/scirobotics.abm6074`.

```bibtex
@article{doi:10.1126/scirobotics.abm6074,
  author  = {Steven Macenski and Tully Foote and Brian Gerkey and Chris Lalancette and William Woodall},
  title   = {Robot Operating System 2: Design, architecture, and uses in the wild},
  journal = {Science Robotics},
  volume  = {7},
  number  = {66},
  pages   = {eabm6074},
  year    = {2022},
  doi     = {10.1126/scirobotics.abm6074}
}
```

**Specialized citation** (node composition): Macenski, Soragna, Carroll, Ge — *"Impact of ROS 2 Node Composition in Robotic Systems"*, IEEE RA-L 2023. DOI `10.48550/arXiv.2305.09933`.

---

## Contact
**Source**: https://docs.ros.org/en/jazzy/Contact.html

Official channels:
- **Robotics Stack Exchange** — primary venue for technical Q&A. Search first; tag with `ros2` and the distro.
- **GitHub Issues** at https://github.com/ros2 — bug reports and package-specific issues.
- **Open Robotics Discourse** — high-level discussions, REPs, feature plans (not code Q&A).
- **Email** `ros@osrfoundation.org` — sensitive / security reports only.

Discouraged: contacting individual developers directly, cross-posting, reposting. Note: there is **no official Slack/Discord** linked from the Jazzy Contact page; the community uses Stack Exchange + Discourse + GitHub.
