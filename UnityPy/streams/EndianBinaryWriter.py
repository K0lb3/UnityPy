import builtins
from io import BytesIO, IOBase
from struct import pack
from typing import Callable, Sequence, TypeVar, Union

T = TypeVar("T")


class EndianBinaryWriter:
    endian: str
    Position: int
    stream: IOBase

    def __init__(self, input_: Union[bytes, bytearray, IOBase] = b"", endian: str = ">"):
        if isinstance(input_, (bytes, bytearray)):
            self.stream = BytesIO(input_)
            self.stream.seek(0, 2)
        elif isinstance(input_, IOBase):
            self.stream = input_
        else:
            raise ValueError("Invalid input type - %s." % type(input_))
        self.endian = endian
        self.Position = self.stream.tell()

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

    def write_bytes(self, value: builtins.bytes):
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

    def write_aligned_string(self, value: str):
        bstring = value.encode("utf8", "surrogateescape")
        self.write_int(len(bstring))
        self.write(bstring)
        self.align_stream(4)

    def align_stream(self, alignment: int = 4):
        pos = self.stream.tell()
        align = (alignment - pos % alignment) % alignment
        self.write(b"\0" * align)

    def write_array(
        self,
        command: Callable[[T], None],
        value: Sequence[T],
        write_length: bool = True,
    ):
        if write_length:
            self.write_int(len(value))
        for val in value:
            command(val)

    def write_byte_array(self, value: builtins.bytes):
        self.write_int(len(value))
        self.write(value)

    def write_boolean_array(self, value: Sequence[bool]):
        self.write_array(self.write_boolean, value)

    def write_u_short_array(self, value: Sequence[int]):
        self.write_array(self.write_u_short, value)

    def write_int_array(self, value: Sequence[int], write_length: bool = False):
        return self.write_array(self.write_int, value, write_length)

    def write_u_int_array(self, value: Sequence[int], write_length: bool = False):
        return self.write_array(self.write_u_int, value, write_length)

    def write_float_array(self, value: Sequence[float], write_length: bool = False):
        return self.write_array(self.write_float, value, write_length)

    def write_string_array(self, value: Sequence[str]):
        self.write_array(self.write_aligned_string, value)
