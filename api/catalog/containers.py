from functools import partial

from dependency_injector import containers, providers

from datagen.api import assets
from datagen.api.catalog.hooks import HICPresetsHook, HumansDefaultsHook
from datagen.api.catalog.impl import AssetCatalog, DatagenAssetsCatalog
from datagen.dev import load_resource

load_cache_resource = partial(load_resource, "cache")


class AssetsCatalogContainer(containers.DeclarativeContainer):

    humans = providers.Singleton(
        AssetCatalog,
        asset_type=assets.Human,
        asset_id_to_asset_attrs=load_cache_resource("humans", "attributes.json"),
        hooks=providers.List(
            providers.Singleton(
                HumansDefaultsHook, asset_id_to_asset_defaults=load_cache_resource("humans", "defaults.json")
            )
        ),
    )

    sequences = providers.Singleton(
        AssetCatalog,
        asset_type=assets.DataSequence,
        asset_id_to_asset_attrs=load_cache_resource("hic", "attributes.json"),
        hooks=providers.List(
            providers.Singleton(HICPresetsHook, asset_id_to_asset_presets=load_cache_resource("hic", "presets.json"))
        ),
    )
    eyes = providers.Singleton(
        AssetCatalog,
        asset_type=assets.Eyes,
        asset_id_to_asset_attrs=load_cache_resource("eyes.json"),
    )

    hair = providers.Singleton(
        AssetCatalog,
        asset_type=assets.Hair,
        asset_id_to_asset_attrs=load_cache_resource("hair.json"),
    )

    eyebrows = providers.Singleton(
        AssetCatalog,
        asset_type=assets.Eyebrows,
        asset_id_to_asset_attrs=load_cache_resource("eyebrows.json"),
    )

    facial_hair = providers.Singleton(
        AssetCatalog,
        asset_type=assets.FacialHair,
        asset_id_to_asset_attrs=load_cache_resource("beards.json"),
    )

    glasses = providers.Singleton(
        AssetCatalog,
        asset_type=assets.Glasses,
        asset_id_to_asset_attrs=load_cache_resource("glasses.json"),
    )

    masks = providers.Singleton(
        AssetCatalog,
        asset_type=assets.Mask,
        asset_id_to_asset_attrs=load_cache_resource("masks.json"),
    )

    backgrounds = providers.Singleton(
        AssetCatalog,
        asset_type=assets.Background,
        asset_id_to_asset_attrs=load_cache_resource("backgrounds.json"),
    )

    catalog = providers.Singleton(
        DatagenAssetsCatalog,
        humans=humans,
        sequences=sequences,
        hair=hair,
        eyes=eyes,
        eyebrows=eyebrows,
        facial_hair=facial_hair,
        glasses=glasses,
        masks=masks,
        backgrounds=backgrounds,
    )
