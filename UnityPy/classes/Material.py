from .NamedObject import NamedObject
from .PPtr import PPtr


class Material(NamedObject):
    def __init__(self, reader):
        super().__init__(reader=reader)
        version = self.version
        self.m_Shader = PPtr(reader)  # Shader

        if version >= (5,):  # 5.0 and up
            self.m_ShaderKeywords = reader.read_aligned_string()
            self.m_LightmapFlags = reader.read_u_int()

        elif version >= (4, 1):  # 4.x
            self.m_ShaderKeywords = reader.read_string_array()

        if version >= (5, 6):  # 5.6 and up
            self.m_EnableInstancingVariants = reader.read_boolean()
            # var m_DoubleSidedGI = a_Stream.read_boolean() //2017 and up
            reader.align_stream()

        if version >= (4, 3):  # 4.3 and up
            self.m_CustomRenderQueue = reader.read_int()

        if version >= (5, 1):  # 5.1 and up
            stringTagMapSize = reader.read_int()
            self.stringTagMap = {}
            for _ in range(stringTagMapSize):
                first = reader.read_aligned_string()
                second = reader.read_aligned_string()
                self.stringTagMap[first] = second

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
        m_TexEnvsSize = reader.read_int()
        self.m_TexEnvs = {}
        for i in range(m_TexEnvsSize):
            key = reader.read_aligned_string()
            self.m_TexEnvs[key] = UnityTexEnv(reader)

        m_FloatsSize = reader.read_int()
        self.m_Floats = {}
        for i in range(m_FloatsSize):
            key = reader.read_aligned_string()
            self.m_Floats[key] = reader.read_float()

        m_ColorsSize = reader.read_int()
        self.m_Colors = {}
        for i in range(m_ColorsSize):
            key = reader.read_aligned_string()
            self.m_Colors[key] = reader.read_color4()
