from .EditorExtension import EditorExtension
from ..streams import EndianBinaryWriter


class NamedObject(EditorExtension):
    m_Name: str

    def __init__(self, reader):
        super().__init__(reader=reader)
        self.reader.reset()
        self.m_Name = self.reader.read_aligned_string()

    def save(self, writer: EndianBinaryWriter = None):
        if not writer:
            writer = EndianBinaryWriter(endian=self.reader.endian)
        super().save(writer)
        writer.write_aligned_string(self.m_Name)

    @property
    def name(self):
        return self.m_Name

    @name.setter
    def name(self, value):
        self.m_Name = value

    def __repr__(self):
        return f"<{self.__class__.__name__} path_id={self.path_id} name={self.m_Name}>"
