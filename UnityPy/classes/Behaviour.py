from .Component import Component
from ..streams import EndianBinaryReader, EndianBinaryWriter

class Behaviour(Component):
    def __init__(self, reader : EndianBinaryReader):
        super().__init__(reader=reader)
        self.m_Enabled = reader.read_byte()
        reader.align_stream()
    
    def save(self, writer: EndianBinaryWriter = None):
        if writer is None:
            writer = EndianBinaryWriter(endian=self.reader.endian)
        version = self.version
        super().save(writer)
        writer.write_byte(self.m_Enabled)
        writer.align_stream()