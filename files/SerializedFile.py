import os
import re
from enums.BuildTarget import BuildTarget
from EndianBinaryReader import EndianBinaryReader
from CommonString import CommonString
from enums.ClassIDType import ClassIDType


class SerializedFileHeader():
	m_MetadataSize: int
	m_FileSize: int
	m_Version: int
	m_DataOffset: int
	m_Endianess: bytes
	m_Reserved: bytes


class LocalSerializedObjectIdentifier():
	localSerializedFileIndex: int
	localIdentifierInFile: int


class FileIdentifier():
	guid: str
	type: int
	# enum { kNonAssetType = 0, kDeprecatedCachedAssetType = 1, kSerializedAssetType = 2, kMetaAssetType = 3 };
	pathName: str
	# custom
	fileName: str


class TypeTreeNode():
	m_Type: str
	m_Name: str
	m_ByteSize: int
	m_Index: int
	m_IsArray: int
	m_Version: int
	m_MetaFlag: int
	m_Level: int
	m_TypeStrOffset: int
	m_NameStrOffset: int


class BuildType():
	def __init__(self, type: str = ""):
		self.buildType = type
	
	def IsAlpha(self):
		return self.buildType == "a"
	
	def IsPatch(self):
		return self.buildType == "p"


class SerializedType():
	classID: ClassIDType
	m_IsStrippedType: bool
	m_ScriptTypeIndex = -1
	m_Nodes: list  # TypeTreeNode
	m_ScriptID: bytes  # Hash128
	m_OldTypeHash: bytes  # Hash128}


class ObjectInfo():
	byteStart: int
	byteSize: int
	typeID: int
	classID: ClassIDType
	m_PathID: int
	serializedType: SerializedType


class SerializedFile():
	version = [0, 0, 0, 0]
	Objects = {}
	unityVersion = "2.5.0f5"
	m_TargetPlatform = BuildTarget.UnknownPlatform
	m_EnableTypeTree = True
	m_Types = []
	m_Objects = []
	m_ScriptTypes = []
	m_Externals = []
	
	def __init__(self, assetsManager, fullName: str, reader):
		self.assetsManager = assetsManager
		self.reader = reader
		self.fullName = fullName
		self.fileName = os.path.basename(fullName)
		self.upperFileName = self.fileName.upper()
		
		# ReadHeader
		header = SerializedFileHeader()
		self.header = header
		header.m_MetadataSize = reader.ReadUInt32()
		header.m_FileSize = reader.ReadUInt32()
		header.m_Version = reader.ReadUInt32()
		header.m_DataOffset = reader.ReadUInt32()
		
		if header.m_Version >= 9:
			header.m_Endianess = reader.ReadBoolean()
			header.m_Reserved = reader.ReadBytes(3)
			m_FileEndianess = '>' if header.m_Endianess else '<'
		else:
			reader.Position = header.m_FileSize - header.m_MetadataSize
			header.m_Endianess = reader.ReadBoolen()
			m_FileEndianess = '>' if header.m_Endianess else '<'
		
		# ReadMetadata
		if m_FileEndianess == '<':
			reader.endian = '<'
		
		if header.m_Version >= 7:
			unityVersion = reader.ReadStringToNull()
			self.SetVersion(unityVersion)
		
		if header.m_Version >= 8:
			m_TargetPlatform = reader.ReadInt32()
			try:
				m_TargetPlatform = BuildTarget(m_TargetPlatform)
			except KeyError:
				m_TargetPlatform = BuildTarget.UnknownPlatform
		
		if header.m_Version >= 13:
			self.m_EnableTypeTree = reader.ReadBoolean()
		
		# ReadTypes
		typeCount = reader.ReadInt32()
		self.m_Types = [
				self.ReadSerializedType()
				for i in range(typeCount)
		]
		
		if header.m_Version >= 7 and header.m_Version < 14:
			bigIDEnabled = reader.ReadInt32()
		
		# ReadObjects
		objectCount = reader.ReadInt32()
		self.m_Objects = []
		for i in range(objectCount):
			objectInfo = ObjectInfo()
			if header.m_Version < 14:
				objectInfo.m_PathID = reader.ReadInt32()
			else:
				reader.AlignStream()
				objectInfo.m_PathID = reader.ReadInt64()
			
			objectInfo.byteStart = reader.ReadUInt32()
			objectInfo.byteStart += header.m_DataOffset
			objectInfo.byteSize = reader.ReadUInt32()
			objectInfo.typeID = reader.ReadInt32()
			if header.m_Version < 16:
				objectInfo.classID = ClassIDType(reader.ReadUInt16())
				# m_Types.Find(x => x.classID == objectInfo.typeID)
				objectInfo.serializedType = [
						x for x in self.m_Types if x.classID == objectInfo.typeID][0]
				isDestroyed = reader.ReadUInt16()
			else:
				typ = self.m_Types[objectInfo.typeID]
				objectInfo.serializedType = typ
				objectInfo.classID = ClassIDType(typ.classID)
			
			if header.m_Version == 15 or header.m_Version == 16:
				stripped = reader.ReadByte()
			
			self.m_Objects.append(objectInfo)
		
		if header.m_Version >= 11:
			scriptCount = reader.ReadInt32()
			self.m_ScriptTypes = []
			for i in range(scriptCount):
				m_ScriptType = LocalSerializedObjectIdentifier()
				m_ScriptType.localSerializedFileIndex = reader.ReadInt32()
				if header.m_Version < 14:
					m_ScriptType.localIdentifierInFile = reader.ReadInt32()
				else:
					reader.AlignStream()
					m_ScriptType.localIdentifierInFile = reader.ReadInt64()
				self.m_ScriptTypes.append(m_ScriptType)
		
		externalsCount = reader.ReadInt32()
		self.m_Externals = []
		for i in range(externalsCount):
			m_External = FileIdentifier()
			if header.m_Version >= 6:
				tempEmpty = reader.ReadStringToNull()
			if header.m_Version >= 5:
				m_External.guid = reader.ReadBytes(16)
				m_External.type = reader.ReadInt32()
			m_External.pathName = reader.ReadStringToNull()
			m_External.fileName = os.path.basename(m_External.pathName)
			self.m_Externals.append(m_External)
		
		if header.m_Version >= 5:
			pass
			# var userInformation = reader.ReadStringToNull();
	
	def SetVersion(self, stringVersion):
		self.unityVersion = stringVersion
		self.buildType = BuildType(re.findall(r'([^\d.])', stringVersion)[0])
		versionSplit = re.split(r'\D', stringVersion)
		self.version = [int(x) for x in versionSplit]
	
	def ReadSerializedType(self):
		type_ = SerializedType()
		type_.classID = self.reader.ReadInt32()
		
		if self.header.m_Version >= 16:
			type_.m_IsStrippedType = self.reader.ReadBoolean()
		
		if self.header.m_Version >= 17:
			type_.m_ScriptTypeIndex = self.reader.ReadInt16()
		
		if self.header.m_Version >= 13:
			if (self.header.m_Version < 16 and type_.classID < 0) or (self.header.m_Version >= 16 and type_.classID == 114):
				type_.m_ScriptID = self.reader.ReadBytes(16)  # Hash128
			type_.m_OldTypeHash = self.reader.ReadBytes(16)  # Hash128
		
		if self.m_EnableTypeTree:
			typeTree = []
			if self.header.m_Version >= 12 or self.header.m_Version == 10:
				self.ReadTypeTree5(typeTree)
			else:
				self.ReadTypeTree(typeTree)
			
			type_.m_Nodes = typeTree
		
		return type_
	
	def ReadTypeTree(self, typeTree, level = 0):
		typeTreeNode = TypeTreeNode()
		typeTree.append(typeTreeNode)
		typeTreeNode.m_Level = level
		typeTreeNode.m_Type = self.reader.ReadStringToNull()
		typeTreeNode.m_Name = self.reader.ReadStringToNull()
		typeTreeNode.m_ByteSize = self.reader.ReadInt32()
		if self.header.m_Version == 2:
			variableCount = self.reader.ReadInt32()
		
		if self.header.m_Version != 3:
			typeTreeNode.m_Index = self.reader.ReadInt32()
		
		typeTreeNode.m_IsArray = self.reader.ReadInt32()
		typeTreeNode.m_Version = self.reader.ReadInt32()
		if self.header.m_Version != 3:
			typeTreeNode.m_MetaFlag = self.reader.ReadInt32()
		
		childrenCount = self.reader.ReadInt32()
		for i in range(childrenCount):
			self.ReadTypeTree(typeTree, level + 1)
	
	def ReadTypeTree5(self, typeTree):
		numberOfNodes = self.reader.ReadInt32()
		stringBufferSize = self.reader.ReadInt32()
		
		nodeSize = 24
		if self.header.m_Version > 17:
			nodeSize = 32
		
		self.reader.Position += numberOfNodes * nodeSize
		stringBufferReader = EndianBinaryReader(
				self.reader.read(stringBufferSize))
		self.reader.Position -= numberOfNodes * nodeSize + stringBufferSize
		
		for i in range(numberOfNodes):
			typeTreeNode = TypeTreeNode()
			typeTree.append(typeTreeNode)
			typeTreeNode.m_Version = self.reader.ReadUInt16()
			typeTreeNode.m_Level = self.reader.ReadByte()
			typeTreeNode.m_IsArray = self.reader.ReadBoolean()
			typeTreeNode.m_TypeStrOffset = self.reader.ReadUInt32()
			typeTreeNode.m_NameStrOffset = self.reader.ReadUInt32()
			typeTreeNode.m_ByteSize = self.reader.ReadInt32()
			typeTreeNode.m_Index = self.reader.ReadInt32()
			typeTreeNode.m_MetaFlag = self.reader.ReadInt32()
			
			if self.header.m_Version > 17:
				self.reader.Position += 8
			
			typeTreeNode.m_Type = self.ReadString(
					stringBufferReader, typeTreeNode.m_TypeStrOffset)
			typeTreeNode.m_Name = self.ReadString(
					stringBufferReader, typeTreeNode.m_NameStrOffset)
		
		self.reader.Position += stringBufferSize
	
	def ReadString(self, stringBufferReader, value):
		isOffset = (value & 0x80000000) == 0
		if isOffset:
			stringBufferReader.Position = value
			return stringBufferReader.ReadStringToNull()
		
		offset = value & 0x7FFFFFFF
		if offset in CommonString:
			return CommonString[offset]
		
		return str(offset)
