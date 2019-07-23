from .enums.BuildTarget import BuildTarget
from .helpers import TypeTreeHelper


class Object():
	# assetsFile : SerializedFile
	# reader : ObjectReader
	# m_PathID : int
	# version : list
	# buildType #BuildType
	# platform #BuildTarget
	# type #ClassIDType
	# serializedType #SerializedType
	# byteSize : int
	
	def __init__(self, reader):
		# reader : ObjectReader
		self.reader = reader
		reader.Reset()
		self.m_Name = reader.ReadAlignedString()
		reader.Reset()
		self.assetsFile = reader.assetsFile
		self.type = reader.type
		self.m_PathID = reader.m_PathID
		self.version = reader.version
		self.buildType = reader.buildType
		self.platform = reader.platform
		self.serializedType = reader.serializedType
		self.byteSize = reader.byteSize
		
		if self.platform == BuildTarget.NoTarget:
			self.m_ObjectHideFlags = reader.ReadUInt32()
		self.Read()
	
	def HasStructMember(self, name: str) -> bool:
		return self.serializedType.m_Nodes and any([x.name == name for x in self.serializedType.m_Nodes])
	
	def Dump(self) -> str:
		self.reader.Reset()
		if getattr(self.serializedType, 'm_Nodes', None):
			sb = []
			TypeTreeHelper.ReadTypeString(sb, self.serializedType.m_Nodes, self.reader)
			return ''.join(sb)
		return ''
	
	def Read(self) -> dict:
		self.reader.Reset()
		self.typeTree = TypeTreeHelper.ReadValue(self.serializedType.m_Nodes, self.reader, 0)
		return self.typeTree
	
	def GetRawData(self) -> bytes:
		self.reader.Reset()
		return self.reader.ReadBytes(self.byteSize)
