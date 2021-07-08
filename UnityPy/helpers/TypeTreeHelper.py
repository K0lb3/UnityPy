from typing import Dict
from UnityPy.streams import EndianBinaryReader, EndianBinaryWriter
from ctypes import c_uint32
import base64
import tabulate


def get_nodes(nodes: list, index: int) -> list:
    '''Copies all nodes above the level of the node at the set index.

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
    '''
    nodes2 = [nodes[index]]
    level = nodes[index].level
    for node in nodes[index+1:]:
        if (node.level <= level):
            return nodes2
        nodes2.append(node)
    return nodes2


def read_typetree(nodes: list, reader: EndianBinaryReader) -> dict:
    '''Reads the typetree of the object contained in the reader via the node list.

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
    '''
    # reader.reset()
    if isinstance(nodes[0], dict):
        nodes = node_dict_to_class(nodes)

    obj = {}
    i = c_uint32(1)
    while i.value < len(nodes):
        node = nodes[i.value]
        obj[node.name] = read_value(nodes, reader, i)
        i.value += 1

    readed = reader.Position - reader.byte_start
    if readed != reader.byte_size:
        print(
            f"Error while read type, read {readed} bytes but expected {reader.byte_size} bytes")

    return obj


def read_value(nodes: list, reader: EndianBinaryReader, i: c_uint32):
    node = nodes[i.value]
    typ = node.type
    align = (node.meta_flag & 0x4000) != 0

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
    elif typ == "map": # map == MultiDict
        if ((nodes[i.value + 1].meta_flag & 0x4000) != 0):
            align = True
        map_ = get_nodes(nodes, i.value)
        i.value += len(map_) - 1
        first = get_nodes(map_, 4)
        second = get_nodes(map_, 4 + len(first))
        size = reader.read_int()
        value = [None]*size
        for j in range(size):
            key = read_value(first, reader, c_uint32(0))
            value[j] = (key, read_value(second, reader, c_uint32(0)))
    elif typ == "TypelessData":
        size = reader.read_int()
        value = reader.read_bytes(size)
        i.value += 2  # Size == int, Data(typ) == char/uint8
    else:
        # Vector
        if i.value < len(nodes) - 1 and nodes[i.value + 1].type == "Array":
            if (nodes[i.value + 1].meta_flag & 0x4000) != 0:
                align = True
            vector = get_nodes(nodes, i.value)
            i.value += len(vector) - 1
            size = reader.read_int()
            value = [
                read_value(vector, reader, c_uint32(3))
                for _ in range(size)
            ]
        else:  # Class
            clz = get_nodes(nodes, i.value)
            i.value += len(clz) - 1
            value = {}
            j = c_uint32(1)
            while j.value < len(clz):
                clz_node = clz[j.value]
                value[clz_node.name] = read_value(clz, reader, j)
                j.value += 1

    if align:
        reader.align_stream()
    return value


def read_typetree_str(sb: list, nodes: list, reader: EndianBinaryReader) -> list:
    '''Reads the typetree of the object contained in the reader via the node list and dumps it as string.

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
    '''
    # reader.reset()
    if isinstance(nodes[0], dict):
        nodes = node_dict_to_class(nodes)

    i = c_uint32(0)
    while i.value < len(nodes):
        read_value_str(sb, nodes, reader, i)
        i.value += 1

    readed = reader.Position - reader.byte_start
    if readed != reader.byte_size:
        print(
            f"Error while read type, read {readed} bytes but expected {reader.byte_size} bytes")

    return sb


def read_value_str(sb: list, nodes: list, reader: EndianBinaryReader, i: c_uint32) -> list:
    node = nodes[i.value]
    typ = node.type
    align = (node.meta_flag & 0x4000) != 0
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
        sb.append('{0}{1} {2} = "{3}"\r\n'.format(
            "\t" * node.level, node.type, node.name, value
        ))
    elif typ == "map":
        if ((nodes[i.value + 1].meta_flag & 0x4000) != 0):
            align = True
        map_ = get_nodes(nodes, i.value)
        i.value += len(map_) - 1
        first = get_nodes(map_, 4)
        second = get_nodes(map_, 4 + len(first))
        size = reader.read_int()
        append = False
        sb.append("{0}{1} {2}\r\n".format(
            "\t" * node.level, node.type, node.name))
        sb.append("{0}{1} {2}\r\n".format(
            "\t" * (node.level + 1), "Array", "Array"))
        sb.append("{0}{1} {2} = {3}\r\n".format(
            "\t" * (node.level + 1), "int", "size", size))
        for j in range(size):
            sb.append("{0}[{1}]\r\n".format("\t" * (node.level + 2), j))
            sb.append("{0}{1} {2}\r\n".format(
                "\t" * (node.level + 2), "pair", "data"))
            read_value_str(sb, first, reader, c_uint32(0))
            read_value_str(sb, second, reader, c_uint32(0))
    elif typ == "TypelessData":
        size = reader.read_int()
        value = reader.read_bytes(size)
        i.value += 2  # Size == int, Data(typ) == char/uint8
        append = False
        sb.append("{0}{1} {2}\r\n".format(
            "\t" * node.level, node.type, node.name))
        sb.append("{0}{1} {2} = {3}\r\n".format(
            "\t" * node.level, "int", "size", size))
        # sb.append("{0}{1} {2} = {3}\r\n".format(
        #    "\t" * node.level, "UInt8", "data", base64.b64encode(value)))
    else:
        # Vector
        if i.value < len(nodes) - 1 and nodes[i.value + 1].type == "Array":
            if (nodes[i.value + 1].meta_flag & 0x4000) != 0:
                align = True
            vector = get_nodes(nodes, i.value)
            i.value += len(vector) - 1
            size = reader.read_int()
            append = False
            sb.append("{0}{1} {2}\r\n".format(
                "\t" * node.level, node.type, node.name))
            sb.append("{0}{1} {2}\r\n".format(
                "\t" * (node.level + 1), "Array", "Array"))
            sb.append("{0}{1} {2} = {3}\r\n".format(
                "\t" * (node.level + 1), "int", "size", size))
            for j in range(size):
                sb.append("{0}[{1}]\r\n".format("\t" * (node.level + 2), j))
                read_value_str(sb, vector, reader, c_uint32(3))

        else:  # Class
            clz = get_nodes(nodes, i.value)
            i.value += len(clz) - 1
            j = c_uint32(1)
            append = False
            sb.append("{0}{1} {2}\r\n".format(
                "\t" * node.level, node.type, node.name))
            while j.value < len(clz):
                read_value_str(sb, clz, reader, j)
                j.value += 1

    if append:
        sb.append("{0}{1} {2} = {3}\r\n".format(
            "\t" * node.level, node.type, node.name, value
        ))

    if align:
        reader.align_stream()
    return sb


def dump_typetree(nodes) -> str:
    '''Dumps the structure of the given nodes.

        Parameters
        ----------
        nodes : list
            List of nodes/nodes

        Returns
        -------
        str
            The dumped structure
    '''
    field_names = ["level", "type", "name", "meta_flag"]
    rows = [
        [
            getattr(x, key) for key in field_names
        ]
        for x in nodes
    ]
    return tabulate.tabulate(rows, headers=field_names)


def write_typetree(obj: dict, nodes: list, writer: EndianBinaryWriter = None) -> EndianBinaryWriter:
    '''Writes the data of the object via the given typetree of the object into the writer.

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
    '''
    if not writer:
        writer = EndianBinaryWriter()
    
    if isinstance(nodes[0], dict):
        nodes = node_dict_to_class(nodes)
    
    i = c_uint32(1)
    while i.value < len(nodes):
        value = obj[nodes[i.value].name]
        write_value(value, nodes, writer, i)
        i.value += 1
    return writer


def write_value(value, nodes: list, writer: EndianBinaryWriter, i: c_uint32):
    node = nodes[i.value]
    typ = node.type
    align = (node.meta_flag & 0x4000) != 0

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
        if ((nodes[i.value + 1].meta_flag & 0x4000) != 0):
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
        if i.value < len(nodes) - 1 and nodes[i.value + 1].type == "Array":
            if (nodes[i.value + 1].meta_flag & 0x4000) != 0:
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
                val = value[clz[j.value].name]
                write_value(val, clz, writer, j)
                j.value += 1

    if align:
        writer.align_stream()

def node_dict_to_class(nodes: list):
    class Fake:
        def __init__(self, data) -> None:
            self.__dict__ = data
    
    return [Fake(node) for node in nodes]