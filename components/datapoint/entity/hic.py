import os
from typing import ClassVar

from datagen import modalities
from datagen.components.datapoint.entity import base


class DataPoint(base.DataPoint):
    PLUGINS_GROUP_NAME: ClassVar[str] = "datagen.plugins.datapoints.hic"

    @modalities.textual_modality
    def actor_metadata(self) -> modalities.TextualModality:
        return modalities.TextualModality(factory_name="actors", file_name="actor_metadata.json")

    @modalities.textual_modality
    def keypoints(self) -> modalities.TextualModality:
        return modalities.TextualModality(
            factory_name="keypoints", file_name=os.path.join("key_points", "all_key_points.json")
        )

    @modalities.textual_modality
    def _center_of_geometry(self) -> modalities.TextualModality:
        return modalities.TextualModality(factory_name="center_of_geometry", file_name="center_of_geometry.json")

    @property
    def center_of_geometry(self) -> dict:
        return self._center_of_geometry.dict_
