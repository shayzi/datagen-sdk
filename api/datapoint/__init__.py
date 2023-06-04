import sys

from datagen.api import ApiContainer
from datagen.dev import FunctionalModule

print("❗❗❗'datagen.api.datapoint' module is deprecated, please use 'datagen.api' instead.")

api = ApiContainer.api()

sys.modules[__name__] = FunctionalModule(functionality=api)
