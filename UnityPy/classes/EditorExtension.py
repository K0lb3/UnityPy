from .Object import Object
from .PPtr import PPtr, save_ptr
from ..enums import BuildTarget
from ..streams import EndianBinaryWriter, EndianBinaryReader


class EditorExtension(Object):
    def __init__(self, reader: EndianBinaryReader):
        super().__init__(reader=reader)
        if self.platform == BuildTarget.NoTarget:
            self.prefab_parent_object = PPtr(reader)
            self.prefab_internal = PPtr(reader)

    def save(self, writer: EndianBinaryWriter):
        super().save(writer, intern_call=True)
        if self.platform == BuildTarget.NoTarget:
            save_ptr(self.prefab_parent_object, writer, self.reader.version2)
            save_ptr(self.prefab_internal, writer, self.reader.version2)
