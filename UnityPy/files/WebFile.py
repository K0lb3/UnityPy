import io
import os

from ..EndianBinaryReader import EndianBinaryReader
from ..helpers import CompressionHelper


class WebData:
	offset: int
	length: int
	path: str


class File:
	name: str
	stream: io.BytesIO


class WebFile:
	files: list
	_compression = str

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

	def reader_web_data(self, reader):
		"""Extracts the files saved in the WebFile."""
		signature = reader.read_string_to_null()
		if signature != "UnityWebData1.0":
			return
		head_length = reader.read_int()
		data_list = []
		while reader.Position < head_length:
			data = WebData()
			data.offset = reader.read_int()
			data.length = reader.read_int()
			path_length = reader.read_int()
			data.path = reader.read_bytes(path_length).decode('utf8')
			data_list.append(data)

		for data in data_list:
			reader.Position = data.offset
			f = File()
			f.name = os.path.basename(data.path)
			f.stream = io.BytesIO(reader.read(data.length))
			self.files.append(f)
