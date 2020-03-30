import io
import struct

from ..math import Color, Matrix4x4, Quaternion, Vector2, Vector3, Vector4, Rectangle


class EndianBinaryReader:
    endian: str
    Length: int
    Position: int
    stream: io.BufferedReader

    def __init__(self, input_, endian=">"):
        if isinstance(input_, (bytes, bytearray)):
            self.stream = io.BytesIO(input_)
        elif isinstance(input_, (io.BytesIO, io.BufferedReader)):
            self.stream = input_
        else:
            # test if input is a streamable object
            try:
                p = input_.tell()
                input_.read(1)
                input_.seek(p)
                assert p == input_.tell()
                self.stream = input_
            except:
                raise ValueError("Invalid input type - %s." % type(input_))

        self.endian = endian
        self.Length = self.stream.seek(0, 2)
        self.Position = 0

    def get_position(self):
        return self.stream.tell()

    def set_position(self, value):
        self.stream.seek(value)

    Position = property(get_position, set_position)

    @property
    def bytes(self):
        last_pos = self.Position
        self.Position = 0
        ret = self.read()
        self.Position = last_pos
        return ret

    def __add__(self, value):
        if isinstance(value, (bytes, bytearray)):
            old_pos = self.Position
            self.Position = self.Length
            self.stream.write(value)
            self.Length += len(value)
            self.Position = old_pos
        else:
            raise ValueError("Invalid Input")

    def dispose(self):
        self.stream.close()
        pass

    def read(self, *args):
        return self.stream.read(*args)

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

    def read_string(self, size=None, encoding="utf-8") -> str:
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
        return b"".join(ret).decode("utf8", "replace")

    def read_aligned_string(self):
        length = self.read_int()
        if 0 < length <= self.Length - self.Position:
            string_data = self.read_bytes(length)
            result = string_data.decode("utf8", "backslashreplace")
            self.align_stream(4)
            return result
        return ""

    def align_stream(self, alignment=4):
        pos = self.Position
        mod = pos % alignment
        if mod != 0:
            self.Position += alignment - mod

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

    def read_matrix(self):
        return Matrix4x4(self.read_float_array(16))

    def read_array(self, command, length: int):
        return [command() for i in range(length)]

    def read_boolean_array(self):
        return self.read_array(self.read_boolean, self.read_int())

    def read_u_short_array(self):
        return self.read_array(self.read_u_short, self.read_int())

    def read_int_array(self, length=0):
        return self.read_array(self.read_int, length if length else self.read_int())

    def read_u_int_array(self, length=0):
        return self.read_array(self.read_u_int, length if length else self.read_int())

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

    def read_u_int_array_array(self):
        return self.read_array(self.read_u_int_array, self.read_int())
