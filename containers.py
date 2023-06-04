from dependency_injector import containers, providers

from datagen.impl import Datagen


class DatagenContainer(containers.DeclarativeContainer):
    datagen = providers.Singleton(Datagen)
