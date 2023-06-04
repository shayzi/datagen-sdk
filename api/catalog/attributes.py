from datagen_protocol.schema.attributes import *  # noqa: F401 F403


class AllOf(list):
    def __init__(self, *attributes):
        super().__init__(attributes)


class AnyOf(list):
    def __init__(self, *attributes):
        super().__init__(attributes)
