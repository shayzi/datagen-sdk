from dataclasses import field
from typing import TypeVar, Optional

import marshmallow
import marshmallow_dataclass
from marshmallow import ValidationError
from marshmallow.fields import Field

from datagen.modalities.textual.common.ndarray import NumpyArray

SubSegments = TypeVar("SubSegments")


@marshmallow_dataclass.dataclass
class Keypoints:
    name: str
    coords_2d: NumpyArray = field(repr=False)
    coords_3d: NumpyArray = field(repr=False)
    is_visible: NumpyArray = field(repr=False)


class SubSegmentsField(Field):
    def _deserialize(self, value, *args, **kwargs):
        sub_segments = []
        for name, data in value.items():
            try:
                sub_segments.append(Keypoints.Schema().load({"name": name, **data}))
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

    def __dir__(self):
        return [seg.name for seg in self.sub_segments]


@marshmallow_dataclass.dataclass(base_schema=KeypointsSchema)
class SceneKeypoints:
    scene: SubSegments

    def __getattr__(self, item):
        for sub_seg in self.scene:
            if sub_seg.name == item:
                return sub_seg

    def __dir__(self):
        return [seg.name for seg in self.scene]
