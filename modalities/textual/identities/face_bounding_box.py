import marshmallow_dataclass


@marshmallow_dataclass.dataclass
class FaceBoundingBox:
    min_x: int
    min_y: int
    max_x: int
    max_y: int
