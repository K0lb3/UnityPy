import lz4.block
import lzma
import struct
import gzip
import brotli

gzipMagic = b'\x1f\x8b'
brotliMagic = b'brotli'


def DecompressLZMA(data):
	# taken from unitypack
	props, dict_size = struct.unpack("<BI", data[:5])
	lc = props % 9
	props = int(props / 9)
	pb = int(props / 5)
	lp = props % 5
	dec = lzma.LZMADecompressor(format = lzma.FORMAT_RAW, filters = [{
			"id"       : lzma.FILTER_LZMA1,
			"dict_size": dict_size,
			"lc"       : lc,
			"lp"       : lp,
			"pb"       : pb,
	}])
	return dec.decompress(data[5:])


def DecompressLZ4(data, uncompressedSize):  # LZ4M LZ4HC
	return lz4.block.decompress(data, uncompressedSize)


def DecompressBrotli(data):
	return brotli.decompress(data)


def DecompressGZIP(data):
	return gzip.decompress(data)
