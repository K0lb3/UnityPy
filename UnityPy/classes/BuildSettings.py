from .Object import Object


class BuildSettings(Object):
    def __init__(self, reader):
        super().__init__(reader=reader)
        self.levels = reader.read_string_array()
        self.has_render_texture = reader.read_boolean()
        self.has_pro_version = reader.read_boolean()
        self.has_publishing_rights = reader.read_boolean()
        self.has_shadows = reader.read_boolean()
        self.version = reader.read_aligned_string()
