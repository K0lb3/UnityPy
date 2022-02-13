from .EditorExtension import EditorExtension
from .PPtr import PPtr
from ..streams import EndianBinaryReader, EndianBinaryWriter

class GameObject(EditorExtension):
    def __init__(self, reader):
        super().__init__(reader=reader)
        component_size = reader.read_int()
        self.m_Components = [None]*component_size
        for i in range(component_size):
            if self.version < (5, 5):
                first = reader.read_int()
            self.m_Components[i] = PPtr(reader)
        self.m_Layer = reader.read_int()
        self.name = reader.read_aligned_string()
        # self.reader.read_the_rest(self.byte_size-1,1
        self.m_IsActive = False
        data = self.reader.get_raw_data()
        if data[-1] == 0x1:
            self.m_IsActive = True
    def save(self, writer:EndianBinaryWriter=None):
        super().save(writer)
        data = bytearray(self.reader.get_raw_data())
        if self.m_IsActive is True:
            data[-1] = 0x1
        else:
            data[-1] = 0x0
        self.set_raw_data(data)
