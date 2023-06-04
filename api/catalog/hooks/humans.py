from datagen.api import assets
from datagen.api.assets import Human
from datagen.api.catalog.impl import InitParametersHook


class HumansDefaultsHook(InitParametersHook[Human]):
    def __init__(self, asset_id_to_asset_defaults: dict):
        self._asset_id_to_asset_defaults = asset_id_to_asset_defaults

    def __call__(self, asset_id: str) -> dict:
        from datagen.api import catalog

        defaults = self._asset_id_to_asset_defaults[asset_id]
        default_eyes = catalog.eyes.parse(**defaults["eyes"])
        default_hair = catalog.hair.parse(**defaults["hair"])
        default_eyebrows = catalog.eyebrows.parse(**defaults["eyebrows"])
        return {"head": assets.Head(eyes=default_eyes, eyebrows=default_eyebrows, hair=default_hair)}
