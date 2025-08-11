from __future__ import annotations

from enum import IntEnum, IntFlag
from importlib.resources import open_binary
from io import BytesIO
from struct import Struct
from typing import Any, Dict, List, Optional, Tuple, TypeVar

from .TypeTreeHelper import TypeTreeNode
from .UnityVersion import UnityVersion

T = TypeVar("T")

TPKTYPETREE: TpkTypeTreeBlob = None  # pyright: ignore[reportAssignmentType]
CLASSES_CACHE: Dict[Tuple[int, UnityVersion], TypeTreeNode] = {}
NODES_CACHE: Dict[TpkUnityClass, TypeTreeNode] = {}


def init():
    with open_binary("UnityPy.resources", "uncompressed.tpk") as f:
        data = f.read()

    global TPKTYPETREE
    with BytesIO(data) as stream:
        blob = TpkFile(stream).GetDataBlob()
        assert isinstance(blob, TpkTypeTreeBlob)
        TPKTYPETREE = blob


def get_typetree_node(class_id: int, version: UnityVersion):
    global CLASSES_CACHE
    key = (class_id, version)
    cached = CLASSES_CACHE.get(key)
    if cached:
        return cached

    class_info = TPKTYPETREE.ClassInformation[class_id].getVersionedClass(version)
    if class_info is None:
        raise ValueError("Could not find class info for class id {}".format(class_id))

    node = generate_node(class_info)
    CLASSES_CACHE[key] = node
    return node


def generate_node(class_info: TpkUnityClass) -> TypeTreeNode:
    global NODES_CACHE
    cached = NODES_CACHE.get(class_info)
    if cached:
        return cached

    assert class_info.ReleaseRootNode is not None, "Class {} has no ReleaseRootNode".format(class_info)

    nodes = []
    NODES = TPKTYPETREE.NodeBuffer.Nodes
    stack = [(class_info.ReleaseRootNode, 0)]
    index = 0
    while stack:
        node_id, level = stack.pop(0)
        node: TpkUnityNode = NODES[node_id]
        nodes.append(
            TypeTreeNode(
                m_ByteSize=node.ByteSize,
                m_Index=index,
                m_Version=node.Version,
                m_MetaFlag=node.MetaFlag,
                m_Level=level,
                m_Type=TPKTYPETREE.StringBuffer.Strings[node.TypeName],
                m_Name=TPKTYPETREE.StringBuffer.Strings[node.Name],
            )
        )
        stack = [(node_id, level + 1) for node_id in node.SubNodes] + stack
        index += 1
    result = TypeTreeNode.from_list(nodes)
    NODES_CACHE[class_info] = result
    return result


######################################################################################
#
#   Enums
#
######################################################################################


class TpkCompressionType(IntEnum):
    NONE = 0
    Lz4 = 1
    Lzma = 2
    Brotli = 3


class TpkDataType(IntEnum):
    TypeTreeInformation = 0
    Collection = 1
    FileSystem = 2
    Json = 3
    ReferenceAssemblies = 4
    EngineAssets = 5

    def ToBlob(self, stream):
        if self.value == TpkDataType.TypeTreeInformation:
            return TpkTypeTreeBlob(stream)
        elif self.value == TpkDataType.Collection:
            return TpkCollectionBlob(stream)
        elif self.value == TpkDataType.FileSystem:
            return TpkFileSystemBlob(stream)
        elif self.value == TpkDataType.Json:
            return TpkJsonBlob(stream)
        else:
            raise Exception("Unimplemented TpkDataType -> Blob conversion")


class TpkUnityClassFlags(IntFlag):
    NONE = 0
    IsAbstract = 1
    IsSealed = 2
    IsEditorOnly = 4
    IsReleaseOnly = 8
    IsStripped = 16
    Reserved = 32
    HasEditorRootNode = 64
    HasReleaseRootNode = 128


######################################################################################
#
#   Main Class
#
######################################################################################


class TpkFile:
    Struct = Struct("<IbbbbIII")
    TpkMagicBytes: int = 0x2A4B5054  # b"TPK*"
    TpkVersionNumber: int = 1
    CompressionType: TpkCompressionType
    DataType: TpkDataType
    CompressedSize: int
    UncompressedSize: int
    CompressedBytes: bytes

    def __init__(self, stream: BytesIO):
        (
            magic,
            versionNumber,
            compressionType,
            dataType,
            _,
            _,
            self.CompressedSize,
            self.UncompressedSize,
        ) = TpkFile.Struct.unpack(stream.read(TpkFile.Struct.size))
        if magic != TpkFile.TpkMagicBytes:
            raise Exception("Invalid TPK magic bytes")
        if versionNumber != TpkFile.TpkVersionNumber:
            raise Exception("Invalid TPK version number")
        self.CompressionType = TpkCompressionType(compressionType)
        self.DataType = TpkDataType(dataType)
        self.CompressedBytes = stream.read(self.CompressedSize)
        if len(self.CompressedBytes) != self.CompressedSize:
            raise Exception("Invalid compressed size")

    def GetDataBlob(self) -> TpkDataBlob:
        decompressed: bytes
        if self.CompressionType == TpkCompressionType.NONE:
            decompressed = self.CompressedBytes

        elif self.CompressionType == TpkCompressionType.Lz4:
            import lz4.block

            decompressed = lz4.block.decompress(self.CompressedBytes, self.UncompressedSize)

        elif self.CompressionType == TpkCompressionType.Lzma:
            import lzma

            decompressed = lzma.decompress(self.CompressedBytes)

        elif self.CompressionType == TpkCompressionType.Brotli:
            import brotli

            decompressed = brotli.decompress(self.CompressedBytes)

        else:
            raise Exception("Invalid compression type")

        return self.DataType.ToBlob(BytesIO(decompressed))


######################################################################################
#
#   Blobs
#
######################################################################################


class TpkDataBlob:
    __slots__ = ("DataType",)
    DataType: TpkDataType

    def __init__(self, stream: BytesIO) -> None:
        raise NotImplementedError("TpkDataBlob is an abstract class")


class TpkTypeTreeBlob(TpkDataBlob):
    __slots__ = (
        "CreationTime",
        "Versions",
        "ClassInformation",
        "CommonString",
        "NodeBuffer",
        "StringBuffer",
    )
    CreationTime: int
    Versions: List[UnityVersion]
    ClassInformation: Dict[int, TpkClassInformation]  # List[TpkClassInformation]
    CommonString: TpkCommonString
    NodeBuffer: TpkUnityNodeBuffer
    StringBuffer: TpkStringBuffer
    DataType: TpkDataType = TpkDataType.TypeTreeInformation

    def __init__(self, stream: BytesIO) -> None:
        (self.CreationTime,) = INT64.unpack(stream.read(INT64.size))
        (versionCount,) = INT32.unpack(stream.read(INT32.size))
        self.Versions = [read_version(stream) for _ in range(versionCount)]
        (classCount,) = INT32.unpack(stream.read(INT32.size))
        self.ClassInformation = {x.ID: x for x in (TpkClassInformation(stream) for _ in range(classCount))}
        self.CommonString = TpkCommonString(stream)
        self.NodeBuffer = TpkUnityNodeBuffer(stream)
        self.StringBuffer = TpkStringBuffer(stream)


class TpkCollectionBlob(TpkDataBlob):
    __slots__ = "Blobs"
    Blobs: List[Tuple[str, TpkDataBlob]]

    def __init__(self, stream: BytesIO) -> None:
        (count,) = INT32.unpack(stream.read(INT32.size))
        self.Blobs = [
            # relativePath, data
            (
                read_string(stream),
                TpkDataType(BYTE.unpack(stream.read(1))[0]).ToBlob(stream),
            )
            for _ in range(count)
        ]


class TpkFileSystemBlob(TpkDataBlob):
    __slots__ = ("Files",)
    # TODO: check if dict might be better
    Files: List[Tuple[str, bytes]]

    def __init__(self, stream: BytesIO) -> None:
        (count,) = INT32.unpack(stream.read(INT32.size))
        self.Files = [
            # relativePath, data
            (read_string(stream), read_data(stream))
            for _ in range(count)
        ]


class TpkJsonBlob(TpkDataBlob):
    __slots__ = "Text"
    Text: str
    DataType = TpkDataType.Json

    def __init__(self, stream: BytesIO) -> None:
        self.Text = read_string(stream)


######################################################################################
#
#   Unity
#
######################################################################################


class TpkUnityClass:
    __slots__ = ("Name", "Base", "Flags", "EditorRootNode", "ReleaseRootNode")
    Struct = Struct("<HHb")
    Name: int
    Base: int
    Flags: TpkUnityClassFlags
    EditorRootNode: Optional[int]
    ReleaseRootNode: Optional[int]

    def __init__(self, stream: BytesIO) -> None:
        self.Name, self.Base, Flags = TpkUnityClass.Struct.unpack(stream.read(TpkUnityClass.Struct.size))
        self.Flags = TpkUnityClassFlags(Flags)
        self.EditorRootNode = self.ReleaseRootNode = None
        if self.Flags & TpkUnityClassFlags.HasEditorRootNode:
            (self.EditorRootNode,) = UINT16.unpack(stream.read(UINT16.size))
        if self.Flags & TpkUnityClassFlags.HasReleaseRootNode:
            (self.ReleaseRootNode,) = UINT16.unpack(stream.read(UINT16.size))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "Name": self.Name,
            "Base": self.Base,
            "Flags": self.Flags,
            "EditorRootNode": self.EditorRootNode,
            "ReleaseRootNode": self.ReleaseRootNode,
        }

    def __eq__(self, other: TpkUnityClass) -> bool:
        return self.to_dict() == other.to_dict()

    def __hash__(self) -> int:
        return hash(
            (
                self.Name,
                self.Base,
                self.Flags,
                self.EditorRootNode,
                self.ReleaseRootNode,
            )
        )


class TpkClassInformation:
    __slots__ = ("ID", "Classes")
    ID: int
    # TODO - might want to use dict
    Classes: List[Tuple[UnityVersion, Optional[TpkUnityClass]]]

    def __init__(self, stream: BytesIO) -> None:
        (self.ID,) = INT32.unpack(stream.read(INT32.size))
        (count,) = INT32.unpack(stream.read(INT32.size))
        self.Classes = [
            (
                read_version(stream),
                TpkUnityClass(stream) if stream.read(1)[0] else None,
            )
            for _ in range(count)
        ]

    def getVersionedClass(self, version: UnityVersion) -> Optional[TpkUnityClass]:
        return get_item_for_version(version, self.Classes)


class TpkUnityNodeBuffer:
    Nodes: List[TpkUnityNode]

    def __init__(self, stream: BytesIO) -> None:
        (count,) = INT32.unpack(stream.read(INT32.size))
        self.Nodes = [TpkUnityNode(stream) for _ in range(count)]

    def __getitem__(self, index: int) -> TpkUnityNode:
        return self.Nodes[index]


class TpkUnityNode:
    __slots__ = (
        "TypeName",
        "Name",
        "ByteSize",
        "Version",
        "TypeFlags",
        "MetaFlag",
        "SubNodes",
    )
    Struct = Struct("<HHihbIH")
    TypeName: int
    Name: int
    ByteSize: int
    Version: int
    TypeFlags: int
    MetaFlag: int
    SubNodes: List[int]

    def __init__(self, stream: BytesIO) -> None:
        (
            self.TypeName,
            self.Name,
            self.ByteSize,
            self.Version,
            self.TypeFlags,
            self.MetaFlag,
            count,
        ) = TpkUnityNode.Struct.unpack(stream.read(TpkUnityNode.Struct.size))

        SubNodeStruct = Struct(f"<{count}H")
        self.SubNodes = list(SubNodeStruct.unpack(stream.read(SubNodeStruct.size)))

    def __eq__(self, other: TpkUnityNode) -> bool:
        return self.__dict__ == other.__dict__

    def __hash__(self) -> int:
        # TODO
        return hash(self.__dict__)


######################################################################################
#
#   Strings
#
######################################################################################


class TpkStringBuffer:
    __slots__ = "Strings"
    Strings: List[str]

    def __init__(self, stream: BytesIO) -> None:
        self.Strings = [read_string(stream) for _ in range(INT32.unpack(stream.read(INT32.size))[0])]

    @property
    def Count(self) -> int:
        return len(self.Strings)


class TpkCommonString:
    __slots__ = ("VersionInformation", "StringBufferIndices")
    VersionInformation: List[Tuple[UnityVersion, int]]
    StringBufferIndices: Tuple[int, ...]

    def __init__(self, stream: BytesIO) -> None:
        (versionCount,) = INT32.unpack(stream.read(INT32.size))
        self.VersionInformation = [(read_version(stream), stream.read(1)[0]) for _ in range(versionCount)]
        (indicesCount,) = INT32.unpack(stream.read(INT32.size))
        indicesStruct = Struct(f"<{indicesCount}H")
        self.StringBufferIndices = indicesStruct.unpack(stream.read(indicesStruct.size))

    def GetStrings(self, buffer: TpkStringBuffer) -> List[str]:
        return [buffer.Strings[i] for i in self.StringBufferIndices]

    def GetCount(self, exactVersion: UnityVersion) -> int:
        return get_item_for_version(exactVersion, self.VersionInformation)


######################################################################################
#
# helper functions
#
######################################################################################

BYTE = Struct("b")
UINT16 = Struct("<H")
INT32 = Struct("<i")
INT64 = Struct("<q")
UINT64 = Struct("<Q")


def read_string(stream: BytesIO) -> str:
    # varint
    shift = 0
    length = 0
    while True:
        (i,) = stream.read(1)
        length |= (i & 0x7F) << shift
        shift += 7
        if not (i & 0x80):
            break
    # string
    return stream.read(length).decode("utf-8")


def read_data(stream: BytesIO) -> bytes:
    return stream.read(INT32.unpack(stream.read(INT32.size))[0])


def read_version(stream: BytesIO) -> UnityVersion:
    return UnityVersion(UINT64.unpack(stream.read(UINT64.size))[0])


def get_item_for_version(exactVersion: UnityVersion, items: List[Tuple[UnityVersion, T]]) -> T:
    ret = None
    for version, item in items:
        if exactVersion >= version:
            ret = item
        else:
            break
    if ret:
        return ret
    raise ValueError("Could not find exact version")


init()
