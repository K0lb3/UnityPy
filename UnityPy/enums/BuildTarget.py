from enum import IntEnum


class BuildTarget(IntEnum):
    UnknownPlatform = (3716,)
    DashboardWidget = (1,)
    StandaloneOSX = (2,)
    StandaloneOSXPPC = (3,)
    StandaloneOSXIntel = (4,)
    StandaloneWindows = (5,)
    WebPlayer = (6,)
    WebPlayerStreamed = (7,)
    Wii = (8,)
    iOS = (9,)
    PS3 = (10,)
    XBOX360 = (11,)
    Android = (13,)
    StandaloneGLESEmu = (14,)
    NaCl = (16,)
    StandaloneLinux = (17,)
    FlashPlayer = (18,)
    StandaloneWindows64 = (19,)
    WebGL = (20,)
    WSAPlayer = (21,)
    StandaloneLinux64 = (24,)
    StandaloneLinuxUniversal = (25,)
    WP8Player = (26,)
    StandaloneOSXIntel64 = (27,)
    BlackBerry = (28,)
    Tizen = (29,)
    PSP2 = (30,)
    PS4 = (31,)
    PSM = (32,)
    XboxOne = (33,)
    SamsungTV = (34,)
    N3DS = (35,)
    WiiU = (36,)
    tvOS = (37,)
    Switch = (38,)
    NoTarget = -2

    @classmethod
    def _missing_(cls, value):
        return BuildTarget.UnknownPlatform
