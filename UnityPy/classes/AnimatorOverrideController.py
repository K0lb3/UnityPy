from .PPtr import PPtr
from .RuntimeAnimatorController import RuntimeAnimatorController


class AnimationClipOverride:
    def __init__(self, reader):
        self.m_OriginalClip = PPtr(reader)
        self.m_OverrideClip = PPtr(reader)


class AnimatorOverrideController(RuntimeAnimatorController):
    def __init__(self, reader):
        super().__init__(reader=reader)
        self.m_Controller = PPtr(reader)
        num_overrides = reader.read_int()
        self.m_Clips = [AnimationClipOverride(
            reader) for _ in range(num_overrides)]
