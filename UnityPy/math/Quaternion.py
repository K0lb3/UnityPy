from dataclasses import dataclass


@dataclass
class Quaternion:
    X: float
    Y: float
    Z: float
    W: float

    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0, w: float = 1.0):
        if not all(isinstance(v, (int, float)) for v in (x, y, z, w)):
            raise TypeError("All components must be numeric.")
        self.X = float(x)
        self.Y = float(y)
        self.Z = float(z)
        self.W = float(w)

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
