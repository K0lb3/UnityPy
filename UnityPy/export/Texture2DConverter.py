from __future__ import annotations

import struct
from io import BytesIO
from threading import Lock
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple, Union

import astc_encoder
import texture2ddecoder
from PIL import Image

from ..enums import BuildTarget, TextureFormat
from ..helpers import TextureSwizzler

if TYPE_CHECKING:
    from ..classes import Texture2D


TF = TextureFormat

TEXTURE_FORMAT_BLOCK_SIZE_TABLE: Dict[TF, Optional[Tuple[int, int]]] = {}
for tf in TF:
    if tf.name.startswith("ASTC"):
        split = tf.name.rsplit("_", 1)[1].split("x")
        block_size = (int(split[0]), int(split[1]))
    elif tf.name.startswith(("DXT", "BC", "ETC", "EAC")):
        block_size = (4, 4)
    elif tf.name.startswith("PVRTC"):
        block_size = (8 if tf.name.endswith("2") else 4, 4)
    else:
        block_size = None
    TEXTURE_FORMAT_BLOCK_SIZE_TABLE[tf] = block_size


def get_compressed_image_size(width: int, height: int, texture_format: TextureFormat):
    block_size = TEXTURE_FORMAT_BLOCK_SIZE_TABLE[texture_format]
    if block_size is None:
        return (width, height)
    block_width, block_height = block_size

    def pad(value: int, pad_by: int) -> int:
        to_pad = value % pad_by
        if to_pad:
            value += pad_by - to_pad
        return value

    width = pad(width, block_width)
    height = pad(height, block_height)
    return width, height


def pad_image(img: Image.Image, pad_width: int, pad_height: int) -> Image.Image:
    ori_width, ori_height = img.size
    if pad_width == ori_width and pad_height == ori_height:
        return img

    # Paste the original image at the top-left corner
    pad_img = Image.new(img.mode, (pad_width, pad_height))
    pad_img.paste(img, (0, 0))

    # Fill the right border: duplicate the last column
    if pad_width != ori_width:
        right_strip = img.crop((ori_width - 1, 0, ori_width, ori_height))
        right_strip = right_strip.resize((pad_width - ori_width, ori_height), resample=Image.Resampling.NEAREST)
        pad_img.paste(right_strip, (ori_width, 0))

    # Fill the bottom border: duplicate the last row
    if pad_height != ori_height:
        bottom_strip = img.crop((0, ori_height - 1, ori_width, ori_height))
        bottom_strip = bottom_strip.resize((ori_width, pad_height - ori_height), resample=Image.Resampling.NEAREST)
        pad_img.paste(bottom_strip, (0, ori_height))

    # Fill the bottom-right corner with the bottom-right pixel
    if pad_width != ori_width and pad_height != ori_height:
        corner = img.getpixel((ori_width - 1, ori_height - 1))
        corner_img = Image.new(img.mode, (pad_width - ori_width, pad_height - ori_height), color=corner)
        pad_img.paste(corner_img, (ori_width, ori_height))

    return pad_img


def compress_etcpak(data: bytes, width: int, height: int, target_texture_format: TextureFormat) -> bytes:
    import etcpak

    if target_texture_format in [TF.DXT1, TF.DXT1Crunched]:
        return etcpak.compress_bc1(data, width, height)
    elif target_texture_format in [TF.DXT5, TF.DXT5Crunched]:
        return etcpak.compress_bc3(data, width, height)
    elif target_texture_format == TF.BC4:
        return etcpak.compress_bc4(data, width, height)
    elif target_texture_format == TF.BC5:
        return etcpak.compress_bc5(data, width, height)
    elif target_texture_format == TF.BC7:
        return etcpak.compress_bc7(data, width, height, None)
    elif target_texture_format in [TF.ETC_RGB4, TF.ETC_RGB4Crunched, TF.ETC_RGB4_3DS]:
        return etcpak.compress_etc1_rgb(data, width, height)
    elif target_texture_format == TF.ETC2_RGB:
        return etcpak.compress_etc2_rgb(data, width, height)
    elif target_texture_format in [TF.ETC2_RGBA8, TF.ETC2_RGBA8Crunched, TF.ETC2_RGBA1]:
        return etcpak.compress_etc2_rgba(data, width, height)
    else:
        raise NotImplementedError(f"etcpak has no compress function for {target_texture_format.name}")


def compress_astc(data: bytes, width: int, height: int, target_texture_format: TextureFormat) -> bytes:
    astc_image = astc_encoder.ASTCImage(astc_encoder.ASTCType.U8, width, height, 1, data)
    block_size = TEXTURE_FORMAT_BLOCK_SIZE_TABLE[target_texture_format]
    assert block_size is not None, f"failed to get block size for {target_texture_format.name}"
    swizzle = astc_encoder.ASTCSwizzle.from_str("RGBA")

    context, lock = get_astc_context(block_size)
    with lock:
        enc_img = context.compress(astc_image, swizzle)

    return enc_img


def image_to_texture2d(
    img: Image.Image,
    target_texture_format: Union[TextureFormat, int],
    platform: Union[BuildTarget, int] = 0,
    platform_blob: Optional[List[int]] = None,
    flip: bool = True,
) -> Tuple[bytes, TextureFormat]:
    """Converts a PIL Image to Texture2D bytes."""
    if not isinstance(target_texture_format, TextureFormat):
        target_texture_format = TextureFormat(target_texture_format)

    if flip:
        img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

    # defaults
    compress_func = None
    tex_format = TF.RGBA32
    pil_mode = "RGBA"

    # DXT / BC
    if target_texture_format in [TF.DXT1, TF.DXT1Crunched]:
        tex_format = TF.DXT1
        compress_func = compress_etcpak
    elif target_texture_format in [TF.DXT5, TF.DXT5Crunched]:
        tex_format = TF.DXT5
        compress_func = compress_etcpak
    elif target_texture_format in [TF.BC4, TF.BC5, TF.BC7]:
        tex_format = target_texture_format
        compress_func = compress_etcpak
    # ASTC
    elif target_texture_format.name.startswith("ASTC"):
        if "_HDR_" in target_texture_format.name:
            block_size = TEXTURE_FORMAT_BLOCK_SIZE_TABLE[target_texture_format]
            assert block_size is not None
            if img.mode == "RGB":
                tex_format = getattr(TF, f"ASTC_RGB_{block_size[0]}x{block_size[1]}")
            else:
                tex_format = getattr(TF, f"ASTC_RGBA_{block_size[0]}x{block_size[1]}")
        else:
            tex_format = target_texture_format
        compress_func = compress_astc
    # ETC
    elif target_texture_format in [TF.ETC_RGB4, TF.ETC_RGB4Crunched, TF.ETC_RGB4_3DS]:
        if target_texture_format == TF.ETC_RGB4_3DS:
            tex_format = TF.ETC_RGB4_3DS
        else:
            tex_format = target_texture_format
        compress_func = compress_etcpak
    elif target_texture_format == TF.ETC2_RGB:
        tex_format = TF.ETC2_RGB
        compress_func = compress_etcpak
    elif target_texture_format in [TF.ETC2_RGBA8, TF.ETC2_RGBA8Crunched, TF.ETC2_RGBA1]:
        tex_format = TF.ETC2_RGBA8
        compress_func = compress_etcpak
    # A
    elif target_texture_format == TF.Alpha8:
        tex_format = TF.Alpha8
        pil_mode = "A"
    # R - should probably be merged into #A, as pure R is used as Alpha
    # but need test data for this first
    elif target_texture_format in [
        TF.R8,
        TF.R16,
        TF.RHalf,
        TF.RFloat,
        TF.EAC_R,
        TF.EAC_R_SIGNED,
    ]:
        tex_format = TF.R8
        pil_mode = "R"
    # RGBA
    elif target_texture_format in [
        TF.RGB565,
        TF.RGB24,
        TF.BGR24,
        TF.RGB9e5Float,
        TF.PVRTC_RGB2,
        TF.PVRTC_RGB4,
        TF.ATC_RGB4,
    ]:
        tex_format = TF.RGB24
        pil_mode = "RGB"
    # everything else defaulted to RGBA

    width, height = img.width, img.height
    switch_info = None

    if TextureSwizzler.is_switch_swizzled(platform, platform_blob):
        s_tex_format = tex_format
        if tex_format == TF.RGB24:
            s_tex_format = TF.RGBA32
            pil_mode = "RGBA"
        elif tex_format == TF.BGR24:
            s_tex_format = TF.BGRA32
            pil_mode = "BGRA"

        assert platform_blob is not None
        gobs_per_block = TextureSwizzler.get_switch_gobs_per_block(platform_blob)
        block_size = TextureSwizzler.TEXTURE_FORMAT_BLOCK_SIZE_MAP[s_tex_format]
        width, height = TextureSwizzler.get_padded_texture_size(img.width, img.height, *block_size, gobs_per_block)
        switch_info = (block_size, gobs_per_block)

    if compress_func:
        width, height = get_compressed_image_size(width, height, tex_format)
        img = pad_image(img, width, height)
        enc_img = compress_func(img.tobytes("raw", "RGBA"), width, height, tex_format)
    else:
        if switch_info:
            img = pad_image(img, width, height)

        enc_img = img.tobytes("raw", pil_mode)

    if switch_info:
        block_size, gobs_per_block = switch_info
        enc_img = bytes(TextureSwizzler.swizzle(enc_img, width, height, *block_size, gobs_per_block))

    return enc_img, tex_format


def get_image_from_texture2d(
    texture_2d: Texture2D,
    flip: bool = True,
) -> Image.Image:
    """Converts the given Texture2D object to PIL Image."""
    return parse_image_data(
        texture_2d.get_image_data(),
        texture_2d.m_Width,
        texture_2d.m_Height,
        texture_2d.m_TextureFormat,
        getattr(texture_2d.object_reader, "version", (0, 0, 0, 0)),
        getattr(texture_2d.object_reader, "platform", BuildTarget.UnknownPlatform),
        getattr(texture_2d, "m_PlatformBlob", None),
        flip,
    )


def parse_image_data(
    image_data: Union[bytes, bytearray, memoryview],
    width: int,
    height: int,
    texture_format: Union[TextureFormat, int],
    version: Tuple[int, int, int, int],
    platform: Union[BuildTarget, int],
    platform_blob: Optional[List[int]] = None,
    flip: bool = True,
) -> Image.Image:
    """Converts the given image data bytes to PIL Image."""
    if not width or not height:
        return Image.new("RGBA", (0, 0))

    if not image_data:
        raise ValueError("Texture2D has no image data")

    if not isinstance(texture_format, TextureFormat):
        texture_format = TextureFormat(texture_format)

    if platform == BuildTarget.XBOX360 and texture_format in XBOX_SWAP_FORMATS:
        image_data = swap_bytes_for_xbox(image_data)

    original_width, original_height = (width, height)

    if TextureSwizzler.is_switch_swizzled(platform, platform_blob):
        if texture_format == TF.RGB24:
            texture_format = TF.RGBA32
        elif texture_format == TF.BGR24:
            texture_format = TF.BGRA32

        assert platform_blob is not None
        gobs_per_block = TextureSwizzler.get_switch_gobs_per_block(platform_blob)
        block_size = TextureSwizzler.TEXTURE_FORMAT_BLOCK_SIZE_MAP[texture_format]
        width, height = TextureSwizzler.get_padded_texture_size(width, height, *block_size, gobs_per_block)
        image_data = TextureSwizzler.deswizzle(image_data, width, height, *block_size, gobs_per_block)
    else:
        width, height = get_compressed_image_size(width, height, texture_format)

    if not isinstance(image_data, bytes):
        # bytes(bytes item) would cause an unnecessary copy
        image_data = bytes(image_data)

    if "Crunched" in texture_format.name:
        if (
            version[0] > 2017
            or (version[0] == 2017 and version[1] >= 3)  # 2017.3 and up
            or texture_format == TF.ETC_RGB4Crunched
            or texture_format == TF.ETC2_RGBA8Crunched
        ):
            image_data = texture2ddecoder.unpack_unity_crunch(image_data)
        else:
            image_data = texture2ddecoder.unpack_crunch(image_data)

    if texture_format not in CONV_TABLE:
        raise NotImplementedError(f"Not implemented texture format: {texture_format.name}")
    conv_func, conv_args = CONV_TABLE[texture_format]

    img = conv_func(image_data, width, height, *conv_args)

    if original_width != width or original_height != height:
        img = img.crop((0, 0, original_width, original_height))

    if img and flip:
        return img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

    return img


def swap_bytes_for_xbox(image_data: Union[bytes, bytearray, memoryview]) -> bytearray:
    """Swaps the texture bytes for textures deployed on XBOX360."""
    image_data = bytearray(image_data)
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
    swap: Optional[Tuple[int, ...]] = None,
) -> Image.Image:
    img = Image.frombytes(mode, (width, height), image_data, codec, args) if width else Image.new(mode, (width, height))
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
    image = astc_encoder.ASTCImage(astc_encoder.ASTCType.U8, width, height, 1)
    texture_size = calculate_astc_compressed_size(width, height, block_size)
    if len(image_data) < texture_size:
        raise ValueError(f"Invalid ASTC data size: {len(image_data)} < {texture_size}")

    context, lock = get_astc_context(block_size)
    with lock:
        context.decompress(image_data[:texture_size], image, astc_encoder.ASTCSwizzle.from_str("RGBA"))
    assert image.data is not None, "Decompression failed, image data is None"

    return Image.frombytes("RGBA", (width, height), image.data, "raw", "RGBA")


ASTC_CONTEXTS: Dict[Tuple[int, int], Tuple[astc_encoder.ASTCContext, Lock]] = {}


def get_astc_context(block_size: tuple):
    """Get the ASTC context and its lock using the given `block_size`."""
    if block_size not in ASTC_CONTEXTS:
        config = astc_encoder.ASTCConfig(
            astc_encoder.ASTCProfile.LDR,
            *block_size,
            block_z=1,
            quality=100,
            flags=astc_encoder.ASTCConfigFlags.USE_DECODE_UNORM8,
        )
        context = astc_encoder.ASTCContext(config)
        lock = Lock()
        ASTC_CONTEXTS[block_size] = (context, lock)
    return ASTC_CONTEXTS[block_size]


def calculate_astc_compressed_size(width: int, height: int, block_size: tuple) -> int:
    """Calculate the size of the compressed data for ASTC."""
    # calculate the number of blocks
    block_count_x = (width + block_size[0] - 1) // block_size[0]
    block_count_y = (height + block_size[1] - 1) // block_size[1]
    # ignore depth for 2D textures
    # calculate the size of the compressed data
    return block_count_x * block_count_y * 16


def pvrtc(image_data: bytes, width: int, height: int, fmt: bool) -> Image.Image:
    image_data = texture2ddecoder.decode_pvrtc(image_data, width, height, fmt)
    return Image.frombytes("RGBA", (width, height), image_data, "raw", "BGRA")


def etc(image_data: bytes, width: int, height: int, fmt: str) -> Image.Image:
    if fmt == "ETC1":
        image_data = texture2ddecoder.decode_etc1(image_data, width, height)
    elif fmt == "ETC2_RGB":
        image_data = texture2ddecoder.decode_etc2(image_data, width, height)
    elif fmt == "ETC2_A1":
        image_data = texture2ddecoder.decode_etc2a1(image_data, width, height)
    elif fmt == "ETC2_A8":
        image_data = texture2ddecoder.decode_etc2a8(image_data, width, height)
    else:
        raise NotImplementedError(f"Unknown ETC mode: {fmt}")

    return Image.frombytes("RGBA", (width, height), image_data, "raw", "BGRA")


def eac(image_data: bytes, width: int, height: int, fmt: str) -> Image.Image:
    if fmt == "EAC_R":
        image_data = texture2ddecoder.decode_eacr(image_data, width, height)
    elif fmt == "EAC_R_SIGNED":
        image_data = texture2ddecoder.decode_eacr_signed(image_data, width, height)
    elif fmt == "EAC_RG":
        image_data = texture2ddecoder.decode_eacrg(image_data, width, height)
    elif fmt == "EAC_RG_SIGNED":
        image_data = texture2ddecoder.decode_eacrg_signed(image_data, width, height)
    else:
        raise NotImplementedError(f"Unknown EAC mode: {fmt}")

    return Image.frombytes("RGBA", (width, height), image_data, "raw", "BGRA")


def half(
    image_data: bytes,
    width: int,
    height: int,
    mode: str,
    codec: str,
    args,
    swap: Optional[tuple] = None,
) -> Image.Image:
    # convert half-float to int8
    stream = BytesIO(image_data)
    image_data = bytes(int(struct.unpack("e", stream.read(2))[0] * 256) for _ in range(width * height * len(codec)))
    return pillow(image_data, width, height, mode, codec, args, swap)


RG_PADDING_MAP = {
    "RGE": 16,
    "RGF": 32,
    "RG;16": 16,
    "RG;16s": 16,
    "RG;8s": 8,
}


def rg(image_data: bytes, width: int, height: int, mode: str, codec: str, args) -> Image.Image:
    # convert rg to rgb by adding in zeroes
    padding_size = RG_PADDING_MAP[codec]
    stream = BytesIO(image_data)
    padding = bytes(padding_size)
    rgb_data = b"".join(stream.read(padding_size * 2) + padding for _ in range(len(image_data) // (2 * padding_size)))
    if codec == "RGE":
        return half(rgb_data, width, height, mode, "RGB", args)
    else:
        return pillow(rgb_data, width, height, mode, codec.replace("RG", "RGB"), args)


def rgb9e5float(image_data: bytes, width: int, height: int) -> Image.Image:
    rgb = bytearray(width * height * 3)
    for i, (n,) in enumerate(struct.iter_unpack("<i", image_data)):
        scale = n >> 27 & 0x1F
        scalef = 2 ** (scale - 24)
        scaleb = scalef * 255.0
        b = (n >> 18 & 0x1FF) * scaleb
        g = (n >> 9 & 0x1FF) * scaleb
        r = (n & 0x1FF) * scaleb

        offset = i * 3
        rgb[offset : offset + 3] = [r, g, b]

    return Image.frombytes("RGB", (width, height), rgb, "raw", "RGB")


# Mapping TextureFormat -> (converter function, (additional args, ...))
CONV_TABLE: Dict[TF, Tuple[Callable[..., Image.Image], Tuple[Any, ...]]] = {
    TF.Alpha8: (pillow, ("RGBA", "raw", "A")),
    TF.ARGB4444: (pillow, ("RGBA", "raw", "RGBA;4B", (2, 1, 0, 3))),
    TF.RGB24: (pillow, ("RGB", "raw", "RGB")),
    TF.RGBA32: (pillow, ("RGBA", "raw", "RGBA")),
    TF.ARGB32: (pillow, ("RGBA", "raw", "ARGB")),
    TF.ARGBFloat: (pillow, ("RGBA", "raw", "RGBAF", (2, 1, 0, 3))),
    TF.RGB565: (pillow, ("RGB", "raw", "BGR;16")),
    TF.BGR24: (pillow, ("RGB", "raw", "BGR")),
    TF.R8: (pillow, ("RGB", "raw", "R")),
    TF.R16: (pillow, ("RGB", "raw", "R;16")),
    TF.RG16: (rg, ("RGB", "raw", "RG")),
    TF.DXT1: (pillow, ("RGBA", "bcn", 1)),
    TF.DXT3: (pillow, ("RGBA", "bcn", 2)),
    TF.DXT5: (pillow, ("RGBA", "bcn", 3)),
    TF.RGBA4444: (pillow, ("RGBA", "raw", "RGBA;4B", (3, 2, 1, 0))),
    TF.BGRA32: (pillow, ("RGBA", "raw", "BGRA")),
    TF.RHalf: (half, ("R", "raw", "R")),
    TF.RGHalf: (rg, ("RGB", "raw", "RGE")),
    TF.RGBAHalf: (half, ("RGB", "raw", "RGB")),
    TF.RFloat: (pillow, ("RGB", "raw", "RF")),
    TF.RGFloat: (rg, ("RGB", "raw", "RGF")),
    TF.RGBAFloat: (pillow, ("RGBA", "raw", "RGBAF")),
    # TF.YUY2: NotImplementedError("YUY2 not implemented"),
    TF.RGB9e5Float: (rgb9e5float, ()),
    TF.BC4: (pillow, ("L", "bcn", 4)),
    TF.BC5: (pillow, ("RGB", "bcn", 5)),
    TF.BC6H: (pillow, ("RGBA", "bcn", 6)),
    TF.BC7: (pillow, ("RGBA", "bcn", 7)),
    TF.DXT1Crunched: (pillow, ("RGBA", "bcn", 1)),
    TF.DXT5Crunched: (pillow, ("RGBA", "bcn", 3)),
    TF.PVRTC_RGB2: (pvrtc, (True,)),
    TF.PVRTC_RGBA2: (pvrtc, (True,)),
    TF.PVRTC_RGB4: (pvrtc, (False,)),
    TF.PVRTC_RGBA4: (pvrtc, (False,)),
    TF.ETC_RGB4: (etc, ("ETC1",)),
    TF.ATC_RGB4: (atc, (False,)),
    TF.ATC_RGBA8: (atc, (True,)),
    TF.EAC_R: (eac, ("EAC_R",)),
    TF.EAC_R_SIGNED: (eac, ("EAC_R_SIGNED",)),
    TF.EAC_RG: (eac, ("EAC_RG",)),
    TF.EAC_RG_SIGNED: (eac, ("EAC_RG_SIGNED",)),
    TF.ETC2_RGB: (etc, ("ETC2_RGB",)),
    TF.ETC2_RGBA1: (etc, ("ETC2_A1",)),
    TF.ETC2_RGBA8: (etc, ("ETC2_A8",)),
    TF.ASTC_RGB_4x4: (astc, ((4, 4),)),
    TF.ASTC_RGB_5x5: (astc, ((5, 5),)),
    TF.ASTC_RGB_6x6: (astc, ((6, 6),)),
    TF.ASTC_RGB_8x8: (astc, ((8, 8),)),
    TF.ASTC_RGB_10x10: (astc, ((10, 10),)),
    TF.ASTC_RGB_12x12: (astc, ((12, 12),)),
    TF.ASTC_RGBA_4x4: (astc, ((4, 4),)),
    TF.ASTC_RGBA_5x5: (astc, ((5, 5),)),
    TF.ASTC_RGBA_6x6: (astc, ((6, 6),)),
    TF.ASTC_RGBA_8x8: (astc, ((8, 8),)),
    TF.ASTC_RGBA_10x10: (astc, ((10, 10),)),
    TF.ASTC_RGBA_12x12: (astc, ((12, 12),)),
    TF.ETC_RGB4_3DS: (etc, ("ETC1",)),
    TF.ETC_RGBA8_3DS: (etc, ("ETC1",)),
    TF.ETC_RGB4Crunched: (etc, ("ETC1",)),
    TF.ETC2_RGBA8Crunched: (etc, ("ETC2_A8",)),
    TF.ASTC_HDR_4x4: (astc, ((4, 4),)),
    TF.ASTC_HDR_5x5: (astc, ((5, 5),)),
    TF.ASTC_HDR_6x6: (astc, ((6, 6),)),
    TF.ASTC_HDR_8x8: (astc, ((8, 8),)),
    TF.ASTC_HDR_10x10: (astc, ((10, 10),)),
    TF.ASTC_HDR_12x12: (astc, ((12, 12),)),
    TF.RG32: (rg, ("RGB", "raw", "RG;16")),
    TF.RGB48: (pillow, ("RGB", "raw", "RGB;16")),
    TF.RGBA64: (pillow, ("RGBA", "raw", "RGBA;16")),
    TF.R8_SIGNED: (pillow, ("R", "raw", "R;8s")),
    TF.RG16_SIGNED: (rg, ("RGB", "raw", "RG;8s")),
    TF.RGB24_SIGNED: (pillow, ("RGB", "raw", "RGB;8s")),
    TF.RGBA32_SIGNED: (pillow, ("RGBA", "raw", "RGBA;8s")),
    TF.R16_SIGNED: (pillow, ("R", "raw", "R;16s")),
    TF.RG32_SIGNED: (rg, ("RGB", "raw", "RG;16s")),
    TF.RGB48_SIGNED: (pillow, ("RGB", "raw", "RGB;16s")),
    TF.RGBA64_SIGNED: (pillow, ("RGBA", "raw", "RGBA;16s")),
}

# XBOX Swap Formats
XBOX_SWAP_FORMATS = [TF.RGB565, TF.DXT1, TF.DXT1Crunched, TF.DXT5, TF.DXT5Crunched]
