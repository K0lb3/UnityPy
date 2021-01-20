import os
import re
import sys

from . import File
from .. import classes
from ..CommonString import COMMON_STRING
from ..enums import BuildTarget, ClassIDType
from ..streams import EndianBinaryReader, EndianBinaryWriter

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

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.path})>"

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
        return self.build_type == "a"

    @property
    def is_path(self):
        return self.build_type == "p"


class SerializedType:
    class_id: ClassIDType
    is_stripped_type: bool
    script_type_index = -1
    nodes: list = []  # TypeTreeNode
    script_id: bytes  # Hash128
    old_type_hash: bytes  # Hash128}


class SerializedFile(File.File):
    reader: EndianBinaryReader
    is_changed: bool
    unity_version: str
    version: list
    build_type: BuildType
    target_platform: BuildTarget
    types: list
    script_types: list
    externals: list
    _container: dict
    objects: dict
    container_: dict
    _cache: dict
    header: SerializedFileHeader

    @property
    def files(self):
        return self.objects

    def __init__(self, reader: EndianBinaryReader, parent=None):
        self.is_changed = False
        self.parent = parent
        self.reader = reader

        self.unity_version = "2.5.0f5"
        self.version = (0, 0, 0, 0)
        self.build_type = BuildType("")
        self.target_platform = BuildTarget.UnknownPlatform
        self._enable_type_tree = True
        self.types = []
        self.script_types = []
        self.externals = []
        self._container = {}

        self.objects = {}
        self.container_ = {}
        # used to speed up mass asset extraction
        # some assets refer to each other, so by keeping the result
        # of specific assets cached the extraction can be speed up by a lot.
        # used by: Sprite (Texture2D (with alpha) cached),
        self._cache = {}
        self.unknown = 0

        # ReadHeader
        header = SerializedFileHeader(reader)
        self.header = header

        if header.version >= 9:
            header.endian = ">" if reader.read_boolean() else "<"
            header.reserved = reader.read_bytes(3)
        else:
            reader.Position = header.file_size - header.metadata_size
            header.endian = ">" if reader.read_boolean() else "<"

        if header.version >= 22:
            header.metadata_size = reader.read_u_int()
            header.file_size = reader.read_long()
            header.data_offset = reader.read_long()
            self.unknown = reader.read_long()  # unknown

        reader.endian = header.endian

        if header.version >= 7:
            unity_version = reader.read_string_to_null()
            self.set_version(unity_version)

        if header.version >= 8:
            self._m_target_platform = reader.read_int()
            self.target_platform = BuildTarget(self._m_target_platform)

        if header.version >= 13:
            self._enable_type_tree = reader.read_boolean()

        # ReadTypes
        type_count = reader.read_int()
        self.types = [self.read_serialized_type() for _ in range(type_count)]

        self.big_id_enabled = 0
        if 7 <= header.version < 14:
            self.big_id_enabled = reader.read_int()

        # ReadObjects
        object_count = reader.read_int()
        self.objects = {}
        for _ in range(object_count):
            obj = ObjectReader(self, reader)
            self.objects[obj.path_id] = obj

        # Read Scripts
        if header.version >= 11:
            script_count = reader.read_int()
            self.script_types = [
                LocalSerializedObjectIdentifier(header, reader)
                for _ in range(script_count)
            ]

        # Read Externals
        externals_count = reader.read_int()
        self.externals = [
            FileIdentifier(header, reader) for _ in range(externals_count)
        ]

        if header.version >= 20:
            ref_type_count = reader.read_int()
            self.ref_types = [
                self.read_serialized_type() for _ in range(ref_type_count)
            ]

        if header.version >= 5:
            self.userInformation = reader.read_string_to_null()

        # read the asset_bundles to get the containers
        for obj in self.objects.values():
            if obj.type == ClassIDType.AssetBundle:
                data = obj.read()
                for container, asset_info in data.container.items():
                    asset = asset_info.asset
                    self.container_[container] = asset
                    if hasattr(asset, "path_id"):
                        self._container[asset.path_id] = container
        #if environment is not None:
        #    environment.container = {**environment.container, **self.container}

    @property
    def container(self):
        return self.container_

    def set_version(self, string_version):
        self.unity_version = string_version
        build_type = re.findall(r"([^\d.])", string_version)
        self.build_type = BuildType(build_type[0] if build_type else "")
        version_split = re.split(r"\D", string_version)
        self.version = tuple(int(x) for x in version_split)

    def mark_changed(self):
        self.is_changed = True
        if self.parent:
            self.parent.mark_changed()

    def read_serialized_type(self):
        type_ = SerializedType()
        type_.class_id = self.reader.read_int()

        if self.header.version >= 16:
            type_.is_stripped_type = self.reader.read_boolean()

        if self.header.version >= 17:
            type_.script_type_index = self.reader.read_short()

        if self.header.version >= 13:
            if (self.header.version < 16 and type_.class_id < 0) or (
                self.header.version >= 16 and type_.class_id == 114
            ):
                type_.script_id = self.reader.read_bytes(16)  # Hash128
            type_.old_type_hash = self.reader.read_bytes(16)  # Hash128

        if self._enable_type_tree:
            type_tree = []
            if self.header.version >= 12 or self.header.version == 10:
                type_.string_data = self.read_type_tree_blob(type_tree)
            else:
                self.read_type_tree(type_tree)

            if self.header.version >= 21:
                type_.type_dependencies = self.reader.read_int_array()

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

    def read_type_tree_blob(self, type_tree):
        reader = self.reader
        number_of_nodes = self.reader.read_int()
        string_buffer_size = self.reader.read_int()

        for _ in range(number_of_nodes):
            node = TypeTreeNode()
            type_tree.append(node)
            node.version = reader.read_u_short()
            node.level = reader.read_byte()
            node.is_array = reader.read_boolean()
            node.type_str_offset = reader.read_u_int()
            node.name_str_offset = reader.read_u_int()
            node.byte_size = reader.read_int()
            node.index = reader.read_int()
            node.meta_flag = reader.read_int()

            if self.header.version > 19:
                node.ref_type_hash = reader.read_u_long()

        string_buffer_reader = EndianBinaryReader(
            reader.read(string_buffer_size), reader.endian)
        for node in type_tree:
            node.type = read_string(string_buffer_reader, node.type_str_offset)
            node.name = read_string(string_buffer_reader, node.name_str_offset)

        return string_buffer_reader.bytes

    def save(self, packer: str = "none") -> bytes:
        # Structure:
        #   1. header
        #       file header
        #       types
        #       objects
        #       scripts
        #       externals
        #   2. small 0es offset - align stream
        #   3. objects data

        # adjust metadata_size, data_offst and file_size
        header = self.header
        types = self.types
        objects = self.objects
        script_types = self.script_types
        externals = self.externals

        # the data-offset is required for the header and is kinda hard to calculate,
        # so we split the asset building up into multiple parts
        fileheader_writer = EndianBinaryWriter()
        header_writer = EndianBinaryWriter(endian=header.endian)
        data_writer = EndianBinaryWriter(endian=header.endian)

        # 1. building the header without file header

        # reader.Position = header.file_size - header.metadata_size
        # header.endian = '>' if reader.read_boolean() else '<'
        if header.version < 9:
            header_writer.write_boolean(header.endian == ">")

        if header.version >= 7:
            header_writer.write_string_to_null(self.unity_version)

        if header.version >= 8:
            header_writer.write_int(self._m_target_platform)

        if header.version >= 13:
            header_writer.write_boolean(self._enable_type_tree)

        # types
        header_writer.write_int(len(types))
        for typ in types:
            self.save_serialized_type(typ, header, header_writer)

        if 7 <= header.version < 14:
            header_writer.write_int(self.big_id_enabled)

        # objects
        header_writer.write_int(len(objects))
        for i, obj in enumerate(objects.values()):
            obj.write(header, header_writer, data_writer)
            if i < len(objects) - 1:
                data_writer.align_stream(8)

        # scripts
        if header.version >= 11:
            header_writer.write_int(len(script_types))
            for script_type in script_types:
                script_type.write(header, header_writer)

        # externals
        header_writer.write_int(len(externals))
        for external in externals:
            external.write(header, header_writer)

        header_writer.write_string_to_null(self.userInformation)
        if header.version >= 21:
            header_writer.write_int(self.unknown)

        if header.version >= 9:
            # file header
            fileheader_size = 4 * 4 + 1 + 3  # following + endian + reserved
            metadata_size = header_writer.Length
            # metadata size
            fileheader_writer.write_u_int(header_writer.Length)
            # align between metadata and data
            mod = (fileheader_size + metadata_size) % 16
            align_length = 16 - mod if mod else 0

            # file size
            fileheader_writer.write_u_int(
                header_writer.Length
                + data_writer.Length
                + fileheader_size
                + align_length
            )
            # version
            fileheader_writer.write_u_int(header.version)
            # data offset
            fileheader_writer.write_u_int(
                header_writer.Length + fileheader_size + align_length
            )
            # endian
            fileheader_writer.write_boolean(header.endian == ">")
            fileheader_writer.write_bytes(header.reserved)

            # self.reader.bytes[fileheader_size:fileheader_size+header_writer.Length] == header_writer.bytes

            return (
                fileheader_writer.bytes
                + header_writer.bytes
                + b"\x00" * align_length
                + data_writer.bytes
            )

        else:
            # file header
            fileheader_size = 4 * 4
            metadata_size = header_writer.Length
            # metadata size
            fileheader_writer.write_u_int(metadata_size)
            # file size
            fileheader_writer.write_u_int(
                metadata_size + data_writer.Length + fileheader_size
            )
            # version
            fileheader_writer.write_u_int(header.version)
            # data offset - unity seems to align the stream .... but it's apparently not necessary
            fileheader_writer.write_u_int(fileheader_size)

            return fileheader_writer.bytes + data_writer.bytes + header_writer.bytes

    def save_serialized_type(
        self,
        typ: SerializedType,
        header: SerializedFileHeader,
        writer: EndianBinaryWriter,
    ):
        writer.write_int(typ.class_id)

        if header.version >= 16:
            writer.write_boolean(typ.is_stripped_type)

        if header.version >= 17:
            writer.write_short(typ.script_type_index)

        if header.version >= 13:
            if (header.version < 16 and typ.class_id < 0) or (
                header.version >= 16 and typ.class_id == 114
            ):
                writer.write_bytes(typ.script_id)  # Hash128
            writer.write_bytes(typ.old_type_hash)  # Hash128

        if self._enable_type_tree:
            if header.version >= 12 or header.version == 10:
                self.save_type_tree5(typ.nodes, writer, typ.string_data)
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

    def save_type_tree5(self, nodes: list, writer: EndianBinaryWriter, str_data=b""):
        # node count
        # stream buffer size
        # node data
        # string buffer

        string_buffer = EndianBinaryWriter()
        """
        saved_strings = {}
        def save_string(value: str) -> int:
            import re
            if value in saved_strings:
                return saved_strings[value]

            for key, val in COMMON_STRING.items():
                if val == value:
                    return key | 0x80000000
            if re.match(r"\d+", value):
                return int(value)
            else:
                # normal string
                offset = string_buffer.Position
                saved_strings[value] = offset
                string_buffer.write_string_to_null(value)
                return offset
        """
        string_buffer.write(str_data)
        strings_values = [
            (node.type_str_offset, node.name_str_offset) for node in nodes
        ]

        # number of nodes
        writer.write_int(len(nodes))
        # string buffer size
        writer.write_int(string_buffer.Length)

        # nodes
        for i, node in enumerate(nodes):
            # version
            writer.write_u_short(node.version)
            # level
            writer.write_byte(node.level)
            # is array
            writer.write_boolean(node.is_array)
            # type str offfset
            writer.write_u_int(strings_values[i][0])
            # name str offset
            writer.write_u_int(strings_values[i][1])
            # byte size
            writer.write_int(node.byte_size)
            # index
            writer.write_int(node.index)
            # meta flag
            writer.write_int(node.meta_flag)
            # ref hash
            if self.header.version > 19:
                writer.write_u_long(node.ref_type_hash)

        # string buffer
        writer.write(string_buffer.bytes)

        if self.header.version >= 21:
            writer.write_bytes(b"\x00" * 4)


def read_string(string_buffer_reader: EndianBinaryReader, value: int) -> str:
    is_offset = (value & 0x80000000) == 0
    if is_offset:
        string_buffer_reader.Position = value
        return string_buffer_reader.read_string_to_null()

    offset = value & 0x7FFFFFFF
    if offset in COMMON_STRING:
        return COMMON_STRING[offset]

    return str(offset)


class ObjectReader:
    byte_start: int
    byte_size: int
    type_id: int
    class_id: ClassIDType
    path_id: int
    serialized_type: SerializedType

    def __init__(self, assets_file, reader):
        self.assets_file = assets_file
        self.reader = reader
        self.data = b""
        self.version = assets_file.version
        self.version2 = assets_file.header.version
        self.platform = assets_file.target_platform
        self.build_type = assets_file.build_type

        header = assets_file.header
        types = assets_file.types

        if assets_file.big_id_enabled:
            self.path_id = reader.read_long()
        elif header.version < 14:
            self.path_id = reader.read_int()
        else:
            reader.align_stream()
            self.path_id = reader.read_long()

        if header.version >= 22:
            self.byte_start_offset = (self.reader.real_offset(), 8)
            self.byte_start = reader.read_long()
        else:
            self.byte_start_offset = (self.reader.real_offset(), 4)
            self.byte_start = reader.read_u_int()

        self.byte_start += header.data_offset
        self.byte_header_offset = header.data_offset
        self.byte_base_offset = self.reader.BaseOffset

        self.byte_size_offset = (self.reader.real_offset(), 4)
        self.byte_size = reader.read_u_int()

        self.type_id = reader.read_int()
        if header.version < 16:
            self.class_id = reader.read_u_short()
            if types:
                self.serialized_type = (
                    x for x in types if x.class_id == self.type_id).__next__()
            else:
                self.serialized_type = SerializedType()
        else:
            typ = types[self.type_id]
            self.serialized_type = typ
            self.class_id = typ.class_id

        self.type = ClassIDType(self.class_id)

        if header.version < 11:
            self.is_destroyed = reader.read_u_short()

        if 11 <= header.version < 17:
            script_type_index = reader.read_short()
            if self.serialized_type:
                self.serialized_type.script_type_index = script_type_index

        if header.version == 15 or header.version == 16:
            self.stripped = reader.read_byte()

    def write(self, header, writer, data_writer):
        # validated
        if header.version < 14:
            writer.write_int(self.path_id)
        else:
            writer.align_stream()
            writer.write_long(self.path_id)

        if self.data:
            data = self.data
        else:
            self.reset()
            data = self.reader.read(self.byte_size)

        writer.write_u_int(data_writer.Position)
        writer.write_u_int(len(data))

        data_writer.write(data)

        writer.write_int(self.type_id)

        if header.version < 16:
            # WARNING - CLASSIDTYPE MIGHT CHANGE THE NUMBER IF IT'S UNKNOWN
            writer.write_u_short(self.class_id)
            writer.write_u_short(self.is_destroyed)

        if header.version == 15 or header.version == 16:
            writer.write_byte(self.stripped)

    def set_raw_data(self, data):
        self.data = data
        self.assets_file.mark_changed()

    @property
    def container(self):
        return (
            self.assets_file._container[self.path_id]
            if self.path_id in self.assets_file._container
            else None
        )

    def reset(self):
        self.reader.Position = self.byte_start

    def read(self):
        try:
            return getattr(classes, self.type.name, classes.Object)(self)
        except Exception as e:
            raise e
        # TODO: only specific exceptions here?
        except:
            # HACK: in case the parsing via the class fails this solution
            #       uses the type tree to set the variables and then changes the class
            obj = classes.Object(self)
            obj.__class__ = getattr(classes, self.type.name, classes.Object)
            for key, val in obj.__dict__.items():
                if " " in key:
                    obj.__dict__[key.replace(" ", "_")] = val
                    delattr(obj, key)
            return obj

    def __getattr__(self, item: str):
        if hasattr(self.reader, item):
            return getattr(self.reader, item)

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.type.name)
