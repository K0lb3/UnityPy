from .Component import Component
from .PPtr import PPtr


class MeshFilter(Component):
    def __init__(self, reader):
        super().__init__(reader=reader)
        self.Mesh = PPtr(reader)
