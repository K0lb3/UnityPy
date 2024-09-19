#define PY_SSIZE_T_CLEAN
#pragma once
#include "AnimationClip.hpp"
#include <Python.h>

PyObject *unpack_vertexdata(PyObject *self, PyObject *args);