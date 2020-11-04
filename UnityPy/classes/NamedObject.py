from .EditorExtension import EditorExtension
from ..streams import EndianBinaryWriter


class NamedObject(EditorExtension):
    def __init__(self, reader):
        super().__init__(reader=reader)
        self.reader.reset()
        self.name = self.reader.read_aligned_string()

    def save(self, writer: EndianBinaryWriter):
        super().save(writer)
        writer.write_aligned_string(self.name) # self.name if self.name else '' ?
