#include "AnimationClip.h"
#include <Python.h>

#define MIN(x, y) (((x) < (y)) ? (x) : (y))

/* AnimationClip.py */
static float *UnpackFloats(uint32_t m_NumItems, float m_Range, float m_Start, uint8_t *m_Data, char m_BitSize, int itemCountInChunk, int chunkStride, int start, int numChunks)
{
    int bitPos = m_BitSize * start;
    int indexPos = bitPos / 8;
    bitPos %= 8;

    float scale = 1.0f / m_Range;
    if (numChunks == -1)
        numChunks = (int)m_NumItems / itemCountInChunk;

    // TODO: might be better to use ulong instead of uint
    uint32_t end = chunkStride * numChunks / 4;
    // TODO: check if this is correct
    float *data = (float *)malloc(sizeof(float) * numChunks * itemCountInChunk);
    float *dataStart = data;
    for (uint32_t index = 0; index != end; index += chunkStride / 4)
    {
        for (int i = 0; i < itemCountInChunk; ++i)
        {
            uint32_t x = 0;
            int bits = 0;
            while (bits < m_BitSize)
            {
                x |= (uint32_t)((m_Data[indexPos] >> bitPos) << bits);
                int num = MIN(m_BitSize - bits, 8 - bitPos);
                bitPos += num;
                bits += num;
                if (bitPos == 8)
                {
                    indexPos++;
                    bitPos = 0;
                }
            }
            x &= (uint32_t)(1 << m_BitSize) - 1u;
            *data++ = (x / (scale * ((1 << m_BitSize) - 1)) + m_Start);
        }
    }
    return dataStart;
}

// TODO: check if bitPos, bits, and num can be reduced to chars
static int *UnpackInts(uint32_t m_NumItems, uint8_t *m_Data, char m_BitSize)
{
    int *data = (int *)malloc(m_NumItems * sizeof(int));

    int indexPos = 0;
    int bitPos = 0;
    for (uint32_t i = 0; i < m_NumItems; i++)
    {
        int bits = 0;
        data[i] = 0;
        while (bits < m_BitSize)
        {
            data[i] |= (m_Data[indexPos] >> bitPos) << bits;
            int num = MIN(m_BitSize - bits, 8 - bitPos);
            bitPos += num;
            bits += num;
            if (bitPos == 8)
            {
                indexPos++;
                bitPos = 0;
            }
        }
        data[i] &= (1 << m_BitSize) - 1;
    }
    return data;
}

// TODO: implement unpack quaternions

PyObject *unpack_floats(PyObject *self, PyObject *args)
{
    // define vars
    uint32_t m_NumItems;
    float m_Range;
    float m_Start;
    uint8_t *m_Data;
    char m_BitSize;
    int itemCountInChunk;
    int chunkStride;
    int start;
    int numChunks;
    Py_ssize_t data_size;

    start = 0;
    numChunks = -1;
    if (!PyArg_ParseTuple(args, "Iffy#bii|ii", &m_NumItems, &m_Range, &m_Start, &m_Data, &data_size, &m_BitSize, &itemCountInChunk, &chunkStride, &start, &numChunks))
        return NULL;

    // decode
    float *array = UnpackFloats(m_NumItems, m_Range, m_Start, m_Data, m_BitSize, itemCountInChunk, chunkStride, start, numChunks);

    if (numChunks == -1)
        numChunks = (int)m_NumItems / itemCountInChunk;
    Py_ssize_t array_len = numChunks * itemCountInChunk;
    // return
    PyObject *lst = PyList_New(array_len);
    if (!lst)
        return NULL;
    for (Py_ssize_t i = 0; i < array_len; i++)
    {
        PyObject *num = PyFloat_FromDouble(array[i]);
        if (!num)
        {
            Py_DECREF(lst);
            return NULL;
        }
        PyList_SET_ITEM(lst, i, num); // reference to num stolen
    }
    free(array);
    return lst;
}

PyObject *unpack_ints(PyObject *self, PyObject *args)
{
    // define vars
    uint32_t m_NumItems;
    uint8_t *m_Data;
    char m_BitSize;
    Py_ssize_t data_size;

    if (!PyArg_ParseTuple(args, "Iy#b", &m_NumItems, &m_Data, &data_size, &m_BitSize))
        return NULL;

    // decode
    int *array = UnpackInts(m_NumItems, m_Data, m_BitSize);

    // return
    PyObject *lst = PyList_New(m_NumItems);
    if (!lst)
        return NULL;
    for (uint32_t i = 0; i < m_NumItems; i++)
    {
        PyObject *num = PyLong_FromLong(array[i]);
        if (!num)
        {
            Py_DECREF(lst);
            return NULL;
        }
        PyList_SET_ITEM(lst, i, num); // reference to num stolen
    }
    free(array);
    return lst;
}