from ctypes import *
from enum import Enum
import os
import platform
from UnityPy.streams import EndianBinaryWriter, EndianBinaryReader
# dll init
ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
LIB_PATH = os.path.join(ROOT, "lib", "FMOD",platform.system(), platform.architecture()[0])
if platform.system() == 'Windows':
    _dll = WinDLL(os.path.join(LIB_PATH, "fmod.dll"))
elif platform.system() == "Linux":
    _dll = CDLL(os.path.join(LIB_PATH, "libfmod.so"))
elif platform.system() == "Darwin":
    _dll = CDLL(os.path.join(LIB_PATH, "libfmod.dylib"))
else:
    print("UnityPy/export/AudioClipConverter - Warning: unknown system\nIf you want to export AudioClips, you have to set UnityPy.export.AudioClipConverter._dll yourself.")

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
    #system = pyfmodex.System()
    sys_ptr = c_void_p()
    ckresult(_dll.FMOD_System_Create(byref(sys_ptr)))
    #system.init(1, INIT_FLAGS.NORMAL, None)
    ckresult(_dll.FMOD_System_Init(sys_ptr, clip.m_Channels, None, None))

    # get sound
    exinfo = byref(CREATESOUNDEXINFO(length=clip.m_Size))
    #sound = system.create_sound(bytes(clip.m_AudioData),mode=MODE.OPENMEMORY,exinfo=exinfo)
    snd_ptr = c_void_p()
    ckresult(_dll.FMOD_System_CreateSound(sys_ptr, bytes(
        clip.m_AudioData), 0x00000800, exinfo, byref(snd_ptr)))
    sound = Sound(snd_ptr)
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
    # system.release()
    ckresult(_dll.FMOD_System_Release(sys_ptr))
    return samples


def subsound_to_wav(subsound):
    # get sound settings
    length = subsound.get_length(0x00000004)  # TIMEUNIT.PCMBYTES
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
        ptr_data = string_at(ptr, length.value)
        w.write(ptr_data)
    subsound.unlock(*lock)
    return w.bytes


# following code is copied from
# https://github.com/tyrylu/pyfmodex
# pyfmodex can't be used by itself
# because it would require adding the libs to the path first

class CREATESOUNDEXINFO(Structure):
    _fields_ = [("cbsize", c_int), ("length", c_uint)]

    def __init__(self, *args, **kwargs):
        Structure.__init__(self, *args, **kwargs)
        self.cbsize = sizeof(self)


class so:
    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)


class Sound(object):
    def __init__(self, ptr):
        """Constructor.
        :param ptr: The pointer representing this object.
        """
        self._ptr = ptr

    def _call_fmod(self, funcname, *args):
        result = getattr(_dll, funcname)(self._ptr, *args)
        ckresult(result)

    @property
    def num_subsounds(self):
        num = c_int()
        self._call_fmod("FMOD_Sound_GetNumSubSounds", byref(num))
        return num.value

    def get_subsound(self, index):
        sh_ptr = c_void_p()
        self._call_fmod("FMOD_Sound_GetSubSound", index, byref(sh_ptr))
        return Sound(sh_ptr)

    def get_length(self, ltype):
        len = c_uint()
        self._call_fmod("FMOD_Sound_GetLength", byref(len), int(ltype))
        return len.value

    @property
    def format(self):
        type = c_int()
        format = c_int()
        channels = c_int()
        bits = c_int()
        self._call_fmod("FMOD_Sound_GetFormat", byref(type),
                        byref(format), byref(channels), byref(bits))
        return so(type=type.value, format=format.value, channels=channels.value, bits=bits.value)

    @property
    def default_frequency(self):
        freq = c_float()
        pri = c_int()
        self._call_fmod("FMOD_Sound_GetDefaults", byref(freq), byref(pri))
        return freq.value

    def lock(self, offset, length):
        ptr1 = c_void_p()
        len1 = c_uint()
        ptr2 = c_void_p()
        len2 = c_uint()
        ckresult(_dll.FMOD_Sound_Lock(self._ptr, offset, length,
                                      byref(ptr1), byref(ptr2), byref(len1), byref(len2)))
        return ((ptr1, len1), (ptr2, len2))

    def release(self):
        self._call_fmod("FMOD_Sound_Release")

    def unlock(self, i1, i2):
        """I1 and I2 are tuples of form (ptr, len)."""
        ckresult(_dll.FMOD_Sound_Unlock(self._ptr, i1[0], i2[0], i1[1], i2[1]))


def ckresult(result):
    result = RESULT(result)
    if result is not RESULT.OK:
        raise FmodError(result)


class FmodError(Exception):
    def __init__(self, result):
        self.result = result
        self.message = result.name.replace("_", " ")

    def __str__(self):
        return self.message


class RESULT(Enum):
    OK = 0
    BADCOMMAND = 1
    CHANNEL_ALLOC = 2
    CHANNEL_STOLEN = 3
    DMA = 4
    DSP_CONNECTION = 5
    DSP_DONTPROCESS = 6
    DSP_FORMAT = 7
    DSP_INUSE = 8
    DSP_NOTFOUND = 9
    DSP_RESERVED = 10
    DSP_SILENCE = 11
    DSP_TYPE = 12
    FILE_BAD = 13
    FILE_COULDNOTSEEK = 14
    FILE_DISKEJECTED = 15
    FILE_EOF = 16
    FILE_ENDOFDATA = 17
    FILE_NOTFOUND = 18
    FORMAT = 19
    HEADER_MISMATCH = 20
    HTTP = 21
    HTTP_ACCESS = 22
    HTTP_PROXY_AUTH = 23
    HTTP_SERVER_ERROR = 24
    HTTP_TIMEOUT = 25
    INITIALIZATION = 26
    INITIALIZED = 27
    INTERNAL = 28
    INVALID_FLOAT = 29
    INVALID_HANDLE = 30
    INVALID_PARAM = 31
    INVALID_POSITION = 32
    INVALID_SPEAKER = 33
    INVALID_SYNCPOINT = 34
    INVALID_THREAD = 35
    INVALID_VECTOR = 36
    MAXAUDIBLE = 37
    MEMORY = 38
    MEMORY_CANTPOINT = 39
    NEEDS3D = 40
    NEEDSHARDWARE = 41
    NET_CONNECT = 42
    NET_SOCKET_ERROR = 43
    NET_URL = 44
    NET_WOULD_BLOCK = 45
    NOTREADY = 46
    OUTPUT_ALLOCATED = 47
    OUTPUT_CREATEBUFFER = 48
    OUTPUT_DRIVERCALL = 49
    OUTPUT_FORMAT = 50
    OUTPUT_INIT = 51
    OUTPUT_NODRIVERS = 52
    PLUGIN = 53
    PLUGIN_MISSING = 54
    PLUGIN_RESOURCE = 55
    PLUGIN_VERSION = 56
    RECORD = 57
    REVERB_CHANNELGROUP = 58
    REVERB_INSTANCE = 59
    SUBSOUNDS = 60
    SUBSOUND_ALLOCATED = 61
    SUBSOUND_CANTMOVE = 62
    TAGNOTFOUND = 63
    TOOMANYCHANNELS = 64
    TRUNCATED = 65
    UNIMPLEMENTED = 66
    UNINITIALIZED = 67
    UNSUPPORTED = 68
    VERSION = 69
    EVENT_ALREADY_LOADED = 70
    EVENT_LIVEUPDATE_BUSY = 71
    EVENT_LIVEUPDATE_MISMATCH = 72
    EVENT_LIVEUPDATE_TIMEOUT = 73
    EVENT_NOTFOUND = 74
    STUDIO_UNINITIALIZED = 75
    STUDIO_NOT_LOADED = 76
    INVALID_STRING = 77
    ALREADY_LOCKED = 78
    NOT_LOCKED = 79
    RECORD_DISCONNECTED = 80
    TOOMANYSAMPLES = 81
