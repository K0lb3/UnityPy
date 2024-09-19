#define PY_SSIZE_T_CLEAN
#pragma once
#include <Python.h>
PyObject *unpack_floats(PyObject *self, PyObject *args);
PyObject *unpack_ints(PyObject *self, PyObject *args);