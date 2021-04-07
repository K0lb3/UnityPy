from .Behaviour import Behaviour
from .PPtr import PPtr


class Animator(Behaviour):
    def __init__(self, reader):
        super().__init__(reader=reader)

        self.m_Avatar = PPtr(reader)  # Avatar
        self.m_Controller = PPtr(reader)  # RuntimeAnimatorController
        self.m_CullingMode = reader.read_int()
        version = self.version

        if version >= (4, 5):  # 4.5 and up
            self.m_UpdateMode = reader.read_int()

        self.m_ApplyRootMotion = reader.read_boolean()
        if (4, 5) < version[2:] <= (5, 0):  # 4.5 and up - 5.0 down
            reader.align_stream()

        if version >= (5,):  # 5.0 and up
            self.m_LinearVelocityBlending = reader.read_boolean()
            reader.align_stream()

        if version[2:] < (4, 5):  # 4.5 down
            self.m_AnimatePhysics = reader.read_boolean()

        if version >= (4, 3):  # 4.3 and up
            self.m_HasTransformHierarchy = reader.read_boolean()

        if version >= (4, 5):  # 4.5 and up
            self.m_AllowConstantClipSamplingOptimization = reader.read_boolean()

        if (4,) < version[:1] < (2018,):  # 5.0 and up - 2018 down
            reader.align_stream()

        if version >= (2018,):  # 2018 and up
            self.m_KeepAnimatorControllerStateOnDisable = reader.read_boolean()
            reader.align_stream()
