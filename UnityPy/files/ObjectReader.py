from ..enums import ClassIDType

from . import SerializedFile
from .. import classes
from ..classes.Object import NodeHelper
from ..streams import EndianBinaryReader, EndianBinaryWriter
from ..helpers import TypeTreeHelper
from ..helpers.Tpk import get_typetree_nodes
from ..exceptions import TypeTreeError


class ObjectReader:
    byte_start: int
    byte_size: int
    type_id: int
    class_id: int
    type: ClassIDType
    path_id: int
    # serialized_type: SerializedType
    _read_until: int

    # saves where the parser stopped
    # in case that not all data is read
    # and the obj.data is changed, the unknown data can be added again

    def __init__(self, assets_file, reader: EndianBinaryReader):
        self.assets_file = assets_file
        self.reader = reader
        self.data = b""
        self.version = assets_file.version
        self.version2 = assets_file.header.version
        self.platform = assets_file.target_platform
        self.build_type = assets_file.build_type

        header = assets_file.header
        types = assets_file.types

        # AssetStudio ObjectInfo init
        if assets_file.big_id_enabled:
            self.path_id = reader.read_long()
        elif header.version < 14:
            self.path_id = reader.read_int()
        else:
            reader.align_stream()
            self.path_id = reader.read_long()

        if header.version >= 22:
            self.byte_start_offset = (self.reader.real_offset(), 8)
            self.byte_start = reader.read_long()
        else:
            self.byte_start_offset = (self.reader.real_offset(), 4)
            self.byte_start = reader.read_u_int()

        self.byte_start += header.data_offset
        self.byte_header_offset = header.data_offset
        self.byte_base_offset = self.reader.BaseOffset

        self.byte_size_offset = (self.reader.real_offset(), 4)
        self.byte_size = reader.read_u_int()

        self.type_id = reader.read_int()

        if header.version < 16:
            self.class_id = reader.read_u_short()
            self.serialized_type = None
            for typ in types:
                if typ.class_id == self.type_id:
                    self.serialized_type = typ
                    break
        else:
            typ = types[self.type_id]
            self.serialized_type = typ
            self.class_id = typ.class_id

        self.type = ClassIDType(self.class_id)

        if header.version < 11:
            self.is_destroyed = reader.read_u_short()

        if 11 <= header.version < 17:
            script_type_index = reader.read_short()
            if self.serialized_type:
                self.serialized_type.script_type_index = script_type_index

        if header.version == 15 or header.version == 16:
            self.stripped = reader.read_byte()

    def write(
        self, header, writer: EndianBinaryWriter, data_writer: EndianBinaryWriter
    ):
        if self.assets_file.big_id_enabled:
            writer.write_long(self.path_id)
        elif header.version < 14:
            writer.write_int(self.path_id)
        else:
            writer.align_stream()
            writer.write_long(self.path_id)

        if self.data:
            data = self.data
            # in some cases the parser doesn't read all of the object data
            # games might still require the missing data
            # so following code appends the missing data back to edited objects
            # -> following solution has let to some problems, so it will be removed for now
            # if self.type != ClassIDType.MonoBehaviour:
            #     end_pos = self.byte_start + self.byte_size
            #     if self._read_until and self._read_until != end_pos:
            #         self.reader.Position = self._read_until
            #         data += self.reader.read_bytes(end_pos - self._read_until)
        else:
            self.reset()
            data = self.reader.read(self.byte_size)

        if header.version >= 22:
            writer.write_long(data_writer.Position)
        else:
            writer.write_u_int(data_writer.Position)

        writer.write_u_int(len(data))
        data_writer.write(data)

        writer.write_int(self.type_id)

        if header.version < 16:
            writer.write_u_short(self.class_id)

        if header.version < 11:
            writer.write_u_short(self.is_destroyed)

        if 11 <= header.version < 17:
            writer.write_short(self.serialized_type.script_type_index)

        if header.version == 15 or header.version == 16:
            writer.write_byte(self.stripped)

    def set_raw_data(self, data):
        self.data = data
        self.assets_file.mark_changed()

    @property
    def container(self):
        return self.assets_file._container.path_dict.get(self.path_id)

    @property
    def Position(self):
        return self.reader.Position

    @Position.setter
    def Position(self, pos):
        self.reader.Position = pos

    def reset(self):
        self.reader.Position = self.byte_start

    def read(self, return_typetree_on_error: bool = True):
        cls = getattr(classes, self.type.name, None)

        obj = None
        if cls:
            try:
                obj = cls(self)
            except Exception as e:
                if return_typetree_on_error:
                    print(f"Error during the parsing of object {self.path_id}")
                    print(e)
                    print("Returning the typetree")
                else:
                    raise e
        if not obj:
            obj = self.read_typetree(wrap=True)
        self._read_until = self.reader.Position
        return obj

    def get(self, key, default=None):
        return getattr(self, key, default)

    def __getattr__(self, item: str):
        if hasattr(self.reader, item):
            return getattr(self.reader, item)

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.type.name)

    ###################################################
    #
    #           Typetree Stuff
    #
    ###################################################

    def dump_typetree(self, nodes: list = None) -> str:
        self.reset()
        sb = []
        nodes = self.get_typetree(nodes)
        TypeTreeHelper.read_typetree_str(sb, nodes, self)
        return "".join(sb)

    def dump_typetree_structure(self) -> str:
        return TypeTreeHelper.dump_typetree(self.get_typetree_nodes())

    def get_typetree_nodes(self, nodes: list = None) -> list:
        if nodes:
            return nodes

        if self.serialized_type:
            nodes = self.serialized_type.nodes
        if not nodes:
            nodes = get_typetree_nodes(self.class_id, self.version)
        if not nodes:
            raise TypeTreeError("There are no TypeTree nodes for this object.")
        return nodes

    def read_typetree(self, nodes: list = None, wrap: bool = False) -> dict:
        self.reset()
        nodes = self.get_typetree_nodes(nodes)
        res = TypeTreeHelper.read_typetree(nodes, self)
        return NodeHelper(res, self.assets_file) if wrap else res

    def save_typetree(
        self, tree: dict, nodes: list = None, writer: EndianBinaryWriter = None
    ):
        nodes = self.get_typetree_nodes(nodes)
        if not writer:
            writer = EndianBinaryWriter(endian=self.reader.endian)
        writer = TypeTreeHelper.write_typetree(tree, nodes, writer)
        data = writer.bytes
        self.set_raw_data(data)
        return data

    def get_raw_data(self) -> bytes:
        pos = self.Position
        self.reset()
        ret = self.reader.read_bytes(self.byte_size)
        self.Position = pos
        return ret

    def set_raw_data(self, data):
        self.data = data
        if self.assets_file:
            self.assets_file.mark_changed()
