from .NamedObject import NamedObject
from .PPtr import PPtr


class Font(NamedObject):
    def __init__(self, reader):
        super().__init__(reader=reader)
        version = self.version
        if version >= (5, 5):  # 5.5 and up:
            self.LineSpacing = reader.read_float()
            self.DefaultMaterial = PPtr(reader)
            self.FontSize = reader.read_float()
            self.Texture = PPtr(reader)
            self.AsciiStartOffset = reader.read_int()
            self.Tracking = reader.read_float()
            self.CharacterSpacing = reader.read_int()
            self.CharacterPadding = reader.read_int()
            self.ConvertCase = reader.read_int()
            CharacterRects_size = reader.read_int()
            for i in range(CharacterRects_size):
                reader.Position += 44  # CharacterInfo data 41
            KerningValues_size = reader.read_int()
            for i in range(KerningValues_size):
                reader.Position += 8
            self.PixelScale = reader.read_float()
            FontData_size = reader.read_int()
            if FontData_size > 0:
                self.FontData = reader.read_bytes(FontData_size)
        else:
            self.AsciiStartOffset = reader.read_int()

            if version[:1] <= (3,):
                self.FontCountX = reader.read_int()
                self.FontCountY = reader.read_int()

            self.Kerning = reader.read_float()
            self.LineSpacing = reader.read_float()

            if version[:1] <= (3,):
                PerCharacterKerning_size = reader.read_int()
                for i in range(PerCharacterKerning_size):
                    first = reader.read_int()
                    second = reader.read_float()
            else:
                self.CharacterSpacing = reader.read_int()
                self.CharacterPadding = reader.read_int()

            self.ConvertCase = reader.read_int()
            self.DefaultMaterial = PPtr(reader)

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

            self.Texture = PPtr(reader)

            KerningValues_size = reader.read_int()
            for i in range(KerningValues_size):
                pairfirst = reader.read_short()
                pairsecond = reader.read_short()
                second = reader.read_float()

            if version[:1] <= (3,):
                self.GridFont = reader.read_boolean()
                reader.align_stream()
            else:
                self.PixelScale = reader.read_float()
            FontData_size = reader.read_int()
            if FontData_size > 0:
                self.FontData = reader.read_bytes(FontData_size)
