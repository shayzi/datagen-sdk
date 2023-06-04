import sys

from datagen.api import catalog  # noqa: F401
from datagen.api.containers import ApiContainer
from datagen.api.impl import DatagenAPI
from datagen.dev import FunctionalModule

try:
    from datagen.utilities import camera as camera_utils  # noqa: F401
except ModuleNotFoundError:
    # Did not install the camera-utils optional dependency
    pass

api = ApiContainer.api()

sys.modules[__name__] = FunctionalModule(functionality=api)
