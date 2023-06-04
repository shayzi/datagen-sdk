import marshmallow_dataclass

from datagen.modalities.textual.common.ndarray import NumpyArray


@marshmallow_dataclass.dataclass
class SixDOF:
    location: NumpyArray
    look_at_vector: NumpyArray
