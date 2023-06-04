import abc
from enum import Enum
from typing import Dict, Generic, List, Type, TypeVar, Union

import numpy as np
import pandas as pd
from datagen_protocol.schema.humans.human import Eyebrows, FacialHair

from datagen.api.catalog.exceptions import InvalidAssetIdError, InvalidAttributeError

try:
    from collections import Sequence
except ImportError:
    from collections.abc import Sequence  # >=Python 3.10


from datagen.api.assets import Background, DataSequence, Eyes, Glasses, Hair, Human, Mask
from datagen.api.catalog.attributes import AllOf, AnyOf
from datagen.dev.logging import get_logger

logger = get_logger(__name__)

Asset = TypeVar("Asset")


class AssetProvisioningHook(abc.ABC, Generic[Asset]):
    @abc.abstractmethod
    def __call__(self, *args) -> None:
        ...


class InitParametersHook(AssetProvisioningHook, abc.ABC, Generic[Asset]):
    @abc.abstractmethod
    def __call__(self, asset_id: str) -> dict:
        ...


class PostLoadHook(AssetProvisioningHook, abc.ABC, Generic[Asset]):
    @abc.abstractmethod
    def __call__(self, asset: Asset) -> None:
        ...


class AssetCreationHooks(Generic[Asset]):
    def __init__(self, hooks: List[AssetProvisioningHook]):
        self._hooks = hooks

    @property
    def _init_hooks(self) -> List[InitParametersHook]:
        return list(filter(lambda h: isinstance(h, InitParametersHook), self._hooks))  # type: ignore

    def get_init_params(self, asset_id: str) -> dict:
        init_params = {}
        for h in self._init_hooks:
            init_params.update(**h(asset_id))
        return init_params

    @property
    def _post_load_hooks(self) -> List[PostLoadHook]:
        return list(filter(lambda h: isinstance(h, PostLoadHook), self._hooks))  # type: ignore

    def post_load(self, asset: Asset) -> None:
        for h in self._post_load_hooks:
            h(asset)


class AssetInstancesProvisioner(Generic[Asset]):
    def __init__(
        self,
        asset_type: Type[Asset],
        asset_id_to_asset_attrs: dict,
        hooks: List[AssetProvisioningHook[Asset]],
    ):
        self._asset_type = asset_type
        self._asset_id_to_asset_attrs = asset_id_to_asset_attrs
        self._hooks = AssetCreationHooks(hooks)

    def provision(self, asset_id: str) -> Asset:
        return self._asset_type(
            id=asset_id,
            **self._hooks.get_init_params(asset_id),
            attributes=self._asset_id_to_asset_attrs[asset_id],
        )

    def parse(self, asset_id: str, asset_body_dict: dict) -> Asset:
        return self._asset_type(
            id=asset_id,
            **asset_body_dict,
            attributes=self._asset_id_to_asset_attrs[asset_id],
        )

    def post_load(self, asset: Asset) -> Asset:
        self._hooks.post_load(asset)
        return asset


class CatalogInstancesCache(Generic[Asset]):
    def __init__(self, provisioner: AssetInstancesProvisioner):
        self._provisioner = provisioner
        self._cache = {}

    def get(self, asset_id: str) -> Asset:
        asset = self._load(asset_id)
        asset = self._provisioner.post_load(asset)
        return asset

    def _load(self, asset_id) -> Asset:
        try:
            asset = self._cache[asset_id].copy(deep=True)
        except KeyError:
            asset = self._cache.setdefault(asset_id, self._provisioner.provision(asset_id))
        return asset


class AssetInstancesList(Sequence):
    def __init__(self, instances_cache: CatalogInstancesCache, assets_ids: List[str]):
        self._instances_cache = instances_cache
        self._assets_ids = assets_ids

    def __repr__(self):
        return f"<{self.__class__.__name__}({len(self)})>"

    def __iter__(self):
        return AssetInstancesIter(self)

    def __len__(self):
        return len(self._assets_ids)

    def __getitem__(self, index):
        return self._instances_cache.get(asset_id=self._assets_ids[index])

    def __contains__(self, element):
        return element in self._assets_ids


class AssetInstancesIter:
    def __init__(self, instances_list: AssetInstancesList):
        self._idx = 0
        self._instances_list = instances_list

    def __iter__(self):
        return self

    def __next__(self):
        if self._idx >= len(self._instances_list):
            raise StopIteration
        self._idx += 1
        return self._instances_list[self._idx - 1]


class AttributesDataFrame:
    def __init__(self, attributes_df: pd.DataFrame):
        self._df = attributes_df

    def query(self, attributes: Dict[str, Union[Enum, AllOf, AnyOf]], limit: int = None) -> List[str]:
        if attributes:
            df = self._df.loc[self._create_query_series(attributes)]
        else:
            df = self._df
        return list(df.index)[:limit]

    def _create_query_series(self, attributes: Dict[str, Union[Enum, AllOf, AnyOf]]) -> np.ndarray:
        attrs_series_list = [
            self._create_attr_series(attr_name, attr_query_val) for attr_name, attr_query_val in attributes.items()
        ]
        return np.logical_and.reduce(attrs_series_list)

    def _create_attr_series(
        self, attr_name: str, attr_query_val: Union[str, Enum, AllOf, AnyOf]
    ) -> Union[pd.Series, np.ndarray]:
        if isinstance(attr_query_val, (str, Enum)):
            return self._create_series(attr_name, attr_query_val)
        elif isinstance(attr_query_val, (AllOf, AnyOf)):
            series_list = [self._create_series(attr_name, attr_val) for attr_val in attr_query_val]
            operator = np.logical_and if isinstance(attr_query_val, AllOf) else np.logical_or
            return operator.reduce(series_list)

    def _create_series(self, attr_name: str, attr_val: Union[str, Enum]) -> pd.Series:
        if isinstance(attr_val, Enum):
            attr_val = attr_val.value
        return self._df[f"{attr_val}_{attr_name}"].__eq__(True)

    @classmethod
    def from_dict(cls, asset_id_to_asset_attrs: dict) -> "AttributesDataFrame":
        attrs_dataframe_dict = {
            asset_id: AttributesDataFrame._get_dataframe_row(asset_attrs_dict)
            for asset_id, asset_attrs_dict in asset_id_to_asset_attrs.items()
        }
        attr_dataframe = pd.DataFrame.from_dict(attrs_dataframe_dict, orient="index")
        return cls(attributes_df=attr_dataframe)

    @staticmethod
    def _get_dataframe_row(asset_attrs_dict: dict) -> dict:
        dataframe_row = {}
        for attr_name, attr_value in asset_attrs_dict.items():
            if not isinstance(attr_value, list):
                attr_value = [attr_value]
            for v in attr_value:
                if isinstance(v, str):
                    dataframe_row[v + "_" + attr_name] = True
        return dataframe_row


class AssetCatalog(Generic[Asset]):
    def __init__(
        self, asset_type: Type[Asset], asset_id_to_asset_attrs: dict, hooks: List[AssetProvisioningHook[Asset]] = None
    ):
        if hooks is None:
            hooks = []
        self._provisioner = AssetInstancesProvisioner(asset_type, asset_id_to_asset_attrs, hooks)
        self._instances_cache = CatalogInstancesCache(self._provisioner)
        self._attributes_df = AttributesDataFrame.from_dict(asset_id_to_asset_attrs)

    def get(self, id: str = None, limit: int = None, **attributes) -> Union[Asset, AssetInstancesList]:
        if id:
            return self._query_by_id(asset_id=id)
        else:
            return self._query_by_attributes(limit=limit, **attributes)

    def count(self, **attributes) -> int:
        return len(self._attributes_df.query(attributes))

    def parse(self, id: str, **asset_body) -> Asset:
        return self._provisioner.parse(asset_id=id, asset_body_dict=asset_body)

    def _query_by_id(self, asset_id: str) -> Asset:
        try:
            return self._instances_cache.get(asset_id)
        except KeyError as e:
            error_msg = f"Asset with ID {asset_id} not found in local cache."
            logger.error(error_msg)
            raise InvalidAssetIdError(error_msg) from e

    def _query_by_attributes(self, limit: int = None, **attributes) -> Union[Asset, AssetInstancesList]:
        try:
            matching_assets_ids = self._attributes_df.query(attributes, limit)
            if limit == 1:
                return self._instances_cache.get(matching_assets_ids[0])
            else:
                return AssetInstancesList(instances_cache=self._instances_cache, assets_ids=matching_assets_ids)
        except KeyError as e:
            error_msg = f"Received invalid asset attribute {e.args[0]}"
            logger.error(error_msg)
            raise InvalidAttributeError(error_msg) from e


class DatagenAssetsCatalog:
    def __init__(
        self,
        humans: AssetCatalog[Human],
        sequences: AssetCatalog[DataSequence],
        hair: AssetCatalog[Hair],
        eyes: AssetCatalog[Eyes],
        eyebrows: AssetCatalog[Eyebrows],
        facial_hair: AssetCatalog[FacialHair],
        glasses: AssetCatalog[Glasses],
        masks: AssetCatalog[Mask],
        backgrounds: AssetCatalog[Background],
    ):
        self.humans = humans
        self.sequences = sequences
        self.hair = hair
        self.eyes = eyes
        self.eyebrows = eyebrows
        self.beards = facial_hair
        self.glasses = glasses
        self.masks = masks
        self.backgrounds = backgrounds
