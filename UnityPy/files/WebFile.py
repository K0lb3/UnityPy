from . import File
from ..helpers import CompressionHelper
from ..streams import EndianBinaryReader, EndianBinaryWriter


class WebFile(File.File):
    """A package which can hold other WebFiles, Bundles and SerialiedFiles.
    It may be compressed via gzip or brotli.

    files -- list of all files in the WebFile
    """

    def __init__(self, reader: EndianBinaryReader, parent: File, name=None, **kwargs):
        """Constructor Method"""
        super().__init__(parent=parent, name=name, **kwargs)

        # check compression
        magic = reader.read_bytes(2)
        reader.Position = 0

        if magic == CompressionHelper.GZIP_MAGIC:
            self.packer = "gzip"
            data = CompressionHelper.decompress_gzip(reader.bytes)
            reader = EndianBinaryReader(data, endian="<")
        else:
            reader.Position = 0x20
            magic = reader.read_bytes(6)
            reader.Position = 0
            if CompressionHelper.BROTLI_MAGIC == magic:
                self.packer = "brotli"
                data = CompressionHelper.decompress_brotli(reader.bytes)
                reader = EndianBinaryReader(data, endian="<")
            else:
                self.packer = "none"
                reader.endian = "<"

        # signature check
        signature = reader.read_string_to_null()
        if signature != "UnityWebData1.0":
            return
        self.signature = signature

        # read header -> contains file headers
        head_length = reader.read_int()

        files = []
        while reader.Position < head_length:
            offset = reader.read_int()
            length = reader.read_int()
            path_length = reader.read_int()
            name = bytes(reader.read_bytes(path_length)).decode("utf-8")
            files.append(File.DirectoryInfo(name, offset, length))

        self.read_files(reader, files)

    def save(
        self,
        files: dict = None,
        packer: str = "none",
        signature: str = "UnityWebData1.0",
    ) -> bytes:
        # solve defaults
        if not files:
            files = self.files
        if not packer:
            packer = self.packer

        # get raw data
        files = {
            name: f.bytes if isinstance(f, EndianBinaryReader) else f.save()
            for name, f in files.items()
        }

        # create writer
        writer = EndianBinaryWriter(endian="<")
        # signature
        writer.write_string_to_null(signature)

        # data offset
        offset = sum(
            [
                writer.Position,  # signature
                sum(
                    len(path.encode("utf-8")) for path in files.keys()
                ),  # path of each file
                4 * 3 * len(files),  # 3 ints per file
                4,  # offset int
            ]
        )

        writer.write_int(offset)

        # 1. file headers
        for name, data in files.items():
            # offset
            writer.write_int(offset)
            # length
            length = len(data)
            writer.write_int(length)
            offset += length
            # path
            enc_path = name.encode("utf-8")
            writer.write_int(len(enc_path))
            writer.write(enc_path)

        # 2. file data
        for data in files.values():
            writer.write(data)

        if packer == "gzip":
            return CompressionHelper.compress_gzip(writer.bytes)
        elif packer == "brotli":
            return CompressionHelper.compress_brotli(writer.bytes)
        else:
            return writer.bytes
