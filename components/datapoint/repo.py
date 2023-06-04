from dataclasses import dataclass
from pathlib import Path
from typing import List, Iterable

from dependency_injector import containers
from dependency_injector.wiring import inject

from datagen.components.datapoint import DataPoint

IDENTITIES_SCENE_FRAMES_RANGE = range(1)


@inject
@dataclass
class DatapointsRepository:
    datapoints_container: containers.DeclarativeContainer

    def get_datapoints(self, scene_path: Path, camera_name: str) -> List[DataPoint]:
        datapoints = []
        for frame_num in self._get_frames_range(scene_path):
            for environment in self._get_datapoints_environments(scene_path, camera_name, frame_num):
                datapoints.append(
                    self.datapoints_container.factory(
                        scene_path=scene_path,
                        camera=camera_name,
                        frame_num=frame_num,
                        visible_spectrum_image_name=environment.image_name,
                    )
                )
        return datapoints

    def _get_frames_range(self, scene_path: Path) -> range:
        if self._is_hic_scene(scene_path):
            return self._get_hic_scene_frames_range(scene_path)
        else:
            return IDENTITIES_SCENE_FRAMES_RANGE

    @staticmethod
    def _get_hic_scene_frames_range(scene_path: Path) -> range:
        frames_dirs = list(filter(lambda item: item.name.isnumeric(), scene_path.joinpath("frames").iterdir()))
        frames_num = len(frames_dirs)
        return range(1, frames_num + 1)

    def _get_datapoints_environments(
        self, scene_path: Path, camera_name: str, frame_num: int
    ) -> Iterable["Environment"]:
        return self.datapoints_container.modalities().read_textual_modality(
            modality_factory_name="environments",
            modality_file_path=self._get_environments_modality_file_path(scene_path, camera_name, frame_num),
        )

    def _get_environments_modality_file_path(self, scene_path: Path, camera_name: str, frame_num: int) -> str:
        if self._is_hic_scene(scene_path):
            base_path = scene_path.joinpath("frames", str(frame_num).zfill(3))
        else:
            base_path = scene_path
        return str(base_path.joinpath(camera_name, "environment.json"))

    @staticmethod
    def _is_hic_scene(scene_path: Path) -> bool:
        frames_path = scene_path.joinpath("frames")
        return frames_path.exists() and frames_path.is_dir()
