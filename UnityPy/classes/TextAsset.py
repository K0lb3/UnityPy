from .NamedObject import NamedObject


class TextAsset(NamedObject):
	def __init__(self, reader):
		super().__init__(reader=reader)
		self.script = reader.read_bytes(reader.read_int())

	@property
	def text(self):
		return self.script if isinstance(self.script, str) else self.script.decode('utf8')
