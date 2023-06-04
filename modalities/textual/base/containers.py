import json
from functools import lru_cache, partial

from dependency_injector import containers, providers
from packaging import version

INITIAL_MODALITIES_VERSION = "1.0.0"


@lru_cache(maxsize=None)
def modality_factory(modality_container: providers.Container, modality_file_path: str):
    """
    Important - Please note this function caches its return values!
    """
    modality_dict, modality_version = _parse_modality_file(modality_file_path)
    return modality_container.create(modality_version, modality_dict=modality_dict)


def _parse_modality_file(modality_file_path: str) -> tuple:
    with open(modality_file_path) as f:
        modality_params = json.load(f)
        modality_version = _get_modality_version(modality_params)
    return modality_params, modality_version


def _get_modality_version(modality_params: dict) -> int:
    modality_version = modality_params.pop("version", INITIAL_MODALITIES_VERSION)
    modality_version_ = version.parse(modality_version).major
    return modality_version_


def load_dataclass(clazz: type, modality_dict: dict):
    return clazz.Schema().load(modality_dict)


modality_dataclass_factory = partial(providers.Factory, load_dataclass)


def load_pydantic_obj(clazz: type, modality_dict: dict):
    return clazz.parse_obj(modality_dict)


modality_pydantic_factory = partial(providers.Factory, load_pydantic_obj)


class CameraMetadataModalityContainer(containers.DeclarativeContainer):

    from .camera_metadata import CameraMetadata

    create = providers.FactoryAggregate({1: modality_dataclass_factory(clazz=CameraMetadata)})


class SegmentationModalityContainer(containers.DeclarativeContainer):

    from .segmentation import Segmentation

    create = providers.FactoryAggregate({1: modality_dataclass_factory(clazz=Segmentation)})


class EnvironmentsModalityContainer(containers.DeclarativeContainer):

    from .environments import Environments

    create = providers.FactoryAggregate({1: modality_dataclass_factory(clazz=Environments)})


class LightsMetadataModalityContainer(containers.DeclarativeContainer):

    from datagen.modalities.textual.base.lights_metadata import LightsMetadata

    create = providers.FactoryAggregate({1: modality_dataclass_factory(clazz=LightsMetadata)})


class BaseModalitiesContainer(containers.DeclarativeContainer):
    environments = providers.Callable(
        modality_factory, modality_container=providers.Container(EnvironmentsModalityContainer)
    )

    camera_metadata = providers.Callable(
        modality_factory, modality_container=providers.Container(CameraMetadataModalityContainer)
    )

    segmentation = providers.Callable(
        modality_factory, modality_container=providers.Container(SegmentationModalityContainer)
    )

    lights_metadata = providers.Callable(
        modality_factory, modality_container=providers.Container(LightsMetadataModalityContainer)
    )
