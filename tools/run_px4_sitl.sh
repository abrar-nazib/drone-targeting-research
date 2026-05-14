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
PROJ_RESOURCE_PATHS=(
  "$PROJ_ROOT/ros2_ws/install/drone_description/share/drone_description/models"
  "$PROJ_ROOT/ros2_ws/install/drone_sim_bringup/share/drone_sim_bringup"
  "$PROJ_ROOT/ros2_ws/install/clearpath_gz/share/clearpath_gz/meshes"
  "$PROJ_ROOT/ros2_ws/install/clearpath_gz/share/clearpath_gz"
)

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

usage() {
  cat <<EOF
Usage: $(basename "$0") [-H] [world_name]

Options:
  -H            headless (no Gazebo GUI)
  -h            this help

If no world_name is given, presents an interactive menu.
Available worlds:
$(for e in "${WORLDS[@]}"; do printf "  %-25s  %s\n" "${e%%:*}" "${e##*:}"; done)
EOF
  exit 1
}

while getopts ":Hh" opt; do
  case "$opt" in
    H) HEADLESS=1 ;;
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

echo
echo "==> world:    $WORLD"
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

echo "==> Sourcing ROS 2 Jazzy + setting GZ_DISTRO=harmonic..."
echo

# ROS's setup.bash references unbound vars internally; turn off nounset
# just for the source, then restore.
set +u
# shellcheck disable=SC1091
source /opt/ros/jazzy/setup.bash
set -u
export GZ_DISTRO=harmonic
# Build GZ_SIM_RESOURCE_PATH from the project's resource dirs (these are
# what let `model://orchard/...`, `model://camera_rig/...`, etc. resolve).
RP=""
for p in "${PROJ_RESOURCE_PATHS[@]}" "$PROJ_WORLDS"; do
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
    PX4_SYS_AUTOSTART=4001 \
    PX4_SIM_MODEL=x500 \
    PX4_GZ_WORLD="$WORLD" \
    ../bin/px4
else
  env \
    PX4_GZ_SIM_RENDER_ENGINE=ogre \
    PX4_SYS_AUTOSTART=4001 \
    PX4_SIM_MODEL=x500 \
    PX4_GZ_WORLD="$WORLD" \
    ../bin/px4
fi
