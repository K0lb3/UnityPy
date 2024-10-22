from __future__ import annotations

import ctypes
import os
import platform
from typing import TYPE_CHECKING, Dict, Union

from UnityPy.streams import EndianBinaryWriter

from ..helpers.ResourceReader import get_resource_data

if TYPE_CHECKING:
    from ..classes import AudioClip

# pyfmodex loads the dll/so/dylib on import
# so we have to adjust the environment vars
# before importing it
# This is done in import_pyfmodex()
# which will replace the global pyfmodex var
pyfmodex = None


def get_fmod_path(
    system: Union["Windows", "Linux", "Darwin"], arch: ["x64", "x86", "arm"]
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

    if "arm" in machine or "aarch64" in machine:
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


def extract_audioclip_samples(audio: AudioClip) -> Dict[str, bytes]:
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
    return dump_samples(audio, audio_data)


def dump_samples(clip: AudioClip, audio_data: bytes) -> Dict[str, bytes]:
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
        samples[filename] = subsound_to_wav(subsound)
        subsound.release()

    sound.release()
    system.release()
    return samples


def subsound_to_wav(subsound) -> bytes:
    # get sound settings
    length = subsound.get_length(pyfmodex.enums.TIMEUNIT.PCMBYTES)
    channels = subsound.format.channels
    bits = subsound.format.bits
    sample_rate = int(subsound.default_frequency)

    # write to buffer
    w = EndianBinaryWriter(endian="<")
    # riff chucnk
    w.write(b"RIFF")
    w.write_int(length + 36)  # sizeof(FmtChunk) + sizeof(RiffChunk) + length
    w.write(b"WAVE")
    # fmt chunck
    w.write(b"fmt ")
    w.write_int(16)  # sizeof(FmtChunk) - sizeof(RiffChunk)
    w.write_short(1)
    w.write_short(channels)
    w.write_int(sample_rate)
    w.write_int(sample_rate * channels * bits // 8)
    w.write_short(channels * bits // 8)
    w.write_short(bits)
    # data chunck
    w.write(b"data")
    w.write_int(length)
    # data
    lock = subsound.lock(0, length)
    for ptr, length in lock:
        ptr_data = ctypes.string_at(ptr, length.value)
        w.write(ptr_data)
    subsound.unlock(*lock)
    return w.bytes
