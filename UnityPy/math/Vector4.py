from dataclasses import dataclass
from math import sqrt
from typing import Sequence

kEpsilon = 0.00001


@dataclass
class Vector4:
    """https://github.com/Unity-Technologies/UnityCsReference/blob/master/Runtime/Export/Math/Vector4.cs"""

    X: float = 0.0
    Y: float = 0.0
    Z: float = 0.0
    W: float = 0.0

    def __init__(self, *args):
        if len(args) == 1:
            args = args[0]

        if isinstance(args, Sequence):
            if len(args) == 4:  # args=(x, y, z, w)
                self.X, self.Y, self.Z, self.W = args
            elif len(args) == 2:  # args=(Vector3, w)
                self.X, self.Y, self.Z = args[0]
                self.W = args[1]
            elif len(args) == 0:  # args=()
                self.X = self.Y = self.Z = self.W = 0.0
            else:
                raise TypeError("Invalid argument length for Vector4")
        else:
            raise TypeError("If only 1 argument passed, it must be a sequence")

    def __getitem__(self, index):
        return (self.X, self.Y, self.Z, self.W)[index]

    def __setitem__(self, index, value):
        if index == 0:
            self.X = value
        elif index == 1:
            self.Y = value
        elif index == 2:
            self.Z = value
        elif index == 3:
            self.W = value
        else:
            raise IndexError("Index out of range")

    def __hash__(self):
        return (
            self.X.__hash__()
            ^ (self.Y.__hash__() << 2)
            ^ (self.Z.__hash__() >> 2)
            ^ (self.W.__hash__() >> 1)
        )

    def normalize(self):
        length = self.length()
        if length > kEpsilon:
            invNorm = 1.0 / length
            self.X *= invNorm
            self.Y *= invNorm
            self.Z *= invNorm
            self.W *= invNorm
        else:
            self.X = self.Y = self.Z = self.W = 0.0

    Normalize = normalize

    def length(self):
        return sqrt(self.lengthSquared())

    Length = length

    def lengthSquared(self):
        return self.X**2 + self.Y**2 + self.Z**2 + self.W**2

    LengthSquared = lengthSquared

    @staticmethod
    def Zero():
        return Vector4(0, 0, 0, 0)

    @staticmethod
    def One():
        return Vector4(1, 1, 1, 1)

    def __add__(a, b):
        return Vector4(a.X + b.X, a.Y + b.Y, a.Z + b.Z, a.W + b.W)

    def __sub__(a, b):
        return Vector4(a.X - b.X, a.Y - b.Y, a.Z - b.Z, a.W - b.W)

    def __mul__(a, d):
        return Vector4(a.X * d, a.Y * d, a.Z * d, a.W * d)

    def __truediv__(a, d):
        return Vector4(a.X / d, a.Y / d, a.Z / d, a.W / d)

    def __eq__(lhs, rhs):
        if isinstance(rhs, Vector4):
            diff = lhs - rhs
            return diff.lengthSquared() < kEpsilon * kEpsilon
        return False

    def __ne__(lhs, rhs):
        return not (lhs == rhs)

    def Vector3(self):
        from .Vector3 import Vector3

        return Vector3(self.X, self.Y, self.Z)
