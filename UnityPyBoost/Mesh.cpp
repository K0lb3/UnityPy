#include "Mesh.hpp"
#include <Python.h>
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
        return NULL;
    }

    uint8_t *vertexData = (uint8_t *)vertexDataView.buf;

    Py_ssize_t componentBytesLength = m_VertexCount * m_ChannelDimension * componentByteSize;

    // check if max values are ok
    uint32_t maxVertexDataAccess = (m_VertexCount - 1) * m_StreamStride + m_ChannelOffset + m_StreamOffset + componentByteSize * (m_ChannelDimension - 1) + componentByteSize;
    if (maxVertexDataAccess > vertexDataView.len)
    {
        PyBuffer_Release(&vertexDataView);
        PyErr_SetString(PyExc_ValueError, "Vertex data access out of bounds");
        return NULL;
    }

    PyObject *res = PyBytes_FromStringAndSize(nullptr, componentBytesLength);
    if (!res)
    {
        PyBuffer_Release(&vertexDataView);
        return NULL;
    }
    uint8_t *componentBytes = (uint8_t *)PyBytes_AS_STRING(res);

    for (uint32_t v = 0; v < m_VertexCount; v++)
    {
        uint32_t vertexOffset = m_StreamOffset + m_ChannelOffset + m_StreamStride * v;
        for (uint32_t d = 0; d < m_ChannelDimension; d++)
        {
            uint32_t vertexDataOffset = vertexOffset + componentByteSize * d;
            uint32_t componentOffset = componentByteSize * (v * m_ChannelDimension + d);
            memcpy(componentBytes + componentOffset, vertexData + vertexDataOffset, componentByteSize);
        }
    }

    if (swap) // swap bytes
    {
        if (componentByteSize == 2)
        {
            uint16_t *componentUints = (uint16_t *)componentBytes;
            for (uint32_t i = 0; i < componentBytesLength; i += 2)
            {
                swap_any_inplace(componentUints++);
            }
        }
        else if (componentByteSize == 4)
        {

            uint32_t *componentUints = (uint32_t *)componentBytes;
            for (uint32_t i = 0; i < componentBytesLength; i += 4)
            {
                swap_any_inplace(componentUints++);
            }
        }
    }

    PyBuffer_Release(&vertexDataView);
    return res;

    // fast enough in Python
    // uint32_t itemCount = componentBytesLength / componentByteSize;
    // PyObject *lst = PyList_New(itemCount);
    // if (!lst)
    //     return NULL;

    // switch (format)
    // {
    // case kVertexFormatFloat:
    // {
    //     float *items = (float *)componentBytes;
    //     for (uint32_t i = 0; i < itemCount; i++)
    //     {
    //         PyList_SetItem(lst, i, PyFloat_FromDouble((double)*items++));
    //     }
    //     // result[i] = BitConverter.ToSingle(inputBytes, i * 4);
    //     break;
    // }
    // case kVertexFormatFloat16:
    // {
    //     uint16_t *items = (uint16_t *)componentBytes;
    //     for (uint32_t i = 0; i < itemCount; i++)
    //     {
    //         double x = _PyFloat_Unpack2(items++, 0);
    //         if (x == -1.0 && PyErr_Occurred())
    //         {
    //             return NULL;
    //         }
    //         PyList_SetItem(lst, i, PyFloat_FromDouble(x));
    //     }
    //     // result[i] = Half.ToHalf(inputBytes, i * 2);
    //     break;
    // }
    // case kVertexFormatUNorm8:
    // {
    //     uint8_t *items = componentBytes;
    //     for (uint32_t i = 0; i < itemCount; i++)
    //     {
    //         PyList_SetItem(lst, i, PyFloat_FromDouble((double)(*items++ / 255.0f)));
    //     }
    //     // result[i] = inputBytes[i] / 255f;
    //     break;
    // }
    // case kVertexFormatSNorm8:
    // {
    //     int8_t *items = (int8_t *)componentBytes;
    //     for (uint32_t i = 0; i < itemCount; i++)
    //     {
    //         PyList_SetItem(lst, i, PyFloat_FromDouble((double)MAX((*items++ / 127.0f), -1.0f)));
    //     }
    //     // result[i] = Math.Max((sbyte)inputBytes[i] / 127f, -1f);
    //     break;
    // }
    // case kVertexFormatUNorm16:
    // {
    //     uint16_t *items = (uint16_t *)componentBytes;
    //     for (uint32_t i = 0; i < itemCount; i++)
    //     {
    //         PyList_SetItem(lst, i, PyFloat_FromDouble((double)(*items++ / 65535.0f)));
    //     }
    //     // result[i] = BitConverter.ToUInt16(inputBytes, i * 2) / 65535f;
    //     break;
    // }
    // case kVertexFormatSNorm16:
    // {
    //     int16_t *items = (int16_t *)componentBytes;
    //     for (uint32_t i = 0; i < itemCount; i++)
    //     {
    //         PyList_SetItem(lst, i, PyFloat_FromDouble((double)MAX((*items++ / 32767.0f), -1.0f)));
    //     }
    //     // result[i] = Math.Max(BitConverter.ToInt16(inputBytes, i * 2) / 32767f, -1f);
    //     break;
    // }
    // case kVertexFormatUInt8:
    // case kVertexFormatSInt8:
    // {
    //     uint8_t *items = componentBytes;
    //     for (uint32_t i = 0; i < itemCount; i++)
    //     {
    //         PyList_SetItem(lst, i, PyLong_FromUnsignedLong((uint32_t)*items++));
    //     }
    //     // result[i] = inputBytes[i];
    //     break;
    // }
    // case kVertexFormatUInt16:
    // case kVertexFormatSInt16:
    // {
    //     uint16_t *items = (uint16_t *)componentBytes;
    //     for (uint32_t i = 0; i < itemCount; i++)
    //     {
    //         PyList_SetItem(lst, i, PyLong_FromUnsignedLong((uint32_t)*items++));
    //     }
    //     // result[i] = BitConverter.ToInt16(inputBytes, i * 2);
    //     break;
    // }
    // case kVertexFormatUInt32:
    // case kVertexFormatSInt32:
    // {
    //     uint32_t *items = (uint32_t *)componentBytes;
    //     for (uint32_t i = 0; i < itemCount; i++)
    //     {
    //         PyList_SetItem(lst, i, PyLong_FromUnsignedLong(*items++));
    //     }
    //     // result[i] = BitConverter.ToInt32(inputBytes, i * 4);
    //     break;
    // }
    // }
    // free(componentBytes);
    // return lst;
}
