# Installation & Platform Setup (ROS 2 Jazzy)

> Source index: https://docs.ros.org/en/jazzy/Installation.html
>
> ROS 2 Jazzy Jalisco targets **Ubuntu 24.04 (Noble Numbat)** as its Tier 1 Linux platform, **RHEL 9** as Tier 2, **Windows 10** (binary, VS 2019) as Tier 1, and **macOS** as Tier 3 (source only). Aarch64 is Tier 1; 32-bit arm is Tier 3. See REP-2000 for the authoritative platform tier list.
>
> Installation method picker:
> - Linux + root: deb / RPM packages (auto deps, system updates).
> - Linux, no root: binary archive.
> - Windows: binary archive (only supported route).
> - Need to modify or omit ROS 2 core: build from source.
> - Contributing to ROS 2 itself: latest development (rolling) source build.
>
> Cross-cutting gotchas applicable everywhere:
> - Never source two ROS 2 distributions in the same shell. Either remove `source /opt/ros/<distro>/setup.bash` from `~/.bashrc` or open a fresh terminal before working with a source build. Verify with `printenv | grep -i ROS`.
> - GitHub auth on this machine is SSH only. If `git clone` or any tooling resolves an `https://github.com/...` URL and prompts for a username, switch the remote to `git@github.com:...`. PAT/HTTPS auth is broken via `ksshaskpass`.
> - The official RHEL/Ubuntu deb sources now flow through the `ros-infrastructure/ros-apt-source` GitHub release (a `ros2-apt-source_*.deb` / `ros2-release-*.noarch.rpm`). The legacy `apt-key add` workflow has been retired.

---

## Installation (overview)
**Source**: https://docs.ros.org/en/jazzy/Installation.html

The overview page enumerates the supported binary and source install paths and recommends a default per platform. It states: "Binary packages are for general use and provide an already-built install of ROS 2." Source installs are framed as: "Building from source is meant for developers looking to alter or explicitly omit parts of ROS 2's base."

Binary support matrix:
- Ubuntu Linux (amd64 / aarch64), Noble Numbat (24.04): deb packages **(recommended)** or binary archive.
- RHEL 9 (amd64): RPM packages **(recommended)** or binary archive.
- Windows 10 (amd64): Windows binary built against VS 2019.

Source build supported platforms:
- Ubuntu 24.04, Windows 10, RHEL 9 / Fedora, macOS.

The page makes one important caveat: binaries are only published for Tier 1 OSes per REP-2000. Anything else (BSDs, ARM32, exotic distros, recent Fedora) requires a source build or Docker. It also distinguishes the two flavours of the apt/dnf metapackage you will pick from on Linux: `ros-jazzy-desktop` (the kitchen-sink developer install with RViz, demos, tutorials) versus `ros-jazzy-ros-base` (libraries + tools, no GUI). Contributors hacking on the ROS 2 core are pointed at the "latest development (source)" alternative.

When a future agent is bootstrapping a new machine, this page is the decision tree: pick the row, follow the link. For Ubuntu 24.04 development boxes, the answer is almost always `Ubuntu-Install-Debs.html`.

---

## Ubuntu (deb packages) - the canonical Linux install
**Source**: https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html

Target OS: **Ubuntu 24.04 Noble Numbat**. This is the path you want on any Ubuntu 24.04 system with sudo. End to end:

**1. Locale (must be UTF-8).**
```bash
locale  # check for UTF-8
sudo apt update && sudo apt install locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
```

**2. Enable Universe and install the ROS 2 apt source package.** This replaces the old `apt-key`/`add-apt-repository` recipe:
```bash
sudo apt install software-properties-common
sudo add-apt-repository universe
sudo apt update && sudo apt install curl -y
export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F'"' '{print $4}')
curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})_all.deb"
sudo dpkg -i /tmp/ros2-apt-source.deb
```

**3. Install ROS 2 itself.** Pick exactly one of the metapackages:
```bash
sudo apt update
sudo apt upgrade
sudo apt install ros-jazzy-desktop          # RViz, demos, tutorials, ros2 CLI
# OR for headless / robot deployment:
sudo apt install ros-jazzy-ros-base         # Communications libs + tools, no GUI
sudo apt update && sudo apt install ros-dev-tools  # colcon, rosdep, vcs, etc.
```

**4. Source the environment in every shell that uses ROS.**
```bash
source /opt/ros/jazzy/setup.bash    # also setup.sh / setup.zsh
```

**5. Smoke test in two terminals.**
```bash
# Terminal 1
source /opt/ros/jazzy/setup.bash
ros2 run demo_nodes_cpp talker
# Terminal 2
source /opt/ros/jazzy/setup.bash
ros2 run demo_nodes_py listener
```

**6. Uninstall** (purges every ros-jazzy-* package, then the apt source):
```bash
sudo apt remove '~nros-jazzy-*' && sudo apt autoremove
sudo apt remove ros2-apt-source
sudo apt update && sudo apt autoremove && sudo apt upgrade
```

Common pitfalls: forgetting Universe (causes `Unable to locate package ros-jazzy-*`); installing both `desktop` and a source build and sourcing them in the same shell; running on Ubuntu 22.04 - Jazzy is **not** packaged for Jammy, that's Humble's slot.

---

## Ubuntu (binary archive)
**Source**: https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Binary.html

**Status: 404 Not Found at the time of fetch.** This page no longer exists in the Jazzy docs - the binary tarball install was apparently dropped for Jazzy and the deb/source paths are the only documented Ubuntu options. If you genuinely need a no-root install on Ubuntu, fall back to either the source build (see Ubuntu-Development-Setup) or a Docker-based install (`docker pull ros:jazzy-ros-base`). Older distros (Humble, Iron) still ship a `Ubuntu-Install-Binary.html` page; do not assume their commands transfer.

---

## Windows (binary)
**Source**: https://docs.ros.org/en/jazzy/Installation/Windows-Install-Binary.html

Target OS: **Windows 10 only.** Binaries built against Visual Studio 2019. The packages are not relocatable, so the docs hardcode the install root at `C:\pixi_ws` to keep paths short.

Prerequisite: install **pixi** (https://pixi.sh/latest/) from PowerShell, then close and reopen PowerShell so `pixi` is on PATH.

Workspace + dependency install:
```powershell
md C:\pixi_ws
cd C:\pixi_ws
irm https://raw.githubusercontent.com/ros2/ros2/refs/heads/jazzy/pixi.toml -OutFile pixi.toml
pixi install
```

ROS 2 release: download `ros2-jazzy-*-windows-release-amd64.zip` from https://github.com/ros2/ros2/releases and extract it to `C:\pixi_ws\ros2-windows`.

Per-shell environment setup (use `cmd.exe`, not PowerShell, for the ROS env):
```cmd
cd C:\pixi_ws
pixi shell
call C:\pixi_ws\ros2-windows\local_setup.bat
```

Smoke test in two cmd terminals:
```cmd
ros2 run demo_nodes_cpp talker
ros2 run demo_nodes_py listener
```

Uninstall is just deleting the workspace:
```cmd
rmdir /s /q C:\pixi_ws
```

Documented gotcha: "If you do not have RTI Connext DDS installed on your computer, it is normal to receive a warning that it is missing." Other Windows-specific traps that bite repeatedly (covered in the troubleshooting page below): the 260-character path limit (enable `LongPathsEnabled` in the registry), Windows Defender locking files mid-build (exclude the workspace), and missing `msvcr20.dll` killing Fast RTPS at runtime.

---

## RHEL 9 (RPM packages)
**Source**: https://docs.ros.org/en/jazzy/Installation/RHEL-Install-RPMs.html

Target OS: **RHEL 9** (and binary-compatible derivatives via EPEL + CodeReady Builder).

**1. Enable EPEL and CRB.**
```bash
sudo dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-$(rpm -E %rhel).noarch.rpm
sudo env FORCE_DNF=1 crb enable
```

**2. Install the ROS 2 release RPM** (analogous to the apt-source deb):
```bash
sudo dnf install curl
export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F'"' '{print $4}')
sudo dnf install "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-release-${ROS_APT_SOURCE_VERSION}-1.noarch.rpm"
```

**3. Locale.**
```bash
locale
sudo dnf install langpacks-en glibc-langpack-en
export LANG=en_US.UTF-8
```

**4. Install ROS 2.**
```bash
sudo dnf update
sudo dnf install ros-jazzy-desktop          # full
# OR
sudo dnf install ros-jazzy-ros-base         # minimal
```

**5. Optional dev tools** (note these are a hand-rolled list, *not* a `ros-dev-tools` metapackage like on Ubuntu):
```bash
sudo dnf install -y cmake gcc-c++ git make patch python3-colcon-common-extensions \
  python3-flake8-blind-except python3-flake8-class-newline python3-flake8-deprecated \
  python3-mypy python3-pip python3-pydocstyle python3-pytest python3-pytest-repeat \
  python3-pytest-rerunfailures python3-rosdep python3-setuptools python3-vcstool wget
```

**6. Source + smoke test.**
```bash
source /opt/ros/jazzy/setup.bash
ros2 run demo_nodes_cpp talker      # Terminal 1
ros2 run demo_nodes_py listener     # Terminal 2
```

**7. Uninstall.**
```bash
sudo dnf remove ros-jazzy-*
sudo dnf remove ros2-release
```

Gotcha: skipping `crb enable` causes opaque dependency errors when dnf tries to resolve packages that live in the CodeReady Builder repo.

---

## Installation alternatives (index)
**Source**: https://docs.ros.org/en/jazzy/Installation/Alternatives.html

Hub page that just enumerates the alternatives: "A list of alternative ways to install ROS 2 - whether it's by building from source or installing a binary." Links covered:

1. Ubuntu (source) - `Ubuntu-Development-Setup.html`
2. Ubuntu (binary) - the now-404 tarball page
3. Windows (source) - `Windows-Development-Setup.html`
4. RHEL (source) - `RHEL-Development-Setup.html`
5. RHEL (binary) - the RPM page, also reachable as a primary install path
6. macOS (source) - `macOS-Development-Setup.html` (Tier 3)
7. Latest development (source) - rolling

Rule of thumb: if you don't need a hot-patched ROS 2 core or an unsupported OS, don't reach for these. Binary installs reach a working state in minutes; source builds take 30-90 minutes and want gigabytes of RAM.

---

## Ubuntu (build from source / development setup)
**Source**: https://docs.ros.org/en/jazzy/Installation/Alternatives/Ubuntu-Development-Setup.html

Use this when you need to patch ROS 2 core packages, run with non-default options, or the deb install isn't possible (e.g., no sudo, custom toolchain). The locale and apt-source steps mirror the deb install:

```bash
locale
sudo apt update && sudo apt install locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
locale  # verify
```

```bash
sudo apt install software-properties-common
sudo add-apt-repository universe
sudo apt update && sudo apt install curl -y
export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F'"' '{print $4}')
curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})_all.deb"
sudo dpkg -i /tmp/ros2-apt-source.deb
```

Build prerequisites (note: `ros-dev-tools` carries colcon, rosdep, vcs, ament, etc., so most of these test deps are extras):
```bash
sudo apt update && sudo apt install -y \
  python3-flake8-blind-except \
  python3-flake8-class-newline \
  python3-flake8-deprecated \
  python3-mypy \
  python3-pip \
  python3-pytest \
  python3-pytest-cov \
  python3-pytest-mock \
  python3-pytest-repeat \
  python3-pytest-rerunfailures \
  python3-pytest-runner \
  python3-pytest-timeout \
  ros-dev-tools
```

Pull the ROS 2 source tree using `vcs` against the canonical repos manifest:
```bash
mkdir -p ~/ros2_jazzy/src
cd ~/ros2_jazzy
vcs import --input https://raw.githubusercontent.com/ros2/ros2/jazzy/ros2.repos src
```

Resolve and install all system deps via rosdep. The skip-keys here are load-bearing - those packages either aren't packaged on Ubuntu or are commercial:
```bash
sudo apt upgrade
sudo rosdep init
rosdep update
rosdep install --from-paths src --ignore-src -y --skip-keys "fastcdr rti-connext-dds-6.0.1 urdfdom_headers"
```

Build everything (symlink-install lets you edit Python sources without rebuilding):
```bash
cd ~/ros2_jazzy/
colcon build --symlink-install
```

> **Critical warning** (verbatim from the docs): "If you have already installed ROS 2 another way (either via debs or the binary distribution), make sure that you run the below commands in a fresh environment that does not have those other installations sourced." This is the #1 source of weird CMake / Python errors.

Source the workspace overlay (use `local_setup` not `setup` if you don't want to also chain a base install):
```bash
. ~/ros2_jazzy/install/local_setup.bash
```

Smoke test in two terminals (each must source the overlay):
```bash
. ~/ros2_jazzy/install/local_setup.bash
ros2 run demo_nodes_cpp talker

. ~/ros2_jazzy/install/local_setup.bash
ros2 run demo_nodes_py listener
```

Uninstall is just `rm -rf ~/ros2_jazzy`.

---

## Windows (build from source)
**Source**: https://docs.ros.org/en/jazzy/Installation/Alternatives/Windows-Development-Setup.html

Windows 10 only. Recommended in a clean environment (fresh install, Docker, or VM). Keep the workspace path short (the docs use `C:\dev`).

**Enable Win32 long paths** before doing anything else - hit this once and you save hours of debugging:
```powershell
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

**Install Visual Studio 2019 Build Tools** with MSBuild, .NET, VC tools, and the Windows SDK:
```powershell
irm https://aka.ms/vs/16/release/vs_buildtools.exe -OutFile vs_buildtools_2019.exe
.\vs_buildtools_2019.exe --quiet --wait --norestart   # plus the workload args from the docs page
```

**Install pixi** (https://pixi.sh/latest/), then:
```cmd
cd C:\dev
irm https://raw.githubusercontent.com/ros2/ros2/refs/heads/jazzy/pixi.toml -OutFile pixi.toml
pixi install
```

**Configure the MSVC compiler** in every fresh `cmd.exe` you build from:
```cmd
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" x86_amd64
```

**Pull source and build.** `--merge-install` collapses every package's prefix into one to avoid blowing past the Windows PATH limit:
```cmd
pixi shell
vcs import --input https://raw.githubusercontent.com/ros2/ros2/jazzy/ros2.repos src
colcon build --merge-install
```

**Source the overlay per shell**, then smoke test:
```cmd
call C:\dev\jazzy\install\local_setup.bat
ros2 run demo_nodes_cpp talker
ros2 run demo_nodes_py listener
```

Common Windows traps (see Troubleshooting): antivirus locking files mid-build, Chocolatey's `patch.exe` triggering UAC and hanging the build, missing Visual C++ 2013 runtime causing Fast RTPS to fail to load.

---

## RHEL (build from source)
**Source**: https://docs.ros.org/en/jazzy/Installation/Alternatives/RHEL-Development-Setup.html

RHEL 9 64-bit (Tier 2 per REP-2000). Locale first:
```bash
locale
sudo dnf install langpacks-en glibc-langpack-en
export LANG=en_US.UTF-8
locale  # verify
```

EPEL + CodeReady Builder:
```bash
sudo dnf install 'dnf-command(config-manager)' epel-release -y
sudo dnf config-manager --set-enabled crb
```

Build deps (this list is canonical - copy as-is):
```bash
sudo dnf install -y \
  cmake gcc-c++ git make patch \
  python3-colcon-common-extensions python3-mypy python3-pip python3-pydocstyle \
  python3-pytest python3-pytest-cov python3-pytest-mock python3-pytest-repeat \
  python3-pytest-rerunfailures python3-pytest-runner python3-rosdep \
  python3-setuptools python3-vcstool wget
```

Some flake8 plugins aren't in EPEL, install via pip:
```bash
python3 -m pip install -U --user \
  flake8-blind-except==0.1.1 \
  flake8-class-newline \
  flake8-deprecated
```

Get sources, install rosdep deps, build:
```bash
mkdir -p ~/ros2_jazzy/src
cd ~/ros2_jazzy
vcs import --input https://raw.githubusercontent.com/ros2/ros2/jazzy/ros2.repos src

sudo dnf update
sudo rosdep init
rosdep update
rosdep install --from-paths src --ignore-src -y \
  --skip-keys "fastcdr rti-connext-dds-6.0.1 urdfdom_headers"

cd ~/ros2_jazzy/
colcon build --symlink-install
```

Same warning as Ubuntu: don't have `source /opt/ros/${ROS_DISTRO}/setup.bash` in `.bashrc` while building from source. `printenv | grep -i ROS` should be empty.

To skip OpenCV-heavy demos that frequently break on RHEL:
```bash
colcon build --symlink-install --packages-skip image_tools intra_process_demo
```

Optional: build with Clang instead of GCC:
```bash
sudo dnf install clang
export CC=clang
export CXX=clang++
colcon build --cmake-force-configure
```

Source overlay + smoke test:
```bash
. ~/ros2_jazzy/install/local_setup.bash
ros2 run demo_nodes_cpp talker
ros2 run demo_nodes_py listener
```

Uninstall: `rm -rf ~/ros2_jazzy`.

---

## macOS (build from source)
**Source**: https://docs.ros.org/en/jazzy/Installation/Alternatives/macOS-Development-Setup.html

macOS is **Tier 3** for Jazzy. The page states: "We currently support macOS Mojave (10.14)" - which is conspicuously old; expect issues on modern Apple Silicon and recent macOS releases. No binaries are provided.

Xcode and command line tools:
```bash
xcode-select --install
sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer
sudo xcodebuild -license
```

Homebrew system deps:
```bash
brew install asio assimp bison bullet cmake console_bridge cppcheck cunit eigen \
  freetype graphviz opencv openssl orocos-kdl pcre poco pyqt@5 python qt@5 sip \
  spdlog tinyxml2
```

Environment exports (OpenSSL location and Qt5 paths):
```bash
echo "export OPENSSL_ROOT_DIR=$(brew --prefix openssl)" >> ~/.zshrc
export CMAKE_PREFIX_PATH=$CMAKE_PREFIX_PATH:$(brew --prefix qt@5)
export PATH=$PATH:$(brew --prefix qt@5)/bin
```

Python build/runtime deps (note pinned versions - they matter):
```bash
python3 -m pip install --upgrade pip
python3 -m pip install -U \
  --config-settings="--global-option=build_ext" \
  --config-settings="--global-option=-I$(brew --prefix graphviz)/include/" \
  --config-settings="--global-option=-L$(brew --prefix graphviz)/lib/" \
  argcomplete catkin_pkg colcon-common-extensions coverage cryptography empy \
  flake8 flake8-blind-except==0.1.1 flake8-builtins flake8-class-newline \
  flake8-comprehensions flake8-deprecated flake8-docstrings flake8-import-order \
  flake8-quotes importlib-metadata jsonschema lark==1.1.1 lxml matplotlib mock \
  mypy==0.931 netifaces nose pep8 psutil pydocstyle pydot pygraphviz \
  pyparsing==2.4.7 pytest-mock rosdep rosdistro setuptools==59.6.0 vcstool
```

Disable **System Integrity Protection (SIP)** following Apple's recovery-mode procedure - SIP strips `DYLD_LIBRARY_PATH` from inherited environments, which breaks ROS 2's runtime library resolution.

Build:
```bash
mkdir -p ~/ros2_jazzy/src
cd ~/ros2_jazzy
vcs import --input https://raw.githubusercontent.com/ros2/ros2/jazzy/ros2.repos src

cd ~/ros2_jazzy/
colcon build --symlink-install --packages-skip-by-dep python_qt_binding
```

The `--packages-skip-by-dep python_qt_binding` is required because of "an unresolved issue with SIP, Qt@5, and PyQt5". GUI tools (RViz, rqt) won't fully work with this skip in place.

Source overlay (zsh on modern macOS):
```bash
. ~/ros2_jazzy/install/setup.zsh
ros2 run demo_nodes_cpp talker
ros2 run demo_nodes_py listener
```

For our drone perception work, macOS is not a target. This page exists for completeness; in practice run macOS users in Docker (`docker run -it ros:jazzy-ros-base`) instead of fighting this build.

---

## Latest development (source) - the rolling distro
**Source**: https://docs.ros.org/en/jazzy/Installation/Alternatives/Latest-Development-Setup.html

This page is a thin wrapper that points at "Testing binaries" and "Build from source" sub-flows for users tracking the bleeding edge (the Rolling distribution, the next-after-Jazzy work). It links out to the same per-platform development setup pages (Ubuntu / Windows / RHEL / macOS) used above, except they should be followed against the **rolling** branch rather than the **jazzy** branch.

In practice the only thing that changes vs. the Jazzy source instructions: the `vcs import` URL becomes `https://raw.githubusercontent.com/ros2/ros2/rolling/ros2.repos`, and you'd typically install into a separate workspace (e.g. `~/ros2_rolling`) so it doesn't collide with a Jazzy checkout.

Verbatim warning from the page: "The latest development does not go through the same rigorous testing as releases and is not recommended if you are looking for a stable version of ROS 2." Use this only when you are contributing PRs to ROS 2 core or you specifically need an unreleased fix. Production / research code should pin to Jazzy.

For maintaining either a Jazzy or Rolling source checkout once you have it set up, see the next page.

---

## Maintaining a source checkout
**Source**: https://docs.ros.org/en/jazzy/Installation/Maintaining-a-Source-Checkout.html

Once you have `~/ros2_jazzy` built from source, this page describes the periodic resync workflow.

**Refresh the `ros2.repos` manifest itself** - new packages get added or moved upstream:
```bash
cd ~/ros2_jazzy
mv -i ros2.repos ros2.repos.old
wget https://raw.githubusercontent.com/ros2/ros2/jazzy/ros2.repos
```
Windows equivalent:
```cmd
cd \dev\ros2_jazzy
curl -sk https://raw.githubusercontent.com/ros2/ros2/jazzy/ros2.repos -o ros2.repos
```

**Refresh remote knowledge in every cloned repo** (so new tags/branches show up):
```bash
vcs custom --args remote update
```

**Pull updated source** matching the new manifest:
```bash
vcs import src < ros2.repos
vcs pull src
```
Windows / PowerShell variant:
```bash
vcs import --input ros2.repos src
vcs pull src
```

**Rebuild** (incremental thanks to colcon):
```bash
colcon build --symlink-install
```

If a sync goes badly, nuke `build/`, `install/`, and `log/` and run a clean `colcon build` - that's almost always faster than debugging a half-broken incremental build.

**Snapshot your exact state** (handy for sharing reproducible workspaces or pinning a research bake):
```bash
cd ~/ros2_jazzy
vcs export src > my_ros2.repos
```

The exported `my_ros2.repos` pins every repo to its current commit hash, so feeding it back to `vcs import` recreates an identical checkout. Use this whenever you commit a working snapshot to your project repo.

---

## Installation Troubleshooting
**Source**: https://docs.ros.org/en/jazzy/How-To-Guides/Installation-Troubleshooting.html

Reference for symptom -> fix when an install or first run misbehaves. Organized by platform.

**General (any OS):**
- *Nodes don't see each other across machines on the same LAN.* DDS uses UDP multicast for discovery. Open the firewall to multicast traffic and verify with the ros2 multicast tools:
  ```bash
  sudo ufw allow in proto udp to 224.0.0.0/4
  sudo ufw allow in proto udp from 224.0.0.0/4
  ros2 multicast receive   # in one shell
  ros2 multicast send      # in another, possibly on another host
  ```
- *`import rclpy` fails even though the libs are present.* Mismatch between the Python interpreter used to build vs. run. After OS upgrades this is common - rebuild the workspace with the current `python3`.

**Linux:**
- *Internal compiler error / build killed on a low-RAM machine.* Build single-threaded:
  ```bash
  MAKEFLAGS=-j1 colcon build
  ```
- *`ros1_bridge` runs out of memory.* Drop a `COLCON_IGNORE` file into `src/ros2/ros1_bridge/` to skip it; needs ~4 GB to compile.
- *Two ROS 2 hosts on the same LAN cross-talk.* Set distinct `ROS_DOMAIN_ID` per machine: `export ROS_DOMAIN_ID=42` (any int 0-101).
- *Sourcing `setup.bash` raises an exception.* Bump colcon:
  ```bash
  colcon version-check
  sudo apt install python3-colcon* --only-upgrade
  ```
- *Conda + apt Python collisions.* Strip conda's bin dir out of `PATH` (and remove its `conda init` block from `.bashrc`) before sourcing ROS.
- *RViz2 won't open under Wayland.* Force XWayland:
  ```bash
  QT_QPA_PLATFORM=xcb rviz2
  ```

**macOS:**
- *Segfault running anything Python under pyenv.* Rebuild the pyenv Python with framework support enabled.
- *"Library not loaded" / dylib missing at runtime.* SIP is stripping `DYLD_LIBRARY_PATH`. Disable SIP (recovery mode).
- *`unknown type name 'Q_ENUM'` during build.* You have Qt4 instead of Qt5: `brew install qt@5`.
- *"symbol not found" with Homebrew OpenCV.* Re-link conflicting image libs:
  ```bash
  brew unlink libpng libtiff libjpeg
  # plus install_name_tool fixups
  ```
- *Xcode developer-dir mismatch.*
  ```bash
  xcode-select --install
  sudo xcodebuild -license accept
  sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
  ```
- *"Failed to detect successful installation of [qt5]".*
  ```bash
  cd /usr/local/Cellar
  sudo ln -s qt qt5
  ```

**Windows:**
- *`import` fails despite DLLs being present.* Check every prereq from the install doc; use the Dependencies tool to find the missing DLL; confirm the workspace is actually sourced (`call install\local_setup.bat`).
- *CMake error: "file modification time is in the future".* Antivirus is touching files mid-build. Exclude the workspace from Windows Defender.
- *Path > 260 chars error.* Enable long paths via registry:
  - `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem\LongPathsEnabled = 1`
  - or Group Policy: enable "Win32 long paths".
- *CMake can't find asio / tinyxml2 / eigen.* Reinstall the offending Chocolatey package: `choco uninstall <pkg>` then reinstall.
- *`patch.exe` opens a UAC dialog and stalls the build.*
  ```cmd
  choco uninstall patch
  colcon build --cmake-clean-cache
  ```
  (Falls back to Git's bundled patch.)
- *"Failed to load Fast RTPS shared library."* Missing `msvcr20.dll` (VC++ 2013 redistributable). Install it from Microsoft.
- *"Failed to create process."* Python isn't on PATH where ROS expects it (default `C:\Python38\`).
- *RViz segfaults under WSL2.* Force software OpenGL:
  ```bash
  export LIBGL_ALWAYS_SOFTWARE=true && rviz2
  ```

When you hit any of these in the field, search this section first - the fixes are usually one command and the docs list them explicitly.

---

## Installing ROS 2 on a Raspberry Pi
**Source**: https://docs.ros.org/en/jazzy/How-To-Guides/Installing-on-Raspberry-Pi.html

Confirms ARM is supported: aarch64 is **Tier 1**, arm32 is **Tier 3**. The official guide spells out two install paths and stays brief - no Pi-model enumeration, no swap/thermal/USB-power advice in the doc itself. (Practical experience: use Pi 4B 4GB+ or Pi 5 with active cooling and a fast SD/USB-SSD; older Pis run out of RAM during compiles.)

**Path 1 - Ubuntu Server 24.04 arm64 + deb install (recommended for this project).**
1. Flash Ubuntu 24.04 arm64 from https://ubuntu.com/download/raspberry-pi using Raspberry Pi Imager.
2. Verify the OS choice against REP-2000 (Jazzy = Noble = Ubuntu 24.04).
3. **Critical step the docs call out:** edit `/etc/apt/sources.list.d/ubuntu.sources` to enable `noble`, `noble-updates`, and `noble-backports`. Example block from the doc:
   ```
   Types: deb
   URIs: http://ports.ubuntu.com/ubuntu-ports/
   Suites: noble noble-updates noble-backports
   ```
   Without `-updates` and `-backports`, several rosdep deps fail to resolve.
4. Then follow the standard Ubuntu deb install above (locale -> apt source -> `sudo apt install ros-jazzy-ros-base`). Pick `ros-base` not `desktop` on a headless Pi - skipping RViz/Qt saves ~700 MB.

**Path 2 - Raspberry Pi OS 64-bit + Docker.** The Pi-native OS isn't a Tier 1 ROS 2 host, so use containers:
1. Flash 64-bit Raspberry Pi OS from https://www.raspberrypi.com/software/operating-systems/.
2. Install Docker per the Debian instructions.
3. Pull and run the official ROS image:
   ```bash
   docker pull ros:jazzy-ros-core
   docker run -it --rm ros:jazzy-ros-core
   ```

The doc does **not** cover, but you'll want to know:
- Set `ROS_DOMAIN_ID` to the same integer on every Pi/host that should communicate, different from any other ROS 2 LAN.
- For low-RAM Pis (2 GB), enable swap before any colcon build.
- For multicast across a Pi's wifi link, confirm the AP doesn't drop UDP multicast (cheap routers often do).
- CycloneDDS is widely recommended over Fast DDS on Pi for lower CPU use; install with `sudo apt install ros-jazzy-rmw-cyclonedds-cpp` and `export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp`.

For the drone targeting research project, the canonical Pi setup is: Pi 5 (or Pi 4B 4GB+) -> Ubuntu Server 24.04 arm64 -> ros-jazzy-ros-base -> CycloneDDS.
