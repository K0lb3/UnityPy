from collections import defaultdict
from .Object import Object
from .PPtr import PPtr, save_ptr
from ..streams import EndianBinaryReader, EndianBinaryWriter


class ResourceManager(Object):
    def __init__(self, reader):
        super().__init__(reader)
        m_ContainerSize = reader.read_int()
        self.m_Container = defaultdict(list)
        for _ in range(m_ContainerSize):
            self.m_Container[reader.read_aligned_string()].append(PPtr(reader))

    def save(self, writer: EndianBinaryWriter = None):
        if not writer:
            writer = EndianBinaryWriter(endian=self.reader.endian)
        super().save(writer, intern_call=True)
        writer.write_int(sum([len(vals) for vals in self.m_Container.values()]))
        for key, vals in self.m_Container.items():
            for val in vals:
                writer.write_aligned_string(key)
                save_ptr(val, writer)
        return writer
