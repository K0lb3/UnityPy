from .NamedObject import NamedObject
from .PPtr import PPtr
from .Sprite import SpriteSettings, SecondarySpriteTexture


class SpriteAtlas(NamedObject):
    def __init__(self, reader):
        super().__init__(reader=reader)
        packed_sprites_size = reader.read_int()
        self.m_PackedSprites = [PPtr(reader) for _ in range(packed_sprites_size)]

        self.m_PackedSpriteNamesToIndex = reader.read_string_array()
        m_render_data_map_size = reader.read_int()
        self.m_RenderDataMap = {}
        for _ in range(m_render_data_map_size):
            first = reader.read_bytes(16)  # GUID
            second = reader.read_long()
            value = SpriteAtlasData(reader)
            self.m_RenderDataMap[(first, second)] = value


class SpriteAtlasData:
    def __init__(self, reader):
        self.version = version = reader.version
        self.texture = PPtr(reader)  # Texture2D
        self.alphaTexture = PPtr(reader)  # Texture2D
        self.textureRect = reader.read_rectangle_f()
        self.textureRectOffset = reader.read_vector2()
        if version >= (2017, 2):  # 2017.2 and up
            self.atlasRectOffset = reader.read_vector2()
        self.uvTransform = reader.read_vector4()
        self.downscaleMultiplier = reader.read_float()
        self.settingsRaw = SpriteSettings(reader)

        if version >= (2020, 2):
            secondaryTexturesSize = reader.read_int()
            self.secondaryTextures = [
                SecondarySpriteTexture(reader) for _ in range(secondaryTexturesSize)
            ]
            reader.align_stream()
