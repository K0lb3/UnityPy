#define PY_SSIZE_T_CLEAN
#pragma once
#include <Python.h>
#include "structmember.h"
#include <vector>

enum NodeDataType
{
    u8 = 0,
    u16 = 1,
    u32 = 2,
    u64 = 3,
    s8 = 4,
    s16 = 5,
    s32 = 6,
    s64 = 7,
    f32 = 8,
    f64 = 9,
    boolean = 10,
    str = 11,
    bytes = 12,
    pair = 13,
    array = 14,
    pptr = 15,
    unk = 255
};

typedef struct TypeTreeNodeObject
{
    PyObject_HEAD
        // helper field - simple hash of type for faster comparison
        unsigned int _data_type;
        bool _align;
    // used filds for fast access
    PyObject* m_Children;
    PyObject *m_Name;
    // fields not used in C
    PyObject *m_Level;
    PyObject *m_Type;
    PyObject *m_ByteSize;
    PyObject *m_Version;
    PyObject *m_TypeFlags;
    PyObject *m_VariableCount;
    PyObject *m_Index;
    PyObject *m_MetaFlag;
    PyObject *m_RefTypeHash;
} TypeTreeNodeObject;

int add_typetreenode_to_module(PyObject *m);

PyObject *read_typetree(PyObject *self, PyObject *args, PyObject *kwargs);
