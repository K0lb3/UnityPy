from enum import IntEnum

from .NamedObject import NamedObject
from ..ResourceReader import ResourceReader


class AudioClip(NamedObject):
	def __init__(self, reader):
		super().__init__(reader=reader)
		version = self.version
		if version[0] < 5:  #
			self.m_Format = reader.read_int()
			self.m_Type = AudioType(reader.read_int())
			self.m_3D = reader.read_boolean()
			self.m_UseHardware = reader.read_boolean()
			reader.align_stream()

			if version[0] >= 4 or (version[0] == 3 and version[1] >= 2):  # 3.2.0 to 5
				self.m_Stream = reader.read_int()
				m_Size = reader.read_int()
				tsize = m_Size + 4 - m_Size % 4 if (m_Size % 4 != 0) else m_Size
				if reader.byteSize + reader.byteStart - reader.Position != tsize:
					m_Offset = reader.read_int()
					self.m_Source = self.assets_file.full_name + ".resS"
			else:
				m_Size = reader.read_int()

			self.extension = AUDIO_TYPE_EXTEMSION.get(self.m_Type, '.audioclip')
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
			m_Offset = reader.read_long()
			m_Size = reader.read_long()
			self.m_CompressionFormat = AudioCompressionFormat(reader.read_int())

			self.extension = AUDIO_TYPE_EXTEMSION.get(self.m_CompressionFormat, '.audioclip')

		if self.m_Source:  #
			resourceReader = ResourceReader(self.m_Source, self.assets_file, m_Offset, m_Size)
		else:
			resourceReader = ResourceReader(reader, reader.Position, m_Size)
		self.m_AudioData = resourceReader.get_data()


class AudioType(IntEnum):
	UNKNOWN = 0,
	ACC = 1,
	AIFF = 2,
	IT = 10,
	MOD = 12,
	MPEG = 13,
	OGGVORBIS = 14,
	S3M = 17,
	WAV = 20,
	XM = 21,
	XMA = 22,
	VAG = 23,
	AUDIOQUEUE = 24


class AudioCompressionFormat(IntEnum):
	PCM = 0,
	Vorbis = 1,
	ADPCM = 2,
	MP3 = 3,
	VAG = 4,
	HEVAG = 5,
	XMA = 6,
	AAC = 7,
	GCADPCM = 8,
	ATRAC9 = 9


AUDIO_TYPE_EXTEMSION = {
	AudioType.ACC: ".m4a",
	AudioType.AIFF: ".aif",
	AudioType.IT: ".it",
	AudioType.MOD: ".mod",
	AudioType.MPEG: ".mp3",
	AudioType.OGGVORBIS: ".ogg",
	AudioType.S3M: ".s3m",
	AudioType.WAV: ".wav",
	AudioType.XM: ".xm",
	AudioType.XMA: ".wav",
	AudioType.VAG: ".vag",
	AudioType.AUDIOQUEUE: ".fsb",

	AudioCompressionFormat.PCM: ".fsb",
	AudioCompressionFormat.Vorbis: ".fsb",
	AudioCompressionFormat.ADPCM: ".fsb",
	AudioCompressionFormat.MP3: ".fsb",
	AudioCompressionFormat.VAG: ".vag",
	AudioCompressionFormat.HEVAG: ".vag",
	AudioCompressionFormat.XMA: ".wav",
	AudioCompressionFormat.AAC: ".m4a",
	AudioCompressionFormat.GCADPCM: ".fsb",
	AudioCompressionFormat.ATRAC9: ".at9",
}
