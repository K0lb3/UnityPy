import os
import re
import sys

from ..CommonString import COMMON_STRING
from ..EndianBinaryReader import EndianBinaryReader
from ..EndianBinaryWriter import EndianBinaryWriter
from ..ObjectReader import ObjectReader
from ..enums import BuildTarget, ClassIDType

RECURSION_LIMIT = sys.getrecursionlimit()


class SerializedFileHeader:
	metadata_size: int
	file_size: int
	version: int
	data_offset: int
	endian: bytes
	reserved: bytes

	def __init__(self, reader: EndianBinaryReader):
		self.metadata_size = reader.read_u_int()
		self.file_size = reader.read_u_int()
		self.version = reader.read_u_int()
		self.data_offset = reader.read_u_int()


class LocalSerializedObjectIdentifier:  # script type
	local_serialized_file_index: int
	local_identifier_in_file: int

	def __init__(self, header: SerializedFileHeader, reader: EndianBinaryReader):
		self.local_serialized_file_index = reader.read_int()
		if header.version < 14:
			self.local_identifier_in_file = reader.read_int()
		else:
			reader.align_stream()
			self.local_identifier_in_file = reader.read_long()

	def write(self, header: SerializedFileHeader, writer: EndianBinaryWriter):
		writer.write_int(self.local_serialized_file_index)
		if header.version < 14:
			writer.write_int(self.local_identifier_in_file)
		else:
			writer.align_stream()
			writer.write_long(self.local_identifier_in_file)


class FileIdentifier:  # external
	guid: bytes
	type: int
	# enum { kNonAssetType = 0, kDeprecatedCachedAssetType = 1, kSerializedAssetType = 2, kMetaAssetType = 3 };
	path: str

	@property
	def name(self):
		return os.path.basename(self.path)

	def __init__(self, header: SerializedFileHeader, reader: EndianBinaryReader):
		if header.version >= 6:
			self.temp_empty = reader.read_string_to_null()
		if header.version >= 5:
			self.guid = reader.read_bytes(16)
			self.type = reader.read_int()
		self.path = reader.read_string_to_null()

	def write(self, header: SerializedFileHeader, writer: EndianBinaryWriter):
		if header.version >= 6:
			writer.write_string_to_null(self.temp_empty)
		if header.version >= 5:
			writer.write_bytes(self.guid)
			writer.write_int(self.type)
		writer.write_string_to_null(self.path)


class TypeTreeNode:
	type: str
	name: str
	byte_size: int
	index: int
	is_array: int
	version: int
	meta_flag: int
	level: int
	type_str_offset: int
	name_str_offset: int


class BuildType:
	build_type: str

	def __init__(self, build_type):
		self.build_type = build_type

	@property
	def is_alpha(self):
		return self.build_type == 'a'

	@property
	def is_path(self):
		return self.build_type == 'p'


class SerializedType:
	class_id: ClassIDType
	is_stripped_type: bool
	script_type_index = -1
	nodes: list = []  # TypeTreeNode
	script_id: bytes  # Hash128
	old_type_hash: bytes  # Hash128}


class ObjectInfo:
	byte_start: int
	byte_size: int
	type_id: int
	class_id: ClassIDType
	path_id: int
	serialized_type: SerializedType

	def __init__(self, header, reader, types):
		if header.version < 14:
			self.path_id = reader.read_int()
		else:
			reader.align_stream()
			self.path_id = reader.read_long()

		self.byte_start = reader.read_u_int()
		self.byte_start += header.data_offset
		self.byte_size = reader.read_u_int()
		self.type_id = reader.read_int()
		if header.version < 16:
			self.class_id = ClassIDType(reader.read_u_short())
			# _types.Find(x => x.class_id == object_info.type_id)
			if types:
				self.serialized_type = [
					x for x in types if x.class_id == self.type_id][0]
			else:
				self.serialized_type = SerializedType()
			self.is_destroyed = reader.read_u_short()
		else:
			typ = types[self.type_id]
			self.serialized_type = typ
			self.class_id = ClassIDType(typ.class_id)

		if header.version == 15 or header.version == 16:
			self.stripped = reader.read_byte()

	def write(self, header, writer):
		if header.version < 14:
			writer.write_int(self.path_id)
		else:
			writer.align_stream()
			writer.write_long(self.path_id)

		writer.write_u_int(self.byte_start - header.data_offset)
		writer.write_u_int(self.byte_size)
		writer.writ_int(self.type_id)

		if header.version < 16:
			# WARNING - CLASSIDTYPE MIGHT CHANGE THE NUMBER IF IT'S UNNOWN
			writer.write_u_short(int(self.class_id))
			writer.write_u_short(self.is_destroyed)

		if header.version == 15 or header.version == 16:
			writer.write_byte(self.stripped)


class SerializedFile:
	reader: EndianBinaryReader
	full_name: str
	unity_version: str
	version: list
	build_type: BuildType
	target_platform: BuildTarget
	_types: list
	_objects: list
	_script_types: list
	_externals: list
	_container: dict
	objects: dict
	container: dict
	_cache: dict
	header: SerializedFileHeader

	@property
	def name(self) -> str:
		return os.path.basename(self.full_name)

	def __repr__(self):
		return "<%s %s>" % (
			self.__class__.__name__, self.name
		)

	def __init__(self, assets_manager, full_name: str, reader: EndianBinaryReader):
		self.assets_manager = assets_manager
		self.reader = reader
		self.full_name = full_name

		self.unity_version = "2.5.0f5"
		self.version = [0, 0, 0, 0]
		self.build_type = BuildType("")
		self.target_platform = BuildTarget.UnknownPlatform
		self._enable_type_tree = True
		self._types = []
		self._objects = []
		self._script_types = []
		self._externals = []
		self._container = {}

		self.objects = {}
		self.container = {}
		# used to speed up mass asset extraction
		# some assets refer to each other, so by keeping the result
		# of specific assets cached the extraction can be speed up by a lot.
		# used by: Sprite (Texture2D (with alpha) cached),
		self._cache = {}

		# ReadHeader
		header = SerializedFileHeader(reader)
		self.header = header

		if header.version >= 9:
			header.endian = '>' if reader.read_boolean() else '<'
			header.reserved = reader.read_bytes(3)
		else:
			reader.Position = header.file_size - header.metadata_size
			header.endian = '>' if reader.read_boolean() else '<'

		reader.endian = header.endian

		if header.version >= 7:
			unity_version = reader.read_string_to_null()
			self.set_version(unity_version)

		if header.version >= 8:
			self._m_target_platform = reader.read_int()
			try:
				self.target_platform = BuildTarget(self._m_target_platform)
			except KeyError:
				self.target_platform = BuildTarget.UnknownPlatform

		if header.version >= 13:
			self._enable_type_tree = reader.read_boolean()

		# ReadTypes
		type_count = reader.read_int()

		self._types = [
			self.read_serialized_type()
			for _ in range(type_count)
		]

		if 7 <= header.version < 14:
			self.big_id_enabled = reader.read_int()

		# ReadObjects
		object_count = reader.read_int()
		self._objects = [
			ObjectInfo(header, reader, self._types)
			for _ in range(object_count)
		]

		if header.version >= 11:
			script_count = reader.read_int()
			self._script_types = [
				LocalSerializedObjectIdentifier(header, reader)
				for _ in range(script_count)
			]

		externals_count = reader.read_int()
		self._externals = [
			FileIdentifier(header, reader)
			for _ in range(externals_count)
		]

		self.userInformation = reader.read_string_to_null()

		# read the asset_bundles to get the containers
		old_pos = reader.Position

		self.objects = {
			object_info.path_id: ObjectReader(reader, self, object_info)
			for object_info in self._objects
		}

		for obj in self.objects.values():
			if obj.type == ClassIDType.AssetBundle:
				data = obj.read()
				for container, asset_info in data.container.items():
					asset = asset_info.asset
					self.container[container] = asset
					self._container[asset.path_id] = container

		reader.Position = old_pos

	def set_version(self, string_version):
		self.unity_version = string_version
		self.build_type = BuildType(re.findall(r'([^\d.])', string_version)[0])
		version_split = re.split(r'\D', string_version)
		self.version = [int(x) for x in version_split]

	def read_serialized_type(self):
		type_ = SerializedType()
		type_.class_id = self.reader.read_int()

		if self.header.version >= 16:
			type_.is_stripped_type = self.reader.read_boolean()

		if self.header.version >= 17:
			type_.script_type_index = self.reader.read_short()

		if self.header.version >= 13:
			if (self.header.version < 16 and type_.class_id < 0) or (
				self.header.version >= 16 and type_.class_id == 114):
				type_.script_id = self.reader.read_bytes(16)  # Hash128
			type_.old_type_hash = self.reader.read_bytes(16)  # Hash128

		if self._enable_type_tree:
			type_tree = []
			if self.header.version >= 12 or self.header.version == 10:
				self.read_type_tree5(type_tree)
			else:
				self.read_type_tree(type_tree)

			type_.nodes = type_tree

		return type_

	def read_type_tree(self, type_tree, level=0):
		if level == RECURSION_LIMIT - 1:
			raise RecursionError

		type_tree_node = TypeTreeNode()
		type_tree.append(type_tree_node)
		type_tree_node.level = level
		type_tree_node.type = self.reader.read_string_to_null()
		type_tree_node.name = self.reader.read_string_to_null()
		type_tree_node.byte_size = self.reader.read_int()
		if self.header.version == 2:
			type_tree_node.variable_count = self.reader.read_int()

		if self.header.version != 3:
			type_tree_node.index = self.reader.read_int()

		type_tree_node.is_array = self.reader.read_int()
		type_tree_node.version = self.reader.read_int()
		if self.header.version != 3:
			type_tree_node.meta_flag = self.reader.read_int()

		children_count = self.reader.read_int()
		for i in range(children_count):
			self.read_type_tree(type_tree, level + 1)

	def read_type_tree5(self, type_tree):
		number_of_nodes = self.reader.read_int()
		string_buffer_size = self.reader.read_int()

		node_size = 24
		if self.header.version > 17:
			node_size = 32

		self.reader.Position += number_of_nodes * node_size
		string_buffer_reader = EndianBinaryReader(
			self.reader.read(string_buffer_size))
		self.reader.Position -= number_of_nodes * node_size + string_buffer_size

		for i in range(number_of_nodes):
			type_tree_node = TypeTreeNode()
			type_tree.append(type_tree_node)
			type_tree_node.version = self.reader.read_u_short()
			type_tree_node.level = self.reader.read_byte()
			type_tree_node.is_array = self.reader.read_boolean()
			type_tree_node.type_str_offset = self.reader.read_u_int()
			type_tree_node.name_str_offset = self.reader.read_u_int()
			type_tree_node.byte_size = self.reader.read_int()
			type_tree_node.index = self.reader.read_int()
			type_tree_node.meta_flag = self.reader.read_int()

			if self.header.version > 17:
				self.reader.Position += 8

			type_tree_node.type = read_string(
				string_buffer_reader, type_tree_node.type_str_offset)
			type_tree_node.name = read_string(
				string_buffer_reader, type_tree_node.name_str_offset)

		self.reader.Position += string_buffer_size

	def save(self) -> bytes:
		# adjust metadata_size, data_offst and file_size
		header = self.header
		types = self._types
		objects = self._objects
		script_types = self._script_types
		externals = self._externals

		# fix header
		# metadata_size
		# file_size
		# data_offset

		# write-up
		writer = EndianBinaryWriter()
		# header
		writer.write_u_int(header.metadata_size)
		writer.write_u_int(header.file_size)
		writer.write_u_int(header.version)
		writer.write_u_int(header.data_offset)

		if header.version >= 9:
			writer.write_boolean(header.endian == '>')
			writer.write_bytes(header.reserved)
		else:
			NotImplementedError("old header version")
		# reader.Position = header.file_size - header.metadata_size
		# header.endian = '>' if reader.read_boolean() else '<'

		writer.endian = header.endian

		if header.version >= 7:
			writer.write_string_to_null(self.unity_version)

		if header.version >= 8:
			writer.write_int(self._m_target_platform)

		if header.version >= 13:
			writer.write_boolean(self._enable_type_tree)

		# types
		writer.write(len(types))
		for typ in types:
			self.save_serialized_type(typ, header, writer)

		if 7 <= header.version < 14:
			writer.write_int(self.big_id_enabled)

		# objects
		writer.write_int(len(objects))
		for obj in objects:
			obj.write(writer, header, writer)

		# scripts
		if header.version >= 11:
			writer.write_int(len(script_types))
			for script_type in script_types:
				script_type.write(header, writer)

		# externals
		writer.write_int(len(externals))
		for external in externals:
			external.write(header, writer)

		writer.write_string_to_null(self.userInformation)

		return writer.bytes

	def save_serialized_type(self, typ: SerializedType, header: SerializedFileHeader, writer: EndianBinaryWriter):
		writer.write_int(typ.class_id)

		if header.version >= 16:
			writer.write_boolean(typ.is_stripped_type)

		if header.version >= 17:
			writer.write_short(typ.script_type_index)

		if header.version >= 13:
			if (header.version < 16 and typ.class_id < 0) or (
				header.version >= 16 and typ.class_id == 114):
				writer.write_bytes(typ.script_id)  # Hash128
			writer.write_bytes(header.old_type_hash)  # Hash128

		if self._enable_type_tree:
			if header.version >= 12 or header.version == 10:
				self.save_type_tree5(typ.nodes, writer)
			else:
				self.save_type_tree(typ.nodes, writer)

	def save_type_tree(self, nodes: list, writer: EndianBinaryWriter):
		for i, node in nodes:
			writer.write_string_to_null(node.type)
			writer.write_string_to_null(node.name)
			writer.write_int(node.byte_size)
			if self.header.version == 2:
				writer.write_int(node.variable_count)

			if self.header.version != 3:
				writer.write_int(node.index)

			writer.write_int(node.is_array)
			writer.write_int(node.version)
			if self.header.version != 3:
				writer.write_int(node.meta_flag)

			# calc children count
			children_count = 0
			for node2 in nodes[i + 1:]:
				if node2.level == node.level:
					break
				if node2.level == node.level - 1:
					children_count += 1
			writer.write_int(children_count)

	def save_type_tree5(self, nodes: list, writer: EndianBinaryWriter):
		# node count
		# stream buffer size
		# node data
		# string buffer
		string_buffer = EndianBinaryWriter()
		for node in nodes:
			string_buffer.write_string_to_null(node.type)
			string_buffer.write_string_to_null(node.name)

		writer.write_int(len(nodes))
		writer.write_int(string_buffer.Length)

		offset = 0
		for node in nodes:
			writer.write_u_short(node.version)
			writer.write_byte(node.level)
			writer.write_boolean(node.is_array)
			writer.write_u_int(offset)
			offset += len(node.type)
			writer.write_u_int(offset)
			offset += len(node.name)
			writer.write_int(node.byte_size)
			writer.write_int(node.index)
			writer.write_int(node.meta_flag)

			if self.header.version > 17:
				writer.write(b"\x00" * 8)

		writer.write(string_buffer.bytes)


def read_string(string_buffer_reader, value) -> str:
	is_offset = (value & 0x80000000) == 0
	if is_offset:
		string_buffer_reader.Position = value
		return string_buffer_reader.read_string_to_null()

	offset = value & 0x7FFFFFFF
	if offset in COMMON_STRING:
		return COMMON_STRING[offset]

	return str(offset)
