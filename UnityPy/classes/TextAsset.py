from .NamedObject import NamedObject
from ..streams import EndianBinaryWriter, EndianBinaryReader


class TextAsset(NamedObject):
    def __init__(self, reader: EndianBinaryReader):
        super().__init__(reader=reader)
        self.script = reader.read_bytes(reader.read_int())

    @property
    def text(self):
        return bytes(self.script).decode("utf8")

    @text.setter
    def text(self, val):
        self.script = val.encode("utf8")

    def save(self, writer: EndianBinaryWriter = None):
        if writer is None:
            writer = EndianBinaryWriter(endian=self.reader.endian)
        super().save(writer)
        writer.write_int(len(self.script))
        writer.write_bytes(self.script)
        writer.align_stream()

        self.set_raw_data(writer.bytes)
