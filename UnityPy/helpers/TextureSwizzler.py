# based on https://github.com/nesrak1/UABEA/blob/master/TexturePlugin/Texture2DSwitchDeswizzler.cs
from typing import Dict, Tuple

from PIL import Image

from ..enums import TextureFormat

try:
    from ..UnityPyBoost import switch_deswizzle as switch_deswizzle_c
except:
    switch_deswizzle_c = None


GOB_X_BLOCK_COUNT = 4
GOB_Y_BLOCK_COUNT = 8
BLOCKS_IN_GOB = GOB_X_BLOCK_COUNT * GOB_Y_BLOCK_COUNT


def ceil_divide(a: int, b: int) -> int:
    return (a + b - 1) / b


def switch_deswizzle(
    src_image: Image.Image, block_size: Tuple[int, int], gobs_per_block: int
) -> Image.Image:
    src_bytes = src_image.tobytes()
    pixel_width = len(src_image.mode)

    if switch_deswizzle_c:
        dst_bytes = switch_deswizzle_c(
            src_bytes, pixel_width, *src_image.size, *block_size, gobs_per_block
        )
        return Image.frombytes(src_image.mode, src_image.size, dst_bytes)

    dst_bytes = bytearray(len(src_bytes))

    width, height = src_image.size
    block_width, block_height = block_size
    block_count_x = width // block_width
    block_count_y = height // block_height

    gob_count_x = block_count_x // GOB_X_BLOCK_COUNT
    gob_count_y = block_count_y // GOB_Y_BLOCK_COUNT

    src_x = 0
    src_y = 0

    block_pixel_width = block_width * pixel_width
    row_pixel_width = width * pixel_width
    data_size = len(src_bytes)

    GOB_MAP = [
        (((l >> 3) & 0b10) | ((l >> 1) & 0b1), ((l >> 1) & 0b110) | (l & 0b1))
        for l in range(BLOCKS_IN_GOB)
    ]

    for y in range(gob_count_y):
        for x in range(gob_count_x):
            for k in range(gobs_per_block):
                for gob_x, gob_y in GOB_MAP:
                    gob_dst_x = x * GOB_X_BLOCK_COUNT + gob_x
                    gob_dst_y = (y * gobs_per_block + k) * GOB_Y_BLOCK_COUNT + gob_y

                    src_offset = (
                        src_x * block_width + (src_y * block_height) * width
                    ) * pixel_width
                    dst_offset = (
                        gob_dst_x * block_width + (gob_dst_y * block_height) * width
                    ) * pixel_width

                    for by in range(block_height):
                        if dst_offset > data_size or src_offset > data_size:
                            break
                        copy_width = block_pixel_width
                        if (data_size - src_offset) < block_pixel_width:
                            copy_width = data_size - src_offset
                        elif (data_size - dst_offset) < block_pixel_width:
                            copy_width = data_size - dst_offset

                        dst_bytes[dst_offset : dst_offset + copy_width] = src_bytes[
                            src_offset : src_offset + copy_width
                        ]
                        src_offset += row_pixel_width
                        dst_offset += row_pixel_width

                    src_x += 1
                    if src_x >= block_count_x:
                        src_x = 0
                        src_y += 1

    return Image.frombytes(src_image.mode, src_image.size, dst_bytes)


def switch_swizzle(
    src_image: Image.Image, block_size: Tuple[int, int], gobs_per_block: int
) -> Image.Image:
    dstImage = Image.new(src_image.mode, src_image.size)

    blockCountX, blockCountY = map(ceil_divide, zip(src_image.size, block_size))

    gob_count_x = blockCountX / GOB_X_BLOCK_COUNT
    gob_count_y = blockCountY / GOB_Y_BLOCK_COUNT

    dstX = 0
    dstY = 0

    for i in range(gob_count_y):
        for j in range(gob_count_x):
            for k in range(gobs_per_block):
                for l in range(BLOCKS_IN_GOB):
                    # todo: use table for speedy boi
                    gobX = ((l >> 3) & 0b10) | ((l >> 1) & 0b1)
                    gobY = ((l >> 1) & 0b110) | (l & 0b1)
                    gobSrcX = j * GOB_X_BLOCK_COUNT + gobX
                    gobSrcY = (i * gobs_per_block + k) * GOB_Y_BLOCK_COUNT + gobY
                    CopyBlock(
                        src_image, dstImage, gobSrcX, gobSrcY, dstX, dstY, *block_size
                    )

                    dstX += 1
                    if dstX >= blockCountX:
                        dstX = 0
                        dstY += 1

    return dstImage


# this should be the amount of pixels that can fit 16 bytes
TEXTUREFORMAT_BLOCK_SIZE_MAP: Dict[TextureFormat, Tuple[int, int]] = {
    TextureFormat.Alpha8: [16, 1],  # 1 byte per pixel
    TextureFormat.ARGB4444: [8, 1],  # 2 bytes per pixel
    TextureFormat.RGBA32: [4, 1],  # 4 bytes per pixel
    TextureFormat.ARGB32: [4, 1],  # 4 bytes per pixel
    TextureFormat.ARGBFloat: [1, 1],  # 16 bytes per pixel (?)
    TextureFormat.RGB565: [8, 1],  # 2 bytes per pixel
    TextureFormat.R16: [8, 1],  # 2 bytes per pixel
    TextureFormat.DXT1: [8, 4],  # 8 bytes per 4x4=16 pixels
    TextureFormat.DXT5: [4, 4],  # 16 bytes per 4x4=16 pixels
    TextureFormat.RGBA4444: [8, 1],  # 2 bytes per pixel
    TextureFormat.BGRA32: [4, 1],  # 4 bytes per pixel
    TextureFormat.BC6H: [4, 4],  # 16 bytes per 4x4=16 pixels
    TextureFormat.BC7: [4, 4],  # 16 bytes per 4x4=16 pixels
    TextureFormat.BC4: [8, 4],  # 8 bytes per 4x4=16 pixels
    TextureFormat.BC5: [4, 4],  # 16 bytes per 4x4=16 pixels
    TextureFormat.ASTC_RGB_4x4: [4, 4],  # 16 bytes per 4x4=16 pixels
    TextureFormat.ASTC_RGB_5x5: [5, 5],  # 16 bytes per 5x5=25 pixels
    TextureFormat.ASTC_RGB_6x6: [6, 6],  # 16 bytes per 6x6=36 pixels
    TextureFormat.ASTC_RGB_8x8: [8, 8],  # 16 bytes per 8x8=64 pixels
    TextureFormat.ASTC_RGB_10x10: [10, 10],  # 16 bytes per 10x10=100 pixels
    TextureFormat.ASTC_RGB_12x12: [12, 12],  # 16 bytes per 12x12=144 pixels
    TextureFormat.ASTC_RGBA_4x4: [4, 4],  # 16 bytes per 4x4=16 pixels
    TextureFormat.ASTC_RGBA_5x5: [5, 5],  # 16 bytes per 5x5=25 pixels
    TextureFormat.ASTC_RGBA_6x6: [6, 6],  # 16 bytes per 6x6=36 pixels
    TextureFormat.ASTC_RGBA_8x8: [8, 8],  # 16 bytes per 8x8=64 pixels
    TextureFormat.ASTC_RGBA_10x10: [10, 10],  # 16 bytes per 10x10=100 pixels
    TextureFormat.ASTC_RGBA_12x12: [12, 12],  # 16 bytes per 12x12=144 pixels
    TextureFormat.RG16: [8, 1],  # 2 bytes per pixel
    TextureFormat.R8: [16, 1],  # 1 byte per pixel
}


def get_padded_texture_size(
    width: int, height: int, block_width: int, block_height: int, gobs_per_block: int
):
    width = (
        ceil_divide(width, block_width * GOB_X_BLOCK_COUNT)
        * block_width
        * GOB_X_BLOCK_COUNT
    )
    height = (
        ceil_divide(height, block_height * GOB_Y_BLOCK_COUNT * gobs_per_block)
        * block_height
        * GOB_Y_BLOCK_COUNT
        * gobs_per_block
    )
    return width, height


def get_switch_gobs_per_block(platform_blob: bytes) -> int:
    return 1 << int.from_bytes(platform_blob[8:12], "little")
