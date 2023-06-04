from dataclasses import dataclass, field

from datagen.api.assets import HumanDatapoint
from datagen.api.requests.datapoint.builder import HumanDatapointBuilder


@dataclass
class DataRequestDirector:
    builder: HumanDatapointBuilder = field(init=False)

    def build_datapoint(self) -> HumanDatapoint:
        datapoint = self.builder.get_basic_datapoint()
        datapoint.accessories = self.builder.get_accessories()
        datapoint.background = self.builder.get_background()
        datapoint.lights = self.builder.get_lights()
        return datapoint.copy(deep=True)
