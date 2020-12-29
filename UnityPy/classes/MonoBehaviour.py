from .Behaviour import Behaviour
from .PPtr import PPtr


class MonoBehaviour(Behaviour):
    def __init__(self, reader):
        super().__init__(reader=reader)
        self.script = PPtr(reader)
        self.name = reader.read_aligned_string()

        if self.assets_file._enable_type_tree:
            self.read_type_tree()
        self._raw_offset = reader.Position

    @property
    def raw_data(self) -> bytes:
        """
        Reads the undocumentated data following the default init.
        This is usefull for classes that are stored via MonoBehaviours.
        """
        reader = self.reader
        reader.Position = self._raw_offset
        return reader.read_bytes(reader.byte_size - (self._raw_offset - reader.byte_start))
