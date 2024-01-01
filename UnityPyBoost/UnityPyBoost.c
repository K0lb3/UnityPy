#define PY_SSIZE_T_CLEAN
#pragma once
#include <Python.h>
#include "AnimationClip.h"
#include "Mesh.h"
#include "TextureSwizzler.h"
#include "TypeTreeHelper.h"

/* Mesh.py */

static struct PyMethodDef method_table[] = {
    {"unpack_floats",
     (PyCFunction)unpack_floats,
     METH_VARARGS,
     "replacement for PackedFloatVector.unpack_floats"},
    {"unpack_ints",
     (PyCFunction)unpack_ints,
     METH_VARARGS,
     "replacement for PackedIntVector.unpack_ints"},
    {"unpack_vertexdata",
     (PyCFunction)unpack_vertexdata,
     METH_VARARGS,
     "replacement for VertexData to ComponentData in Mesh.ReadVertexData"},
    {"read_typetree",
     (PyCFunction)read_typetree,
     METH_VARARGS,
     "replacement for TypeTreeHelper.read_typetree"},
    {"switch_deswizzle",
     (PyCFunction)switch_deswizzle,
     METH_VARARGS,
     "replacement for TextureSwizzler.switch_deswizzle"},
    {NULL,
     NULL,
     0,
     NULL} // Sentinel value ending the table
};

// A struct contains the definition of a module
static PyModuleDef UnityPyBoost_module = {
    PyModuleDef_HEAD_INIT,
    "UnityPyBoost", // Module name
    "TODO",
    -1, // Optional size of the module state memory
    method_table,
    NULL, // Optional slot definitions
    NULL, // Optional traversal function
    NULL, // Optional clear function
    NULL  // Optional module deallocation function
};

// The module init function
PyMODINIT_FUNC PyInit_UnityPyBoost(void)
{
    PyObject *module = PyModule_Create(&UnityPyBoost_module);
    add_typetreenode_to_module(module);
    return module;
}