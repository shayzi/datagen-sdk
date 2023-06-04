from dependency_injector import containers, providers

from datagen.modalities.textual.base.containers import (
    BaseModalitiesContainer,
    modality_dataclass_factory,
    modality_factory,
)


class ActorsModalityContainer(containers.DeclarativeContainer):

    from .actor_metadata import Actors

    create = providers.FactoryAggregate({1: modality_dataclass_factory(clazz=Actors)})


class KeypointsModalityContainer(containers.DeclarativeContainer):

    from .keypoints import Keypoints

    create = providers.FactoryAggregate(
        {1: modality_dataclass_factory(clazz=Keypoints), 2: modality_dataclass_factory(clazz=Keypoints)}
    )


class CenterOfGeometryModalityContainer(containers.DeclarativeContainer):

    from .center_of_geometry import CenterOfGeometry

    create = providers.FactoryAggregate({1: modality_dataclass_factory(clazz=CenterOfGeometry)})


class HICModalitiesContainer(BaseModalitiesContainer):

    actors = providers.Callable(modality_factory, modality_container=providers.Container(ActorsModalityContainer))

    keypoints = providers.Callable(modality_factory, modality_container=providers.Container(KeypointsModalityContainer))

    center_of_geometry = providers.Callable(
        modality_factory, modality_container=providers.Container(CenterOfGeometryModalityContainer)
    )
