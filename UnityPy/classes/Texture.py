from .NamedObject import NamedObject
from ..streams import EndianBinaryWriter


class Texture(NamedObject):
    def __init__(self, reader):
        super().__init__(reader=reader)
        if (2017, 3) <= self.version < (2023, 2, 0, 18):  # 2017.3 - 2023.2.0.18
            self.m_ForcedFallbackFormat = reader.read_int()
            self.m_DownscaleFallback = reader.read_boolean()
        if self.version >= (2020, 2):  # 2020.2 and up
            self.m_IsAlphaChannelOptional = reader.read_boolean()
        reader.align_stream()

    def save(self, writer: EndianBinaryWriter):
        super().save(writer)
        if (2017, 3) <= self.version < (2023, 2, 0, 18):  # 2017.3 - 2023.2.0.18
            writer.write_int(self.m_ForcedFallbackFormat)
            writer.write_boolean(self.m_DownscaleFallback)
        if self.version >= (2020, 2):  # 2020.2 and up
            writer.write_boolean(self.m_IsAlphaChannelOptional)
        writer.align_stream()
