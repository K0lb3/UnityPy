from .EndianBinaryReader import EndianBinaryReader
from .files.SerializedFile import SerializedType
from . import classes


class ObjectInfo():
	byteStart: int
	byteSize: int
	typeID: int
	classID: int
	
	m_PathID: int
	serializedType: SerializedType


class ObjectReader(EndianBinaryReader):
	# assetsFile : SerializedFile
	# m_PathID : long
	# byteStart : uint
	# byteSize : uint
	# type : ClassIDType
	# serializedType : SerializedType
	# platform : BuildTarget
	# m_Version : uint
	
	# version => assetsFile.version : int[]
	# buildType => assetsFile.buildType : BuildType
	
	def __init__(self, reader, assetsFile, objectInfo):
		self.assetsFile = assetsFile
		self.m_PathID = objectInfo.m_PathID
		self.byteStart = objectInfo.byteStart
		self.byteSize = objectInfo.byteSize
		self.serializedType = objectInfo.serializedType
		self.platform = assetsFile.m_TargetPlatform
		self.m_Version = assetsFile.header.m_Version
		self.type = getattr(classes, str(objectInfo.classID), classes.Object)
		
		self.version = assetsFile.version
		self.buildType = assetsFile.buildType
		
		# self.reader = reader
		self.endian = reader.endian
		self.stream = reader.stream  # [self.byteStart:self.byteStart+self.byteSize]
		self.Length = reader.Length
	
	def Reset(self):
		self.Position = self.byteStart
	
	def Read(self):
		return self.type(self)
