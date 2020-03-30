from .Component import Component
from .PPtr import PPtr


class Transform(Component):
    def __init__(self, reader):
        super().__init__(reader=reader)
        self.local_rotation = reader.read_quaternion()
        self.local_position = reader.read_vector3()
        self.local_scale = reader.read_vector3()

        children_count = reader.read_int()
        self.children = [PPtr(reader) for _ in range(children_count)]
        self.father = PPtr(reader)
