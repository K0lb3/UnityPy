from enum import IntEnum


class MeshTopology(IntEnum):
    Triangles = 0
    TriangleStrip = 1  # deprecated
    Quads = 2
    Lines = 3
    LineStrip = 4
    Points = 5
