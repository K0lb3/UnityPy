#define PY_SSIZE_T_CLEAN
#pragma once
#include <Python.h>
#include "structmember.h"
#include "TypeTreeHelper.h"
#include <stdio.h>
#include <string.h>
#include "endian.h"

typedef struct
{
    char *data;
    char *dataStart;
    char *dataEnd;
    char swap;
    PyObject *obj;
} Reader;
typedef PyObject *(*read_type)(Reader *);

#define kAlignBytesFlag 1 << 14
#define kAnyChildUsesAlignBytesFlag 1 << 15

#define HASH_SInt8 235330747
#define HASH_UInt8 237702589
#define HASH_char 2090147939
#define HASH_SInt16 3470947178
#define HASH_short 274395349
#define HASH_UInt16 3549217964
#define HASH_unsigned_short 878862258
#define HASH_SInt32 3470947240
#define HASH_int 193495088
#define HASH_UInt32 3549218026
#define HASH_unsigned_int 2990314445
#define HASH_TypePtr 238243313
#define HASH_SInt64 3470947341
#define HASH_long_long 2373003301
#define HASH_UInt64 3549218127
#define HASH_unsigned_long_long 857652610
#define HASH_FileSize 2878770112
#define HASH_float 259121563
#define HASH_double 4181547808
#define HASH_bool 2090120081
#define HASH_string 479440892
#define HASH_TypelessData 1242572536
#define HASH_map 193499011

#define CHECK_LENGTH(reader, length)                                                                                                                                                                                                      \
    if (reader->data + length > reader->dataEnd)                                                                                                                                                                                          \
    {                                                                                                                                                                                                                                     \
        PyErr_Format(PyExc_ValueError, "Can't read %d bytes at position %d of %d\nError occured at %s:%d:%s", length, (int)(reader->data - reader->dataStart), (int)(reader->dataEnd - reader->dataStart), __FILE__, __LINE__, __func__); \
        return NULL;                                                                                                                                                                                                                      \
    }

static char SURROGATEESCAPE[] = "surrogateescape";

/* function signatures */
static int read_length(Reader *reader);
static PyObject *read_SInt8(Reader *reader);
static PyObject *read_UInt8(Reader *reader);
static PyObject *read_SInt16(Reader *reader);
static PyObject *read_UInt16(Reader *reader);
static PyObject *read_SInt32(Reader *reader);
static PyObject *read_UInt32(Reader *reader);
static PyObject *read_SInt64(Reader *reader);
static PyObject *read_UInt64(Reader *reader);
static PyObject *read_float(Reader *reader);
static PyObject *read_double(Reader *reader);
static PyObject *read_bool(Reader *reader);
static PyObject *read_string(Reader *reader);
static PyObject *read_TypelessData(Reader *reader);

static uint32_t hash_string(const char *str);

static read_type getReadFunction(int hash_value, int* index);
static PyObject* getSubNodes(PyObject* nodes, int* index);

static PyObject *TypeTreeHelper_ReadValue(PyObject *nodes, Reader *reader, int *index);
static PyObject *TypeTreeHelper_ReadValueVector(PyObject *nodes, Reader *reader, int *index);

PyObject *read_typetree(PyObject *self, PyObject *args);

/* implementation */
static inline uint32_t hash_str(const char *str)
{
    unsigned int hash = 5381;
    int c;
    while ((c = *str++))
        hash = ((hash << 5) + hash) + c;
    return hash;
}

static inline void initReadFuncOrNodes(PyObject *nodes, int *index, PyObject **subnodes, read_type *func, char *subalign)
{
    TypeTreeNodeObject *node = (TypeTreeNodeObject *)PyList_GetItem(nodes, *index);
    uint32_t hash = hash_str(node->type);
    *func = getReadFunction(hash, index);
    if (*func == NULL)
    {
        *subnodes = getSubNodes(nodes, index);
    }
    else
    {
        *subalign = (node->meta_flag & kAlignBytesFlag) ? 1 : 0;
    }
}


static inline void align4(Reader *reader)
{
    char mod = (reader->data - reader->dataStart) % 4;
    if (mod != 0)
    {
        reader->data += 4 - mod;
    }
}

static inline PyObject *read_bool(Reader *reader)
{
    CHECK_LENGTH(reader, 1);
    return PyBool_FromLong(*(char *)reader->data++);
}

static inline PyObject *read_SInt8(Reader *reader)
{
    CHECK_LENGTH(reader, 1);
    return PyLong_FromLong(*(signed char *)reader->data++);
}

static inline PyObject *read_UInt8(Reader *reader)
{
    CHECK_LENGTH(reader, 1);
    return PyLong_FromUnsignedLong(*(unsigned char *)reader->data++);
}

static inline PyObject *read_SInt16(Reader *reader)
{
    CHECK_LENGTH(reader, 2);
    PyObject *ret = NULL;
    if (reader->swap)
    {
        ret = PyLong_FromLong((signed short)bswap16(*(unsigned short *)reader->data));
    }
    else
    {
        ret = PyLong_FromLong(*(signed short *)(reader->data));
    }
    reader->data += 2;
    return ret;
}

static inline PyObject *read_UInt16(Reader *reader)
{
    CHECK_LENGTH(reader, 2);
    PyObject *ret = NULL;
    if (reader->swap)
    {
        ret = PyLong_FromUnsignedLong((unsigned short)bswap16(*(unsigned short *)reader->data));
    }
    else
    {
        ret = PyLong_FromUnsignedLong(*(unsigned short *)(reader->data));
    }
    reader->data += 2;
    return ret;
}

static inline PyObject *read_SInt32(Reader *reader)
{
    CHECK_LENGTH(reader, 4);
    PyObject *ret = NULL;
    if (reader->swap)
    {
        ret = PyLong_FromLong((signed int)bswap32(*(unsigned int *)reader->data));
    }
    else
    {
        ret = PyLong_FromLong(*(signed int *)(reader->data));
    }
    reader->data += 4;
    return ret;
}

static inline PyObject *read_UInt32(Reader *reader)
{
    CHECK_LENGTH(reader, 4);
    PyObject *ret = NULL;
    if (reader->swap)
    {
        ret = PyLong_FromUnsignedLong((unsigned int)bswap32(*(unsigned int *)reader->data));
    }
    else
    {
        ret = PyLong_FromUnsignedLong(*(unsigned int *)(reader->data));
    }
    reader->data += 4;
    return ret;
}

static inline PyObject *read_SInt64(Reader *reader)
{
    CHECK_LENGTH(reader, 8);
    PyObject *ret = NULL;
    if (reader->swap)
    {
        ret = PyLong_FromLongLong((signed long long)bswap64(*(unsigned long long *)reader->data));
    }
    else
    {
        ret = PyLong_FromLongLong(*(signed long long *)(reader->data));
    }
    reader->data += 8;
    return ret;
}

static inline PyObject *read_UInt64(Reader *reader)
{
    CHECK_LENGTH(reader, 8);
    PyObject *ret = NULL;
    if (reader->swap)
    {
        ret = PyLong_FromUnsignedLongLong((unsigned long long)bswap64(*(unsigned long long *)reader->data));
    }
    else
    {
        ret = PyLong_FromUnsignedLongLong(*(unsigned long long *)(reader->data));
    }
    reader->data += 8;
    return ret;
}

static inline PyObject *read_float(Reader *reader)
{
    CHECK_LENGTH(reader, 4);
    PyObject *ret = NULL;
    if (reader->swap)
    {
        ret = PyFloat_FromDouble((float)bswap32(*(unsigned int *)reader->data));
    }
    else
    {
        ret = PyFloat_FromDouble(*(float *)(reader->data));
    }
    reader->data += 4;
    return ret;
}

static inline PyObject *read_double(Reader *reader)
{
    CHECK_LENGTH(reader, 8);
    PyObject *ret = NULL;
    if (reader->swap)
    {
        ret = PyFloat_FromDouble((double)bswap64(*(unsigned long long *)reader->data));
    }
    else
    {
        ret = PyFloat_FromDouble(*(double *)(reader->data));
    }
    reader->data += 8;
    return ret;
}

static inline int read_length(Reader *reader)
{
    int length = *(int *)reader->data;
    reader->data += 4;
    if (reader->swap)
    {
        length = bswap32(length);
    }
    return length;
}

static inline PyObject *read_string(Reader *reader)
{
    CHECK_LENGTH(reader, 4);
    int length = read_length(reader);
    CHECK_LENGTH(reader, length);
    PyObject *str = PyUnicode_DecodeUTF8(reader->data, length, SURROGATEESCAPE);
    reader->data += length;
    // align
    align4(reader);
    return str;
}

static inline PyObject *read_TypelessData(Reader *reader)
{
    CHECK_LENGTH(reader, 4);
    int length = read_length(reader);
    CHECK_LENGTH(reader, length);
    PyObject *value = PyMemoryView_FromMemory(reader->data, length, PyBUF_READ);
    reader->data += length;
    return value;
}

static inline read_type getReadFunction(int hash_value, int *index)
{
    switch (hash_value)
    {
    case HASH_SInt8:
        return read_SInt8;
    case HASH_UInt8:
    case HASH_char:
        return read_UInt8;
    case HASH_SInt16:
    case HASH_short:
        return read_SInt16;
    case HASH_UInt16:
    case HASH_unsigned_short:
        return read_UInt16;
    case HASH_SInt32:
    case HASH_int:
        return read_SInt32;
    case HASH_UInt32:
    case HASH_unsigned_int:
    case HASH_TypePtr: // Type*
        return read_UInt32;
    case HASH_SInt64:
    case HASH_long_long:
        return read_SInt64;
    case HASH_UInt64:
    case HASH_unsigned_long_long:
    case HASH_FileSize:
        return read_UInt64;
    case HASH_float:
        return read_float;
    case HASH_double:
        return read_double;
    case HASH_bool:
        return read_bool;
    case HASH_string:
        *index += 3;
        return read_string;
    case HASH_TypelessData:
        *index += 2;
        return read_TypelessData;
    default:
        return NULL;
    }
}

static PyObject *getSubNodes(PyObject *nodes, int *index)
{
    PyObject *result = NULL;
    TypeTreeNodeObject *node = (TypeTreeNodeObject *)PyList_GetItem(nodes, *index);
    unsigned short level = node->level;
    for (int i = *index + 1; i < PyList_Size(nodes); i++)
    {
        if (((TypeTreeNodeObject *)PyList_GetItem(nodes, i))->level <= level)
        {
            result = PyList_GetSlice(nodes, *index, i);
            *index = i - 1;
            return result;
        }
    }
    result = PyList_GetSlice(nodes, *index, PyList_Size(nodes));
    *index = PyList_Size(nodes) - 1;
    return result;
}

static inline int PyDict_SetItemString_Safe(PyObject *dict, const char *key, PyObject *value)
{
    int ret = PyDict_SetItemString(dict, key, value);
    // SetItemString increases the ref count
    // so we have to decrease it here again
    // so that the value will be destroyed with the dict
    Py_XDECREF(value);
    return ret;
}

static inline int PyList_SetItem_Safe(PyObject *list, int i, PyObject *value)
{
    int ret = PyList_SetItem(list, i, value);
    // SetItem increases the ref count
    // so we have to decrease it here again
    // so that the value will be destroyed with the list
    // Py_XDECREF(value);
    return ret;
}



static PyObject *TypeTreeHelper_ReadValue(PyObject *nodes, Reader *reader, int *index)
{
    if (*index >= PyList_Size(nodes))
    {
        PyErr_SetString(PyExc_RuntimeError, "index out of range");
        return NULL;
    }
    TypeTreeNodeObject *node = (TypeTreeNodeObject *)PyList_GetItem(nodes, *index);
    PyObject *value = NULL;
    int sub_index = 0;

    char align = (node->meta_flag & kAlignBytesFlag) ? 1 : 0;
    // printf("RVa: %d\t%lld\t%s\t%s\t%d\t%d\n", *index, (reader->data - reader->dataStart), node->name, node->type, align, node->meta_flag);

    int hash_value = hash_str(node->type);
    read_type func = getReadFunction(hash_value, index);
    if (func)
    {
        value = func(reader);
    }
    else
    {
        if (hash_value == HASH_map)
        {
            TypeTreeNodeObject *node2 = (TypeTreeNodeObject *)PyList_GetItem(nodes, *index + 1);
            if (node2->meta_flag & kAlignBytesFlag)
                align = 1;

            CHECK_LENGTH(reader, 4);
            int size = read_length(reader);

            *index += 4; // skip self, Array, size, pair
            PyObject *first_nodes = NULL;
            read_type first_func = NULL;
            char firstalign = 0;
            initReadFuncOrNodes(nodes, index, &first_nodes, &first_func, &firstalign);
            *index += 1; // move to start of second
            PyObject *second_nodes = NULL;
            read_type second_func = NULL;
            char secondalign = 0;
            initReadFuncOrNodes(nodes, index, &second_nodes, &second_func, &secondalign);

            value = PyList_New(size);
            PyObject *first;
            PyObject *second;
            for (int i = 0; i < size; i++)
            {
                sub_index = 0;
                first = (first_func) ? first_func(reader) : TypeTreeHelper_ReadValue(first_nodes, reader, &sub_index);
                if (first == NULL)
                {
                    Py_XDECREF(value);
                    return NULL;
                }
                if (firstalign)
                    align4(reader);
                sub_index = 0;
                second = (second_func) ? second_func(reader) : TypeTreeHelper_ReadValue(second_nodes, reader, &sub_index);
                if (second == NULL)
                {
                    Py_XDECREF(first);
                    Py_XDECREF(second);
                    return NULL;
                }
                if (secondalign)
                    align4(reader);
                PyList_SetItem(value, i, PyTuple_Pack(2, first, second));
                Py_XDECREF(first);
                Py_XDECREF(second);
            }
            Py_XDECREF(first_nodes);
            Py_XDECREF(second_nodes);
        }
        else
        {
            TypeTreeNodeObject *node2 = (TypeTreeNodeObject *)PyList_GetItem(nodes, *index + 1);
            if (strcmp(node2->type, "Array") == 0)
            {
                if (node2->meta_flag & kAlignBytesFlag)
                    align = 1;
                *index += 3; // skip self, Array, size
                PyObject *vector_nodes = NULL;
                read_type vector_func = NULL;
                char subalign = 0;
                initReadFuncOrNodes(nodes, index, &vector_nodes, &vector_func, &subalign);

                int size = read_length(reader);
                value = PyList_New(size);
                for (int i = 0; i < size; i++)
                {
                    int sub_index = 0;
                    PyObject *vector_value = (vector_func) ? vector_func(reader) : TypeTreeHelper_ReadValue(vector_nodes, reader, &sub_index);
                    if (vector_value == NULL)
                    {
                        Py_XDECREF(value);
                        return NULL;
                    }
                    if (subalign)
                        align4(reader);
                    PyList_SetItem_Safe(value, i, vector_value);
                }
                Py_XDECREF(vector_nodes);
            }
            else // Class
            {
                PyObject *cls_nodes = getSubNodes(nodes, index);
                int j = 1;
                value = PyDict_New();
                char *j_name = NULL;
                while (j < PyList_Size(cls_nodes))
                {
                    j_name = ((TypeTreeNodeObject *)PyList_GetItem(cls_nodes, j))->name;
                    PyObject *j_value = TypeTreeHelper_ReadValue(cls_nodes, reader, &j);
                    if (j_value == NULL)
                    {
                        Py_XDECREF(value);
                        return NULL;
                    }
                    PyDict_SetItemString_Safe(value, j_name, j_value);
                    j++;
                }
                Py_XDECREF(cls_nodes);
            }
        }
    }

    if (align)
        align4(reader);
    return value;
}

static PyObject *TypeTreeHelper_ReadTypeTree(PyObject *nodes, PyObject *buf, char swap)
{
    Py_buffer view;
    if (Py_TYPE(buf)->tp_as_buffer && Py_TYPE(buf)->tp_as_buffer->bf_releasebuffer)
    {
        buf = PyMemoryView_FromObject(buf);
        if (buf == NULL)
        {
            return NULL;
        }
    }
    else
    {
        Py_INCREF(buf);
    }

    if (PyObject_GetBuffer(buf, &view, PyBUF_WRITABLE | PyBUF_SIMPLE) < 0)
    {
        PyErr_Clear();
        if (PyObject_GetBuffer(buf, &view, PyBUF_SIMPLE) < 0)
        {
            Py_DECREF(buf);
            return NULL;
        }
    }

    Reader reader = {
        .data = (char *)view.buf,
        .dataStart = (char *)view.buf,
        .dataEnd = (char *)view.buf + view.len,
        .swap = swap,
        .obj = buf};

    PyBuffer_Release(&view);

    int index = 0;
    PyObject *result = TypeTreeHelper_ReadValue(nodes, &reader, &index);

    Py_DECREF(buf);

    return result;
}

PyObject *read_typetree(PyObject *self, PyObject *args)
{
    PyObject *nodes = PyTuple_GetItem(args, 0);
    PyObject *buf = PyTuple_GetItem(args, 1);
    PyObject *swap_obj = PyTuple_GetItem(args, 2);
    char swap = 0;

    if (!PyUnicode_Check(swap_obj))
    {
        PyErr_SetString(PyExc_TypeError,
                        "The endian attribute value must be a string");
        return NULL;
    }
    if (PyUnicode_GET_LENGTH(swap_obj) != 1)
    {
        PyErr_SetString(PyExc_TypeError,
                        "The endian attribute value must be a string of size 1");
        return NULL;
    }
    char endian = *(char*)PyUnicode_DATA(swap_obj);
    switch (endian)
    {
    case '<':
        if (IS_LITTLE_ENDIAN == 0)
            swap = 1;
        break;
    case '>':
        if (IS_LITTLE_ENDIAN == 1)
            swap = 1;
        break;
    case '=':
    case '|':
        break;
    default:
    {
        PyErr_SetString(PyExc_TypeError,
                        "The endian attribute value must be one of '>', '<', '=', '|'");
        return NULL;
    }
    }
    return TypeTreeHelper_ReadTypeTree(nodes, buf, swap);
}

static void
TypeTreeNode_dealloc(TypeTreeNodeObject *self)
{
    PyMem_Free(self->name);
    PyMem_Free(self->type);
    // for (unsigned short i = 0; i < self->children_count; i++)
    // {
    //     Py_DECREF((PyObject*)self->children[i]);
    // }
    // PyMem_Free(self->children);
    Py_TYPE(self)->tp_free((PyObject *)self);
}

PyObject *
TypeTreeNode_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    TypeTreeNodeObject *self;
    self = (TypeTreeNodeObject *)type->tp_alloc(type, 0);
    if (self != NULL)
    {
        self->version = 0;
        self->level = 0;
        self->is_array = 0;
        self->byte_size = 0;
        self->index = 0;
        self->meta_flag = 0;
        self->type = NULL;
        self->name = NULL;
        // self->type[0] = '\0';
        // self->name[0] = '\0';
        // self->children_count = 0;
        // self->children = NULL;
        self->type_str_offset = 0;
        self->name_str_offset = 0;
        self->ref_type_hash = 0;
        self->variable_count = 0;
    }
    return (PyObject *)self;
}

static int
TypeTreeNode_init(TypeTreeNodeObject *self, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {
        "name",            // char*
        "type",            // char*
        "level",           // uint8
        "meta_flag",       // int32
        "version",         // int16
        "is_array",        // char
        "byte_size",       // int
        "index",           // int
        "type_str_offset", // unsigned int
        "name_str_offset", // unsigned int
        "ref_type_hash",   // unsigned long long
        "variable_count",  // int
        NULL};
    const char *type = NULL;
    const char *name = NULL;
    if (!PyArg_ParseTupleAndKeywords(
            args,
            kwds,
            "|zzbihbiiIIKi",
            kwlist,
            &name,
            &type,
            &self->level,
            &self->meta_flag,
            &self->version,
            &self->is_array,
            &self->byte_size,
            &self->index,
            &self->type_str_offset,
            &self->name_str_offset,
            &self->ref_type_hash,
            &self->variable_count))
        return -1;
    if (type != NULL)
    {
        self->type = PyMem_Malloc(strlen(type) + 1);
        strcpy(self->type, type);
    }
    if (name != NULL)
    {
        self->name = PyMem_Malloc(strlen(name) + 1);
        strcpy(self->name, name);
    }
    return 0;
};

static PyMemberDef TypeTreeNode_members[] = {
    {"type", T_STRING, offsetof(TypeTreeNodeObject, type), 0, ""},
    {"name", T_STRING, offsetof(TypeTreeNodeObject, name), 0, ""},
    {"byte_size", T_INT, offsetof(TypeTreeNodeObject, byte_size), 0, ""},
    {"index", T_INT, offsetof(TypeTreeNodeObject, index), 0, ""},
    {"is_array", T_BOOL, offsetof(TypeTreeNodeObject, is_array), 0, ""},
    {"version", T_SHORT, offsetof(TypeTreeNodeObject, version), 0, ""},
    {"meta_flag", T_INT, offsetof(TypeTreeNodeObject, meta_flag), 0, ""},
    {"level", T_UBYTE, offsetof(TypeTreeNodeObject, level), 0, ""},
    {"type_str_offset", T_UINT, offsetof(TypeTreeNodeObject, type_str_offset), 0, ""},
    {"name_str_offset", T_UINT, offsetof(TypeTreeNodeObject, name_str_offset), 0, ""},
    {"ref_type_hash", T_ULONGLONG, offsetof(TypeTreeNodeObject, ref_type_hash), 0, ""},
    {"variable_count", T_INT, offsetof(TypeTreeNodeObject, variable_count), 0, ""},
    {NULL} /* Sentinel */
};

static PyObject *
TypeTreeNode_repr(PyObject *self)
{
    TypeTreeNodeObject *node = (TypeTreeNodeObject *)self;
    char *type = node->type;
    char *name = node->name;
    char *type_str = "";
    char *name_str = "";
    if (type != NULL)
    {
        type_str = PyMem_Malloc(strlen(type) + 1);
        strcpy(type_str, type);
    }
    if (name != NULL)
    {
        name_str = PyMem_Malloc(strlen(name) + 1);
        strcpy(name_str, name);
    }
    char buf[1024];
    memset(buf, 0, 1024);
    sprintf(buf, "TypeTreeNode(type=%s, name=%s, byte_size=%d, index=%d, is_array=%d, version=%d, meta_flag=%d, level=%d, type_str_offset=%d, name_str_offset=%d, ref_type_hash=%llu, variable_count=%d)", type_str, name_str, node->byte_size, node->index, node->is_array, node->version, node->meta_flag, node->level, node->type_str_offset, node->name_str_offset, node->ref_type_hash, node->variable_count);
    PyMem_Free(type_str);
    PyMem_Free(name_str);
    return PyUnicode_FromString(buf);
}

// PyTypeObject TypeTreeNodeType;

// static int
// TypeTreeNode_set_children(TypeTreeNodeObject *self, PyObject *value, void *closure)
// {
//     PyObject *tmp;
//     if (value == NULL)
//     {
//         PyErr_SetString(PyExc_TypeError, "Cannot delete the children attribute");
//         return -1;
//     }
//     if (!PyList_Check(value))
//     {
//         PyErr_SetString(PyExc_TypeError, "The children attribute value must be a list");
//         return -1;
//     }
//     for (unsigned short i = 0; i < self->children_count; i++)
//     {
//         Py_DECREF((PyObject*)self->children[i]);
//     }
//     PyMem_Free(self->children);
//     self->children_count = PyList_Size(value);
//     self->children = PyMem_Malloc(sizeof(TypeTreeNodeObject *) * self->children_count);
//     for (unsigned short i = 0; i < self->children_count; i++)
//     {
//         tmp = PyList_GetItem(value, i);
//         if (!PyObject_TypeCheck(tmp, &TypeTreeNodeType))
//         {
//             PyErr_SetString(PyExc_TypeError, "The children attribute value must be a list of TypeTreeNode objects");
//             return -1;
//         }
//         self->children[i] = (TypeTreeNodeObject *)tmp;
//         Py_INCREF(tmp);
//     }
//     return 0;
// }

// static PyGetSetDef TypeTreeNode_getsetters[] = {
//     {"children", (getter) TypeTreeNode_get_children, (setter) TypeTreeNode_set_children,
//      "", NULL},
//     {NULL}  /* Sentinel */
// };

PyTypeObject TypeTreeNodeType = {
    PyVarObject_HEAD_INIT(NULL, 0)
        .tp_name = "UnityPyBoost.TypeTreeNode",
    .tp_doc = PyDoc_STR("TypeTreeNode objects"),
    .tp_basicsize = sizeof(TypeTreeNodeObject),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_new = TypeTreeNode_new,
    .tp_init = (initproc)TypeTreeNode_init,
    .tp_dealloc = (destructor)TypeTreeNode_dealloc,
    .tp_members = TypeTreeNode_members,
    .tp_repr = (reprfunc)TypeTreeNode_repr,
};

int add_typetreenode_to_module(PyObject *m)
{
    if (PyType_Ready(&TypeTreeNodeType) < 0)
        return -1;
    Py_INCREF(&TypeTreeNodeType);
    PyModule_AddObject(m, "TypeTreeNode", (PyObject *)&TypeTreeNodeType);
    return 0;
}
