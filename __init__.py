import sys

from .containers import DatagenContainer
from .components.dataset import DatasetConfig
from datagen.dev import __version__, FunctionalModule

datagen = DatagenContainer().datagen()

sys.modules[__name__] = FunctionalModule(datagen)
