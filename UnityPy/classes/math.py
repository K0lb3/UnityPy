"""
Definitions for math related classes.
As most calculations involving them are done in numpy,
we define them here as subtypes of np.ndarray, so that casting won't be necessary.
"""

from attrs import define


@define(slots=True)
class Vector2f:
    x: float = 0
    y: float = 0

    def __repr__(self) -> str:
        return f"Vector2f({self.x}, {self.y})"


@define(slots=True)
class Vector3f:
    x: float = 0
    y: float = 0
    z: float = 0

    def __repr__(self) -> str:
        return f"Vector3f({self.x}, {self.y}, {self.z})"


@define(slots=True)
class Vector4f:
    x: float = 0
    y: float = 0
    z: float = 0
    w: float = 0

    def __repr__(self) -> str:
        return f"Vector4f({self.x}, {self.y}, {self.z}, {self.w})"


float3 = Vector3f
float4 = Vector4f


class Quaternionf(Vector4f):
    # TODO: Implement quaternion operations
    def __repr__(self) -> str:
        return f"Quaternion({self.x}, {self.y}, {self.z}, {self.w})"


@define(slots=True)
class Matrix3x4f:
    e00: float
    e01: float
    e02: float
    e03: float
    e10: float
    e11: float
    e12: float
    e13: float
    e20: float
    e21: float
    e22: float
    e23: float


@define(slots=True)
class Matrix4x4f:
    e00: float
    e01: float
    e02: float
    e03: float
    e10: float
    e11: float
    e12: float
    e13: float
    e20: float
    e21: float
    e22: float
    e23: float
    e30: float
    e31: float
    e32: float
    e33: float


@define(slots=True)
class ColorRGBA:
    r: float = 0
    g: float = 0
    b: float = 0
    a: float = 1

    def __new__(
        cls, r: float = 0, g: float = 0, b: float = 0, a: float = 1, rgba: int = -1
    ) -> "ColorRGBA":
        obj = super().__new__(cls)
        if rgba != -1:
            r = ((rgba >> 24) & 0xFF) / 255
            g = ((rgba >> 16) & 0xFF) / 255
            b = ((rgba >> 8) & 0xFF) / 255
            a = (rgba & 0xFF) / 255
        obj.__init__(r, g, b, a)
        return obj

    @property
    def rgba(self) -> int:
        return (
            self.r * 255 << 24 | self.g * 255 << 16 | self.b * 255 << 8 | self.a * 255
        )

    @rgba.setter
    def rgba(self, value: int):
        self.r = ((value >> 24) & 0xFF) / 255
        self.g = ((value >> 16) & 0xFF) / 255
        self.b = ((value >> 8) & 0xFF) / 255
        self.a = (value & 0xFF) / 255


__all__ = (
    "Vector2f",
    "Vector3f",
    "Vector4f",
    "Quaternionf",
    "Matrix3x4f",
    "Matrix4x4f",
    "ColorRGBA",
    "float3",
    "float4",
)
