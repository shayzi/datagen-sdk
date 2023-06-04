from dependency_injector import containers, providers

from datagen.dev import PluginsFactory
from datagen.components.datapoint import DatapointsRepository
from datagen.components.datapoint import HICDataPoint, IdentitiesDataPoint
from datagen.modalities.containers import DatapointModalitiesContainer


class DatapointsContainer(containers.DeclarativeContainer):

    __self__ = providers.Self()

    config = providers.Configuration()

    modalities = providers.Container(DatapointModalitiesContainer, config=config)

    factory = providers.Selector(
        config.environment,
        hic=PluginsFactory(HICDataPoint, modalities_container=modalities),
        identities=PluginsFactory(IdentitiesDataPoint, modalities_container=modalities),
    )

    repo = providers.Factory(DatapointsRepository, __self__)
