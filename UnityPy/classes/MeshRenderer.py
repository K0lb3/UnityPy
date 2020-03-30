from .Renderer import Renderer


class MeshRenderer(Renderer):
    def __init__(self, reader):
        super().__init__(reader=reader)
