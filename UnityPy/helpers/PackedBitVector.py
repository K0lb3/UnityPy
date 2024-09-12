from typing import Optional, List, TYPE_CHECKING, Tuple

# from ..objects.math import Quaternionf
if TYPE_CHECKING:
    from ..classes.generated import PackedBitVector


def reshape(data: list, shape: Optional[Tuple[int, ...]] = None) -> list:
    if shape is None:
        return data
    if len(shape) == 1:
        m = shape[0]
        return [data[i : i + m] for i in range(0, len(data), m)]
    elif len(shape) == 2:
        m, n = shape
        return [
            [[data[i + j : i + j + n] for j in range(0, m * n, n)]]
            for i in range(0, len(data), m * n)
        ]
    else:
        raise ValueError("Invalid shape")


def unpack_ints(
    packed: "PackedBitVector",
    start: int = 0,
    count: Optional[int] = None,
    shape: Optional[Tuple[int, ...]] = None,
) -> List[int]:
    assert packed.m_BitSize is not None

    m_BitSize = packed.m_BitSize
    m_Data = packed.m_Data

    bitPos = m_BitSize * start
    indexPos = bitPos // 8
    bitPos %= 8

    if count is None:
        count = packed.m_NumItems

    # if m_BitSize <= 8:
    #     dtype = np.uint8
    # elif m_BitSize <= 16:
    #     dtype = np.uint16
    # elif m_BitSize <= 32:
    #     dtype = np.uint32
    # elif m_BitSize <= 64:
    #     dtype = np.uint64
    # else:
    #     raise ValueError("Invalid bit size")

    # data = np.zeros(packed.m_NumItems, dtype=dtype)
    data = [0] * packed.m_NumItems

    for i in range(packed.m_NumItems):
        bits = 0
        value = 0
        while bits < m_BitSize:
            value |= (m_Data[indexPos] >> bitPos) << bits
            num = min(m_BitSize - bits, 8 - bitPos)
            bitPos += num
            bits += num
            if bitPos == 8:
                indexPos += 1
                bitPos = 0
        data[i] = value & ((1 << m_BitSize) - 1)

    return reshape(data, shape)


def unpack_floats(
    packed: "PackedBitVector",
    start: int = 0,
    count: Optional[int] = None,
    shape: Optional[Tuple[int, ...]] = None,
) -> List[float]:
    assert (
        packed.m_BitSize is not None
        and packed.m_Range is not None
        and packed.m_Start is not None
    )

    # read as int and cast up to double to prevent loss of precision
    quantized_f64 = unpack_ints(packed, start, count)
    quantized = [x * packed.m_Range + packed.m_Start for x in quantized_f64]
    return reshape(quantized, shape)


# def pack_ints(
#     data: npt.NDArray[np.uint], bitsize: Optional[int] = 0
# ) -> PackedBitVector:
#     # ensure that the data type is unsigned
#     assert "uint" in data.dtype.name

#     m_NumItems = data.size

#     maxi = data.max()
#     # Prevent overflow
#     if bitsize:
#         m_BitSize = bitsize
#     else:
#         m_BitSize = (32 if maxi == 0xFFFFFFFF else np.ceil(np.log2(maxi + 1))) % 256
#     m_Data = np.zeros((m_NumItems * m_BitSize + 7) // 8, dtype=np.uint8)

#     indexPos = 0
#     bitPos = 0
#     for x in data:
#         bits = 0
#         while bits < m_BitSize:
#             m_Data[indexPos] |= (x >> bits) << bitPos
#             num = min(m_BitSize - bits, 8 - bitPos)
#             bitPos += num
#             bits += num
#             if bitPos == 8:
#                 indexPos += 1
#                 bitPos = 0

#     return PackedBitVector(m_NumItems=m_NumItems, m_BitSize=m_BitSize, m_Data=m_Data)


# def pack_floats(
#     data: npt.NDArray[np.floating[Any]],
#     bitsize: Optional[int] = None,
# ) -> PackedBitVector:
#     min = data.min()
#     max = data.max()
#     range = max - min
#     data_f64 = data.astype(np.float64)
#     # rebase to 0
#     data_f64 -= min
#     # scale to [0, 1]
#     data_f64 /= range
#     # quantize to [0, 2^bit_size - 1]
#     bitsize = bitsize or max(data.itemsize, 32)
#     assert bitsize is not None

#     data_f64 *= (1 << bitsize) - 1
#     # pack the data
#     packed = pack_ints(data_f64.astype(np.uint32), bitsize)
#     packed.m_Start = min
#     packed.m_Range = range
#     return packed

__all__ = ("unpack_ints", "unpack_floats")
