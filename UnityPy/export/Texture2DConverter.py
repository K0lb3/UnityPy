﻿import texture2ddecoder
import etcpak
from PIL import Image
from copy import copy
from io import BytesIO
import struct
from ..enums import TextureFormat, BuildTarget

TF = TextureFormat


def image_to_texture2d(img: Image.Image, target_texture_format: TF, flip: bool = True):
    if flip:
        img = img.transpose(Image.FLIP_TOP_BOTTOM)

    # DXT
    if target_texture_format in [TF.DXT1, TF.DXT1Crunched]:
        raw_img = img.convert("RGBA").tobytes()
        enc_img = etcpak.compress_to_dxt1(raw_img, img.width, img.height)
        tex_format = TF.DXT1
    elif target_texture_format in [TF.DXT5, TF.DXT5Crunched]:
        raw_img = img.convert("RGBA").tobytes()
        enc_img = etcpak.compress_to_dxt5(raw_img, img.width, img.height)
        tex_format = TF.DXT5
    # ETC
    elif target_texture_format in [TF.ETC_RGB4, TF.ETC_RGB4Crunched, TF.ETC_RGB4_3DS]:
        r, g, b, a = img.split()
        raw_img = Image.merge("RGBA", (b, g, r, a)).tobytes()
        enc_img = etcpak.compress_to_etc1(raw_img, img.width, img.height)
        tex_format = TF.ETC_RGB4
    elif target_texture_format == TF.ETC2_RGB:
        r, g, b, a = img.split()
        raw_img = Image.merge("RGBA", (b, g, r, a)).tobytes()
        enc_img = etcpak.compress_to_etc2_rgb(raw_img, img.width, img.height)
        tex_format = TF.ETC2_RGB
    elif (
        target_texture_format in [TF.ETC2_RGBA8, TF.ETC2_RGBA8Crunched, TF.ETC2_RGBA1]
        or "_RGB_" in target_texture_format.name
    ):
        r, g, b, a = img.split()
        raw_img = Image.merge("RGBA", (b, g, r, a)).tobytes()
        enc_img = etcpak.compress_to_etc2_rgba(raw_img, img.width, img.height)
        tex_format = TF.ETC2_RGBA8
    # A
    elif target_texture_format == TF.Alpha8:
        enc_img = img.tobytes("raw", "A")
        tex_format = TF.Alpha8
    # R - should probably be moerged into #A, as pure R is used as Alpha
    # but need test data for this first
    elif target_texture_format in [
        TF.R8,
        TF.R16,
        TF.RHalf,
        TF.RFloat,
        TF.EAC_R,
        TF.EAC_R_SIGNED,
    ]:
        enc_img = img.tobytes("raw", "R")
        tex_format = TF.R8
    # RGBA
    elif target_texture_format in [
        TF.RGB565,
        TF.RGB24,
        TF.RGB9e5Float,
        TF.PVRTC_RGB2,
        TF.PVRTC_RGB4,
        TF.ATC_RGB4,
    ]:
        enc_img = img.tobytes("raw", "RGB")
        tex_format = TF.RGB24
    # everything else defaulted to RGBA
    else:
        enc_img = img.tobytes("raw", "RGBA")
        tex_format = TF.RGBA32

    return enc_img, tex_format


def get_image_from_texture2d(texture_2d, flip=True) -> Image.Image:
    """converts the given texture into PIL.Image

    :param texture_2d: texture to be converterd
    :type texture_2d: Texture2D
    :param flip: flips the image back to the original (all Unity textures are flipped by default)
    :type flip: bool
    :return: PIL.Image object
    :rtype: Image
    """
    image_data = copy(bytes(texture_2d.image_data))
    if not image_data:
        return Image.new("RGB", (0, 0))

    texture_format = (
        texture_2d.m_TextureFormat
        if isinstance(texture_2d.m_TextureFormat, TF)
        else TF(texture_2d.m_TextureFormat)
    )
    selection = CONV_TABLE[texture_format]

    if len(selection) == 0:
        raise NotImplementedError(
            f"Not implemented texture format: {texture_format.name}"
        )

    if texture_format in XBOX_SWAP_FORMATS:
        image_data = swap_bytes_for_xbox(image_data, texture_2d.platform)

    if "Crunched" in texture_format.name:
        version = texture_2d.version
        if (
            version[0] > 2017
            or (version[0] == 2017 and version[1] >= 3)  # 2017.3 and up
            or texture_format == TF.ETC_RGB4Crunched
            or texture_format == TF.ETC2_RGBA8Crunched
        ):
            image_data = texture2ddecoder.unpack_unity_crunch(image_data)
        else:
            image_data = texture2ddecoder.unpack_crunch(image_data)

    img = selection[0](
        image_data, texture_2d.m_Width, texture_2d.m_Height, *selection[1:]
    )

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
    if (
        build_target == BuildTarget.XBOX360
    ):  # swap bytes for Xbox confirmed,PS3 not encountered
        for i in range(0, len(image_data), 2):
            image_data[i : i + 2] = image_data[i : i + 2][::-1]
    return image_data


def pillow(
    image_data: bytes,
    width: int,
    height: int,
    mode: str,
    codec: str,
    args,
    swap: tuple = None,
) -> Image.Image:
    img = (
        Image.frombytes(mode, (width, height), image_data, codec, args)
        if width
        else Image.new(mode, (width, height))
    )
    if swap:
        channels = img.split()
        img = Image.merge(mode, [channels[x] for x in swap])
    return img


def atc(image_data: bytes, width: int, height: int, alpha: bool) -> Image.Image:
    if alpha:
        image_data = texture2ddecoder.decode_atc_rgba8(image_data, width, height)
    else:
        image_data = texture2ddecoder.decode_atc_rgb4(image_data, width, height)

    return Image.frombytes("RGBA", (width, height), image_data, "raw", "BGRA")


def astc(image_data: bytes, width: int, height: int, block_size: tuple) -> Image.Image:
    image_data = texture2ddecoder.decode_astc(image_data, width, height, *block_size)
    return Image.frombytes("RGBA", (width, height), image_data, "raw", "BGRA")


def pvrtc(image_data: bytes, width: int, height: int, fmt: bool):
    image_data = texture2ddecoder.decode_pvrtc(image_data, width, height, fmt)
    return Image.frombytes("RGBA", (width, height), image_data, "raw", "BGRA")


def etc(image_data: bytes, width: int, height: int, fmt: list):
    if fmt[0] == 1:
        image_data = texture2ddecoder.decode_etc1(image_data, width, height)
    elif fmt[0] == 2:
        if fmt[1] == "RGB":
            image_data = texture2ddecoder.decode_etc2(image_data, width, height)
        elif fmt[1] == "A1":
            image_data = texture2ddecoder.decode_etc2a1(image_data, width, height)
        elif fmt[1] == "A8":
            image_data = texture2ddecoder.decode_etc2a8(image_data, width, height)
    else:
        raise NotImplementedError("unknown etc mode")
    return Image.frombytes("RGBA", (width, height), image_data, "raw", "BGRA")


def eac(image_data: bytes, width: int, height: int, fmt: list):
    if fmt == "EAC_R":
        image_data = texture2ddecoder.decode_eacr(image_data, width, height)
    elif fmt == "EAC_R_SIGNED":
        image_data = texture2ddecoder.decode_eacr_signed(image_data, width, height)
    elif fmt == "EAC_RG":
        image_data = texture2ddecoder.decode_eacrg(image_data, width, height)
    elif fmt == "EAC_RG_SIGNED":
        image_data = texture2ddecoder.decode_eacrg_signed(image_data, width, height)
    return Image.frombytes("RGBA", (width, height), image_data, "raw", "BGRA")


def half(
    image_data: bytes,
    width: int,
    height: int,
    mode: str,
    codec: str,
    args,
    swap: tuple = None,
) -> Image.Image:
    # convert half-float to int8
    stream = BytesIO(image_data)
    image_data = bytes(
        int(struct.unpack("e", stream.read(2))[0] * 256)
        for _ in range(width * height * len(codec))
    )
    return pillow(image_data, width, height, mode, codec, args, swap)


CONV_TABLE = {
#  FORMAT                  FUNC     #ARGS.....
#----------------------- -------- -------- ------------ ----------------- ------------ ----------
(  TF.Alpha8,              pillow,  "RGBA",  "raw",       "A"                                   ),
(  TF.ARGB4444,            pillow,  "RGBA",  "raw",       "RGBA;4B",          (2,1,0,3)         ),
(  TF.RGB24,               pillow,  "RGB",   "raw",       "RGB"                                 ),
(  TF.RGBA32,              pillow,  "RGBA",  "raw",       "RGBA"                                ),
(  TF.ARGB32,              pillow,  "RGBA",  "raw",       "ARGB"                                ),
(  TF.RGB565,              pillow,  "RGB",   "raw",       "BGR;16"                              ),
(  TF.R8,                  pillow,  "RGB",   "raw",       "R"                                   ),
(  TF.R16,                 pillow,  "RGB",   "raw",       "R;16"                                ),
(  TF.RG16,                                                                                     ),
(  TF.DXT1,                pillow,  "RGBA",  "bcn",       1                                     ),
(  TF.DXT5,                pillow,  "RGBA",  "bcn",       3                                     ),
(  TF.RGBA4444,            pillow,  "RGBA",  "raw",       'RGBA;4B',          (3,2,1,0)         ),
(  TF.BGRA32,              pillow,  "RGBA",  "raw",       "BGRA"                                ),
(  TF.RHalf,               half,    "R",     "raw",       "R"                                   ),
(  TF.RGHalf,                                                                                   ),
(  TF.RGBAHalf,            half,    "RGB",   "raw",       "RGB"                                 ),
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
(  TF.PVRTC_RGB2,          pvrtc,   True                                                       ),
(  TF.PVRTC_RGBA2,         pvrtc,   True                                                        ),
(  TF.PVRTC_RGB4,          pvrtc,   False                                                       ),
(  TF.PVRTC_RGBA4,         pvrtc,   False                                                        ),
(  TF.ETC_RGB4,            etc,     (1,)                                                        ),
(  TF.ATC_RGB4,            atc,     False                                                       ),
(  TF.ATC_RGBA8,           atc,     True                                                        ),
(  TF.EAC_R,               eac,     "EAC_R"                                                     ),
(  TF.EAC_R_SIGNED,        eac,     "EAC_R:SIGNED"                                              ),
(  TF.EAC_RG,              eac,     "EAC_RG"                                                    ),
(  TF.EAC_RG_SIGNED,       eac,     "EAC_RG_SIGNED"                                             ),
(  TF.ETC2_RGB,            etc,     (2,"RGB")                                                   ),
(  TF.ETC2_RGBA1,          etc,     (2, "A1")                                                   ),
(  TF.ETC2_RGBA8,          etc,     (2, "A8")                                                   ),
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
(  TF.ETC_RGB4_3DS,        etc,     (1,)                                                        ),
(  TF.ETC_RGBA8_3DS,       etc,     (1,)                                                        ),
(  TF.ETC_RGB4Crunched,    etc,     (1,)                                                        ),
(  TF.ETC2_RGBA8Crunched,  etc,     (2, "A8")                                                   ),
(  TF.ASTC_HDR_4x4,        astc,    (4,4)                                                       ),
(  TF.ASTC_HDR_5x5,        astc,    (5,5)                                                       ),
(  TF.ASTC_HDR_6x6,        astc,    (6,6)                                                       ),
(  TF.ASTC_HDR_8x8,        astc,    (8,8)                                                       ),
(  TF.ASTC_HDR_10x10,      astc,    (10,10)                                                     ),
(  TF.ASTC_HDR_12x12,      astc,    (12,12)                                                     ),
}

# format conv_table to a dict
CONV_TABLE = {line[0]: line[1:] for line in CONV_TABLE}

# XBOX Swap Formats
XBOX_SWAP_FORMATS = [TF.RGB565, TF.DXT1, TF.DXT1Crunched, TF.DXT5, TF.DXT5Crunched]
