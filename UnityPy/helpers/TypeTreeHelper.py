from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Optional, Union

from attrs import define

from .. import classes
from ..streams.EndianBinaryReader import EndianBinaryReader
from ..streams.EndianBinaryWriter import EndianBinaryWriter
from .TypeTreeNode import TypeTreeNode

Object = classes.Object
UnknownObject = classes.UnknownObject
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


@define(slots=True)
class TypeTreeConfig:
    as_dict: bool
    assetsfile: "Optional[SerializedFile]" = None
    has_registry: bool = False

    def copy(self) -> TypeTreeConfig:
        return TypeTreeConfig(self.as_dict, self.assetsfile, self.has_registry)


def get_ref_type_node(ref_object: dict, assetfile: SerializedFile) -> TypeTreeNode:
    typ = ref_object["type"]
    if isinstance(typ, dict):
        cls = typ["class"]
        ns = typ["ns"]
        asm = typ["asm"]
    else:
        cls = getattr(typ, "class")
        ns = typ.ns
        asm = typ.asm

    if not assetfile or not assetfile.ref_types:
        raise ValueError("SerializedFile has no ref_types")

    if cls == "":
        return None

    for ref_type in assetfile.ref_types:
        if (
            cls == ref_type.m_ClassName
            and ns == ref_type.m_NameSpace
            and asm == ref_type.m_AssemblyName
        ):
            return ref_type.node
    else:
        raise ValueError(f"Referenced type not found: {cls} {ns} {asm}")


def read_typetree(
    root_node: TypeTreeNode,
    reader: EndianBinaryReader,
    as_dict: bool = True,
    byte_size: Optional[int] = None,
    check_read: bool = True,
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
    bytes_read: int
    if byte_size and read_typetree_boost:
        data = reader.read_bytes(byte_size)
        obj, bytes_read = read_typetree_boost(
            data, root_node, reader.endian, as_dict, assetsfile, classes
        )
    else:
        pos = reader.Position
        config = TypeTreeConfig(as_dict, assetsfile, False)
        obj = read_value(root_node, reader, config)
        bytes_read = reader.Position - pos

    if check_read and bytes_read != byte_size:
        raise ValueError(
            f"Expected to read {byte_size} bytes, but only read {bytes_read} bytes"
        )

    return obj


def write_typetree(
    value: Union[dict[str, Any], Object],
    root_node: TypeTreeNode,
    writer: EndianBinaryWriter,
    assetsfile: Optional[SerializedFile] = None,
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
    config = TypeTreeConfig(isinstance(value, dict), assetsfile, False)
    return write_value(value, root_node, writer, config)


def read_value(
    node: TypeTreeNode,
    reader: EndianBinaryReader,
    config: TypeTreeConfig,
) -> Any:
    # print(reader.Position, node.m_Name, node.m_Type, node.m_MetaFlag)
    align = metaflag_is_aligned(node.m_MetaFlag)

    func = FUNCTION_READ_MAP.get(node.m_Type)
    if func:
        value = func(reader)
    elif node.m_Type == "pair":
        first = read_value(node.m_Children[0], reader, config)
        second = read_value(node.m_Children[1], reader, config)
        value = (first, second)
    elif node.m_Type == "ReferencedObject":
        value = {}
        for child in node.m_Children:
            if child.m_Type == "ReferencedObjectData":
                ref_type_nodes = get_ref_type_node(value, config.assetsfile)
                if ref_type_nodes is None:
                    continue
                value[child.m_Name] = read_value(ref_type_nodes, reader, config)
            else:
                value[child.m_Name] = read_value(child, reader, config)
    # Vector
    elif node.m_Children and node.m_Children[0].m_Type == "Array":
        if metaflag_is_aligned(node.m_Children[0].m_MetaFlag):
            align = True

        # size = read_value(node.m_Children[0].m_Children[0], reader, as_dict)
        size = reader.read_int()
        subtype = node.m_Children[0].m_Children[1]
        if metaflag_is_aligned(subtype.m_MetaFlag):
            value = read_value_array(subtype, reader, config)
        else:
            value = [read_value(subtype, reader, config) for _ in range(size)]

    else:  # Class
        value = {}
        for child in node.m_Children:
            if child.m_Type == "ManagedReferencesRegistry":
                if config.has_registry:
                    continue
                else:
                    config = config.copy()
                    config.has_registry = True
            value[child.m_Name if config.as_dict else child._clean_name] = read_value(
                child, reader, config
            )

        if not config.as_dict:
            if node.m_Type.startswith("PPtr<"):
                value = PPtr[Any](
                    assetsfile=config.assetsfile,
                    m_FileID=value["m_FileID"],
                    m_PathID=value["m_PathID"],
                )
            else:
                clz = getattr(classes, node.m_Type, UnknownObject)
                try:
                    value = clz(**value)
                except TypeError:
                    keys = set(value.keys())
                    annotation_keys = set(clz.__annotations__)
                    missing_keys = annotation_keys - keys
                    if clz is UnknownObject or missing_keys:
                        value = UnknownObject(node, **value)
                    else:
                        extra_keys = keys - annotation_keys
                        if extra_keys:
                            instance = clz(
                                **{key: value[key] for key in annotation_keys}
                            )
                            for key in extra_keys:
                                setattr(instance, key, value[key])
                            value = instance
                        else:
                            value = UnknownObject(**value)

    if align:
        reader.align_stream()

    return value


def read_value_array(
    node: TypeTreeNode,
    reader: EndianBinaryReader,
    config: TypeTreeConfig,
    size: int,
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
            lambda reader: read_value(key_node, reader, config),
        )
        value_func = FUNCTION_READ_MAP.get(
            value_node.m_Type,
            lambda reader: read_value(value_node, reader, config),
        )
        value = [(key_func(reader), value_func(reader)) for _ in range(size)]
    elif node.m_Type == "ReferencedObject":
        value = [None] * size
        for i in range(size):
            item = {}
            for child in node.m_Children:
                if child.m_Type == "ReferencedObjectData":
                    ref_type_nodes = get_ref_type_node(item, config.assetsfile)
                    item[child.m_Name] = read_value(ref_type_nodes, reader, config)
                else:
                    item[child.m_Name] = read_value(child, reader, config)
            value[i] = item
    # Vector
    elif node.m_Children and node.m_Children[0].m_Type == "Array":
        if metaflag_is_aligned(node.m_Children[0].m_MetaFlag):
            align = True
        subtype = node.m_Children[0].m_Children[1]
        if metaflag_is_aligned(subtype.m_MetaFlag):
            value = [
                read_value_array(subtype, reader, config, reader.read_int())
                for _ in range(size)
            ]
        else:
            value = [
                [read_value(subtype, reader, config) for _ in range(reader.read_int())]
                for _ in range(size)
            ]
    else:  # Class
        if config.as_dict:
            value = [
                {
                    child.m_Name: read_value(child, reader, config)
                    for child in node.m_Children
                }
                for _ in range(size)
            ]
        elif node.m_Type.startswith("PPtr<"):
            value = [
                PPtr[Any](
                    assetsfile=config.assetsfile,
                    **{
                        child.m_Name: read_value(child, reader, config)
                        for child in node.m_Children
                    },
                )
                for _ in range(size)
            ]
        else:
            clz = getattr(
                classes,
                node.m_Type,
                UnknownObject,
            )
            keys = set(child._clean_name for child in node.m_Children)
            annotation_keys = set(clz.__annotations__)
            missing_keys = annotation_keys - keys
            extra_keys = keys - annotation_keys
            if missing_keys or clz is UnknownObject:
                value = [
                    UnknownObject(
                        node,
                        **{
                            child._clean_name: read_value(child, reader, config)
                            for child in node.m_Children
                        },
                    )
                    for _ in range(size)
                ]
            elif extra_keys:
                value = [None] * size
                for i in range(size):
                    value_i_d = {
                        child._clean_name: read_value(child, reader, config)
                        for child in node.m_Children
                    }
                    value_i = clz(
                        **{
                            key: value
                            for key, value in value_i_d.items()
                            if key in annotation_keys
                        }
                    )
                    for key in extra_keys:
                        setattr(value_i, key, value_i_d[key])
                    value[i] = value_i
            else:
                value = [
                    clz(
                        **{
                            child._clean_name: read_value(child, reader, config)
                            for child in node.m_Children
                        }
                    )
                    for _ in range(size)
                ]

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
    value: Union[dict[str, Any], Object],
    node: TypeTreeNode,
    writer: EndianBinaryWriter,
    config: TypeTreeConfig,
) -> None:
    # print(reader.Position, node.m_Name, node.m_Type, node.m_MetaFlag)
    align = metaflag_is_aligned(node.m_MetaFlag)

    func = FUNCTION_WRITE_MAP.get(node.m_Type)
    if func:
        value = func(writer, value)
    elif node.m_Type == "pair":
        write_value(value[0], node.m_Children[0], writer, config)
        write_value(value[1], node.m_Children[1], writer, config)
    elif node.m_Type == "ReferencedObject":
        for child in node.m_Children:
            if child.m_Type == "ReferencedObjectData":
                ref_type_nodes = get_ref_type_node(value, config.assetsfile)
                write_value(value[child.m_Name], ref_type_nodes, writer, config)
            else:
                write_value(value[child.m_Name], child, writer, config)
    elif node.m_Children and node.m_Children[0].m_Type == "Array":
        if metaflag_is_aligned(node.m_Children[0].m_MetaFlag):
            align = True

        writer.write_int(len(value))
        subtype = node.m_Children[0].m_Children[1]
        [write_value(sub_value, subtype, writer, config) for sub_value in value]

    else:  # Class
        if isinstance(value, dict):
            for child in node.m_Children:
                if child.m_Type == "ManagedReferencesRegistry":
                    if config.has_registry:
                        continue
                    else:
                        config = config.copy()
                        config.has_registry = True
                write_value(value[child.m_Name], child, writer, config)
        else:
            for child in node.m_Children:
                if child.m_Type == "ManagedReferencesRegistry":
                    if config.has_registry:
                        continue
                    else:
                        config = config.copy()
                        config.has_registry = True
                write_value(getattr(value, child._clean_name), child, writer, config)

    if align:
        writer.align_stream()
