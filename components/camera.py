from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from dependency_injector.wiring import inject, Provide

from datagen.components.datapoint import DataPoint
from datagen.components.datapoint import DatapointsRepository
from datagen.components.sequence import Sequence


@dataclass
class Camera:
    name: str
    scene_path: Path
    datapoints: List[DataPoint] = field(init=False, repr=False)

    def __post_init__(self):
        self.datapoints = self._init_datapoints()

    @inject
    def _init_datapoints(self, repo: DatapointsRepository = Provide["repo"]) -> List[DataPoint]:
        return repo.get_datapoints(scene_path=self.scene_path, camera_name=self.name)

    def get_sequence(self, **env_attributes) -> Sequence:
        """"
        :returns a sequence of datapoints ordered by frames, in context of a single environment (Time of Day etc.)
        """
        return Sequence(
            scene_path=self.scene_path,
            camera_name=self.name,
            datapoints=tuple(dp for dp in self.datapoints if dp.environment.matches(**env_attributes)),
        )

    def __iter__(self):
        for datapoint in self.datapoints:
            yield datapoint

    def __getitem__(self, key):
        return self.datapoints[key]

    def __len__(self):
        return len(self.datapoints)
