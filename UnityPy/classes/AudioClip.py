from .NamedObject import NamedObject
from ..enums import AudioType, AudioCompressionFormat, AUDIO_TYPE_EXTEMSION
from ..export import AudioClipConverter
from ..helpers.ResourceReader import get_resource_data


class AudioClip(NamedObject):
    def __init__(self, reader):
        super().__init__(reader=reader)
        self.m_Source = ""
        version = self.version
        if version < (5,):  # 5.0 down
            self.m_Format = reader.read_int()
            self.m_Type = AudioType(reader.read_int())
            self.m_3D = reader.read_boolean()
            self.m_UseHardware = reader.read_boolean()
            reader.align_stream()

            if version >= (3, 2):  # and version <= (5,): # 3.2.0 to 5
                self.m_Stream = reader.read_int()
                self.m_Size = reader.read_int()
                tsize = self.m_Size + 4 - self.m_Size % 4 if (self.m_Size % 4 != 0) else self.m_Size
                if reader.byte_size + reader.byte_start - reader.Position != tsize:
                    m_Offset = reader.read_u_int()
                    self.m_Source = self.assets_file.full_name + ".resS"
            else:
                self.m_Size = reader.read_int()

            self.extension = AUDIO_TYPE_EXTEMSION.get(self.m_Type, ".audioclip")
        else:
            self.m_LoadType = reader.read_int()
            self.m_Channels = reader.read_int()
            self.m_Frequency = reader.read_int()
            self.m_BitsPerSample = reader.read_int()
            self.m_Length = reader.read_float()
            self.m_IsTrackerFormat = reader.read_boolean()
            reader.align_stream()
            self.m_SubsoundIndex = reader.read_int()
            self.m_PreloadAudioData = reader.read_boolean()
            self.m_LoadInBackground = reader.read_boolean()
            self.m_Legacy3D = reader.read_boolean()
            reader.align_stream()
            self.m_Source = reader.read_aligned_string()
            self.m_Offset = reader.read_u_long()
            self.m_Size = reader.read_long()
            self.m_CompressionFormat = AudioCompressionFormat(reader.read_int())

            self.extension = AUDIO_TYPE_EXTEMSION.get(
                self.m_CompressionFormat, ".audioclip"
            )

        if self.m_Source:
            self.m_AudioData = get_resource_data(
                self.m_Source, self.assets_file, self.m_Offset, self.m_Size
            )
        else:
            self.m_AudioData = reader.read_bytes(self.m_Size)

    @property
    def samples(self) -> dict:
        return AudioClipConverter.extract_audioclip_samples(self)
