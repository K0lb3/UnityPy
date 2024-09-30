from typing import Union, BinaryIO, Optional

from PIL import Image

from ..generated import Texture2D


def _Texture2d_get_image(self: Texture2D):
    from ...export import Texture2DConverter

    return Texture2DConverter.get_image_from_texture2d(self)


def _Texture2d_set_image(
    self: Texture2D,
    img: Union["Image.Image", str, BinaryIO],
    target_format: Optional[int] = None,
    mipmap_count: int = 1,
):
    from ...export import Texture2DConverter

    if not target_format:
        target_format = self.m_TextureFormat

    if not isinstance(img, Image.Image):
        img = Image.open(img)

    img_data, tex_format = Texture2DConverter.image_to_texture2d(img, target_format)
    self.m_Width = img.width
    self.m_Height = img.height

    if mipmap_count > 1:
        width = self.m_Width
        height = self.m_Height
        re_img = img
        for i in range(mipmap_count - 1):
            width //= 2
            height //= 2
            if width < 4 or height < 4:
                mipmap_count = i + 1
                break
            re_img = re_img.resize((width, height), Image.BICUBIC)
            img_data += Texture2DConverter.image_to_texture2d(re_img, target_format)[0]

    # disable mipmaps as we don't store them ourselves by default
    if self.m_MipMap is not None:
        self.m_MipMap = mipmap_count > 1
    if self.m_MipCount is not None:
        self.m_MipCount = mipmap_count

    self.image_data = img_data
    # width * height * channel count
    self.m_CompleteImageSize = len(
        img_data
    )  # img.width * img.height * len(img.getbands())
    self.m_TextureFormat = tex_format

    if self.m_StreamData is not None:
        self.m_StreamData.path = ""
        self.m_StreamData.offset = 0
        self.m_StreamData.size = 0


def _Texture2D_get_image_data(self: Texture2D):
    if self.image_data:
        return self.image_data
    if self.m_StreamData:
        from ...helpers.ResourceReader import get_resource_data

        return get_resource_data(
            self.m_StreamData.path,
            self.object_reader.assets_file,
            self.m_StreamData.offset,
            self.m_StreamData.size,
        )
    raise ValueError("No image data found")


Texture2D.image = property(_Texture2d_get_image, _Texture2d_set_image)
Texture2D.set_image = _Texture2d_set_image
Texture2D.get_image_data = _Texture2D_get_image_data


__all__ = ("Texture2D",)
