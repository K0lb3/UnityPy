from . import File
from ..enums import FileType
from ..helpers import CompressionHelper, ImportHelper
from ..streams import EndianBinaryReader, EndianBinaryWriter

from collections import namedtuple
BlockInfo = namedtuple("BlockInfo", "uncompressedSize compressedSize flags")
DirectoryInfoFS = namedtuple("DirectoryInfoFS", "offset size flags path")


class BundleFile(File.File):
    format: int
    is_changed: bool
    signature: str
    version_engine: str
    version_player: str

    def __init__(self, reader: EndianBinaryReader, parent : File):
        super().__init__(parent = parent)
        signature = self.signature = reader.read_string_to_null()

        if signature == "UnityArchive":
            raise NotImplemented("BundleFile - UnityArchive")
        elif signature in ["UnityWeb", "UnityRaw"]:
            m_DirectoryInfo, blocksReader = self.read_web_raw(reader)
        elif signature == "UnityFS":
            m_DirectoryInfo, blocksReader = self.read_fs(reader)

        self.read_files(blocksReader, m_DirectoryInfo)

    def read_web_raw(self, reader: EndianBinaryReader):
        # def read_header_and_blocks_info(self, reader:EndianBinaryReader):
        isCompressed = self.signature == "UnityWeb"
        version = self.version = reader.read_u_int()
        self.version_player = reader.read_string_to_null()
        self.version_engine = reader.read_string_to_null()
        if version >= 4:
            _hash = reader.read_bytes(16)
            crc = reader.read_u_int()

        minimumStreamedBytes = reader.read_u_int()
        headerSize = reader.read_u_int()
        numberOfLevelsToDownloadBeforeStreaming = reader.read_u_int()
        levelCount = reader.read_int()
        reader.Position += 4 * 2 * (levelCount - 1)

        compressedSize = reader.read_u_int()
        uncompressedSize = reader.read_u_int()
        flags = True

        if version >= 2:
            completeFileSize = reader.read_u_int()

        if version >= 3:
            fileInfoHeaderSize = reader.read_u_int()

        reader.Position = headerSize

        uncompressedBytes = reader.read_bytes(compressedSize)
        if flags:
            uncompressedBytes = CompressionHelper.decompress_lzma(uncompressedBytes)

        blocksReader = EndianBinaryReader(uncompressedBytes, offset=headerSize)
        nodesCount = blocksReader.read_int()
        m_DirectoryInfo = [
            File.DirectoryInfo(
                blocksReader.read_string_to_null(),  # path
                blocksReader.read_u_int(),  # offset
                blocksReader.read_u_int(),  # size
            )
            for i in range(nodesCount)
        ]

        return m_DirectoryInfo, blocksReader

    def read_fs(self, reader: EndianBinaryReader):
        self.version = reader.read_u_int()
        self.version_player = reader.read_string_to_null()
        self.version_engine = reader.read_string_to_null()
        size = reader.read_long()

        # header
        compressedSize = reader.read_u_int()
        uncompressedSize = reader.read_u_int()
        flags = reader.read_u_int()

        _position = reader.Position
        if flags & 0x80 != 0:  # kArchiveBlocksInfoAtTheEnd
            reader.Position = reader.Length - compressedSize
            blocksInfoBytes = reader.read_bytes(compressedSize)
            reader.Position = _position
        else:  # 0x40 kArchiveBlocksAndDirectoryInfoCombined
            if self.version >= 7:
                reader.allign_stream(16)
            blocksInfoBytes = reader.read_bytes(compressedSize)

        switch = flags & 0x3F

        if switch == 1:  # LZMA
            blocksInfoBytes = CompressionHelper.decompress_lzma(blocksInfoBytes)
        elif switch in [2, 3]:  # LZ4, LZ4HC
            blocksInfoBytes = CompressionHelper.decompress_lz4(
                blocksInfoBytes, uncompressedSize
            )
        # elif switch == 4: #LZHAM:

        blocksInfoReader = EndianBinaryReader(blocksInfoBytes, offset=_position)

        uncompressedDataHash = blocksInfoReader.read_bytes(16)
        blocksInfoCount = blocksInfoReader.read_int()

        m_BlocksInfo = [
            BlockInfo(
                blocksInfoReader.read_u_int(),  # uncompressedSize
                blocksInfoReader.read_u_int(),  # compressedSize
                blocksInfoReader.read_u_short(),  # flags
            )
            for i in range(blocksInfoCount)
        ]

        nodesCount = blocksInfoReader.read_int()
        m_DirectoryInfo = [
            DirectoryInfoFS(
                blocksInfoReader.read_long(),  # offset
                blocksInfoReader.read_long(),  # size
                blocksInfoReader.read_u_int(),  # flags
                blocksInfoReader.read_string_to_null(),  # path
            )
            for i in range(nodesCount)
        ]

        # def read_blocks(reader : EndianBinaryReader, blocksStream):
        def decompress_block(blockInfo):
            switch = blockInfo.flags & 0x3F  # kStorageBlockCompressionTypeMask
            if switch == 1:  # LZMA
                return CompressionHelper.decompress_lzma(
                    reader.read_bytes(blockInfo.compressedSize)
                )
            elif switch in [2, 3]:  # LZ4, LZ4HC
                return CompressionHelper.decompress_lz4(
                    reader.read_bytes(blockInfo.compressedSize),
                    blockInfo.uncompressedSize,
                )
            # elif switch == 4: #LZHAM:
            else:  # no compression
                return reader.read_bytes(blockInfo.uncompressedSize)

        blocksReader = EndianBinaryReader(
            b"".join(decompress_block(blockInfo) for blockInfo in m_BlocksInfo),
            offset=(blocksInfoReader.real_offset())
        )

        return m_DirectoryInfo, blocksReader

    def save(self, packer="none"):
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
            raise NotImplemented("BundleFile - UnityArchive")
        elif self.signature in ["UnityWeb", "UnityRaw"]:
            raise NotImplemented("Saving Unity Web and Raw bundles isn't supported yet")
            # self.save_web_raw(writer)
        elif self.signature == "UnityFS":
            if not packer or packer == "none":
                self.save_fs(writer)
            elif packer == "lz4":
                self.save_fs(writer, block_info_flag=194, data_flag=2)
            else:
                raise NotImplemented("UnityFS - Packer:", packer)
        return writer.bytes

    def save_fs(self, writer: EndianBinaryWriter, padding=False, block_info_flag=64, data_flag=64):
        # header
        # compressed blockinfo (block details & directionary)
        # compressed assets

        # 0b1000000 / 0b11000000 | 64 / 192 - uncompressed
        # 0b11000010 | 194 - lz4
        #block_info_flag

        # 0 / 0b1000000 | 0 / 64 - uncompressed
        # 0b1   | 1 - lzma
        # 0b10  | 2 - lz4
        # 0b11  | 3 - lz4hc [not implemented]
        # 0b100 | 4 - lzham [not implemented]
        #data_flag

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
        data_writer = EndianBinaryWriter()
        files = [
            (
                name,
                f.flags,
                data_writer.write_bytes(
                    f.bytes if isinstance(f, EndianBinaryReader) else f.save()
                ),
            )
            for name, f in self.files.items()
        ]

        file_data = data_writer.bytes
        data_writer.dispose()
        uncompressed_data_size = len(file_data)

        # compress the data
        switch = data_flag & 0x3F
        if switch == 1:  # LZMA
            file_data = CompressionHelper.compress_lzma(file_data)
        elif switch in [2, 3]:  # LZ4, LZ4HC
            file_data = CompressionHelper.compress_lz4(file_data)
        elif switch == 4:  # LZHAM
            raise NotImplementedError
        # else no compression - data stays the same
        compressed_data_size = len(file_data)

        # write the block_info
        block_writer = EndianBinaryWriter(b"\x00" * 0x10)
        # data block info
        # block count
        block_writer.write_int(1)
        # uncompressed size
        block_writer.write_u_int(uncompressed_data_size)
        # compressed size
        block_writer.write_u_int(compressed_data_size)
        # flag
        block_writer.write_short(data_flag)

        # file block info
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
            block_writer.write_int(f_flag)
            # name
            block_writer.write_string_to_null(f_name)

        # compress the block data
        block_data = block_writer.bytes
        block_writer.dispose()

        uncompressed_block_data_size = len(block_data)

        switch = block_info_flag & 0x3F
        if switch == 1:  # LZMA
            block_data = CompressionHelper.compress_lzma(block_data)
        elif switch in [2, 3]:  # LZ4, LZ4HC
            block_data = CompressionHelper.compress_lz4(block_data)
        elif switch == 4:  # LZHAM
            raise NotImplementedError

        compressed_block_data_size = len(block_data)

        # write the header info
        writer.write_long(
            writer.Length
            + 8
            + 4
            + 4
            + 4
            + (1 if padding else 0)
            + compressed_block_data_size
            + compressed_data_size
        )
        writer.write_int(compressed_block_data_size)
        writer.write_int(uncompressed_block_data_size)
        writer.write_int(block_info_flag)
        if padding:
            writer.write_boolean(padding)

        if (block_info_flag & 0x80) != 0:  # at end of file
            writer.write(file_data)
            writer.write(block_data)
        else:
            writer.write(block_data)
            writer.write(file_data)
