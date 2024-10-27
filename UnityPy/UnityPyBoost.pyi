from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Optional, Union

if TYPE_CHECKING:
    from .classes import Object
    from .files.SerializedFile import SerializedFile

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
    endian: Union["<", ">"],
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

def decrypt_block(
    index_bytes: Union[bytes, bytearray],
    substitute_bytes: Union[bytes, bytearray],
    data: Union[bytes, bytearray],
    index: int,
) -> bytes: ...
