from dataclasses import dataclass
from math import sqrt
from typing import Sequence

kEpsilon = 0.00001


@dataclass
class Vector3:
    """https://github.com/Unity-Technologies/UnityCsReference/blob/master/Runtime/Export/Math/Vector3.cs"""

    X: float = 0.0
    Y: float = 0.0
    Z: float = 0.0

    def __init__(self, *args):
        from .Vector4 import Vector4

        if len(args) == 1:
            args = args[0]

        if isinstance(args, Sequence):
            if len(args) == 3:  # args=(x, y, z)
                self.X, self.Y, self.Z = args
            elif len(args) == 0:  # args=()
                self.X = self.Y = self.Z = 0.0
            else:
                raise TypeError("Invalid argument length for Vector3")
        elif isinstance(args, Vector4):
            # dirty patch for Vector4
            self.X, self.Y, self.Z = args.X, args.Y, args.Z
        else:
            raise TypeError(
                "If only 1 argument passed, it must be a sequence or Vector4"
            )

    def __getitem__(self, index):
        return (self.X, self.Y, self.Z)[index]

    def __setitem__(self, index, value):
        if index == 0:
            self.X = value
        elif index == 1:
            self.Y = value
        elif index == 2:
            self.Z = value
        else:
            raise IndexError("Index out of range")

    def __hash__(self):
        return self.X.__hash__() ^ (self.Y.__hash__() << 2) ^ (self.Z.__hash__() >> 2)

    def normalize(self):
        length = self.length()
        if length > kEpsilon:
            invNorm = 1.0 / length
            self.X *= invNorm
            self.Y *= invNorm
            self.Z *= invNorm
        else:
            self.X = self.Y = self.Z = 0.0

    Normalize = normalize

    def length(self):
        return sqrt(self.lengthSquared())

    Length = length

    def lengthSquared(self):
        return self.X**2 + self.Y**2 + self.Z**2

    LengthSquared = lengthSquared

    @staticmethod
    def Zero():
        return Vector3(0, 0, 0)

    @staticmethod
    def One():
        return Vector3(1, 1, 1)

    def __add__(a, b):
        return Vector3(a.X + b.X, a.Y + b.Y, a.Z + b.Z)

    def __sub__(a, b):
        return Vector3(a.X - b.X, a.Y - b.Y, a.Z - b.Z)

    def __mul__(a, d):
        return Vector3(a.X * d, a.Y * d, a.Z * d)

    def __truediv__(a, d):
        return Vector3(a.X / d, a.Y / d, a.Z / d)

    def __eq__(lhs, rhs):
        if isinstance(rhs, Vector3):
            diff = lhs - rhs
            return diff.lengthSquared() < kEpsilon * kEpsilon
        return False

    def __ne__(lhs, rhs):
        return not (lhs == rhs)

    def Vector2(self):
        from .Vector2 import Vector2

        return Vector2(self.X, self.Y)

    def Vector4(self):
        from .Vector4 import Vector4

        return Vector4(self.X, self.Y, self.Z, 0.0)
