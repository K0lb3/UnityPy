from .File import File
from .SerializedFile import SerializedFile
from ..enums import FileType
from ..helpers import CompressionHelper, ImportHelper
from ..streams import EndianBinaryReader, EndianBinaryWriter


class BundleFile(File):
    format: int
    version_player: str
    version_engine: str

    def __init__(self, reader: EndianBinaryReader, environment=None):
        self.files = {}
        self.signature = reader.read_string_to_null()
        self.format = reader.read_int()
        self.version_player = reader.read_string_to_null()
        self.version_engine = reader.read_string_to_null()

        if self.format == 6:
            self.read_format_6(reader, self.signature != "UnityFS")

        elif self.signature in [
            "UnityWeb",
            "UnityRaw",
            "\xFA\xFA\xFA\xFA\xFA\xFA\xFA\xFA",
        ]:
            if self.format < 6:
                bundle_size = reader.read_int()

            dummy2 = reader.read_short()
            offset = reader.read_short()

            if self.signature in ["UnityWeb", "\xFA\xFA\xFA\xFA\xFA\xFA\xFA\xFA"]:
                dummy3 = reader.read_int()
                lzma_chunks = reader.read_int()
                reader.Position = reader.Position + (lzma_chunks - 1) * 8
                lzma_size = reader.read_int()
                stream_size = reader.read_int()

                reader.Position = offset
                lzma_buffer = reader.read_bytes(lzma_size)
                data_reader = EndianBinaryReader(
                    CompressionHelper.decompress_lzma(lzma_buffer)
                )
                self.get_assets_files(data_reader, 0)

            elif self.signature == "UnityRaw":
                reader.Position = offset
                self.get_assets_files(reader, offset)

        else:
            raise ValueError(
                f"unknown combination of format ({self.format}) & signature ({self.signature})"
            )

        for name, item in self.files.items():
            # check for serialized files
            if name.endswith((".resS", ".resource", ".config", ".xml", ".dat")):
                environment.resources[name] = item
            else:
                typ, _ = ImportHelper.check_file_type(item)
                if typ == FileType.AssetsFile:
                    item.Position = 0
                    sf = SerializedFile(item, environment, self)
                    sf.flag = item.flag
                    self.files[name] = sf
                    environment.assets[name] = sf
                else:
                    environment.resources[name] = item

    def get_assets_files(self, reader: EndianBinaryReader, offset):
        file_count = reader.read_int()
        files = [
            # name, offset, size
            (reader.read_string_to_null(), reader.read_int(), reader.read_int())
            for _ in range(file_count)
        ]
        for name, f_offset, size in files:
            reader.Position = offset + f_offset
            self.files[name] = EndianBinaryReader(reader.read(size))

    def read_format_6(self, reader: EndianBinaryReader, padding):
        bundle_size = reader.read_long()
        compressed_size = reader.read_int()
        uncompressed_size = reader.read_int()
        flag = reader.read_int()

        if padding:
            reader.read_byte()

        if (flag & 0x80) != 0:  # at end of file
            position = reader.Position
            reader.Position = reader.Length - compressed_size
            block_info_bytes = reader.read_bytes(compressed_size)
            reader.Position = position
        else:
            block_info_bytes = reader.read_bytes(compressed_size)

        switch = flag & 0x3F
        if switch == 1:  # LZMA
            blocks_info_data = CompressionHelper.decompress_lzma(block_info_bytes)
        elif switch in [2, 3]:  # LZ4, LZ4HC
            blocks_info_data = CompressionHelper.decompress_lz4(
                block_info_bytes, uncompressed_size
            )
        # elif switch == 4: #LZHAM:
        else:  # no compression
            blocks_info_data = block_info_bytes

        blocks_info_reader = EndianBinaryReader(blocks_info_data)
        blocks_info_reader.Position = 0x10
        block_count = blocks_info_reader.read_int()
        block_infos = [BlockInfo(blocks_info_reader) for _ in range(block_count)]

        data = []
        for block_info in block_infos:
            switch = block_info.flag & 0x3F

            if switch == 1:  # LZMA
                data.append(
                    CompressionHelper.decompress_lzma(
                        reader.read(block_info.compressed_size)
                    )
                )
            elif switch in [2, 3]:  # LZ4, LZ4HC
                data.append(
                    CompressionHelper.decompress_lz4(
                        reader.read(block_info.compressed_size),
                        block_info.uncompressed_size,
                    )
                )
            # elif switch == 4: #LZHAM:
            else:  # no compression
                data.append(reader.read(block_info.compressed_size))

        data_stream = EndianBinaryReader(b"".join(data))
        entry_info_count = blocks_info_reader.read_int()

        for _ in range(entry_info_count):
            offset = blocks_info_reader.read_long()
            size = blocks_info_reader.read_long()
            flag = blocks_info_reader.read_int()
            name = blocks_info_reader.read_string_to_null()
            data_stream.Position = offset

            item = EndianBinaryReader(data_stream.read(size))
            item.flag = flag
            self.files[name] = item

    def save(self):
        # file_header
        #     signature	(string_to_null)
        #     format		(int)
        #     version_player	(string_to_null)
        #     version_engine	(string_to_null)
        writer = EndianBinaryWriter()

        writer.write_string_to_null(self.signature)
        writer.write_int(self.format)
        writer.write_string_to_null(self.version_player)
        writer.write_string_to_null(self.version_engine)

        if self.format == 6:  # WORKS
            self.save_format_6(writer, self.signature != "UnityFS")
        else:  # WIP
            raise NotImplementedError("Not Implemented")

        return writer.bytes

    def save_format_6(self, writer: EndianBinaryWriter, padding=False):
        # 192 - uncompressed
        # 194 - lz4
        block_info_flag = 64
        # 0/64 - uncompressed
        # 1 - lzma
        # 2 - lz4
        # 3 - lz4hc - not implemented
        # 4 - lzham - not implemented
        data_flag = 64
        # header:
        #     bundle_size		(long)
        #     compressed_size	(int)
        #     uncompressed_size	(int)
        #     flag			    (int)
        #     ?padding?		    (bool)
        #   This will be written at the end,
        #   because the size can only be calculated after the data compression,

        # block_info:
        #     *flag & 0x80 ? at the end : right after header
        #     *decompression via flag & 0x3F
        #     *read compressed_size -> uncompressed_size
        #     0x10 offset
        #     *read blocks infos of the data stream
        #     count			(int)
        #     (
        #         uncompressed_size(uint)
        #         compressed_size (uint)
        #         flag(short)
        #     )
        #     *decompression via info.flag & 0x3F

        #     *afterwards the file positions
        #     file_count		(int)
        #     (
        #         offset	(long)
        #         size		(long)
        #         flag		(int)
        #         name		(string_to_null)
        #     )

        # file list & file data
        data_writer = EndianBinaryWriter()
        files = [
            (
                name,
                f.flag,
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


class BlockInfo:
    compressed_size: int
    uncompressed_size: int
    flag: int

    def __init__(self, reader: EndianBinaryReader):
        self.uncompressed_size = reader.read_u_int()
        self.compressed_size = reader.read_u_int()
        self.flag = reader.read_short()
