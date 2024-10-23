import gc
import math
import os
import random
from typing import List, Tuple, TypeVar, Union, Type

import psutil

from UnityPy.classes.generated import GameObject
from UnityPy.helpers.Tpk import get_typetree_node
from UnityPy.helpers.TypeTreeHelper import read_typetree, write_typetree
from UnityPy.helpers.TypeTreeNode import TypeTreeNode
from UnityPy.streams import EndianBinaryReader, EndianBinaryWriter

PROCESS = psutil.Process(os.getpid())


def get_memory():
    gc.collect()
    return PROCESS.memory_info().rss


def check_leak(func):
    def wrapper(*args, **kwargs):
        mem_0 = get_memory()
        func(*args, **kwargs)
        mem_1 = get_memory()
        diff = mem_1 - mem_0
        if diff != 0:
            diff %= 4096
        assert diff == 0, f"Memory leak in {func.__name__}"

    return wrapper


TEST_NODE_STR = "TestNode"


@check_leak
def test_typetreenode():
    TypeTreeNode(
        m_Level=0, m_Type=TEST_NODE_STR, m_Name=TEST_NODE_STR, m_ByteSize=0, m_Version=0
    )


def generate_dummy_node(typ: str, name: str = ""):
    return TypeTreeNode(m_Level=0, m_Type=typ, m_Name=name, m_ByteSize=0, m_Version=0)


SIMPLE_NODE_SAMPLES = [
    (["SInt8"], int, (-(2**7), 2**7)),
    (["SInt16", "short"], int, (-(2**15), 2**15)),
    (["SInt32", "int"], int, (-(2**31), 2**31)),
    (["SInt64", "long long"], int, (-(2**63), 2**63)),
    (["UInt8", "char"], int, (0, 2**8)),
    (["UInt16", "unsigned short"], int, (0, 2**16)),
    (["UInt32", "unsigned int", "Type*"], int, (0, 2**32)),
    (["UInt64", "unsigned long long", "FileSize"], int, (0, 2**64)),
    (["float"], float, (-1, 1)),
    (["double"], float, (-1, 1)),
    (["bool"], bool, (False, True)),
]

T = TypeVar("T")

INT_BYTESIZE_MAP = {
    1: "b",
    2: "h",
    4: "i",
    8: "q",
}


def generate_sample_data(
    u_type: List[str],
    py_typ: Type[Union[int, float, str]],
    bounds: Tuple[T, T],
    count: int = 10,
) -> List[T]:
    if py_typ is int:
        if bounds[0] < 0:
            # signed
            byte_size = math.log2(bounds[1]) + 1
            signed = True
        elif bounds[0] == 0:
            # unsigned
            byte_size = math.log2(bounds[1])
            signed = False

        byte_size = round(byte_size / 8)
        char = INT_BYTESIZE_MAP[byte_size]
        if not signed:
            char = char.upper()

        sample_values = [
            bounds[0],
            *[random.randint(bounds[0], bounds[1] - 1) for _ in range(count)],
            bounds[1] - 1,
        ]
        # sample_data = pack(f"<{count+2}{char}", *sample_values)

    elif py_typ is float:
        sample_values = [
            bounds[0],
            *[random.uniform(bounds[0], bounds[1]) for _ in range(count)],
            bounds[1],
        ]
        char = "f" if u_type == "float" else "d"
        # sample_data = pack(f"<{count+2}f", *sample_values)

    elif py_typ is bool:
        sample_values = [
            bounds[0],
            *[random.choice([True, False]) for _ in range(count)],
            bounds[1],
        ]
        # sample_data = pack(f"<{count+2}?", *sample_values)

    elif py_typ is str:
        raise NotImplementedError("String generation not implemented")

    elif py_typ is bytes:
        raise NotImplementedError("Bytes generation not implemented")

    return sample_values


def _test_read_typetree(node: TypeTreeNode, data: bytes, as_dict: bool):
    reader = EndianBinaryReader(data, "<")
    py_values = read_typetree(node, reader, as_dict=as_dict, check_read=False)
    reader.Position = 0
    cpp_values = read_typetree(node, reader, as_dict=as_dict, byte_size=len(data))
    assert py_values == cpp_values
    return py_values


@check_leak
def test_simple_nodes():
    for typs, py_typ, bounds in SIMPLE_NODE_SAMPLES:
        values = generate_sample_data(typs, py_typ, bounds)
        for typ in typs:
            node = generate_dummy_node(typ)
            for value in values:
                writer = EndianBinaryWriter(b"", "<")
                write_typetree(value, node, writer)
                raw = writer.bytes
                re_value = _test_read_typetree(node, raw, as_dict=True)
                assert (
                    abs(value - re_value) < 1e-5
                ), f"Failed on {typ}: {value} != {re_value}"


@check_leak
def test_simple_nodes_array():
    def generate_list_node(item_node: TypeTreeNode):
        root = generate_dummy_node("root", "root")
        array = generate_dummy_node("Array", "Array")
        array.m_Children = [None, item_node]
        root.m_Children = [array]
        return root

    for typs, py_typ, bounds in SIMPLE_NODE_SAMPLES:
        values = generate_sample_data(typs, py_typ, bounds)
        for typ in typs:
            node = generate_dummy_node(typ)
            array_node = generate_list_node(node)
            writer = EndianBinaryWriter(b"", "<")
            write_typetree(values, array_node, writer)
            raw = writer.bytes
            re_values = _test_read_typetree(array_node, raw, as_dict=True)
            assert all(
                (abs(value - re_value) < 1e-5)
                for value, re_value in zip(values, re_values)
            ), f"Failed on {typ}: {values} != {re_values}"


TEST_CLASS_NODE = get_typetree_node(1, (5, 0, 0, 0))
TEST_CLASS_NODE_OBJ = GameObject(
    m_Component=[], m_IsActive=True, m_Layer=0, m_Name="TestObject", m_Tag=0
)
TEST_CLASS_NODE_DICT = TEST_CLASS_NODE_OBJ.__dict__


def test_class_node_dict():
    writer = EndianBinaryWriter(b"", "<")
    write_typetree(TEST_CLASS_NODE_DICT, TEST_CLASS_NODE, writer)
    raw = writer.bytes
    re_value = _test_read_typetree(TEST_CLASS_NODE, raw, as_dict=True)
    assert re_value == TEST_CLASS_NODE_DICT


def test_class_node_clz():
    writer = EndianBinaryWriter(b"", "<")
    write_typetree(TEST_CLASS_NODE_OBJ, TEST_CLASS_NODE, writer)
    raw = writer.bytes
    re_value = _test_read_typetree(TEST_CLASS_NODE, raw, as_dict=False)
    assert re_value == TEST_CLASS_NODE_OBJ


def test_node_from_list_clz():
    node = TypeTreeNode.from_list(list(TEST_CLASS_NODE.traverse()))
    assert node == TEST_CLASS_NODE


def test_node_from_list_dict():
    node = TypeTreeNode.from_list(TEST_CLASS_NODE.to_dict_list())
    assert node == TEST_CLASS_NODE


if __name__ == "__main__":
    for x in list(locals()):
        if str(x)[:4] == "test":
            locals()[x]()
    input("All Tests Passed")
