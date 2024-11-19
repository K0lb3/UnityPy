import sys

from typing_extensions import Literal

Endianess = Literal["<", ">"]
SYS_ENDIAN = "<" if sys.byteorder == "little" else ">"


TYPE_PARAM_SIZE_LIST = [
    ("short", "h", 2),
    ("u_short", "H", 2),
    ("int", "i", 4),
    ("u_int", "I", 4),
    ("long", "q", 8),
    ("u_long", "Q", 8),
    ("half", "e", 2),
    ("float", "f", 4),
    ("double", "d", 8),
    ("vector2", "2f", 8),
    ("vector3", "3f", 12),
    ("vector4", "4f", 16),
]
