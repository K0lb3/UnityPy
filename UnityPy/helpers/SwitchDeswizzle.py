# based on https://github.com/nesrak1/UABEA/blob/master/TexturePlugin/Texture2DSwitchDeswizzler.cs
from typing import Dict, Tuple

from PIL import Image

from ..enums import TextureFormat


GOB_X_BLOCK_COUNT = 4
GOB_Y_BLOCK_COUNT = 8
BLOCKS_IN_GOB = GOB_X_BLOCK_COUNT * GOB_Y_BLOCK_COUNT


def CeilDivide(a: int, b: int) -> int:
    return (a + b - 1) / b


def CopyBlock(
    srcImage: Image.Image,
    dstImage: Image.Image,
    sbx: int,
    sby: int,
    dbx: int,
    dby: int,
    blockSizeW: int,
    blockSizeH: int,
):
    srcBlock = srcImage.crop(
        sbx * blockSizeW,
        sby * blockSizeH,
        sbx * blockSizeH + blockSizeW,
        sby * blockSizeH + blockSizeH,
    )
    dstImage.paste(srcBlock, (dbx * blockSizeW, dby * blockSizeH))


def SwitchDeswizzle(
    srcImage: Image.Image, blockSize: Tuple[int, int], gobsPerBlock: int
) -> Image.Image:
    dstImage = Image.new(srcImage.mode, srcImage.size)

    blockCountX, blockCountY = map(CeilDivide, zip(srcImage.size, blockSize))

    gobCountX = blockCountX / GOB_X_BLOCK_COUNT
    gobCountY = blockCountY / GOB_Y_BLOCK_COUNT

    srcX = 0
    srcY = 0

    for i in range(gobCountY):
        for j in range(gobCountX):
            for k in range(gobsPerBlock):
                for l in range(BLOCKS_IN_GOB):
                    # todo: use table for speedy boi
                    gobX = ((l >> 3) & 0b10) | ((l >> 1) & 0b1)
                    gobY = ((l >> 1) & 0b110) | (l & 0b1)
                    gobDstX = j * GOB_X_BLOCK_COUNT + gobX
                    gobDstY = (i * gobsPerBlock + k) * GOB_Y_BLOCK_COUNT + gobY
                    CopyBlock(
                        srcImage, dstImage, srcX, srcY, gobDstX, gobDstY, *blockSize
                    )

                    srcX += 1
                    if srcX >= blockCountX:
                        srcX = 0
                        srcY += 1

    return dstImage


def SwitchSwizzle(
    srcImage: Image.Image, blockSize: Tuple[int, int], gobsPerBlock: int
) -> Image.Image:
    dstImage = Image.new(srcImage.mode, srcImage.size)

    blockCountX, blockCountY = map(CeilDivide, zip(srcImage.size, blockSize))

    gobCountX = blockCountX / GOB_X_BLOCK_COUNT
    gobCountY = blockCountY / GOB_Y_BLOCK_COUNT

    dstX = 0
    dstY = 0

    for i in range(gobCountY):
        for j in range(gobCountX):
            for k in range(gobsPerBlock):
                for l in range(BLOCKS_IN_GOB):
                    # todo: use table for speedy boi
                    gobX = ((l >> 3) & 0b10) | ((l >> 1) & 0b1)
                    gobY = ((l >> 1) & 0b110) | (l & 0b1)
                    gobSrcX = j * GOB_X_BLOCK_COUNT + gobX
                    gobSrcY = (i * gobsPerBlock + k) * GOB_Y_BLOCK_COUNT + gobY
                    CopyBlock(
                        srcImage, dstImage, gobSrcX, gobSrcY, dstX, dstY, *blockSize
                    )

                    dstX += 1
                    if dstX >= blockCountX:
                        dstX = 0
                        dstY += 1

    return dstImage


# this should be the amount of pixels that can fit 16 bytes
TextureFormatBlockSizeMap: Dict[TextureFormat, Tuple[int, int]] = {
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


def GetPaddedTextureSize(
    width: int, height: int, blockWidth: int, blockHeight: int, gobsPerBlock: int
):
    width = (
        CeilDivide(width, blockWidth * GOB_X_BLOCK_COUNT)
        * blockWidth
        * GOB_X_BLOCK_COUNT
    )
    height = (
        CeilDivide(height, blockHeight * GOB_Y_BLOCK_COUNT * gobsPerBlock)
        * blockHeight
        * GOB_Y_BLOCK_COUNT
        * gobsPerBlock
    )
    return width, height


def GetSwitchGobsPerBlock(platformBlob: bytes) -> int:
    return 1 << int.from_bytes(platformBlob[:8], "little")
