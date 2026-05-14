import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'drone_sim_bringup'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        (os.path.join('share', package_name), ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob(os.path.join('launch', '*.launch.py'))),
        (os.path.join('share', package_name, 'config'),
            glob(os.path.join('config', '*.yaml'))),
        (os.path.join('share', package_name, 'worlds'),
            glob(os.path.join('worlds', '*.sdf'))),
        (os.path.join('share', package_name, 'materials', 'textures'),
            glob(os.path.join('materials', 'textures', '*'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='abrar',
    maintainer_email='abrarnazib@gmail.com',
    description='Launch files, bridge config, worlds, and pose teleporter for the kinematic camera rig.',
    license='Apache-2.0',
    extras_require={
        'test': ['pytest'],
    },
    entry_points={
        'console_scripts': [
            'pose_teleporter = drone_sim_bringup.pose_teleporter:main',
            'dataset_capture = drone_sim_bringup.dataset_capture:main',
        ],
    },
)
