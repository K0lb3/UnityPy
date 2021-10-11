from .PPtr import PPtr
from ..enums import BuildTarget
from ..helpers import TypeTreeHelper
from ..streams import EndianBinaryWriter
from ..files import ObjectReader
import types
from ..exceptions import TypeTreeError as TypeTreeError

class Object(object):
    type_tree: dict

    def __init__(self, reader: ObjectReader):
        self.reader = reader
        self.assets_file = reader.assets_file
        self.type = reader.type
        self.path_id = reader.path_id
        self.version = reader.version
        self.build_type = reader.build_type
        self.platform = reader.platform
        self.serialized_type = reader.serialized_type
        self.byte_size = reader.byte_size
        self.assets_file = reader.assets_file

        if self.platform == BuildTarget.NoTarget:
            self._object_hide_flags = reader.read_u_int()

        self.container = (
            self.assets_file._container[self.path_id]
            if self.path_id in self.assets_file._container
            else None
        )

        self.reader.reset()
        if type(self) == Object:
            self.read_typetree()

    def has_struct_member(self, name: str) -> bool:
        return self.serialized_type.m_Nodes and any(
            [x.name == name for x in self.serialized_type.m_Nodes]
        )

    def dump_typetree(self, nodes: list = None) -> str:
        return self.reader.dump_typetree(nodes=nodes)

    def dump_typetree_structure(self) -> str:
        return self.reader.dump_typetree_structure()

    def read_typetree(self, nodes: list = None) -> dict:
        try:
            tree = self.reader.read_typetree(nodes)
        except TypeTreeError as e:
            print("Failed to read TypeTree:\n", e.message)
            return {}
        self.type_tree = NodeHelper(tree, self.assets_file)
        return tree

    def save_typetree(self, nodes: list = None, writer: EndianBinaryWriter = None):
        if not writer:
            writer = EndianBinaryWriter(endian=self.reader.endian)

        def class_to_dict(value):
            if isinstance(value, list):
                return [class_to_dict(val) for val in value]
            elif isinstance(value, dict):
                return {
                    key: class_to_dict(val)
                    for key, val in value.items()
                }
            elif hasattr(value, "__dict__"):
                if isinstance(value, PPtr):
                    return {"m_PathID": value.path_id, "m_FileID": value.file_id}
                return {
                    key: class_to_dict(val)
                    for key, val in value.__dict__.items()
                    if not isinstance(value, (types.FunctionType, types.MethodType)) and not key in ["type_tree", "assets_file"]
                }
            else:
                return value

        obj = class_to_dict(self if not self.type_tree else self.type_tree)
        return self.reader.save_typetree(obj, nodes, writer)

    def get_raw_data(self) -> bytes:
        return self.reader.get_raw_data()

    def set_raw_data(self, data):
        self.reader.set_raw_data(data)

    def save(self, writer: EndianBinaryWriter = None, intern_call=False):
        if not writer:
            writer = EndianBinaryWriter(endian=self.reader.endian)
        if intern_call:
            if self.platform == BuildTarget.NoTarget:
                writer.write_u_int(self._object_hide_flags)
        elif self.serialized_type.nodes:
            # save for objects WITHOUT specific save function
            # so we have to use the typetree if it exists
            self.save_typetree()
        else:
            raise NotImplementedError(
                "There is no save function for this obj.type nor has it any typetree nodes that could be used.")

    def _save(self, writer):
        # the reader is actually an ObjectReader,
        # the data value is written back into the asset
        self.reader.data = writer.bytes

    def __getattr__(self, name):
        """
        If item not found in __dict__, read type_tree and check if it is in there.
        """
        if name == "type_tree" or self.type_tree == None:
            old_pos = self.reader.Position
            self.read_typetree()
            self.reader.Position = old_pos
            if name == "type_tree":
                return self.type_tree

        return getattr(self.type_tree, name)

    def get(self, key, default=None):
        return getattr(self, key, default)

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.name)


class NodeHelper:
    def __init__(self, data, assets_file):
        if "m_PathID" in data and "m_FileID" in data:
            # used to make pointers directly useable
            self.path_id = data["m_PathID"]
            self.file_id = data["m_FileID"]
            self.index = data.get("m_Index", -2)
            self.assets_file = assets_file
            self._obj = None
            self.__class__ = PPtr
        else:
            self.__dict__ = {
                key: NodeHelper(val, assets_file) for key, val in data.items()
            }

    def __new__(cls, data, assets_file):
        if isinstance(data, dict):
            return super(NodeHelper, cls).__new__(cls)
        elif isinstance(data, list):
            return [NodeHelper(x, assets_file) for x in data]
        return data

    def __getitem__(self, item):
        return getattr(self, item)

    def to_dict(self):
        def dump(val):
            return (
                val.to_dict()
                if isinstance(val, NodeHelper)
                else [dump(item) for item in val]
                if isinstance(val, list)
                else {"m_PathID": val.path_id, "m_FileID": val.file_id}
                if isinstance(val, PPtr)
                else [x for x in val]
                if isinstance(val, (bytearray, bytes))
                else val
            )

        return {key: dump(val) for key, val in self.__dict__.items()}

    def items(self):
        return self.__dict__.items()

    def values(self):
        return self.__dict__.values()

    def keys(self):
        return self.__dict__.keys()

    def __repr__(self):
        return "<NodeHelper - %s>" % self.__dict__.__repr__()

