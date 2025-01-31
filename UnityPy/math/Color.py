from .Vector4 import Vector4


class Color:
    R: float
    G: float
    B: float
    A: float

    def __init__(self, r: float = 0.0, g: float = 0.0, b: float = 0.0, a: float = 0.0):
        if not all(isinstance(v, (int, float)) for v in (r, g, b, a)):
            raise TypeError("All components must be numeric.")
        self.R = r
        self.G = g
        self.B = b
        self.A = a

    def __add__(self, other):
        return Color(
            self.R + other.R, self.G + other.G, self.B + other.B, self.A + other.A
        )

    def __sub__(self, other):
        return Color(
            self.R - other.R, self.G - other.G, self.B - other.B, self.A - other.A
        )

    def __mul__(self, other):
        if isinstance(other, Color):
            return Color(
                self.R * other.R, self.G * other.G, self.B * other.B, self.A * other.A
            )
        else:
            return Color(self.R * other, self.G * other, self.B * other, self.A * other)

    def __truediv__(self, other):
        if isinstance(other, Color):
            return Color(
                self.R / other.R, self.G / other.G, self.B / other.B, self.A / other.A
            )
        else:
            return Color(self.R / other, self.G / other, self.B / other, self.A / other)

    def __eq__(self, other):
        if isinstance(other, Color):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not (self == other)

    def Vector4(self):
        return Vector4(self.R, self.G, self.B, self.A)
