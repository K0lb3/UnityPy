class Quaternion:
    X: float
    Y: float
    Z: float
    W: float
    
    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0, w: float = 0.0):
        self._data = [0.0] * 4
        self.X = x
        self.Y = y
        self.Z = z
        self.W = w
    
    @property
    def X(self) -> float:
        return self._data[0]
    
    @X.setter
    def X(self, value: float):
        self._data[0] = value
    
    @property
    def Y(self) -> float:
        return self._data[1]
    
    @Y.setter
    def Y(self, value: float):
        self._data[1] = value
    
    @property
    def Z(self) -> float:
        return self._data[2]
    
    @Z.setter
    def Z(self, value: float):
        self._data[2] = value
    
    @property
    def W(self) -> float:
        return self._data[3]
    
    @W.setter
    def W(self, value: float):
        self._data[3] = value
    
    def __getitem__(self, value):
        return self._data[value]
    
    def __setitem__(self, index, value):
        self._data[index] = value
