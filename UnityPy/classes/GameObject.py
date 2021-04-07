from .EditorExtension import EditorExtension
from .PPtr import PPtr


class GameObject(EditorExtension):
    def __init__(self, reader):
        super().__init__(reader=reader)
        component_size = reader.read_int()
        self.m_Components = [None]*component_size
        for i in range(component_size):
            if self.version < (5, 5):
                first = reader.read_int()
            self.m_Components[i] = PPtr(reader)
        self.m_Layer = reader.read_int()
        self.name = reader.read_aligned_string()
