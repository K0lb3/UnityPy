from typing import List, Optional

from PIL.Image import Image

from UnityPy.classes.generated import GLTextureSettings, StreamingInfo, Texture

class Texture2DArray(Texture):
  image_data: bytes
  m_ColorSpace: int
  m_DataSize: int
  m_Depth: int
  m_Format: int
  m_Height: int
  m_IsReadable: bool
  m_MipCount: int
  m_Name: str
  m_TextureSettings: GLTextureSettings
  m_Width: int
  m_DownscaleFallback: Optional[bool] = None
  m_ForcedFallbackFormat: Optional[int] = None
  m_IgnoreMipmapLimit: Optional[bool] = None
  m_IsAlphaChannelOptional: Optional[bool] = None
  m_MipmapLimitGroupName: Optional[str] = None
  m_MipsStripped: Optional[int] = None
  m_StreamData: Optional[StreamingInfo] = None
  m_UsageMode: Optional[int] = None

  @property
  def images(self) -> List[Image]: ...
