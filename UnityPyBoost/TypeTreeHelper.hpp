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
    Array = 14,
    PPtr = 15,
    ReferencedObject = 16,
    ReferencedObjectData = 17,
    ManagedReferencesRegistry = 18,
    unk = 255
};

typedef struct TypeTreeNodeObject
{
    PyObject_HEAD
        // helper field - simple hash of type for faster comparison
        NodeDataType _data_type;
    bool _align;
    PyObject *_clean_name; // str
    // used filds for fast access
    PyObject *m_Children; // list of TypeTreeNodes
    PyObject *m_Name;     // str
    PyObject *m_Type;     // str
    // fields not used in C
    PyObject *m_Level;         // legacy: /,   blob: u8
    PyObject *m_ByteSize;      // legacy: i32, blob: i32
    PyObject *m_Version;       // legacy: i32, blob: i16
    PyObject *m_TypeFlags;     // legacy: i32, blob: u8
    PyObject *m_VariableCount; // legacy: i32, blob: /
    PyObject *m_Index;         // legacy: i32, blob: i32
    PyObject *m_MetaFlag;      // legacy: i32, blob: i32
    PyObject *m_RefTypeHash;   // legacy: /,   blob: u64
} TypeTreeNodeObject;

int add_typetreenode_to_module(PyObject *m);

PyObject *read_typetree(PyObject *self, PyObject *args, PyObject *kwargs);
