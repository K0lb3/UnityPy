import io
import os

from ..EndianBinaryReader import EndianBinaryReader
from ..EndianBinaryWriter import EndianBinaryWriter
from ..helpers import CompressionHelper


class BundleFile:
	bundle_reader: EndianBinaryReader
	files: list
	path: str
	signature: str
	format: int
	version_player: str
	version_engine: str

	def __init__(self, bundle_reader: EndianBinaryReader, path: str):
		self.files = []
		self.path = path
		self.signature = bundle_reader.read_string_to_null()
		self.format = bundle_reader.read_int()
		self.version_player = bundle_reader.read_string_to_null()
		self.version_engine = bundle_reader.read_string_to_null()

		if self.signature in ["UnityWeb", "UnityRaw", "\xFA\xFA\xFA\xFA\xFA\xFA\xFA\xFA"]:
			if self.format < 6:
				bundle_size = bundle_reader.read_int()
			elif self.format == 6:
				self.read_format_6(bundle_reader, True)
				return

			dummy2 = bundle_reader.read_short()
			offset = bundle_reader.read_short()

			if self.signature in ["UnityWeb", "\xFA\xFA\xFA\xFA\xFA\xFA\xFA\xFA"]:
				dummy3 = bundle_reader.read_int()
				lzma_chunks = bundle_reader.read_int()
				bundle_reader.Position = bundle_reader.Position + (lzma_chunks - 1) * 8
				lzma_size = bundle_reader.read_int()
				stream_size = bundle_reader.read_int()

				bundle_reader.Position = offset
				lzma_buffer = bundle_reader.read_bytes(lzma_size)
				data_reader = EndianBinaryReader(CompressionHelper.decompress_lzma(lzma_buffer))
				self.get_assets_files(data_reader, 0)
			elif self.signature == "UnityRaw":
				bundle_reader.Position = offset
				self.get_assets_files(bundle_reader, offset)

		elif self.signature == "UnityFS":
			if self.format == 6:
				self.read_format_6(bundle_reader)

	def get_assets_files(self, reader: EndianBinaryReader, offset):
		file_count = reader.read_int()
		self.files = [
			File(self.format, reader, offset)
			for _ in range(file_count)
		]

	def read_format_6(self, bundle_reader: EndianBinaryReader, padding=False):
		bundle_size = bundle_reader.read_long()
		compressed_size = bundle_reader.read_int()
		uncompressed_size = bundle_reader.read_int()
		flag = bundle_reader.read_int()
		self._header_compression_flag = flag

		if padding:
			bundle_reader.read_byte()

		if (flag & 0x80) != 0:  # at end of file
			position = bundle_reader.Position
			bundle_reader.Position = bundle_reader.Length - compressed_size
			block_info_bytes = bundle_reader.read_bytes(compressed_size)
			bundle_reader.Position = position
		else:
			block_info_bytes = bundle_reader.read_bytes(compressed_size)

		switch = flag & 0x3F
		if switch == 1:  # LZMA
			blocks_info_data = CompressionHelper.decompress_lzma(block_info_bytes)
		elif switch in [2, 3]:  # LZ4, LZ4HC
			blocks_info_data = CompressionHelper.decompress_lz4(block_info_bytes, uncompressed_size)
		# elif switch == 4: #LZHAM:
		else:  # no compression
			blocks_info_data = block_info_bytes

		blocks_info_reader = EndianBinaryReader(blocks_info_data)
		blocks_info_reader.Position = 0x10
		block_count = blocks_info_reader.read_int()
		block_infos = [
			BlockInfo(blocks_info_reader)
			for _ in range(block_count)
		]

		data = []
		for block_info in block_infos:
			switch = block_info.flag & 0x3F

			if switch == 1:  # LZMA
				data.append(CompressionHelper.decompress_lzma(bundle_reader.read(block_info.compressed_size)))
			elif switch in [2, 3]:  # LZ4, LZ4HC
				data.append(CompressionHelper.decompress_lz4(bundle_reader.read(block_info.compressed_size),
															block_info.uncompressed_size))
			# elif switch == 4: #LZHAM:
			else:  # no compression
				data.append(bundle_reader.read(block_info.compressed_size))

		data_stream = EndianBinaryReader(b''.join(data))
		entry_info_count = blocks_info_reader.read_int()
		self.files = [
			File(6, blocks_info_reader, data_stream)
			for _ in range(entry_info_count)
		]

	def save(self):
		writer = EndianBinaryWriter()

		writer.write_string_to_null(self.signature)
		writer.write_int(self.format)
		writer.write_string_to_null(self.version_player)
		writer.write_string_to_null(self.version_engine)

		if self.format == 6:  # WORKS
			padding = True if self.signature in ["UnityWeb", "UnityRaw", "\xFA\xFA\xFA\xFA\xFA\xFA\xFA\xFA"] else False
			self.save_format_6(writer, padding)
		else:  # WIP
			raise NotImplementedError("Not Implemented")

		return writer.bytes

	def save_format_6(self, writer: EndianBinaryWriter, padding=False):
		header_compression_flag = self._header_compression_flag
		# WORKS
		data_compression = self._header_compression_flag & 0x3F
		block_info_compression = self._header_compression_flag & 0x3F
		# generate compressed data
		# Structure:
		# 	main stream:
		# 		bundle_size			- ???
		# 		compressed_size		- size after compression
		# 		uncompressed_size	- size before compression
		# 		flag				- compression - none = 0x10
		# 		block_info			- read via compressed_size
		# 	block_info stream:
		# 		0x10 offset
		# 		block_count			- number of blocks
		# 		block_infos			- block infos - read after another
		# 			uncompressed_size
		# 			compressed_size
		# 			flag			- compression - none = 0
		# 		data - read blocks from info and merge them
		# 		entry_info_count	- number of files
		# 		files:
		# 			offset			- in data stream
		# 			size			- in data stream
		# 			flag			- compression
		# 			name
		# 	data stream:			- data from block info stream
		# 		files read via entry infos from block info

		files = self.files  # packed assets, self.files for debugging
		# data - compression can be added later on
		data = b"".join(f.stream.getbuffer() for f in files)

		# block info stream
		bs = EndianBinaryWriter()
		# weird offset
		bs.write(b"\x00" * 0x10)
		# block count = 1 - enough for up to 4 GB
		bs.write_int(1)
		# uncompressed_size
		bs.write_u_int(len(data))
		# compress data
		if data_compression == 1:  # LZMA
			data = CompressionHelper.compress_lzma(data)
		elif data_compression in [2, 3]:  # LZ4, LZ4HC
			data = CompressionHelper.compress_lz4(data)
		elif data_compression == 4:  # LZHAM
			raise NotImplementedError("not implemented")

		# data = compress(data)
		bs.write_u_int(len(data))
		# compression flag
		bs.write_short(header_compression_flag)
		# entry info count
		bs.write_int(len(files))

		offset = 0
		for f in files:
			offset = f.write(6, bs, offset)

		block_info_data = bs.bytes
		# calculate sizes
		uncompressed_size = len(block_info_data)
		# compress block
		if block_info_compression == 1:  # LZMA
			block_info_data = CompressionHelper.compress_lzma(block_info_data)
		elif block_info_compression in [2, 3]:  # LZ4, LZ4HC
			block_info_data = CompressionHelper.compress_lz4(block_info_data)
		elif block_info_compression == 4:  # LZHAM:
			raise NotImplementedError("not implemented")

		compressed_size = len(block_info_data)
		bundle_size = writer.Position + len(data) + len(block_info_data) + 8 + 4 + 4 + 4 + (1 if padding else 0)
		flag = 64 + block_info_compression

		# write stuff
		writer.write_long(bundle_size)
		writer.write_int(compressed_size)
		writer.write_int(uncompressed_size)
		writer.write_int(flag)

		if padding:
			writer.write_byte(1)

		writer.write(block_info_data)
		writer.write(data)

	def __repr__(self):
		return "<%s %s>" % (
			self.__class__.__name__, self.path
		)


class File:
	flag: int
	path: str
	stream: io.BytesIO

	@property
	def name(self):
		return os.path.basename(self.path)

	def __init__(self, format: int, *args):
		if format == 6:
			blocks_info_reader = args[0]
			data_stream = args[1]
			offset = blocks_info_reader.read_long()
			size = blocks_info_reader.read_long()
			self.flag = blocks_info_reader.read_int()
			self.path = blocks_info_reader.read_string_to_null()
			data_stream.Position = offset
			self.stream = io.BytesIO(data_stream.read(size))
		else:
			reader = args[0]
			offset = args[1]
			self.path = reader.read_string_to_null()
			offset = reader.read_int() + offset
			size = reader.read_int()
			next_file_pos = reader.Position
			reader.Position = offset
			self.stream = io.BytesIO(reader.read(size))
			reader.Position = next_file_pos

	def write(self, format: int, bs: EndianBinaryWriter, offset):
		if format == 6:
			# offset
			bs.write_long(offset)
			length = len(self.stream.getbuffer())
			# size
			bs.write_long(length)
			# flag
			bs.write_int(self.flag)
			# file_name
			bs.write_string_to_null(self.name)
			return offset + length
		else:
			raise NotImplementedError(f"writing files, format {format}")


class BlockInfo:
	compressed_size: int
	uncompressed_size: int
	flag: int

	def __init__(self, reader: EndianBinaryReader):
		self.uncompressed_size = reader.read_u_int()
		self.compressed_size = reader.read_u_int()
		self.flag = reader.read_short()
