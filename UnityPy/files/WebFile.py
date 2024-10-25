import gzip
from typing import List, Literal, Optional, Self, Tuple, cast

import brotli

from ..streams import EndianBinaryWriter
from ..streams.EndianBinaryReader import EndianBinaryReader
from .File import ContainerFile, DirectoryInfo, parseable_filetype

GZIP_MAGIC: bytes = b"\x1f\x8b"
BROTLI_MAGIC: bytes = b"brotli"

TCompressionType = Literal["none", "gzip", "brotli"]


@parseable_filetype
class WebFile(ContainerFile):
    """A package which can hold other WebFiles, Bundles and SerialiedFiles.
    It may be compressed via gzip or brotli.

    files -- list of all files in the WebFile
    """

    SIGNATURE_CHECK = b"UnityWebData"
    signature: str
    compression: TCompressionType

    @classmethod
    def probe(cls, reader: EndianBinaryReader) -> bool:
        start_pos = reader.tell()
        if reader.read_bytes(2) == GZIP_MAGIC:
            return True

        reader.seek(0x20)
        if reader.read_bytes(6) == BROTLI_MAGIC:
            return True

        reader.seek(start_pos)
        if reader.read_bytes(len(cls.SIGNATURE_CHECK)) == cls.SIGNATURE_CHECK:
            return True

        return False

    def parse(self, reader: Optional[EndianBinaryReader] = None) -> Self:
        reader = self._opt_get_set_reader(reader)

        # check compression
        magic = reader.read_bytes(2)
        reader.seek(0)

        if magic == GZIP_MAGIC:
            self.compression = "gzip"
            compressed_data = reader.get_bytes()
            decompressed_data = gzip.decompress(compressed_data)
            reader = EndianBinaryReader(decompressed_data, endian="<")
        else:
            reader.seek(0x20)
            magic = reader.read_bytes(6)
            reader.seek(0)
            if BROTLI_MAGIC == magic:
                self.compression = "brotli"
                compressed_data = reader.read(reader.Length)
                # no type hint for brotli.decompress
                decompressed_data = cast(bytes, brotli.decompress(compressed_data))  # type: ignore
                reader = EndianBinaryReader(decompressed_data, endian="<")
            else:
                self.compression = "none"
                reader.endian = "<"

        # signature check not required as we already checked for it in probe
        self.signature = reader.read_string_to_null()

        # read header -> contains file headers
        file_header_end = reader.read_int()
        self.directory_infos = []
        while reader.tell() < file_header_end:
            self.directory_infos.append(
                DirectoryInfo(
                    offset=reader.read_int(),
                    size=reader.read_int(),
                    path=reader.read_string(),
                )
            )
        self.directory_reader = reader
        return self

    def dump(
        self,
        writer: Optional[EndianBinaryWriter] = None,
        compression: Optional[TCompressionType] = None,
    ) -> EndianBinaryWriter:
        if writer is None:
            writer = EndianBinaryWriter(endian="<")
        else:
            raise NotImplementedError("WebFile - dump with writer")

        # write empty header to not having to keep the dumped files in memory
        header_length = (
            # signature - ending with \0
            len(self.signature.encode("utf-8"))
            + 1
            # file header end
            + 4
            # directory infos
            + sum(
                # 4 - offset, 4 - size, 4 - string length, len(path) - string
                12 + len(child.path)
                for child in self.childs or self.directory_infos
            )
        )
        start_offset = writer.tell()
        writer.write_bytes(b"\0" * header_length)

        child_offset_sizes: List[Tuple[int, int]] = []
        if self.childs:
            for child in self.childs:
                child_data = child.dump().get_bytes()
                child_offset_sizes.append((writer.tell(), len(child_data)))
                writer.write_bytes(child_data)
        else:
            for directory_info in self.directory_infos:
                child_offset_sizes.append((writer.tell(), directory_info.size))
                self.directory_reader.seek(directory_info.offset)
                writer.write_bytes(self.directory_reader.read(directory_info.size))

        # write header
        writer.seek(start_offset)
        writer.write_string_to_null(self.signature)
        writer.write_int(header_length)
        for child, (offset, size) in zip(
            self.childs or self.directory_infos, child_offset_sizes
        ):
            writer.write_int(offset)
            writer.write_int(size)
            writer.write_string(child.path)

        writer.seek(0, 2)

        compression = compression or self.compression
        if compression == "gzip":
            compressed_data = gzip.compress(writer.get_bytes())
            writer = EndianBinaryWriter(compressed_data, endian="<")
        elif compression == "brotli":
            compressed_data = cast(bytes, brotli.compress(writer.get_bytes()))  # type: ignore
            writer = EndianBinaryWriter(compressed_data, endian="<")

        return writer


@parseable_filetype
class TuanjieWebFile(WebFile):
    SIGNATURE_CHECK = b"TuanjieWebData"
