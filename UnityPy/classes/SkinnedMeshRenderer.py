from .PPtr import PPtr
from .Renderer import Renderer


class SkinnedMeshRenderer(Renderer):
    def __init__(self, reader):
        super().__init__(reader=reader)
        version = self.version
        self.m_Quality = reader.read_int()
        self.m_UpdateWhenOffscreen = reader.read_boolean()
        self.m_SkinNormals = reader.read_boolean()  # 3.1.0 and below
        reader.align_stream()

        if version < (2, 6):  # 2.6 down
            self.m_DisableAnimationWhenOffscreen = PPtr(reader)  # Animation

        self.m_Mesh = PPtr(reader)  # Mesh

        m_BonesSize = reader.read_int()
        self.m_Bones = [PPtr(reader) for _ in range(m_BonesSize)]

        if version >= (4, 3):  # 4.3 and up
            self.m_BlendShapeWeights = reader.read_float_array()
