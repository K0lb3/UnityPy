from .NamedObject import NamedObject
from ..helpers.ResourceReader import get_resource_data
from .PPtr import PPtr


class VideoClip(NamedObject):
    def __init__(self, reader):
        super().__init__(reader=reader)
        self.original_path = reader.read_aligned_string()
        self.proxy_width = reader.read_u_int()
        self.proxy_height = reader.read_u_int()
        self.width = reader.read_u_int()
        self.height = reader.read_u_int()
        if self.version >= (2017, 2):  # 2017.2 and up
            self.pixel_aspec_ratio_num = reader.read_u_int()
            self.pixel_aspec_ratio_den = reader.read_u_int()
        self.frame_rate = reader.read_double()
        self.frame_count = reader.read_u_long()
        self.format = reader.read_int()
        self.audio_channel_count = reader.read_u_short_array()
        reader.align_stream()
        self.audio_sample_rate = reader.read_u_int_array()
        self.audio_language = reader.read_string_array()
        # StreamedResource m_ExternalResources
        if self.version >= (2020,):  # 2020.1 and up
            video_shader_size = reader.ReadInt32()
            self.video_shaders = [PPtr(reader) for _ in range(video_shader_size)]

        # StreamedResource
        source = reader.read_aligned_string()
        offset = reader.read_u_long()
        size = reader.read_u_long()

        self.has_split_alpha = reader.read_boolean()

        if self.version >= (2020,):  # 2020.1 and up
            self.m_sRGB = reader.read_boolean()

        if source:
            self.VideoData = get_resource_data(source, self.assets_file, offset, size)
        else:
            self.VideoData = reader.read(size)
