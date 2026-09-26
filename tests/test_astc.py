import struct

import astc_encoder
import pytest

from UnityPy.enums import TextureFormat as TF
from UnityPy.export.Texture2DConverter import CONV_TABLE

# the colour astcenc returns for a block it cannot decode in the selected profile
ERROR_COLOUR = (255, 0, 255, 255)
WIDTH = HEIGHT = 24


def compress(profile, block_size, pixels):
    image = astc_encoder.ASTCImage(
        astc_encoder.ASTCType.F32, WIDTH, HEIGHT, 1, struct.pack(f"<{len(pixels)}f", *pixels)
    )
    config = astc_encoder.ASTCConfig(profile, *block_size, block_z=1, quality=100)
    return astc_encoder.ASTCContext(config).compress(image, astc_encoder.ASTCSwizzle.from_str("RGBA"))


def gradient(peak):
    """RGBA floats rising from left to right up to `peak` in red, half of that in green."""
    pixels = []
    for _ in range(HEIGHT):
        for x in range(WIDTH):
            v = peak * (x + 1) / WIDTH
            pixels += [v, v / 2, 0.1, 1.0]
    return pixels


def decode(texture_format, data):
    func, args = CONV_TABLE[texture_format]
    image = func(data, WIDTH, HEIGHT, *args)
    raw = image.tobytes()
    return [tuple(raw[i : i + 4]) for i in range(0, len(raw), 4)]


def expected(pixels):
    """The 8-bit values of the source floats, clamped to [0, 1]."""
    return [tuple(round(min(max(c, 0.0), 1.0) * 255) for c in pixels[i : i + 4]) for i in range(0, len(pixels), 4)]


def assert_close(decoded, source, tolerance):
    for got, want in zip(decoded, expected(source)):
        assert all(abs(g - w) <= tolerance for g, w in zip(got, want)), (got, want)


@pytest.mark.parametrize("block_size", [(4, 4), (5, 5), (6, 6), (8, 8), (10, 10), (12, 12)])
def test_astc_hdr(block_size):
    source = gradient(peak=2.0)
    data = compress(astc_encoder.ASTCProfile.HDR, block_size, source)
    decoded = decode(getattr(TF, f"ASTC_HDR_{block_size[0]}x{block_size[1]}"), data)
    assert ERROR_COLOUR not in decoded
    assert_close(decoded, source, tolerance=16)
    # values above 1.0 are clamped in the 8-bit image
    assert decoded[WIDTH - 1][0] == 255


@pytest.mark.parametrize("block_size", [(4, 4), (6, 6), (8, 8)])
def test_astc_ldr(block_size):
    source = gradient(peak=1.0)
    data = compress(astc_encoder.ASTCProfile.LDR, block_size, source)
    decoded = decode(getattr(TF, f"ASTC_RGBA_{block_size[0]}x{block_size[1]}"), data)
    assert_close(decoded, source, tolerance=4)
