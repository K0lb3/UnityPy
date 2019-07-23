from ..enums import FileType
from .CompressionHelper import gzipMagic, brotliMagic
from ..EndianBinaryReader import EndianBinaryReader
import os


def FileNameWithoutExtension(fileName: str):
	return os.path.splitext(os.path.basename(fileName))[0]


def ListAllFiles(directory: str):
	return [
			val for sublist in [
					[
							os.path.join(dirpath, filename)
							for filename in filenames
					]
					for (dirpath, dirnames, filenames) in os.walk(directory)
					if '.git' not in dirpath
			]
			for val in sublist
	]


def MergeSplitAssets(path: str, allDirectories = False):
	if allDirectories:
		splitFiles = [fp for fp in ListAllFiles(path) if fp[-7:] == ".split0"]
	else:
		splitFiles = [os.path.join(path, fp)
		              for fp in os.listdir(path) if fp[-7:] == ".split0"]
	
	for splitFile in splitFiles:
		destFile = FileNameWithoutExtension(splitFile)
		destPath = os.path.dirname(splitFile)
		destFull = os.path.join(destFile, destPath)
		
		if not os.path.exists(destFull):
			with open(destFull, 'wb') as f:
				i = 0
				while True:
					splitPart = ''.join([destFull, '.split', str(i)])
					if not os.path.isfile(splitPart):
						break
					f.write(open(splitPart, 'rb').read())


def ProcessingSplitFiles(selectFile: list) -> list:
	splitFiles = [fp for fp in selectFile if '.split' in fp]
	selectFile = [f for f in selectFile if f not in splitFiles]
	
	splitFiles = set([FileNameWithoutExtension(fp) for fp in splitFiles])
	for splitFile in splitFiles:
		if os.path.isfile:
			selectFile.append(splitFile)
	return selectFile


def CheckFileType(input):
	if type(input) == str and os.path.isfile(input):
		reader = EndianBinaryReader(open(input, 'rb'))
	else:
		reader = EndianBinaryReader(input)
	
	signature = reader.ReadStringToNull(20)
	reader.Position = 0
	if signature in ["UnityWeb", "UnityRaw", "\xFA\xFA\xFA\xFA\xFA\xFA\xFA\xFA", "UnityFS"]:
		return (FileType.BundleFile, reader)
	elif signature == "UnityWebData1.0":
		return (FileType.WebFile, reader)
	else:
		magic = reader.ReadBytes(2)
		reader.Position = 0
		if gzipMagic == magic:
			return (FileType.WebFile, reader)
		reader.Position = 0x20
		magic = reader.ReadBytes(6)
		reader.Position = 0
		if brotliMagic == magic:
			return (FileType.WebFile, reader)
		return (FileType.AssetsFile, reader)
