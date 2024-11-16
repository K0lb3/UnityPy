from __future__ import annotations

from typing import TYPE_CHECKING, Generic, List, Optional, Tuple, TypeVar, Union

from ..enums import ClassIDType
from ..exceptions import TypeTreeError
from ..helpers import TypeTreeHelper
from ..helpers.Tpk import get_typetree_node
from ..helpers.TypeTreeNode import TypeTreeNode
from ..streams import EndianBinaryReader, EndianBinaryWriter

if TYPE_CHECKING:
    from ..enums import BuildTarget
    from ..files.SerializedFile import BuildType, SerializedFile, SerializedType

T = TypeVar("T")


class ObjectReader(Generic[T]):
    assets_file: SerializedFile
    reader: EndianBinaryReader
    data: bytes
    version: Tuple[int, int, int, int]
    version2: int
    platform: BuildTarget
    build_type: BuildType
    path_id: int
    byte_start_offset: Tuple[int, int]
    byte_start: int
    byte_size_offset: Tuple[int, int]
    byte_size: int
    type_id: int
    serialized_type: Optional[SerializedType]
    class_id: int
    type: ClassIDType
    is_destroyed: Optional[int]
    is_stripped: Optional[int]

    # saves where the parser stopped
    # in case that not all data is read
    # and the obj.data is changed, the unknown data can be added again

    def __init__(self, assets_file: SerializedFile, reader: EndianBinaryReader):
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
        if self.assets_file:
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

    def read(self, check_read: bool = True) -> T:
        obj = self.read_typetree(wrap=True, check_read=check_read)
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

    def dump_typetree_structure(
        self,
        nodes: Optional[Union[TypeTreeNode, List[dict]]] = None,
        indent: str = "  ",
    ) -> str:
        node = self._get_typetree_node(nodes)
        return node.dump_structure(indent=indent)

    def read_typetree(
        self,
        nodes: Optional[Union[TypeTreeNode, List[dict]]] = None,
        wrap: bool = False,
        check_read: bool = True,
    ) -> Union[dict, T]:
        self.reset()
        node = self._get_typetree_node(nodes)
        ret = TypeTreeHelper.read_typetree(
            node,
            self.reader,
            as_dict=not wrap,
            assetsfile=self.assets_file,
            byte_size=self.byte_size,
            check_read=check_read,
        )
        if wrap:
            ret.set_object_reader(self)
        return ret

    def save_typetree(
        self,
        tree: dict,
        nodes: Optional[Union[TypeTreeNode, List[dict]]] = None,
        writer: EndianBinaryWriter = None,
    ):
        node = self._get_typetree_node(nodes)
        if not writer:
            writer = EndianBinaryWriter(endian=self.reader.endian)
        TypeTreeHelper.write_typetree(tree, node, writer, self.assets_file)
        data = writer.bytes
        self.set_raw_data(data)
        return data

    def get_raw_data(self) -> bytes:
        pos = self.Position
        self.reset()
        ret = self.reader.read_bytes(self.byte_size)
        self.Position = pos
        return ret

    def _get_typetree_node(
        self, node: Optional[Union[TypeTreeNode, List[dict]]] = None
    ) -> TypeTreeNode:
        if isinstance(node, TypeTreeNode):
            return node
        elif isinstance(node, list):
            return TypeTreeNode.from_list(node)
        elif node is not None:
            raise ValueError("nodes must be a list[dict] or TypeTreeNode")

        if self.serialized_type:
            node = self.serialized_type.node
        if not node:
            node = get_typetree_node(self.class_id, self.version)
        if not node:
            raise TypeTreeError("There are no TypeTree nodes for this object.")
        return node

    # UnityPy 2 syntax early implementation
    def parse_as_object(self) -> T:
        return self.read()

    def parse_as_dict(self) -> dict:
        return self.read_typetree()
