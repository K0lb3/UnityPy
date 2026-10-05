from __future__ import annotations

import re
from struct import Struct
from threading import Lock
from typing import (
    TYPE_CHECKING,
    Dict,
    Iterator,
    List,
    Optional,
    Tuple,
    Union,
    cast,
)

from attrs import define, field

from ..helpers.Tpk import get_common_strings
from ..streams.EndianBinaryReader import EndianBinaryReader
from ..streams.EndianBinaryWriter import EndianBinaryWriter

try:
    from ..UnityPyBoost import TypeTreeNode as TypeTreeNodeC
except ImportError:

    @define(slots=True)
    class TypeTreeNodeC:
        m_Level: int
        m_Type: str
        m_Name: str
        m_ByteSize: int
        m_Version: int
        m_Children: List[TypeTreeNode] = field(factory=list)
        m_TypeFlags: Optional[int] = None
        m_VariableCount: Optional[int] = None
        m_Index: Optional[int] = None
        m_MetaFlag: Optional[int] = None
        m_RefTypeHash: Optional[int] = None
        _clean_name: str = field(init=False)

        def __attrs_post_init__(self):
            self._clean_name = clean_name(self.m_Name)

        def __repr__(self):
            return f"TypeTreeNode(m_Level={self.m_Level}, m_Type='{self.m_Type}', \
                m_Name='{self.m_Name}', m_MetaFlag={self.m_MetaFlag})"


TYPETREENODE_KEYS = [
    "m_Level",
    "m_Type",
    "m_Name",
    "m_ByteSize",
    "m_Version",
    "m_Children",
    "m_TypeFlags",
    "m_VariableCount",
    "m_Index",
    "m_MetaFlag",
    "m_RefTypeHash",
]

SYSTEM_GLOBAL_LOCK = Lock()
NAME_PEEK_NODE_CACHE: dict[Tuple[str, str, int], Union[Tuple[TypeTreeNode, str], None]] = {}


class TypeTreeNode(TypeTreeNodeC):
    def traverse(self, ignore_shared_children: bool = False) -> Iterator[TypeTreeNode]:
        stack: list[TypeTreeNode] = [self]
        while stack:
            node = stack.pop()
            yield node
            if ignore_shared_children and node.m_TypeFlags & 32 != 0:
                continue
            stack.extend(reversed(node.m_Children))

    @classmethod
    def parse(cls, reader: EndianBinaryReader, version: int) -> TypeTreeNode:
        # stack approach is way faster than recursion
        # using a fake root node to avoid special case for root node
        dummy_node = cls(-1, "", "", 0, 0, [])
        dummy_root = cls(-1, "", "", 0, 0, [dummy_node])

        stack: List[Tuple[TypeTreeNode, int]] = [(dummy_root, 1)]
        while stack:
            parent, count = stack[-1]
            if count == 1:
                stack.pop()
            else:
                stack[-1] = (parent, count - 1)

            node = cls(
                m_Level=parent.m_Level + 1,
                m_Type=reader.read_string_to_null(),
                m_Name=reader.read_string_to_null(),
                m_ByteSize=reader.read_int(),
                m_VariableCount=reader.read_int() if version == 2 else None,
                m_Index=reader.read_int() if version != 3 else None,
                m_TypeFlags=reader.read_int(),
                m_Version=reader.read_int(),
                m_MetaFlag=reader.read_int() if version != 3 else None,
            )
            parent.m_Children[-count] = node
            children_count = reader.read_int()
            if children_count > 0:
                node.m_Children = [dummy_node] * children_count
                stack.append((node, children_count))
        return dummy_root.m_Children[0]

    @classmethod
    def parse_blob(cls, reader: EndianBinaryReader, version: int) -> TypeTreeNode:
        node_count = reader.read_int()
        stringbuffer_size = reader.read_int()

        node_struct, keys = _get_blob_node_struct(reader.endian, version)
        struct_data = reader.read(node_struct.size * node_count)
        stringbuffer_reader = EndianBinaryReader(reader.read(stringbuffer_size), reader.endian)

        CommonString = get_common_strings()

        def read_string(reader: EndianBinaryReader, value: int) -> str:
            is_offset = (value & 0x80000000) == 0
            if is_offset:
                reader.Position = value
                return reader.read_string_to_null()

            offset = value & 0x7FFFFFFF
            return CommonString.get(offset, str(offset))

        fake_root: TypeTreeNode = cls(-1, "", "", 0, 0, [])
        stack: List[TypeTreeNode] = [fake_root]
        parent = fake_root
        prev = fake_root

        for raw_node in node_struct.iter_unpack(struct_data):
            node = cls(
                **dict(zip(keys[:3], raw_node[:3])),
                **dict(zip(keys[5:], raw_node[5:])),
                m_Type=read_string(stringbuffer_reader, raw_node[3]),
                m_Name=read_string(stringbuffer_reader, raw_node[4]),
            )

            if node.m_Level > prev.m_Level:
                stack.append(parent)
                parent = prev
            elif node.m_Level < prev.m_Level:
                while node.m_Level <= parent.m_Level:
                    parent = stack.pop()

            parent.m_Children.append(node)
            prev = node

        return fake_root.m_Children[0]

    @classmethod
    def from_list(cls, nodes: Union[List[Dict[str, Union[str, int]]], List[TypeTreeNode]]) -> TypeTreeNode:
        fake_root: TypeTreeNode = cls(-1, "", "", 0, 0, [])
        stack: List[TypeTreeNode] = [fake_root]
        parent = fake_root
        prev = fake_root

        # check if the nodes contain all required fields
        if isinstance(nodes[0], dict):
            if "m_Level" not in nodes[0] or "m_Type" not in nodes[0] or "m_Name" not in nodes[0]:
                raise ValueError("Nodes must contain at least m_Level, m_Type and m_Name")
            patch_dict = {}
            if "m_ByteSize" not in nodes[0]:
                patch_dict["m_ByteSize"] = 0
            if "m_Version" not in nodes[0]:
                patch_dict["m_Version"] = 0
            nodes = [cls(**node, **patch_dict) for node in nodes]

        if TYPE_CHECKING:
            nodes = cast(List[TypeTreeNode], nodes)

        for node in nodes:
            if node.m_Level > prev.m_Level:
                stack.append(parent)
                parent = prev
            elif node.m_Level < prev.m_Level:
                while node.m_Level <= parent.m_Level:
                    parent = stack.pop()

            parent.m_Children.append(node)
            prev = node

        return fake_root.m_Children[0]

    def get_name_peek_node(self) -> Union[Tuple[TypeTreeNode, str], None]:
        global SYSTEM_GLOBAL_LOCK
        with SYSTEM_GLOBAL_LOCK:
            key = (self.m_Name, self.m_Type, self.m_Version)
            if key in NAME_PEEK_NODE_CACHE:
                return NAME_PEEK_NODE_CACHE[key]

            result: Union[Tuple[TypeTreeNode, str], None] = None
            for i, child in enumerate(self.m_Children):
                if child.m_Name in ("m_Name", "name"):
                    peek_node = TypeTreeNode(
                        self.m_Level,
                        self.m_Type,
                        self.m_Name,
                        self.m_ByteSize,
                        self.m_Version,
                        self.m_Children[: i + 1],
                    )
                    result = peek_node, child.m_Name
                    break
            NAME_PEEK_NODE_CACHE[key] = result
            return result

    def dump(self, writer: EndianBinaryWriter, version: int):
        stack: list[TypeTreeNode] = [self]
        while stack:
            node = stack.pop()

            writer.write_string_to_null(self.m_Type)
            writer.write_string_to_null(self.m_Name)
            writer.write_int(self.m_ByteSize)
            if version == 2:
                assert self.m_VariableCount is not None
                writer.write_int(self.m_VariableCount)
            if version != 3:
                assert self.m_Index is not None
                writer.write_int(self.m_Index)
            writer.write_int(self.m_TypeFlags or 0)
            writer.write_int(self.m_Version)
            if version != 3:
                assert self.m_MetaFlag is not None
                writer.write_int(self.m_MetaFlag)

            writer.write_int(len(self.m_Children))

            stack.extend(reversed(node.m_Children))

    def dump_blob(self, writer: EndianBinaryWriter, version: int):
        node_writer = EndianBinaryWriter(endian=writer.endian)
        string_writer = EndianBinaryWriter()

        # string buffer setup
        CommonStringOffsetMap = {string: offset for offset, string in get_common_strings().items()}

        string_offsets: dict[str, int] = {}

        def write_string(string: str) -> int:
            offset = string_offsets.get(string)
            if offset is None:
                common_offset = CommonStringOffsetMap.get(string)
                if common_offset:
                    offset = common_offset | 0x80000000
                else:
                    offset = string_writer.Position
                    string_writer.write_string_to_null(string)
                string_offsets[string] = offset
            return offset

        # node buffer setup
        node_struct, keys = _get_blob_node_struct(writer.endian, version)

        def write_node(node: TypeTreeNode):
            node_writer.write(
                node_struct.pack(
                    *[getattr(node, key) for key in keys[:3]],
                    write_string(node.m_Type),
                    write_string(node.m_Name),
                    *[getattr(node, key) for key in keys[5:]],
                )
            )

        # write nodes
        node_count = len([write_node(node) for node in self.traverse(ignore_shared_children=True)])

        writer.write_int(node_count)
        writer.write_int(string_writer.Position)
        writer.write(node_writer.bytes)
        writer.write(string_writer.bytes)

    def dump_structure(self, indent: str = "  ") -> str:
        # dump structure similar to https://github.com/AssetRipper/TypeTreeDumps/blob/main/StructsDump
        sb = [
            f"{indent}{self.m_Type} {self.m_Name} // ByteSize{{{self.m_ByteSize:X}}}, Index{{{self.m_Index}}}, \
                Version{{{self.m_Version}}}, TypeFlags{{{self.m_TypeFlags}}}, MetaFlag{{{self.m_MetaFlag}}}"
        ]
        for child in self.m_Children:
            sb.append(child.dump_structure(indent + "  "))
        return "\n".join(sb)

    def to_dict(self) -> dict:
        return {
            key: value for key, value in ((key, getattr(self, key)) for key in TYPETREENODE_KEYS) if value is not None
        }

    def to_dict_list(self) -> List[dict]:
        return [
            self.to_dict(),
            *(item for child in self.m_Children for item in child.to_dict_list()),
        ]

    def __eq__(self, other: TypeTreeNode) -> bool:  # type: ignore
        return self.to_dict() == other.to_dict() and self.m_Children == other.m_Children


def _get_blob_node_struct(endian: str, version: int) -> tuple[Struct, list[str]]:
    struct_type = f"{endian}hBBIIiii"
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
    if version >= 19:
        struct_type += "Q"
        keys.append("m_RefTypeHash")

    return Struct(struct_type), keys


CLEAN_NAME_REMOVE_RE = re.compile(r"[\?\*]")
CLEAN_NAME_REPLACE_RE = re.compile(r"[ \.:\-\[\]]")


def clean_name(name: str) -> str:
    # keep in sync with TypeTreeHelper.cpp
    if len(name) == 0:
        return name
    if name.startswith("(int&)"):
        name = name[6:]
    name = CLEAN_NAME_REMOVE_RE.sub("", name)
    name = CLEAN_NAME_REPLACE_RE.sub("_", name)
    if name in ["pass", "from"]:
        name += "_"
    if name[0].isdigit():
        name = f"x{name}"
    return name


@define(slots=True, frozen=True)
class TypeTreeNodeInfo:
    version: int
    node: TypeTreeNode
    ref_hashes: List[bytes]

    @classmethod
    def from_reader(cls, reader: EndianBinaryReader) -> "TypeTreeNodeInfo":
        magic = reader.read_bytes(4)
        if magic != b"mhtt":
            raise ValueError("Invalid type tree blob magic")
        version = reader.read_int()
        node = TypeTreeNode.parse_blob(reader, version)
        ref_hash_count = reader.read_u_int()
        ref_hashes = [reader.read_bytes(16) for _ in range(ref_hash_count)]
        return cls(version, node, ref_hashes)

    def to_bytes(self, endian: str) -> bytes:
        info_writer = EndianBinaryWriter(endian=endian)
        info_writer.write_bytes(b"mhtt")
        info_writer.write_int(self.version)
        self.node.dump_blob(info_writer, self.version)
        info_writer.write_u_int(len(self.ref_hashes))
        for ref_hash in self.ref_hashes:
            info_writer.write_bytes(ref_hash)
        return info_writer.bytes


@define(slots=True, frozen=True)
class TypeTreeNodeInfoHandler:
    hash: bytes
    info: Optional[TypeTreeNodeInfo]

    @classmethod
    def from_reader(cls, reader: EndianBinaryReader) -> "TypeTreeNodeInfoHandler":
        hash = reader.read_bytes(16)
        serialized_size = reader.read_u_int()
        if serialized_size >= 8:
            info = TypeTreeNodeInfo.from_reader(reader)
            return cls(hash, info)
        else:
            return cls(hash, None)

    def to_writer(self, writer: EndianBinaryWriter):
        start = writer.tell()
        writer.write(self.hash)
        if self.info is None:
            writer.write_u_int(0)
        else:
            info_bytes = self.info.to_bytes(writer.endian)
            writer.write_u_int(len(info_bytes))
            writer.write_bytes(info_bytes)
        return writer.tell() - start


__all__ = (
    "TypeTreeNode",
    "TypeTreeNodeInfoHandler",
    "get_common_strings",
    "clean_name",
)
