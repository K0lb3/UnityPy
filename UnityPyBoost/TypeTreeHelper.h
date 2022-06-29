#define PY_SSIZE_T_CLEAN
#pragma once
#include <Python.h>
#include "structmember.h"

typedef struct TypeTreeNodeObject{
    PyObject_HEAD
    short version;
    unsigned char level;
    char is_array;
    int byte_size;
    int index;
    int meta_flag;
    char *type;
    char *name;
    unsigned short children_count;
    //struct TypeTreeNodeObject **children;
    // UnityFS
    unsigned int type_str_offset;
    unsigned int name_str_offset;
    // UnityFS - version >= 19
    unsigned long long ref_type_hash;
    // UnityRaw - versin = 2
    int variable_count;
} TypeTreeNodeObject;

int add_typetreenode_to_module(PyObject *m);

PyObject* read_typetree(PyObject *self, PyObject *args);