from ..enums import BuildTarget
from ..helpers import TypeTreeHelper
from ..streams import EndianBinaryWriter, EndianBinaryReader


class Object(object):
    type_tree: dict

    def __init__(self, reader):
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
            self.__dict__.update(self.read_type_tree().__dict__)

    def has_struct_member(self, name: str) -> bool:
        return self.serialized_type.m_Nodes and any(
            [x.name == name for x in self.serialized_type.m_Nodes]
        )

    def dump(self) -> str:
        self.reader.reset()
        if getattr(self.serialized_type, "nodes", None):
            sb = []
            TypeTreeHelper(self.reader).read_type_string(sb, self.serialized_type.nodes)
            return "".join(sb)
        return ""

    def read_type_tree(self) -> dict:
        old_pos = self.reader.Position
        self.reader.reset()
        if self.serialized_type.nodes:
            self.type_tree = TypeTreeHelper(self.reader).read_value(
                self.serialized_type.nodes, 0
            )
        else:
            self.type_tree = {}
        self.reader.Position = old_pos
        return NodeHelper(self.type_tree, self.assets_file)

    def get_raw_data(self) -> bytes:
        self.reader.reset()
        return self.reader.read_bytes(self.byte_size)

    def set_raw_data(self, data):
        self.reader.data = data

    def save(self, writer: EndianBinaryWriter, intern_call=False):
        if intern_call:
            if self.platform == BuildTarget.NoTarget:
                writer.write_u_int(self._object_hide_flags)

    def _save(self, writer):
        # the reader is actually an ObjectReader,
        # the data value is written back into the asset
        self.reader.data = writer.bytes

    def __getattr__(self, item):
        """
        If item not found in __dict__, read type_tree and check if it is in there.
        """
        self.read_type_tree()
        if item in self.type_tree:
            return self.type_tree[item]

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.name)


from .PPtr import PPtr


class NodeHelper:
    def __init__(self, data, assets_file):
        if "m_PathID" in data and "m_FileID" in data:
            # used to make pointers directly useable
            self.path_id = data["m_PathID"]
            self.file_id = data["m_FileID"]
            self.index = data.get("m_Index", -2)
            self.assets_file = assets_file
            self.__class__ = PPtr
        else:
            self.__dict__ = {
                str(key): NodeHelper(val, assets_file) for key, val in data.items()
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

