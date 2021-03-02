from .NamedObject import NamedObject
from ..helpers.ResourceReader import get_resource_data
from .PPtr import PPtr


class VideoClip(NamedObject):
    def __init__(self, reader):
        super().__init__(reader=reader)
        self.m_OriginalPath = reader.read_aligned_string()
        self.m_ProxyWidth = reader.read_u_int()
        self.m_ProxyHeight = reader.read_u_int()
        self.Width = reader.read_u_int()
        self.Height = reader.read_u_int()
        if self.version >= (2017, 2):  # 2017.2 and up
            self.m_PixelAspecRatioNum = reader.read_u_int()
            self.m_PixelAspecRatioDen = reader.read_u_int()
        self.m_FrameRate = reader.read_double()
        self.m_FrameCount = reader.read_u_long()
        self.m_Format = reader.read_int()
        self.m_AudioChannelCount = reader.read_u_short_array()
        reader.align_stream()
        self.m_AudioSampleRate = reader.read_u_int_array()
        self.m_AudioLanguage = reader.read_string_array()
        if self.version >= (2020,):  # 2020.1 and up
            m_VideoShadersSize = reader.read_int()
            self.m_VideoShaders = [
                PPtr(reader) for _ in range(m_VideoShadersSize)
            ]

        # m_ExternalResources = new StreamedResource(reader)
        self.source = reader.read_aligned_string()
        self.offset = reader.read_u_long()
        self.size = reader.read_u_long()

        self.m_HasSplitAlpha = reader.read_boolean()
        if self.version >= (2020,):  # 2020.1 and up
            self.m_sRGB = reader.read_boolean()

        if self.source:
            self.m_VideoData = get_resource_data(
                self.source, self.assets_file, self.offset, self.size)
        else:
            self.reader.Position = self.data_offset
            self.m_VideoData = self.reader.read_bytes(self.size)
