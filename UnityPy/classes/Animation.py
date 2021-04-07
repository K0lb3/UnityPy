from .Behaviour import Behaviour
from .PPtr import PPtr


class Animation(Behaviour):
    def __init__(self, reader):
        super().__init__(reader=reader)
        self.m_Animation = PPtr(reader)
        num_animations = reader.read_int()
        self.m_Animations = [PPtr(reader) for _ in range(num_animations)]
