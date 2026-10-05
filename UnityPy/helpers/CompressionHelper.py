import gzip
import lzma
import struct
from typing import Callable, Dict, List, Optional, Tuple, Union

import brotli
import lz4.block
from attrs import define

from ..enums.BundleFile import CompressionFlags
from ..streams import EndianBinaryReader, EndianBinaryWriter

ByteString = Union[bytes, bytearray, memoryview]
GZIP_MAGIC: bytes = b"\x1f\x8b"
BROTLI_MAGIC: bytes = b"brotli"


# LZMA
def decompress_lzma(data: ByteString, read_decompressed_size: bool = False) -> bytes:
    """decompresses lzma-compressed data

    :param data: compressed data
    :type data: ByteString
    :raises _lzma.LZMAError: Compressed data ended before the end-of-stream marker was reached
    :return: uncompressed data
    :rtype: bytes
    """
    props, dict_size = struct.unpack("<BI", data[:5])
    lc = props % 9
    remainder = props // 9
    pb = remainder // 5
    lp = remainder % 5
    dec = lzma.LZMADecompressor(
        format=lzma.FORMAT_RAW,
        filters=[
            {
                "id": lzma.FILTER_LZMA1,
                "dict_size": dict_size,
                "lc": lc,
                "lp": lp,
                "pb": pb,
            }
        ],
    )
    data_offset = 13 if read_decompressed_size else 5
    return dec.decompress(data[data_offset:])


def compress_lzma(data: ByteString, write_decompressed_size: bool = False) -> bytes:
    """compresses data via lzma (unity specific)
    The current static settings may not be the best solution,
    but they are the most commonly used values and should therefore be enough for the time being.

    :param data: uncompressed data
    :type data: ByteString
    :return: compressed data
    :rtype: bytes
    """
    dict_size = 0x800000  # 1 << 23
    compressor = lzma.LZMACompressor(
        format=lzma.FORMAT_RAW,
        filters=[
            {
                "id": lzma.FILTER_LZMA1,
                "dict_size": dict_size,
                "lc": 3,
                "lp": 0,
                "pb": 2,
                "mode": lzma.MODE_NORMAL,
                "mf": lzma.MF_BT4,
                "nice_len": 123,
            }
        ],
    )

    compressed_data = compressor.compress(data) + compressor.flush()
    cdl = len(compressed_data)
    if write_decompressed_size:
        return struct.pack(f"<BIQ{cdl}s", 0x5D, dict_size, len(data), compressed_data)
    else:
        return struct.pack(f"<BI{cdl}s", 0x5D, dict_size, compressed_data)


# LZ4
def decompress_lz4(data: ByteString, uncompressed_size: int) -> bytes:  # LZ4M/LZ4HC
    """decompresses lz4-compressed data

    :param data: compressed data
    :type data: ByteString
    :param uncompressed_size: size of the uncompressed data
    :type uncompressed_size: int
    :raises _block.LZ4BlockError: Decompression failed: corrupt input or insufficient space in destination buffer.
    :return: uncompressed data
    :rtype: bytes
    """
    return lz4.block.decompress(data, uncompressed_size)


def compress_lz4(data: ByteString) -> bytes:  # LZ4M/LZ4HC
    """compresses data via lz4.block

    :param data: uncompressed data
    :type data: ByteString
    :return: compressed data
    :rtype: bytes
    """
    return lz4.block.compress(data, mode="high_compression", compression=9, store_size=False)


# Brotli
def decompress_brotli(data: ByteString) -> bytes:
    """decompresses brotli-compressed data

    :param data: compressed data
    :type data: ByteString
    :raises brotli.error: BrotliDecompress failed
    :return: uncompressed data
    :rtype: bytes
    """
    return brotli.decompress(data)


def compress_brotli(data: ByteString) -> bytes:
    """compresses data via brotli

    :param data: uncompressed data
    :type data: ByteString
    :return: compressed data
    :rtype: bytes
    """
    return brotli.compress(data)


# GZIP
def decompress_gzip(data: ByteString) -> bytes:
    """decompresses gzip-compressed data

    :param data: compressed data
    :type data: ByteString
    :raises OSError: Not a gzipped file
    :return: uncompressed data
    :rtype: bytes
    """
    return gzip.decompress(data)


def compress_gzip(data: ByteString) -> bytes:
    """compresses data via gzip
    The current static settings may not be the best solution,
    but they are the most commonly used values and should therefore be enough for the time being.

    :param data: uncompressed data
    :type data: ByteString
    :return: compressed data
    :rtype: bytes
    """
    return gzip.compress(data)


@define(slots=True, frozen=True)
class BlockInfo:
    uncompressedSize: int
    compressedSize: int
    flags: int
    offset: Optional[int] = None

    @classmethod
    def from_reader(cls, reader: EndianBinaryReader, version: int):
        return cls(
            reader.read_u_int(),  # uncompressedSize
            reader.read_u_int(),  # compressedSize
            reader.read_u_short(),  # flags
            offset=reader.read_u_long() if version >= 9 else None,
        )

    def write_to(self, writer: EndianBinaryWriter):
        writer.write_u_int(self.uncompressedSize)
        writer.write_u_int(self.compressedSize)
        writer.write_u_short(self.flags)
        if self.offset is not None:
            writer.write_u_long(self.offset)


def chunk_based_compress(data: ByteString, block_info_flag: int, version: int) -> Tuple[ByteString, List[BlockInfo]]:
    """compresses AssetBundle data based on the block_info_flag
    LZ4/LZ4HC will be chunk-based compression

    :param data: uncompressed data
    :type data: ByteString
    :param block_info_flag: block info flag
    :type block_info_flag: int
    :return: compressed data and block info
    :rtype: tuple
    """
    switch = block_info_flag & 0x3F
    chunk_size = None
    compress_func = None
    if switch == 0:  # NONE
        return data, [BlockInfo(len(data), len(data), block_info_flag, None if version < 9 else 0)]

    if switch in COMPRESSION_MAP:
        compress_func = COMPRESSION_MAP[switch]
    else:
        raise NotImplementedError(f"No compression function in the CompressionHelper.COMPRESSION_MAP for {switch}")

    if switch in COMPRESSION_CHUNK_SIZE_MAP:
        chunk_size = COMPRESSION_CHUNK_SIZE_MAP[switch]
    else:
        raise NotImplementedError(f"No chunk size in the CompressionHelper.COMPRESSION_CHUNK_SIZE_MAP for {switch}")

    block_info = []
    compressed_data = bytearray()
    for uncompressed_offset in range(0, len(data), chunk_size):
        chunk_flag = block_info_flag
        uncompressed_chunk = data[uncompressed_offset : uncompressed_offset + chunk_size]
        compressed_chunk = compress_func(uncompressed_chunk)

        if len(compressed_data) >= chunk_size:  # compression has no effect, so store as uncompressed
            compressed_chunk = uncompressed_chunk
            chunk_flag = block_info_flag ^ switch

        block_info.append(
            BlockInfo(
                len(uncompressed_chunk),
                len(compressed_chunk),
                chunk_flag,
                len(compressed_data) if version >= 9 else None,
            )
        )

        compressed_data.extend(compressed_chunk)
        if version >= 9:
            # align by 16
            alignment = 16
            align = (alignment - len(compressed_data) % alignment) % alignment
            compressed_data.extend(b"\x00" * align)

    return compressed_data, block_info


def decompress_lzham(data: ByteString, uncompressed_size: int) -> bytes:
    raise NotImplementedError("Custom compression or unimplemented LZHAM (removed by Unity) encountered!")


DECOMPRESSION_MAP: Dict[Union[int, CompressionFlags], Callable[[ByteString, int], ByteString]] = {
    CompressionFlags.NONE: lambda cd, _ucs: cd,
    CompressionFlags.LZMA: lambda cd, _ucs: decompress_lzma(cd),
    CompressionFlags.LZ4: decompress_lz4,
    CompressionFlags.LZ4HC: decompress_lz4,
    CompressionFlags.LZHAM: decompress_lzham,
}

COMPRESSION_MAP: Dict[Union[int, CompressionFlags], Callable[[ByteString], ByteString]] = {
    CompressionFlags.NONE: lambda cd: cd,
    CompressionFlags.LZMA: compress_lzma,
    CompressionFlags.LZ4: compress_lz4,
    CompressionFlags.LZ4HC: compress_lz4,
}

COMPRESSION_CHUNK_SIZE_MAP: Dict[Union[int, CompressionFlags], int] = {
    CompressionFlags.NONE: 0xFFFFFFFF,
    CompressionFlags.LZMA: 0xFFFFFFFF,
    CompressionFlags.LZ4: 0x00020000,
    CompressionFlags.LZ4HC: 0x00020000,
}


__all__ = (
    "compress_brotli",
    "compress_gzip",
    "compress_lz4",
    "compress_lzma",
    "decompress_brotli",
    "decompress_gzip",
    "decompress_lz4",
    "decompress_lzma",
    "decompress_lzham",
    "chunk_based_compress",
    "COMPRESSION_MAP",
    "DECOMPRESSION_MAP",
    "COMPRESSION_CHUNK_SIZE_MAP",
    "BlockInfo",
)
