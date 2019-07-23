from ..helpers import CompressionHelper
import os
from ..EndianBinaryReader import EndianBinaryReader
import io


class WebData():
	dataOffset: 'int'
	dataLength: 'int'
	path: str


class WebFile():
	def __init__(self, reader):
		self.fileList = []
		
		magic = reader.ReadBytes(2)
		reader.Position = 0
		
		if magic == CompressionHelper.gzipMagic:
			data = CompressionHelper.DecompressGZIP(reader.bytes)
			binaryReader = EndianBinaryReader(data, endian = '<')
			self.ReadWebData(binaryReader)
		else:
			reader.Position = 0x20
			magic = reader.ReadBytes(6)
			reader.Position = 0
			if CompressionHelper.brotliMagic == magic:
				data = CompressionHelper.DecompressBrotli(reader.bytes)
				binaryReader = EndianBinaryReader(data, endian = '<')
				self.ReadWebData(binaryReader)
			else:
				reader.endian = '<'  # little endian
				self.ReadWebData(reader)
	
	def ReadWebData(self, reader):
		signature = reader.ReadStringToNull()
		if signature != "UnityWebData1.0":
			return
		headLength = reader.ReadInt32()
		self.dataList = []
		while reader.Position < headLength:
			data = WebData()
			data.dataOffset = reader.ReadInt32()
			data.dataLength = reader.ReadInt32()
			
			pathLength = reader.ReadInt32()
			data.path = reader.ReadBytes(pathLength).decode('utf8')
			self.dataList.append(data)
		
		for data in self.dataList:
			f = File()
			f.fileName = os.path.basename(data.path)
			reader.Position = data.dataOffset
			f.stream = io.BytesIO(reader.read(data.dataLength))
			self.fileList.append(f)


class File:
	fileName: str
	stream: io.BytesIO
