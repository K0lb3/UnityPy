from typing import BinaryIO, List, Optional, Union

from PIL.Image import Image

from UnityPy.classes.generated import GLTextureSettings, StreamingInfo, Texture

class Texture2D(Texture):
  image_data: bytes
  m_CompleteImageSize: int
  m_Height: int
  m_ImageCount: int
  m_IsReadable: bool
  m_LightmapFormat: int
  m_Name: str
  m_TextureDimension: int
  m_TextureFormat: int
  m_TextureSettings: GLTextureSettings
  m_Width: int
  m_ColorSpace: Optional[int] = None
  m_DownscaleFallback: Optional[bool] = None
  m_ForcedFallbackFormat: Optional[int] = None
  m_IgnoreMasterTextureLimit: Optional[bool] = None
  m_IgnoreMipmapLimit: Optional[bool] = None
  m_IsAlphaChannelOptional: Optional[bool] = None
  m_IsPreProcessed: Optional[bool] = None
  m_MipCount: Optional[int] = None
  m_MipMap: Optional[bool] = None
  m_MipmapLimitGroupName: Optional[str] = None
  m_MipsStripped: Optional[int] = None
  m_PlatformBlob: Optional[List[int]] = None
  m_ReadAllowed: Optional[bool] = None
  m_StreamData: Optional[StreamingInfo] = None
  m_StreamingMipmaps: Optional[bool] = None
  m_StreamingMipmapsPriority: Optional[int] = None

  @property
  def image(self) -> Image: ...
  def set_image(
      self,
      img: Union[Image, str, BinaryIO],
      target_format: Optional[int] = None,
      mipmap_count: int = 1,
  ) -> None: ...
  def get_image_data(self) -> bytes: ...

