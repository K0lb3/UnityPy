from types import SimpleNamespace

import pytest

import UnityPy
from UnityPy.classes.generated import GLTextureSettings, StreamingInfo, Texture2D, Texture2DArray
from UnityPy.enums import TextureFormat
from UnityPy.enums.GraphicsFormat import GraphicsFormat
from UnityPy.streams import EndianBinaryReader

VERSION = (2022, 3, 0, 0)


def object_reader():
    environment = UnityPy.Environment()

    def load_dependencies(possible_dependencies=None):
        raise AssertionError("no dependency should be loaded")

    assets_file = SimpleNamespace(environment=environment, load_dependencies=load_dependencies, _cache={})
    return SimpleNamespace(assets_file=assets_file, version=VERSION, platform=0)


def texture_settings():
    return GLTextureSettings(m_Aniso=1, m_FilterMode=1, m_MipBias=0.0, m_WrapMode=0)


def texture2d(width, height, image_data=b"", stream_path=""):
    texture = Texture2D(
        image_data=image_data,
        m_CompleteImageSize=len(image_data),
        m_ForcedFallbackFormat=0,
        m_Height=height,
        m_ImageCount=1,
        m_IsReadable=False,
        m_LightmapFormat=0,
        m_MipCount=1,
        m_Name="texture",
        m_TextureDimension=2,
        m_TextureFormat=TextureFormat.RGBA32,
        m_TextureSettings=texture_settings(),
        m_Width=width,
        m_StreamData=StreamingInfo(offset=0, path=stream_path, size=0),
    )
    texture.object_reader = object_reader()
    return texture


def test_texture2d_without_size():
    assert texture2d(0, 0).image.size == (0, 0)


def test_texture2d_without_image_data():
    with pytest.raises(ValueError):
        texture2d(2, 2).get_image_data()


ARRAY_LAYERS = [bytes([255, 0, 0, 255, 0, 255, 0, 255]), bytes([0, 0, 255, 255, 255, 255, 255, 255])]
ARRAY_PIXELS = [
    [(255, 0, 0, 255), (0, 255, 0, 255)],
    [(0, 0, 255, 255), (255, 255, 255, 255)],
]


def texture2darray(image_data=b"", stream_path=""):
    data_size = sum(len(layer) for layer in ARRAY_LAYERS)
    texture = Texture2DArray(
        image_data=image_data,
        m_ColorSpace=1,
        m_DataSize=data_size,
        m_Depth=len(ARRAY_LAYERS),
        m_Format=GraphicsFormat.R8G8B8A8_UNorm,
        m_Height=1,
        m_IsReadable=False,
        m_MipCount=1,
        m_Name="array",
        m_TextureSettings=texture_settings(),
        m_Width=2,
        m_StreamData=StreamingInfo(offset=4, path=stream_path, size=data_size if stream_path else 0),
    )
    texture.object_reader = object_reader()
    return texture


def array_pixels(texture):
    return [[image.getpixel((x, 0)) for x in range(2)] for image in texture.images]


def test_texture2darray_inline():
    assert array_pixels(texture2darray(image_data=b"".join(ARRAY_LAYERS))) == ARRAY_PIXELS


def test_texture2darray_streamed():
    # streamed arrays serialize an empty image_data and point at a resource file
    texture = texture2darray(stream_path="archive:/CAB-array/CAB-array.resS")
    resource = EndianBinaryReader(b"\0" * 4 + b"".join(ARRAY_LAYERS))
    texture.object_reader.assets_file.environment.register_cab("CAB-array.resS", resource)
    assert array_pixels(texture) == ARRAY_PIXELS
    assert texture.get_image_data() == b"".join(ARRAY_LAYERS)


def test_texture2darray_without_image_data():
    with pytest.raises(ValueError):
        texture2darray().get_image_data()
