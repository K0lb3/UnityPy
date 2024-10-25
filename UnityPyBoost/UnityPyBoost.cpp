#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "Mesh.hpp"
#include "TypeTreeHelper.hpp"
#include "ArchiveStorageDecryptor.hpp"

/* Mesh.py */

static struct PyMethodDef method_table[] = {
    {"unpack_vertexdata",
     (PyCFunction)unpack_vertexdata,
     METH_VARARGS,
     "replacement for VertexData to ComponentData in Mesh.ReadVertexData"},
    {"read_typetree",
     (PyCFunction)read_typetree,
     METH_VARARGS | METH_KEYWORDS,
     "replacement for TypeTreeHelper.read_typetree"},
     {"decrypt_block",
     (PyCFunction)decrypt_block,
     METH_VARARGS,
     "replacement for ArchiveStorageDecryptor.decrypt_block"},
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
