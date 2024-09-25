from __future__ import annotations
import re
from typing import Optional, Any, Union, TYPE_CHECKING

from .TypeTreeNode import TypeTreeNode
from ..streams.EndianBinaryReader import EndianBinaryReader
from ..streams.EndianBinaryWriter import EndianBinaryWriter

from .. import classes

Object = classes.Object
PPtr = classes.PPtr

if TYPE_CHECKING:
    from ..files.SerializedFile import SerializedFile


try:
    from ..UnityPyBoost import read_typetree as read_typetree_boost
except ImportError:
    read_typetree_boost = None

kAlignBytes = 0x4000

FUNCTION_READ_MAP = {
    "SInt8": EndianBinaryReader.read_byte,
    "UInt8": EndianBinaryReader.read_u_byte,
    "char": EndianBinaryReader.read_u_byte,
    "short": EndianBinaryReader.read_short,
    "SInt16": EndianBinaryReader.read_short,
    "unsigned short": EndianBinaryReader.read_u_short,
    "UInt16": EndianBinaryReader.read_u_short,
    "int": EndianBinaryReader.read_int,
    "SInt32": EndianBinaryReader.read_int,
    "unsigned int": EndianBinaryReader.read_u_int,
    "UInt32": EndianBinaryReader.read_u_int,
    "Type*": EndianBinaryReader.read_u_int,
    "long long": EndianBinaryReader.read_long,
    "SInt64": EndianBinaryReader.read_long,
    "unsigned long long": EndianBinaryReader.read_u_long,
    "UInt64": EndianBinaryReader.read_u_long,
    "FileSize": EndianBinaryReader.read_u_long,
    "float": EndianBinaryReader.read_float,
    "double": EndianBinaryReader.read_double,
    "bool": EndianBinaryReader.read_boolean,
    "string": EndianBinaryReader.read_aligned_string,
    "TypelessData": EndianBinaryReader.read_byte_array,
}
FUNCTION_READ_MAP_ARRAY = {
    "SInt8": EndianBinaryReader.read_byte_array,
    "UInt8": EndianBinaryReader.read_u_byte_array,
    "char": EndianBinaryReader.read_u_byte_array,
    "short": EndianBinaryReader.read_short_array,
    "SInt16": EndianBinaryReader.read_short_array,
    "unsigned short": EndianBinaryReader.read_u_short_array,
    "UInt16": EndianBinaryReader.read_u_short_array,
    "int": EndianBinaryReader.read_int_array,
    "SInt32": EndianBinaryReader.read_int_array,
    "unsigned int": EndianBinaryReader.read_u_int_array,
    "UInt32": EndianBinaryReader.read_u_int_array,
    "Type*": EndianBinaryReader.read_u_int_array,
    "long long": EndianBinaryReader.read_long_array,
    "SInt64": EndianBinaryReader.read_long_array,
    "unsigned long long": EndianBinaryReader.read_u_long_array,
    "UInt64": EndianBinaryReader.read_u_long_array,
    "FileSize": EndianBinaryReader.read_u_long_array,
    "float": EndianBinaryReader.read_float_array,
    "double": EndianBinaryReader.read_double_array,
    "bool": EndianBinaryReader.read_boolean_array,
}


def read_typetree(
    root_node: TypeTreeNode,
    reader: EndianBinaryReader,
    as_dict: bool = True,
    expected_read: Optional[int] = None,
    assetsfile: Optional[SerializedFile] = None,
) -> Union[dict[str, Any], Object]:
    """Reads the typetree of the object contained in the reader via the node list.

    Parameters
    ----------
    nodes : list
        List of nodes/nodes
    reader : EndianBinaryReader
        Reader of the object to be parsed

    Returns
    -------
    dict | objects.Object
        The parsed typtree
    """
    if expected_read and read_typetree_boost:
        data = reader.read_bytes(expected_read)
        return read_typetree_boost(
            data, root_node, reader.endian, as_dict, assetsfile, classes, clean_name
        )

    pos = reader.Position
    obj = read_value(root_node, reader, as_dict, assetsfile)

    read = reader.Position - pos
    if expected_read is not None and read != expected_read:
        raise ValueError(
            f"Expected to read {expected_read} bytes, but read {read} bytes"
        )

    return obj


def write_typetree(
    value: Union[dict[str, Any], Object],
    root_node: TypeTreeNode,
    writer: EndianBinaryWriter,
) -> None:
    """Writes the typetree of the object contained in the reader via the node list.

    Parameters
    ----------
    value: dict | objects.Object
        The object to be written
    nodes : list
        List of nodes/nodes
    writer : EndianBinaryWriter
        Writer of the object to be parsed
    """
    return write_value(value, root_node, writer)


def read_value(
    node: TypeTreeNode,
    reader: EndianBinaryReader,
    as_dict: bool,
    assetsfile: Optional[SerializedFile],
) -> Any:
    # print(reader.Position, node.m_Name, node.m_Type, node.m_MetaFlag)
    align = metaflag_is_aligned(node.m_MetaFlag)

    func = FUNCTION_READ_MAP.get(node.m_Type)
    if func:
        value = func(reader)
    elif node.m_Type == "pair":
        first = read_value(node.m_Children[0], reader, as_dict, assetsfile)
        second = read_value(node.m_Children[1], reader, as_dict, assetsfile)
        value = (first, second)
    # Vector
    elif node.m_Children and node.m_Children[0].m_Type == "Array":
        if metaflag_is_aligned(node.m_Children[0].m_MetaFlag):
            align = True

        # size = read_value(node.m_Children[0].m_Children[0], reader, as_dict)
        size = reader.read_int()
        subtype = node.m_Children[0].m_Children[1]
        if metaflag_is_aligned(subtype.m_MetaFlag):
            value = read_value_array(subtype, reader, as_dict, size, assetsfile)
        else:
            value = [
                read_value(subtype, reader, as_dict, assetsfile) for _ in range(size)
            ]

    else:  # Class
        value = {
            child.m_Name: read_value(child, reader, as_dict, assetsfile)
            for child in node.m_Children
        }

        if not as_dict:
            if node.m_Type.startswith("PPtr<"):
                value = PPtr[Any](
                    assetsfile=assetsfile,
                    m_FileID=value["m_FileID"],
                    m_PathID=value["m_PathID"],
                )
            else:
                clz = getattr(classes, node.m_Type, Object)
                clz_kwargs = {clean_name(key): value for key, value in value.items()}
                try:
                    value = clz(**clz_kwargs)
                except TypeError:
                    extra_keys = set(clz_kwargs.keys()) - set(clz.__annotations__)
                    value = clz(
                        **{
                            key: value
                            for key, value in clz_kwargs.items()
                            if key in clz.__annotations__
                        }
                    )
                    for key in extra_keys:
                        setattr(value, key, clz_kwargs[key])

    if align:
        reader.align_stream()

    return value


def read_value_array(
    node: TypeTreeNode,
    reader: EndianBinaryReader,
    as_dict: bool,
    size: int,
    assetsfile: Optional[SerializedFile],
) -> Any:
    align = metaflag_is_aligned(node.m_MetaFlag)

    func = FUNCTION_READ_MAP_ARRAY.get(node.m_Type)
    if func:
        value = func(reader, size)
    elif node.m_Type == "string":
        value = [reader.read_aligned_string() for _ in range(size)]
    elif node.m_Type == "TypelessData":
        value = [reader.read_bytes() for _ in range(size)]
    elif node.m_Type == "pair":
        key_node = node.m_Children[0]
        value_node = node.m_Children[1]

        key_func = FUNCTION_READ_MAP.get(
            key_node.m_Type,
            lambda reader: read_value(key_node, reader, as_dict, assetsfile),
        )
        value_func = FUNCTION_READ_MAP.get(
            value_node.m_Type,
            lambda reader: read_value(value_node, reader, as_dict, assetsfile),
        )
        value = [(key_func(reader), value_func(reader)) for _ in range(size)]
    # Vector
    elif node.m_Children and node.m_Children[0].m_Type == "Array":
        if metaflag_is_aligned(node.m_Children[0].m_MetaFlag):
            align = True
        subtype = node.m_Children[0].m_Children[1]
        if metaflag_is_aligned(subtype.m_MetaFlag):
            value = [
                read_value_array(
                    subtype, reader, as_dict, reader.read_int(), assetsfile
                )
                for _ in range(size)
            ]
        else:
            value = [
                [
                    read_value(subtype, reader, as_dict, assetsfile)
                    for _ in range(reader.read_int())
                ]
                for _ in range(size)
            ]
    else:  # Class
        if as_dict:
            value = [
                {
                    child.m_Name: read_value(child, reader, as_dict, assetsfile)
                    for child in node.m_Children
                }
                for _ in range(size)
            ]
        else:
            if node.m_Type.startswith("PPtr<"):
                value = [
                    PPtr[Any](
                        assetsfile=assetsfile,
                        **{
                            child.m_Name: read_value(child, reader, as_dict, assetsfile)
                            for child in node.m_Children
                        },
                    )
                    for _ in range(size)
                ]
            else:
                clz = getattr(
                    classes,
                    node.m_Type,
                    Object,
                )
                clean_names = [clean_name(child.m_Name) for child in node.m_Children]
                if all(name in clz.__annotations__ for name in clean_names):
                    value = [
                        clz(
                            **{
                                name: read_value(child, reader, as_dict, assetsfile)
                                for name, child in zip(clean_names, node.m_Children)
                            }
                        )
                        for _ in range(size)
                    ]
                else:
                    extra_keys = set(clean_names) - set(clz.__annotations__)
                    value = [None] * size
                    for i in range(size):
                        value_i_d = {
                            clean_name(child.m_Name): read_value(
                                child, reader, as_dict, assetsfile
                            )
                            for child in node.m_Children
                        }
                        value_i = clz(
                            **{
                                key: value
                                for key, value in value_i_d.items()
                                if key in clz.__annotations__
                            }
                        )
                        for key in extra_keys:
                            setattr(value_i, key, value_i_d[key])
                        value[i] = value_i
    if align:
        reader.align_stream()
    return value


def metaflag_is_aligned(meta_flag: int | None) -> bool:
    return ((meta_flag or 0) & kAlignBytes) != 0


def clean_name(name: str) -> str:
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


FUNCTION_WRITE_MAP = {
    "SInt8": EndianBinaryWriter.write_byte,
    "UInt8": EndianBinaryWriter.write_u_byte,
    "char": EndianBinaryWriter.write_u_byte,
    "short": EndianBinaryWriter.write_short,
    "SInt16": EndianBinaryWriter.write_short,
    "unsigned short": EndianBinaryWriter.write_u_short,
    "UInt16": EndianBinaryWriter.write_u_short,
    "int": EndianBinaryWriter.write_int,
    "SInt32": EndianBinaryWriter.write_int,
    "unsigned int": EndianBinaryWriter.write_u_int,
    "UInt32": EndianBinaryWriter.write_u_int,
    "Type*": EndianBinaryWriter.write_u_int,
    "long long": EndianBinaryWriter.write_long,
    "SInt64": EndianBinaryWriter.write_long,
    "unsigned long long": EndianBinaryWriter.write_u_long,
    "UInt64": EndianBinaryWriter.write_u_long,
    "FileSize": EndianBinaryWriter.write_u_long,
    "float": EndianBinaryWriter.write_float,
    "double": EndianBinaryWriter.write_double,
    "bool": EndianBinaryWriter.write_boolean,
    "string": EndianBinaryWriter.write_aligned_string,
    "TypelessData": EndianBinaryWriter.write_byte_array,
}


def write_value(
    value: Any,
    node: TypeTreeNode,
    writer: EndianBinaryWriter,
) -> None:
    # print(reader.Position, node.m_Name, node.m_Type, node.m_MetaFlag)
    align = metaflag_is_aligned(node.m_MetaFlag)

    func = FUNCTION_WRITE_MAP.get(node.m_Type)
    if func:
        value = func(writer, value)
    elif node.m_Type == "pair":
        write_value(value[0], node.m_Children[0], writer)
        write_value(value[1], node.m_Children[1], writer)
    elif node.m_Children and node.m_Children[0].m_Type == "Array":
        if metaflag_is_aligned(node.m_Children[0].m_MetaFlag):
            align = True

        writer.write_int(len(value))
        subtype = node.m_Children[0].m_Children[1]
        [write_value(sub_value, subtype, writer) for sub_value in value]

    else:  # Class
        if isinstance(value, dict):
            for child in node.m_Children:
                write_value(value[child.m_Name], child, writer)
        else:
            for child in node.m_Children:
                write_value(getattr(value, clean_name(child.m_Name)), child, writer)

    if align:
        writer.align_stream()
