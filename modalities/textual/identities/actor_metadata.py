from dataclasses import field
from typing import ClassVar, List

import marshmallow
import marshmallow_dataclass
from marshmallow.decorators import pre_load
from marshmallow.fields import Field
from marshmallow_dataclass import NewType

from datagen.modalities.textual.common.identity_label import IdentityLabel
from datagen.modalities.textual.common.ndarray import NumpyArray
from datagen.modalities.textual.common.sixdof import SixDOF

EYES_FULLY_OPENED = 5


@marshmallow_dataclass.dataclass
class FaceExpression:
    name: str
    intensity_level: int


@marshmallow_dataclass.dataclass
class RollPitchYaw:
    roll: float
    pitch: float
    yaw: float


@marshmallow_dataclass.dataclass
class HeadMetadata:
    head_root_location: NumpyArray
    head_rotation: RollPitchYaw
    head_six_dof: SixDOF


@marshmallow_dataclass.dataclass
class RollPitchYaw:
    roll: float
    pitch: float
    yaw: float


@marshmallow_dataclass.dataclass
class HeadMetadata:
    head_root_location: NumpyArray
    head_rotation: RollPitchYaw
    head_six_dof: SixDOF


@marshmallow_dataclass.dataclass
class Coord2DPerEye:
    camera_name: str
    right_eye: NumpyArray
    left_eye: NumpyArray


@marshmallow_dataclass.dataclass
class Coords3DPerEye:
    right_eye: NumpyArray
    left_eye: NumpyArray


class SinglePointPerEyeSchema(marshmallow.Schema):
    @pre_load
    def rearrange_fields(self, in_data: dict, **kwargs):
        in_data["coords_2d"] = self._adjust_to_2d_coords_schema(in_data.pop("2d"))
        in_data["coords_3d"] = in_data.pop("3d")
        return in_data

    @staticmethod
    def _adjust_to_2d_coords_schema(eyes_2d_data: dict) -> list:
        coord_2d_data = []
        for camera_name, camera_eyes_2d_data in eyes_2d_data.items():
            coord_2d_data.append({"camera_name": camera_name, **camera_eyes_2d_data})
        return coord_2d_data


@marshmallow_dataclass.dataclass(base_schema=SinglePointPerEyeSchema)
class SinglePointPerEye:
    coords_2d: List[Coord2DPerEye]
    coords_3d: Coords3DPerEye


@marshmallow_dataclass.dataclass
class Multi2DPointsPerEye:
    camera_name: str
    right_eye: NumpyArray
    left_eye: NumpyArray

    @pre_load
    def rearrange_fields(self, in_data: dict, **kwargs):
        in_data["right_eye"] = [[entry["x"], entry["y"]] for entry in in_data["right_eye"]]
        in_data["left_eye"] = [[entry["x"], entry["y"]] for entry in in_data["left_eye"]]
        return in_data


@marshmallow_dataclass.dataclass
class Multi3DPointsPerEye:
    right_eye: NumpyArray
    left_eye: NumpyArray

    @pre_load
    def rearrange_fields(self, in_data: dict, **kwargs):
        in_data["right_eye"] = [[entry["x"], entry["y"], entry["z"]] for entry in in_data["right_eye"]]
        in_data["left_eye"] = [[entry["x"], entry["y"], entry["z"]] for entry in in_data["left_eye"]]
        return in_data


class MultiPointsPerEyeSchema(marshmallow.Schema):
    @pre_load
    def rearrange_fields(self, in_data: dict, **kwargs):
        in_data["coords_2d"] = self._adjust_to_2d_coord_schema(in_data.pop("2d"))
        in_data["coords_3d"] = in_data.pop("3d")
        return in_data

    @staticmethod
    def _adjust_to_2d_coord_schema(eyes_2d_data: dict) -> list:
        coords_2d_data = []
        for camera_name, camera_eyes_2d_data in eyes_2d_data.items():
            coords_2d_data.append({"camera_name": camera_name, **camera_eyes_2d_data})
        return coords_2d_data


@marshmallow_dataclass.dataclass(base_schema=MultiPointsPerEyeSchema)
class MultiPointsPerEye:
    coords_2d: List[Multi2DPointsPerEye]
    coords_3d: Multi3DPointsPerEye


@marshmallow_dataclass.dataclass
class AxisDirection:
    optical_axis_direction: NumpyArray
    visual_axis_direction: NumpyArray

    @pre_load
    def rearrange_fields(self, in_data: dict, **kwargs):
        return in_data.pop("axis_directions")


@marshmallow_dataclass.dataclass
class AxisDirections:
    right_eye: AxisDirection
    left_eye: AxisDirection


@marshmallow_dataclass.dataclass
class EyeGaze:
    axis_directions: AxisDirections
    target_point: Coords3DPerEye
    eye_gaze_direction_type: str


@marshmallow_dataclass.dataclass
class Accessory:
    type: ClassVar[str]


@marshmallow_dataclass.dataclass
class Glasses(Accessory):
    type: ClassVar[str] = "glasses"
    style: str
    lens_color: str
    reflectivity: float
    transparency: float
    location: str = "on_nose"

    @pre_load
    def rearrange_fields(self, in_data: dict, **kwargs):
        if "metallic_intensity" in in_data:
            in_data["reflectivity"] = in_data.pop("metallic_intensity")
        if "transparency_intensity" in in_data:
            in_data["transparency"] = in_data.pop("transparency_intensity")
        return in_data

    @property
    def metallic_intensity(self) -> float:
        return self.reflectivity

    @property
    def transparency_intensity(self) -> float:
        return self.transparency


@marshmallow_dataclass.dataclass
class Mask(Accessory):
    type: ClassVar[str] = "mask"
    style: str
    mask_color: str
    mask_texture: str
    roughness: float
    location: str = "on_nose"


class AccessoryField(Field):
    ACCESSORY_TYPE_TO_CLASS = {"glasses": Glasses, "mask": Mask}

    def _deserialize(self, accessory_dict: dict, attr, data, **kwargs) -> Accessory:
        accessory_type = accessory_dict.pop("type")
        return self.ACCESSORY_TYPE_TO_CLASS[accessory_type.lower()].Schema().load(accessory_dict)


AccessoryType = NewType("Accessory", Accessory, field=AccessoryField)


@marshmallow_dataclass.dataclass
class ActorMetadata:
    identity_id: str
    identity_label: IdentityLabel
    facial_hair_included: bool
    face_expression: FaceExpression
    head_metadata: HeadMetadata
    center_of_rotation_point: SinglePointPerEye
    apex_of_cornea_point: SinglePointPerEye
    center_of_iris_point: SinglePointPerEye
    center_of_pupil_point: SinglePointPerEye
    iris_circle: MultiPointsPerEye
    pupil_circle: MultiPointsPerEye
    eye_gaze: EyeGaze
    eyelid_closure_intensity_level: int = field(default=EYES_FULLY_OPENED)
    accessories: List[AccessoryType] = field(default_factory=list)
