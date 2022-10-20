#define PY_SSIZE_T_CLEAN
#pragma once
#include <Python.h>
#include "structmember.h"

typedef struct TypeTreeNodeObject{
    PyObject_HEAD
    short m_Version;
    unsigned char m_Level;
    int m_TypeFlags;
    int m_ByteSize;
    int m_Index;
    int m_MetaFlag;
    char *m_Type;
    char *m_Name;
    //unsigned short children_count;
    //struct TypeTreeNodeObject **children;
    // UnityFS
    unsigned int m_TypeStrOffset;
    unsigned int m_NameStrOffset;
    // UnityFS - version >= 19
    unsigned long long m_RefTypeHash;
    // UnityRaw - versin = 2
    int m_VariableCount;
    // helper fields
    unsigned int typehash;
} TypeTreeNodeObject;

int add_typetreenode_to_module(PyObject *m);

PyObject* read_typetree(PyObject *self, PyObject *args);