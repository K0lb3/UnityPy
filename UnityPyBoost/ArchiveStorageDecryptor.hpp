#define PY_SSIZE_T_CLEAN
#pragma once
#include <Python.h>

PyObject *decrypt_block(PyObject *self, PyObject *args);
