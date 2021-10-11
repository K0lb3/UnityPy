from .Behaviour import Behaviour
from .PPtr import PPtr, save_ptr
from ..streams import EndianBinaryReader, EndianBinaryWriter
from ..exceptions import TypeTreeError as TypeTreeError

class MonoBehaviour(Behaviour):
    def __init__(self, reader: EndianBinaryReader):
        super().__init__(reader=reader)
        self.m_Script = PPtr(reader)
        self.name = reader.read_aligned_string()

        self._raw_offset = reader.Position
        if self.assets_file._enable_type_tree:
            try:
                self.read_typetree()
            except TypeTreeError as e:
                print("Failed to read TypeTree:\n", e.message)
                self.assets_file._enable_type_tree = False

    def save(self, writer: EndianBinaryWriter = None, raw_data: bytes = None):
        if writer is None:
            writer = EndianBinaryWriter(endian=self.reader.endian)
        if not raw_data:
            ValueError("No raw data given")
        
        super().save(writer)
        save_ptr(self.m_Script, writer)
        writer.write_aligned_string(self.name)
        writer.write(raw_data)
        
        self.set_raw_data(writer.bytes)

    @property
    def raw_data(self) -> bytes:
        """
        Reads the undocumentated data following the default init.
        This is usefull for classes that are stored via MonoBehaviours.
        """
        reader = self.reader
        reader.Position = self._raw_offset
        return reader.read_bytes(reader.byte_size - (self._raw_offset - reader.byte_start))

