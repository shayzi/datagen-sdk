from dataclasses import dataclass
from typing import List, Optional, Union

from datagen.api.assets import Accessories, Background, Camera, Glasses, Human, HumanDatapoint, Light, Mask


@dataclass
class HumanDatapointBuilder:
    human: Human
    camera: Camera
    glasses: Optional[Glasses]
    mask: Optional[Mask]
    background: Optional[Background]
    lights: Optional[List[Light]]

    def get_basic_datapoint(self) -> HumanDatapoint:
        return HumanDatapoint(human=self.human.copy(deep=True), camera=self.camera.copy(deep=True))

    def get_accessories(self) -> Union[Accessories, None]:
        if self.glasses is None and self.mask is None:
            return None
        else:
            accessories = Accessories()
            if self.glasses is not None:
                accessories.glasses = self.glasses.copy(deep=True)
            if self.mask is not None:
                accessories.mask = self.mask.copy(deep=True)
            return accessories

    def get_background(self) -> Union[Background, None]:
        if self.background is not None:
            return self.background.copy(deep=True)
        else:
            return None

    def get_lights(self) -> Union[List[Light], None]:
        if self.lights is not None and len(self.lights) > 0:
            return [light.copy(deep=True) for light in self.lights]
        else:
            return None
