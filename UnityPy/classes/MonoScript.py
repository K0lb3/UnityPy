from .NamedObject import NamedObject


class MonoScript(NamedObject):
    def __init__(self, reader):
        super().__init__(reader=reader)
        version = self.version
        if version >= (3, 4):  # 3.4 and up
            self.execution_order = reader.read_int()
        if version < (5,):  # 5.0 down
            self.properties_hash = reader.read_u_int()
        else:
            self.properties_hash = reader.read_bytes(16)
        if version < (3,):  # 3.0 down
            self.path_name = reader.read_aligned_string()

        self.class_name = reader.read_aligned_string()
        if version >= (3,):  # 3.0 and up
            self.namespace = reader.read_aligned_string()
        self.assembly_name = reader.read_aligned_string()
        if version < (2018, 2):  # 2018.2 down
            self.is_editor_script = reader.read_boolean()
