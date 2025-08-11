from __future__ import annotations

from ntpath import basename
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from attrs import define

from .. import config
from ..enums import BuildTarget, ClassIDType, CommonString
from ..helpers.ContainerHelper import ContainerHelper
from ..helpers.TypeTreeHelper import TypeTreeNode
from ..helpers.UnityVersion import UnityVersion
from ..streams import EndianBinaryWriter
from . import BundleFile, File, ObjectReader

if TYPE_CHECKING:
    from ..classes import AssetBundle, Object
    from ..files import ObjectReader
    from ..streams.EndianBinaryReader import EndianBinaryReader


@define(slots=True)
class SerializedFileHeader:
    metadata_size: int
    file_size: int
    version: int
    data_offset: int
    endian: str
    reserved: bytes

    def __init__(self, reader: EndianBinaryReader):
        (
            self.metadata_size,
            self.file_size,
            self.version,
            self.data_offset,
        ) = reader.read_u_int_array(4)


@define(slots=True)
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


@define(slots=True)
class FileIdentifier:  # external
    path: str
    temp_empty: Optional[str] = None
    guid: Optional[bytes] = None
    type: Optional[int] = None
    # enum { kNonAssetType = 0, kDeprecatedCachedAssetType = 1, kSerializedAssetType = 2, kMetaAssetType = 3 };

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
            assert self.temp_empty is not None
            writer.write_string_to_null(self.temp_empty)
        if header.version >= 5:
            assert self.guid is not None and self.type is not None
            writer.write_bytes(self.guid)
            writer.write_int(self.type)
        writer.write_string_to_null(self.path)


@define(slots=True, init=False)
class SerializedType:
    class_id: int
    is_stripped_type: Optional[bool] = None
    script_type_index: int = -1
    script_id: Optional[bytes] = None  # Hash128
    old_type_hash: Optional[bytes] = None  # Hash128
    node: Optional[TypeTreeNode] = None
    # ref type
    m_ClassName: Optional[str] = None
    m_NameSpace: Optional[str] = None
    m_AssemblyName: Optional[str] = None
    # 21+
    type_dependencies: Optional[Tuple[int, ...]] = None

    def __init__(
        self,
        reader: EndianBinaryReader,
        serialized_file: SerializedFile,
        is_ref_type: bool,
    ):
        version = serialized_file.header.version
        self.class_id = reader.read_int()
        self.__attrs_init__(self.class_id)

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
                self.node = TypeTreeNode.parse_blob(reader, version)
            else:
                self.node = TypeTreeNode.parse(reader, version)

            if version >= 21:
                if is_ref_type:
                    self.m_ClassName = reader.read_string_to_null()
                    self.m_NameSpace = reader.read_string_to_null()
                    self.m_AssemblyName = reader.read_string_to_null()
                else:
                    self.type_dependencies = reader.read_int_array()

    def write(
        self,
        serialized_file: SerializedFile,
        writer: EndianBinaryWriter,
        is_ref_type: bool,
    ):
        version = serialized_file.header.version
        writer.write_int(self.class_id)

        if version >= 16:
            assert self.is_stripped_type is not None
            writer.write_boolean(self.is_stripped_type)

        if version >= 17:
            assert self.script_type_index is not None
            writer.write_short(self.script_type_index)

        if version >= 13:
            if (
                (is_ref_type and self.script_type_index >= 0)
                or (version < 16 and self.class_id < 0)
                or (version >= 16 and self.class_id == 114)
            ):
                assert self.script_id is not None
                writer.write_bytes(self.script_id)  # Hash128
            assert self.old_type_hash is not None
            writer.write_bytes(self.old_type_hash)  # Hash128

        if serialized_file._enable_type_tree:
            assert self.node is not None
            if version >= 12 or version == 10:
                self.node.dump_blob(writer, version)
            else:
                serialized_file.dump(writer, version)

            if version >= 21:
                if is_ref_type:
                    assert (
                        self.m_ClassName is not None
                        and self.m_NameSpace is not None
                        and self.m_AssemblyName is not None
                    )
                    writer.write_string_to_null(self.m_ClassName)
                    writer.write_string_to_null(self.m_NameSpace)
                    writer.write_string_to_null(self.m_AssemblyName)
                else:
                    assert self.type_dependencies is not None
                    writer.write_int_array(self.type_dependencies, True)

    @property
    def nodes(self) -> Optional[TypeTreeNode]:
        # for compatibility with old versions
        return self.node


class SerializedFile(File.File):
    reader: EndianBinaryReader
    version: UnityVersion
    unity_version: str
    target_platform: BuildTarget
    _enable_type_tree: bool
    types: List[SerializedType]
    script_types: List[LocalSerializedObjectIdentifier]
    externals: List[FileIdentifier]
    ref_types: Optional[List[SerializedType]]
    objects: Dict[int, ObjectReader]
    unknown: int
    header: SerializedFileHeader
    _m_target_platform: int
    big_id_enabled: int
    userInformation: Optional[str]
    assetbundle: Optional[AssetBundle]
    _cache: Dict[str, Object]

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
            self.script_types = [LocalSerializedObjectIdentifier(header, reader) for _ in range(script_count)]

        # Read Externals
        externals_count = reader.read_int()
        self.externals = [FileIdentifier(header, reader) for _ in range(externals_count)]

        if header.version >= 20:
            ref_type_count = reader.read_int()
            self.ref_types = [SerializedType(reader, self, True) for _ in range(ref_type_count)]

        if config.SERIALIZED_FILE_PARSE_TYPETREE is False:
            self._enable_type_tree = False

        if header.version >= 5:
            self.userInformation = reader.read_string_to_null()

        # read the asset_bundles to get the containers
        for obj in self.objects.values():
            if obj.type == ClassIDType.AssetBundle:
                self.assetbundle = obj.read()
                self._container = ContainerHelper(self.assetbundle)
                break
        else:
            self.assetbundle = None
            self._container = ContainerHelper([])

    @property
    def container(self):
        return self._container

    def load_dependencies(self, possible_dependencies: Optional[list] = None):
        """Load all external dependencies.

        Parameters
        ----------
        possible_dependencies : list
            List of possible dependencies for cases
            where the target file is not listed as external.
        """
        for file_id in self.externals:
            self.environment.load_file(file_id.path, True)

        if possible_dependencies is None:
            return

        for dependency in possible_dependencies:
            try:
                self.environment.load_file(dependency, True)
            except FileNotFoundError:
                pass

    def set_version(self, string_version: str):
        self.unity_version = string_version
        if not string_version or string_version == "0.0.0":
            # weird case, but apparently can happen?
            # check "cant read Texture2D by 2020.3.13 f1 AssetBundle #77" for details
            if isinstance(self.parent, BundleFile.BundleFile):
                string_version = self.parent.version_engine
            if not string_version or string_version == "0.0.0":
                string_version = config.get_fallback_version()
        self.version = UnityVersion.from_str(string_version)

    def get_writeable_cab(self, name: str = "CAB-UnityPy_Mod.resS"):
        """
        Creates a new cab file in the bundle that contains the given data.
        This is usefull for asset types that use resource files.
        """
        if not isinstance(self.parent, (File.BundleFile.BundleFile, File.WebFile.WebFile)):
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

    def save(self, packer: Optional[str] = None) -> bytes:
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
            assert self.ref_types is not None
            meta_writer.write_int(len(self.ref_types))
            for ref_type in self.ref_types:
                ref_type.write(self, meta_writer, True)

        if header.version >= 5:
            assert self.userInformation is not None
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


def read_string(string_buffer_reader: EndianBinaryReader, value: int) -> str:
    is_offset = (value & 0x80000000) == 0
    if is_offset:
        string_buffer_reader.Position = value
        return string_buffer_reader.read_string_to_null()

    offset = value & 0x7FFFFFFF
    return CommonString.get(offset, str(offset))
