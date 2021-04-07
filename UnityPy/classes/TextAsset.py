from .NamedObject import NamedObject
from ..streams import EndianBinaryWriter


class TextAsset(NamedObject):
    def __init__(self, reader):
        super().__init__(reader=reader)
        self.m_Script = reader.read_bytes(reader.read_int())

    @property
    def script(self):
        # required for backward compatibility
        return self.m_Script

    @script.setter
    def script(self, value):
        self.m_Script = value

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
        writer.write_int(len(self.m_Script))
        writer.write_bytes(self.m_Script)
        writer.align_stream()

        self.set_raw_data(writer.bytes)
