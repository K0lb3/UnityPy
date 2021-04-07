from .Object import Object
from .PPtr import PPtr, save_ptr
from ..enums import BuildTarget
from ..streams import EndianBinaryWriter


class EditorExtension(Object):
    def __init__(self, reader):
        super().__init__(reader=reader)
        if self.platform == BuildTarget.NoTarget:
            self.m_PrefabParentObject = PPtr(reader)
            self.m_PrefabInternal = PPtr(reader)

    def save(self, writer: EndianBinaryWriter = None):
        if not writer:
            writer = EndianBinaryWriter(endian = self.reader.endian)
        super().save(writer, intern_call=True)
        if self.platform == BuildTarget.NoTarget:
            save_ptr(self.m_PrefabParentObject, writer)
            save_ptr(self.m_PrefabInternal, writer)
