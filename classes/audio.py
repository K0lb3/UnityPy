import logging
from enum import IntEnum

from .component import Behaviour
from .object import Object, field


class AudioFormat(IntEnum):
	UNKNOWN = 0
	ACC = 1
	AIFF = 2
	IT = 10
	MOD = 12
	MPEG = 13
	OGGVORBIS = 14
	S3M = 17
	WAV = 20
	XM = 21
	XMA = 22
	VAG = 23
	AUDIOQUEUE = 24


class AudioRolloffMode(IntEnum):
	Logarithmic = 0
	Linear = 1
	Custom = 2


class AudioClip(Object):
	bits_per_sample = field("m_BitsPerSample")
	channels = field("m_Channels")
	compression_format = field("m_CompressionFormat")
	frequency = field("m_Frequency")
	is_tracker_format = field("m_IsTrackerFormat")
	legacy3d = field("m_Legacy3D")
	length = field("m_Length")
	load_in_background = field("m_LoadInBackground")
	load_type = field("m_LoadType")
	preload_audio_data = field("m_PreloadAudioData")
	subsound_index = field("m_SubsoundIndex")
	resource = field("m_Resource")
	
	@property
	def data(self):
		if not hasattr(self, "_data"):
			self._data = self.resource.get_data()
		return self._data


class AudioSource(Behaviour):
	bypass_effects = field("BypassEffects", bool)
	bypass_listener_effects = field("BypassListenerEffects", bool)
	bypass_reverb_zones = field("BypassReverbZones", bool)
	clip = field("m_audioClip")
	doppler_level = field("DopplerLevel")
	loop = field("Loop", bool)
	max_distance = field("MaxDistance")
	min_distance = field("MinDistance")
	mute = field("Mute", bool)
	output_audio_mixer_group = field("OutputAudioMixerGroup")
	pan_stereo = field("Pan2D")
	pitch = field("m_Pitch")
	play_on_awake = field("m_PlayOnAwake", bool)
	priority = field("Priority")
	rolloff_mode = field("rolloffMode", AudioRolloffMode)
	volume = field("m_Volume")
	
	rolloff_custom_curve = field("rolloffCustomCurve")
	reverb_zone_mix_custom_curve = field("reverbZoneMixCustomCurve")
	pan_level_custom_curve = field("panLevelCustomCurve")
	spread_custom_curve = field("spreadCustomCurve")


class StreamedResource(Object):
	offset = field("m_Offset")
	source = field("m_Source")
	size = field("m_Size")
	
	def get_data(self):
		if not self.asset:
			logging.warning("No data available for StreamedResource")
			return b""
		self.asset._buf.seek(self.asset._buf_ofs + self.offset)
		return self.asset._buf.read(self.size)
