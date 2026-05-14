import os
import re

from ament_index_python.packages import get_package_share_directory, PackageNotFoundError

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node


def _resolve_world_path(world_file: str) -> str:
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
    try:
        with open(world_path, 'r', encoding='utf-8') as f:
            head = f.read(4096)
        m = re.search(r"<world\s+name=['\"]([^'\"]+)['\"]", head)
        if m:
            return m.group(1)
    except OSError:
        pass
    return default


def _build(context, *args, **kwargs):
    world = LaunchConfiguration('world').perform(context)
    override = LaunchConfiguration('world_name').perform(context)
    world_path = _resolve_world_path(world)
    world_name = override or _world_internal_name(world_path, world.rsplit('.', 1)[0])

    return [Node(
        package='drone_sim_bringup',
        executable='dataset_capture',
        name='dataset_capture',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'service_name': f'/world/{world_name}/set_pose',
            'run_id': LaunchConfiguration('run_id').perform(context),
            'output_dir': LaunchConfiguration('output_dir').perform(context),
        }],
    )]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('world', default_value='empty_lab.sdf',
                              description='Must match the world used in kinematic_rig.launch.py'),
        DeclareLaunchArgument('world_name', default_value='',
                              description='Override for the SDF\'s internal <world name=>. '
                                          'Auto-detected from the SDF if blank.'),
        DeclareLaunchArgument('run_id', default_value=''),
        DeclareLaunchArgument(
            'output_dir',
            default_value='/media/abrar/AbrarSSD/ROS/drone_targeting_research/data/captures'),
        OpaqueFunction(function=_build),
    ])
