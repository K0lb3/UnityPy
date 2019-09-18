from .NamedObject import NamedObject


class TextAsset(NamedObject):
	def __init__(self, reader):
		super().__init__(reader = reader)
		self.script = reader.read_bytes(reader.read_int())
