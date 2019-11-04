from .Behaviour import Behaviour
from .PPtr import PPtr


class MonoBehaviour(Behaviour):
	def __init__(self, reader):
		super().__init__(reader=reader)
		self.script = PPtr(reader)
		self.name = reader.read_aligned_string()
