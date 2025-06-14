# based on https://github.com/nesrak1/AssetsTools.NET/blob/dev/AssetsTools.NET.Texture/Swizzle/SwitchSwizzle.cs
from typing import Dict, List, Optional, Tuple, Union

from ..enums import BuildTarget, TextureFormat

GOB_X_TEXEL_COUNT = 4
GOB_Y_TEXEL_COUNT = 8
TEXEL_BYTE_SIZE = 16
TEXELS_IN_GOB = GOB_X_TEXEL_COUNT * GOB_Y_TEXEL_COUNT
GOB_MAP = [(((v >> 3) & 0b10) | ((v >> 1) & 0b1), ((v >> 1) & 0b110) | (v & 0b1)) for v in range(TEXELS_IN_GOB)]


def ceil_divide(a: int, b: int) -> int:
    return (a + b - 1) // b


def deswizzle(
    data: Union[bytes, bytearray, memoryview],
    width: int,
    height: int,
    block_width: int,
    block_height: int,
    texels_per_block: int,
) -> bytearray:
    block_count_x = ceil_divide(width, block_width)
    block_count_y = ceil_divide(height, block_height)
    gob_count_x = block_count_x // GOB_X_TEXEL_COUNT
    gob_count_y = block_count_y // GOB_Y_TEXEL_COUNT
    new_data = bytearray(len(data))
    data_view = memoryview(data)

    for i in range(gob_count_y // texels_per_block):
        for j in range(gob_count_x):
            base_gob_dst_x = j * 4
            for k in range(texels_per_block):
                base_gob_dst_y = (i * texels_per_block + k) * GOB_Y_TEXEL_COUNT
                for gob_x, gob_y in GOB_MAP:
                    dst_offset = ((base_gob_dst_y + gob_y) * block_count_x + (base_gob_dst_x + gob_x)) * TEXEL_BYTE_SIZE
                    new_data[dst_offset : dst_offset + TEXEL_BYTE_SIZE] = data_view[:TEXEL_BYTE_SIZE]
                    data_view = data_view[TEXEL_BYTE_SIZE:]
    return new_data


def swizzle(
    data: Union[bytes, bytearray, memoryview],
    width: int,
    height: int,
    block_width: int,
    block_height: int,
    texels_per_block: int,
) -> bytearray:
    block_count_x = ceil_divide(width, block_width)
    block_count_y = ceil_divide(height, block_height)
    gob_count_x = block_count_x // GOB_X_TEXEL_COUNT
    gob_count_y = block_count_y // GOB_Y_TEXEL_COUNT
    new_data = bytearray(len(data))
    data_view = memoryview(new_data)

    for i in range(gob_count_y // texels_per_block):
        for j in range(gob_count_x):
            base_gob_dst_x = j * 4
            for k in range(texels_per_block):
                base_gob_dst_y = (i * texels_per_block + k) * GOB_Y_TEXEL_COUNT
                for gob_x, gob_y in GOB_MAP:
                    src_offset = ((base_gob_dst_y + gob_y) * block_count_x + (base_gob_dst_x + gob_x)) * TEXEL_BYTE_SIZE
                    data_view[:TEXEL_BYTE_SIZE] = data[src_offset : src_offset + TEXEL_BYTE_SIZE]
                    data_view = data_view[TEXEL_BYTE_SIZE:]

    return new_data


# this should be the amount of pixels that can fit 16 bytes
TEXTURE_FORMAT_BLOCK_SIZE_MAP: Dict[TextureFormat, Tuple[int, int]] = {
    TextureFormat.Alpha8: (16, 1),  # 1 byte per pixel
    TextureFormat.ARGB4444: (8, 1),  # 2 bytes per pixel
    TextureFormat.RGBA32: (4, 1),  # 4 bytes per pixel
    TextureFormat.ARGB32: (4, 1),  # 4 bytes per pixel
    TextureFormat.ARGBFloat: (1, 1),  # 16 bytes per pixel (?)
    TextureFormat.RGB565: (8, 1),  # 2 bytes per pixel
    TextureFormat.R16: (8, 1),  # 2 bytes per pixel
    TextureFormat.DXT1: (8, 4),  # 8 bytes per 4x4=16 pixels
    TextureFormat.DXT5: (4, 4),  # 16 bytes per 4x4=16 pixels
    TextureFormat.RGBA4444: (8, 1),  # 2 bytes per pixel
    TextureFormat.BGRA32: (4, 1),  # 4 bytes per pixel
    TextureFormat.BC6H: (4, 4),  # 16 bytes per 4x4=16 pixels
    TextureFormat.BC7: (4, 4),  # 16 bytes per 4x4=16 pixels
    TextureFormat.BC4: (8, 4),  # 8 bytes per 4x4=16 pixels
    TextureFormat.BC5: (4, 4),  # 16 bytes per 4x4=16 pixels
    TextureFormat.ASTC_RGB_4x4: (4, 4),  # 16 bytes per 4x4=16 pixels
    TextureFormat.ASTC_RGB_5x5: (5, 5),  # 16 bytes per 5x5=25 pixels
    TextureFormat.ASTC_RGB_6x6: (6, 6),  # 16 bytes per 6x6=36 pixels
    TextureFormat.ASTC_RGB_8x8: (8, 8),  # 16 bytes per 8x8=64 pixels
    TextureFormat.ASTC_RGB_10x10: (10, 10),  # 16 bytes per 10x10=100 pixels
    TextureFormat.ASTC_RGB_12x12: (12, 12),  # 16 bytes per 12x12=144 pixels
    TextureFormat.ASTC_RGBA_4x4: (4, 4),  # 16 bytes per 4x4=16 pixels
    TextureFormat.ASTC_RGBA_5x5: (5, 5),  # 16 bytes per 5x5=25 pixels
    TextureFormat.ASTC_RGBA_6x6: (6, 6),  # 16 bytes per 6x6=36 pixels
    TextureFormat.ASTC_RGBA_8x8: (8, 8),  # 16 bytes per 8x8=64 pixels
    TextureFormat.ASTC_RGBA_10x10: (10, 10),  # 16 bytes per 10x10=100 pixels
    TextureFormat.ASTC_RGBA_12x12: (12, 12),  # 16 bytes per 12x12=144 pixels
    TextureFormat.RG16: (8, 1),  # 2 bytes per pixel
    TextureFormat.R8: (16, 1),  # 1 byte per pixel
}


def get_padded_texture_size(width: int, height: int, block_width: int, block_height: int, texels_per_block: int):
    width = ceil_divide(width, block_width * GOB_X_TEXEL_COUNT) * block_width * GOB_X_TEXEL_COUNT
    height = (
        ceil_divide(height, block_height * GOB_Y_TEXEL_COUNT * texels_per_block)
        * block_height
        * GOB_Y_TEXEL_COUNT
        * texels_per_block
    )
    return width, height


def get_switch_gobs_per_block(platform_blob: List[int]) -> int:
    return 1 << int.from_bytes(platform_blob[8:12], "little")


def is_switch_swizzled(platform: Union[BuildTarget, int], platform_blob: Optional[List[int]]) -> bool:
    if platform != BuildTarget.Switch:
        return False
    if not platform_blob or len(platform_blob) < 12:
        return False
    gobs_per_block = get_switch_gobs_per_block(platform_blob)
    return gobs_per_block > 1
