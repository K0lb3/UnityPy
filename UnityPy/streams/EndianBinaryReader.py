import sys
from struct import Struct, unpack
import re
from typing import List, Union
from io import BytesIO, BufferedIOBase, IOBase, BufferedReader

reNot0 = re.compile(b"(.*?)\x00", re.S)

SYS_ENDIAN = "<" if sys.byteorder == "little" else ">"

from ..math import Color, Matrix4x4, Quaternion, Vector2, Vector3, Vector4, Rectangle

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
    ("vector2", "2f", 8),
    ("vector3", "3f", 12),
    ("vector4", "4f", 16),
]

LOCALS = locals()
for endian_s, endian_l in (("<", "little"), (">", "big")):
    for typ, param, _ in TYPE_PARAM_SIZE_LIST:
        LOCALS[f"unpack_{endian_l}_{typ}"] = Struct(f"{endian_s}{param}").unpack
        LOCALS[f"unpack_{endian_l}_{typ}_from"] = Struct(
            f"{endian_s}{param}"
        ).unpack_from


class EndianBinaryReader:
    endian: str
    Length: int
    Position: int
    BaseOffset: int

    def __new__(
        cls,
        item: Union[bytes, bytearray, memoryview, BytesIO, str],
        endian: str = ">",
        offset: int = 0,
    ):
        if isinstance(item, (bytes, bytearray, memoryview)):
            obj = super(EndianBinaryReader, cls).__new__(EndianBinaryReader_Memoryview)
        elif isinstance(item, (IOBase, BufferedIOBase)):
            obj = super(EndianBinaryReader, cls).__new__(EndianBinaryReader_Streamable)
        elif isinstance(item, str):
            item = open(item, "rb")
            obj = super(EndianBinaryReader, cls).__new__(EndianBinaryReader_Streamable)
        elif isinstance(item, EndianBinaryReader):
            item = (
                item.stream
                if isinstance(item, EndianBinaryReader_Streamable)
                else item.view
            )
            return EndianBinaryReader(item, endian, offset)
        elif hasattr(item, "read"):
            if hasattr(item, "seek") and hasattr(item, "tell"):
                obj = super(EndianBinaryReader, cls).__new__(
                    EndianBinaryReader_Streamable
                )
            else:
                item = item.read()
                obj = super(EndianBinaryReader, cls).__new__(
                    EndianBinaryReader_Memoryview
                )

        obj.__init__(item, endian)
        return obj

    def __init__(self, item, endian=">", offset=0):
        self.endian = endian
        self.BaseOffset = offset
        self.Position = 0

    @property
    def bytes(self):
        # implemented by Streamable and Memoryview versions
        return b""

    def read(self, *args):
        # implemented by Streamable and Memoryview versions
        return b""

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

    def read_string(self, size=None, encoding="utf8") -> str:
        if size is None:
            ret = self.read_string_to_null()
        else:
            ret = unpack(f"{self.endian}{size}is", self.read(size))[0]
        try:
            return ret.decode(encoding)
        except UnicodeDecodeError:
            return ret

    def read_string_to_null(self, max_length=32767) -> str:
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

    def read_quaternion(self) -> Quaternion:
        return Quaternion(
            self.read_float(), self.read_float(), self.read_float(), self.read_float()
        )

    def read_vector2(self) -> Vector2:
        return Vector2(self.read_float(), self.read_float())

    def read_vector3(self) -> Vector3:
        return Vector3(self.read_float(), self.read_float(), self.read_float())

    def read_vector4(self) -> Vector4:
        return Vector4(
            self.read_float(), self.read_float(), self.read_float(), self.read_float()
        )

    def read_rectangle_f(self) -> Rectangle:
        return Rectangle(
            self.read_float(), self.read_float(), self.read_float(), self.read_float()
        )

    def read_color_uint(self):
        r = self.read_u_byte()
        g = self.read_u_byte()
        b = self.read_u_byte()
        a = self.read_u_byte()

        return Color(r / 255.0, g / 255.0, b / 255.0, a / 255.0)

    def read_color4(self) -> Color:
        return Color(
            self.read_float(), self.read_float(), self.read_float(), self.read_float()
        )

    def read_byte_array(self) -> bytes:
        return self.read(self.read_int())

    def read_matrix(self) -> Matrix4x4:
        return Matrix4x4(self.read_float_array(16))

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

    def read_u_int_array_array(self, length: int = None) -> List[List[int]]:
        return self.read_array(
            self.read_u_int_array, length if length is not None else self.read_int()
        )

    def read_float_array(self, length: int = None) -> List[float]:
        return self.read_array_struct("f", length)

    def read_double_array(self, length: int = None) -> List[float]:
        return self.read_array_struct("d", length)

    def read_string_array(self) -> List[str]:
        return self.read_array(self.read_aligned_string, self.read_int())

    def read_vector2_array(self) -> List[Vector2]:
        return self.read_array(self.read_vector2, self.read_int())

    def read_vector4_array(self) -> List[Vector4]:
        return self.read_array(self.read_vector4, self.read_int())

    def read_matrix_array(self) -> List[Matrix4x4]:
        return self.read_array(self.read_matrix, self.read_int())

    def real_offset(self) -> int:
        """Returns offset in the underlying file.
        (Not working with unpacked streams.)
        """
        return self.BaseOffset + self.Position

    def read_the_rest(self, obj_start: int, obj_size: int) -> bytes:
        """Returns the rest of the current reader bytes."""
        return self.read_bytes(obj_size - (self.Position - obj_start))


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
    def endian(self, value: str):
        if value not in ("<", ">"):
            raise ValueError("Invalid endian")
        if value != self._endian:
            setattr(
                self,
                "__class__",
                EndianBinaryReader_Memoryview_LittleEndian
                if value == "<"
                else EndianBinaryReader_Memoryview_BigEndian,
            )
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

    def read_vector2(self):
        (x, y) = unpack_little_vector2_from(self.view, self.Position)
        self.Position += 8
        return Vector2(x, y)

    def read_vector3(self):
        (x, y, z) = unpack_little_vector3_from(self.view, self.Position)
        self.Position += 12
        return Vector3(x, y, z)

    def read_vector4(self):
        (x, y, z, w) = unpack_little_vector4_from(self.view, self.Position)
        self.Position += 16
        return Vector4(x, y, z, w)


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

    def read_vector2(self):
        (x, y) = unpack_big_vector2_from(self.view, self.Position)
        self.Position += 8
        return Vector2(x, y)

    def read_vector3(self):
        (x, y, z) = unpack_big_vector3_from(self.view, self.Position)
        self.Position += 12
        return Vector3(x, y, z)

    def read_vector4(self):
        (x, y, z, w) = unpack_big_vector4_from(self.view, self.Position)
        self.Position += 16
        return Vector4(x, y, z, w)


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
            setattr(
                self,
                "__class__",
                EndianBinaryReader_Streamable_LittleEndian
                if value == "<"
                else EndianBinaryReader_Streamable_BigEndian,
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

    def read_vector2(self):
        return Vector2(*unpack_little_vector2(self.read(8)))

    def read_vector3(self):
        return Vector3(*unpack_little_vector3(self.read(12)))

    def read_vector4(self):
        return Vector4(*unpack_little_vector4(self.read(16)))


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

    def read_vector2(self):
        return Vector2(*unpack_big_vector2(self.read(8)))

    def read_vector3(self):
        return Vector3(*unpack_big_vector3(self.read(12)))

    def read_vector4(self):
        return Vector4(*unpack_big_vector4(self.read(16)))
