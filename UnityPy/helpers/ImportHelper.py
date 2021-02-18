import os
import re

from .CompressionHelper import BROTLI_MAGIC, GZIP_MAGIC
from ..enums import FileType
from ..streams import EndianBinaryReader


def file_name_without_extension(file_name: str) -> str:
    return os.path.splitext(os.path.basename(file_name))[0]


def list_all_files(directory: str) -> list:
    return [
        val
        for sublist in [
            [os.path.join(dir_path, filename) for filename in filenames]
            for (dir_path, dirn_ames, filenames) in os.walk(directory)
            if ".git" not in dir_path
        ]
        for val in sublist
    ]


def find_all_files(directory: str, search_str: str) -> list:
    return [
        val
        for sublist in [
            [
                os.path.join(dir_path, filename)
                for filename in filenames
                if search_str in filename
            ]
            for (dir_path, dirn_ames, filenames) in os.walk(directory)
            if ".git" not in dir_path
        ]
        for val in sublist
    ]


def merge_split_assets(path: str, all_directories=False):
    if all_directories:
        split_files = [fp for fp in list_all_files(path) if fp[-7:] == ".split0"]
    else:
        split_files = [
            os.path.join(path, fp) for fp in os.listdir(path) if fp[-7:] == ".split0"
        ]

    for split_file in split_files:
        dest_file = file_name_without_extension(split_file)
        dest_path = os.path.dirname(split_file)
        dest_full = os.path.join(dest_file, dest_path)

        if not os.path.exists(dest_full):
            with open(dest_full, "wb") as f:
                i = 0
                while True:
                    split_part = "".join([dest_full, ".split", str(i)])
                    if not os.path.isfile(split_part):
                        break
                    f.write(open(split_part, "rb").read())


def processing_split_files(select_file: list) -> list:
    split_files = [fp for fp in select_file if ".split" in fp]
    select_file = [f for f in select_file if f not in split_files]

    split_files = set([file_name_without_extension(fp) for fp in split_files])
    for splitFile in split_files:
        if os.path.isfile:
            select_file.append(splitFile)
    return select_file



def check_file_type(input_) -> (FileType, EndianBinaryReader):
    if isinstance(input_, str) and os.path.isfile(input_):
        reader = EndianBinaryReader(open(input_, "rb"))
    elif isinstance(input_, EndianBinaryReader):
        reader = input_
    else:
        try:
            reader = EndianBinaryReader(input_)
        except:
            return None, None

    if reader.Length < 20:
        return FileType.ResourceFile, reader

    signature = reader.read_string_to_null(20)
    reader.Position = 0
    if signature in [
        "UnityWeb",
        "UnityRaw",
        "\xFA\xFA\xFA\xFA\xFA\xFA\xFA\xFA",
        "UnityFS",
    ]:
        return FileType.BundleFile, reader
    elif signature == "UnityWebData1.0":
        return FileType.WebFile, reader
    elif signature == "PK\x03\x04\x14":
        return FileType.ZIP, reader
    else:
        if reader.Length < 128:
            return FileType.ResourceFile, reader

        magic = bytes(reader.read_bytes(2))
        reader.Position = 0
        if GZIP_MAGIC == magic:
            return FileType.WebFile, reader
        reader.Position = 0x20
        magic = bytes(reader.read_bytes(6))
        reader.Position = 0
        if BROTLI_MAGIC == magic:
            return FileType.WebFile, reader

        # check if AssetsFile
        old_endian = reader.endian
        assets_file = True
        # read as if assetsfile and check version
        # ReadHeader
        reader.Position = 0
        metadata_size = reader.read_u_int()
        file_size = reader.read_u_int()
        version = reader.read_u_int()
        data_offset = reader.read_u_int()

        if version >= 9:
            endian = ">" if reader.read_boolean() else "<"
            reserved = reader.read_bytes(3)
        else:
            reader.Position = file_size - metadata_size
            endian = ">" if reader.read_boolean() else "<"

        if version >= 22:
            metadata_size = reader.read_u_int()
            file_size = reader.read_long()
            data_offset = reader.read_long()
            unknown = reader.read_long()  # unknown

        reader.endian = endian

        if (
            version < 0
            or version > 100
            or any(
                [
                    x < 0 or x > reader.Length
                    for x in [file_size, metadata_size, version, data_offset]
                ]
            )
            or file_size < metadata_size
        ):
            return FileType.ResourceFile, reader

        if version >= 7:
            unity_version = reader.read_string_to_null()
            if len([x for x in re.split(r"\D", unity_version) if x != ""]) < 2:
                assets_file = False

        # check end
        reader.endian = old_endian
        reader.Position = 0
        if assets_file:
            return FileType.AssetsFile, reader
        else:
            return FileType.ResourceFile, reader
