from __future__ import annotations

import ctypes
import os
import platform
from typing import TYPE_CHECKING, Dict, Union

from UnityPy.streams import EndianBinaryWriter

from ..helpers.ResourceReader import get_resource_data

try:
    import numpy as np
except ImportError:
    np = None
    import struct

if TYPE_CHECKING:
    from ..classes import AudioClip

# pyfmodex loads the dll/so/dylib on import
# so we have to adjust the environment vars
# before importing it
# This is done in import_pyfmodex()
# which will replace the global pyfmodex var
pyfmodex = None


def get_fmod_path(
    system: Union["Windows", "Linux", "Darwin"], arch: ["x64", "x86", "arm", "arm64"]
) -> str:
    if system == "Darwin":
        # universal dylib
        return "lib/FMOD/Darwin/libfmod.dylib"

    if system == "Windows":
        return f"lib/FMOD/Windows/{arch}/fmod.dll"

    if system == "Linux":
        if arch == "x64":
            arch = "x86_64"
        return f"lib/FMOD/Linux/{arch}/libfmod.so"

    raise NotImplementedError(f"Unsupported system: {system}")


def import_pyfmodex():
    global pyfmodex
    if pyfmodex is not None:
        return

    # determine system - Windows, Darwin, Linux, Android
    system = platform.system()
    arch = platform.architecture()[0]
    machine = platform.machine()

    if "arm" in machine:
        arch = "arm"
    elif "aarch64" in machine:
        if system == "Linux":
            arch = "arm64"
        else:
            arch = "arm"
    elif arch == "32bit":
        arch = "x86"
    elif arch == "64bit":
        arch = "x64"

    fmod_rel_path = get_fmod_path(system, arch)
    fmod_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))), fmod_rel_path
    )
    os.environ["PYFMODEX_DLL_PATH"] = fmod_path

    # build path and load library
    # prepare the environment for pyfmodex
    if system != "Windows":
        # hotfix ctypes for pyfmodex for non windows systems
        ctypes.windll = None

    import pyfmodex


def extract_audioclip_samples(
    audio: AudioClip, convert_pcm_float: bool = True
) -> Dict[str, bytes]:
    """extracts all the samples from an AudioClip
    :param audio: AudioClip
    :type audio: AudioClip
    :return: {filename : sample(bytes)}
    :rtype: dict
    """
    if audio.m_AudioData:
        audio_data = audio.m_AudioData
    else:
        resource = audio.m_Resource
        audio_data = get_resource_data(
            resource.m_Source,
            audio.object_reader.assets_file,
            resource.m_Offset,
            resource.m_Size,
        )

    magic = memoryview(audio_data)[:8]
    if magic[:4] == b"OggS":
        return {f"{audio.m_Name}.ogg": audio_data}
    elif magic[:4] == b"RIFF":
        return {f"{audio.m_Name}.wav": audio_data}
    elif magic[4:8] == b"ftyp":
        return {f"{audio.m_Name}.m4a": audio_data}
    return dump_samples(audio, audio_data, convert_pcm_float)


def dump_samples(
    clip: AudioClip, audio_data: bytes, convert_pcm_float: bool = True
) -> Dict[str, bytes]:
    if pyfmodex is None:
        import_pyfmodex()
    if not pyfmodex:
        return {}
    # init system
    system = pyfmodex.System()
    system.init(clip.m_Channels, pyfmodex.flags.INIT_FLAGS.NORMAL, None)

    sound = system.create_sound(
        bytes(audio_data),
        pyfmodex.flags.MODE.OPENMEMORY,
        exinfo=pyfmodex.structure_declarations.CREATESOUNDEXINFO(
            length=len(audio_data),
            numchannels=clip.m_Channels,
            defaultfrequency=clip.m_Frequency,
        ),
    )

    # iterate over subsounds
    samples = {}
    for i in range(sound.num_subsounds):
        if i > 0:
            filename = "%s-%i.wav" % (clip.m_Name, i)
        else:
            filename = "%s.wav" % clip.m_Name
        subsound = sound.get_subsound(i)
        samples[filename] = subsound_to_wav(subsound, convert_pcm_float)
        subsound.release()

    sound.release()
    system.release()
    return samples


def subsound_to_wav(subsound, convert_pcm_float: bool = True) -> bytes:
    # get sound settings
    sound_format = subsound.format.format
    sound_data_length = subsound.get_length(pyfmodex.enums.TIMEUNIT.PCMBYTES)
    channels = subsound.format.channels
    bits = subsound.format.bits
    sample_rate = int(subsound.default_frequency)

    if sound_format in [
        pyfmodex.enums.SOUND_FORMAT.PCM8,
        pyfmodex.enums.SOUND_FORMAT.PCM16,
        pyfmodex.enums.SOUND_FORMAT.PCM24,
        pyfmodex.enums.SOUND_FORMAT.PCM32,
    ]:
        audio_format = 1
        wav_data_length = sound_data_length
        convert_pcm_float = False
    elif sound_format == pyfmodex.enums.SOUND_FORMAT.PCMFLOAT:
        if convert_pcm_float:
            audio_format = 1
            bits = 16
            wav_data_length = sound_data_length // 2
        else:
            audio_format = 3
            wav_data_length = sound_data_length
    else:
        raise NotImplementedError("Sound format " + sound_format + " is not supported.")

    w = EndianBinaryWriter(endian="<")

    # RIFF header
    w.write(b"RIFF")  # chunk id
    w.write_int(
        wav_data_length + 36
    )  # chunk size - 4 + (8 + 16 (sub chunk 1 size)) + (8 + length (sub chunk 2 size))
    w.write(b"WAVE")  # format

    # fmt chunk - sub chunk 1
    w.write(b"fmt ")  # sub chunk 1 id
    w.write_int(16)  # sub chunk 1 size, 16 for PCM
    w.write_short(audio_format)  # audio format, 1: PCM integer, 3: IEEE 754 float
    w.write_short(channels)  # number of channels
    w.write_int(sample_rate)  # sample rate
    w.write_int(sample_rate * channels * bits // 8)  # byte rate
    w.write_short(channels * bits // 8)  # block align
    w.write_short(bits)  # bits per sample

    # data chunk - sub chunk 2
    w.write(b"data")  # sub chunk 2 id
    w.write_int(wav_data_length)  # sub chunk 2 size
    # sub chunk 2 data
    lock = subsound.lock(0, sound_data_length)
    for ptr, sound_data_length in lock:
        ptr_data = ctypes.string_at(ptr, sound_data_length.value)
        if convert_pcm_float:
            if np is not None:
                ptr_data = np.frombuffer(ptr_data, dtype=np.float32)
                ptr_data = (ptr_data * 2**15).astype(np.int16).tobytes()
            else:
                ptr_data = struct.unpack("<%df" % (len(ptr_data) // 4), ptr_data)
                ptr_data = struct.pack(
                    "<%dh" % len(ptr_data), *[int(f * 2**15) for f in ptr_data]
                )

        w.write(ptr_data)
    subsound.unlock(*lock)

    return w.bytes
