from enum import IntEnum


class VertexChannelFormat(IntEnum):
    kChannelFormatFloat = 0
    kChannelFormatFloat16 = 1
    kChannelFormatColor = 2
    kChannelFormatByte = 3
    kChannelFormatUInt32 = 4


class VertexFormat2017(IntEnum):
    kVertexFormatFloat = 0
    kVertexFormatFloat16 = 1
    kVertexFormatColor = 2
    kVertexFormatUNorm8 = 3
    kVertexFormatSNorm8 = 4
    kVertexFormatUNorm16 = 5
    kVertexFormatSNorm16 = 6
    kVertexFormatUInt8 = 7
    kVertexFormatSInt8 = 8
    kVertexFormatUInt16 = 9
    kVertexFormatSInt16 = 10
    kVertexFormatUInt32 = 11
    kVertexFormatSInt32 = 12


class VertexFormat(IntEnum):
    kVertexFormatFloat = 0
    kVertexFormatFloat16 = 1
    kVertexFormatUNorm8 = 2
    kVertexFormatSNorm8 = 3
    kVertexFormatUNorm16 = 4
    kVertexFormatSNorm16 = 5
    kVertexFormatUInt8 = 6
    kVertexFormatSInt8 = 7
    kVertexFormatUInt16 = 8
    kVertexFormatSInt16 = 9
    kVertexFormatUInt32 = 10
    kVertexFormatSInt32 = 11


VERTEX_CHANNEL_FORMAT_STRUCT_TYPE_MAP = {
    VertexChannelFormat.kChannelFormatFloat: "f",
    VertexChannelFormat.kChannelFormatFloat16: "e",
    VertexChannelFormat.kChannelFormatColor: "B",
    VertexChannelFormat.kChannelFormatByte: "B",
    VertexChannelFormat.kChannelFormatUInt32: "I",
}

VERTEX_FORMAT_2017_STRUCT_TYPE_MAP = {
    VertexFormat2017.kVertexFormatFloat: "f",
    VertexFormat2017.kVertexFormatFloat16: "h",
    VertexFormat2017.kVertexFormatColor: "B",
    VertexFormat2017.kVertexFormatUNorm8: "B",
    VertexFormat2017.kVertexFormatSNorm8: "b",
    VertexFormat2017.kVertexFormatUNorm16: "H",
    VertexFormat2017.kVertexFormatSNorm16: "h",
    VertexFormat2017.kVertexFormatUInt8: "B",
    VertexFormat2017.kVertexFormatSInt8: "b",
    VertexFormat2017.kVertexFormatUInt16: "H",
    VertexFormat2017.kVertexFormatSInt16: "h",
    VertexFormat2017.kVertexFormatUInt32: "I",
    VertexFormat2017.kVertexFormatSInt32: "i",
}

VERTEX_FORMAT_STRUCT_TYPE_MAP = {
    VertexFormat.kVertexFormatFloat: "f",
    VertexFormat.kVertexFormatFloat16: "h",
    VertexFormat.kVertexFormatUNorm8: "B",
    VertexFormat.kVertexFormatSNorm8: "b",
    VertexFormat.kVertexFormatUNorm16: "H",
    VertexFormat.kVertexFormatSNorm16: "h",
    VertexFormat.kVertexFormatUInt8: "B",
    VertexFormat.kVertexFormatSInt8: "b",
    VertexFormat.kVertexFormatUInt16: "H",
    VertexFormat.kVertexFormatSInt16: "h",
    VertexFormat.kVertexFormatUInt32: "I",
    VertexFormat.kVertexFormatSInt32: "i",
}
