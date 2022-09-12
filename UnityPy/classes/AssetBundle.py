from collections import defaultdict
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
        self.m_PreloadTable = [PPtr(reader) for _ in range(preload_table_size)]
        container_size = reader.read_int()
        self.m_Container = {}
        self.list_container = defaultdict(list)
        # TODO - m_Container is a multi-dict, multiple values can have the same key
        # list_container is a dict of list that workaround the issue temporarily before version 2
        for i in range(container_size):
            key = reader.read_aligned_string()
            info = AssetInfo(reader)
            self.m_Container[key] = info
            self.list_container[key].append(info)
