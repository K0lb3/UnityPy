from .EditorExtension import EditorExtension


class NamedObject(EditorExtension):
	def __init__(self, reader):
		super().__init__(reader=reader)
		self.reader.reset()
		self.name = self.reader.read_aligned_string()
