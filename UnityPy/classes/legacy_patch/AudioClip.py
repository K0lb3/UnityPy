from ..generated import AudioClip
from ...enums import AUDIO_TYPE_EXTEMSION


def _AudioClip_extension(self: AudioClip) -> str:
    return AUDIO_TYPE_EXTEMSION.get(self.m_CompressionFormat, ".audioclip")


def _AudioClip_samples(self: AudioClip) -> dict:
    from ...export import AudioClipConverter

    return AudioClipConverter.extract_audioclip_samples(self)


AudioClip.extension = property(_AudioClip_extension)
AudioClip.samples = property(_AudioClip_samples)

__all__ = ("AudioClip",)
