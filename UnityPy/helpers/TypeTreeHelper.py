from typing import Any, Dict, List, Union, Iterable, Tuple
from ..streams import EndianBinaryReader, EndianBinaryWriter
from ctypes import c_uint32
import tabulate
from ..exceptions import TypeTreeError as TypeTreeError

kAlignBytes = 0x4000


class TypeTreeNode(object):
    __slots__ = (
        "m_Version",
        "m_Level",
        "m_TypeFlags",
        "m_ByteSize",
        "m_Index",
        "m_MetaFlag",
        "m_Type",
        "m_Name",
        "m_TypeStrOffset",
        "m_NameStrOffset",
        "m_RefTypeHash",
        "m_VariableCount",
    )
    m_Type: str
    m_Name: str
    m_ByteSize: int
    m_Index: int
    m_Version: int
    m_MetaFlag: int
    m_Level: int
    m_TypeStrOffset: int
    m_NameStrOffset: int
    m_RefTypeHash: str
    m_TypeFlags: int
    m_VariableCount: int

    def __init__(self, data: Union[dict, Iterable[Tuple]] = None, **kwargs):
        if isinstance(data, dict):
            items = data.items()
        elif kwargs:
            items = kwargs.items()
        else:
            items = data

        for key, val in items:
            setattr(self, key, val)

    def __repr__(self):
        return f"<TypeTreeNode({self.m_Level} {self.m_Type} {self.m_Name})>"


try:
    from ..UnityPyBoost import TypeTreeNode, read_typetree as read_typetree_c
except:
    read_typetree_c = None


def node_dict_to_node_cls(nodes: List[dict]) -> List[TypeTreeNode]:
    """Converts all dict-type nodes into TypeTreeNodes

    Parameters
    ----------
    nodes : List[dict]
        nodes/nodes of the typetree as dict

    Returns
    -------
    List[TypeTreeNode]
        a list of TypeTreeNode-type nodes
    """
    # legacy support
    if not next(iter(nodes[0])).startswith("m_"):
        return [
            TypeTreeNode(
                m_Name=x["name"],
                m_Type=x["type"],
                m_Level=x["level"],
                m_MetaFlag=x["meta_flag"],
            )
            for x in nodes
        ]

    return [TypeTreeNode(**node) for node in nodes]


def check_nodes(nodes: List[Union[dict, TypeTreeNode]]) -> List[TypeTreeNode]:
    """Checks the type of the nodes and converts them if necessary.

    Parameters
    ----------
    nodes : List[Union[dict, TypeTreeNode]]
        nodes/nodes of the typetree as dict or TypeTreeNode

    Returns
    -------
    List[TypeTreeNode]
        a list of TypeTreeNode-type nodes
    """
    if isinstance(nodes, list):
        if len(nodes) == 0:
            raise ValueError("not enough nodes")
        if isinstance(nodes[0], TypeTreeNode):
            return nodes
        elif isinstance(nodes[0], dict):
            return node_dict_to_node_cls(nodes)
    raise ValueError(
        f"nodes must be a list of dict or TypeTreeNode elements, but received {type(nodes)} - {type(nodes[0]) if isinstance(nodes, list) else ''}"
    )


def get_nodes(nodes: List[TypeTreeNode], index: int) -> list:
    """Copies all nodes above the level of the node at the set index.

    Parameters
    ----------
    nodes : list
        nodes/nodes of the typetree
    index : int
        index of the node

    Returns
    -------
    list
        A list of nodes
    """
    level = nodes[index].m_Level
    for i, node in enumerate(nodes[index + 1 :], index + 1):
        if node.m_Level <= level:
            return nodes[index:i]
    return nodes[index:]


def read_typetree(
    nodes: List[Union[dict, TypeTreeNode]], reader: EndianBinaryReader
) -> dict:
    """Reads the typetree of the object contained in the reader via the node list.

    Parameters
    ----------
    nodes : list
        List of nodes/nodes
    reader : EndianBinaryReader
        Reader of the object to be parsed

    Returns
    -------
    dict
        The parsed typtree
    """
    reader.reset()

    nodes = check_nodes(nodes)

    if read_typetree_c:
        return read_typetree_c(
            nodes, reader.read_bytes(reader.byte_size), reader.endian
        )

    obj = read_value(nodes, reader, c_uint32(0))

    read = reader.Position - reader.byte_start
    if read != reader.byte_size:
        raise TypeTreeError(
            f"Error while read type, read {read} bytes but expected {reader.byte_size} bytes",
            nodes,
        )

    return obj


def read_value(nodes: List[TypeTreeNode], reader: EndianBinaryReader, i: c_uint32):
    node = nodes[i.value]
    typ = node.m_Type
    align = (node.m_MetaFlag & kAlignBytes) != 0

    if typ == "SInt8":
        value = reader.read_byte()
    elif typ in ["UInt8", "char"]:
        value = reader.read_u_byte()
    elif typ in ["short", "SInt16"]:
        value = reader.read_short()
    elif typ in ["UInt16", "unsigned short"]:
        value = reader.read_u_short()
    elif typ in ["int", "SInt32"]:
        value = reader.read_int()
    elif typ in ["UInt32", "unsigned int", "Type*"]:
        value = reader.read_u_int()
    elif typ in ["long long", "SInt64"]:
        value = reader.read_long()
    elif typ in ["UInt64", "unsigned long long", "FileSize"]:
        value = reader.read_u_long()
    elif typ == "float":
        value = reader.read_float()
    elif typ == "double":
        value = reader.read_double()
    elif typ == "bool":
        value = reader.read_boolean()
    elif typ == "string":
        value = reader.read_aligned_string()
        i.value += 3  # Array, Size, Data(typ)
    elif typ == "map":  # map == MultiDict
        if (nodes[i.value + 1].m_MetaFlag & kAlignBytes) != 0:
            align = True
        map_ = get_nodes(nodes, i.value)
        i.value += len(map_) - 1
        first = get_nodes(map_, 4)
        second = get_nodes(map_, 4 + len(first))
        size = reader.read_int()
        value = [None] * size
        for j in range(size):
            key = read_value(first, reader, c_uint32(0))
            value[j] = (key, read_value(second, reader, c_uint32(0)))
    elif typ == "TypelessData":
        size = reader.read_int()
        value = reader.read_bytes(size)
        i.value += 2  # Size == int, Data(typ) == char/uint8
    else:
        # Vector
        if i.value < len(nodes) - 1 and nodes[i.value + 1].m_Type == "Array":
            if (nodes[i.value + 1].m_MetaFlag & kAlignBytes) != 0:
                align = True
            vector = get_nodes(nodes, i.value)
            i.value += len(vector) - 1
            size = reader.read_int()
            value = [read_value(vector, reader, c_uint32(3)) for _ in range(size)]
        else:  # Class
            clz = get_nodes(nodes, i.value)
            i.value += len(clz) - 1
            value = {}
            j = c_uint32(1)
            while j.value < len(clz):
                clz_node = clz[j.value]
                value[clz_node.m_Name] = read_value(clz, reader, j)
                j.value += 1

    if align:
        reader.align_stream()
    return value


def read_typetree_str(
    sb: List[str], nodes: List[Union[dict, TypeTreeNode]], reader: EndianBinaryReader
) -> list:
    """Reads the typetree of the object contained in the reader via the node list and dumps it as string.

    Parameters
    ----------
    sb : list
        StringBuilder - a list used to build the string dump, should be empty
    nodes : list
        List of nodes/nodes
    reader : EndianBinaryReader
        Reader of the object to be parsed

    Returns
    -------
    list
        The sb given as input
    """
    # reader.reset()
    nodes = check_nodes(nodes)

    i = c_uint32(0)
    while i.value < len(nodes):
        read_value_str(sb, nodes, reader, i)
        i.value += 1

    readed = reader.Position - reader.byte_start
    if readed != reader.byte_size:
        raise TypeTreeError(
            f"Error while read type, read {readed} bytes but expected {reader.byte_size} bytes",
            nodes,
        )

    return sb


def read_value_str(
    sb: List[str], nodes: List[TypeTreeNode], reader: EndianBinaryReader, i: c_uint32
) -> list:
    node = nodes[i.value]
    typ = node.m_Type
    align = (node.m_MetaFlag & kAlignBytes) != 0
    append = True

    if typ == "SInt8":
        value = reader.read_byte()
    elif typ in ["UInt8", "char"]:
        value = reader.read_u_byte()
    elif typ in ["short", "SInt16"]:
        value = reader.read_short()
    elif typ in ["UInt16", "unsigned short"]:
        value = reader.read_u_short()
    elif typ in ["int", "SInt32"]:
        value = reader.read_int()
    elif typ in ["UInt32", "unsigned int", "Type*"]:
        value = reader.read_u_int()
    elif typ in ["long long", "SInt64"]:
        value = reader.read_long()
    elif typ in ["UInt64", "unsigned long long", "FileSize"]:
        value = reader.read_u_long()
    elif typ == "float":
        value = reader.read_float()
    elif typ == "double":
        value = reader.read_double()
    elif typ == "bool":
        value = reader.read_boolean()
    elif typ == "string":
        value = reader.read_aligned_string()
        i.value += 3  # Array, Size, Data(typ)
        append = False
        sb.append(
            '{0}{1} {2} = "{3}"\r\n'.format(
                "\t" * node.m_Level, node.m_Type, node.m_Name, value
            )
        )
    elif typ == "map":
        if (nodes[i.value + 1].m_MetaFlag & kAlignBytes) != 0:
            align = True
        map_ = get_nodes(nodes, i.value)
        i.value += len(map_) - 1
        first = get_nodes(map_, 4)
        second = get_nodes(map_, 4 + len(first))
        size = reader.read_int()
        append = False
        sb.append(
            "{0}{1} {2}\r\n".format("\t" * node.m_Level, node.m_Type, node.m_Name)
        )
        sb.append("{0}{1} {2}\r\n".format("\t" * (node.m_Level + 1), "Array", "Array"))
        sb.append(
            "{0}{1} {2} = {3}\r\n".format(
                "\t" * (node.m_Level + 1), "int", "size", size
            )
        )
        for j in range(size):
            sb.append("{0}[{1}]\r\n".format("\t" * (node.m_Level + 2), j))
            sb.append(
                "{0}{1} {2}\r\n".format("\t" * (node.m_Level + 2), "pair", "data")
            )
            read_value_str(sb, first, reader, c_uint32(0))
            read_value_str(sb, second, reader, c_uint32(0))
    elif typ == "TypelessData":
        size = reader.read_int()
        value = reader.read_bytes(size)
        i.value += 2  # Size == int, Data(typ) == char/uint8
        append = False
        sb.append(
            "{0}{1} {2}\r\n".format("\t" * node.m_Level, node.m_Type, node.m_Name)
        )
        sb.append(
            "{0}{1} {2} = {3}\r\n".format("\t" * node.m_Level, "int", "size", size)
        )
        # sb.append("{0}{1} {2} = {3}\r\n".format(
        #    "\t" * node.level, "UInt8", "data", base64.b64encode(value)))
    else:
        # Vector
        if i.value < len(nodes) - 1 and nodes[i.value + 1].m_Type == "Array":
            if (nodes[i.value + 1].m_MetaFlag & kAlignBytes) != 0:
                align = True
            vector = get_nodes(nodes, i.value)
            i.value += len(vector) - 1
            size = reader.read_int()
            append = False
            sb.append(
                "{0}{1} {2}\r\n".format("\t" * node.m_Level, node.m_Type, node.m_Name)
            )
            sb.append(
                "{0}{1} {2}\r\n".format("\t" * (node.m_Level + 1), "Array", "Array")
            )
            sb.append(
                "{0}{1} {2} = {3}\r\n".format(
                    "\t" * (node.m_Level + 1), "int", "size", size
                )
            )
            for j in range(size):
                sb.append("{0}[{1}]\r\n".format("\t" * (node.m_Level + 2), j))
                read_value_str(sb, vector, reader, c_uint32(3))

        else:  # Class
            clz = get_nodes(nodes, i.value)
            i.value += len(clz) - 1
            j = c_uint32(1)
            append = False
            sb.append(
                "{0}{1} {2}\r\n".format("\t" * node.m_Level, node.m_Type, node.m_Name)
            )
            while j.value < len(clz):
                read_value_str(sb, clz, reader, j)
                j.value += 1

    if append:
        sb.append(
            "{0}{1} {2} = {3}\r\n".format(
                "\t" * node.m_Level, node.m_Type, node.m_Name, value
            )
        )

    if align:
        reader.align_stream()
    return sb


def dump_typetree(nodes: List[TypeTreeNode]) -> str:
    """Dumps the structure of the given nodes.

    Parameters
    ----------
    nodes : list
        List of nodes/nodes

    Returns
    -------
    str
        The dumped structure
    """
    field_names = ["m_Level", "m_Type", "m_Name", "m_MetaFlag"]
    rows = [[getattr(x, key) for key in field_names] for x in nodes]
    return tabulate.tabulate(rows, headers=field_names)


def write_typetree(
    obj: dict, nodes: List[Union[dict, TypeTreeNode]], writer: EndianBinaryWriter = None
) -> EndianBinaryWriter:
    """Writes the data of the object via the given typetree of the object into the writer.

    Parameters
    ----------
    obj : dict
        Object to be saved
    nodes : list
        List of nodes/nodes
    writer : EndianBinaryWriter
        Writer of the object to be saved

    Returns
    -------
    EndianBinaryWriter
        The writer that was used to save the data of the given object.
    """
    if not writer:
        writer = EndianBinaryWriter()

    nodes = check_nodes(nodes)

    i = c_uint32(1)
    while i.value < len(nodes):
        value = obj[nodes[i.value].m_Name]
        write_value(value, nodes, writer, i)
        i.value += 1
    return writer


def write_value(
    value: Any, nodes: List[TypeTreeNode], writer: EndianBinaryWriter, i: c_uint32
):
    node = nodes[i.value]
    typ = node.m_Type
    align = (node.m_MetaFlag & kAlignBytes) != 0

    if typ == "SInt8":
        writer.write_byte(value)
    elif typ in ["UInt8", "char"]:
        writer.write_u_byte(value)
    elif typ in ["short", "SInt16"]:
        writer.write_short(value)
    elif typ in ["UInt16", "unsigned short"]:
        writer.write_u_short(value)
    elif typ in ["int", "SInt32"]:
        writer.write_int(value)
    elif typ in ["UInt32", "unsigned int", "Type*"]:
        writer.write_u_int(value)
    elif typ in ["long long", "SInt64"]:
        writer.write_long(value)
    elif typ in ["UInt64", "unsigned long long", "FileSize"]:
        writer.write_u_long(value)
    elif typ == "float":
        writer.write_float(value)
    elif typ == "double":
        writer.write_double(value)
    elif typ == "bool":
        writer.write_boolean(value)
    elif typ == "string":
        writer.write_aligned_string(value)
        i.value += 3  # Array, Size, Data(typ)
    elif typ == "map":
        if (nodes[i.value + 1].m_MetaFlag & kAlignBytes) != 0:
            align = True
        map_ = get_nodes(nodes, i.value)
        i.value += len(map_) - 1
        first = get_nodes(map_, 4)
        second = get_nodes(map_, 4 + len(first))
        # size
        writer.write_int(len(value))
        # data
        for key, val in value:
            write_value(key, first, writer, c_uint32(0))
            write_value(val, second, writer, c_uint32(0))

    elif typ == "TypelessData":
        writer.write_int(len(value))
        writer.write_bytes(value)
        i.value += 2  # Size == int, Data(typ) == char/uint8
    else:
        # Vector
        if i.value < len(nodes) - 1 and nodes[i.value + 1].m_Type == "Array":
            if (nodes[i.value + 1].m_MetaFlag & kAlignBytes) != 0:
                align = True
            vector = get_nodes(nodes, i.value)
            i.value += len(vector) - 1
            writer.write_int(len(value))
            for val in value:
                write_value(val, vector, writer, c_uint32(3))
        else:  # Class
            clz = get_nodes(nodes, i.value)
            i.value += len(clz) - 1
            j = c_uint32(1)
            while j.value < len(clz):
                val = value[clz[j.value].m_Name]
                write_value(val, clz, writer, j)
                j.value += 1

    if align:
        writer.align_stream()
