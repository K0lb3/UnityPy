"""Regression tests for #388.

MonoBehaviour nodes produced by TypeTreeGenerator carry a fixed header whose
align flags sit on m_GameObject, m_Script and m_Name instead of only after
m_Enabled. Reading with that header shifts m_Script by 3 bytes, and saving
writes the wrong m_Script back. generate_monobehaviour_node must replace the
generated fields up to and including m_Name with the class database header.
"""

import struct
from types import SimpleNamespace

from UnityPy.enums import ClassIDType
from UnityPy.files.ObjectReader import ObjectReader
from UnityPy.helpers.Tpk import get_typetree_node
from UnityPy.helpers.TypeTreeHelper import read_typetree, write_typetree
from UnityPy.helpers.TypeTreeNode import TypeTreeNode
from UnityPy.helpers.UnityVersion import UnityVersion
from UnityPy.streams import EndianBinaryReader, EndianBinaryWriter

ALIGN = 0x4000
VERSION = "2022.3.0f1"
SCRIPT_PATH_ID = 0x1122334455667788


def clone_node(node: TypeTreeNode) -> TypeTreeNode:
    return TypeTreeNode(
        m_Level=node.m_Level,
        m_Type=node.m_Type,
        m_Name=node.m_Name,
        m_ByteSize=node.m_ByteSize,
        m_Version=node.m_Version,
        m_Children=[clone_node(child) for child in node.m_Children],
        m_TypeFlags=node.m_TypeFlags,
        m_MetaFlag=node.m_MetaFlag,
        m_Index=node.m_Index,
    )


def class_db_node() -> TypeTreeNode:
    return get_typetree_node(ClassIDType.MonoBehaviour, UnityVersion.from_str(VERSION))


def script_field(typ: str, name: str, meta_flag: int = 0) -> TypeTreeNode:
    return TypeTreeNode(
        m_Level=1, m_Type=typ, m_Name=name, m_ByteSize=0, m_Version=0, m_Children=[], m_MetaFlag=meta_flag
    )


def make_generated_node() -> TypeTreeNode:
    """Fabricates a TypeTreeGenerator node: class-db fields with the
    generator's align flags, plus the script's own fields."""
    node = clone_node(class_db_node())
    for child in node.m_Children:
        if child.m_Name in ("m_GameObject", "m_Script", "m_Name"):
            child.m_MetaFlag = (child.m_MetaFlag or 0) | ALIGN
        elif child.m_Name == "m_Enabled":
            child.m_MetaFlag = (child.m_MetaFlag or 0) & ~ALIGN
    node.m_Children = [
        *node.m_Children,
        script_field("int", "count"),
        script_field("bool", "flag", ALIGN),
        script_field("int", "after"),
    ]
    return node


def aligned_string(value: str) -> bytes:
    data = value.encode()
    return struct.pack("<i", len(data)) + data + bytes(-len(data) % 4)


# a Sample MonoBehaviour as Unity serializes it:
# m_Enabled is followed by 3 bytes of padding
SAMPLE_DATA = (
    struct.pack("<iq", 0, 1)  # m_GameObject
    + struct.pack("<B3x", 1)  # m_Enabled
    + struct.pack("<iq", 0, SCRIPT_PATH_ID)  # m_Script
    + aligned_string("sample")  # m_Name
    + struct.pack("<i", 5)  # count
    + struct.pack("<B3x", 1)  # flag
    + struct.pack("<i", 9)  # after
)


class FakeGenerator:
    def __init__(self, node: TypeTreeNode):
        self.node = node

    def get_nodes_up(self, assembly_name: str, fullname: str) -> TypeTreeNode:
        assert assembly_name == "Game"
        assert fullname == "Sample"
        return self.node


def make_reader(monkeypatch, generated_node: TypeTreeNode) -> ObjectReader:
    script = SimpleNamespace(m_Namespace="", m_ClassName="Sample", m_AssemblyName="Game")
    monobehaviour = SimpleNamespace(m_Script=SimpleNamespace(deref_parse_as_object=lambda: script))
    monkeypatch.setattr(
        ObjectReader,
        "parse_monobehaviour_head",
        lambda self, mb_node=None: monobehaviour,
    )
    assets_file = SimpleNamespace(environment=SimpleNamespace(typetree_generator=FakeGenerator(generated_node)))
    return ObjectReader(
        assets_file=assets_file,
        reader=EndianBinaryReader(b"", "<"),
        path_id=1,
        type_id=0,
        serialized_type=None,
        class_id=int(ClassIDType.MonoBehaviour),
        type=ClassIDType.MonoBehaviour,
        byte_start=0,
        byte_size=len(SAMPLE_DATA),
        is_destroyed=None,
        is_stripped=None,
    )


def header_flags(node: TypeTreeNode):
    return [(child.m_Name, bool((child.m_MetaFlag or 0) & ALIGN)) for child in node.m_Children[:4]]


def test_generated_node_header_is_replaced(monkeypatch):
    reader = make_reader(monkeypatch, make_generated_node())
    node = reader.generate_monobehaviour_node(class_db_node())

    assert header_flags(node) == [
        ("m_GameObject", False),
        ("m_Enabled", True),
        ("m_Script", False),
        ("m_Name", False),
    ]
    # the script's own fields are kept, untouched
    assert [child.m_Name for child in node.m_Children[4:]] == ["count", "flag", "after"]


def test_generated_node_reads_and_saves_m_script(monkeypatch):
    reader = make_reader(monkeypatch, make_generated_node())
    node = reader.generate_monobehaviour_node(class_db_node())

    value = read_typetree(node, EndianBinaryReader(SAMPLE_DATA, "<"), as_dict=True, check_read=False)
    assert value["m_Script"]["m_PathID"] == SCRIPT_PATH_ID
    assert (value["count"], value["flag"], value["after"]) == (5, True, 9)

    writer = EndianBinaryWriter(b"", "<")
    write_typetree(value, node, writer)
    assert writer.bytes == SAMPLE_DATA
