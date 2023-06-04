from pathlib import Path
from dependency_injector import containers, providers

from datagen.imaging.opencv import OpenCVImagingLibrary
from datagen.modalities import textual as textual_modalities


class VisualModalitiesContainer(containers.DeclarativeContainer):

    config = providers.Configuration()

    imaging_library = providers.Selector(config, opencv=providers.Singleton(OpenCVImagingLibrary))


def read_visual_modality(
    modalities_container: containers.DeclarativeContainer,
    modality_file_path: str,
    keep_alpha: bool,
    convert_to_uint8: bool,
):
    return (
        modalities_container.visual()
        .imaging_library()
        .read(image_file_path=modality_file_path, keep_alpha=keep_alpha, convert_to_uint8=convert_to_uint8)
    )


def read_textual_modality(
    modalities_container: containers.DeclarativeContainer, modality_file_path: str, modality_factory_name: str
):
    return modalities_container.textual().providers[modality_factory_name](modality_file_path=modality_file_path)


class DatapointModalitiesContainer(containers.DeclarativeContainer):

    __self__ = providers.Self()

    config = providers.Configuration()

    visual = providers.Container(VisualModalitiesContainer, config=config.imaging_library)

    textual = providers.Selector(
        config.environment,
        hic=providers.Container(textual_modalities.HICModalitiesContainer),
        identities=providers.Container(textual_modalities.IdentitiesModalitiesContainer),
    )

    read_visual_modality = providers.Callable(read_visual_modality, modalities_container=__self__)

    read_textual_modality = providers.Callable(read_textual_modality, modalities_container=__self__)

    wiring_config = containers.WiringConfiguration(packages=[textual_modalities])
