import gzip
import lzma
import struct
from typing import Callable, Dict, Tuple, Union

import brotli
import lz4.block

from ..enums.BundleFile import CompressionFlags

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


def chunk_based_compress(data: ByteString, block_info_flag: int) -> Tuple[ByteString, list]:
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
        return data, [(len(data), len(data), block_info_flag)]

    if switch in COMPRESSION_MAP:
        compress_func = COMPRESSION_MAP[switch]
    else:
        raise NotImplementedError(f"No compression function in the CompressionHelper.COMPRESSION_MAP for {switch}")

    if switch in COMPRESSION_CHUNK_SIZE_MAP:
        chunk_size = COMPRESSION_CHUNK_SIZE_MAP[switch]
    else:
        raise NotImplementedError(f"No chunk size in the CompressionHelper.COMPRESSION_CHUNK_SIZE_MAP for {switch}")

    block_info = []
    uncompressed_data_size = len(data)
    compressed_file_data = bytearray()
    p = 0
    while uncompressed_data_size > chunk_size:
        compressed_data = compress_func(data[p : p + chunk_size])
        if len(compressed_data) > chunk_size:
            compressed_file_data.extend(data[p : p + chunk_size])
            block_info.append(
                (
                    chunk_size,
                    chunk_size,
                    block_info_flag ^ switch,
                )
            )
        else:
            compressed_file_data.extend(compressed_data)
            block_info.append(
                (
                    chunk_size,
                    len(compressed_data),
                    block_info_flag,
                )
            )
        p += chunk_size
        uncompressed_data_size -= chunk_size
    if uncompressed_data_size > 0:
        compressed_data = compress_func(data[p:])
        if len(compressed_data) > uncompressed_data_size:
            compressed_file_data.extend(data[p:])
            block_info.append(
                (
                    uncompressed_data_size,
                    uncompressed_data_size,
                    block_info_flag ^ switch,
                )
            )
        else:
            compressed_file_data.extend(compressed_data)
            block_info.append(
                (
                    uncompressed_data_size,
                    len(compressed_data),
                    block_info_flag,
                )
            )
    return bytes(compressed_file_data), block_info


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
)
