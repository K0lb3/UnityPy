from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

from ..classes import MonoBehaviour
from ..classes.ClassIDTypeToClassMap import ClassIDTypeToClassMap
from ..enums import BuildTarget, ClassIDType
from ..exceptions import TypeTreeError
from ..helpers import TypeTreeHelper
from ..helpers.Tpk import get_typetree_node
from ..helpers.TypeTreeNode import TypeTreeNode
from ..helpers.UnityVersion import UnityVersion
from ..streams import EndianBinaryReader, EndianBinaryWriter

if TYPE_CHECKING:
    from ..files.SerializedFile import SerializedFile, SerializedType

T = TypeVar("T")
NodeInput = Union[TypeTreeNode, List[Dict[str, Union[str, int]]]]


class ObjectReader(Generic[T]):
    assets_file: SerializedFile
    reader: EndianBinaryReader
    data: bytes
    version: UnityVersion
    version2: int
    platform: BuildTarget
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

    def write(self, header, writer: EndianBinaryWriter, data_writer: EndianBinaryWriter):
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
            assert self.is_destroyed is not None
            writer.write_u_short(self.is_destroyed)

        if 11 <= header.version < 17:
            assert self.serialized_type is not None
            writer.write_short(self.serialized_type.script_type_index)

        if header.version == 15 or header.version == 16:
            writer.write_byte(self.stripped)

    def set_raw_data(self, data):
        self.data = data
        if self.assets_file:
            self.assets_file.mark_changed()

    def get_class(self) -> Union[Type[T], None]:
        return ClassIDTypeToClassMap.get(self.type)  # type: ignore

    def peek_name(self) -> Union[str, None]:
        """Peeks the name of the object without reading/parsing the whole object."""
        node = self._get_typetree_node()
        peek_node = node.get_name_peek_node()
        if peek_node:
            node, key = peek_node
            return self.parse_as_dict(node, check_read=False)[key]
        else:
            return None

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
        return obj  # type: ignore

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
        nodes: Optional[NodeInput] = None,
        indent: str = "  ",
    ) -> str:
        node = self._get_typetree_node(nodes)
        return node.dump_structure(indent=indent)

    def read_typetree(
        self,
        nodes: Optional[NodeInput] = None,
        wrap: bool = False,
        check_read: bool = True,
    ) -> Union[dict, T]:
        node = self._get_typetree_node(nodes)
        self.reset()
        ret = TypeTreeHelper.read_typetree(
            node,
            self.reader,
            as_dict=not wrap,
            assetsfile=self.assets_file,
            byte_size=self.byte_size,
            check_read=check_read,
        )
        if wrap:
            ret.set_object_reader(self)  # type: ignore
        return ret  # type: ignore

    def save_typetree(
        self,
        tree: Union[dict, T],
        nodes: Optional[NodeInput] = None,
        writer: Optional[EndianBinaryWriter] = None,
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
        self,
        node: Optional[NodeInput] = None,
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
            if node.m_Type == "MonoBehaviour":
                try:
                    node = self.generate_monobehaviour_node(node)
                except ValueError:
                    pass
        if not node:
            raise TypeTreeError("There are no TypeTree nodes for this object.")
        return node

    # UnityPy 2 syntax early implementation
    def parse_as_object(self, node: Optional[NodeInput] = None, check_read: bool = True) -> T:
        return self.read_typetree(nodes=node, wrap=True, check_read=check_read)  # type: ignore

    def parse_as_dict(self, node: Optional[NodeInput] = None, check_read: bool = True) -> dict[str, Any]:
        return self.read_typetree(nodes=node, wrap=False, check_read=check_read)  # type: ignore

    def patch(
        self,
        obj: Union[dict, T],
        nodes: Optional[NodeInput] = None,
        writer: Optional[EndianBinaryWriter] = None,
    ):
        return self.save_typetree(obj, nodes=nodes, writer=writer)

    # MonoBehaviour specific methods
    def parse_monobehaviour_head(self, mb_node: Optional[TypeTreeNode] = None) -> MonoBehaviour:
        if mb_node is None:
            mb_node = get_typetree_node(ClassIDType.MonoBehaviour, self.version)

        mb = self.read_typetree(nodes=mb_node, wrap=True, check_read=False)
        return cast(MonoBehaviour, mb)

    def generate_monobehaviour_node(self, mb_node: Optional[TypeTreeNode] = None) -> TypeTreeNode:
        env = self.assets_file.environment
        generator = env.typetree_generator
        if generator is None:
            raise ValueError("MonoBehaviour detected, but no typetree_generator set to the environment!")

        monobehaviour = self.parse_monobehaviour_head(mb_node)
        script = monobehaviour.m_Script.deref_parse_as_object()

        if script.m_Namespace != "":
            fullname = f"{script.m_Namespace}.{script.m_ClassName}"
        else:
            fullname = script.m_ClassName

        node = generator.get_nodes_up(script.m_AssemblyName, fullname)
        if node:
            return node
        else:
            raise ValueError(f"Failed to generate MonoBehaviour node for {fullname} of {script.m_AssemblyName}!")
