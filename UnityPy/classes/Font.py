from .NamedObject import NamedObject
from .PPtr import PPtr


class Font(NamedObject):
    def __init__(self, reader):
        super().__init__(reader=reader)
        version = self.version
        if version >= (5, 5):  # 5.5 and up:
            self.m_LineSpacing = reader.read_float()
            self.m_DefaultMaterial = PPtr(reader)
            self.m_FontSize = reader.read_float()
            self.m_Texture = PPtr(reader)
            self.m_AsciiStartOffset = reader.read_int()
            self.m_Tracking = reader.read_float()
            self.m_CharacterSpacing = reader.read_int()
            self.m_CharacterPadding = reader.read_int()
            self.m_ConvertCase = reader.read_int()
            CharacterRects_size = reader.read_int()
            for i in range(CharacterRects_size):
                reader.Position += 44  # CharacterInfo data 41
            KerningValues_size = reader.read_int()
            for i in range(KerningValues_size):
                reader.Position += 8
            self.m_PixelScale = reader.read_float()
            FontData_size = reader.read_int()
            if FontData_size > 0:
                self.m_FontData = reader.read_bytes(FontData_size)
        else:
            self.m_AsciiStartOffset = reader.read_int()

            if version[:1] <= (3,):
                self.m_FontCountX = reader.read_int()
                self.m_FontCountY = reader.read_int()

            self.m_Kerning = reader.read_float()
            self.m_LineSpacing = reader.read_float()

            if version[:1] <= (3,):
                PerCharacterKerning_size = reader.read_int()
                for i in range(PerCharacterKerning_size):
                    first = reader.read_int()
                    second = reader.read_float()
            else:
                self.m_CharacterSpacing = reader.read_int()
                self.m_CharacterPadding = reader.read_int()

            self.m_ConvertCase = reader.read_int()
            self.m_DefaultMaterial = PPtr(reader)

            CharacterRects_size = reader.read_int()
            for i in range(CharacterRects_size):
                index = reader.read_int()
                # Rectf uv
                uvx = reader.read_float()
                uvy = reader.read_float()
                uvwidth = reader.read_float()
                uvheight = reader.read_float()
                # Rectf vert
                vertx = reader.read_float()
                verty = reader.read_float()
                vertwidth = reader.read_float()
                vertheight = reader.read_float()
                width = reader.read_float()

                if version >= (4,):
                    flipped = reader.read_boolean()
                    reader.align_stream()

            self.m_Texture = PPtr(reader)

            KerningValues_size = reader.read_int()
            for i in range(KerningValues_size):
                pairfirst = reader.read_short()
                pairsecond = reader.read_short()
                second = reader.read_float()

            if version[:1] <= (3,):
                self.m_GridFont = reader.read_boolean()
                reader.align_stream()
            else:
                self.m_PixelScale = reader.read_float()
            FontData_size = reader.read_int()
            if FontData_size > 0:
                self.m_FontData = reader.read_bytes(FontData_size)
