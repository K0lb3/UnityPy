from .Object import Object
from .PPtr import PPtr
from ..enums import BuildTarget


class EditorExtension(Object):
	def __init__(self, reader):
		super().__init__(reader=reader)
		if self.platform == BuildTarget.NoTarget:
			self.prefab_parent_object = PPtr(reader)
			self.prefab_internal = PPtr(reader)
