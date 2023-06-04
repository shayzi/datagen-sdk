import marshmallow_dataclass
from marshmallow import pre_load

from datagen.modalities.textual.identities.keypoints import base


@marshmallow_dataclass.dataclass(base_schema=base.KeypointsSchema)
class SceneKeypoints(base.SceneKeypoints):
    @pre_load
    def convert_to_v2_structure(self, in_data: dict, **kwargs) -> dict:
        in_data["standard"]["coords_2d"] = in_data["standard"].pop("keypoints_2d_coordinates")
        in_data["standard"]["coords_3d"] = in_data["standard"].pop("keypoints_3d_coordinates")
        in_data["dense"]["coords_2d"] = in_data["dense"].pop("keypoints_2d_coordinates")
        in_data["dense"]["coords_3d"] = in_data["dense"].pop("keypoints_3d_coordinates")
        return {"scene": {"face": in_data}}

