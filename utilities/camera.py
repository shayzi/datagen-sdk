import math
import sys
from dataclasses import dataclass
from typing import Union, ClassVar, NamedTuple, TypeVar, Generator, List

import numpy as np

from datagen import config
from datagen.dev import FunctionalModule
from datagen.api import assets
from datagen.utilities.arrays import to_arrays
from datagen.utilities.extrinsics import Extrinsics

Resolution = NamedTuple('Resolution', x=int, y=int)

Sensor = NamedTuple("Sensor", width=float, height=float)


@dataclass
class Focus:
    focal_length: float
    fov: float

    @classmethod
    def from_focal_length(cls, focal_length: float, sensor_width: float) -> "Focus":
        fov = 2 * np.arctan2(0.5 * sensor_width, focal_length)
        return cls(fov=fov, focal_length=focal_length)

    @classmethod
    def from_fov(cls, fov: float, sensor_width: float) -> "Focus":
        focal_length = sensor_width / (np.tan(fov / 2) * 2)
        return cls(fov=fov, focal_length=focal_length)


@dataclass
class Intrinsics:
    resolution: Resolution
    sensor: Sensor
    focus: Focus
    pxl_aspect_ratio: float

    @property
    def matrix(self):
        pixels_per_mm_h = self.resolution.x / self.sensor.height
        pixels_per_mm_w = self.resolution.y / self.sensor.width
        f_x, f_y = self.focus.focal_length * pixels_per_mm_h, self.focus.focal_length * pixels_per_mm_w
        return np.array(
            [
                [f_x, 0, self.resolution.x / 2],
                [0.0, f_y * self.pxl_aspect_ratio, self.resolution.y / 2],
                [0.0, 0.0, 1.0],
            ]
        )


P = TypeVar("P", bound=Union[assets.Point, "np.ndarray"])
CP = TypeVar("CP", bound=Union[assets.Camera, assets.Point, "np.ndarray"])


class CameraUtils:
    """
    Camera Asset Utilities
    """

    PLUGINS_GROUP_NAME: ClassVar[str] = "datagen.plugins.utils.camera"

    def calculate_rotation(self, camera: CP, look_at_point: P) -> assets.Rotation:
        """Calculates rotation needed in order to rotate the camera towards a given look-at-point.

        Args:
            camera (Union[assets.Camera, assets.Point, np.ndarray]): The camera to calculate the rotation for.
            look_at_point (Union[assets.Point, np.ndarray]): The look-at-point the camera should be rotated towards.

        Returns:
            assets.Rotation: The yaw-pitch-roll value needed in order to rotate a camera
            towards the given look-at-point.

        Examples:
            >>> camera_utils.calculate_rotation(
            >>>     camera=np.ndarray([-0.056, -1.985, -0.367]), look_at_point=np.ndarray([0., 0., 0.1]))
            >>> )
            np.ndarray([ 1.641, 13.246,  0.])

            >>> camera_utils.calculate_rotation(
            >>>     camera=assets.Point(x=-0.056, y=-1.985, z=-0.367), look_at_point=assets.Point(x=0., y=0., z=0.1))
            >>> )
            np.ndarray([ 1.641, 13.246,  0.])

            >>> camera = assets.Camera()
            >>> camera.extrinsics.location = assets.Point(x=-0.056, y=-1.985, z=-0.367)
            >>> camera_utils.calculate_rotation(camera, look_at_point=assets.Point(x=0., y=0., z=0.1)))
            Point(x=1.641, y=13.246,  z=0.)
        """
        camera_location = self._get_camera_location(camera)
        camera_location, look_at_point = to_arrays(camera_location, look_at_point)
        extrinsics = Extrinsics.from_look_at(camera_location, look_at_point)
        ypr = extrinsics.rotation.to_ypr()
        return assets.Rotation.from_ypr(ypr)

    def rotate(self, camera: assets.Camera, look_at_point: P) -> None:
        """Rotates the camera towards the given look-at-point.

        Args:
            camera (assets.Camera): The camera to rotate.
            look_at_point (Union[assets.Point, np.ndarray]): The look-at-point the camera should be rotated towards.

        Examples:
            >>> camera = assets.Camera()
            >>> camera.extrinsics.location = assets.Point(x=-0.056, y=-1.985, z=-0.367)
            >>> camera_utils.rotate(camera, look_at_point=assets.Point(x=0., y=0., z=0.1)))
            >>> camera.extrinsics.location
            Point(x=1.641, y=13.246,  z=0.)
        """
        camera.extrinsic_params.rotation = self.calculate_rotation(camera, look_at_point=look_at_point)

    def _get_camera_location(self, camera: Union[assets.Camera, P]) -> P:
        return camera if isinstance(camera, (assets.Point, np.ndarray)) else camera.extrinsic_params.location

    def get_extrinsic_matrix(self, camera: assets.Camera) -> "np.ndarray":
        """Calculates the extrinsic matrix of the camera.

        Args:
            camera (assets.Camera): The camera to get extrinsic matrix for.

        Returns:
            np.ndarray: The extrinsic matrix of the camera
        """
        extrinsics = self._get_extrinsics_from_camera_asset(camera)
        return extrinsics.matrix

    def get_rotation_matrix(self, camera: assets.Camera) -> "np.ndarray":
        """Calculates the rotation matrix of the camera.

        Args:
            camera (assets.Camera): The camera to get rotation matrix for.

        Returns:
            np.ndarray: The rotation matrix of the camera
        """
        extrinsics = self._get_extrinsics_from_camera_asset(camera)
        return extrinsics.rotation.matrix

    def _get_extrinsics_from_camera_asset(self, camera: assets.Camera) -> Extrinsics:
        camera_location, yaw_pitch_roll = to_arrays(camera.extrinsic_params.location, camera.extrinsic_params.rotation)
        extrinsics = Extrinsics.from_yaw_pitch_roll(camera_location, yaw_pitch_roll)
        return extrinsics

    def create_cameras_ring(
        self,
        cameras_num: int,
        cameras_intrinsics: assets.CameraIntrinsicParams,
        cameras_look_at_point: assets.Point,
        radius: float,
        z_value: float,
    ) -> List[assets.Camera]:
        cameras = []
        for camera_idx, camera_location in enumerate(
            self._get_ring_cameras_locations(cameras_num, cameras_look_at_point, radius, z_value)
        ):
            camera = self.init_camera(
                camera_idx=camera_idx, camera_intrinsics=cameras_intrinsics, camera_location=camera_location
            )
            self.rotate(camera, look_at_point=cameras_look_at_point)
            cameras.append(camera)
        return cameras

    def _get_ring_cameras_locations(
        self, cameras_num: int, ring_center: assets.Point, r: float, z: float
    ) -> Generator[assets.Point, None, None]:
        for i, xy_angle in enumerate(np.linspace(0, 360, num=cameras_num, endpoint=False)):
            xy_rad = (xy_angle * math.pi) / 180
            yield assets.Point(
                x=(math.sin(xy_rad) + ring_center.x) * (-1.0 * r),
                y=(math.cos(xy_rad) + ring_center.y) * (-1.0 * r),
                z=z + 0.12,
            )

    def init_camera(
        self,
        camera_idx: int = None,
        camera_intrinsics: assets.CameraIntrinsicParams = None,
        camera_extrinsics: assets.CameraExtrinsicParams = None,
        camera_location: assets.Point = None,
    ) -> assets.Camera:
        camera = assets.Camera()
        camera.name = f"Camera_{str(camera_idx).zfill(2)}" if camera_idx else config.assets.camera.name
        if camera_intrinsics:
            camera.intrinsics = camera_intrinsics
        if camera_extrinsics:
            camera.extrinsic_params = camera_extrinsics
        if camera_location:
            camera.extrinsic_params.location = camera_location
        return camera


sys.modules[__name__] = FunctionalModule(functionality=CameraUtils())
