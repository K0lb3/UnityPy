from .Component import Component


class Behaviour(Component):
    def __init__(self, reader):
        super().__init__(reader=reader)
        self.enabled = reader.read_byte()
        self._dummy = reader.align_stream()
