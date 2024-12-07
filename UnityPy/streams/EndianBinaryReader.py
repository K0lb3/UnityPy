from __future__ import annotations

import re
from abc import ABC, ABCMeta, abstractmethod
from io import BytesIO, IOBase
from struct import Struct, unpack
from typing import BinaryIO, List, Optional, Union

from ._defines import TYPE_PARAM_SIZE_LIST, Endianess

reNot0 = re.compile(b"(.*?)\x00", re.S)


class EndianBinaryReader(ABC, metaclass=ABCMeta):
    endian: Endianess
    Length: int
    Position: int
    BaseOffset: int

    def __new__(
        cls,
        item: Union[bytes, bytearray, memoryview, BytesIO, str, IOBase],
        endian: Endianess = ">",
        offset: int = 0,
    ):
        """
        Creates a new instance of EndianBinaryReader, choosing the appropriate subclass based on the type of the input.

        Args:
            item: The data source (bytes, memoryview, file path, or stream).
            endian: Endianness to use for reading data ('>' for big-endian, '<' for little-endian).
            offset: Initial offset to set for reading.

        Returns:
            An instance of either EndianBinaryReader_Memoryview or EndianBinaryReader_Streamable.

        Raises:
            ValueError: If the provided `item` type is unsupported.
        """
        if isinstance(item, (bytes, bytearray, memoryview)):
            # Handle in-memory binary data
            obj = super().__new__(EndianBinaryReader_Memoryview)
        elif isinstance(item, IOBase):  # Includes BufferedIOBase
            # Handle stream-like objects
            obj = super().__new__(EndianBinaryReader_Streamable)
        elif isinstance(item, str):
            # Handle file paths as input
            try:
                item = open(item, "rb")
                obj = super().__new__(EndianBinaryReader_Streamable)
            except FileNotFoundError as e:
                raise ValueError(f"File not found: {item}") from e
        elif isinstance(item, EndianBinaryReader):
            # Wrap another EndianBinaryReader instance
            new_item = (
                item.stream
                if isinstance(item, EndianBinaryReader_Streamable)
                else item.view
            )
            return cls(new_item, endian, offset)
        elif hasattr(item, "read"):
            # Handle generic objects with a `read` method
            if hasattr(item, "seek"):
                obj = super().__new__(EndianBinaryReader_Streamable)
            else:
                item = item.read()
                obj = super().__new__(EndianBinaryReader_Memoryview)
        else:
            raise ValueError(f"Unsupported input type: {type(item).__name__}")

        # Initialize the chosen subclass
        obj.__init__(item, endian)
        return obj

    def __init__(self, item, endian=">", offset=0):
        self.endian = endian
        self.BaseOffset = offset
        self.Position = 0

    def seek(self, offset: int, whence: int = 0) -> int:
        if whence == 0:
            self.Position = offset
        elif whence == 1:
            self.Position += offset
        elif whence == 2:
            self.Position = self.Length + offset
        else:
            raise ValueError("Invalid whence")
        return self.Position

    def tell(self) -> int:
        return self.Position

    def get_bytes(self) -> bytes:
        return self.bytes

    @abstractmethod
    def create_sub_reader(self, offset: int, length: int) -> EndianBinaryReader:
        pass

    @property
    def bytes(self):
        raise NotImplementedError(f"{self.__class__.__name__}.read not implemented!")

    def read(self, *args):
        raise NotImplementedError(f"{self.__class__.__name__}.read not implemented!")

    def read_byte(self) -> int:
        return unpack(self.endian + "b", self.read(1))[0]

    def read_u_byte(self) -> int:
        return unpack(self.endian + "B", self.read(1))[0]

    def read_bytes(self, num) -> bytes:
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

    def read_string_to_null(self, max_length=32767) -> str:
        ret = []
        c = b""
        while c != b"\0" and len(ret) < max_length and self.Position != self.Length:
            ret.append(c)
            c = self.read(1)
            if not c:
                raise ValueError("Unterminated string: %r" % ret)
        return b"".join(ret).decode("utf8", "surrogateescape")

    def read_string(self, size: Optional[int] = None, encoding: str = "utf8") -> str:
        length = size if size is not None else self.read_int()
        if 0 < length <= self.Length - self.Position:
            string_data = bytes(self.read_bytes(length))
            result = string_data.decode(encoding, "surrogateescape")
            return result
        return ""

    def read_aligned_string(self) -> str:
        ret = self.read_string()
        self.align_stream()
        return ret

    def align_stream(self, alignment=4):
        self.Position += (alignment - self.Position % alignment) % alignment
        return self.Position

    def read_byte_array(self) -> bytes:
        return self.read(self.read_int())

    def read_array(self, command, length: int) -> list:
        return [command() for _ in range(length)]

    def read_array_struct(self, param: str, length: int = None) -> list:
        if length is None:
            length = self.read_int()
        struct = Struct(f"{self.endian}{length}{param}")
        return struct.unpack(self.read(struct.size))

    def read_boolean_array(self, length: int = None) -> List[bool]:
        return self.read_array_struct("?", length)

    def read_u_byte_array(self, length: int = None) -> List[int]:
        return self.read_array_struct("B", length)

    def read_u_short_array(self, length: int = None) -> List[int]:
        return self.read_array_struct("h", length)

    def read_short_array(self, length: int = None) -> List[int]:
        return self.read_array_struct("H", length)

    def read_int_array(self, length: int = None) -> List[int]:
        return self.read_array_struct("i", length)

    def read_u_int_array(self, length: int = None) -> List[int]:
        return self.read_array_struct("I", length)

    def read_long_array(self, length: int = None) -> List[int]:
        return self.read_array_struct("q", length)

    def read_u_long_array(self, length: int = None) -> List[int]:
        return self.read_array_struct("Q", length)

    def read_float_array(self, length: int = None) -> List[float]:
        return self.read_array_struct("f", length)

    def read_double_array(self, length: int = None) -> List[float]:
        return self.read_array_struct("d", length)

    def real_offset(self) -> int:
        """Returns offset in the underlying file.
        (Not working with unpacked streams.)
        """
        return self.BaseOffset + self.Position

    def read_the_rest(self, obj_start: int, obj_size: int) -> bytes:
        """Returns the rest of the current reader bytes."""
        return self.read_bytes(obj_size - (self.Position - obj_start))

    def unpack_array(self, string: str, count: int) -> list:
        struct = Struct(f"{self.endian}{string}")
        return list(struct.iter_unpack(self.read(count * struct.size)))


class EndianBinaryReader_Memoryview(EndianBinaryReader):
    __slots__ = ("view", "_endian", "BaseOffset", "Position", "Length")
    view: memoryview

    def __init__(self, view, endian=">", offset=0):
        self._endian = ""
        super().__init__(view, endian=endian, offset=offset)
        self.view = memoryview(view)
        self.Length = len(view)

    @property
    def endian(self):
        return self._endian

    @endian.setter
    def endian(self, value):
        if value not in ("<", ">"):
            raise ValueError("Invalid endian")
        if value != self._endian:
            for typ, _, _ in TYPE_PARAM_SIZE_LIST:
                func_name_e = f"read_{value}_{typ}"
                func_name = f"read_{typ}"
                setattr(self, func_name, getattr(self, func_name_e))
            self._endian = value

    @property
    def bytes(self):
        return self.view

    def dispose(self):
        self.view.release()

    def read(self, length: int):
        if not length:
            return b""
        ret = self.view[self.Position : self.Position + length]
        self.Position += length
        return ret

    def read_aligned_string(self):
        length = self.read_int()
        if 0 < length <= self.Length - self.Position:
            string_data = self.read_bytes(length)
            result = bytes(string_data).decode("utf8", "surrogateescape")
            self.align_stream()
            return result
        return ""

    def read_string_to_null(self, max_length=32767) -> str:
        match = reNot0.search(self.view, self.Position, self.Position + max_length)
        if not match:
            if self.Position + max_length >= self.Length:
                raise Exception("String not terminated")
            else:
                return bytes(self.read_bytes(max_length)).decode(
                    "utf8", "surrogateescape"
                )
        ret = match[1].decode("utf8", "surrogateescape")
        self.Position = match.end()
        return ret

    def create_sub_reader(self, offset: int, length: int) -> EndianBinaryReader:
        return EndianBinaryReader_Memoryview(
            self.view, self.endian, self.BaseOffset + offset
        )


class EndianBinaryReader_Streamable(EndianBinaryReader):
    __slots__ = ("stream", "_endian", "BaseOffset")
    stream: BinaryIO

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
            for typ, _, _ in TYPE_PARAM_SIZE_LIST:
                func_name_e = f"read_{value}_{typ}"
                func_name = f"read_{typ}"
                setattr(self, func_name, getattr(self, func_name_e))
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

    def create_sub_reader(self, offset: int, length: int) -> EndianBinaryReader:
        return EndianBinaryReader_Streamable(self.stream, self.endian, offset)


# generate endianed functions
for endian_s in Endianess.__args__:
    for typ, param, _ in TYPE_PARAM_SIZE_LIST:

        def generate_funcs():
            func_name = f"read_{endian_s}_{typ}"
            struct = Struct(f"{endian_s}{param}")

            def mv_func(self: EndianBinaryReader_Memoryview):
                value = struct.unpack_from(self.view, self.Position)[0]
                self.Position += struct.size
                return value

            def st_func(self: EndianBinaryReader_Streamable):
                return struct.unpack(self.stream)[0]

            setattr(EndianBinaryReader_Memoryview, func_name, mv_func)
            setattr(EndianBinaryReader_Streamable, func_name, st_func)

        generate_funcs()
