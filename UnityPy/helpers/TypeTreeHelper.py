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

kAlignBytes = 0x4000


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

    match node.m_Type:
        case "SInt8":
            value = reader.read_byte()
        case "UInt8" | "char":
            value = reader.read_u_byte()
        case "short" | "SInt16":
            value = reader.read_short()
        case "UInt16" | "unsigned short":
            value = reader.read_u_short()
        case "int" | "SInt32":
            value = reader.read_int()
        case "UInt32" | "unsigned int" | "Type*":
            value = reader.read_u_int()
        case "long long" | "SInt64":
            value = reader.read_long()
        case "UInt64" | "unsigned long long" | "FileSize":
            value = reader.read_u_long()
        case "float":
            value = reader.read_float()
        case "double":
            value = reader.read_double()
        case "bool":
            value = reader.read_boolean()
        case "string":
            value = reader.read_aligned_string()
        case "TypelessData":
            value = reader.read_byte_array()
        case "pair":
            first = read_value(node.m_Children[0], reader, as_dict, assetsfile)
            second = read_value(node.m_Children[1], reader, as_dict, assetsfile)
            value = (first, second)
        case _:
            if not node.m_Children:
                value = None
                # raise NotImplementedError(f"Reference type {node.m_Type} not implemented")
            # Vector
            elif node.m_Children and node.m_Children[0].m_Type == "Array":
                if metaflag_is_aligned(node.m_Children[0].m_MetaFlag):
                    align = True

                size = (
                    reader.read_int()
                )  # read_value(node.m_Children[0].m_Children[0], reader, as_dict)
                subtype = node.m_Children[0].m_Children[1]
                if metaflag_is_aligned(subtype.m_MetaFlag):
                    value = read_value_array(subtype, reader, as_dict, size, assetsfile)
                else:
                    value = [
                        read_value(subtype, reader, as_dict, assetsfile)
                        for _ in range(size)
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
                            type=node.m_Type[6:-1],
                        )
                    else:
                        clz = getattr(classes, node.m_Type, Object)
                        clz_kwargs = {
                            clean_name(key): value for key, value in value.items()
                        }
                        try:
                            value = clz(**clz_kwargs)
                        except TypeError:
                            extra_keys = set(clz_kwargs.keys()) - set(
                                clz.__annotations__
                            )
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

    match node.m_Type:
        case "SInt8":
            value = reader.read_byte_array(size)
        case "UInt8" | "char":
            value = reader.read_u_byte_array(size)
        case "short" | "SInt16":
            value = reader.read_short_array(size)
        case "UInt16" | "unsigned short":
            value = reader.read_u_short_array(size)
        case "int" | "SInt32":
            value = reader.read_int_array(size)
        case "UInt32" | "unsigned int" | "Type*":
            value = reader.read_u_int_array(size)
        case "long long" | "SInt64":
            value = reader.read_long_array(size)
        case "UInt64" | "unsigned long long" | "FileSize":
            value = reader.read_u_long_array(size)
        case "float":
            value = reader.read_float_array(size)
        case "double":
            value = reader.read_double_array(size)
        case "bool":
            value = reader.read_boolean_array(size)
        case "string":
            value = [reader.read_aligned_string() for _ in range(size)]
        case "TypelessData":
            value = [reader.read_bytes() for _ in range(size)]
        case "pair":
            value = [
                (
                    read_value(node.m_Children[0], reader, as_dict, assetsfile),
                    read_value(node.m_Children[1], reader, as_dict, assetsfile),
                )
                for _ in range(size)
            ]
        case _:
            if not node.m_Children:
                value = None
                # raise NotImplementedError(f"Reference type {node.m_Type} not implemented")
            # Vector
            elif node.m_Children[0].m_Type == "Array":
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
                                type=node.m_Type[6:-1],
                                **{
                                    child.m_Name: read_value(
                                        child, reader, as_dict, assetsfile
                                    )
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
                        clean_names = [
                            clean_name(child.m_Name) for child in node.m_Children
                        ]
                        if all(name in clz.__annotations__ for name in clean_names):
                            value = [
                                clz(
                                    **{
                                        name: read_value(
                                            child, reader, as_dict, assetsfile
                                        )
                                        for name, child in zip(
                                            clean_names, node.m_Children
                                        )
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


def write_value(
    value: Any,
    node: TypeTreeNode,
    writer: EndianBinaryWriter,
) -> None:
    # print(reader.Position, node.m_Name, node.m_Type, node.m_MetaFlag)
    align = metaflag_is_aligned(node.m_MetaFlag)

    match node.m_Type:
        case "SInt8":
            writer.write_byte(value)
        case "UInt8" | "char":
            writer.write_u_byte(value)
        case "short" | "SInt16":
            writer.write_short(value)
        case "UInt16" | "unsigned short":
            writer.write_u_short(value)
        case "int" | "SInt32":
            writer.write_int(value)
        case "UInt32" | "unsigned int" | "Type*":
            writer.write_u_int(value)
        case "long long" | "SInt64":
            writer.write_long(value)
        case "UInt64" | "unsigned long long" | "FileSize":
            writer.write_u_long(value)
        case "float":
            writer.write_float(value)
        case "double":
            writer.write_double(value)
        case "bool":
            writer.write_boolean(value)
        case "string":
            writer.write_aligned_string(value)
        case "TypelessData":
            writer.write_byte_array(value)
        case "pair":
            write_value(value[0], node.m_Children[0], writer)
            write_value(value[1], node.m_Children[1], writer)
        case _:
            if not node.m_Children:
                value = None
                # raise NotImplementedError(f"Reference type {node.m_Type} not implemented")
            # Vector
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
                        write_value(
                            getattr(value, clean_name(child.m_Name)), child, writer
                        )

    if align:
        writer.align_stream()
