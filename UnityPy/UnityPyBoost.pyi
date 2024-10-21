from __future__ import annotations
from typing import Union, TYPE_CHECKING, Literal, Optional, List, Any

if TYPE_CHECKING:
    from .files.SerializedFile import SerializedFile
    from .classes import Object

def unpack_vertexdata(
    data: Union[bytes, bytearray],
    vertex_count: int,
    stream_offset: int,
    stream_stride: int,
    channel_offset: int,
    channel_dimension: int,
    swap: bool,
) -> bytes: ...
def read_typetree(
    data: Union[bytes, bytearray],
    node: TypeTreeNode,
    endian: Literal["<", ">"],
    as_dict: bool,
    assetsfile: SerializedFile,
    classes: dict,
) -> Union[dict[str, Any], Object]: ...

class TypeTreeNode:
    m_Level: int
    m_Type: str
    m_Name: str
    m_ByteSize: int
    m_Version: int
    m_Children: List[TypeTreeNode]
    m_TypeFlags: Optional[int] = None
    m_VariableCount: Optional[int] = None
    m_Index: Optional[int] = None
    m_MetaFlag: Optional[int] = None
    m_RefTypeHash: Optional[int] = None
    _clean_name: str
