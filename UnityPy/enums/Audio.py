from enum import IntEnum


class AudioType(IntEnum):
    UNKNOWN = (0,)
    ACC = (1,)
    AIFF = (2,)
    IT = (10,)
    MOD = (12,)
    MPEG = (13,)
    OGGVORBIS = (14,)
    S3M = (17,)
    WAV = (20,)
    XM = (21,)
    XMA = (22,)
    VAG = (23,)
    AUDIOQUEUE = 24


class AudioCompressionFormat(IntEnum):
    PCM = (0,)
    Vorbis = (1,)
    ADPCM = (2,)
    MP3 = (3,)
    VAG = (4,)
    HEVAG = (5,)
    XMA = (6,)
    AAC = (7,)
    GCADPCM = (8,)
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
