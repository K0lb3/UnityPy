from .Behaviour import Behaviour
from .PPtr import PPtr


class Animator(Behaviour):
    def __init__(self, reader):
        super().__init__(reader=reader)

        self.avatar = PPtr(reader)  # Avatar
        self.controller = PPtr(reader)  # RuntimeAnimatorController
        self.culling_mode = reader.read_int()
        version = self.version

        if version[:2] > (4, 4):
            self.update_mode = reader.read_int()

        self.m_ApplyRootMotion = reader.read_boolean()
        if version >= (4, 5):  # 4.5 and up - 5.0 down
            reader.align_stream()

        if version >= (5,):  # 5.0 and up
            self.linear_velocity_blending = reader.read_boolean()
            reader.align_stream()

        if version < (4, 5):  # 4.5 down
            self.animate_physics = reader.read_boolean()

        if version >= (4, 3):  # 4.3 and up
            self.has_transform_hierarchy = reader.read_boolean()

        if version >= (4, 5):  # 4.5 and up
            self.allow_constant_clip_sampling_optimization = reader.read_boolean()

        if (4,) < version[:1] < (2018,):  # 5.0 and up - 2018 down
            reader.align_stream()

        if version >= (2018,):  # 2018 and up
            self.m_KeepAnimatorControllerStateOnDisable = reader.read_boolean()
            reader.align_stream()
