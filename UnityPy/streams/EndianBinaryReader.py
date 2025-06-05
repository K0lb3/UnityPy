import builtins
import re
import sys
from io import BufferedReader, IOBase
from struct import Struct, unpack
from typing import Callable, List, Optional, Tuple, Union

reNot0 = re.compile(b"(.*?)\x00", re.S)

SYS_ENDIAN = "<" if sys.byteorder == "little" else ">"

# generate unpack and unpack_from functions
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
]

LOCALS = locals()
for endian_s, endian_l in (("<", "little"), (">", "big")):
    for typ, param, _ in TYPE_PARAM_SIZE_LIST:
        LOCALS[f"unpack_{endian_l}_{typ}"] = Struct(f"{endian_s}{param}").unpack
        LOCALS[f"unpack_{endian_l}_{typ}_from"] = Struct(f"{endian_s}{param}").unpack_from


class EndianBinaryReader:
    endian: str
    Length: int
    Position: int
    BaseOffset: int

    def __new__(
        cls,
        item: Union[bytes, bytearray, memoryview, IOBase, str],
        endian: str = ">",
        offset: int = 0,
    ):
        if isinstance(item, (bytes, bytearray, memoryview)):
            obj = super(EndianBinaryReader, cls).__new__(EndianBinaryReader_Memoryview)
        elif isinstance(item, IOBase):
            obj = super(EndianBinaryReader, cls).__new__(EndianBinaryReader_Streamable)
        elif isinstance(item, str):
            item = open(item, "rb")
            obj = super(EndianBinaryReader, cls).__new__(EndianBinaryReader_Streamable)
        elif isinstance(item, EndianBinaryReader):
            item = item.stream if isinstance(item, EndianBinaryReader_Streamable) else item.view
            return EndianBinaryReader(item, endian, offset)
        elif hasattr(item, "read"):
            if hasattr(item, "seek") and hasattr(item, "tell"):
                obj = super(EndianBinaryReader, cls).__new__(EndianBinaryReader_Streamable)
            else:
                item = item.read()
                obj = super(EndianBinaryReader, cls).__new__(EndianBinaryReader_Memoryview)

        obj.__init__(item, endian)
        return obj

    def __init__(self, item, endian: str = ">", offset: int = 0):
        self.endian = endian
        self.BaseOffset = offset
        self.Position = 0

    @property
    def bytes(self) -> builtins.bytes:
        # implemented by Streamable and Memoryview versions
        return b""

    def read(self, *args) -> builtins.bytes:
        # implemented by Streamable and Memoryview versions
        return b""

    def read_byte(self) -> int:
        return unpack(self.endian + "b", self.read(1))[0]

    def read_u_byte(self) -> int:
        return unpack(self.endian + "B", self.read(1))[0]

    def read_bytes(self, num: int) -> builtins.bytes:
        return self.read(num)

    def read_short(self) -> int:
        return unpack(self.endian + "h", self.read(2))[0]

    def read_int(self) -> int:
        return unpack(self.endian + "i", self.read(4))[0]

    def read_long(self) -> int:
        return unpack(self.endian + "q", self.read(8))[0]

    def read_u_short(self) -> int:
        return unpack(self.endian + "H", self.read(2))[0]

    def read_u_int(self) -> int:
        return unpack(self.endian + "I", self.read(4))[0]

    def read_u_long(self) -> int:
        return unpack(self.endian + "Q", self.read(8))[0]

    def read_float(self) -> float:
        return unpack(self.endian + "f", self.read(4))[0]

    def read_double(self) -> float:
        return unpack(self.endian + "d", self.read(8))[0]

    def read_boolean(self) -> bool:
        return bool(unpack(self.endian + "?", self.read(1))[0])

    def read_string(self, size: Optional[int] = None, encoding: str = "utf8") -> str:
        if size is None:
            ret = self.read_string_to_null()
        else:
            ret = unpack(f"{self.endian}{size}is", self.read(size))[0]
        try:
            return ret.decode(encoding)
        except UnicodeDecodeError:
            return ret

    def read_string_to_null(self, max_length: int = 32767) -> str:
        ret = []
        c = b""
        while c != b"\0" and len(ret) < max_length and self.Position != self.Length:
            ret.append(c)
            c = self.read(1)
            if not c:
                raise ValueError("Unterminated string: %r" % ret)
        return b"".join(ret).decode("utf8", "surrogateescape")

    def read_aligned_string(self) -> str:
        length = self.read_int()
        if 0 < length <= self.Length - self.Position:
            string_data = bytes(self.read_bytes(length))
            result = string_data.decode("utf8", "surrogateescape")
            self.align_stream()
            return result
        return ""

    def align_stream(self, alignment=4):
        self.Position += (alignment - self.Position % alignment) % alignment

    def read_byte_array(self) -> builtins.bytes:
        return self.read(self.read_int())

    def read_array(self, command: Callable, length: int) -> list:
        return [command() for _ in range(length)]

    def read_array_struct(self, param: str, length: Optional[int] = None) -> tuple:
        if length is None:
            length = self.read_int()
        struct = Struct(f"{self.endian}{length}{param}")
        return struct.unpack(self.read(struct.size))

    def read_boolean_array(self, length: Optional[int] = None) -> Tuple[bool, ...]:
        return self.read_array_struct("?", length)

    def read_u_byte_array(self, length: Optional[int] = None) -> Tuple[int, ...]:
        return self.read_array_struct("B", length)

    def read_u_short_array(self, length: Optional[int] = None) -> Tuple[int, ...]:
        return self.read_array_struct("h", length)

    def read_short_array(self, length: Optional[int] = None) -> Tuple[int, ...]:
        return self.read_array_struct("H", length)

    def read_int_array(self, length: Optional[int] = None) -> Tuple[int, ...]:
        return self.read_array_struct("i", length)

    def read_u_int_array(self, length: Optional[int] = None) -> Tuple[int, ...]:
        return self.read_array_struct("I", length)

    def read_long_array(self, length: Optional[int] = None) -> Tuple[int, ...]:
        return self.read_array_struct("q", length)

    def read_u_long_array(self, length: Optional[int] = None) -> Tuple[int, ...]:
        return self.read_array_struct("Q", length)

    def read_u_int_array_array(self, length: Optional[int] = None) -> List[Tuple[int, ...]]:
        return self.read_array(self.read_u_int_array, length if length is not None else self.read_int())

    def read_float_array(self, length: Optional[int] = None) -> Tuple[float, ...]:
        return self.read_array_struct("f", length)

    def read_double_array(self, length: Optional[int] = None) -> Tuple[float, ...]:
        return self.read_array_struct("d", length)

    def read_string_array(self) -> List[str]:
        return self.read_array(self.read_aligned_string, self.read_int())

    def real_offset(self) -> int:
        """Returns offset in the underlying file.
        (Not working with unpacked streams.)
        """
        return self.BaseOffset + self.Position

    def read_the_rest(self, obj_start: int, obj_size: int) -> builtins.bytes:
        """Returns the rest of the current reader bytes."""
        return self.read_bytes(obj_size - (self.Position - obj_start))


class EndianBinaryReader_Memoryview(EndianBinaryReader):
    __slots__ = ("view", "_endian", "BaseOffset", "Position", "Length")
    view: memoryview

    def __init__(self, view, endian: str = ">", offset: int = 0):
        self._endian = ""
        super().__init__(view, endian=endian, offset=offset)
        self.view = memoryview(view)
        self.Length = len(view)

    @property
    def endian(self):
        return self._endian

    @endian.setter
    def endian(self, value: str):
        if value not in ("<", ">"):
            raise ValueError("Invalid endian")
        if value != self._endian:
            setattr(  # noqa: B010
                self,
                "__class__",
                EndianBinaryReader_Memoryview_LittleEndian if value == "<" else EndianBinaryReader_Memoryview_BigEndian,
            )
            self._endian = value

    @property
    def bytes(self) -> memoryview:
        return self.view

    def dispose(self) -> None:
        self.view.release()

    def read(self, length: int) -> memoryview:
        if not length:
            return memoryview(b"")
        ret = self.view[self.Position : self.Position + length]
        self.Position += length
        return ret

    def read_aligned_string(self) -> str:
        length = self.read_int()
        if 0 < length <= self.Length - self.Position:
            string_data = self.read_bytes(length)
            result = bytes(string_data).decode("utf8", "surrogateescape")
            self.align_stream()
            return result
        return ""

    def read_string_to_null(self, max_length: int = 32767) -> str:
        match = reNot0.search(self.view, self.Position, self.Position + max_length)
        if not match:
            if self.Position + max_length >= self.Length:
                raise Exception("String not terminated")
            else:
                return bytes(self.read_bytes(max_length)).decode("utf8", "surrogateescape")
        ret = match[1].decode("utf8", "surrogateescape")
        self.Position = match.end()
        return ret


class EndianBinaryReader_Memoryview_LittleEndian(EndianBinaryReader_Memoryview):
    def read_u_short(self):
        (ret,) = unpack_little_u_short_from(self.view, self.Position)
        self.Position += 2
        return ret

    def read_short(self):
        (ret,) = unpack_little_short_from(self.view, self.Position)
        self.Position += 2
        return ret

    def read_int(self):
        (ret,) = unpack_little_int_from(self.view, self.Position)
        self.Position += 4
        return ret

    def read_u_int(self):
        (ret,) = unpack_little_u_int_from(self.view, self.Position)
        self.Position += 4
        return ret

    def read_long(self):
        (ret,) = unpack_little_long_from(self.view, self.Position)
        self.Position += 8
        return ret

    def read_u_long(self):
        (ret,) = unpack_little_u_long_from(self.view, self.Position)
        self.Position += 8
        return ret

    def read_half(self):
        (ret,) = unpack_little_half_from(self.view, self.Position)
        self.Position += 2
        return ret

    def read_float(self):
        (ret,) = unpack_little_float_from(self.view, self.Position)
        self.Position += 4
        return ret

    def read_double(self):
        (ret,) = unpack_little_double_from(self.view, self.Position)
        self.Position += 8
        return ret


class EndianBinaryReader_Memoryview_BigEndian(EndianBinaryReader_Memoryview):
    def read_u_short(self):
        (ret,) = unpack_big_u_short_from(self.view, self.Position)
        self.Position += 2
        return ret

    def read_short(self):
        (ret,) = unpack_big_short_from(self.view, self.Position)
        self.Position += 2
        return ret

    def read_int(self):
        (ret,) = unpack_big_int_from(self.view, self.Position)
        self.Position += 4
        return ret

    def read_u_int(self):
        (ret,) = unpack_big_u_int_from(self.view, self.Position)
        self.Position += 4
        return ret

    def read_long(self):
        (ret,) = unpack_big_long_from(self.view, self.Position)
        self.Position += 8
        return ret

    def read_u_long(self):
        (ret,) = unpack_big_u_long_from(self.view, self.Position)
        self.Position += 8
        return ret

    def read_half(self):
        (ret,) = unpack_big_half_from(self.view, self.Position)
        self.Position += 2
        return ret

    def read_float(self):
        (ret,) = unpack_big_float_from(self.view, self.Position)
        self.Position += 4
        return ret

    def read_double(self):
        (ret,) = unpack_big_double_from(self.view, self.Position)
        self.Position += 8
        return ret


class EndianBinaryReader_Streamable(EndianBinaryReader):
    __slots__ = ("stream", "_endian", "BaseOffset")
    stream: BufferedReader

    def __init__(self, stream, endian=">", offset=0):
        self._endian = ""
        self.stream = stream
        super().__init__(stream, endian=endian, offset=offset)
        self.read = self.stream.read

    def get_position(self):
        return self.stream.tell()

    def set_position(self, value):
        self.stream.seek(value + self.BaseOffset)

    @property
    def endian(self):
        return self._endian

    @endian.setter
    def endian(self, value):
        if value not in ("<", ">"):
            raise ValueError("Invalid endian")
        if value != self._endian:
            setattr(  # noqa: B010
                self,
                "__class__",
                EndianBinaryReader_Streamable_LittleEndian if value == "<" else EndianBinaryReader_Streamable_BigEndian,
            )
            self._endian = value

    @property
    def Length(self):
        pos = self.Position
        length = self.stream.seek(0, 2) - self.BaseOffset
        self.Position = pos
        return length

    Position = property(get_position, set_position)

    @property
    def bytes(self):
        last_pos = self.Position
        self.Position = 0
        ret = self.read(self.Length)
        self.Position = last_pos
        return ret

    def dispose(self):
        self.stream.close()
        pass


class EndianBinaryReader_Streamable_LittleEndian(EndianBinaryReader_Streamable):
    def read_u_short(self):
        return unpack_little_u_short(self.read(2))[0]

    def read_short(self):
        return unpack_little_short(self.read(2))[0]

    def read_int(self):
        return unpack_little_int(self.read(4))[0]

    def read_u_int(self):
        return unpack_little_u_int(self.read(4))[0]

    def read_long(self):
        return unpack_little_long(self.read(8))[0]

    def read_u_long(self):
        return unpack_little_u_long(self.read(8))[0]

    def read_half(self):
        return unpack_little_half(self.read(2))[0]

    def read_float(self):
        return unpack_little_float(self.read(4))[0]

    def read_double(self):
        return unpack_little_double(self.read(8))[0]


class EndianBinaryReader_Streamable_BigEndian(EndianBinaryReader_Streamable):
    def read_u_short(self):
        return unpack_big_u_short(self.read(2))[0]

    def read_short(self):
        return unpack_big_short(self.read(2))[0]

    def read_int(self):
        return unpack_big_int(self.read(4))[0]

    def read_u_int(self):
        return unpack_big_u_int(self.read(4))[0]

    def read_long(self):
        return unpack_big_long(self.read(8))[0]

    def read_u_long(self):
        return unpack_big_u_long(self.read(8))[0]

    def read_half(self):
        return unpack_big_half(self.read(2))[0]

    def read_float(self):
        return unpack_big_float(self.read(4))[0]

    def read_double(self):
        return unpack_big_double(self.read(8))[0]
