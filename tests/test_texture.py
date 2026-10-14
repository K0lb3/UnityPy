from types import SimpleNamespace

import pytest

import UnityPy
from UnityPy.classes.generated import GLTextureSettings, StreamingInfo, Texture2D
from UnityPy.enums import TextureFormat

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
