import dataclasses
from collections import namedtuple
from typing import List, TypeVar

import marshmallow
import marshmallow_dataclass
from marshmallow import pre_load
from marshmallow.fields import Field

SINGLE_ENV_DEFAULT_IMG_NAME = "visible_spectrum.png"


class Environment:
    def __init__(self, **attrs):
        for attr_name, attr_val in attrs.items():
            setattr(self, attr_name, attr_val)

    def matches(self, **env_attributes) -> bool:
        is_match = True
        for attr_name, attr_value in env_attributes.items():
            is_match &= self.__dict__[attr_name] == attr_value
        return is_match

    @property
    def transparent_background(self) -> bool:
        return getattr(self, "background", None) == "transparent"


EnvironmentType = TypeVar("EnvironmentType")


class EnvironmentField(Field):
    def _deserialize(self, anv_attrs, *args, **kwargs):
        environment = Environment(**anv_attrs)
        return environment


class EnvironmentsSchema(marshmallow.Schema):
    TYPE_MAPPING = {EnvironmentType: EnvironmentField}

    @pre_load
    def rearrange_fields(self, in_data: dict, **kwargs):
        if "environments" not in in_data:
            in_data["image_name"] = SINGLE_ENV_DEFAULT_IMG_NAME
            in_data = {"environments": [in_data]}
        return in_data


@marshmallow_dataclass.dataclass(base_schema=EnvironmentsSchema)
class Environments:
    environments: List[EnvironmentType]

    def __iter__(self):
        for environment in self.environments:
            yield environment

    def __getitem__(self, image_name: str):
        return next(env for env in self if env.image_name == image_name)
