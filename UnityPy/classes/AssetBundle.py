from .NamedObject import NamedObject
from .PPtr import PPtr


class AssetInfo:
    def __init__(self, reader):
        self.preload_index = reader.read_int()
        self.preload_size = reader.read_int()
        self.asset = PPtr(reader)


class AssetBundle(NamedObject):
    def __init__(self, reader):
        super().__init__(reader=reader)
        preload_table_size = reader.read_int()
        self.preload_table = [PPtr(reader) for _ in range(preload_table_size)]
        container_size = reader.read_int()
        self.container = {}
        for i in range(container_size):
            key = reader.read_aligned_string()
            self.container[key] = AssetInfo(reader)
