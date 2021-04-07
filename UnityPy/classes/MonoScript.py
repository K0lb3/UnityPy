from .NamedObject import NamedObject


class MonoScript(NamedObject):
    def __init__(self, reader):
        super().__init__(reader=reader)
        version = self.version
        if version >= (3, 4):  # 3.4 and up
            self.m_ExecutionOrder = reader.read_int()
        if version < (5,):  # 5.0 down
            self.m_PropertiesHash = reader.read_u_int()
        else:
            self.m_PropertiesHash = reader.read_bytes(16)
        if version < (3,):  # 3.0 down
            self.m_PathName = reader.read_aligned_string()

        self.m_ClassName = reader.read_aligned_string()
        if version >= (3,):  # 3.0 and up
            self.m_Namespace = reader.read_aligned_string()

        self.m_AssemblyName = reader.read_aligned_string()
        if version < (2018, 2):  # 2018.2 down
            self.m_IsEditorScript = reader.read_boolean()
