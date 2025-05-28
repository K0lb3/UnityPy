# based on https://github.com/nesrak1/UABEA/blob/master/TexturePlugin/Texture2DSwitchDeswizzler.cs
from typing import Dict, Optional, Sequence, Tuple, Union

from UnityPy.enums import BuildTarget

from ..enums import TextureFormat as TF


PlatformBlobType = Union[bytes, Sequence[int]]


GOB_X_TEXEL_COUNT = 4
GOB_Y_TEXEL_COUNT = 8
TEXEL_BYTE_SIZE = 16
TEXELS_IN_GOB = GOB_X_TEXEL_COUNT * GOB_Y_TEXEL_COUNT
GOB_MAP = [
    (((l >> 3) & 0b10) | ((l >> 1) & 0b1), ((l >> 1) & 0b110) | (l & 0b1))
    for l in range(TEXELS_IN_GOB)
]


def _ceil_divide(a: int, b: int) -> int:
    return (a + b - 1) // b


def _deswizzle(
    data: bytes,
    width: int,
    height: int,
    block_width: int,
    block_height: int,
    texels_per_block: int,
) -> bytes:
    block_count_x = _ceil_divide(width, block_width)
    block_count_y = _ceil_divide(height, block_height)
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
                    dst_offset = (
                        (base_gob_dst_y + gob_y) * block_count_x
                        + (base_gob_dst_x + gob_x)
                    ) * TEXEL_BYTE_SIZE
                    new_data[dst_offset : dst_offset + TEXEL_BYTE_SIZE] = data_view[
                        :TEXEL_BYTE_SIZE
                    ]
                    data_view = data_view[TEXEL_BYTE_SIZE:]

    return bytes(new_data)


def _swizzle(
    data: bytes,
    width: int,
    height: int,
    block_width: int,
    block_height: int,
    texels_per_block: int,
) -> bytes:
    block_count_x = _ceil_divide(width, block_width)
    block_count_y = _ceil_divide(height, block_height)
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
                    src_offset = (
                        (base_gob_dst_y + gob_y) * block_count_x
                        + (base_gob_dst_x + gob_x)
                    ) * TEXEL_BYTE_SIZE
                    data_view[:TEXEL_BYTE_SIZE] = data[
                        src_offset : src_offset + TEXEL_BYTE_SIZE
                    ]
                    data_view = data_view[TEXEL_BYTE_SIZE:]

    return bytes(new_data)


def _get_padded_texture_size(
    width: int, height: int, block_width: int, block_height: int, texels_per_block: int
) -> Tuple[int, int]:
    width = (
        _ceil_divide(width, block_width * GOB_X_TEXEL_COUNT)
        * block_width
        * GOB_X_TEXEL_COUNT
    )
    height = (
        _ceil_divide(height, block_height * GOB_Y_TEXEL_COUNT * texels_per_block)
        * block_height
        * GOB_Y_TEXEL_COUNT
        * texels_per_block
    )
    return width, height


def _get_texels_per_block(platform_blob: PlatformBlobType) -> int:
    if not platform_blob:
        raise ValueError("Given platform_blob is empty")
    return 1 << int.from_bytes(platform_blob[8:12], "little")


# this should be the amount of pixels that can fit 16 bytes
TEXTURE_FORMAT_BLOCK_SIZE_MAP: Dict[TF, Tuple[int, int]] = {
    TF.Alpha8: (16, 1),  # 1 byte per pixel
    TF.ARGB4444: (8, 1),  # 2 bytes per pixel
    TF.RGBA32: (4, 1),  # 4 bytes per pixel
    TF.ARGB32: (4, 1),  # 4 bytes per pixel
    TF.ARGBFloat: (1, 1),  # 16 bytes per pixel (?)
    TF.RGB565: (8, 1),  # 2 bytes per pixel
    TF.R16: (8, 1),  # 2 bytes per pixel
    TF.DXT1: (8, 4),  # 8 bytes per 4x4=16 pixels
    TF.DXT5: (4, 4),  # 16 bytes per 4x4=16 pixels
    TF.RGBA4444: (8, 1),  # 2 bytes per pixel
    TF.BGRA32: (4, 1),  # 4 bytes per pixel
    TF.BC6H: (4, 4),  # 16 bytes per 4x4=16 pixels
    TF.BC7: (4, 4),  # 16 bytes per 4x4=16 pixels
    TF.BC4: (8, 4),  # 8 bytes per 4x4=16 pixels
    TF.BC5: (4, 4),  # 16 bytes per 4x4=16 pixels
    TF.ASTC_RGB_4x4: (4, 4),  # 16 bytes per 4x4=16 pixels
    TF.ASTC_RGB_5x5: (5, 5),  # 16 bytes per 5x5=25 pixels
    TF.ASTC_RGB_6x6: (6, 6),  # 16 bytes per 6x6=36 pixels
    TF.ASTC_RGB_8x8: (8, 8),  # 16 bytes per 8x8=64 pixels
    TF.ASTC_RGB_10x10: (10, 10),  # 16 bytes per 10x10=100 pixels
    TF.ASTC_RGB_12x12: (12, 12),  # 16 bytes per 12x12=144 pixels
    TF.ASTC_RGBA_4x4: (4, 4),  # 16 bytes per 4x4=16 pixels
    TF.ASTC_RGBA_5x5: (5, 5),  # 16 bytes per 5x5=25 pixels
    TF.ASTC_RGBA_6x6: (6, 6),  # 16 bytes per 6x6=36 pixels
    TF.ASTC_RGBA_8x8: (8, 8),  # 16 bytes per 8x8=64 pixels
    TF.ASTC_RGBA_10x10: (10, 10),  # 16 bytes per 10x10=100 pixels
    TF.ASTC_RGBA_12x12: (12, 12),  # 16 bytes per 12x12=144 pixels
    TF.RG16: (8, 1),  # 2 bytes per pixel
    TF.R8: (16, 1),  # 1 byte per pixel
}


def deswizzle(
    data: bytes,
    width: int,
    height: int,
    texture_format: TF,
    platform_blob: PlatformBlobType,
) -> bytes:
    block_size = TEXTURE_FORMAT_BLOCK_SIZE_MAP.get(texture_format)
    if not block_size:
        raise NotImplementedError(
            f"Not implemented swizzle format: {texture_format.name}"
        )
    texels_per_block = _get_texels_per_block(platform_blob)
    return _deswizzle(data, width, height, *block_size, texels_per_block)


def swizzle(
    data: bytes,
    width: int,
    height: int,
    texture_format: TF,
    platform_blob: PlatformBlobType,
) -> bytes:
    block_size = TEXTURE_FORMAT_BLOCK_SIZE_MAP.get(texture_format)
    if not block_size:
        raise NotImplementedError(
            f"Not implemented swizzle format: {texture_format.name}"
        )
    texels_per_block = _get_texels_per_block(platform_blob)
    return _swizzle(data, width, height, *block_size, texels_per_block)


def get_padded_image_size(
    width: int,
    height: int,
    texture_format: TF,
    platform_blob: PlatformBlobType,
):
    block_size = TEXTURE_FORMAT_BLOCK_SIZE_MAP.get(texture_format)
    if not block_size:
        raise NotImplementedError(
            f"Not implemented swizzle format: {texture_format.name}"
        )
    texels_per_block = _get_texels_per_block(platform_blob)
    return _get_padded_texture_size(width, height, *block_size, texels_per_block)


def is_switch_swizzled(
    platform: Union[BuildTarget, int], platform_blob: Optional[PlatformBlobType] = None
) -> bool:
    if platform != BuildTarget.Switch:
        return False
    if not platform_blob or len(platform_blob) < 12:
        return False
    gobs_per_block = _get_texels_per_block(platform_blob)
    return gobs_per_block > 1
