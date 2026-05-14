"""Capture stereo + semantic-segmentation frames at a list of fixed poses.

For each pose: teleport the camera_rig, wait for the first frame on each
subscribed topic with header.stamp > teleport time (so we never save a
stale pre-teleport frame), then write PNGs + metadata to a per-pose dir.

The node is designed to run with use_sim_time=True so all timing is in
sim seconds; this works correctly regardless of real-time factor.
"""

import json
import math
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data

from geometry_msgs.msg import Pose, Point, Quaternion
from ros_gz_interfaces.msg import Entity
from ros_gz_interfaces.srv import SetEntityPose
from sensor_msgs.msg import CameraInfo, Image


@dataclass
class RigPose:
    x: float
    y: float
    z: float
    yaw: float


def yaw_to_quat(yaw: float) -> Quaternion:
    half = 0.5 * yaw
    return Quaternion(x=0.0, y=0.0, z=math.sin(half), w=math.cos(half))


# Looking at the three labelled shapes in empty_lab.sdf from a few angles.
DEFAULT_POSES: List[RigPose] = [
    RigPose(x=-2.5, y=0.0,  z=1.5, yaw=0.0),
    RigPose(x=-2.5, y=-1.5, z=1.5, yaw=0.4),
    RigPose(x=-2.5, y=1.5,  z=1.5, yaw=-0.4),
    RigPose(x=-3.0, y=0.0,  z=2.5, yaw=0.0),
    RigPose(x=-3.5, y=0.0,  z=0.8, yaw=0.0),
    RigPose(x=-1.5, y=2.5,  z=1.5, yaw=-1.0),
    RigPose(x=-1.5, y=-2.5, z=1.5, yaw=1.0),
]

IMAGE_TOPICS: List[Tuple[str, str]] = [
    ('left',        '/stereo/left/image'),
    ('right',       '/stereo/right/image'),
    ('depth',       '/stereo/left/depth'),
    ('seg_colored', '/segmentation/semantic/colored_map'),
    ('seg_labels',  '/segmentation/semantic/labels_map'),
]

CAMERA_INFO_TOPICS: List[Tuple[str, str]] = [
    ('left',  '/stereo/left/camera_info'),
    ('right', '/stereo/right/camera_info'),
]

# Color cameras only — segmentation outputs are saved raw so label IDs
# (which may be encoded in a specific channel) are not perturbed.
RGB_TO_BGR = {'left', 'right', 'seg_colored'}


class DatasetCapture(Node):
    def __init__(self):
        super().__init__('dataset_capture')

        self.declare_parameter('rig_name', 'camera_rig')
        self.declare_parameter('service_name', '/world/empty_lab/set_pose')
        self.declare_parameter('output_dir',
                               '/media/abrar/AbrarSSD/ROS/drone_targeting_research/data/captures')
        self.declare_parameter('run_id', '')
        self.declare_parameter('post_teleport_wait_sec', 0.2)
        self.declare_parameter('frame_timeout_sec', 5.0)

        self.rig_name = self.get_parameter('rig_name').value
        service_name = self.get_parameter('service_name').value
        out_root = Path(self.get_parameter('output_dir').value)
        run_id = self.get_parameter('run_id').value or time.strftime('run_%Y%m%d_%H%M%S')
        self.run_dir = out_root / run_id
        self.post_teleport_wait_sec = float(self.get_parameter('post_teleport_wait_sec').value)
        self.frame_timeout_sec = float(self.get_parameter('frame_timeout_sec').value)

        self.run_dir.mkdir(parents=True, exist_ok=True)

        self.bridge = CvBridge()

        self.latest_images: Dict[str, Optional[Image]] = {n: None for n, _ in IMAGE_TOPICS}
        self.latest_camera_info: Dict[str, Optional[CameraInfo]] = {n: None for n, _ in CAMERA_INFO_TOPICS}

        for name, topic in IMAGE_TOPICS:
            self.create_subscription(Image, topic, self._make_image_cb(name), qos_profile_sensor_data)

        for name, topic in CAMERA_INFO_TOPICS:
            self.create_subscription(CameraInfo, topic, self._make_caminfo_cb(name), 10)

        self.cli = self.create_client(SetEntityPose, service_name)
        self.get_logger().info(f'Waiting for {service_name}...')
        if not self.cli.wait_for_service(timeout_sec=15.0):
            raise RuntimeError(f'Service {service_name} not available')

        self.get_logger().info(f'Run directory: {self.run_dir}')

    def _make_image_cb(self, name):
        def _cb(msg: Image):
            self.latest_images[name] = msg
        return _cb

    def _make_caminfo_cb(self, name):
        def _cb(msg: CameraInfo):
            self.latest_camera_info[name] = msg
        return _cb

    @staticmethod
    def _stamp_sec(msg) -> float:
        return msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9

    def _now_sim_sec(self) -> float:
        return self.get_clock().now().nanoseconds * 1e-9

    def _wait_for_camera_info(self) -> bool:
        deadline_wall = time.monotonic() + self.frame_timeout_sec
        while any(ci is None for ci in self.latest_camera_info.values()):
            rclpy.spin_once(self, timeout_sec=0.05)
            if time.monotonic() > deadline_wall:
                missing = [n for n, ci in self.latest_camera_info.items() if ci is None]
                self.get_logger().error(f'CameraInfo timeout. Missing: {missing}')
                return False
        return True

    def _wait_for_fresh_images(self, after_sim_sec: float) -> bool:
        deadline_wall = time.monotonic() + self.frame_timeout_sec
        while True:
            rclpy.spin_once(self, timeout_sec=0.05)
            if all(m is not None and self._stamp_sec(m) > after_sim_sec
                   for m in self.latest_images.values()):
                return True
            if time.monotonic() > deadline_wall:
                stale = [n for n, m in self.latest_images.items()
                         if m is None or self._stamp_sec(m) <= after_sim_sec]
                self.get_logger().error(f'Frame timeout. Stale: {stale}')
                return False

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
            return False
        result = future.result()
        return result is not None and result.success

    def _save_image(self, msg: Image, path: Path, name: str):
        cv = self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
        if name == 'depth':
            # Float32 depth in metres → 16-bit PNG in millimetres (KITTI/NYU
            # convention). Pixels beyond 65.535 m and invalid (inf/NaN)
            # values clamp to 0, which downstream code treats as "no return".
            d = np.asarray(cv, dtype=np.float32)
            d = np.where(np.isfinite(d) & (d > 0), d * 1000.0, 0.0)
            d = np.clip(d, 0, 65535).astype(np.uint16)
            cv2.imwrite(str(path), d)
            return
        if name in RGB_TO_BGR and cv.ndim == 3 and msg.encoding in ('rgb8', 'rgba8'):
            cv = cv2.cvtColor(cv, cv2.COLOR_RGB2BGR if msg.encoding == 'rgb8' else cv2.COLOR_RGBA2BGRA)
        cv2.imwrite(str(path), cv)

    def save_pose(self, idx: int, pose: RigPose, sim_time: float):
        pose_dir = self.run_dir / f'{idx:05d}'
        pose_dir.mkdir(parents=True, exist_ok=True)

        per_frame = {}
        for name, _topic in IMAGE_TOPICS:
            msg = self.latest_images[name]
            self._save_image(msg, pose_dir / f'{name}.png', name)
            per_frame[name] = {
                'encoding': msg.encoding,
                'height': msg.height,
                'width': msg.width,
                'frame_id': msg.header.frame_id,
                'stamp_sec': self._stamp_sec(msg),
            }

        meta = {
            'pose_index': idx,
            'rig_pose': asdict(pose),
            'sim_time_sec': sim_time,
            'world': 'empty_lab',
            'rig_name': self.rig_name,
            'frames': per_frame,
        }
        (pose_dir / 'metadata.json').write_text(json.dumps(meta, indent=2))

    def save_intrinsics(self):
        out: Dict = {}
        for name, _topic in CAMERA_INFO_TOPICS:
            ci = self.latest_camera_info[name]
            out[name] = {
                'frame_id': ci.header.frame_id,
                'height': ci.height,
                'width': ci.width,
                'distortion_model': ci.distortion_model,
                'D': list(ci.d),
                'K': list(ci.k),
                'R': list(ci.r),
                'P': list(ci.p),
            }
        out['baseline_m'] = 0.10
        (self.run_dir / 'intrinsics.json').write_text(json.dumps(out, indent=2))

    def run(self, poses: List[RigPose]) -> bool:
        if not self._wait_for_camera_info():
            return False
        self.save_intrinsics()
        self.get_logger().info(f'Captured intrinsics. Starting {len(poses)} poses.')

        for idx, pose in enumerate(poses):
            if not self.teleport(pose):
                self.get_logger().error(f'Teleport failed at pose {idx}')
                return False

            time.sleep(self.post_teleport_wait_sec)
            now_sim = self._now_sim_sec()

            if not self._wait_for_fresh_images(now_sim):
                return False

            self.save_pose(idx, pose, now_sim)
            self.get_logger().info(
                f'[{idx+1}/{len(poses)}] x={pose.x:+.2f} y={pose.y:+.2f} z={pose.z:+.2f} yaw={pose.yaw:+.2f}')

        self.get_logger().info(f'Done. {len(poses)} poses written to {self.run_dir}')
        return True


def main():
    rclpy.init()
    node = DatasetCapture()
    try:
        node.run(DEFAULT_POSES)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
