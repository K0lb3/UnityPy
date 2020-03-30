from .PPtr import PPtr
from .Texture import Texture


class MovieTexture(Texture):
    def __init__(self, reader):
        super().__init__(reader=reader)
        self.Loop = reader.read_boolean()
        reader.align_stream()
        self.AudioClip = PPtr(reader)  # AudioClip
        self.m_MovieData = reader.read_bytes(reader.read_int())
