from .Behaviour import Behaviour
from .PPtr import PPtr


class Animation(Behaviour):
    def __init__(self, reader):
        super().__init__(reader=reader)
        self.animation = PPtr(reader)
        num_animations = reader.read_int()
        self.animations = [PPtr(reader) for i in range(num_animations)]
