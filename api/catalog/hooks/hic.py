from typing import Dict, List

from datagen.api.assets import DataSequence
from datagen.api.catalog.impl import InitParametersHook


class HICPresetsHook(InitParametersHook[DataSequence]):
    def __init__(self, asset_id_to_asset_presets: dict):
        self._asset_id_to_asset_presets = asset_id_to_asset_presets

    def __call__(self, asset_id: str) -> dict:
        return dict(presets=self._asset_id_to_asset_presets[asset_id])

