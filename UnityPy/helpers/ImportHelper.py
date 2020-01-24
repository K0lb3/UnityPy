import os

from .CompressionHelper import BROTLI_MAGIC, GZIP_MAGIC
from ..EndianBinaryReader import EndianBinaryReader
from ..enums import FileType


def file_name_without_extension(file_name: str) -> str:
	return os.path.splitext(os.path.basename(file_name))[0]


def list_all_files(directory: str) -> list:
	return [
		val for sublist in [
			[
				os.path.join(dir_path, filename)
				for filename in filenames
			]
			for (dir_path, dirn_ames, filenames) in os.walk(directory)
			if '.git' not in dir_path
		]
		for val in sublist
	]


def find_all_files(directory: str, search_str: str) -> list:
	return [
		val for sublist in [
			[
				os.path.join(dir_path, filename)
				for filename in filenames
				if search_str in filename
			]
			for (dir_path, dirn_ames, filenames) in os.walk(directory)
			if '.git' not in dir_path
		]
		for val in sublist
	]


def merge_split_assets(path: str, all_directories=False):
	if all_directories:
		split_files = [fp for fp in list_all_files(path) if fp[-7:] == ".split0"]
	else:
		split_files = [os.path.join(path, fp) for fp in os.listdir(path) if fp[-7:] == ".split0"]

	for split_file in split_files:
		dest_file = file_name_without_extension(split_file)
		dest_path = os.path.dirname(split_file)
		dest_full = os.path.join(dest_file, dest_path)

		if not os.path.exists(dest_full):
			with open(dest_full, 'wb') as f:
				i = 0
				while True:
					split_part = ''.join([dest_full, '.split', str(i)])
					if not os.path.isfile(split_part):
						break
					f.write(open(split_part, 'rb').read())


def processing_split_files(select_file: list) -> list:
	split_files = [fp for fp in select_file if '.split' in fp]
	select_file = [f for f in select_file if f not in split_files]

	split_files = set([file_name_without_extension(fp) for fp in split_files])
	for splitFile in split_files:
		if os.path.isfile:
			select_file.append(splitFile)
	return select_file


def check_file_type(input_) -> (FileType, EndianBinaryReader):
	if isinstance(input_, str) and os.path.isfile(input_):
		reader = EndianBinaryReader(open(input_, 'rb'))
	else:
		reader = EndianBinaryReader(input_)

	signature = reader.read_string_to_null(20)
	reader.Position = 0
	if signature in ["UnityWeb", "UnityRaw", "\xFA\xFA\xFA\xFA\xFA\xFA\xFA\xFA", "UnityFS"]:
		return FileType.BundleFile, reader
	elif signature == "UnityWebData1.0":
		return FileType.WebFile, reader
	elif signature == "PK\x03\x04\x14":
		return FileType.ZIP, reader
	else:
		magic = reader.read_bytes(2)
		reader.Position = 0
		if GZIP_MAGIC == magic:
			return FileType.WebFile, reader
		reader.Position = 0x20
		magic = reader.read_bytes(6)
		reader.Position = 0
		if BROTLI_MAGIC == magic:
			return FileType.WebFile, reader
		return FileType.AssetsFile, reader
