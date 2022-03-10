from dataclasses import dataclass
from math import sqrt


kEpsilon = 0.00001


@dataclass
class Vector3:
    X: float = 0.0
    Y: float = 0.0
    Z: float = 0.0

    def __init__(self, *args):
        if len(args) == 3 or len(args) == 1 and isinstance(args[0], (tuple, list)):
            self.X, self.Y, self.Z = args
        elif len(args) == 1:
            # dirty patch for Vector4
            self.__dict__ = args[0].__dict__

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

    def __eq__(self, other):
        if isinstance(other, Vector3):
            return self.X == other.X and self.Y == other.Y and self.Z == other.Z
        else:
            return False

    def normalize(self):
        length = self.length()
        if length > kEpsilon:
            invNorm = 1.0 / length
            self.X *= invNorm
            self.Y *= invNorm
            self.Z *= invNorm
        else:
            X = 0
            Y = 0
            Z = 0

    def Normalize(self):
        self.normalize()

    def length(self):
        return sqrt(self.LengthSquared())

    def Length(self):
        return self.length()

    def LengthSquared(self):
        return self.X ** 2 + self.Y ** 2 + self.Y ** 2

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

    def __div__(a, d):
        return Vector3(a.X / d, a.Y / d, a.Z / d)

    def __eq__(lhs, rhs):
        return (lhs - rhs).LengthSquared() < kEpsilon

    def __ne__(lhs, rhs):
        return not (lhs == rhs)

    def Vector2(self):
        from .Vector2 import Vector2
        return Vector2(self.X, self.Y)

    def Vector4(self):
        from .Vector4 import Vector4
        return Vector4(self.X, self.Y, self.Z, 0.0)
