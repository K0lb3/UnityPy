from .NamedObject import NamedObject
from .PPtr import PPtr


class Material(NamedObject):
    def __init__(self, reader):
        super().__init__(reader=reader)
        version = self.version
        self.m_Shader = PPtr(reader)  # Shader

        if version >= (2021, 3):  # 2021.3 and up
            self.m_ValidKeywords = reader.read_string_array()
            self.m_InvalidKeywords = reader.read_string_array()
        elif version >= (5,):  # 5.0 and up
            self.m_ShaderKeywords = reader.read_aligned_string()
        elif version >= (4, 1):  # 4.x
            self.m_ShaderKeywords = reader.read_string_array()

        if version >= (5,):
            self.m_LightmapFlags = reader.read_u_int()

        if version >= (5, 6):  # 5.6 and up
            self.m_EnableInstancingVariants = reader.read_boolean()
            # var m_DoubleSidedGI = a_Stream.read_boolean() //2017 and up
            reader.align_stream()

        if version >= (4, 3):  # 4.3 and up
            self.m_CustomRenderQueue = reader.read_int()

        if version >= (5, 1):  # 5.1 and up
            self.stringTagMap = {
                reader.read_aligned_string(): reader.read_aligned_string()
                for _ in range(reader.read_int())
            }

        if version >= (5, 6):  # 5.6 and up
            self.disabledShaderPasses = reader.read_string_array()

        self.m_SavedProperties = UnityPropertySheet(reader)


class UnityTexEnv:
    def __init__(self, reader):
        self.m_Texture = PPtr(reader)  # Texture
        self.m_Scale = reader.read_vector2()
        self.m_Offset = reader.read_vector2()


class UnityPropertySheet:
    def __init__(self, reader):
        self.m_TexEnvs = {
            reader.read_aligned_string(): UnityTexEnv(reader)
            for _ in range(reader.read_int())
        }

        if reader.version >= (2021,):  # 2021.1 and up
            self.m_Ints = {
                reader.read_aligned_string(): reader.read_int()
                for _ in range(reader.read_int())
            }

        self.m_Floats = {
            reader.read_aligned_string(): reader.read_float()
            for _ in range(reader.read_int())
        }

        self.m_Colors = {
            reader.read_aligned_string(): reader.read_color4()
            for _ in range(reader.read_int())
        }
