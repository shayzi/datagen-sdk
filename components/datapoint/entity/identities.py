import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from datagen import modalities
from datagen.api.assets import HumanDatapoint
from datagen.components.datapoint.entity import base


@dataclass
class DataPoint(base.DataPoint):
    PLUGINS_GROUP_NAME: ClassVar[str] = "datagen.plugins.datapoints.identities"

    @modalities.visual_modality
    def hdri_map(self) -> modalities.VisualModality:
        return modalities.VisualModality("hdri_map.exr")

    @modalities.textual_modality
    def actor_metadata(self) -> modalities.TextualModality:
        return modalities.TextualModality(factory_name="actor_metadata", file_name="actor_metadata.json")

    @modalities.textual_modality
    def face_bounding_box(self) -> modalities.TextualModality:
        return modalities.TextualModality(factory_name="face_bounding_box", file_name="face_bounding_box.json")

    @modalities.textual_modality
    def keypoints(self) -> modalities.TextualModality:
        return modalities.TextualModality(
            factory_name="keypoints",
            file_name=os.path.join("key_points", "all_key_points.json"),
            pre_process=CreateV1AllKeypointsFile(self),
        )

    @modalities.textual_modality
    def _datapoint_request(self) -> modalities.TextualModality:
        """
        :returns: DataRequest containing the HumanDatapoint asset associated with this datapoint.
        """
        return modalities.TextualModality(factory_name="datapoint_request", file_name="datapoint_request.json")

    @property
    def datapoint_request(self) -> HumanDatapoint:
        return self._datapoint_request.datapoints[0]


class CreateV1AllKeypointsFile(modalities.ModalityPreProcess):
    """
    V1 keypoints content comes in two separate files: standard_keypoints.json & dense_keypoints.json
    which have to be consolidated into a single json since the SDK assumes that the content of
    any given modality will always appear in a single json file. We consolidate both files into
    '<DATAPOINT_CAMERA_PATH>/key_points/all_key_points.json', To match v2 keypoints json file location.
    """

    def __init__(self, dp: DataPoint):
        self._dp = dp

    def __call__(self):
        is_v1_keypoints = not self._get_all_keypoints_file().exists()
        if is_v1_keypoints:
            self._create_all_keypoints_file_for_v1()

    def _create_all_keypoints_file_for_v1(self):
        self._get_all_keypoints_file().parent.mkdir()
        self._get_all_keypoints_file().write_text(self._get_keypoints_v1_file_content())

    def _get_keypoints_v1_file_content(self) -> str:
        standard_keypoints = json.loads(self._dp.camera_path.joinpath("standard_keypoints.json").read_text())
        dense_keypoints = json.loads(self._dp.camera_path.joinpath("dense_keypoints.json").read_text())
        keypoints_v1_file_content = json.dumps(
            {"standard": standard_keypoints, "dense": dense_keypoints}, indent=4, sort_keys=True
        )
        return keypoints_v1_file_content

    def _get_all_keypoints_file(self) -> Path:
        return self._dp.camera_path.joinpath("key_points", "all_key_points.json")
