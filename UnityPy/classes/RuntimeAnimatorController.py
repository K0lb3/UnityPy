from .NamedObject import NamedObject


class RuntimeAnimatorController(NamedObject):
    def __init__(self, reader):
        super().__init__(reader=reader)
