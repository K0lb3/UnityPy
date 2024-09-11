# TODO: implement encryption for saving files
from collections import namedtuple
import re
from typing import Tuple, Union

from . import File
from ..enums import ArchiveFlags, ArchiveFlagsOld, CompressionFlags
from ..helpers import ArchiveStorageManager, CompressionHelper
from ..streams import EndianBinaryReader, EndianBinaryWriter

from .. import config

BlockInfo = namedtuple("BlockInfo", "uncompressedSize compressedSize flags")
DirectoryInfoFS = namedtuple("DirectoryInfoFS", "offset size flags path")
reVersion = re.compile(r"(\d+)\.(\d+)\.(\d+)\w.+")


class BundleFile(File.File):
    format: int
    is_changed: bool
    signature: str
    version_engine: str
    version_player: str
    dataflags: Tuple[ArchiveFlags, ArchiveFlagsOld]
    decryptor: ArchiveStorageManager.ArchiveStorageDecryptor = None
    _uses_block_alignment: bool = False

    def __init__(
        self, reader: EndianBinaryReader, parent: File, name: str = None, **kwargs
    ):
        super().__init__(parent=parent, name=name, **kwargs)
        signature = self.signature = reader.read_string_to_null()
        self.version = reader.read_u_int()
        self.version_player = reader.read_string_to_null()
        self.version_engine = reader.read_string_to_null()

        if signature == "UnityArchive":
            raise NotImplementedError("BundleFile - UnityArchive")
        elif signature in ["UnityWeb", "UnityRaw"]:
            m_DirectoryInfo, blocksReader = self.read_web_raw(reader)
        elif signature == "UnityFS":
            m_DirectoryInfo, blocksReader = self.read_fs(reader)
        else:
            raise NotImplementedError(f"Unknown Bundle signature: {signature}")

        self.read_files(blocksReader, m_DirectoryInfo)

    def read_web_raw(self, reader: EndianBinaryReader):
        # def read_header_and_blocks_info(self, reader:EndianBinaryReader):
        version = self.version
        if version >= 4:
            self._hash = reader.read_bytes(16)
            self.crc = reader.read_u_int()

        minimumStreamedBytes = reader.read_u_int()
        headerSize = reader.read_u_int()
        numberOfLevelsToDownloadBeforeStreaming = reader.read_u_int()
        levelCount = reader.read_int()
        reader.Position += 4 * 2 * (levelCount - 1)

        compressedSize = reader.read_u_int()
        uncompressedSize = reader.read_u_int()

        if version >= 2:
            completeFileSize = reader.read_u_int()

        if version >= 3:
            fileInfoHeaderSize = reader.read_u_int()

        reader.Position = headerSize

        uncompressedBytes = reader.read_bytes(compressedSize)
        if self.signature == "UnityWeb":
            uncompressedBytes = CompressionHelper.decompress_lzma(uncompressedBytes, True)

        blocksReader = EndianBinaryReader(uncompressedBytes, offset=headerSize)
        nodesCount = blocksReader.read_int()
        m_DirectoryInfo = [
            File.DirectoryInfo(
                blocksReader.read_string_to_null(),  # path
                blocksReader.read_u_int(),  # offset
                blocksReader.read_u_int(),  # size
            )
            for _ in range(nodesCount)
        ]

        return m_DirectoryInfo, blocksReader

    def read_fs(self, reader: EndianBinaryReader):
        size = reader.read_long()

        # header
        compressedSize = reader.read_u_int()
        uncompressedSize = reader.read_u_int()
        self.dataflags = reader.read_u_int()

        version = self.get_version_tuple()
        # https://issuetracker.unity3d.com/issues/files-within-assetbundles-do-not-start-on-aligned-boundaries-breaking-patching-on-nintendo-switch
        # Unity CN introduced encryption before the alignment fix was introduced.
        # Unity CN used the same flag for the encryption as later on the alignment fix,
        # so we have to check the version to determine the correct flag set.
        if (
            version < (2020,)
            or (version[0] == 2020 and version < (2020, 3, 34))
            or (version[0] == 2021 and version < (2021, 3, 2))
            or (version[0] == 2022 and version < (2022, 1, 1))
        ):
            self.dataflags = ArchiveFlagsOld(self.dataflags)
        else:
            self.dataflags = ArchiveFlags(self.dataflags)

        if self.dataflags & self.dataflags.UsesAssetBundleEncryption:
            self.decryptor = ArchiveStorageManager.ArchiveStorageDecryptor(reader)

        # check if we need to align the reader
        # - align to 16 bytes and check if all are 0
        # - if not, reset the reader to the previous position
        if self.version >= 7:
            reader.align_stream(16)
            self._uses_block_alignment = True
        elif version >= (2019, 4):
            pre_align = reader.Position
            align_data = reader.read((16 - pre_align % 16) % 16)
            if any(align_data):
                reader.Position = pre_align
            else:
                self._uses_block_alignment = True

        start = reader.Position
        if (
            self.dataflags & ArchiveFlags.BlocksInfoAtTheEnd
        ):  # kArchiveBlocksInfoAtTheEnd
            reader.Position = reader.Length - compressedSize
            blocksInfoBytes = reader.read_bytes(compressedSize)
            reader.Position = start
        else:  # 0x40 kArchiveBlocksAndDirectoryInfoCombined
            blocksInfoBytes = reader.read_bytes(compressedSize)

        blocksInfoBytes = self.decompress_data(
            blocksInfoBytes, uncompressedSize, self.dataflags
        )
        blocksInfoReader = EndianBinaryReader(blocksInfoBytes, offset=start)

        uncompressedDataHash = blocksInfoReader.read_bytes(16)
        blocksInfoCount = blocksInfoReader.read_int()

        m_BlocksInfo = [
            BlockInfo(
                blocksInfoReader.read_u_int(),  # uncompressedSize
                blocksInfoReader.read_u_int(),  # compressedSize
                blocksInfoReader.read_u_short(),  # flags
            )
            for _ in range(blocksInfoCount)
        ]

        nodesCount = blocksInfoReader.read_int()
        m_DirectoryInfo = [
            DirectoryInfoFS(
                blocksInfoReader.read_long(),  # offset
                blocksInfoReader.read_long(),  # size
                blocksInfoReader.read_u_int(),  # flags
                blocksInfoReader.read_string_to_null(),  # path
            )
            for _ in range(nodesCount)
        ]

        if m_BlocksInfo:
            self._block_info_flags = m_BlocksInfo[0].flags

        if (
            isinstance(self.dataflags, ArchiveFlags)
            and self.dataflags & ArchiveFlags.BlockInfoNeedPaddingAtStart
        ):
            reader.align_stream(16)

        blocksReader = EndianBinaryReader(
            b"".join(
                self.decompress_data(
                    reader.read_bytes(blockInfo.compressedSize),
                    blockInfo.uncompressedSize,
                    blockInfo.flags,
                    i,
                )
                for i, blockInfo in enumerate(m_BlocksInfo)
            ),
            offset=(blocksInfoReader.real_offset()),
        )

        return m_DirectoryInfo, blocksReader

    def save(self, packer=None):
        """
        Rewrites the BundleFile and returns it as bytes object.

        packer:
            can be either one of the following strings
            or tuple consisting of (block_info_flag, data_flag)
            allowed strings:
                none - no compression, default, safest bet
                lz4 - lz4 compression
                original - uses the original flags
        """
        # file_header
        #     signature    (string_to_null)
        #     format        (int)
        #     version_player    (string_to_null)
        #     version_engine    (string_to_null)
        writer = EndianBinaryWriter()

        writer.write_string_to_null(self.signature)
        writer.write_u_int(self.version)
        writer.write_string_to_null(self.version_player)
        writer.write_string_to_null(self.version_engine)

        if self.signature == "UnityArchive":
            raise NotImplementedError("BundleFile - UnityArchive")
        elif self.signature in ["UnityWeb", "UnityRaw"]:
            self.save_web_raw(writer)
        elif self.signature == "UnityFS":
            if not packer or packer == "none":
                self.save_fs(writer, 64, 64)
            elif packer == "original":
                self.save_fs(
                    writer,
                    data_flag=self.dataflags,
                    block_info_flag=self._block_info_flags,
                )
            elif packer == "lz4":
                self.save_fs(writer, data_flag=194, block_info_flag=2)
            elif packer == "lzma":
                self.save_fs(writer, data_flag=65, block_info_flag=1)
            elif isinstance(packer, tuple):
                self.save_fs(writer, *packer)
            else:
                raise NotImplementedError("UnityFS - Packer:", packer)
        return writer.bytes

    def save_fs(self, writer: EndianBinaryWriter, data_flag: int, block_info_flag: int):
        # header
        # compressed blockinfo (block details & directionary)
        # compressed assets

        # 0b1000000 / 0b11000000 | 64 / 192 - uncompressed
        # 0b11000010 | 194 - lz4
        # block_info_flag

        # 0 / 0b1000000 | 0 / 64 - uncompressed
        # 0b1   | 1 - lzma
        # 0b10  | 2 - lz4
        # 0b11  | 3 - lz4hc [not implemented]
        # 0b100 | 4 - lzham [not implemented]
        # data_flag

        # header:
        #     bundle_size        (long)
        #     compressed_size    (int)
        #     uncompressed_size    (int)
        #     flag                (int)
        #     ?padding?            (bool)
        #   This will be written at the end,
        #   because the size can only be calculated after the data compression,

        # block_info:
        #     *flag & 0x80 ? at the end : right after header
        #     *decompression via flag & 0x3F
        #     *read compressed_size -> uncompressed_size
        #     0x10 offset
        #     *read blocks infos of the data stream
        #     count            (int)
        #     (
        #         uncompressed_size(uint)
        #         compressed_size (uint)
        #         flag(short)
        #     )
        #     *decompression via info.flag & 0x3F

        #     *afterwards the file positions
        #     file_count        (int)
        #     (
        #         offset    (long)
        #         size        (long)
        #         flag        (int)
        #         name        (string_to_null)
        #     )

        # file list & file data
        # prep nodes and build up block data
        data_writer = EndianBinaryWriter()
        files = [
            (
                name,
                f.flags,
                data_writer.write_bytes(
                    f.bytes
                    if isinstance(f, (EndianBinaryReader, EndianBinaryWriter))
                    else f.save()
                ),
            )
            for name, f in self.files.items()
        ]

        file_data = data_writer.bytes
        data_writer.dispose()

        file_data, block_info = CompressionHelper.chunk_based_compress(
            file_data, block_info_flag
        )

        # write the block_info
        # uncompressedDataHash
        block_writer = EndianBinaryWriter(b"\x00" * 0x10)
        # data block info
        block_writer.write_int(len(block_info))
        for block_uncompressed_size, block_compressed_size, block_flag in block_info:
            # uncompressed size
            block_writer.write_u_int(block_uncompressed_size)
            # compressed size
            block_writer.write_u_int(block_compressed_size)
            # flag
            block_writer.write_u_short(block_flag)

        # file block info
        if not data_flag & 0x40:
            raise NotImplementedError(
                "UnityPy always writes DirectoryInfo, so data_flag must include 0x40"
            )
        # file count
        block_writer.write_int(len(files))
        offset = 0
        for f_name, f_flag, f_len in files:
            # offset
            block_writer.write_long(offset)
            # size
            block_writer.write_long(f_len)
            offset += f_len
            # flag
            block_writer.write_u_int(f_flag)
            # name
            block_writer.write_string_to_null(f_name)

        # compress the block data
        block_data = block_writer.bytes
        block_writer.dispose()

        uncompressed_block_data_size = len(block_data)

        switch = data_flag & 0x3F
        if switch == 1:  # LZMA
            block_data = CompressionHelper.compress_lzma(block_data)
        elif switch in [2, 3]:  # LZ4, LZ4HC
            block_data = CompressionHelper.compress_lz4(block_data)
        elif switch == 4:  # LZHAM
            raise NotImplementedError

        compressed_block_data_size = len(block_data)

        # write the header info
        ## file size - 0 for now, will be set at the end
        writer_header_pos = writer.Position
        writer.write_long(0)
        # compressed blockInfoBytes size
        writer.write_u_int(compressed_block_data_size)
        # uncompressed size
        writer.write_u_int(uncompressed_block_data_size)
        # compression and file layout flag
        writer.write_u_int(data_flag)

        if self._uses_block_alignment:
            # UnityFS\x00 - 8
            # size 8
            # comp sizes 4+4
            # flag 4
            # sum : 28 -> +8 alignment
            writer.align_stream(16)

        if data_flag & 0x80:  # at end of file
            if data_flag & 0x200:
                writer.align_stream(16)
            writer.write(file_data)
            writer.write(block_data)
        else:
            writer.write(block_data)
            if data_flag & 0x200:
                writer.align_stream(16)
            writer.write(file_data)

        writer_end_pos = writer.Position
        writer.Position = writer_header_pos
        # correct file size
        writer.write_long(writer_end_pos)
        writer.Position = writer_end_pos


    def save_web_raw(self, writer: EndianBinaryWriter):
        # (version >= 4) hash
        # (version >= 4) crc
        # minimumStreamedBytes
        # headerSize
        # numberOfLevelsToDownloadBeforeStreaming
        # levelCount
        # compressedSize * levelCount
        # uncompressedSize * levelCount
        # (version >= 2) completeFileSize
        # (version >= 3) file_info_header_size
        # compressed assets

        if self.version > 3:
            raise NotImplementedError("Saving Unity Web bundles with version > 3 is not supported")

        # Calculate fileInfoHeaderSize for set offsets
        file_info_header_size = 4  # for nodesCount

        for file_name in self.files.keys():
            file_info_header_size += len(file_name.encode()) + 1  # +1 for null terminator
            file_info_header_size += 4 * 2  # 4 bytes each for offset and size

        file_info_header_padding_size = 4 - (file_info_header_size % 4) if file_info_header_size % 4 != 0 else 0
        file_info_header_size += file_info_header_padding_size

        # Prepare directory info
        directory_info_writer = EndianBinaryWriter()
        directory_info_writer.write_int(len(self.files))  # nodesCount

        file_content_writer = EndianBinaryWriter()
        current_offset = file_info_header_size

        for file_name, f in self.files.items():
            directory_info_writer.write_string_to_null(file_name)
            directory_info_writer.write_u_int(current_offset)

            # Get file content
            if isinstance(f, (EndianBinaryReader, EndianBinaryWriter)):
                file_data = f.bytes
            else:
                file_data = f.save()

            file_size = len(file_data)
            directory_info_writer.write_u_int(file_size)

            file_content_writer.write_bytes(file_data)
            current_offset += file_size

        directory_info_writer.write(b'\x00' * file_info_header_padding_size)
        uncompressed_directory_info = directory_info_writer.bytes
        uncompressed_file_content = file_content_writer.bytes

        # Combine directory info and file content
        uncompressed_content = uncompressed_directory_info + uncompressed_file_content
        compressed_content = uncompressed_content
        if self.signature == "UnityWeb":
            compressed_content = CompressionHelper.compress_lzma(uncompressed_content, True)

        # Write header
        header_size = writer.Position + 24 # assuming levelCount = 1
        if self.version >= 2:
            header_size += 4
        if self.version >= 3:
            header_size += 4
        if self.version >= 4:
            header_size += 20
        # pad to multiple of 4
        header_size = (header_size + 3) & ~3

        if self.version >= 4:
            writer.write_bytes(self._hash)
            writer.write_u_int(self.crc)

        writer.write_u_int(header_size + len(compressed_content))  # minimumStreamedBytes (same as completeFileSize)
        writer.write_u_int(header_size)  # headerSize
        writer.write_u_int(1)  # numberOfLevelsToDownloadBeforeStreaming (always 1)
        writer.write_int(1)  # levelCount (always 1)

        writer.write_u_int(len(compressed_content))  # compressedSize
        writer.write_u_int(len(uncompressed_content))  # uncompressedSize

        if self.version >= 2:
            writer.write_u_int(header_size + len(compressed_content))  # completeFileSize

        if self.version >= 3:
            writer.write_u_int(file_info_header_size)  # file_info_header_size

        # align header
        writer.align_stream(4)

        # Write compressed content
        writer.write(compressed_content)


    def decompress_data(
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

    def get_version_tuple(self) -> Tuple[int, int, int]:
        """Returns the version as a tuple."""
        version = self.version_engine
        if not version or version == "0.0.0":
            version = config.get_fallback_version()
        return tuple(map(int, reVersion.match(version).groups()))
