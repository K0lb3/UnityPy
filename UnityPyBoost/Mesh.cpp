#include "Mesh.hpp"
#include <Python.h>
#include <string>
#include <swap.hpp>

#define MAX(x, y) (((x) > (y)) ? (x) : (y))

enum VertexFormat
{
    kVertexFormatFloat,
    kVertexFormatFloat16,
    kVertexFormatUNorm8,
    kVertexFormatSNorm8,
    kVertexFormatUNorm16,
    kVertexFormatSNorm16,
    kVertexFormatUInt8,
    kVertexFormatSInt8,
    kVertexFormatUInt16,
    kVertexFormatSInt16,
    kVertexFormatUInt32,
    kVertexFormatSInt32
};

template <uint8_t componentByteSize>
void unpack_vertexdata_template(uint8_t *componentBytes, uint8_t *vertexData, uint32_t m_VertexCount, uint32_t m_StreamOffset, uint32_t m_StreamStride, uint32_t m_ChannelOffset, uint32_t m_ChannelDimension)
{
    const auto channelSize = componentByteSize * m_ChannelDimension;

    uint8_t *componentCur = componentBytes;
    uint8_t *vertexCur = vertexData;

    // move vertexCur to the first vertex
    vertexCur += m_StreamOffset + m_ChannelOffset;

    for (uint32_t v = 0; v < m_VertexCount; v++)
    {
        memcpy(componentCur, vertexCur, channelSize);
        componentCur += channelSize;
        vertexCur += m_StreamStride;
    }
}

template <uint8_t componentByteSize>
void swap_vertexdata(uint8_t *componentBytes, uint32_t m_VertexCount, uint32_t m_ChannelDimension)
{
    if constexpr (componentByteSize == 1)
    {
        // do nothing
    }
    else if constexpr (componentByteSize == 2)
    {
        uint16_t *componentUints = (uint16_t *)componentBytes;
        for (uint32_t i = 0; i < m_VertexCount * m_ChannelDimension; i++)
        {
            swap_any_inplace(componentUints++);
        }
    }
    else if constexpr (componentByteSize == 4)
    {
        uint32_t *componentUints = (uint32_t *)componentBytes;
        for (uint32_t i = 0; i < m_VertexCount * m_ChannelDimension; i++)
        {
            swap_any_inplace(componentUints++);
        }
    }
    else if constexpr (componentByteSize == 8)
    {
        uint64_t *componentUints = (uint64_t *)componentBytes;
        for (uint32_t i = 0; i < m_VertexCount * m_ChannelDimension; i++)
        {
            swap_any_inplace(componentUints++);
        }
    }
    else
    {
        const auto compoentByteSizeStr = std::to_string(componentByteSize);
        const auto error_message = "Swap not implemented for this size: " + compoentByteSizeStr;
        PyErr_SetString(PyExc_ValueError, error_message.c_str());
    }
}

PyObject *unpack_vertexdata(PyObject *self, PyObject *args)
{
    // define vars
    int componentByteSize;
    uint32_t m_VertexCount;
    uint8_t swap;
    // char format;
    Py_buffer vertexDataView;
    uint32_t m_StreamOffset;
    uint32_t m_StreamStride;
    uint32_t m_ChannelOffset;
    uint32_t m_ChannelDimension;

    if (!PyArg_ParseTuple(args, "y*iIIIIIb", &vertexDataView, &componentByteSize, &m_VertexCount, &m_StreamOffset, &m_StreamStride, &m_ChannelOffset, &m_ChannelDimension, &swap))
    {
        if (vertexDataView.buf)
        {
            PyBuffer_Release(&vertexDataView);
        }
        return nullptr;
    }

    uint8_t *vertexData = (uint8_t *)vertexDataView.buf;

    Py_ssize_t componentBytesLength = m_VertexCount * m_ChannelDimension * componentByteSize;

    // check if max values are ok
    uint32_t maxVertexDataAccess = (m_VertexCount - 1) * m_StreamStride + m_ChannelOffset + m_StreamOffset + componentByteSize * (m_ChannelDimension - 1) + componentByteSize;
    if (maxVertexDataAccess > vertexDataView.len)
    {
        PyBuffer_Release(&vertexDataView);
        PyErr_SetString(PyExc_ValueError, "Vertex data access out of bounds");
        return nullptr;
    }

    PyObject *res = PyBytes_FromStringAndSize(nullptr, componentBytesLength);
    if (!res)
    {
        PyBuffer_Release(&vertexDataView);
        return nullptr;
    }
    uint8_t *componentBytes = (uint8_t *)PyBytes_AS_STRING(res);

    switch (componentByteSize)
    {
    case 1:
        unpack_vertexdata_template<1>(componentBytes, vertexData, m_VertexCount, m_StreamOffset, m_StreamStride, m_ChannelOffset, m_ChannelDimension);
        break;
    case 2:
        unpack_vertexdata_template<2>(componentBytes, vertexData, m_VertexCount, m_StreamOffset, m_StreamStride, m_ChannelOffset, m_ChannelDimension);
        if (swap)
        {
            swap_vertexdata<2>(componentBytes, m_VertexCount, m_ChannelDimension);
        }
        break;
    case 4:
        unpack_vertexdata_template<4>(componentBytes, vertexData, m_VertexCount, m_StreamOffset, m_StreamStride, m_ChannelOffset, m_ChannelDimension);
        if (swap)
        {
            swap_vertexdata<4>(componentBytes, m_VertexCount, m_ChannelDimension);
        }
        break;
    case 8:
        unpack_vertexdata_template<8>(componentBytes, vertexData, m_VertexCount, m_StreamOffset, m_StreamStride, m_ChannelOffset, m_ChannelDimension);
        if (swap)
        {
            swap_vertexdata<8>(componentBytes, m_VertexCount, m_ChannelDimension);
        }
        break;
    default:
        PyBuffer_Release(&vertexDataView);
        PyErr_SetString(PyExc_ValueError, "Unsupported component byte size");
        return nullptr;
    }

    PyBuffer_Release(&vertexDataView);
    return res;
}
