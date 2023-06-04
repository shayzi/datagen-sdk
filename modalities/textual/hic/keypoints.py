from dataclasses import field
from typing import TypeVar, Optional, Generator, Iterable

import marshmallow
import marshmallow_dataclass
from marshmallow import pre_load, ValidationError
from marshmallow.fields import Field

from datagen.modalities.textual.common.ndarray import NumpyArray

SubSegments = TypeVar("SubSegments")


@marshmallow_dataclass.dataclass
class Keypoint:
    name: str
    coords_2d: NumpyArray = field(repr=False)
    coords_3d: NumpyArray = field(repr=False)

    @pre_load
    def rearrange_fields(self, in_data: dict, **kwargs) -> dict:
        if all(key in in_data.keys() for key in ["global_3d", "pixel_2d"]):
            in_data["coords_3d"] = in_data.pop("global_3d")
            in_data["coords_2d"] = in_data.pop("pixel_2d")
        return in_data


class SubSegmentsField(Field):
    def _deserialize(self, value, *args, **kwargs):
        sub_segments = []
        for name, data in value.items():
            try:
                sub_segments.append(Keypoint.Schema().load({"name": name, **data}))
            except ValidationError:
                sub_segments.append(NestedSegment(name, self._deserialize(data, *args, **kwargs)))
        return sub_segments


class KeypointsSchema(marshmallow.Schema):
    TYPE_MAPPING = {SubSegments: SubSegmentsField}


@marshmallow_dataclass.dataclass(base_schema=KeypointsSchema)
class NestedSegment:
    name: str
    sub_segments: Optional[SubSegments]

    def __getattr__(self, item):
        for sub_seg in self.sub_segments:
            if sub_seg.name == item:
                return sub_seg

    def __dir__(self) -> Iterable[str]:
        return [seg.name for seg in self.sub_segments]


@marshmallow_dataclass.dataclass(base_schema=KeypointsSchema)
class Keypoints:
    scene: SubSegments

    @pre_load
    def rearrange_fields(self, in_data: dict, **kwargs) -> dict:
        return {"scene": _convert_multi_keypoints_segments_to_matrices(in_data)}

    def __getattr__(self, item):
        for sub_seg in self.scene:
            if sub_seg.name == item:
                return sub_seg

    def __dir__(self) -> Iterable[str]:
        return [seg.name for seg in self.scene]


def _convert_multi_keypoints_segments_to_matrices(in_data: dict) -> dict:
    converted_dict = {}
    for name, data in in_data.items():
        if isinstance(data, dict):
            if _is_multi_keypoints_segment(data):
                converted_dict[name] = _convert_to_matrices(data)
            else:
                converted_dict[name] = _convert_multi_keypoints_segments_to_matrices(data)
        else:
            converted_dict[name] = data
    return converted_dict


def _is_multi_keypoints_segment(in_data: dict) -> bool:
    return all(s.isnumeric() for s in in_data.keys())


def _convert_to_matrices(kp_num_to_coords: dict) -> dict:
    coords_2d_matrix, coords_3d_matrix = [], []
    for kp_coords in _get_coords_sorted_by_kp_num(kp_num_to_coords):
        coords_2d, coords_3d = kp_coords["pixel_2d"], kp_coords["global_3d"]
        coords_2d_matrix.append([coords_2d["x"], coords_2d["y"]])
        coords_3d_matrix.append([coords_3d["x"], coords_3d["y"], coords_3d["z"]])
    return {"coords_2d": coords_2d_matrix, "coords_3d": coords_3d_matrix}


def _get_coords_sorted_by_kp_num(kp_num_to_coords_nd) -> Generator:
    for keypoint_num in sorted(int(s) for s in kp_num_to_coords_nd.keys()):
        yield kp_num_to_coords_nd[str(keypoint_num)]
