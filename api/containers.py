from dependency_injector import containers, providers

from datagen.api.impl import DatagenAPI
from datagen.dev.logging import get_logger

logger = get_logger(__name__)


class ApiContainer(containers.DeclarativeContainer):

    api = providers.Singleton(DatagenAPI)
