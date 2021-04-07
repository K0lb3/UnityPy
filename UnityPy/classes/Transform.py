from .Component import Component
from .PPtr import PPtr


class Transform(Component):
    def __init__(self, reader):
        super().__init__(reader=reader)
        self.m_LocalRotation = reader.read_quaternion()
        self.m_LocalPosition = reader.read_vector3()
        self.m_LocalScale = reader.read_vector3()

        children_count = reader.read_int()
        self.m_Children = [PPtr(reader) for _ in range(children_count)]
        self.m_Father = PPtr(reader)
