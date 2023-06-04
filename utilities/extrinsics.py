import numpy as np
from scipy.spatial.transform import Rotation as RotationScipy

from datagen.utilities.arrays import normalize

DEFAULT_WORLD_UP_VECTOR = np.array([0, 0, 1])

DEFAULT_CAMERA_ROTATION = np.array([[-1, 0, 0], [0, 0, -1], [0, -1, 0]])


class Rotation:
    def __init__(self, rotation_matrix: np.ndarray):
        self._matrix = rotation_matrix

    @property
    def matrix(self) -> np.ndarray:
        return self._matrix

    @classmethod
    def from_ypr(cls, yaw: float, pitch: float, roll: float):
        matrix = RotationScipy.from_euler("yxz", (-yaw, pitch, -roll)).as_matrix()
        return cls(matrix @ DEFAULT_CAMERA_ROTATION)

    def to_ypr(self) -> np.array:
        yaw, pitch, roll = RotationScipy.from_matrix(self._matrix @ DEFAULT_CAMERA_ROTATION.T).as_euler(
            "yxz", degrees=True
        )
        return np.array([-yaw, pitch, roll])


class Extrinsics:
    """
    This class is intentionally generic, in case we'd like
    to use it on assets other than camera (light etc.).
    """

    def __init__(self, location: np.ndarray, rotation: Rotation):
        self._location = location
        self._rotation = rotation

    @property
    def location(self) -> np.ndarray:
        return self._location

    @property
    def rotation(self) -> Rotation:
        return self._rotation

    @property
    def matrix(self) -> np.ndarray:
        rotated_location = -(self._rotation.matrix @ self._location)
        extrinsic_matrix = np.hstack([self._rotation.matrix, rotated_location[..., np.newaxis]])
        return extrinsic_matrix

    @classmethod
    def from_look_at(
        cls,
        camera_location: np.ndarray,
        look_at_point: np.ndarray,
        world_up_vector: np.ndarray = DEFAULT_WORLD_UP_VECTOR,
    ) -> "Extrinsics":
        look_at_vector = normalize(camera_location - look_at_point)
        right_camera = normalize(np.cross(world_up_vector, look_at_vector))
        up_camera = normalize(np.cross(look_at_vector, right_camera))
        rotation = np.reshape(np.concatenate([right_camera, up_camera, look_at_vector]).T, (3, 3))
        if np.linalg.det(rotation) == -1:
            rotation = -rotation
        return Extrinsics(location=camera_location, rotation=Rotation(rotation))

    @classmethod
    def from_yaw_pitch_roll(cls, camera_location: np.ndarray, ypr: np.ndarray) -> "Extrinsics":
        return Extrinsics(location=camera_location, rotation=Rotation.from_ypr(*ypr))
