import marshmallow_dataclass
from marshmallow import pre_load

from datagen.modalities.textual.identities.keypoints import base


@marshmallow_dataclass.dataclass(base_schema=base.KeypointsSchema)
class SceneKeypoints(base.SceneKeypoints):
    @pre_load
    def rearrange_fields(self, in_data: dict, **kwargs) -> dict:
        return {"scene": _rearange_nested_segments(in_data)}


def _rearange_nested_segments(in_data: dict) -> dict:
    converted_dict = {}
    for name, data in in_data.items():
        if isinstance(data, dict):
            if _is_single_coord_keypoint_segment(data):
                converted_dict[name] = _convert_to_single_coord(data)
            elif _is_keypoints_matrix_segment(data):
                converted_dict[name] = _convert_to_matrix(data)
            else:
                converted_dict[name] = _rearange_nested_segments(data)
        else:
            converted_dict[name] = data
    return converted_dict


def _is_single_coord_keypoint_segment(in_data: dict) -> bool:
    return all(key in in_data for key in ["pixel_2d", "global_3d", "is_visible"])


def _convert_to_single_coord(data):
    return {
        "coords_2d": data["pixel_2d"],
        "coords_3d": data["global_3d"],
        "is_visible": data["is_visible"] == "true",
    }


def _is_keypoints_matrix_segment(in_data: dict) -> bool:
    return all(s.isnumeric() for s in in_data.keys())


def _convert_to_matrix(kp_num_to_kp_coords: dict) -> dict:
    coords_2d_matrix, coords_3d_matrix, is_visible_arr = [], [], []
    kp_num_to_kp_coords = _convert_str_keys_to_int(kp_num_to_kp_coords)
    for _, kp_coords in sorted(kp_num_to_kp_coords.items()):
        coords_2d, coords_3d, is_visible_str = kp_coords["pixel_2d"], kp_coords["global_3d"], kp_coords["is_visible"]
        coords_2d_matrix.append([coords_2d["x"], coords_2d["y"]])
        coords_3d_matrix.append([coords_3d["x"], coords_3d["y"], coords_3d["z"]])
        is_visible_arr.append(is_visible_str == "true")
    return {"coords_2d": coords_2d_matrix, "coords_3d": coords_3d_matrix, "is_visible": is_visible_arr}


def _convert_str_keys_to_int(kp_num_to_kp_coords: dict) -> dict:
    return {int(kp_num): kp_coords for kp_num, kp_coords in kp_num_to_kp_coords.items()}
