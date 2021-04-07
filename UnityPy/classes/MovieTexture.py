from .PPtr import PPtr
from .Texture import Texture


class MovieTexture(Texture):
    def __init__(self, reader):
        super().__init__(reader=reader)
        self.m_Loop = reader.read_boolean()
        reader.align_stream()
        self.m_AudioClip = PPtr(reader)  # AudioClip
        self.m_MovieData = reader.read_bytes(reader.read_int())
