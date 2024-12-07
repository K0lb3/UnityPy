from io import BytesIO
from struct import pack
from typing import BinaryIO, Union

from ..math import Color, Matrix4x4, Quaternion, Rectangle, Vector2, Vector3, Vector4
from ._defines import Endianess


class EndianBinaryWriter:
    endian: Endianess
    Length: int
    Position: int
    stream: BinaryIO

    def __init__(
        self, input_: Union[bytes, bytearray, BinaryIO] = b"", endian: Endianess = ">"
    ):
        if isinstance(input_, (bytes, bytearray)):
            self.stream = BytesIO(input_)
            self.stream.seek(0, 2)
        elif isinstance(input_, BinaryIO):
            self.stream = input_
        else:
            raise ValueError("Invalid input type - %s." % type(input_))
        self.endian = endian
        self.Position = self.stream.tell()

    def seek(self, offset: int, whence: int = 0):
        if whence == 0:
            self.Position = offset
        elif whence == 1:
            self.Position += offset
        elif whence == 2:
            self.Position = self.Length + offset
        else:
            raise ValueError("Invalid whence")

    def tell(self) -> int:
        return self.Position

    def get_bytes(self) -> bytes:
        return self.bytes

    @property
    def bytes(self):
        self.stream.seek(0)
        return self.stream.read()

    @property
    def Length(self) -> int:
        pos = self.stream.tell()
        self.stream.seek(0, 2)
        length = self.stream.tell()
        self.stream.seek(pos)
        return length

    def dispose(self):
        self.stream.close()
        pass

    def write(self, *args):
        if self.Position != self.stream.tell():
            self.stream.seek(self.Position)
        ret = self.stream.write(*args)
        self.Position = self.stream.tell()
        return ret

    def write_byte(self, value: int):
        self.write(pack(self.endian + "b", value))

    def write_u_byte(self, value: int):
        self.write(pack(self.endian + "B", value))

    def write_bytes(self, value: bytes):
        return self.write(value)

    def write_short(self, value: int):
        self.write(pack(self.endian + "h", value))

    def write_int(self, value: int):
        self.write(pack(self.endian + "i", value))

    def write_long(self, value: int):
        self.write(pack(self.endian + "q", value))

    def write_u_short(self, value: int):
        self.write(pack(self.endian + "H", value))

    def write_u_int(self, value: int):
        self.write(pack(self.endian + "I", value))

    def write_u_long(self, value: int):
        self.write(pack(self.endian + "Q", value))

    def write_float(self, value: float):
        self.write(pack(self.endian + "f", value))

    def write_double(self, value: float):
        self.write(pack(self.endian + "d", value))

    def write_boolean(self, value: bool):
        self.write(pack(self.endian + "?", value))

    def write_string_to_null(self, value: str):
        self.write(value.encode("utf8", "surrogateescape"))
        self.write(b"\0")

    def write_string(self, value: str):
        bstring = value.encode("utf8", "surrogateescape")
        self.write_int(len(bstring))
        self.write(bstring)

    def write_aligned_string(self, value: str):
        self.write_string(value)
        self.align_stream(4)

    def align_stream(self, alignment=4):
        pos = self.stream.tell()
        align = (alignment - pos % alignment) % alignment
        self.write(b"\0" * align)

    def write_array(self, command, value: list, write_length: bool = True):
        if write_length:
            self.write_int(len(value))
        for val in value:
            command(val)

    def write_byte_array(self, value: bytes):
        self.write_int(len(value))
        self.write(value)

    def write_boolean_array(self, value: list):
        self.write_array(self.write_boolean, value)

    def write_u_short_array(self, value: list):
        self.write_array(self.write_u_short, value)

    def write_int_array(self, value: list, write_length: bool = False):
        return self.write_array(self.write_int, value, write_length)

    def write_u_int_array(self, value: list, write_length: bool = False):
        return self.write_array(self.write_u_int, value, write_length)

    def write_float_array(self, value: list, write_length: bool = False):
        return self.write_array(self.write_float, value, write_length)
