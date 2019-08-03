from ..enums.BuildTarget import BuildTarget
from ..helpers import TypeTreeHelper


def field(f, cast = None, **kwargs):
	def _inner(self):
		try:
			if "default" in kwargs:
				ret = self.type_tree.get(f, kwargs["default"])
			else:
				ret = self.type_tree[f]
			if cast:
				ret = cast(ret)
			return ret
		except:
			return None
	
	return property(_inner)


class Object:
	def __init__(self, reader):
		# reader : ObjectReader
		self.reader = reader
		reader.reset()
		self.name = reader.read_aligned_string()
		reader.reset()
		self.assets_file = reader.assets_file
		self.type = reader.type
		self.path_id = reader.path_id
		self.version = reader.version
		self.build_type = reader.build_type
		self.platform = reader.platform
		self.serialized_type = reader.serialized_type
		self.byte_size = reader.byte_size
		
		if self.platform == BuildTarget.NoTarget:
			self._object_hide_flags = reader.read_u_int()
		self.read()
	
	def has_struct_member(self, name: str) -> bool:
		return self.serialized_type.m_Nodes and any([x.name == name for x in self.serialized_type.m_Nodes])
	
	# def dump(self) -> str:
	# 	self.reader.reset()
	# 	if getattr(self.serialized_type, 'nodes', None):
	# 		sb = []
	# 		TypeTreeHelper.read_type_string(sb, self.serialized_type.m_Nodes, self.reader)
	# 		return ''.join(sb)
	# 	return ''
	
	def read(self) -> dict:
		self.reader.reset()
		if self.serialized_type.nodes:
			self.type_tree = TypeTreeHelper(self.reader).read_value(self.serialized_type.nodes, 0)
		else:
			self.type_tree = {}
		return self.type_tree
	
	def get_raw_data(self) -> bytes:
		self.reader.reset()
		return self.reader.read_bytes(self.byte_size)
	
	def __repr__(self):
		return "<%s %s>" % (
				self.__class__.__name__, self.name
		)


class GameObject(Object):
	active = field("m_IsActive")
	component = field("m_Component")
	layer = field("m_Layer")
	tag = field("m_Tag")
