from typing import Optional

import marshmallow_dataclass
from marshmallow import pre_load

from datagen.modalities.textual.common.ndarray import NumpyArray


@marshmallow_dataclass.dataclass
class Orientation:
    look_at_vector: NumpyArray
    up_vector: NumpyArray


@marshmallow_dataclass.dataclass
class FOV:
    horizontal: float
    vertical: float


@marshmallow_dataclass.dataclass
class Sensor:
    width: float
    height: float

    @pre_load
    def rearrange_fields(self, in_data: dict, **kwargs):
        in_data["width"] = in_data.pop("sensor_width")
        in_data["height"] = in_data.pop("sensor_height")
        return in_data


@marshmallow_dataclass.dataclass
class CameraMetadata:
    camera_name: str
    camera_type: str
    focal_length: Optional[float]
    sensor: Sensor
    resolution_px: NumpyArray
    aspect_px: NumpyArray
    location: NumpyArray
    orientation: Orientation
    fov: FOV
    intrinsic_matrix: NumpyArray
    extrinsic_matrix: NumpyArray
