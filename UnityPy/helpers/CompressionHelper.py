import gzip
import lzma
import struct

import brotli
import lz4.block

GZIP_MAGIC = b'\x1f\x8b'
BROTLI_MAGIC = b'brotli'


def decompress_lzma(data):
	props, dict_size = struct.unpack("<BI", data[:5])
	lc = props % 9
	props = props // 9
	pb = props // 5
	lp = props % 5
	dec = lzma.LZMADecompressor(format = lzma.FORMAT_RAW, filters = [{
			"id"       : lzma.FILTER_LZMA1,
			"dict_size": dict_size,
			"lc"       : lc,
			"lp"       : lp,
			"pb"       : pb,
	}])
	return dec.decompress(data[5:])


def decompress_lz4(data, uncompressed_size):  # LZ4M LZ4HC
	return lz4.block.decompress(data, uncompressed_size)


def decompress_brotli(data):
	return brotli.decompress(data)


def decompress_gzip(data):
	return gzip.decompress(data)
