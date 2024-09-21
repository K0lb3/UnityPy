from __future__ import annotations
from typing import TYPE_CHECKING, List

from ...enums.GraphicsFormat import GRAPHICS_TO_TEXTURE_MAP, GraphicsFormat
from ..generated import Texture2DArray

if TYPE_CHECKING:
    from PIL import Image


def _Texture2DArray_get_images(self: Texture2DArray) -> List[Image.Image]:
    from ...export import Texture2DConverter
    from ...helpers.ResourceReader import get_resource_data

    texture_format = GRAPHICS_TO_TEXTURE_MAP.get(GraphicsFormat(self.m_Format))
    if not texture_format:
        raise NotImplementedError(f"GraphicsFormat {self.m_Format} not supported yet")

    image_data = self.image_data
    if image_data is None:
        image_data = get_resource_data(
            self.m_StreamData.path,
            self.object_reader.assets_file,
            self.m_StreamData.offset,
            self.m_StreamData.size,
        )

    # calculate the number of textures in the array
    texture_size = self.m_DataSize // self.m_Depth

    return [
        Texture2DConverter.parse_image_data(
            image_data[offset : offset + texture_size],
            self.m_Width,
            self.m_Height,
            texture_format,
            self.object_reader.version,
            0,
            None,
        )
        for offset in range(0, self.m_DataSize, texture_size)
    ]


Texture2DArray.images = property(_Texture2DArray_get_images)

__all__ = ("Texture2DArray",)
