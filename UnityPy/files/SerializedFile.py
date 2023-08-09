﻿from ntpath import basename
import re

from . import File, ObjectReader, BundleFile
from ..enums import BuildTarget, ClassIDType, CommonString
from ..streams import EndianBinaryReader, EndianBinaryWriter
from ..helpers.TypeTreeHelper import TypeTreeNode

from struct import Struct

from .. import config


class SerializedFileHeader:
    metadata_size: int
    file_size: int
    version: int
    data_offset: int
    endian: bytes
    reserved: bytes

    def __init__(self, reader: EndianBinaryReader):
        (
            self.metadata_size,
            self.file_size,
            self.version,
            self.data_offset,
        ) = reader.read_u_int_array(4)


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
        return basename(self.path)

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


class BuildType:
    build_type: str

    def __init__(self, build_type):
        self.build_type = build_type

    @property
    def IsAlpha(self):
        return self.build_type == "a"

    @property
    def IsPatch(self):
        return self.build_type == "p"


class SerializedType:
    class_id: int
    is_stripped_type: bool
    script_type_index = -1
    nodes: list = []  # TypeTreeNode
    script_id: bytes  # Hash128
    old_type_hash: bytes  # Hash128}

    def __init__(self, reader, serialized_file, is_ref_type: bool):
        version = serialized_file.header.version
        self.class_id = reader.read_int()

        if version >= 16:
            self.is_stripped_type = reader.read_boolean()

        if version >= 17:
            self.script_type_index = reader.read_short()

        if version >= 13:
            if (
                (is_ref_type and self.script_type_index >= 0)
                or (version < 16 and self.class_id < 0)
                or (version >= 16 and self.class_id == 114)
            ):
                self.script_id = reader.read_bytes(16)
            self.old_type_hash = reader.read_bytes(16)

        if serialized_file._enable_type_tree:
            if version >= 12 or version == 10:
                self.nodes, self.string_data = serialized_file.read_type_tree_blob()
            else:
                self.nodes = serialized_file.read_type_tree()

            if version >= 21:
                if is_ref_type:
                    self.m_ClassName = reader.read_string_to_null()
                    self.m_NameSpace = reader.read_string_to_null()
                    self.m_AssemblyName = reader.read_string_to_null()
                else:
                    self.type_dependencies = reader.read_int_array()

    def write(self, serialized_file, writer, is_ref_type):
        version = serialized_file.header.version
        writer.write_int(self.class_id)

        if version >= 16:
            writer.write_boolean(self.is_stripped_type)

        if version >= 17:
            writer.write_short(self.script_type_index)

        if version >= 13:
            if (
                (is_ref_type and self.script_type_index >= 0)
                or (version < 16 and self.class_id < 0)
                or (version >= 16 and self.class_id == 114)
            ):
                writer.write_bytes(self.script_id)  # Hash128
            writer.write_bytes(self.old_type_hash)  # Hash128

        if serialized_file._enable_type_tree:
            if version >= 12 or version == 10:
                serialized_file.save_type_tree5(self.nodes, writer, self.string_data)
            else:
                serialized_file.save_type_tree(self.nodes, writer)

            if version >= 21:
                if is_ref_type:
                    writer.write_string_to_null(self.m_ClassName)
                    writer.write_string_to_null(self.m_NameSpace)
                    writer.write_string_to_null(self.m_AssemblyName)
                else:
                    writer.write_int_array(self.type_dependencies)


class SerializedFile(File.File):
    reader: EndianBinaryReader
    is_changed: bool
    unity_version: str
    version: tuple
    build_type: BuildType
    target_platform: BuildTarget
    types: list
    script_types: list
    externals: list
    objects: dict
    _cache: dict
    assetbundle: "AssetBundle"
    container: "ContainerHelper"
    header: SerializedFileHeader

    @property
    def files(self):
        if self.objects:
            return self.objects
        return {}

    @files.setter
    def files(self, value):
        self.objects = value

    def __init__(self, reader: EndianBinaryReader, parent=None, name=None, **kwargs):
        super().__init__(parent=parent, name=name, **kwargs)
        self.reader = reader

        self.unity_version = "2.5.0f5"
        self.version = (0, 0, 0, 0)
        self.build_type = BuildType("")
        self.target_platform = BuildTarget.UnknownPlatform
        self._enable_type_tree = True
        self.types = []
        self.script_types = []
        self.externals = []
        self.objects = {}
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
            if header.version >= 22:
                header.metadata_size = reader.read_u_int()
                header.file_size = reader.read_long()
                header.data_offset = reader.read_long()
                self.unknown = reader.read_long()  # unknown
        else:
            reader.Position = header.file_size - header.metadata_size
            header.endian = ">" if reader.read_boolean() else "<"

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
        self.types = [SerializedType(reader, self, False) for _ in range(type_count)]

        self.big_id_enabled = 0
        if 7 <= header.version < 14:
            self.big_id_enabled = reader.read_int()

        # ReadObjects
        object_count = reader.read_int()
        self.objects = {}
        for _ in range(object_count):
            obj = ObjectReader.ObjectReader(self, reader)
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
                SerializedType(reader, self, True) for _ in range(ref_type_count)
            ]

        if config.SERIALIZED_FILE_PARSE_TYPETREE is False:
            self._enable_type_tree = False

        if header.version >= 5:
            self.userInformation = reader.read_string_to_null()

        # read the asset_bundles to get the containers
        for obj in self.objects.values():
            if obj.type == ClassIDType.AssetBundle:
                self.assetbundle = obj.read_typetree(wrap=True)
                self._container = ContainerHelper(self.assetbundle.m_Container)
                break
        else:
            self.assetbundle = None
            self._container = ContainerHelper({})

    @property
    def container(self):
        return self._container

    def load_dependencies(self, possible_dependencies: list = []):
        """Load all external dependencies.

        Parameters
        ----------
        possible_dependencies : list
            List of possible dependencies for cases
            where the target file is not listed as external.
        """
        for file_id in self.externals:
            self.environment.load_file(file_id.path, True)
        for dependency in possible_dependencies:
            try:
                self.environment.load_file(dependency, True)
            except FileNotFoundError:
                pass

    def set_version(self, string_version):
        self.unity_version = string_version
        if not string_version or string_version == "0.0.0":
            # weird case, but apparently can happen?
            # check "cant read Texture2D by 2020.3.13 f1 AssetBundle #77" for details
            if isinstance(self.parent, BundleFile.BundleFile):
                string_version = self.parent.version_engine
            if not string_version or string_version == "0.0.0":
                string_version = config.get_fallback_version()
        build_type = re.findall(r"([^\d.])", string_version)
        self.build_type = BuildType(build_type[0] if build_type else "")
        version_split = re.split(r"\D", string_version)
        self.version = tuple(int(x) for x in version_split)

    def read_type_tree(self):
        type_tree = []
        level_stack = [[0, 1]]
        while level_stack:
            level, count = level_stack[-1]
            if count == 1:
                level_stack.pop()
            else:
                level_stack[-1][1] -= 1

            type_tree_node = TypeTreeNode(
                m_Level=level,
                m_Type=self.reader.read_string_to_null(),
                m_Name=self.reader.read_string_to_null(),
                m_ByteSize=self.reader.read_int(),
            )

            type_tree.append(type_tree_node)
            if self.header.version == 2:
                type_tree_node.m_VariableCount = self.reader.read_int()

            if self.header.version != 3:
                type_tree_node.m_Index = self.reader.read_int()

            type_tree_node.m_TypeFlags = self.reader.read_int()
            type_tree_node.m_Version = self.reader.read_int()
            if self.header.version != 3:
                type_tree_node.m_MetaFlag = self.reader.read_int()

            children_count = self.reader.read_int()
            if children_count:
                level_stack.append([level + 1, children_count])
        return type_tree

    def read_type_tree_blob(self):
        reader = self.reader
        number_of_nodes = self.reader.read_int()
        string_buffer_size = self.reader.read_int()

        type = f"{reader.endian}hBBIIiii"
        keys = [
            "m_Version",
            "m_Level",
            "m_TypeFlags",
            "m_TypeStrOffset",
            "m_NameStrOffset",
            "m_ByteSize",
            "m_Index",
            "m_MetaFlag",
        ]
        if self.header.version >= 19:
            type += "Q"
            keys.append("m_RefTypeHash")

        node_struct = Struct(type)
        struct_data = reader.read(node_struct.size * number_of_nodes)
        string_buffer_reader = EndianBinaryReader(
            reader.read(string_buffer_size), reader.endian
        )

        if not config.SERIALIZED_FILE_PARSE_TYPETREE:
            return [], string_buffer_reader.bytes

        type_tree = [
            TypeTreeNode(
                **dict(zip(keys, raw_node)),
                m_Type=read_string(string_buffer_reader, raw_node[3]),
                m_Name=read_string(string_buffer_reader, raw_node[4]),
            )
            for i, raw_node in enumerate(node_struct.iter_unpack(struct_data))
        ]

        return type_tree, string_buffer_reader.bytes

    def get_writeable_cab(self, name: str = "CAB-UnityPy_Mod.resS"):
        """
        Creates a new cab file in the bundle that contains the given data.
        This is usefull for asset types that use resource files.
        """
        if not isinstance(
            self.parent, (File.BundleFile.BundleFile, File.WebFile.WebFile)
        ):
            return None

        cab = self.parent.get_writeable_cab(name)
        cab.path = f"archive:/{self.name}/{name}"
        if not any(cab.path == x.path for x in self.externals):
            # register as external
            class FileIdentifierFake:
                pass

            file_identifier = FileIdentifierFake()
            file_identifier.__class__ = FileIdentifier
            file_identifier.temp_empty = ""
            import uuid

            file_identifier.guid = uuid.uuid1().urn[-16:].encode("ascii")
            file_identifier.path = cab.path
            file_identifier.type = 0
            self.externals.append(file_identifier)

        return cab

    def save(self, packer: str = None) -> bytes:
        # 1. header -> has to be delayed until the very end
        # 2. data -> types, objects, scripts, ...

        # so write the data first
        header = self.header
        meta_writer = EndianBinaryWriter(endian=header.endian)
        data_writer = EndianBinaryWriter(endian=header.endian)

        if header.version >= 7:
            meta_writer.write_string_to_null(self.unity_version)

        if header.version >= 8:
            meta_writer.write_int(self._m_target_platform)

        if header.version >= 13:
            meta_writer.write_boolean(self._enable_type_tree)

        # ReadTypes
        meta_writer.write_int(len(self.types))
        for typ in self.types:
            typ.write(self, meta_writer, False)

        if 7 <= header.version < 14:
            meta_writer.write_int(self.big_id_enabled)

        # ReadObjects
        meta_writer.write_int(len(self.objects))
        for obj in self.objects.values():
            obj.write(header, meta_writer, data_writer)
            data_writer.align_stream(8)

        # Read Scripts
        if header.version >= 11:
            meta_writer.write_int(len(self.script_types))
            for script_type in self.script_types:
                script_type.write(header, meta_writer)

        # Read Externals
        meta_writer.write_int(len(self.externals))
        for external in self.externals:
            external.write(header, meta_writer)

        if header.version >= 20:
            meta_writer.write_int(len(self.ref_types))
            for ref_type in self.ref_types:
                ref_type.write(self, meta_writer, True)

        if header.version >= 5:
            meta_writer.write_string_to_null(self.userInformation)

        # prepare header
        writer = EndianBinaryWriter()
        header_size = 16  # 4*4
        metadata_size = meta_writer.Length
        data_size = data_writer.Length
        if header.version >= 9:
            # 1 bool + 3 reserved + extra header 4 + 3*8
            header_size += 4 if header.version < 22 else 4 + 28
            data_offset = header_size + metadata_size
            # align data_offset
            data_offset += (16 - data_offset % 16) % 16
            file_size = data_offset + data_size
            if header.version < 22:
                writer.write_u_int(metadata_size)
                writer.write_u_int(file_size)
                writer.write_u_int(header.version)
                # reader.Position = header.file_size - header.metadata_size
                # so data follows right after this header -> after 32
                writer.write_u_int(data_offset)
                writer.write_boolean(">" == header.endian)
                writer.write_bytes(header.reserved)
            else:
                # old header
                writer.write_u_int(0)
                writer.write_u_int(0)
                writer.write_u_int(header.version)
                writer.write_u_int(0)
                writer.write_boolean(">" == header.endian)
                writer.write_bytes(header.reserved)
                writer.write_u_int(metadata_size)
                writer.write_long(file_size)
                writer.write_long(data_offset)
                writer.write_long(self.unknown)

            writer.write_bytes(meta_writer.bytes)
            writer.align_stream(16)
            writer.write_bytes(data_writer.bytes)

        else:
            metadata_size += 1  # endian boolean
            file_size = header_size + metadata_size + data_size
            writer.write_u_int(metadata_size)
            writer.write_u_int(file_size)
            writer.write_u_int(header.version)
            # reader.Position = header.file_size - header.metadata_size
            # so data follows right after this header -> after 32
            writer.write_u_int(32)
            writer.write_bytes(data_writer.bytes)
            writer.write_boolean(">" == header.endian)
            writer.write_bytes(meta_writer.bytes)

        return writer.bytes

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
            writer.write_string_to_null(node.m_Type)
            writer.write_string_to_null(node.m_Name)
            writer.write_int(node.byte_size)
            if self.header.version == 2:
                writer.write_int(node.m_VariableCount)

            if self.header.version != 3:
                writer.write_int(node.m_Index)

            writer.write_int(node.m_TypeFlags)
            writer.write_int(node.m_Version)
            if self.header.version != 3:
                writer.write_int(node.m_MetaFlag)

            # calc children count
            children_count = 0
            for node2 in nodes[i + 1 :]:
                if node2.m_Level == node.m_Level:
                    break
                if node2.m_Level == node.m_Level - 1:
                    children_count += 1
            writer.write_int(children_count)

    def save_type_tree5(self, nodes: list, writer: EndianBinaryWriter, str_data=b""):
        # node count
        # stream buffer size
        # node data
        # string buffer

        string_buffer = EndianBinaryWriter()
        string_buffer.write(str_data)
        strings_values = [
            (node.m_TypeStrOffset, node.m_NameStrOffset) for node in nodes
        ]

        # number of nodes
        writer.write_int(len(nodes))
        # string buffer size
        writer.write_int(string_buffer.Length)

        # nodes
        for i, node in enumerate(nodes):
            # version
            writer.write_u_short(node.m_Version)
            # level
            writer.write_byte(node.m_Level)
            # is array
            writer.write_u_byte(node.m_TypeFlags)
            # type str offfset
            writer.write_u_int(strings_values[i][0])
            # name str offset
            writer.write_u_int(strings_values[i][1])
            # byte size
            writer.write_int(node.m_ByteSize)
            # index
            writer.write_int(node.m_Index)
            # meta flag
            writer.write_int(node.m_MetaFlag)
            # ref hash
            if self.header.version > 19:
                writer.write_u_long(node.m_RefTypeHash)

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
    return CommonString.get(offset, str(offset))


class ContainerHelper:
    """Helper class to allow multidict containers
    without breaking compatibility with old versions"""

    def __init__(self, container) -> None:
        self.container = container
        # support for getitem
        self.container_dict = {key: value.asset for key, value in container}
        self.path_dict = {value.asset.path_id: key for key, value in container}

    def items(self):
        return ((key, value.asset) for key, value in self.container)

    def keys(self):
        return list({key for key, value in self.container})

    def values(self):
        return list({value.asset for key, value in self.container})

    def __getitem__(self, key):
        return self.container_dict[key]

    def __setitem__(self, key, value):
        raise NotImplementedError("Assigning to container is not allowed!")

    def __delitem__(self, key):
        raise NotImplementedError("Deleting from the container is not allowed!")

    def __iter__(self):
        return iter(self.keys())

    def __len__(self):
        return len(self.container)

    def __getattr__(self, name: str):
        return self.container_dict[name]

    def __or__(self, other: "ContainerHelper"):
        return ContainerHelper(list(set(self.container + other.container)))

    def __str__(self):
        return f'{{{", ".join(f"{key}: {value}" for key, value in self.items())}}}'

    def __dict__(self):
        return self.container_dict
