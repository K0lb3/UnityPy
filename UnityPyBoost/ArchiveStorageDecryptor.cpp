// based on https://github.com/RazTools/Studio/blob/main/AssetStudio/Crypto/UnityCN.cs

#include "ArchiveStorageDecryptor.hpp"
#include <Python.h>

inline unsigned char decrypt_byte(unsigned char* bytes, uint64_t& offset, uint64_t& index, unsigned char* index_data, unsigned char* substitute_data)
{
    unsigned char count_byte = substitute_data[((index >> 2) & 3) + 4]
                            + substitute_data[index & 3]
                            + substitute_data[((index >> 4) & 3) + 8]
                            + substitute_data[((unsigned char)index >> 6) + 12];
    bytes[offset] = (unsigned char)((index_data[bytes[offset] & 0xF] - count_byte) & 0xF | 0x10 * (index_data[bytes[offset] >> 4] - count_byte));
    count_byte = bytes[offset++];
    index++;
    return count_byte;
}

inline uint64_t decrypt(unsigned char* bytes, uint64_t index, uint64_t remaining, unsigned char* index_data, unsigned char* substitute_data)
{
    uint64_t offset = 0;

    unsigned char current_byte = decrypt_byte(bytes, offset, index, index_data, substitute_data);
    uint64_t current_byte_high = current_byte >> 4;
    uint64_t current_byte_low = current_byte & 0xF;

    if (current_byte_high == 0xF)
    {
        unsigned char count_byte;
        do
        {
            count_byte = decrypt_byte(bytes, offset, index, index_data, substitute_data);
            current_byte_high += count_byte;
        } while (count_byte == 0xFF);
    }

    offset += current_byte_high;

    if (offset < remaining)
    {
        decrypt_byte(bytes, offset, index, index_data, substitute_data);
        decrypt_byte(bytes, offset, index, index_data, substitute_data);
        if (current_byte_low == 0xF)
        {
            unsigned char count_byte;
            do
            {
                count_byte = decrypt_byte(bytes, offset, index, index_data, substitute_data);
            } while (count_byte == 0xFF);
        }
    }

    return offset;
}

PyObject* decrypt_block(PyObject* self, PyObject* args) {
    PyObject* py_index_bytes;
    PyObject* py_substitute_bytes;
    PyObject* py_data;
    uint64_t index;

    if (!PyArg_ParseTuple(args, "OOOi", &py_index_bytes, &py_substitute_bytes, &py_data, &index)) {
        return NULL;
    }

    Py_buffer view;
    if (PyObject_GetBuffer(py_data, &view, PyBUF_SIMPLE) != 0) {
        return NULL;
    }

    if (!PyBytes_Check(py_index_bytes) || !PyBytes_Check(py_substitute_bytes)) {
        PyBuffer_Release(&view);
        PyErr_SetString(PyExc_TypeError, "Attributes 'index' and 'substitute' must be bytes");
        return NULL;
    }

    unsigned char* data = (unsigned char*)view.buf;
    uint64_t size = (uint64_t)view.len;
    unsigned char* index_data = (unsigned char*)PyBytes_AS_STRING(py_index_bytes);
    unsigned char* substitute_data = (unsigned char*)PyBytes_AS_STRING(py_substitute_bytes);

    uint64_t offset = 0;
    while (offset < size) {
        offset += decrypt(data + offset, index++, size - offset, index_data, substitute_data);
    }

    PyBuffer_Release(&view);
    Py_RETURN_NONE;
}

