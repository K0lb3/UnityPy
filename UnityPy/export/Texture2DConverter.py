from sys import platform

import tex2img
from PIL import Image

from ..enums import TextureFormat, BuildTarget

TF = TextureFormat
PREFER_BASISU = False


def get_image_from_texture2d(texture_2d, flip=True) -> Image:
    """converts the given texture into PIL.Image

    :param texture_2d: texture to be converterd
    :type texture_2d: Texture2D
    :param flip: flips the image back to the original (all Unity textures are flipped by default)
    :type flip: bool
    :return: PIL.Image object
    :rtype: Image
    """
    image_data = texture_2d.image_data
    texture_format = texture_2d.m_TextureFormat

    selection = CONV_TABLE[texture_format]

    if len(selection) == 0:
        raise NotImplementedError(f"Not implemented texture format: {texture_format.name}")

    if texture_format in XBOX_SWAP_FORMATS:
        image_data = swap_bytes_for_xbox(image_data, texture_2d.platform)

    if 'Crunched' in texture_format.name:
        image_data = tex2img.crunch_unpack_level(image_data, 0)

    img = selection[0](image_data, texture_2d.m_Width, texture_2d.m_Height, *selection[1:])

    if img and flip:
        return img.transpose(Image.FLIP_TOP_BOTTOM)
    return img


def swap_bytes_for_xbox(image_data: bytes, build_target: BuildTarget) -> bytes:
    """swaps the texture bytes
    This is required for textures deployed on XBOX360.

    :param image_data: texture data
    :type image_data: bytes
    :param build_target: platform of the asset
    :type build_target: BuildTarget
    :return: swapped data if platform = XBOX360 else data
    :rtype: bytes
    """
    if build_target == BuildTarget.XBOX360:  # swap bytes for Xbox confirmed,PS3 not encountered
        for i in range(0, len(image_data), 2):
            image_data[i:i + 2] = image_data[i:i + 2][::-1]
    return image_data


def pillow(image_data: bytes, width: int, height: int, mode: str, codec: str, args, swap=False) -> Image:
    img = Image.frombytes(mode, (width, height), image_data, codec, args)
    if swap:
        channels = img.split()
        img = Image.merge(mode, [channels[x] for x in swap])
    return img


def atc(image_data: bytes, width: int, height: int, alpha: bool) -> Image:
    image_data = tex2img.decompress_atc(image_data, width, height, alpha)
    mode = "RGBA" if alpha else "RGB"
    return Image.frombytes(mode, (width, height), image_data, "raw", mode)


def astc(image_data: bytes, width: int, height: int, block_size: tuple) -> Image:
    image_data = tex2img.decompress_astc(image_data, width, height, *block_size, False)
    return Image.frombytes("RGBA", (width, height), image_data, "raw", "RGBA")


def pvrtc(image_data: bytes, width: int, height: int, fmt: int):
    if platform == "darwin" or PREFER_BASISU:
        image_data = tex2img.decompress_pvrtc(image_data, width, height, False)
    else:
        image_data = tex2img.basisu_decompress(image_data, width, height, fmt)
    return Image.frombytes("RGBA", (width, height), image_data, "raw", "RGBA")


def etc(image_data: bytes, width: int, height: int, fmt: int):
    image_data = tex2img.decompress_etc(image_data, width, height, fmt)
    mode = "RGBA" if fmt > 1 else "RGB"
    return Image.frombytes(mode, (width, height), image_data, "raw", mode)



CONV_TABLE = {
    #FORMAT                #FUNC    #ARGS                    
 #----------------------- -------- -------- ------------ ----------------- ------------ ----------
(  TF.Alpha8,              pillow,  "RGBA",  "raw",       "A"                                   ),
(  TF.ARGB4444,            pillow,  "RGBA",  "raw",       "RGBA;4B",          (2,1,0,3)         ),
(  TF.RGB24,               pillow,  "RGB",   "raw",       "RGB"                                 ),
(  TF.RGBA32,              pillow,  "RGBA",  "raw",       "RGBA"                                ),
(  TF.ARGB32,              pillow,  "RGBA",  "raw",       "ARGB"                                ),
(  TF.RGB565,              pillow,  "RGB",   "raw",       "BGR;16"                              ),
(  TF.R16,                 pillow,  "RGB",   "raw",       "R;16"                                ),
(  TF.DXT1,                pillow,  "RGBA",  "bcn",       1                                     ),
(  TF.DXT5,                pillow,  "RGBA",  "bcn",       3                                     ),
(  TF.RGBA4444,            pillow,  "RGBA",  "raw",       'RGBA;4B',          (3,2,1,0)         ),
(  TF.BGRA32,              pillow,  "RGBA",  "raw",       "BGRA"                                ),
(  TF.RHalf,                                                                                    ),
(  TF.RGHalf,                                                                                   ),
(  TF.RGBAHalf,                                                                                 ),
(  TF.RFloat,              pillow,  "RGB",   "raw",       "RF"                                  ),
(  TF.RGFloat,                                                                                  ),
(  TF.RGBAFloat,           pillow,  "RGBA",  "raw",       "RGBAF"                               ),
(  TF.YUY2,                                                                                     ),
(  TF.RGB9e5Float,                                                                              ),
(  TF.BC4,                 pillow,  "L",     "bcn",       4                                     ),
(  TF.BC5,                 pillow,  "RGBA",  "bcn",       5                                     ),
(  TF.BC6H,                pillow,  "RGBA",  "bcn",       6                                     ),
(  TF.BC7,                 pillow,  "RGBA",  "bcn",       7                                     ),
(  TF.DXT1Crunched,        pillow,  "RGBA",  "bcn",       1                                     ),
(  TF.DXT5Crunched,        pillow,  "RGBA",  "bcn",       3                                     ),
(  TF.PVRTC_RGB2,          pvrtc,   11                                                          ),
(  TF.PVRTC_RGBA2,         pvrtc,   12                                                          ),
(  TF.PVRTC_RGB4,          pvrtc,   11                                                          ),
(  TF.PVRTC_RGBA4,         pvrtc,   12                                                          ),
(  TF.ETC_RGB4,            etc,     0                                                           ),
(  TF.ATC_RGB4,            atc,     False                                                       ),
(  TF.ATC_RGBA8,           atc,     True                                                        ),
(  TF.EAC_R,                                                                                    ),
(  TF.EAC_R_SIGNED,                                                                             ),
(  TF.EAC_RG,                                                                                   ),
(  TF.EAC_RG_SIGNED,                                                                            ),
(  TF.ETC2_RGB,            etc,     1                                                           ),
(  TF.ETC2_RGBA1,          etc,     4                                                           ),
(  TF.ETC2_RGBA8,          etc,     3                                                           ),
(  TF.ASTC_RGB_4x4,        astc,    (4,4)                                                       ),
(  TF.ASTC_RGB_5x5,        astc,    (5,5)                                                       ),
(  TF.ASTC_RGB_6x6,        astc,    (6,6)                                                       ),
(  TF.ASTC_RGB_8x8,        astc,    (8,8)                                                       ),
(  TF.ASTC_RGB_10x10,      astc,    (10,10)                                                     ),
(  TF.ASTC_RGB_12x12,      astc,    (12,12)                                                     ),
(  TF.ASTC_RGBA_4x4,       astc,    (4,4)                                                       ),
(  TF.ASTC_RGBA_5x5,       astc,    (5,5)                                                       ),
(  TF.ASTC_RGBA_6x6,       astc,    (6,6)                                                       ),
(  TF.ASTC_RGBA_8x8,       astc,    (8,8)                                                       ),
(  TF.ASTC_RGBA_10x10,     astc,    (10,10)                                                     ),
(  TF.ASTC_RGBA_12x12,     astc,    (12,12)                                                     ),
(  TF.ETC_RGB4_3DS,        etc,     0                                                           ),
(  TF.ETC_RGBA8_3DS,       etc,     3                                                           ),
(  TF.RG16,                                                                                     ),
(  TF.R8,                  pillow,  "RGB",   "raw",       "R"                                   ),
(  TF.ETC_RGB4Crunched,    etc,     0                                                           ),
(  TF.ETC2_RGBA8Crunched,  etc,     3                                                           ),
(  TF.ASTC_HDR_4x4,        astc,    (4,4)                                                           ),
(  TF.ASTC_HDR_5x5,        astc,    (5,5)                                                           ),
(  TF.ASTC_HDR_6x6,        astc,    (6,6)                                                           ),
(  TF.ASTC_HDR_8x8,        astc,    (8,8)                                                           ),
(  TF.ASTC_HDR_10x10,      astc,    (10,10)                                                          ),
(  TF.ASTC_HDR_12x12,      astc,    (12,12)                                                          ),
}

# format conv_table to a dict
CONV_TABLE = {
    line[0]: line[1:]
    for line in CONV_TABLE
}

# XBOX Swap Formats
XBOX_SWAP_FORMATS = [
    TF.RGB565,
    TF.DXT1,
    TF.DXT1Crunched,
    TF.DXT5,
    TF.DXT5Crunched
]
