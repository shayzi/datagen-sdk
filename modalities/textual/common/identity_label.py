import marshmallow_dataclass


@marshmallow_dataclass.dataclass
class IdentityLabel:
    age: str
    ethnicity: str
    gender: str
