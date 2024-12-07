# TODO: implement encryption for saving files
from abc import ABC, ABCMeta
from enum import IntEnum, IntFlag
from typing import Annotated, List, Optional, Self, Union

from attr import define

from ..helpers import CompressionHelper
from ..helpers.ArchiveStorageManager import ArchiveStorageDecryptor
from ..helpers.Tpk import UnityVersion
from ..streams import EndianBinaryReader, EndianBinaryWriter
from .File import ContainerFile, DirectoryInfo, File, parseable_filetype


@define(slots=True)
class BlockInfo:
    flags: int
    compressed_size: int
    decompressed_size: int
    offset: int


class CompressionFlags(IntEnum):
    NONE = 0
    LZMA = 1
    LZ4 = 2
    LZ4HC = 3
    LZHAM = 4


class ArchiveFlagsOld(IntFlag):
    CompressionTypeMask = 0x3F
    BlocksAndDirectoryInfoCombined = 0x40
    BlocksInfoAtTheEnd = 0x80
    OldWebPluginCompatibility = 0x100
    UsesAssetBundleEncryption = 0x200


class ArchiveFlags(IntFlag):
    CompressionTypeMask = 0x3F
    BlocksAndDirectoryInfoCombined = 0x40
    BlocksInfoAtTheEnd = 0x80
    OldWebPluginCompatibility = 0x100
    BlockInfoNeedPaddingAtStart = 0x200
    UsesAssetBundleEncryption = 0x400


class BundleFile(ContainerFile, ABC, metaclass=ABCMeta):
    signature: str
    stream_version: int
    unity_version: str
    minimum_revision: str
    block_infos: List[BlockInfo]
    block_reader: EndianBinaryReader

    def parse(self, reader: Optional[EndianBinaryReader] = None) -> Self:
        reader = self._opt_get_set_reader(reader)

        self.signature = reader.read_string_to_null()
        self.stream_version = reader.read_u_int()
        if self.stream_version > 0x1000000:
            reader.seek(reader.tell() - 4)
            reader.endian = "<" if reader.endian == ">" else ">"
            self.stream_version = reader.read_u_int()

        self.unity_version = reader.read_string_to_null()
        self.minimum_revision = reader.read_string_to_null()
        return self

    def dump(self, writer: Optional[EndianBinaryWriter] = None) -> EndianBinaryWriter:
        writer = writer or EndianBinaryWriter(endian=self.reader.endian)

        writer.write_string_to_null(self.signature)
        writer.write_u_int(self.stream_version)
        writer.write_string_to_null(self.unity_version)
        writer.write_string_to_null(self.minimum_revision)
        return writer


@parseable_filetype
class BundleFileArchive(BundleFile):
    @classmethod
    def probe(cls, reader: EndianBinaryReader) -> bool:
        signature = reader.read_string_to_null()

        return signature == "UnityArchive"

    def parse(self, reader: Optional[EndianBinaryReader] = None) -> Self:
        super().parse(reader)
        raise NotImplementedError("BundleFile - UnityArchive")

    def dump(self, writer: Optional[EndianBinaryWriter] = None) -> EndianBinaryWriter:
        raise NotImplementedError("BundleFile - UnityArchive")


@parseable_filetype
class BundleFileFS(BundleFile):
    size: int
    version: UnityVersion
    dataflags: Union[ArchiveFlags, ArchiveFlagsOld]
    decompressed_data_hash: Annotated[bytes, 16]
    uses_block_alignment: bool = False
    decryptor: Optional[ArchiveStorageDecryptor] = None

    @classmethod
    def probe(cls, reader: EndianBinaryReader) -> bool:
        signature = reader.read_string_to_null()
        endian = reader.endian
        reader.endian = ">"
        version = reader.read_u_int()
        reader.endian = endian

        return signature == "UnityFS" or (signature == "UnityRaw" and version == 6)

    def parse(self, reader: Optional[EndianBinaryReader] = None) -> Self:
        reader = self._opt_get_set_reader(reader)

        super().parse(reader)
        self.size = reader.read_long()

        # header
        header_compressed_size, header_uncompressed_size, dataflags = (
            reader.read_u_int_array(3)
        )

        # https://issuetracker.unity3d.com/issues/files-within-assetbundles-do-not-start-on-aligned-boundaries-breaking-patching-on-nintendo-switch
        # Unity CN introduced encryption before the alignment fix was introduced.
        # Unity CN used the same flag for the encryption as later on the alignment fix,
        # so we have to check the version to determine the correct flag set.
        version = UnityVersion.fromString(self.minimum_revision)
        self.version = version
        if (
            # < 2000, < 2020.3.34, < 2021.3.2, < 2022.1.1
            version.major < 2020
            or (version.major == 2020 and version < UnityVersion.fromList(2020, 3, 34))
            or (version.major == 2021 and version < UnityVersion.fromList(2021, 3, 2))
            or (version.major == 2022 and version < UnityVersion.fromList(2022, 1, 1))
        ):
            self.dataflags = ArchiveFlagsOld(dataflags)
        else:
            self.dataflags = ArchiveFlags(dataflags)

        if self.dataflags & self.dataflags.UsesAssetBundleEncryption:
            self.decryptor = ArchiveStorageDecryptor(reader)

        # check if we need to align the reader
        # - align to 16 bytes and check if all are 0
        # - if not, reset the reader to the previous position
        if self.stream_version >= 7:
            reader.align_stream(16)
            self.uses_block_alignment = True
        elif version >= UnityVersion.fromList(2019, 4):
            pre_align = reader.tell()
            align_data = reader.read((16 - pre_align % 16) % 16)
            if any(align_data):
                reader.seek(pre_align)
            else:
                self.uses_block_alignment = True

        start = reader.tell()
        seek_back = -1
        if (
            self.dataflags & ArchiveFlags.BlocksInfoAtTheEnd
        ):  # kArchiveBlocksInfoAtTheEnd
            seek_back = reader.tell()
            reader.seek(reader.Length - header_compressed_size)
        # else:  # 0x40 kArchiveBlocksAndDirectoryInfoCombined

        blocksInfoBytes = reader.read_bytes(header_compressed_size)
        blocksInfoBytes = self._decompress_data(
            blocksInfoBytes, header_uncompressed_size, self.dataflags
        )
        blocksInfoReader = EndianBinaryReader(blocksInfoBytes, offset=start)

        self.decompressed_data_hash = blocksInfoReader.read_bytes(16)

        blocksInfoCount = blocksInfoReader.read_int()
        assert blocksInfoCount > 0, "blocksInfoCount <= 0"
        block_offset = 0

        def offset(compressed_size: int):
            nonlocal block_offset
            old_offset = block_offset
            block_offset += compressed_size
            return old_offset

        self.block_infos = [
            BlockInfo(
                flags,
                compressed_size,
                decompressed_size,
                offset(compressed_size),
            )
            for (
                decompressed_size,
                compressed_size,
                flags,
            ) in blocksInfoReader.unpack_array("IIH", blocksInfoCount)
        ]

        directory_count = blocksInfoReader.read_int()
        self.directory_infos = [
            DirectoryInfo(
                offset=blocksInfoReader.read_long(),  # offset
                size=blocksInfoReader.read_long(),  # size
                flags=blocksInfoReader.read_u_int(),  # flags
                path=blocksInfoReader.read_string_to_null(),  # path
            )
            for _ in range(directory_count)
        ]

        if seek_back != -1:
            reader.seek(seek_back)

        if (
            isinstance(self.dataflags, ArchiveFlags)
            and self.dataflags & ArchiveFlags.BlockInfoNeedPaddingAtStart
        ):
            reader.align_stream(16)

        self.directory_reader = EndianBinaryReader(
            b"".join(
                self._decompress_data(
                    reader.read_bytes(blockInfo.compressed_size),
                    blockInfo.decompressed_size,
                    blockInfo.flags,
                    i,
                )
                for i, blockInfo in enumerate(self.block_infos)
            ),
            offset=(blocksInfoReader.real_offset()),
        )
        return self

    def dump(
        self,
        writer: Optional[EndianBinaryWriter] = None,
        block_chunk_flag: Optional[int] = None,
        block_chunk_size: Optional[int] = None,
    ) -> EndianBinaryWriter:
        # File Structure:
        # header:
        #   ...
        #   size
        #   compressedSize
        #   uncompressedSize
        #   dataflags
        #   ..align/seek to end
        #   compressed block info data
        #      hash
        #      blockCount
        #      blockInfos
        #      directoryCount
        #      directoryInfos
        #   compressed directory data (offset of previous in total)

        writer = super().dump(writer)

        # munch childs/files together
        new_directory_infos: List[DirectoryInfo] = []
        childs = self.childs or self.directory_infos
        directory_info_flag = (
            self.directory_infos[0].flags if self.directory_infos else 0
        )

        directory_datas = []
        uncompressed_directory_datas_size = 0

        childs = self.childs or self.directory_infos
        for child in childs:
            if isinstance(child, File):
                child_data = child.dump().get_bytes()
                path = child.name
            else:
                self.directory_reader.seek(child.offset)
                child_data = self.directory_reader.read(child.size)
                path = child.path

            new_directory_infos.append(
                DirectoryInfo(
                    path=path,
                    offset=uncompressed_directory_datas_size,
                    size=len(child_data),
                    flags=directory_info_flag,
                )
            )
            directory_datas.append(child_data)
            uncompressed_directory_datas_size += len(child_data)
        directory_datas = b"".join(directory_datas)

        # compress blocks
        new_block_infos: List[BlockInfo] = []
        compressed_directory_datas = []
        compressed_directory_datas_size = 0

        block_chunk_flag = block_chunk_flag or self.block_infos[0].flags
        block_chunk_size = block_chunk_size or self.block_infos[0].decompressed_size

        for chunk_start in range(0, len(directory_datas), block_chunk_size):
            chunk = directory_datas[chunk_start : chunk_start + block_chunk_size]
            compressed_chunk = self._compress_data(chunk, block_chunk_flag)
            new_block_infos.append(
                BlockInfo(
                    flags=block_chunk_flag,
                    compressed_size=len(compressed_chunk),
                    decompressed_size=len(chunk),
                    offset=compressed_directory_datas_size,
                )
            )
            compressed_directory_datas.append(compressed_chunk)
            compressed_directory_datas_size += len(compressed_chunk)

        compressed_directory_datas = b"".join(compressed_directory_datas)
        del directory_datas

        # write block info
        block_info_writer = EndianBinaryWriter(endian=">")
        # decompressed_data_hash seems to be nearly always 16x 0
        block_info_writer.write_bytes(self.decompressed_data_hash)
        block_info_writer.write_int(len(new_block_infos))
        for block_info in new_block_infos:
            block_info_writer.write_int(block_info.decompressed_size)
            block_info_writer.write_int(block_info.compressed_size)
            block_info_writer.write_u_short(block_info.flags)
        block_info_writer.write_int(len(new_directory_infos))
        for directory_info in new_directory_infos:
            block_info_writer.write_long(directory_info.offset)
            block_info_writer.write_long(directory_info.size)
            block_info_writer.write_u_int(directory_info.flags)
            block_info_writer.write_string_to_null(directory_info.path)

        uncompressed_block_info_size = block_info_writer.tell()
        compressed_block_info = self._compress_data(
            block_info_writer.bytes, self.dataflags
        )
        del block_info_writer

        # estimate size
        def align(alignment: int, value: int) -> int:
            return (alignment - value % alignment) % alignment

        size = writer.Position + 8 + 12  # total size, block header sizes & flag
        if self.stream_version >= 7 or self.uses_block_alignment:
            size += align(16, size)
        if (
            self.dataflags & ArchiveFlags.BlocksInfoAtTheEnd
        ):  # kArchiveBlocksInfoAtTheEnd
            if (
                isinstance(self.dataflags, ArchiveFlags)
                and self.dataflags & ArchiveFlags.BlockInfoNeedPaddingAtStart
            ):
                size += align(16, size)
            size += len(compressed_directory_datas)
            size += len(compressed_block_info)
        else:
            size += len(compressed_block_info)
            if (
                isinstance(self.dataflags, ArchiveFlags)
                and self.dataflags & ArchiveFlags.BlockInfoNeedPaddingAtStart
            ):
                size += align(16, size)
            size += len(compressed_directory_datas)

        # write file
        writer.write_long(size)
        writer.write_u_int(len(compressed_block_info))
        writer.write_u_int(uncompressed_block_info_size)
        dataflags = self.dataflags
        if dataflags & dataflags.UsesAssetBundleEncryption:
            dataflags ^= dataflags.UsesAssetBundleEncryption
        writer.write_u_int(dataflags)

        if self.stream_version >= 7 or self.uses_block_alignment:
            writer.align_stream(16)

        if (
            self.dataflags & ArchiveFlags.BlocksInfoAtTheEnd
        ):  # kArchiveBlocksInfoAtTheEnd
            if (
                isinstance(self.dataflags, ArchiveFlags)
                and self.dataflags & ArchiveFlags.BlockInfoNeedPaddingAtStart
            ):
                writer.align_stream(16)
            writer.write_bytes(compressed_directory_datas)
            writer.write_bytes(compressed_block_info)
        else:
            writer.write_bytes(compressed_block_info)
            if (
                isinstance(self.dataflags, ArchiveFlags)
                and self.dataflags & ArchiveFlags.BlockInfoNeedPaddingAtStart
            ):
                writer.align_stream(16)
            writer.write_bytes(compressed_directory_datas)

        return writer

    def _decompress_data(
        self,
        compressed_data: bytes,
        uncompressed_size: int,
        flags: Union[int, ArchiveFlags, ArchiveFlagsOld],
        index: int = 0,
    ) -> bytes:
        """
        Parameters
        ----------
        compressed_data : bytes
            The compressed data.
        uncompressed_size : int
            The uncompressed size of the data.
        flags : int
            The flags of the data.

        Returns
        -------
        bytes
            The decompressed data."""
        comp_flag = CompressionFlags(flags & ArchiveFlags.CompressionTypeMask)

        if comp_flag == CompressionFlags.LZMA:  # LZMA
            return CompressionHelper.decompress_lzma(compressed_data)
        elif comp_flag in [CompressionFlags.LZ4, CompressionFlags.LZ4HC]:  # LZ4, LZ4HC
            if self.decryptor is not None and flags & 0x100:
                compressed_data = self.decryptor.decrypt_block(compressed_data, index)
            return CompressionHelper.decompress_lz4(compressed_data, uncompressed_size)
        elif comp_flag == CompressionFlags.LZHAM:  # LZHAM
            raise NotImplementedError("LZHAM decompression not implemented")
        else:
            return compressed_data

    def _compress_data(
        self, data: bytes, flags: Union[int, ArchiveFlags, ArchiveFlagsOld]
    ) -> bytes:
        """
        Parameters
        ----------
        data : bytes
            The data to compress.
        flags : int
            The flags of the data.

        Returns
        -------
        bytes
            The compressed data."""
        comp_flag = CompressionFlags(flags & ArchiveFlags.CompressionTypeMask)

        if comp_flag == CompressionFlags.LZMA:  # LZMA
            return CompressionHelper.compress_lzma(data)
        elif comp_flag in [CompressionFlags.LZ4, CompressionFlags.LZ4HC]:  # LZ4, LZ4HC
            return CompressionHelper.compress_lz4(data)
        elif comp_flag == CompressionFlags.LZHAM:  # LZHAM
            raise NotImplementedError("LZHAM compression not implemented")
        else:
            return data


@parseable_filetype
class BundleFileWeb(BundleFile):
    byteStart: int
    numberOfLevelsToDownloadBeforeStreaming: int
    hash: Optional[Annotated[bytes, 16]]
    crc: Optional[int]
    completeFileSize = Optional[int]
    fileInfoHeaderSize = Optional[int]

    @classmethod
    def probe(cls, reader: EndianBinaryReader) -> bool:
        signature = reader.read_string_to_null()
        endian = reader.endian
        reader.endian = ">"
        version = reader.read_u_int()
        reader.endian = endian

        return signature == "UnityWeb" or (signature == "UnityRaw" and version != 6)

    def parse(self, reader: Optional[EndianBinaryReader] = None) -> Self:
        reader = self._opt_get_set_reader(reader)

        super().parse(reader)

        version = self.stream_version
        if version >= 4:
            self.hash = reader.read_bytes(16)
            self.crc = reader.read_u_int()

        self.byteStart = reader.read_u_int()
        headerSize = reader.read_u_int()
        self.numberOfLevelsToDownloadBeforeStreaming = reader.read_u_int()
        levelCount = reader.read_int()
        self.block_infos = [
            BlockInfo(
                compressed_size=reader.read_u_int(),  # compressedSize
                decompressed_size=reader.read_u_int(),  # uncompressedSize
                flags=0,
                offset=0,
            )
            for _ in range(levelCount)
        ]

        block_offset = 0
        for block in self.block_infos:
            block.offset = block_offset
            block_offset += block.compressed_size

        if version >= 2:
            self.completeFileSize = reader.read_u_int()

        if version >= 3:
            self.fileInfoHeaderSize = reader.read_u_int()

        reader.seek(headerSize)

        uncompressedBytes = reader.read_bytes(self.block_infos[-1].compressed_size)
        if self.signature == "UnityWeb":
            uncompressedBytes = CompressionHelper.decompress_lzma(
                uncompressedBytes, True
            )

        directory_reader = EndianBinaryReader(uncompressedBytes, offset=headerSize)
        self.directory_reader = directory_reader
        nodesCount = directory_reader.read_int()
        self.directory_infos = [
            DirectoryInfo(
                path=directory_reader.read_string_to_null(),  # path
                offset=directory_reader.read_u_int(),  # offset
                size=directory_reader.read_u_int(),  # size
            )
            for _ in range(nodesCount)
        ]
        return self

    def dump(self, writer: Optional[EndianBinaryWriter] = None) -> EndianBinaryWriter:
        writer = super().dump(writer)

        # Calculate fileInfoHeaderSize for set offsets
        file_info_header_size = 4  # for nodesCount
        childs = self.childs or self.directory_infos
        for child in childs:
            file_info_header_size += (
                len(child.name.encode("utf8")) + 1
            )  # +1 for null terminator
            file_info_header_size += 4 * 2  # 4 bytes each for offset and size

        file_info_header_padding_size = (
            4 - (file_info_header_size % 4) if file_info_header_size % 4 != 0 else 0
        )
        file_info_header_size += file_info_header_padding_size

        # Prepare directory info
        directory_info_writer = EndianBinaryWriter()
        directory_info_writer.write_int(len(self.files))  # nodesCount

        file_content_writer = EndianBinaryWriter()
        current_offset = file_info_header_size

        for child in childs:
            directory_info_writer.write_string_to_null(child.name)
            directory_info_writer.write_u_int(current_offset)
            # Get file content
            if isinstance(child, File):
                file_data = child.dump().get_bytes()
            else:
                self.directory_reader.seek(child.offset)
                file_data = self.directory_reader.read_bytes(child.size)

            file_size = len(file_data)
            directory_info_writer.write_u_int(file_size)

            file_content_writer.write_bytes(file_data)
            current_offset += file_size

        directory_info_writer.write(b"\x00" * file_info_header_padding_size)
        uncompressed_directory_info = directory_info_writer.bytes
        uncompressed_file_content = file_content_writer.bytes

        # Combine directory info and file content
        uncompressed_content = uncompressed_directory_info + uncompressed_file_content
        compressed_content = uncompressed_content
        if self.signature == "UnityWeb":
            compressed_content = CompressionHelper.compress_lzma(
                uncompressed_content, True
            )

        # Write header
        header_size = writer.Position + 24  # assuming levelCount = 1
        if self.stream_version >= 2:
            header_size += 4
        if self.stream_version >= 3:
            header_size += 4
        if self.stream_version >= 4:
            header_size += 20

        # pad to multiple of 4
        header_size = (header_size + 3) & ~3

        if self.stream_version >= 4:
            writer.write_bytes(self.hash)
            writer.write_u_int(self.crc)

        writer.write_u_int(
            header_size + len(compressed_content)
        )  # minimumStreamedBytes (same as completeFileSize)
        writer.write_u_int(header_size)  # headerSize
        writer.write_u_int(1)  # numberOfLevelsToDownloadBeforeStreaming (always 1)
        writer.write_int(1)  # levelCount (always 1)

        writer.write_u_int(len(compressed_content))  # compressedSize
        writer.write_u_int(len(uncompressed_content))  # uncompressedSize

        if self.stream_version >= 2:
            writer.write_u_int(
                header_size + len(compressed_content)
            )  # completeFileSize

        if self.stream_version >= 3:
            writer.write_u_int(file_info_header_size)  # file_info_header_size

        # align header
        writer.align_stream(4)

        # Write compressed content
        writer.write_bytes(compressed_content)

        return writer
