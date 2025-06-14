from __future__ import annotations

import builtins
import re
import sys
from io import BufferedReader, IOBase
from struct import Struct, unpack
from types import MethodType
from typing import Any, Callable, ClassVar, Dict, List, Literal, Optional, Tuple, Union

reNot0 = re.compile(b"(.*?)\x00", re.S)

SYS_ENDIAN = "<" if sys.byteorder == "little" else ">"
Endianess = Literal["<", ">"]

# generate unpack and unpack_from functions
TYPE_PARAM_SIZE_LIST = [
    ("short", "h"),
    ("u_short", "H"),
    ("int", "i"),
    ("u_int", "I"),
    ("long", "q"),
    ("u_long", "Q"),
    ("half", "e"),
    ("float", "f"),
    ("double", "d"),
]

MEMORY_FUNCTIONS: Dict[Endianess, Dict[str, Callable[["EndianBinaryReader_Memoryview"], Any]]] = {"<": {}, ">": {}}
STREAM_FUNCTIONS: Dict[Endianess, Dict[str, Callable[["EndianBinaryReader_Streamable"], Any]]] = {"<": {}, ">": {}}


class EndianBinaryReader:
    Length: int
    Position: int
    BaseOffset: int
    _endian: Endianess
    _function_map: ClassVar[Dict[Endianess, Dict[str, Callable]]]

    def __new__(
        cls,
        item: Union[bytes, bytearray, memoryview, IOBase, str],
        endian: Endianess = ">",
        offset: int = 0,
    ):
        if isinstance(item, (bytes, bytearray, memoryview)):
            obj = super(EndianBinaryReader, cls).__new__(EndianBinaryReader_Memoryview)  # type: ignore
        elif isinstance(item, IOBase):
            obj = super(EndianBinaryReader, cls).__new__(EndianBinaryReader_Streamable)  # type: ignore
        elif isinstance(item, str):
            obj = super(EndianBinaryReader, cls).__new__(EndianBinaryReader_Streamable_LocalFile)  # type: ignore
        elif isinstance(item, EndianBinaryReader):
            item = item.stream if isinstance(item, EndianBinaryReader_Streamable) else item.view
            return EndianBinaryReader(item, endian, offset)
        elif hasattr(item, "read"):
            if hasattr(item, "seek") and hasattr(item, "tell"):
                obj = super(EndianBinaryReader, cls).__new__(EndianBinaryReader_Streamable)
            else:
                item = item.read()
                obj = super(EndianBinaryReader, cls).__new__(EndianBinaryReader_Memoryview)
        else:
            raise TypeError("Unsupported type for EndianBinaryReader: %s" % type(item))
        return obj

    def __init__(self, item, endian: Endianess = ">", offset: int = 0):
        self._endian = ""  # type: ignore
        self.endian = endian
        self.BaseOffset = offset
        self.Position = 0

    @property
    def endian(self) -> Endianess:
        return self._endian

    @endian.setter
    def endian(self, value: Endianess):
        if value not in ("<", ">"):
            raise ValueError("Invalid endian")
        if value != self._endian:
            for func_name, func in self._function_map[value].items():
                setattr(self, func_name, MethodType(func, self))
            self._endian = value

    @property
    def bytes(self) -> builtins.bytes:
        # implemented by Streamable and Memoryview versions
        return b""

    def read(self, size: Optional[int] = -1, /) -> builtins.bytes:
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

    def read_string(self, size: Optional[int] = None) -> str:
        if size is None:
            return self.read_string_to_null()
        else:
            raw = self.read_bytes(size)
            return raw.decode("utf8", "surrogateescape")

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
    _endian: Endianess
    view: memoryview
    _function_map = MEMORY_FUNCTIONS

    def __init__(self, view, endian: Endianess = ">", offset: int = 0):
        super().__init__(view, endian=endian, offset=offset)
        self.view = memoryview(view)
        self.Length = len(view)

    @property
    def bytes(self):
        return self.view.tobytes()

    def dispose(self) -> None:
        self.view.release()

    def read(self, size: Optional[int] = -1, /):
        if not size:
            return b""
        if size == -1:
            size = self.Length - self.Position
        ret = self.view[self.Position : self.Position + size]
        self.Position += size
        return ret.tobytes()

    def read_array_struct(self, param: str, length: Optional[int] = None) -> tuple:
        if length is None:
            length = self.read_int()
        struct = Struct(f"{self.endian}{length}{param}")
        value = struct.unpack_from(self.view, self.Position)
        self.Position += struct.size
        return value

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


class EndianBinaryReader_Streamable(EndianBinaryReader):
    __slots__ = ("stream", "_endian", "BaseOffset")
    stream: BufferedReader
    _function_map = STREAM_FUNCTIONS

    def __init__(self, stream: BufferedReader, endian: Endianess = ">", offset: int = 0):
        self.stream = stream
        super().__init__(stream, endian=endian, offset=offset)
        self.read = self.stream.read

    @property
    def Position(self) -> int:
        return self.stream.tell() - self.BaseOffset

    @Position.setter
    def Position(self, value: int):
        if value < 0:
            raise ValueError("Position cannot be negative")
        self.stream.seek(value + self.BaseOffset)

    @property
    def Length(self):  # type: ignore
        pos = self.Position
        length = self.stream.seek(0, 2) - self.BaseOffset
        self.Position = pos
        return length

    @property
    def bytes(self):
        last_pos = self.Position
        self.Position = 0
        ret = self.read(self.Length)
        self.Position = last_pos  # type: ignore
        return ret

    def dispose(self):
        self.stream.close()
        pass


class EndianBinaryReader_Streamable_LocalFile(EndianBinaryReader_Streamable):
    def __init__(self, path: str, endian: Endianess = ">", offset: int = 0):
        super().__init__(open(path, "rb"), endian=endian, offset=offset)

    def __del__(self):
        self.stream.close()


for endian_s in ("<", ">"):
    for reader_type_name, struct_type_char in TYPE_PARAM_SIZE_LIST:
        func_name = f"read_{reader_type_name}"
        struct = Struct(f"{endian_s}{struct_type_char}")

        def memory_read_func(self: EndianBinaryReader_Memoryview, /, struct=struct):
            value = struct.unpack_from(self.view, self.Position)[0]
            self.Position += struct.size
            return value

        def stream_read_func(self: EndianBinaryReader_Streamable, /, struct=struct):
            return struct.unpack(self.stream.read(struct.size))[0]

        MEMORY_FUNCTIONS[endian_s][func_name] = memory_read_func
        STREAM_FUNCTIONS[endian_s][func_name] = stream_read_func
