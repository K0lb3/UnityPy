#define PY_SSIZE_T_CLEAN
#pragma once
#include <Python.h>
#include "structmember.h"
#include "TypeTreeHelper.h"
#include <stdio.h>
#include <string.h>

typedef struct
{
    char *data;
    char *dataStart;
    char *dataEnd;
    char swap;
    PyObject *obj;
} Reader;

#define kAlignBytesFlag 1 << 14
#define kAnyChildUsesAlignBytesFlag 1 << 15
static char SURROGATEESCAPE[] = "surrogateescape";

static inline uint32_t hash_str(const char *str)
{
    unsigned int hash = 5381;
    int c;
    while ((c = *str++))
        hash = ((hash << 5) + hash) + c;
    return hash;
}

static inline void align4(Reader *reader)
{
    char mod = (reader->data - reader->dataStart) % 4;
    if (mod != 0)
    {
        reader->data += 4 - mod;
    }
}

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

PyObject *TypeTreeHelper_ReadValueVector(PyObject *nodes, Reader *reader, int *index);

static PyObject *TypeTreeHelper_ReadValue(PyObject *nodes, Reader *reader, int *index)
{
    if (*index >= PyList_Size(nodes))
    {
        PyErr_SetString(PyExc_RuntimeError, "index out of range");
        return NULL;
    }
    TypeTreeNodeObject *node = (TypeTreeNodeObject *)PyList_GetItem(nodes, *index);
    PyObject *value = NULL;
    char align = (node->meta_flag & kAlignBytesFlag) ? 1 : 0;
    // printf("RVa: %d\t%lld\t%s\t%s\t%d\t%d\n", *index, (reader->data - reader->dataStart), node->name, node->type, align, node->meta_flag);
    switch (hash_str(node->type))
    {
    case HASH_SInt8:
        value = PyLong_FromLong((int)*reader->data++);
        break;
    case HASH_UInt8:
    case HASH_char:
        value = PyLong_FromUnsignedLong((unsigned int)*(unsigned char *)reader->data++);
        break;
    case HASH_SInt16:
    case HASH_short:
        value = PyLong_FromLong((int)*(short *)reader->data);
        reader->data += 2;
        break;
    case HASH_UInt16:
    case HASH_unsigned_short:
        value = PyLong_FromUnsignedLong((unsigned int)*(unsigned short *)reader->data);
        reader->data += 2;
        break;
    case HASH_SInt32:
    case HASH_int:
        value = PyLong_FromLong(*(int *)reader->data);
        reader->data += 4;
        break;
    case HASH_UInt32:
    case HASH_unsigned_int:
    case HASH_TypePtr: // Type*
        value = PyLong_FromUnsignedLong(*(unsigned int *)reader->data);
        reader->data += 4;
        break;
    case HASH_SInt64:
    case HASH_long_long:
        value = PyLong_FromLongLong(*(long long *)reader->data);
        reader->data += 8;
        break;
    case HASH_UInt64:
    case HASH_unsigned_long_long:
    case HASH_FileSize:
        value = PyLong_FromUnsignedLongLong(*(unsigned long long *)reader->data);
        reader->data += 8;
        break;
    case HASH_float:
        value = PyFloat_FromDouble((double)*(float *)reader->data);
        reader->data += 4;
        break;
    case HASH_double:
        value = PyFloat_FromDouble(*(double *)reader->data);
        reader->data += 8;
        break;
    case HASH_bool:
        value = PyBool_FromLong((int)*reader->data++);
        break;
    case HASH_string:
        int len_s = *(int *)reader->data;
        reader->data += 4;
        value = PyUnicode_DecodeUTF8(reader->data, len_s, SURROGATEESCAPE);
        reader->data += len_s;
        if (node->meta_flag & kAnyChildUsesAlignBytesFlag)
            align = 1;
        *index += 3;
        break;
    case HASH_TypelessData:
        int len_td = *(int *)reader->data;
        reader->data += 4;
        if (len_td)
        {
            // value = PyBytes_FromStringAndSize(reader->data, len_td);
            // TODO - copy permission from parent node
            value = PyMemoryView_FromMemory(reader->data, len_td, PyBUF_READ);
            reader->data += len_td;
            // Py_buffer *view = (Py_buffer *)PyMemoryView_GET_BUFFER(value);
            // view->obj = reader->obj;
        }
        else
        {
            value = PyBytes_FromStringAndSize(NULL, 0);
        }
        *index += 2;
        break;
    case HASH_map:
        if (node->meta_flag & kAnyChildUsesAlignBytesFlag)
            align = 1;
        int size = (int)*(int *)reader->data;
        reader->data += 4;

        *index += 4; // skip self, Array, size, pair
        PyObject *first_nodes = getSubNodes(nodes, index);
        *index += 1; // move to start of second
        PyObject *second_nodes = getSubNodes(nodes, index);

        int sub_index;
        value = PyList_New(size);
        for (int i = 0; i < size; i++)
        {
            sub_index = 0;
            PyObject *first = TypeTreeHelper_ReadValue(first_nodes, reader, &sub_index);
            sub_index = 0;
            PyObject *second = TypeTreeHelper_ReadValue(second_nodes, reader, &sub_index);
            PyList_SetItem(value, i, PyTuple_Pack(2, first, second));
            Py_XDECREF(first);
            Py_XDECREF(second);
        }
        break;
        Py_XDECREF(first_nodes);
        Py_XDECREF(second_nodes);

    default:
        // Vector
        TypeTreeNodeObject *node2 = (TypeTreeNodeObject *)PyList_GetItem(nodes, *index + 1);
        if (strcmp(node2->type, "Array") == 0)
        {
            if (node->meta_flag & kAnyChildUsesAlignBytesFlag)
                align = 1;
            *index += 3; // skip self, Array, size
            PyObject *vector_nodes = getSubNodes(nodes, index);
            int size = (int)*(int *)reader->data;
            reader->data += 4;
            value = PyList_New(size);
            for (int i = 0; i < size; i++)
            {
                int sub_index = 0;
                PyObject *vector_value = TypeTreeHelper_ReadValue(vector_nodes, reader, &sub_index);
                PyList_SetItem_Safe(value, i, vector_value);
            }
            Py_XDECREF(vector_nodes);
            // int vector_index = 0;
            // value = TypeTreeHelper_ReadValueVector(vector_nodes, reader, &vector_index);
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
                PyDict_SetItemString_Safe(value, j_name, TypeTreeHelper_ReadValue(cls_nodes, reader, &j));
                j++;
            }
            Py_XDECREF(cls_nodes);
        }
        break;
    }

    if (align)
        align4(reader);
    return value;
}

static PyObject *TypeTreeHelper_ReadTypeTree(PyObject *nodes, PyObject *buf)
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
        .swap = 0,
        .obj = buf};

    PyBuffer_Release(&view);

    PyObject *result = PyDict_New();
    if (result == NULL)
    {
        Py_DECREF(buf);
        return NULL;
    }

    int index = 1;
    int count = PyList_Size(nodes);
    while (index < count)
    {
        TypeTreeNodeObject *node = (TypeTreeNodeObject *)PyList_GetItem(nodes, index);
        PyObject *value = TypeTreeHelper_ReadValue(nodes, &reader, &index);
        if (value == NULL)
        {
            Py_XDECREF(result);
            Py_XDECREF(buf);
            return NULL;
        }
        PyDict_SetItemString_Safe(result, node->name, value);
        index++;
    }

    Py_DECREF(buf);

    return result;
}

// PyObject *TypeTreeHelper_ReadValueVector(PyObject *nodes, Reader *reader, int *index)
// {
//     if (*index >= PyList_Size(nodes))
//     {
//         PyErr_SetString(PyExc_RuntimeError, "index out of range");
//         return NULL;
//     }
//     TypeTreeNodeObject *node = PyList_GetItem(nodes, *index);
//     char align = (node->meta_flag & kAlignBytesFlag) ? 1 : 0;

//     printf("RVe: %d\t%lld\t%s\t%s\t%d\t%d\n", *index, (reader->data - reader->dataStart), node->name, node->type, align, node->meta_flag);

//     int vector_size = *(int *)reader->data;
//     reader->data += 4;

//     PyObject *list = PyList_New(vector_size);

//     switch (hash_str(node->type))
//     {
//     case HASH_SInt8:
//         for (int i = 0; i < vector_size; i++)
//         {
//             PyList_SetItem(list, i, PyLong_FromLong((int)*reader->data++));
//         }
//         break;
//     case HASH_UInt8:
//     case HASH_char:
//         for (int i = 0; i < vector_size; i++)
//         {
//             PyList_SetItem(list, i, PyLong_FromUnsignedLong((unsigned int)*(unsigned char *)reader->data++));
//         }
//         break;
//     case HASH_SInt16:
//     case HASH_short:
//         short *raw_list_s = (short *)reader->data;
//         for (int i = 0; i < vector_size; i++)
//         {
//             PyList_SetItem(list, i, PyLong_FromLong((int)*raw_list_s++));
//         }
//         reader->data = (char *)raw_list_s;
//         break;
//     case HASH_UInt16:
//     case HASH_unsigned_short:
//         unsigned short *raw_list_us = (unsigned short *)reader->data;
//         for (int i = 0; i < vector_size; i++)
//         {
//             PyList_SetItem(list, i, PyLong_FromUnsignedLong((unsigned int)*raw_list_us++));
//         }
//         reader->data = (char *)raw_list_us;
//         break;
//     case HASH_SInt32:
//     case HASH_int:
//         int *raw_list_i = (int *)reader->data;
//         for (int i = 0; i < vector_size; i++)
//         {
//             PyList_SetItem(list, i, PyLong_FromLong(*raw_list_i++));
//         }
//         reader->data = (char *)raw_list_i;
//         break;
//     case HASH_UInt32:
//     case HASH_unsigned_int:
//     case HASH_TypePtr:
//         unsigned int *raw_list_ui = (unsigned int *)reader->data;
//         for (int i = 0; i < vector_size; i++)
//         {
//             PyList_SetItem(list, i, PyLong_FromUnsignedLong(*raw_list_ui++));
//         }
//         reader->data = (char *)raw_list_ui;
//         break;
//     case HASH_SInt64:
//     case HASH_long_long:
//         long long *raw_list_l = (long long *)reader->data;
//         for (int i = 0; i < vector_size; i++)
//         {
//             PyList_SetItem(list, i, PyLong_FromLongLong(*raw_list_l++));
//         }
//         reader->data = (char *)raw_list_l;
//         break;
//     case HASH_UInt64:
//     case HASH_unsigned_long_long:
//     case HASH_FileSize:
//         unsigned long long *raw_list_ul = (unsigned long long *)reader->data;
//         for (int i = 0; i < vector_size; i++)
//         {
//             PyList_SetItem(list, i, PyLong_FromUnsignedLongLong(*raw_list_ul++));
//         }
//         reader->data = (char *)raw_list_ul;
//         break;
//     case HASH_float:
//         float *raw_list_f = (float *)reader->data;
//         for (int i = 0; i < vector_size; i++)
//         {
//             PyList_SetItem(list, i, PyFloat_FromDouble((double)*raw_list_f++));
//         }
//         reader->data = (char *)raw_list_f;
//         break;
//     case HASH_double:
//         double *raw_list_d = (double *)reader->data;
//         for (int i = 0; i < vector_size; i++)
//         {
//             PyList_SetItem(list, i, PyFloat_FromDouble(*raw_list_d++));
//         }
//         reader->data = (char *)raw_list_d;
//         break;
//     case HASH_bool:
//         for (int i = 0; i < vector_size; i++)
//         {
//             PyList_SetItem(list, i, PyBool_FromLong((int)*reader->data++));
//         }
//         break;
//     case HASH_string:
//         for (int i = 0; i < vector_size; i++)
//         {
//             int str_len = *(int *)reader->data;
//             reader->data += 4;
//             PyList_SetItem(list, i, PyUnicode_FromStringAndSize(reader->data, str_len));
//             reader->data += str_len;
//             if (align) align4(reader);
//         }
//         index += 3;
//         break;
//     case HASH_TypelessData:
//         for (int i = 0; i < vector_size; i++)
//         {
//             int str_len = *(int *)reader->data;
//             reader->data += 4;
//             PyList_SetItem(list, i, PyBytes_FromStringAndSize(reader->data, str_len));
//             reader->data += str_len;
//             if (align) align4(reader);

//         }
//         index += 2;
//         break;
//     case HASH_map:
//         if (node->meta_flag && kAnyChildUsesAlignBytesFlag)
//             align = 1;
//         *index += 4; // skip self, Array, size, pair
//         PyObject *first_nodes = getSubNodes(nodes, index);
//         *index += 1; // move to start of second
//         PyObject *second_nodes = getSubNodes(nodes, index);
//         int sub_index = 0;
//         for (int i = 0; i < vector_size; i++)
//         {
//             int size = (int)*(int *)reader->data;
//             reader->data += 4;
//             PyObject* item = PyList_New(size);
//             for (int j = 0; j < size; j++)
//             {
//                 sub_index = 0;
//                 PyObject* first = TypeTreeHelper_ReadValue(first_nodes, reader, &sub_index);
//                 sub_index = 0;
//                 PyObject* second = TypeTreeHelper_ReadValue(second_nodes, reader, &sub_index);
//                 PyList_SetItem(item, j, PyTuple_Pack(2, first, second));
//             }
//             PyList_SetItem(list, i, item);
//             if (align) align4(reader);
//         }
//         break;
//     default:
//         TypeTreeNodeObject *node2 = (TypeTreeNodeObject*) PyList_GetItem(nodes, *index + 1);
//         if (strcmp(node2->type, "Array") == 0)
//         {
//             if (node->meta_flag && kAnyChildUsesAlignBytesFlag)
//                 align = 1;
//             *index += 3; // skip self, Array, size
//             PyObject *vector_nodes = getSubNodes(nodes, index);

//             int sub_index = 0;
//             for (int i = 0; i < sub_index; i++){
//                 sub_index = 0;
//                 PyObject* item = TypeTreeHelper_ReadValueVector(vector_nodes, reader, &sub_index);
//                 PyList_SetItem(list, i, item);
//                 if (align) align4(reader);
//             }
//         }
//         else // Class
//         {
//             PyObject *cls_nodes = getSubNodes(nodes, index);
//             for (int i = 0; i < vector_size; i++)
//             {
//                 int j = 1;
//                 PyObject *value = PyDict_New();
//                 while (j < PyList_Size(cls_nodes))
//                 {
//                     PyDict_SetItemString(value, ((TypeTreeNodeObject*)PyList_GetItem(cls_nodes, j))->name, TypeTreeHelper_ReadValue(cls_nodes, reader, &j));
//                     j++;
//                 }
//                 PyList_SetItem(list, i, value);
//                 if (align) align4(reader);
//             }
//         }
//         break;
//     }

//     if (align) align4(reader);
//     return list;
// }

PyObject *read_typetree(PyObject *self, PyObject *args)
{
    PyObject *nodes = PyTuple_GetItem(args, 0);
    PyObject *buf = PyTuple_GetItem(args, 1);
    return TypeTreeHelper_ReadTypeTree(nodes, buf);
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