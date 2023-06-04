from dataclasses import dataclass
from typing import TypeVar, Optional, Iterable

import marshmallow
import marshmallow_dataclass
import numpy as np
from marshmallow import pre_load
from marshmallow.fields import Field

SubSegments = TypeVar("SubSegments")


@dataclass
class _Segment:
    name: str


@dataclass
class NestedSegment(_Segment):
    sub_segments: Optional[SubSegments]

    def __getattr__(self, item):
        for sub_seg in self.sub_segments:
            if sub_seg.name == item:
                if isinstance(sub_seg, ColoredSegment):
                    return sub_seg.color
                else:
                    return sub_seg

    def __dir__(self) -> Iterable[str]:
        return [seg.name for seg in self.sub_segments]


@dataclass
class ColoredSegment(_Segment):
    color: Optional[np.ndarray] = None


class SubSegmentsField(Field):
    def _deserialize(self, value, *args, **kwargs):
        sub_segments = []
        for segment_name, segment_data in value.items():
            try:
                sub_segments.append(self._get_colored_segment(segment_name, segment_data))
            except KeyError:
                sub_segments.append(NestedSegment(segment_name, self._deserialize(segment_data, *args, **kwargs)))
        return sub_segments

    @staticmethod
    def _get_colored_segment(segment_name: str, segment_data: dict) -> ColoredSegment:
        if isinstance(segment_data, list):
            return ColoredSegment(segment_name, np.array(segment_data))
        else:
            return ColoredSegment(segment_name, np.array([segment_data["R"], segment_data["G"], segment_data["B"]]))


class SegmentSchema(marshmallow.Schema):
    TYPE_MAPPING = {SubSegments: SubSegmentsField}


@marshmallow_dataclass.dataclass(base_schema=SegmentSchema)
class Segmentation:
    scene: SubSegments

    @pre_load
    def rearrange_fields(self, in_data: dict, **kwargs) -> dict:
        return {"scene": in_data}

    def __getattr__(self, item):
        for sub_seg in self.scene:
            if sub_seg.name == item:
                if isinstance(sub_seg, ColoredSegment):
                    return sub_seg.color
                else:
                    return sub_seg

    def __dir__(self) -> Iterable[str]:
        return [seg.name for seg in self.scene]