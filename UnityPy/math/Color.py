from .Vector4 import Vector4


class Color:
    R: float
    G: float
    B: float
    A: float

    def __init__(self, r: float, g: float, b: float, a: float):
        self.R = r
        self.G = g
        self.B = b
        self.A = a

    def __eq__(self, other):
        if isinstance(other, Color):
            return self.__dict__ == other.__dict__
        else:
            return False

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

    def __div__(self, other):
        if isinstance(other, Color):
            return Color(
                self.R / other.R, self.G / other.G, self.B / other.B, self.A / other.A
            )
        else:
            return Color(self.R / other, self.G / other, self.B / other, self.A / other)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return self.__dict__ != other.__dict__

    def Vector4(self):
        return Vector4(self.R, self.G, self.B, self.A)
