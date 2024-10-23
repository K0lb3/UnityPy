from __future__ import annotations

import re
from struct import Struct
from typing import TYPE_CHECKING, Dict, Iterator, List, Optional, Tuple

from attrs import define, field

from ..streams.EndianBinaryReader import EndianBinaryReader
from ..streams.EndianBinaryWriter import EndianBinaryWriter

if TYPE_CHECKING:
    from .Tpk import UnityVersion

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


class TypeTreeNode(TypeTreeNodeC):
    def traverse(self) -> Iterator[TypeTreeNode]:
        stack: list[TypeTreeNode] = [self]
        while stack:
            node = stack.pop()
            yield node
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
        stringbuffer_reader = EndianBinaryReader(
            reader.read(stringbuffer_size), reader.endian
        )

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
    def from_list(cls, nodes: List[dict]) -> TypeTreeNode:
        fake_root: TypeTreeNode = cls(-1, "", "", 0, 0, [])
        stack: List[TypeTreeNode] = [fake_root]
        parent = fake_root
        prev = fake_root

        for node in nodes:
            if isinstance(node, dict):
                node = cls(**node)

            if node.m_Level > prev.m_Level:
                stack.append(parent)
                parent = prev
            elif node.m_Level < prev.m_Level:
                while node.m_Level <= parent.m_Level:
                    parent = stack.pop()

            parent.m_Children.append(node)
            prev = node

        return fake_root.m_Children[0]

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
            writer.write_int(self.m_TypeFlags)
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
        CommonStringOffsetMap = {
            string: offset for offset, string in get_common_strings().items()
        }

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
        node_count = len([write_node(node) for node in self.traverse()])

        # write blob
        writer.write_int(node_count)
        writer.write_int(string_writer.Position)
        writer.write(node_writer.bytes)
        writer.write(string_writer.bytes)

    def dump_structure(self, indent: str = "  ") -> str:
        # dump structure similar to https://github.com/AssetRipper/TypeTreeDumps/blob/main/StructsDump
        sb = [
            f"{indent}{self.m_Type} {self.m_Name} // ByteSize{{{self.m_ByteSize:X}}}, Index{{{self.m_Index}}}, Version{{{self.m_Version}}}, TypeFlags{{{self.m_TypeFlags}}}, MetaFlag{{{self.m_MetaFlag}}}"
        ]
        for child in self.m_Children:
            sb.append(child.dump_structure(indent + "  "))
        return "\n".join(sb)

    def to_dict(self) -> dict:
        return {
            key: value
            for key, value in ((key, getattr(self, key)) for key in TYPETREENODE_KEYS)
            if value is not None
        }

    def to_dict_list(self) -> List[dict]:
        return [
            self.to_dict(),
            *(item for child in self.m_Children for item in child.to_dict_list()),
        ]

    def __eq__(self, other: TypeTreeNode) -> bool:
        return self.to_dict() == other.to_dict() and self.m_Children == other.m_Children


COMMONSTRING_CACHE: Dict[Optional[UnityVersion], Dict[int, str]] = {}


def get_common_strings(version: Optional[UnityVersion] = None) -> Dict[int, str]:
    if version in COMMONSTRING_CACHE:
        return COMMONSTRING_CACHE[version]

    from .Tpk import TPKTYPETREE

    tree = TPKTYPETREE
    common_string = tree.CommonString
    strings = common_string.GetStrings(tree.StringBuffer)
    if version:
        count = common_string.GetCount(version)
        strings = strings[:count]

    ret: Dict[int, str] = {}
    offset = 0
    for string in strings:
        ret[offset] = string
        offset += len(string) + 1

    COMMONSTRING_CACHE[version] = ret
    return ret


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


def clean_name(name: str) -> str:
    # keep in sync with TypeTreeHelper.cpp
    if len(name) == 0:
        return name
    if name.startswith("(int&)"):
        name = name[6:]
    if name.endswith("?"):
        name = name[:-1]
    name = re.sub(r"[ \.:\-\[\]]", "_", name)
    if name in ["pass", "from"]:
        name += "_"
    if name[0].isdigit():
        name = f"x{name}"
    return name


__all__ = (
    "TypeTreeNode",
    "get_common_strings",
    "clean_name",
)
