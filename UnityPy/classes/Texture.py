from .NamedObject import NamedObject
from ..streams import EndianBinaryWriter


class Texture(NamedObject):
    def __init__(self, reader):
        super().__init__(reader=reader)
        if self.version >= (2017, 3):  # 2017.3 and up
            self.forced_fallback_format = reader.read_int()
            self.downscale_fallback = reader.read_boolean()
            reader.align_stream()

    def save(self, writer: EndianBinaryWriter):
        super().save(writer)
        if self.version >= (2017, 3):  # 2017.3 and up
            writer.write_int(self.forced_fallback_format)
            writer.write_boolean(self.downscale_fallback)
            writer.align_stream()
