from typing import List

import marshmallow_dataclass
from marshmallow import pre_load

from datagen.modalities.textual.common.ndarray import NumpyArray


@marshmallow_dataclass.dataclass
class Orientation:
    look_at_vector: NumpyArray
    up_vector: NumpyArray


@marshmallow_dataclass.dataclass
class LightSource:
    name: str
    brightness: float
    beam_angle: float
    location: NumpyArray
    orientation: Orientation
    type: str
    falloff: float
    spectrum: str


@marshmallow_dataclass.dataclass
class LightsMetadata:
    lights: List[LightSource]

    @pre_load
    def rearrange_fields(self, in_data: dict, **kwargs) -> dict:
        lights = []
        for light_source_name, light_source_metadata_dict in in_data["lights"].items():
            lights.append({"name": light_source_name, **light_source_metadata_dict})
        return {"lights": lights}
