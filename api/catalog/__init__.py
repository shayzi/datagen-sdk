import sys

from datagen.dev import FunctionalModule
from datagen.api.catalog.containers import AssetsCatalogContainer

catalog = AssetsCatalogContainer().catalog()

sys.modules[__name__] = FunctionalModule(functionality=catalog)
