from helpers import CompressionHelper
from EndianBinaryReader import EndianBinaryReader
import os, io


class StreamFile():
	fileName: str
	stream: io.BytesIO


class BlockInfo():
	compressedSize: int
	uncompressedSize: int
	flag: int
	
	def __init__(self, compressedSize, uncompressedSize, flag):
		self.compressedSize = compressedSize
		self.uncompressedSize = uncompressedSize
		self.flag = flag


class BundleFile():
	# private string path;
	# public string versionPlayer;
	# public string versionEngine;
	# public List<StreamFile> fileList = new List<StreamFile>();
	
	def __init__(self, bundleReader, path):
		self.fileList = []
		self.path = path
		signature = bundleReader.ReadStringToNull()
		format = bundleReader.ReadInt32()
		self.versionPlayer = bundleReader.ReadStringToNull()
		self.versionEngine = bundleReader.ReadStringToNull()
		
		if signature in ["UnityWeb", "UnityRaw", "\xFA\xFA\xFA\xFA\xFA\xFA\xFA\xFA"]:
			if format < 6:
				bundleSize = bundleReader.ReadInt32()
			elif format == 6:
				self.ReadFormat6(bundleReader, True)
				return
			
			dummy2 = bundleReader.ReadInt16()
			offset = bundleReader.ReadInt16()
			dummy3 = bundleReader.ReadInt32()
			lzmaChunks = bundleReader.ReadInt32()
			
			lzmaSize = 0
			streamSize = 0
			
			for i in range(lzmaChunks):
				lzmaSize = bundleReader.ReadInt32()
				streamSize = bundleReader.ReadInt32()
			
			bundleReader.Position = offset
			if signature in ["UnityWeb", "\xFA\xFA\xFA\xFA\xFA\xFA\xFA\xFA"]:
				lzmaBuffer = bundleReader.ReadBytes(lzmaSize)
				self.dataReader = EndianBinaryReader(CompressionHelper.DecompressLZMA(lzmaBuffer))
				self.GetAssetsFiles(self.dataReader, 0)
			elif signature == "UnityRaw":
				self.dataReader = bundleReader
				self.GetAssetsFiles(self.dataReader, offset)
		
		elif signature == "UnityFS":
			if format == 6:
				self.ReadFormat6(bundleReader)
	
	def GetAssetsFiles(self, reader: EndianBinaryReader, offset):
		fileCount = reader.ReadInt32()
		for i in range(fileCount):
			f = object()
			f.name = os.path.basename(reader.ReadStringToNull())
			f.fileOffset = reader.ReadInt32() + offset
			f.fileSize = reader.ReadInt32()
			nextFile = reader.Position
			
			reader.Position = f.fileOffset
			f.stream = io.BytesIO(reader.read(f.fileSize))
			self.fileList.append(f)
			reader.Position = nextFile
	
	def ReadFormat6(self, bundleReader: EndianBinaryReader, padding = False):
		bundleSize = bundleReader.ReadInt64()
		compressedSize = bundleReader.ReadInt32()
		uncompressedSize = bundleReader.ReadInt32()
		flag = bundleReader.ReadInt32()
		if padding:
			bundleReader.ReadByte()
		blockInfoBytes: bytes
		if (flag & 0x80) != 0:  # at end of file
			position = bundleReader.Position
			bundleReader.Position = bundleReader.Length - compressedSize
			blockInfoBytes = bundleReader.ReadBytes(compressedSize)
			bundleReader.Position = position
		else:
			blockInfoBytes = bundleReader.ReadBytes(compressedSize)
		
		switch = flag & 0x3F
		if switch == 1:  # LZMA
			blocksInfoData = CompressionHelper.DecompressLZMA(blockInfoBytes)
		elif switch in [2, 3]:  # LZ4, LZ4HC
			blocksInfoData = CompressionHelper.DecompressLZ4(blockInfoBytes, uncompressedSize)
		# elif switch == 4: #LZHAM:
		else:  # no compression
			blocksInfoData = blockInfoBytes
		
		blocksInfoReader = EndianBinaryReader(blocksInfoData)
		blocksInfoReader.Position = 0x10
		blockcount = blocksInfoReader.ReadInt32()
		blockInfos = [
				BlockInfo(
						uncompressedSize = blocksInfoReader.ReadUInt32(),
						compressedSize = blocksInfoReader.ReadUInt32(),
						flag = blocksInfoReader.ReadInt16()
				)
				for i in range(blockcount)
		]
		
		data = b''
		for blockInfo in blockInfos:
			switch = blockInfo.flag & 0x3F
			
			if switch == 1:  # LZMA
				data += CompressionHelper.DecompressLZMA(bundleReader.read(blockInfo.compressedSize))
			elif switch in [2, 3]:  # LZ4, LZ4HC
				data += CompressionHelper.DecompressLZ4(bundleReader.read(blockInfo.compressedSize), blockInfo.uncompressedSize)
			# elif switch == 4: #LZHAM:
			else:  # no compression
				data += bundleReader.read(blockInfo.compressedSize)
		
		dataStream = EndianBinaryReader(data)
		entryinfo_count = blocksInfoReader.ReadInt32()
		for i in range(entryinfo_count):
			f = File()
			entryinfo_offset = blocksInfoReader.ReadInt64()
			entryinfo_size = blocksInfoReader.ReadInt64()
			f.flag = blocksInfoReader.ReadInt32()
			f.fileName = os.path.basename(blocksInfoReader.ReadStringToNull())
			dataStream.Position = entryinfo_offset
			f.stream = dataStream.read(entryinfo_size)
			self.fileList.append(f)


class File():
	flag: int
	fileName: str
	stream: io.BytesIO
