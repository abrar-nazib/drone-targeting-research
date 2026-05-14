"""Teleport the camera_rig through a list of poses by calling the
bridged Gazebo set_pose service. Used to validate the teleport plumbing
before the dataset-capture node lands on top of it."""

import math
import time
from dataclasses import dataclass

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Pose, Point, Quaternion
from ros_gz_interfaces.srv import SetEntityPose
from ros_gz_interfaces.msg import Entity


@dataclass
class RigPose:
    x: float
    y: float
    z: float
    yaw: float


def yaw_to_quat(yaw: float) -> Quaternion:
    half = 0.5 * yaw
    return Quaternion(x=0.0, y=0.0, z=math.sin(half), w=math.cos(half))


DEFAULT_POSES = [
    RigPose(x=-2.0, y=0.0, z=1.5, yaw=0.0),
    RigPose(x=-1.0, y=-2.0, z=1.2, yaw=0.5),
    RigPose(x=0.0, y=-2.0, z=2.0, yaw=1.0),
    RigPose(x=1.0, y=2.0, z=1.5, yaw=-1.0),
    RigPose(x=-2.0, y=2.0, z=1.0, yaw=-0.5),
]


class PoseTeleporter(Node):
    def __init__(self):
        super().__init__('pose_teleporter')

        self.declare_parameter('rig_name', 'camera_rig')
        self.declare_parameter('settle_seconds', 1.0)
        self.declare_parameter('service_name', '/world/empty_lab/set_pose')

        self.rig_name = self.get_parameter('rig_name').value
        self.settle_seconds = float(self.get_parameter('settle_seconds').value)
        service_name = self.get_parameter('service_name').value

        self.cli = self.create_client(SetEntityPose, service_name)
        self.get_logger().info(f'Waiting for service {service_name}...')
        if not self.cli.wait_for_service(timeout_sec=15.0):
            raise RuntimeError(f'Service {service_name} not available after 15 s')
        self.get_logger().info('Service ready.')

    def teleport(self, pose: RigPose) -> bool:
        req = SetEntityPose.Request()
        req.entity = Entity(name=self.rig_name, type=Entity.MODEL)
        req.pose = Pose(
            position=Point(x=pose.x, y=pose.y, z=pose.z),
            orientation=yaw_to_quat(pose.yaw),
        )
        future = self.cli.call_async(req)
        rclpy.spin_until_future_complete(self, future, timeout_sec=5.0)
        if not future.done():
            self.get_logger().error('Service call timed out')
            return False
        result = future.result()
        if result is None or not result.success:
            self.get_logger().error(f'Set pose failed: {result}')
            return False
        return True

    def run(self, poses):
        for i, p in enumerate(poses):
            self.get_logger().info(
                f'[{i+1}/{len(poses)}] -> x={p.x:+.2f} y={p.y:+.2f} z={p.z:+.2f} yaw={p.yaw:+.2f}')
            if not self.teleport(p):
                return False
            time.sleep(self.settle_seconds)
        return True


def main():
    rclpy.init()
    node = PoseTeleporter()
    try:
        ok = node.run(DEFAULT_POSES)
        node.get_logger().info('Done.' if ok else 'Aborted.')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
