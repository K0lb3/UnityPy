from .NamedObject import NamedObject
from .PPtr import PPtr
from .Sprite import SpriteSettings


class SpriteAtlas(NamedObject):
    def __init__(self, reader):
        super().__init__(reader=reader)
        packed_sprites_size = reader.read_int()
        self.PackSprites = [PPtr(reader) for _ in range(packed_sprites_size)]

        self.packed_sprite_names_to_index = reader.read_string_array()
        m_render_data_map_size = reader.read_int()
        self.render_data_map = {}
        for _ in range(m_render_data_map_size):
            first = reader.read_bytes(16)  # GUID
            second = reader.read_long()
            value = SpriteAtlasData(reader)
            self.render_data_map[(first, second)] = value


class SpriteAtlasData:
    def __init__(self, reader):
        self.version = reader.version
        self.texture = PPtr(reader)  # Texture2D
        self.alphaTexture = PPtr(reader)  # Texture2D
        self.textureRect = reader.read_rectangle_f()
        self.textureRectOffset = reader.read_vector2()
        if self.version >= (2017, 2):  # 2017.2 and up
            self.atlasRectOffset = reader.read_vector2()
        self.uvTransform = reader.read_vector4()
        self.downscaleMultiplier = reader.read_float()
        self.settingsRaw = SpriteSettings(reader)
