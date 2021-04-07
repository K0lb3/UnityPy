from enum import IntEnum


class GfxPrimitiveType(IntEnum):
    kPrimitiveTriangles = 0
    kPrimitiveTriangleStrip = 1
    kPrimitiveQuads = 2
    kPrimitiveLines = 3
    kPrimitiveLineStrip = 4
    kPrimitivePoints = 5