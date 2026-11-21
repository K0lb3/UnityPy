import struct

import pytest

from UnityPy.enums import TextureFormat as TF
from UnityPy.export.Texture2DConverter import parse_image_data

VERSION = (2022, 3, 0, 0)


def decode(name, texel):
    image = parse_image_data(texel * 4, 2, 2, getattr(TF, name), VERSION, 0)
    return image.mode, image.getpixel((0, 0))


# format: (one texel, expected 8-bit pixel)
# Signed formats are SNORM: [-1, 1] is mapped to [0, 255], so 0 -> 128,
# 64/127 -> 192 and -64/127 -> 63 (16-bit: 16384/32767 -> 191, -16384 -> 64).
TEXELS = {
    "RG16": (bytes([0x80, 0x40]), ("RGB", (128, 64, 0))),
    "RG32": (struct.pack("<2H", 0x8000, 0x4000), ("RGB", (128, 64, 0))),
    "RHalf": (struct.pack("<e", 0.5), ("RGB", (128, 0, 0))),
    "RGHalf": (struct.pack("<2e", 0.5, 0.25), ("RGB", (128, 64, 0))),
    "RGBAHalf": (struct.pack("<4e", 0.5, 0.25, 0.0, 1.0), ("RGBA", (128, 64, 0, 255))),
    "RFloat": (struct.pack("<f", 0.5), ("RGB", (128, 0, 0))),
    "RGFloat": (struct.pack("<2f", 0.5, 0.25), ("RGB", (128, 64, 0))),
    "RGBAFloat": (struct.pack("<4f", 0.5, 0.25, 0.0, 1.0), ("RGBA", (128, 64, 0, 255))),
    "ARGBFloat": (struct.pack("<4f", 1.0, 0.5, 0.25, 0.0), ("RGBA", (128, 64, 0, 255))),
    # R = G = 256 * 2**(15 - 24) = 0.5, B = 128 * 2**(15 - 24) = 0.25
    "RGB9e5Float": (
        struct.pack("<I", (15 << 27) | (128 << 18) | (256 << 9) | 256),
        ("RGB", (128, 128, 64)),
    ),
    "R8_SIGNED": (struct.pack("<b", 64), ("RGB", (192, 0, 0))),
    "RG16_SIGNED": (struct.pack("<2b", 64, -64), ("RGB", (192, 63, 0))),
    "RGB24_SIGNED": (struct.pack("<3b", 64, -64, 0), ("RGB", (192, 63, 128))),
    "RGBA32_SIGNED": (struct.pack("<4b", 64, -64, 0, 127), ("RGBA", (192, 63, 128, 255))),
    "R16_SIGNED": (struct.pack("<h", 16384), ("RGB", (191, 0, 0))),
    "RG32_SIGNED": (struct.pack("<2h", 16384, -16384), ("RGB", (191, 64, 0))),
    "RGB48_SIGNED": (struct.pack("<3h", 16384, -16384, 0), ("RGB", (191, 64, 128))),
    "RGBA64_SIGNED": (struct.pack("<4h", 16384, -16384, 0, 32767), ("RGBA", (191, 64, 128, 255))),
}


@pytest.mark.parametrize("name", sorted(TEXELS))
def test_uncompressed_formats(name):
    texel, expected = TEXELS[name]
    assert decode(name, texel) == expected


def test_half_alpha_not_shifted():
    # regression: RGBAHalf used to drop alpha and shift the channels
    assert decode("RGBAHalf", struct.pack("<4e", 0.5, 0.25, 0.0, 0.5)) == ("RGBA", (128, 64, 0, 128))


def test_float_values_outside_unit_range_are_clamped():
    assert decode("RGBAFloat", struct.pack("<4f", 2.0, -1.0, 0.5, 1.0)) == ("RGBA", (255, 0, 128, 255))
    assert decode("RHalf", struct.pack("<e", 2.0)) == ("RGB", (255, 0, 0))


def test_signed_minimum_maps_to_zero():
    assert decode("R8_SIGNED", struct.pack("<b", -128)) == ("RGB", (0, 0, 0))
    assert decode("R16_SIGNED", struct.pack("<h", -32768)) == ("RGB", (0, 0, 0))
