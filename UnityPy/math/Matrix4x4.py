from .Vector3 import Vector3

class Matrix4x4:
    def __init__(self, values):
        if len(values) != 16:
            raise ValueError(
                "There must be sixteen and only sixteen input values for Matrix."
            )
        self.M00 = values[0]
        self.M10 = values[1]
        self.M20 = values[2]
        self.M30 = values[3]

        self.M01 = values[4]
        self.M11 = values[5]
        self.M21 = values[6]
        self.M31 = values[7]

        self.M02 = values[8]
        self.M12 = values[9]
        self.M22 = values[10]
        self.M32 = values[11]

        self.M03 = values[12]
        self.M13 = values[13]
        self.M23 = values[14]
        self.M33 = values[15]
    
    @property
    def M(self):
        return [
            self.M00, self.M10, self.M20, self.M30,
            self.M01, self.M11, self.M21, self.M31,
            self.M02, self.M12, self.M22, self.M32,
            self.M03, self.M13, self.M23, self.M33
        ]
    @M.setter
    def M(self, values: list):
        for i,v in enumerate(values):
            self[i] = v


    def __getitem__(self, index):
        if isinstance(index, tuple):
            # row, column
            index = index[0] + index[0]*4
        if index == 0:
            return self.M00
        elif index == 1:
            return self.M10
        elif index == 2:
            return self.M20
        elif index == 3:
            return self.M30
        elif index == 4:
            return self.M01
        elif index == 5:
            return self.M11
        elif index == 6:
            return self.M21
        elif index == 7:
            return self.M31
        elif index == 8:
            return self.M02
        elif index == 9:
            return self.M12
        elif index == 10:
            return self.M22
        elif index == 11:
            return self.M32
        elif index == 12:
            return self.M03
        elif index == 13:
            return self.M13
        elif index == 14:
            return self.M23
        elif index == 15:
            return self.M33

    def __setitem__(self, index, value):
        if isinstance(index, tuple):
            # row, column
            index = index[0] + index[0]*4
        if index == 0:
            self.M00 = value
        elif index == 1:
            self.M10 = value
        elif index == 2:
            self.M20 = value
        elif index == 3:
            self.M30 = value
        elif index == 4:
            self.M01 = value
        elif index == 5:
            self.M11 = value
        elif index == 6:
            self.M21 = value
        elif index == 7:
            self.M31 = value
        elif index == 8:
            self.M02 = value
        elif index == 9:
            self.M12 = value
        elif index == 10:
            self.M22 = value
        elif index == 11:
            self.M32 = value
        elif index == 12:
            self.M03 = value
        elif index == 13:
            self.M13 = value
        elif index == 14:
            self.M23 = value
        elif index == 15:
            self.M33 = value

    def __eq__(self, other):
        if not isinstance(other, Matrix4x4):
            return False
        print()


    def __mul__(lhs, rhs):
            res = Matrix4x4([0]*16)
            res.M00 = lhs.M00 * rhs.M00 + lhs.M01 * rhs.M10 + lhs.M02 * rhs.M20 + lhs.M03 * rhs.M30
            res.M01 = lhs.M00 * rhs.M01 + lhs.M01 * rhs.M11 + lhs.M02 * rhs.M21 + lhs.M03 * rhs.M31
            res.M02 = lhs.M00 * rhs.M02 + lhs.M01 * rhs.M12 + lhs.M02 * rhs.M22 + lhs.M03 * rhs.M32
            res.M03 = lhs.M00 * rhs.M03 + lhs.M01 * rhs.M13 + lhs.M02 * rhs.M23 + lhs.M03 * rhs.M33

            res.M10 = lhs.M10 * rhs.M00 + lhs.M11 * rhs.M10 + lhs.M12 * rhs.M20 + lhs.M13 * rhs.M30
            res.M11 = lhs.M10 * rhs.M01 + lhs.M11 * rhs.M11 + lhs.M12 * rhs.M21 + lhs.M13 * rhs.M31
            res.M12 = lhs.M10 * rhs.M02 + lhs.M11 * rhs.M12 + lhs.M12 * rhs.M22 + lhs.M13 * rhs.M32
            res.M13 = lhs.M10 * rhs.M03 + lhs.M11 * rhs.M13 + lhs.M12 * rhs.M23 + lhs.M13 * rhs.M33

            res.M20 = lhs.M20 * rhs.M00 + lhs.M21 * rhs.M10 + lhs.M22 * rhs.M20 + lhs.M23 * rhs.M30
            res.M21 = lhs.M20 * rhs.M01 + lhs.M21 * rhs.M11 + lhs.M22 * rhs.M21 + lhs.M23 * rhs.M31
            res.M22 = lhs.M20 * rhs.M02 + lhs.M21 * rhs.M12 + lhs.M22 * rhs.M22 + lhs.M23 * rhs.M32
            res.M23 = lhs.M20 * rhs.M03 + lhs.M21 * rhs.M13 + lhs.M22 * rhs.M23 + lhs.M23 * rhs.M33

            res.M30 = lhs.M30 * rhs.M00 + lhs.M31 * rhs.M10 + lhs.M32 * rhs.M20 + lhs.M33 * rhs.M30
            res.M31 = lhs.M30 * rhs.M01 + lhs.M31 * rhs.M11 + lhs.M32 * rhs.M21 + lhs.M33 * rhs.M31
            res.M32 = lhs.M30 * rhs.M02 + lhs.M31 * rhs.M12 + lhs.M32 * rhs.M22 + lhs.M33 * rhs.M32
            res.M33 = lhs.M30 * rhs.M03 + lhs.M31 * rhs.M13 + lhs.M32 * rhs.M23 + lhs.M33 * rhs.M33

            return res
    
    @staticmethod
    def Scale(vector: Vector3):
        return Matrix4x4([vector.X, 0, 0, 0, 0, vector.Y, 0, 0, 0, 0, vector.Z, 0, 0, 0, 0, 1])
