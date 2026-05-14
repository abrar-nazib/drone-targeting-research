import os
import re

from ament_index_python.packages import get_package_share_directory, PackageNotFoundError

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
    SetEnvironmentVariable,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node


# Props spawned alongside the camera rig. Each entry is:
#   (instance_name, fuel_cache_subpath, x, y, z, yaw)
# The Fuel cache files have been pre-labeled by tools/label_fuel_model.py,
# so spawning them produces correctly labeled segmentation pixels.
LABELED_PROPS = [
    ('pickup_1',     'openrobotics/models/pickup',           6.0,  0.0, 0.0,  0.0),
    ('suv_1',        'openrobotics/models/suv',              6.0,  4.0, 0.0,  0.3),
    ('hatchback_1',  'openrobotics/models/hatchback blue',   6.0, -4.0, 0.0, -0.3),
    ('pine_tree_1',  'openrobotics/models/pine tree',       10.0,  6.0, 0.0,  0.0),
    ('pine_tree_2',  'openrobotics/models/pine tree',       -8.0,  6.0, 0.0,  0.0),
    ('cone_1',       'openrobotics/models/construction cone', 3.0,  1.0, 0.0,  0.0),
    ('cone_2',       'openrobotics/models/construction cone', 3.0, -1.0, 0.0,  0.0),
    ('lamp_post_1',  'openrobotics/models/lamp post',         3.0,  5.0, 0.0,  0.0),
]


def _resolve_fuel_model_sdf(subpath: str) -> str:
    """Find the highest-version model.sdf for a Fuel-cached prop."""
    cache = os.path.expanduser('~/.gz/fuel/fuel.gazebosim.org')
    cur = cache
    for part in subpath.strip('/').split('/'):
        if not os.path.isdir(cur):
            return ''
        match = next((c for c in os.listdir(cur) if c.lower() == part.lower()), None)
        if match is None:
            return ''
        cur = os.path.join(cur, match)
    if not os.path.isdir(cur):
        return ''
    versions = sorted([v for v in os.listdir(cur) if v.isdigit()], key=int, reverse=True)
    if not versions:
        return ''
    return os.path.join(cur, versions[0], 'model.sdf')


def _resolve_world_path(world_file: str) -> str:
    """Search for the world SDF in this project's worlds dir, then in
    optional sister packages (clearpath_gz)."""
    candidate_dirs = [
        os.path.join(get_package_share_directory('drone_sim_bringup'), 'worlds'),
    ]
    for pkg in ('clearpath_gz',):
        try:
            candidate_dirs.append(os.path.join(get_package_share_directory(pkg), 'worlds'))
        except PackageNotFoundError:
            pass
    for d in candidate_dirs:
        candidate = os.path.join(d, world_file)
        if os.path.isfile(candidate):
            return candidate
    return os.path.join(candidate_dirs[0], world_file)


def _world_internal_name(world_path: str, default: str) -> str:
    """Read <world name='...'> from the SDF; fall back to default."""
    try:
        with open(world_path, 'r', encoding='utf-8') as f:
            head = f.read(4096)
        m = re.search(r"<world\s+name=['\"]([^'\"]+)['\"]", head)
        if m:
            return m.group(1)
    except OSError:
        pass
    return default


def _build_actions(context, *args, **kwargs):
    bringup_share = get_package_share_directory('drone_sim_bringup')
    description_share = get_package_share_directory('drone_description')
    ros_gz_sim_share = get_package_share_directory('ros_gz_sim')

    world_file = LaunchConfiguration('world').perform(context)
    world_path = _resolve_world_path(world_file)

    world_name_override = LaunchConfiguration('world_name').perform(context)
    if world_name_override:
        world_name = world_name_override
    else:
        world_name = _world_internal_name(world_path, os.path.splitext(world_file)[0])

    bridge_config = os.path.join(bringup_share, 'config', 'ros_gz_bridge.yaml')
    rig_sdf = os.path.join(description_share, 'models', 'camera_rig', 'model.sdf')

    spawn_x = LaunchConfiguration('spawn_x').perform(context)
    spawn_y = LaunchConfiguration('spawn_y').perform(context)
    spawn_z = LaunchConfiguration('spawn_z').perform(context)

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_share, 'launch', 'gz_sim.launch.py')),
        launch_arguments={'gz_args': f'-r -v 3 {world_path}'}.items(),
    )

    spawn_rig = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'camera_rig',
            '-file', rig_sdf,
            '-x', spawn_x, '-y', spawn_y, '-z', spawn_z,
        ],
        output='screen',
    )

    spawn_props = []
    if LaunchConfiguration('spawn_props').perform(context).lower() == 'true':
        for name, subpath, x, y, z, yaw in LABELED_PROPS:
            sdf = _resolve_fuel_model_sdf(subpath)
            if not sdf:
                continue
            spawn_props.append(Node(
                package='ros_gz_sim',
                executable='create',
                name=f'spawn_{name}',
                arguments=[
                    '-name', name,
                    '-file', sdf,
                    '-x', str(x), '-y', str(y), '-z', str(z), '-Y', str(yaw),
                ],
                output='log',
            ))

    topic_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='ros_gz_topic_bridge',
        parameters=[{'config_file': bridge_config, 'use_sim_time': True}],
        output='screen',
    )

    service_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='ros_gz_service_bridge',
        arguments=[
            f'/world/{world_name}/set_pose@ros_gz_interfaces/srv/SetEntityPose',
        ],
        output='screen',
    )

    return [gz_sim, spawn_rig, topic_bridge, service_bridge]


def generate_launch_description():
    description_share = get_package_share_directory('drone_description')
    bringup_share = get_package_share_directory('drone_sim_bringup')
    extra_paths = [
        os.path.join(description_share, 'models'),
        bringup_share,
    ]
    # Pull in clearpath_gz/meshes if the package is installed, so worlds
    # using `model://office/...` style URIs resolve.
    try:
        cp_share = get_package_share_directory('clearpath_gz')
        extra_paths.append(os.path.join(cp_share, 'meshes'))
        extra_paths.append(cp_share)
    except PackageNotFoundError:
        pass

    set_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=':'.join(extra_paths) + ':' + os.environ.get('GZ_SIM_RESOURCE_PATH', ''),
    )
    set_x11 = SetEnvironmentVariable(name='QT_QPA_PLATFORM', value='xcb')
    set_glx_vendor = SetEnvironmentVariable(name='__GLX_VENDOR_LIBRARY_NAME', value='nvidia')

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        condition=IfCondition(LaunchConfiguration('rviz')),
        output='log',
    )

    return LaunchDescription([
        DeclareLaunchArgument('world', default_value='empty_lab.sdf',
                              description='World SDF filename. Searched in this package\'s worlds/, '
                                          'then in clearpath_gz/worlds/ if installed.'),
        DeclareLaunchArgument('world_name', default_value='',
                              description='Override for the SDF\'s internal <world name=>. '
                                          'Used to derive /world/<name>/set_pose service path. '
                                          'Auto-detected from the SDF if blank.'),
        DeclareLaunchArgument('spawn_props', default_value='false',
                              description='Also spawn the labeled prop set (cars/trees/cones/etc.) '
                                          'alongside the camera rig.'),
        DeclareLaunchArgument('spawn_x', default_value='0.0'),
        DeclareLaunchArgument('spawn_y', default_value='0.0'),
        DeclareLaunchArgument('spawn_z', default_value='1.5'),
        DeclareLaunchArgument('rviz', default_value='false',
                              description='Open RViz alongside Gazebo.'),
        set_resource_path,
        set_x11,
        set_glx_vendor,
        OpaqueFunction(function=_build_actions),
        rviz,
    ])
