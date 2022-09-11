from collections import defaultdict
from .Object import Object
from .PPtr import PPtr, save_ptr
from ..streams import EndianBinaryReader, EndianBinaryWriter


class ResourceManager(Object):
    def __init__(self, reader):
        super().__init__(reader)
        m_ContainerSize = reader.read_int()
        self.m_Container = {}
        self.listContainer = defaultdict(list)
        for _ in range(m_ContainerSize):
            key = reader.read_aligned_string()
            self.m_Container[key] = PPtr(reader)
            self.listContainer[key].append(PPtr(reader))

    def save(self, writer: EndianBinaryWriter = None, multipleObjectsPerContainer: bool = False):
        if not writer:
            writer = EndianBinaryWriter(endian=self.reader.endian)
        super().save(writer, intern_call=True)
        if multipleObjectsPerContainer:
            writer.write_int(sum([len(vals) for vals in self.listContainer.values()]))
            for key, vals in self.listContainer.items():
                for val in vals:
                    writer.write_aligned_string(key)
                    save_ptr(val, writer)
        else:
            writer.write_int(len(self.m_Container))
            for key, val in self.m_Container.items():
                writer.write_aligned_string(key)
                save_ptr(val, writer)
        return writer

