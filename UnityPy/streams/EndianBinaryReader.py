import io
import struct

from ..math import Color, Matrix4x4, Quaternion, Vector2, Vector3, Vector4, Rectangle


class EndianBinaryReader:
    endian: str
    Length: int
    Position: int
    BaseOffset: int

    def __new__(cls, item, endian=">", offset=0):
        if isinstance(item, (bytes, bytearray, memoryview)):
            obj = super(EndianBinaryReader, cls).__new__(
                EndianBinaryReader_Memoryview)
        else:
            obj = super(EndianBinaryReader, cls).__new__(
                EndianBinaryReader_Streamable
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
        return struct.unpack(self.endian + "b", self.read(1))[0]

    def read_u_byte(self) -> int:
        return struct.unpack(self.endian + "B", self.read(1))[0]

    def read_bytes(self, num) -> bytes:
        return self.read(num)

    def read_short(self) -> int:
        return struct.unpack(self.endian + "h", self.read(2))[0]

    def read_int(self) -> int:
        return struct.unpack(self.endian + "i", self.read(4))[0]

    def read_long(self) -> int:
        return struct.unpack(self.endian + "q", self.read(8))[0]

    def read_u_short(self) -> int:
        return struct.unpack(self.endian + "H", self.read(2))[0]

    def read_u_int(self) -> int:
        return struct.unpack(self.endian + "I", self.read(4))[0]

    def read_u_long(self) -> int:
        return struct.unpack(self.endian + "Q", self.read(8))[0]

    def read_float(self) -> float:
        return struct.unpack(self.endian + "f", self.read(4))[0]

    def read_double(self) -> float:
        return struct.unpack(self.endian + "d", self.read(8))[0]

    def read_boolean(self) -> bool:
        return bool(struct.unpack(self.endian + "?", self.read(1))[0])

    def read_string(self, size=None, encoding="utf8") -> str:
        if size is None:
            ret = self.read_string_to_null()
        else:
            ret = struct.unpack(f"{self.endian}{size}is", self.read(size))[0]
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

    def read_aligned_string(self):
        length = self.read_int()
        if 0 < length <= self.Length - self.Position:
            string_data = bytes(self.read_bytes(length))
            result = string_data.decode("utf8", "surrogateescape")
            self.align_stream()
            return result
        return ""

    def align_stream(self, alignment=4):
        self.Position += (alignment - self.Position % alignment) % alignment

    def read_quaternion(self):
        return Quaternion(
            self.read_float(), self.read_float(), self.read_float(), self.read_float()
        )

    def read_vector2(self):
        return Vector2(self.read_float(), self.read_float())

    def read_vector3(self):
        return Vector3(self.read_float(), self.read_float(), self.read_float())

    def read_vector4(self):
        return Vector4(
            self.read_float(), self.read_float(), self.read_float(), self.read_float()
        )

    def read_rectangle_f(self):
        return Rectangle(
            self.read_float(), self.read_float(), self.read_float(), self.read_float()
        )

    def read_color4(self):
        return Color(
            self.read_float(), self.read_float(), self.read_float(), self.read_float()
        )

    def read_byte_array(self):
        return self.read(self.read_int())

    def read_matrix(self):
        return Matrix4x4(self.read_float_array(16))

    def read_array(self, command, length: int):
        return [command() for _ in range(length)]

    def read_boolean_array(self):
        return self.read_array(self.read_boolean, self.read_int())

    def read_u_short_array(self):
        return self.read_array(self.read_u_short, self.read_int())

    def read_int_array(self, length=0):
        return self.read_array(self.read_int, length if length else self.read_int())

    def read_u_int_array(self, length=0):
        return self.read_array(self.read_u_int, length if length else self.read_int())

    def read_u_int_array_array(self, length=0):
        return self.read_array(
            self.read_u_int_array, length if length else self.read_int()
        )

    def read_float_array(self, length=0):
        return self.read_array(self.read_float, length if length else self.read_int())

    def read_string_array(self):
        return self.read_array(self.read_aligned_string, self.read_int())

    def read_vector2_array(self):
        return self.read_array(self.read_vector2, self.read_int())

    def read_vector4_array(self):
        return self.read_array(self.read_vector4, self.read_int())

    def read_matrix_array(self):
        return self.read_array(self.read_matrix, self.read_int())

    def real_offset(self):
        """ Returns offset in the underlying file.
            (Not working with unpacked streams.)
        """
        return self.BaseOffset + self.Position

    def read_the_rest(self, obj_start, obj_size):
        """ Returns the rest of the current reader bytes."""
        return self.read_bytes(obj_size - (self.Position - obj_start))


class EndianBinaryReader_Memoryview(EndianBinaryReader):
    view: memoryview

    def __init__(self, view, endian=">", offset=0):
        super().__init__(view, endian=endian, offset=offset)
        self.view = memoryview(view)
        self.Length = len(view)

    @property
    def bytes(self):
        return self.view

    def dispose(self):
        self.view.release()

    def read(self, length: int):
        if not length:
            return b""
        ret = self.view[self.Position: self.Position + length]
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


class EndianBinaryReader_Streamable(EndianBinaryReader):
    stream: io.BufferedReader

    def __init__(self, stream, endian=">", offset=0):
        self.stream = stream
        self.Length = self.stream.seek(0, 2) - offset
        super().__init__(stream, endian=endian, offset=offset)

    def get_position(self):
        return self.stream.tell()

    def set_position(self, value):
        self.stream.seek(value+self.BaseOffset)

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

    def read(self, length: int):
        if not length:
            return b""
        return self.stream.read(length)

