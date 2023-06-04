from dataclasses import field, dataclass
from typing import List, Iterator, Optional

from datagen import components
from datagen.components.datapoint import DataPoint
from datagen.components.datapoint import DatapointsContainer
from datagen.components import Scene
from datagen.components import DataSource
from datagen.components import SourcesRepository


@dataclass
class DatasetConfig:
    imaging_library: str = "opencv"
    environment: Optional[str] = None

    @property
    def override_environment(self) -> bool:
        return self.environment is not None


@dataclass
class Dataset:
    sources_repo: SourcesRepository = field(repr=False)
    config: DatasetConfig
    scenes: List[Scene] = field(default_factory=list, repr=False)

    def __post_init__(self):
        self._init_sources()

    def _init_sources(self) -> None:
        for source in self.sources_repo.get_all():
            self._init(source)

    def _init(self, source: DataSource) -> None:
        self._init_datapoints_container(source)
        self.scenes.extend(source.init_scenes())

    def _init_datapoints_container(self, source: DataSource) -> None:
        datapoints_container = DatapointsContainer(
            config={
                "environment": self.config.environment if self.config.override_environment else source.environment,
                "imaging_library": self.config.imaging_library
            }
        )
        datapoints_container.wire(packages=[components])

    def __iter__(self) -> Iterator[DataPoint]:
        for scene in self.scenes:
            for datapoint in scene:
                yield datapoint

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._get_single_datapoint(key)
        elif isinstance(key, slice):
            return self._get_multiple_datapoints(key)

    def _get_single_datapoint(self, idx: int) -> DataPoint:
        idx = idx % len(self)
        if not 0 <= idx < len(self):
            raise IndexError("Datapoint index exceeded dataset's size")
        [datapoint] = self._get_datapoints(start=idx, stop=idx + 1)
        return datapoint

    def _get_multiple_datapoints(self, key: slice) -> List[DataPoint]:
        start = key.start if key.start is not None else 0
        stop = key.stop % len(self) if key.stop is not None else len(self) - 1
        if not 0 <= start < stop < len(self):
            raise IndexError("Datapoints indexes exceeded dataset's size")
        return self._get_datapoints(start, stop)

    def _get_datapoints(self, start: int, stop: int) -> List[DataPoint]:
        datapoints = []
        for idx, datapoint in enumerate(self):
            if start <= idx < stop:
                datapoints.append(datapoint)
        return datapoints

    def __len__(self):
        return sum(len(scene) for scene in self.scenes)
