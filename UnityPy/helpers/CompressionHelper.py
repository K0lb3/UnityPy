import gzip
import lzma
import struct

import brotli
import lz4.block

GZIP_MAGIC: bytes = b"\x1f\x8b"
BROTLI_MAGIC: bytes = b"brotli"


# LZMA
def decompress_lzma(data: bytes) -> bytes:
    """decompresses lzma-compressed data

    :param data: compressed data
    :type data: bytes
    :raises _lzma.LZMAError: Compressed data ended before the end-of-stream marker was reached
    :return: uncompressed data
    :rtype: bytes
    """
    props, dict_size = struct.unpack("<BI", data[:5])
    lc = props % 9
    props = props // 9
    pb = props // 5
    lp = props % 5
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
    return dec.decompress(data[5:])


def compress_lzma(data: bytes) -> bytes:
    """compresses data via lzma (unity specific)
    The current static settings may not be the best solution,
    but they are the most commonly used values and should therefore be enough for the time being.

    :param data: uncompressed data
    :type data: bytes
    :return: compressed data
    :rtype: bytes
    """
    compressor = lzma.LZMACompressor(format=lzma.FORMAT_ALONE, filters=[{
        "id": lzma.FILTER_LZMA1,
        "dict_size": 0x200000,
        "lc": 3,
        "lp": 0,
        "pb": 2,
    }])
    compressed_data = compressor.compress(data) + compressor.flush()

    # Skip Decompressed Length
    header = compressed_data[:5]
    compressed_body = compressed_data[13:]

    return header + compressed_body


# LZ4
def decompress_lz4(data: bytes, uncompressed_size: int) -> bytes:  # LZ4M/LZ4HC
    """decompresses lz4-compressed data

    :param data: compressed data
    :type data: bytes
    :param uncompressed_size: size of the uncompressed data
    :type uncompressed_size: int
    :raises _block.LZ4BlockError: Decompression failed: corrupt input or insufficient space in destination buffer.
    :return: uncompressed data
    :rtype: bytes
    """
    return lz4.block.decompress(data, uncompressed_size)


def compress_lz4(data: bytes) -> bytes:  # LZ4M/LZ4HC
    """compresses data via lz4.block

    :param data: uncompressed data
    :type data: bytes
    :return: compressed data
    :rtype: bytes
    """
    return lz4.block.compress(
        data, mode="high_compression", compression=9, store_size=False
    )


# Brotli
def decompress_brotli(data: bytes) -> bytes:
    """decompresses brotli-compressed data

    :param data: compressed data
    :type data: bytes
    :raises brotli.error: BrotliDecompress failed
    :return: uncompressed data
    :rtype: bytes
    """
    return brotli.decompress(data)


def compress_brotli(data: bytes) -> bytes:
    """compresses data via brotli

    :param data: uncompressed data
    :type data: bytes
    :return: compressed data
    :rtype: bytes
    """
    return brotli.compress(data)


# GZIP
def decompress_gzip(data: bytes) -> bytes:
    """decompresses gzip-compressed data

    :param data: compressed data
    :type data: bytes
    :raises OSError: Not a gzipped file
    :return: uncompressed data
    :rtype: bytes
    """
    return gzip.decompress(data)


def compress_gzip(data: bytes) -> bytes:
    """compresses data via gzip
    The current static settings may not be the best solution,
    but they are the most commonly used values and should therefore be enough for the time being.

    :param data: uncompressed data
    :type data: bytes
    :return: compressed data
    :rtype: bytes
    """
    return gzip.compress(data)
