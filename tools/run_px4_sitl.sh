#!/bin/bash
# Launch PX4 SITL (x500 quadrotor) in Gazebo Harmonic.
#
# Usage:
#   run_px4_sitl.sh                  # interactive menu
#   run_px4_sitl.sh <world>          # launch directly with named world
#   run_px4_sitl.sh -H <world>       # headless (no GUI, OGRE 2 internal)
#   run_px4_sitl.sh -h               # help
#
# GUI mode forces PX4_GZ_SIM_RENDER_ENGINE=ogre (OGRE 1) — required on
# the project's RTX 3050 4 GB iGPU to avoid lockstep starvation. See
# .claude/skills/px4-gazebo/reference/08_troubleshooting.md.

set -euo pipefail

PX4_DIR="/media/abrar/AbrarSSD/ROS/PX4-Autopilot"
PROJ_ROOT="/media/abrar/AbrarSSD/ROS/drone_targeting_research"
PROJ_WORLDS="$PROJ_ROOT/ros2_ws/src/drone_sim_bringup/worlds"

# Resource paths so `model://...` URIs inside project worlds resolve.
# Mirror what kinematic_rig.launch.py adds (clearpath_gz meshes for orchard/
# office/etc., drone_description models for camera_rig, bringup share).
# We include the SOURCE models dir too so newly-authored models work
# without re-running `colcon build`.
PROJ_RESOURCE_PATHS=(
  "$PROJ_ROOT/ros2_ws/src/drone_description/models"
  "$PROJ_ROOT/ros2_ws/install/drone_description/share/drone_description/models"
  "$PROJ_ROOT/ros2_ws/install/drone_sim_bringup/share/drone_sim_bringup"
  "$PROJ_ROOT/ros2_ws/install/clearpath_gz/share/clearpath_gz/meshes"
  "$PROJ_ROOT/ros2_ws/install/clearpath_gz/share/clearpath_gz"
  "$PX4_DIR/Tools/simulation/gz/models"
)

# Vehicle catalogue. Each entry is "model_name:SYS_AUTOSTART:description".
# SYS_AUTOSTART is the airframe ID PX4 loads (motor mixing, rate gains,
# etc.) — it MUST match the model's geometry or the drone won't fly
# correctly. x500_stereo_depth inherits x500 via merge include, so it
# uses 4001 too.
DRONES=(
  "x500_stereo_depth:4001:x500 + OakD-Lite stereo (L+R) + depth pod (project default)"
  "x500:4001:bare stock x500 quadrotor (no cameras)"
  "px4vision:4006:Holybro PX4Vision — most agile stock airframe (no cameras)"
  "x500_depth:4002:x500 + OakD-Lite (1 RGB + depth, no stereo right)"
  "x500_vision:4005:x500 + ground-truth odometry publisher"
  "x500_mono_cam:4010:x500 + forward mono camera (1280x960, 100° FOV)"
  "x500_mono_cam_down:4014:x500 + downward mono camera (precision landing)"
  "x500_lidar_2d:4013:x500 + 2D lidar (270°, 0.1–30 m)"
  "x500_lidar_down:4016:x500 + downward 1D rangefinder"
  "x500_lidar_front:4017:x500 + forward 1D lidar (collision prevention)"
  "x500_gimbal:4019:x500 + 3-axis gimbal camera"
  "x500_flow:4021:x500 + downward optical flow + range (GPS-denied)"
  "omnicopter:8011:8-rotor fully-actuated platform"
  "rover_ackermann:4012:Ackermann-steering ground rover (target candidate)"
)

DEFAULT_DRONE_INDEX=1   # x500_stereo_depth

# Format: "world_name:human-readable description"
WORLDS=(
  "default:Empty grey ground (smoke test)"
  "baylands:Large coastal park, trees + water (best stock outdoor)"
  "walls:Obstacle walls (collision-prevention testing)"
  "windy:Default + simulated wind"
  "aruco:ArUco marker on ground (precision-landing test)"
  "moving_platform:5x5m platform that moves on its own (landing-target prototype)"
  "lawn:Flat green field"
  "forest:Dense trees (heavy on iGPU)"
  "rover:Rover-tuned ground"
  "orchard_labeled:Project: 48x38m olive orchard, photo-textured, semantic labels"
  "construction_labeled:Project: ~30x30m construction site, photo-textured, semantic labels"
)

HEADLESS=0
MODEL_ARG=""

usage() {
  cat <<EOF
Usage: $(basename "$0") [-H] [-m model] [world_name]

Options:
  -H            headless (no Gazebo GUI)
  -m <model>    drone model (skip the drone picker)
  -h            this help

If no world_name is given, presents an interactive world picker.
If no -m given, presents an interactive drone picker.

Available worlds:
$(for e in "${WORLDS[@]}"; do printf "  %-25s  %s\n" "${e%%:*}" "${e##*:}"; done)

Available drones (model_name → SYS_AUTOSTART):
$(for e in "${DRONES[@]}"; do n="${e%%:*}"; r="${e#*:}"; a="${r%%:*}"; d="${r#*:}"; printf "  %-22s  %-6s  %s\n" "$n" "$a" "$d"; done)
EOF
  exit 1
}

while getopts ":Hm:h" opt; do
  case "$opt" in
    H) HEADLESS=1 ;;
    m) MODEL_ARG="$OPTARG" ;;
    h) usage ;;
    \?) echo "Unknown flag: -$OPTARG" >&2; usage ;;
  esac
done
shift $((OPTIND - 1))

WORLD="${1:-}"

if [ -z "$WORLD" ]; then
  echo
  echo "Pick a world to launch:"
  echo
  i=1
  for entry in "${WORLDS[@]}"; do
    name="${entry%%:*}"
    desc="${entry##*:}"
    printf "  %2d) %-25s  %s\n" "$i" "$name" "$desc"
    i=$((i+1))
  done
  echo
  read -rp "Number or name [default: 1]: " CHOICE
  CHOICE="${CHOICE:-1}"

  if [[ "$CHOICE" =~ ^[0-9]+$ ]]; then
    if [ "$CHOICE" -lt 1 ] || [ "$CHOICE" -gt "${#WORLDS[@]}" ]; then
      echo "Invalid number: $CHOICE" >&2
      exit 1
    fi
    entry="${WORLDS[$((CHOICE-1))]}"
    WORLD="${entry%%:*}"
  else
    WORLD="$CHOICE"
  fi
fi

# Drone picker — same UX as the world picker. Resolves to a "name:autostart"
# pair which we then use for both PX4_SIM_MODEL and PX4_SYS_AUTOSTART.
# Sources, in priority order:
#   1) -m <model> flag
#   2) PX4_SIM_MODEL env var (power-user override)
#   3) Interactive picker (default)
DRONE_NAME=""
DRONE_AUTOSTART=""
chosen_arg="${MODEL_ARG:-${PX4_SIM_MODEL:-}}"
if [ -n "$chosen_arg" ]; then
  for entry in "${DRONES[@]}"; do
    n="${entry%%:*}"
    if [ "$n" = "$chosen_arg" ]; then
      rest="${entry#*:}"
      DRONE_NAME="$n"
      DRONE_AUTOSTART="${rest%%:*}"
      break
    fi
  done
  if [ -z "$DRONE_NAME" ]; then
    echo "Unknown drone model: $chosen_arg" >&2
    echo "Run with -h for the catalogue, or use the interactive picker." >&2
    exit 1
  fi
else
  echo
  echo "Pick a drone model:"
  echo
  i=1
  for entry in "${DRONES[@]}"; do
    n="${entry%%:*}"
    rest="${entry#*:}"
    a="${rest%%:*}"
    desc="${rest#*:}"
    printf "  %2d) %-22s  %-6s  %s\n" "$i" "$n" "$a" "$desc"
    i=$((i+1))
  done
  echo
  read -rp "Number or name [default: $DEFAULT_DRONE_INDEX = ${DRONES[$((DEFAULT_DRONE_INDEX-1))]%%:*}]: " DCHOICE
  DCHOICE="${DCHOICE:-$DEFAULT_DRONE_INDEX}"

  if [[ "$DCHOICE" =~ ^[0-9]+$ ]]; then
    if [ "$DCHOICE" -lt 1 ] || [ "$DCHOICE" -gt "${#DRONES[@]}" ]; then
      echo "Invalid number: $DCHOICE" >&2
      exit 1
    fi
    entry="${DRONES[$((DCHOICE-1))]}"
  else
    entry=""
    for e in "${DRONES[@]}"; do
      if [ "${e%%:*}" = "$DCHOICE" ]; then entry="$e"; break; fi
    done
    if [ -z "$entry" ]; then
      echo "Unknown drone name: $DCHOICE" >&2; exit 1
    fi
  fi
  DRONE_NAME="${entry%%:*}"
  rest="${entry#*:}"
  DRONE_AUTOSTART="${rest%%:*}"
fi

PX4_SIM_MODEL="$DRONE_NAME"

echo
echo "==> world:    $WORLD"
echo "==> drone:    $DRONE_NAME (SYS_AUTOSTART=$DRONE_AUTOSTART)"
echo "==> headless: $HEADLESS"

# Reap any stale gz sim / px4 processes from a previous run. PX4 sometimes
# doesn't clean its child gz sim on `shutdown`, and the next launch then
# attaches to the old world ("gazebo already running world: ...") instead
# of starting a fresh one.
STALE=$(pgrep -af 'gz sim ' | grep -v 'fuel download' | awk '{print $1}' || true)
STALE_PX4=$(pgrep -f 'build/px4_sitl_default/bin/px4' || true)
if [ -n "$STALE" ] || [ -n "$STALE_PX4" ]; then
  echo "==> reaping stale processes:"
  [ -n "$STALE" ]      && pgrep -af 'gz sim ' | grep -v 'fuel download' | sed 's/^/    /'
  [ -n "$STALE_PX4" ]  && pgrep -af 'build/px4_sitl_default/bin/px4' | sed 's/^/    /'
  # SIGTERM first; SIGKILL anything that doesn't die in 2 sec
  [ -n "$STALE" ]     && kill     $STALE     2>/dev/null || true
  [ -n "$STALE_PX4" ] && kill     $STALE_PX4 2>/dev/null || true
  sleep 2
  STALE=$(pgrep -af 'gz sim ' | grep -v 'fuel download' | awk '{print $1}' || true)
  STALE_PX4=$(pgrep -f 'build/px4_sitl_default/bin/px4' || true)
  [ -n "$STALE" ]     && kill -9  $STALE     2>/dev/null || true
  [ -n "$STALE_PX4" ] && kill -9  $STALE_PX4 2>/dev/null || true
fi

# PX4 looks for worlds at $PX4_DIR/Tools/simulation/gz/worlds/<name>.sdf —
# it does NOT search GZ_SIM_RESOURCE_PATH for the world file itself
# (that env var is only for model:// URIs inside the world). Symlink the
# project worlds in so they're findable by name.
PX4_WORLDS_DIR="$PX4_DIR/Tools/simulation/gz/worlds"
for proj_world in "$PROJ_WORLDS"/*.sdf; do
  [ -e "$proj_world" ] || continue
  base="$(basename "$proj_world")"
  ln -sf "$proj_world" "$PX4_WORLDS_DIR/$base"
done

# Same hardcoded-path issue applies to MODELS. PX4 spawns by reading
# $PX4_DIR/Tools/simulation/gz/models/<PX4_SIM_MODEL>/model.sdf — does
# not honour GZ_SIM_RESOURCE_PATH for that file. Symlink each project
# model in so PX4_SIM_MODEL=x500_stereo_depth (and friends) resolve.
PX4_MODELS_DIR="$PX4_DIR/Tools/simulation/gz/models"
PROJ_MODELS_SRC="$PROJ_ROOT/ros2_ws/src/drone_description/models"
for proj_model in "$PROJ_MODELS_SRC"/*/; do
  [ -d "$proj_model" ] || continue
  base="$(basename "$proj_model")"
  ln -sfn "$proj_model" "$PX4_MODELS_DIR/$base"
done

# Idempotently install an ImageDisplay panel into ~/.gz/sim/8/gui.config
# so the gz GUI shows the drone's left-camera view (topic /stereo/left)
# in a docked panel. Marker comment lets us detect prior install.
GUI_CONFIG="$HOME/.gz/sim/8/gui.config"
GUI_MARKER="<!-- run_px4_sitl.sh: stereo-left ImageDisplay -->"
if [ -f "$GUI_CONFIG" ] && ! grep -qF "$GUI_MARKER" "$GUI_CONFIG"; then
  echo "==> appending stereo-left ImageDisplay panel to $GUI_CONFIG"
  cp "$GUI_CONFIG" "$GUI_CONFIG.bak.$(date +%s)"
  cat >>"$GUI_CONFIG" <<EOF

$GUI_MARKER
<plugin filename="ImageDisplay" name="Stereo Left">
  <gz-gui>
    <title>Stereo Left</title>
    <property type="string" key="state">docked</property>
  </gz-gui>
  <topic>stereo/left</topic>
  <topic_picker>true</topic_picker>
</plugin>
EOF
fi

echo "==> Sourcing ROS 2 Jazzy + setting GZ_DISTRO=harmonic..."
echo

# ROS's setup.bash references unbound vars internally; turn off nounset
# just for the source, then restore.
set +u
# shellcheck disable=SC1091
source /opt/ros/jazzy/setup.bash
set -u
export GZ_DISTRO=harmonic

# Fuel-shortcut symlinks. The Fuel cache stores models at
# ~/.gz/fuel/<server>/<owner>/models/<name>/<version>/, but old-style
# `model://<name>/...` URIs (used by baylands and other vintage
# OpenRobotics models) need `<name>` to be a directory with the model
# contents directly, not behind a `<version>/` layer. Build a flat
# shortcut tree of `<name> -> <latest_version>` symlinks and add it
# to GZ_SIM_RESOURCE_PATH.
FUEL_SHORTCUTS_DIR="$HOME/.gz/extra_models"
mkdir -p "$FUEL_SHORTCUTS_DIR"
for owner_dir in "$HOME"/.gz/fuel/fuel.gazebosim.org/*/models/; do
  [ -d "$owner_dir" ] || continue
  for model_root in "$owner_dir"*/; do
    [ -d "$model_root" ] || continue
    name="$(basename "$model_root")"
    latest_ver=$(find "$model_root" -mindepth 1 -maxdepth 1 -type d \
                  -regextype posix-extended -regex '.*/[0-9]+$' \
                  -printf "%f\n" 2>/dev/null | sort -n | tail -1)
    if [ -n "$latest_ver" ] && [ -e "$model_root$latest_ver/model.sdf" ]; then
      ln -sfn "$model_root$latest_ver" "$FUEL_SHORTCUTS_DIR/$name"
    fi
  done
done

# Build GZ_SIM_RESOURCE_PATH from the project's resource dirs + the
# Fuel shortcuts (these are what let `model://orchard/...`,
# `model://camera_rig/...`, `model://baylands/...` etc. resolve).
RP=""
for p in "${PROJ_RESOURCE_PATHS[@]}" "$PROJ_WORLDS" "$FUEL_SHORTCUTS_DIR"; do
  [ -d "$p" ] && RP="${RP:+$RP:}$p"
done
export GZ_SIM_RESOURCE_PATH="$RP:${GZ_SIM_RESOURCE_PATH:-}"

cd "$PX4_DIR/build/px4_sitl_default/etc"

# When PX4 exits (user typed `shutdown` in pxh>, or Ctrl-C, or crash),
# reap any leftover gz sim server / GUI processes. PX4 doesn't always
# kill its sibling GUI window on shutdown.
cleanup_gz() {
  echo
  echo "==> reaping gz processes..."
  pkill -TERM -f 'gz sim '       2>/dev/null || true
  sleep 1
  pkill -KILL -f 'gz sim '       2>/dev/null || true
  echo "==> done."
}
trap cleanup_gz EXIT INT TERM

if [ "$HEADLESS" -eq 1 ]; then
  env \
    HEADLESS=1 \
    PX4_SYS_AUTOSTART="$DRONE_AUTOSTART" \
    PX4_SIM_MODEL="$PX4_SIM_MODEL" \
    PX4_GZ_WORLD="$WORLD" \
    ../bin/px4
else
  env \
    PX4_GZ_SIM_RENDER_ENGINE=ogre \
    PX4_SYS_AUTOSTART="$DRONE_AUTOSTART" \
    PX4_SIM_MODEL="$PX4_SIM_MODEL" \
    PX4_GZ_WORLD="$WORLD" \
    ../bin/px4
fi
