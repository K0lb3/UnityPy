import io
import os

from ..EndianBinaryReader import EndianBinaryReader
from ..EndianBinaryWriter import EndianBinaryWriter
from ..helpers import CompressionHelper


class WebFile:
	files: list
	compression: str
	signature: str
	"""A package which can hold other WebFiles, Bundles and SerialiedFiles.
	It may be compressed via gzip or brotli.

	files -- list of all files in the WebFile
	"""

	def __init__(self, reader: EndianBinaryReader):
		self.files = []
		magic = reader.read_bytes(2)
		reader.Position = 0

		if magic == CompressionHelper.GZIP_MAGIC:
			self._compression = 'gzip'
			data = CompressionHelper.decompress_gzip(reader.bytes)
			binary_reader = EndianBinaryReader(data, endian='<')
			self.reader_web_data(binary_reader)
		else:
			reader.Position = 0x20
			magic = reader.read_bytes(6)
			reader.Position = 0
			if CompressionHelper.BROTLI_MAGIC == magic:
				self._compression = 'brotli'
				data = CompressionHelper.decompress_brotli(reader.bytes)
				binary_reader = EndianBinaryReader(data, endian='<')
				self.reader_web_data(binary_reader)
			else:
				self._compression = None
				reader.endian = '<'
				self.reader_web_data(reader)

	def reader_web_data(self, reader: EndianBinaryReader):
		"""Extracts the files saved in the WebFile."""
		signature = reader.read_string_to_null()
		if signature != "UnityWebData1.0":
			return

		head_length = reader.read_int()

		while reader.Position < head_length:
			self.files.append(WebData(reader))

		for f in self.files:
			f.read_data(reader)

	def save(self) -> bytes:
		files = self.files

		writer = EndianBinaryWriter(endian="<")
		# signature
		writer.write_string_to_null(self.signature)

		offset = sum([
			writer.Position,  # signature
			sum(len(f.path.encode("utf8")) for f in files),  # path of each file
			4 * 3 * len(files),  # 3 ints per file
			4  # offset int
		])

		# head_length
		writer.write_int(offset)
		# 1. data list
		for f in files:
			offset = f.write(writer, offset)
		# 2. data
		for f in files:
			writer.write(f.stream.getbuffer())

		data = writer.bytes
		if self.compression == "gzip":
			data = CompressionHelper.compress_gzip(data)
		elif self.compression == "brotli":
			data = CompressionHelper.compress_brotli(data)
		return data

	def __repr__(self):
		return "<%s>" % (
			self.__class__.__name__
		)


class WebData:
	offset: int
	length: int
	path: str
	stream: io.BytesIO

	def __init__(self, reader: EndianBinaryReader):
		self.offset = reader.read_int()
		self.length = reader.read_int()
		path_length = reader.read_int()
		self.path = reader.read_bytes(path_length).decode('utf8')

	def write(self, writer: EndianBinaryWriter, offset) -> int:
		# reverse of __init__
		# returns increased offset

		# offset
		writer.write_int(offset)
		# length
		length = len(self.stream.getbuffer())
		writer.write_int(length)
		# path
		enc_path = self.path.encode("utf8")
		writer.write_int(len(enc_path))
		writer.write(enc_path)

		return offset + length

	def read_data(self, reader: EndianBinaryReader):
		reader.Position = self.offset
		self.stream = io.BytesIO(reader.read(self.length))

	@property
	def name(self):
		return os.path.basename(self.path)

	def __repr__(self):
		return "<%s %s>" % (
			self.__class__.__name__, self.name
		)
