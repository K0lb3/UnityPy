import os
import re
import sys

from ..CommonString import COMMON_STRING
from ..EndianBinaryReader import EndianBinaryReader
from ..ObjectReader import ObjectReader
from ..enums import BuildTarget, ClassIDType

RECURSION_LIMIT = sys.getrecursionlimit()


class SerializedFileHeader:
	metadata_size: int
	file_size: int
	version: int
	data_offset: int
	endianess: bytes
	reserved: bytes


class LocalSerializedObjectIdentifier:
	local_serialized_file_index: int
	local_identifier_in_file: int


class FileIdentifier:
	guid: str
	type: int
	# enum { kNonAssetType = 0, kDeprecatedCachedAssetType = 1, kSerializedAssetType = 2, kMetaAssetType = 3 };
	path_name: str
	# custom
	file_name: str


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
	def __init__(self, build_type: str = ""):
		self.build_type = build_type
		self.is_alpha = self.build_type == 'a'
		self.is_path = self.build_type == 'p'


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


class SerializedFile:
	reader: EndianBinaryReader
	full_name: str
	file_name: str
	unity_version: str
	version: list
	build_type: ""
	_target_platform: BuildTarget
	_types: list
	_objects: list
	_script_types: list
	_externals: list
	_container: dict
	objects: dict
	container: dict
	_cache: dict
	header: SerializedFileHeader

	def __init__(self, assets_manager, full_name: str, reader: EndianBinaryReader):
		self.assets_manager = assets_manager
		self.reader = reader
		self.full_name = full_name
		self.file_name = os.path.basename(full_name)

		self.unity_version = "2.5.0f5"
		self.version = [0, 0, 0, 0]
		self.build_type = ""
		self._target_platform = BuildTarget.UnknownPlatform
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
		header = SerializedFileHeader()
		self.header = header
		header.metadata_size = reader.read_u_int()
		header.file_size = reader.read_u_int()
		header.version = reader.read_u_int()
		header.data_offset = reader.read_u_int()

		if header.version >= 9:
			header.endianess = '>' if reader.read_boolean() else '<'
			header.reserved = reader.read_bytes(3)
		else:
			reader.Position = header.file_size - header.metadata_size
			header.endianess = '>' if reader.read_boolean() else '<'

		reader.endian = header.endianess

		if header.version >= 7:
			unity_version = reader.read_string_to_null()
			self.set_version(unity_version)

		if header.version >= 8:
			m_target_platform = reader.read_int()
			try:
				self._target_platform = BuildTarget(m_target_platform)
			except KeyError:
				self._target_platform = BuildTarget.UnknownPlatform

		if header.version >= 13:
			self._enable_type_tree = reader.read_boolean()

		# ReadTypes
		type_count = reader.read_int()

		self._types = [
			self.read_serialized_type()
			for _ in range(type_count)
		]

		if 7 <= header.version < 14:
			big_id_enabled = reader.read_int()

		# ReadObjects
		object_count = reader.read_int()
		asset_bundles = []
		for i in range(object_count):
			object_info = ObjectInfo()
			if header.version < 14:
				object_info.path_id = reader.read_int()
			else:
				reader.align_stream()
				object_info.path_id = reader.read_long()

			object_info.byte_start = reader.read_u_int()
			object_info.byte_start += header.data_offset
			object_info.byte_size = reader.read_u_int()
			object_info.type_id = reader.read_int()
			if header.version < 16:
				object_info.class_id = ClassIDType(reader.read_u_short())
				# _types.Find(x => x.class_id == object_info.type_id)
				object_info.serialized_type = [
					x for x in self._types if x.class_id == object_info.type_id][0]
				is_destroyed = reader.read_u_short()
			else:
				typ = self._types[object_info.type_id]
				object_info.serialized_type = typ
				object_info.class_id = ClassIDType(typ.class_id)

			if header.version == 15 or header.version == 16:
				stripped = reader.read_byte()

			self._objects.append(object_info)
			# user object
			object_reader = ObjectReader(reader, self, object_info)
			self.objects[object_info.path_id] = object_reader

			if object_info.class_id == ClassIDType.AssetBundle:
				asset_bundles.append(object_reader)

		if header.version >= 11:
			script_count = reader.read_int()
			for i in range(script_count):
				m_script_type = LocalSerializedObjectIdentifier()
				m_script_type.local_serialized_file_index = reader.read_int()
				if header.version < 14:
					m_script_type.local_identifier_in_file = reader.read_int()
				else:
					reader.align_stream()
					m_script_type.local_identifier_in_file = reader.read_long()
				self._script_types.append(m_script_type)

		externals_count = reader.read_int()
		for i in range(externals_count):
			m_external = FileIdentifier()
			if header.version >= 6:
				temp_empty = reader.read_string_to_null()
			if header.version >= 5:
				m_external.guid = reader.read_bytes(16)
				m_external.type = reader.read_int()
			m_external.path_name = reader.read_string_to_null()
			m_external.file_name = os.path.basename(m_external.path_name)
			self._externals.append(m_external)

		# var userInformation = reader.read_string_to_null();

		# read the asset_bundles to get the containers
		if asset_bundles:
			old_pos = reader.Position
			for object_reader in asset_bundles:
				data = object_reader.read()
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
			variable_count = self.reader.read_int()

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


def read_string(string_buffer_reader, value) -> str:
	is_offset = (value & 0x80000000) == 0
	if is_offset:
		string_buffer_reader.Position = value
		return string_buffer_reader.read_string_to_null()

	offset = value & 0x7FFFFFFF
	if offset in COMMON_STRING:
		return COMMON_STRING[offset]

	return str(offset)
