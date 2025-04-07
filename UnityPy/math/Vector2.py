from dataclasses import dataclass
from math import sqrt

kEpsilon = 0.00001


@dataclass
class Vector2:
    """https://github.com/Unity-Technologies/UnityCsReference/blob/master/Runtime/Export/Math/Vector2.cs"""

    X: float = 0.0
    Y: float = 0.0

    def __init__(self, x: float = 0.0, y: float = 0.0):
        if not all(isinstance(v, (int, float)) for v in (x, y)):
            raise TypeError("All components must be numeric.")
        self.X = float(x)
        self.Y = float(y)

    def __getitem__(self, index):
        return (self.X, self.Y)[index]

    def __setitem__(self, index, value):
        if index == 0:
            self.X = value
        elif index == 1:
            self.Y = value
        else:
            raise IndexError("Index out of range")

    def __hash__(self):
        return self.X.__hash__() ^ (self.Y.__hash__() << 2)

    def normalize(self):
        length = self.length()
        if length > kEpsilon:
            invNorm = 1.0 / length
            self.X *= invNorm
            self.Y *= invNorm
        else:
            self.X = self.Y = 0.0

    Normalize = normalize

    def length(self):
        return sqrt(self.lengthSquared())

    Length = length

    def lengthSquared(self):
        return self.X**2 + self.Y**2

    LengthSquared = lengthSquared

    @staticmethod
    def Zero():
        return Vector2(0, 0)

    @staticmethod
    def One():
        return Vector2(1, 1)

    def __add__(a, b):
        return Vector2(a.X + b.X, a.Y + b.Y)

    def __sub__(a, b):
        return Vector2(a.X - b.X, a.Y - b.Y)

    def __mul__(a, d):
        return Vector2(a.X * d, a.Y * d)

    def __truediv__(a, d):
        return Vector2(a.X / d, a.Y / d)

    def __eq__(lhs, rhs):
        if isinstance(rhs, Vector2):
            diff = lhs - rhs
            return diff.lengthSquared() < kEpsilon * kEpsilon
        return False

    def __ne__(lhs, rhs):
        return not (lhs == rhs)
