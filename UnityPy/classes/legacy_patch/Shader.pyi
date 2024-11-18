from typing import List, Optional, Tuple, Union

from UnityPy.classes import PPtr
from UnityPy.classes.generated import (GUID, NamedObject, SerializedShader,
                                       Texture)

class Shader(NamedObject):
  m_Name: str
  compressedBlob: Optional[List[int]] = None
  compressedLengths: Optional[Union[List[int], List[List[int]]]] = None
  decompressedLengths: Optional[Union[List[int], List[List[int]]]] = None
  decompressedSize: Optional[int] = None
  m_AssetGUID: Optional[GUID] = None
  m_Dependencies: Optional[List[PPtr[Shader]]] = None
  m_NonModifiableTextures: Optional[List[Tuple[str, PPtr[Texture]]]] = None
  m_ParsedForm: Optional[SerializedShader] = None
  m_PathName: Optional[str] = None
  m_Script: Optional[str] = None
  m_ShaderIsBaked: Optional[bool] = None
  m_SubProgramBlob: Optional[List[int]] = None
  offsets: Optional[Union[List[int], List[List[int]]]] = None
  platforms: Optional[List[int]] = None
  stageCounts: Optional[List[int]] = None

  def export(self) -> str: ...
