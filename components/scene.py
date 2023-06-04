from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from datagen.components.camera import Camera
from datagen.components.datapoint import DataPoint


@dataclass
class Scene:
    path: Path
    cameras: List[Camera] = field(init=False, repr=False)

    def __post_init__(self):
        self.cameras = self._init_cameras()

    def _init_cameras(self) -> List[Camera]:
        return [Camera(name=camera_name, scene_path=self.path) for camera_name in sorted(self._get_cameras_names())]

    def _get_cameras_names(self) -> List[str]:
        if Scene.is_path_to_hic_scene(self.path):
            # for HIC, we have to select a random frame to get the cameras names of from.
            cameras_base_path = self.path.joinpath("frames", "001")
        else:
            cameras_base_path = self.path
        cameras_dirs = filter(lambda path_: path_.is_dir(), cameras_base_path.iterdir())
        return [cam_dir.name for cam_dir in cameras_dirs]

    @staticmethod
    def is_path_to_hic_scene(scene_path: Path) -> bool:
        hic_frames_dir = scene_path.joinpath("frames")
        return hic_frames_dir.exists() and hic_frames_dir.is_dir()

    @property
    def datapoints(self) -> List[DataPoint]:
        return [datapoint for datapoint in self]

    def __getitem__(self, key):
        return self.datapoints[key]

    def __iter__(self):
        for camera in self.cameras:
            for datapoint in camera:
                yield datapoint

    def __len__(self):
        return len(self.datapoints)
