import io
import os

from ..EndianBinaryReader import EndianBinaryReader
from ..helpers import CompressionHelper


class File:
	flag: int
	name: str
	stream: io.BytesIO


class StreamFile:
	name: str
	stream: io.BytesIO


class BlockInfo:
	compressed_size: int
	uncompressed_size: int
	flag: int


class BundleFile:
	bundle_reader: EndianBinaryReader
	files: int
	path: str
	_signature: str
	_format: int
	version_player: str
	version_engine: str

	def __init__(self, bundle_reader: EndianBinaryReader, path: str):
		self.files = []
		self.path = path
		self._signature = bundle_reader.read_string_to_null()
		self._format = bundle_reader.read_int()
		self.version_player = bundle_reader.read_string_to_null()
		self.version_engine = bundle_reader.read_string_to_null()

		if self._signature in ["UnityWeb", "UnityRaw", "\xFA\xFA\xFA\xFA\xFA\xFA\xFA\xFA"]:
			if self._format < 6:
				bundleSize = bundle_reader.read_int()
			elif self._format == 6:
				self.read_format_6(bundle_reader, True)
				return

			dummy2 = bundle_reader.read_short()
			offset = bundle_reader.read_short()

			if self._signature in ["UnityWeb", "\xFA\xFA\xFA\xFA\xFA\xFA\xFA\xFA"]:
				dummy3 = bundle_reader.read_int()
				lzma_chunks = bundle_reader.read_int()
				bundle_reader.Position = bundle_reader.Position + (lzma_chunks - 1) * 8
				lzma_size = bundle_reader.read_int()
				stream_size = bundle_reader.read_int()

				bundle_reader.Position = offset
				lzma_buffer = bundle_reader.read_bytes(lzma_size)
				data_reader = EndianBinaryReader(CompressionHelper.decompress_lzma(lzma_buffer))
				self.get_assets_files(data_reader, 0)
			elif self._signature == "UnityRaw":
				bundle_reader.Position = offset
				self.get_assets_files(bundle_reader, offset)

		elif self._signature == "UnityFS":
			if self._format == 6:
				self.read_format_6(bundle_reader)

	def get_assets_files(self, reader: EndianBinaryReader, offset):
		file_count = reader.read_int()
		for i in range(file_count):
			f = StreamFile()
			f.name = os.path.basename(reader.read_string_to_null())
			offset = reader.read_int() + offset
			size = reader.read_int()

			next_file_pos = reader.Position

			reader.Position = offset
			f.stream = io.BytesIO(reader.read(size))
			self.files.append(f)

			reader.Position = next_file_pos

	def read_format_6(self, bundle_reader: EndianBinaryReader, padding=False):
		bundle_size = bundle_reader.read_long()
		compressed_size = bundle_reader.read_int()
		uncompressed_size = bundle_reader.read_int()
		flag = bundle_reader.read_int()
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
		block_infos = []
		for i in range(block_count):
			block_info = BlockInfo()
			block_info.uncompressed_size = blocks_info_reader.read_u_int()
			block_info.compressed_size = blocks_info_reader.read_u_int()
			block_info.flag = blocks_info_reader.read_short()
			block_infos.append(block_info)

		data = []
		for blockInfo in block_infos:
			switch = blockInfo.flag & 0x3F

			if switch == 1:  # LZMA
				data.append(CompressionHelper.decompress_lzma(bundle_reader.read(blockInfo.compressed_size)))
			elif switch in [2, 3]:  # LZ4, LZ4HC
				data.append(CompressionHelper.decompress_lz4(bundle_reader.read(blockInfo.compressed_size),
															 blockInfo.uncompressed_size))
			# elif switch == 4: #LZHAM:
			else:  # no compression
				data.append(bundle_reader.read(blockInfo.compressed_size))

		data_stream = EndianBinaryReader(b''.join(data))
		entry_info_count = blocks_info_reader.read_int()
		for i in range(entry_info_count):
			f = File()
			offset = blocks_info_reader.read_long()
			size = blocks_info_reader.read_long()
			f.flag = blocks_info_reader.read_int()
			f.file_name = os.path.basename(blocks_info_reader.read_string_to_null())
			data_stream.Position = offset
			f.stream = data_stream.read(size)
			self.files.append(f)
