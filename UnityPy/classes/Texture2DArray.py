from typing import Optional, List

from .Texture import Texture
from .Texture2D import StreamingInfo
from ..enums.GraphicsFormat import GraphicsFormat, GRAPHICS_TO_TEXTURE_MAP
from ..export import Texture2DConverter
from ..helpers.ResourceReader import get_resource_data
from PIL import Image


class GLTextureSettings:
    m_Aniso: int
    m_FilterMode: int
    m_MipBias: float
    m_WrapMode: Optional[int] = None
    m_WrapU: Optional[int] = None
    m_WrapV: Optional[int] = None
    m_WrapW: Optional[int] = None

    def __init__(self, reader):
        self.__dict__.update(**self.read_typetree(wrap=True).__dict__)


class Texture2DArray(Texture):
    image_data: bytes
    m_ColorSpace: int
    m_DataSize: int
    m_Depth: int
    m_Format: GraphicsFormat
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

    def __init__(self, reader):
        super().__init__(reader=reader)
        self.__dict__.update(**reader.read_typetree(wrap=True).__dict__)
        self.m_TextureSettings.__class__ = GLTextureSettings
        self.m_Format = GraphicsFormat(self.m_Format)

    @property
    def image_data(self):
        data = getattr(self, "image data", None)
        if data is None:
            data = get_resource_data(
                self.m_StreamData.path,
                self.assets_file,
                self.m_StreamData.offset,
                self.m_StreamData.size,
            )
        return data

    @property
    def images(self) -> List[Image.Image]:
        texture_format = GRAPHICS_TO_TEXTURE_MAP.get(self.m_Format)
        if not texture_format:
            raise NotImplementedError(
                f"GraphicsFormat {self.m_Format} not supported yet"
            )

        # calculate the number of textures in the array
        texture_size = self.m_DataSize // self.m_Depth
        return [
            Texture2DConverter.parse_image_data(
                self.image_data[offset : offset + texture_size],
                self.m_Width,
                self.m_Height,
                texture_format,
                self.version,
                0,
                None,
            )
            for offset in range(0, self.m_DataSize, texture_size)
        ]
