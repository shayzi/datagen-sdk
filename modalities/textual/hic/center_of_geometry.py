from dataclasses import field
from typing import Optional

import marshmallow_dataclass
from marshmallow import fields, pre_load

from datagen.modalities.textual.common.ndarray import NumpyArray


@marshmallow_dataclass.dataclass
class ObjectCenterOfGeometry:
    semantic_name: Optional[str]
    coords_2d: NumpyArray
    coords_3d: NumpyArray

    @pre_load
    def rearrange_fields(self, in_data: dict, **kwargs):
        center_of_mass_props = in_data.pop("center_of_mass")
        semantic_name = in_data["semantic_name"]
        coords_3d = center_of_mass_props["global_3d"]
        coords_2d = center_of_mass_props["pixel_2d"]
        coords_2d.pop("depth")
        return {"semantic_name": semantic_name, "coords_3d": coords_3d, "coords_2d": coords_2d}


class ObjectCenterOfGeometryField(fields.Field):
    def _deserialize(self, value, *args, **kwargs):
        return ObjectCenterOfGeometry.Schema().load(value)


@marshmallow_dataclass.dataclass
class CenterOfGeometry:
    dict_: dict = field(metadata={
        "marshmallow_field": fields.Dict(keys=fields.Str, values=ObjectCenterOfGeometryField)
    })

    @pre_load
    def rearrange_fields(self, in_data: dict, **kwargs):
        return {"dict_": in_data}

