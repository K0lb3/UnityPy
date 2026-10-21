import struct

from UnityPy.enums import BuildTarget
from UnityPy.enums import TextureFormat as TF
from UnityPy.export.Texture2DConverter import parse_image_data

VERSION = (2021, 3, 56, 0)


def test_r16_decodes_high_byte_into_red():
    values = [0x0000, 0x1234, 0x7FFF, 0xFFFF]
    data = struct.pack("<4H", *values)

    img = parse_image_data(data, 2, 2, TF.R16, VERSION, BuildTarget.StandaloneWindows, flip=False)

    assert img.mode == "RGB"
    assert img.size == (2, 2)
    pixels = img.tobytes()
    assert list(pixels[0::3]) == [v >> 8 for v in values]
    assert not any(pixels[1::3]) and not any(pixels[2::3])
