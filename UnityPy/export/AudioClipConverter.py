import ctypes
import os
import platform
from UnityPy.streams import EndianBinaryWriter, EndianBinaryReader
# pyfmodex init
try:
    ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    LIB_PATH = os.path.join(ROOT, "lib", "FMOD", platform.system(), platform.architecture()[0])

    if platform.system() == 'Windows':
        _dll = ctypes.WinDLL(os.path.join(LIB_PATH, "fmod.dll"))
    elif platform.system() == "Linux":
        _dll = ctypes.CDLL(os.path.join(LIB_PATH, "libfmod.so"))
    elif platform.system() == "Darwin":
        _dll = ctypes.CDLL(os.path.join(LIB_PATH, "libfmod.dylib"))

    import pyfmodex
    pyfmodex.fmodex._dll = _dll
    from pyfmodex.structures import CREATESOUNDEXINFO
    from pyfmodex.flags import MODE, TIMEUNIT, INIT_FLAGS
except Exception as e:
    print("Error during the pyfmodex initialisation - AudioClips.samples won't work", e)


def extract_audioclip_samples(audio) -> dict:
    """extracts all the samples from an AudioClip
        :param audio: AudioClip
        :type audio: AudioClip
        :return: {filename : sample(bytes)}
        :rtype: dict
    """

    if not audio.m_AudioData:
        # eg. StreamedResource not available
        return {}

    magic = memoryview(audio.m_AudioData)[:4]
    if magic == b'OggS':
        return {'%s.ogg' % audio.name: audio.m_AudioData}
    elif magic == b'RIFF':
        return {'%s.wav' % audio.name: audio.m_AudioData}
    return dump_samples(audio)


def dump_samples(clip):
    # init system
    system = pyfmodex.System()
    system.init(1, INIT_FLAGS.NORMAL, None)
    exinfo = CREATESOUNDEXINFO(length=clip.m_Size,)

    # get sound
    sound = system.create_sound(
        bytes(clip.m_AudioData),
        mode=MODE.OPENMEMORY,
        exinfo=exinfo
    )
    # iterate over subsounds
    samples = {}
    for i in range(sound.num_subsounds):
        if i > 0:
            filename = "%s-%i.wav" % (clip.name, i)
        else:
            filename = "%s.wav" % (clip.name)
        subsound = sound.get_subsound(i)
        samples[filename] = subsound_to_wav(subsound)
        subsound.release()

    sound.release()
    system.release()
    return samples


def subsound_to_wav(subsound):
    # get sound settings
    length = subsound.get_length(TIMEUNIT.PCMBYTES)
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
