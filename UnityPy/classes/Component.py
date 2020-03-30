from .EditorExtension import EditorExtension
from .PPtr import PPtr


class Component(EditorExtension):
    def __init__(self, reader):
        super().__init__(reader=reader)
        self.GameObject = PPtr(reader)  # GameObject
