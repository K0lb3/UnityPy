from .EditorExtension import EditorExtension
from .PPtr import PPtr, save_ptr
from ..streams import EndianBinaryReader, EndianBinaryWriter


class Component(EditorExtension):
    def __init__(self, reader: EndianBinaryReader):
        super().__init__(reader=reader)
        self.m_GameObject = PPtr(reader)  # GameObject

    def save(self, writer: EndianBinaryWriter = None):
        if writer is None:
            writer = EndianBinaryWriter(endian=self.reader.endian)
        version = self.version
        super().save(writer)
        save_ptr(self.m_GameObject, writer)
