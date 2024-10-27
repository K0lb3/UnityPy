// based on https://github.com/RazTools/Studio/blob/main/AssetStudio/Crypto/UnityCN.cs

#include "ArchiveStorageDecryptor.hpp"
#include <Python.h>

inline unsigned char decrypt_byte(unsigned char *bytes, uint64_t& offset, uint64_t& index, const unsigned char *index_data, const unsigned char *substitute_data)
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

inline uint64_t decrypt(unsigned char *bytes, uint64_t index, uint64_t remaining, const unsigned char *index_data, const unsigned char *substitute_data)
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

PyObject *decrypt_block(PyObject *self, PyObject *args) {
    Py_buffer index_data;
    Py_buffer substitute_data;
    Py_buffer data;
    uint64_t index;

    if (!PyArg_ParseTuple(args, "y*y*y*K", &index_data, &substitute_data, &data, &index)) {
        if (index_data.buf) PyBuffer_Release(&index_data);
        if (substitute_data.buf) PyBuffer_Release(&substitute_data);
        if (data.buf) PyBuffer_Release(&data);
        return NULL;
    }

    PyObject *result = PyBytes_FromStringAndSize(NULL, data.len);
    if (result == NULL) {
        PyBuffer_Release(&index_data);
        PyBuffer_Release(&substitute_data);
        PyBuffer_Release(&data);
        return NULL;
    }

    unsigned char *result_raw = (unsigned char *)PyBytes_AS_STRING(result);
    memcpy(result_raw, data.buf, data.len);

    uint64_t offset = 0;
    while (offset < data.len) {
        offset += decrypt(result_raw + offset, index++, data.len - offset, (unsigned char *)index_data.buf, (unsigned char *)substitute_data.buf);
    }

    PyBuffer_Release(&index_data);
    PyBuffer_Release(&substitute_data);
    PyBuffer_Release(&data);

    return result;
}

