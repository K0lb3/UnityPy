from .PPtr import PPtr
from .RuntimeAnimatorController import RuntimeAnimatorController


class AnimationClipOverride:
    def __init__(self, reader):
        self.original_clip = PPtr(reader)
        self.override_clip = PPtr(reader)


class AnimatorOverrideController(RuntimeAnimatorController):
    def __init__(self, reader):
        super().__init__(reader=reader)
        self.controller = PPtr(reader)
        num_overrides = reader.read_int()
        self.clips = [AnimationClipOverride(reader) for i in range(num_overrides)]
