from dataclasses import dataclass, field
from pathlib import Path

from datagen import modalities
from datagen.modalities.containers import DatapointModalitiesContainer
from datagen.modalities.textual.base.environments import Environment


@dataclass
class DataPoint:
    visible_spectrum_image_name: str
    frame_num: int
    camera: str
    scene_path: Path
    modalities_container: DatapointModalitiesContainer = field(repr=False)

    @property
    def frame_path(self) -> Path:
        return self.scene_path.joinpath("frames", str(self.frame_num).zfill(3))

    @property
    def camera_path(self) -> Path:
        if self.frame_path.exists():
            return self.frame_path.joinpath(self.camera)
        else:
            return self.scene_path.joinpath(self.camera)

    @modalities.visual_modality
    def visible_spectrum(self) -> modalities.VisualModality:
        return modalities.VisualModality(
            self.visible_spectrum_image_name,
            keep_alpha=self.environment.transparent_background,
            convert_to_uint8=True,
        )

    @modalities.visual_modality
    def semantic_segmentation(self) -> modalities.VisualModality:
        return modalities.VisualModality("semantic_segmentation.png")

    @modalities.textual_modality
    def semantic_segmentation_metadata(self) -> modalities.TextualModality:
        return modalities.TextualModality(factory_name="segmentation", file_name="semantic_segmentation_metadata.json")

    @modalities.visual_modality
    def infrared_spectrum(self) -> modalities.VisualModality:
        return modalities.VisualModality("infrared_spectrum.png", convert_to_uint8=True)

    @modalities.visual_modality
    def depth(self) -> modalities.VisualModality:
        return modalities.VisualModality("depth.exr")

    @modalities.visual_modality
    def normal_maps(self) -> modalities.VisualModality:
        return modalities.VisualModality("normal_maps.exr")

    @modalities.textual_modality
    def camera_metadata(self) -> modalities.TextualModality:
        return modalities.TextualModality(factory_name="camera_metadata", file_name="camera_metadata.json")

    @modalities.textual_modality
    def _environments(self) -> modalities.TextualModality:
        return modalities.TextualModality(factory_name="environments", file_name="environment.json")

    @property
    def environment(self) -> Environment:
        return self._environments[self.visible_spectrum_image_name]

    @modalities.textual_modality
    def lights_metadata(self) -> modalities.TextualModality:
        return modalities.TextualModality(factory_name="lights_metadata", file_name="lights_metadata.json")
