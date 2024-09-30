#include <TypeTreeHelper.hpp>
#include <cstdint>
#include <type_traits>
#include <swap.hpp>
#include <map>

// TypeTreeReader - impl

typedef struct Reader
{
    uint8_t *ptr;
    uint8_t *end;
    uint8_t *start;
} ReaderT;

typedef struct TypeTreeReaderConfig
{
    bool as_dict;
    PyObject *classes;
    PyObject *assetfile;
    PyObject *clean_name;
} TypeTreeReaderConfigT;

inline void align4(ReaderT *reader)
{
    size_t offset = (size_t)reader->ptr - (size_t)reader->start;
    size_t aligned_offset = (offset + 4 - 1) & ~(4 - 1);
    reader->ptr = reader->start + aligned_offset;
}

inline PyObject *read_bool(ReaderT *reader)
{
    if (reader->ptr + 1 > reader->end)
    {
        PyErr_SetString(PyExc_ValueError, "read_bool out of bounds");
        return NULL;
    }
    return *reader->ptr++ ? Py_True : Py_False;
}

inline PyObject *read_u8(ReaderT *reader)
{
    if (reader->ptr + 1 > reader->end)
    {
        PyErr_SetString(PyExc_ValueError, "read_u8 out of bounds");
        return NULL;
    }
    return PyLong_FromUnsignedLong(*reader->ptr++);
}

inline PyObject *read_s8(ReaderT *reader)
{
    if (reader->ptr + 1 > reader->end)
    {
        PyErr_SetString(PyExc_ValueError, "read_s8 out of bounds");
        return NULL;
    }
    return PyLong_FromLong((int8_t)*reader->ptr++);
}

template <typename T, bool swap>
inline PyObject *read_int(ReaderT *reader)
{
    static_assert(std::is_integral<T>::value, "Unsupported type for read_int");

    if (reader->ptr + sizeof(T) > reader->end)
    {
        PyErr_SetString(PyExc_ValueError, "read_int out of bounds");
        return NULL;
    }
    T value = *(T *)reader->ptr;
    if constexpr (swap)
    {
        swap_any_inplace(&value);
    }
    reader->ptr += sizeof(T);
    if constexpr (std::is_signed<T>::value)
    {
        if constexpr (std::is_same<T, int64_t>::value)
        {
            return PyLong_FromLongLong(value);
        }
        else
        {
            return PyLong_FromLong((int32_t)value);
        }
    }
    else
    {
        if constexpr (std::is_same<T, uint64_t>::value)
        {
            return PyLong_FromUnsignedLongLong(value);
        }
        else
        {
            return PyLong_FromUnsignedLong((uint32_t)value);
        }
    }
}

template <typename T, bool swap>
inline PyObject *read_float(ReaderT *reader)
{
    static_assert(std::is_floating_point<T>::value, "Unsupported type for read_float");

    if (reader->ptr + sizeof(T) > reader->end)
    {
        PyErr_SetString(PyExc_ValueError, "read_float out of bounds");
        return NULL;
    }
    T value = *(T *)reader->ptr;
    if constexpr (swap)
    {
        swap_any_inplace(&value);
    }
    reader->ptr += sizeof(T);
    return PyFloat_FromDouble(value);
}

template <bool swap>
inline bool _read_length(ReaderT *reader, int32_t *length)
{
    if (reader->ptr + sizeof(int32_t) > reader->end)
    {
        PyErr_SetString(PyExc_ValueError, "read_length out of bounds");
        return false;
    }
    *length = *(int32_t *)reader->ptr;
    if constexpr (swap)
    {
        swap_any_inplace(length);
    }
    reader->ptr += sizeof(int32_t);
    return true;
}

template <bool swap>
inline PyObject *read_str(ReaderT *reader)
{
    int32_t length;
    if (!_read_length<swap>(reader, &length))
    {
        return NULL;
    }
    if (reader->ptr + length > reader->end)
    {
        PyErr_SetString(PyExc_ValueError, "read_str out of bounds");
        return NULL;
    }
    PyObject *str = PyUnicode_DecodeUTF8((char *)reader->ptr, length, "surrogateescape");
    reader->ptr += length;
    align4(reader);
    return str;
}

template <bool swap>
inline PyObject *read_bytes(ReaderT *reader)
{
    int32_t length;
    if (!_read_length<swap>(reader, &length))
    {
        return NULL;
    }
    if (reader->ptr + length > reader->end)
    {
        PyErr_SetString(PyExc_ValueError, "read_bytes out of bounds");
        return NULL;
    }
    PyObject *bytes = PyBytes_FromStringAndSize((char *)reader->ptr, length);
    reader->ptr += length;
    return bytes;
}

template <bool swap>
inline PyObject *read_pair(ReaderT *reader, TypeTreeNodeObject *node, TypeTreeReaderConfigT *config)
{
    if (PyList_GET_SIZE(node->m_Children) != 2)
    {
        PyErr_SetString(PyExc_ValueError, "Pair node must have 2 children");
        return NULL;
    }

    PyObject *first = read_typetree_value<swap>(reader, (TypeTreeNodeObject *)PyList_GET_ITEM(node->m_Children, 0), config);
    if (!first)
    {
        return NULL;
    }
    PyObject *second = read_typetree_value<swap>(reader, (TypeTreeNodeObject *)PyList_GET_ITEM(node->m_Children, 1), config);
    if (!second)
    {
        Py_DECREF(first);
        return NULL;
    }
    PyObject *pair = PyTuple_Pack(2, first, second);
    Py_DECREF(first);
    Py_DECREF(second);
    return pair;
}

template <bool swap>
inline PyObject *parse_class(ReaderT *reader, PyObject *dict, TypeTreeNodeObject *node, TypeTreeReaderConfigT *config)
{
    PyObject *clz = NULL;

    // Determine the class based on node's _data_type
    if (node->_data_type == NodeDataType::pptr)
    {
        if (PyDict_SetItemString(dict, "assetsfile", config->assetfile) != 0)
        {
            PyErr_SetString(PyExc_RuntimeError, "Failed to set 'assetsfile'");
            Py_DECREF(dict);
            return NULL;
        }
        clz = PyObject_GetAttrString(config->classes, "PPtr");
    }
    else
    {
        clz = PyObject_GetAttr(config->classes, node->m_Type);
        if (clz == NULL)
        {
            clz = PyObject_GetAttrString(config->classes, "Object");
        }
    }

    // check if class is found
    if (clz == NULL)
    {
        PyErr_SetString(PyExc_ValueError, "Failed to get class");
        Py_DECREF(clz);
        Py_DECREF(dict);
        return NULL;
    }

    // try to create class instance
    PyObject *args = PyTuple_New(0);
    PyObject *instance = PyObject_Call(clz, args, dict);
    if (instance != NULL)
    {
        // success
        // cleanup
        Py_DECREF(clz);
        Py_DECREF(args);
        Py_DECREF(dict);
        // return instance
        return instance;
    }
    // failed, clear error
    PyErr_Clear();

    // clean key names
    PyObject *key = NULL;
    PyObject *keys = PyDict_Keys(dict);
    PyObject *clean_args = PyTuple_New(1);
    for (Py_ssize_t i = 0; i < PyList_GET_SIZE(keys); i++)
    {
        key = PyList_GET_ITEM(keys, i);
        PyTuple_SET_ITEM(clean_args, 0, key);
        PyObject *clean_key = PyObject_Call(config->clean_name, clean_args, NULL);
        if (PyUnicode_Compare(key, clean_key))
        {
            PyObject *value = PyDict_GetItem(dict, key);
            PyDict_SetItem(dict, clean_key, value);
            PyDict_DelItem(dict, key);
        }
        Py_DECREF(clean_key);
    }
    // increase ref count for key, as PyTuple_SET_ITEM steals reference, so decref there will decref key
    Py_INCREF(key);
    Py_DECREF(clean_args);
    Py_DECREF(keys);

    // try to create class instance again with cleaned keys
    instance = PyObject_Call(clz, args, dict);
    if (instance != NULL)
    {
        // success
        // cleanup
        Py_DECREF(clz);
        Py_DECREF(args);
        Py_DECREF(dict);
        // return instance
        return instance;
    }
    // failed, clear error
    PyErr_Clear();

    // some keys might be extra, check against __annotations__
    PyObject *annonations = PyObject_GetAttrString(clz, "__annotations__");
    PyObject *extras = PyDict_New();
    keys = PyDict_Keys(dict);
    for (Py_ssize_t i = 0; i < PyList_Size(keys); i++)
    {
        PyObject *key = PyList_GET_ITEM(keys, i);
        if (PyDict_Contains(annonations, key) == 0)
        {
            PyObject *value = PyDict_GetItem(dict, key);
            PyDict_SetItem(extras, key, value);
            PyDict_DelItem(dict, key);
        }
    }
    Py_DECREF(keys);
    Py_DECREF(annonations);

    // try to create class instance again with cleaned keys
    instance = PyObject_Call(clz, args, dict);
    if (instance != NULL)
    {
        // success, manually set extra keys
        PyObject *items = PyDict_Items(extras);
        for (Py_ssize_t i = 0; i < PyList_Size(items); i++)
        {
            PyObject *item = PyList_GET_ITEM(items, i);
            PyObject *key = PyTuple_GetItem(item, 0);
            PyObject *value = PyTuple_GetItem(item, 1);
            PyObject_SetAttr(instance, key, value);
        }
        Py_DECREF(items);
    }
    // cleanup
    Py_DECREF(clz);
    Py_DECREF(args);
    Py_DECREF(dict);
    Py_DECREF(extras);
    // return instance or NULL if failed
    return instance;
}

template <bool swap>
PyObject *read_typetree_value(ReaderT *reader, TypeTreeNodeObject *node, TypeTreeReaderConfigT *config)
{
    bool align = node->_align;
    PyObject *value = nullptr;

    switch (node->_data_type)
    {
    case NodeDataType::u8:
        value = read_u8(reader);
        break;
    case NodeDataType::u16:
        value = read_int<uint16_t, swap>(reader);
        break;
    case NodeDataType::u32:
        value = read_int<uint32_t, swap>(reader);
        break;
    case NodeDataType::u64:
        value = read_int<uint64_t, swap>(reader);
        break;
    case NodeDataType::s8:
        value = read_s8(reader);
        break;
    case NodeDataType::s16:
        value = read_int<int16_t, swap>(reader);
        break;
    case NodeDataType::s32:
        value = read_int<int32_t, swap>(reader);
        break;
    case NodeDataType::s64:
        value = read_int<int64_t, swap>(reader);
        break;
    case NodeDataType::f32:
        value = read_float<float, swap>(reader);
        break;
    case NodeDataType::f64:
        value = read_float<double, swap>(reader);
        break;
    case NodeDataType::boolean:
        value = read_bool(reader);
        break;
    case NodeDataType::str:
        value = read_str<swap>(reader);
        break;
    case NodeDataType::bytes:
        value = read_bytes<swap>(reader);
        break;
    case NodeDataType::pair:
        value = read_pair<swap>(reader, node, config);
        break;
    default:
        TypeTreeNodeObject *child = nullptr;
        if (PyList_GET_SIZE(node->m_Children) > 0)
        {
            child = (TypeTreeNodeObject *)PyList_GET_ITEM(node->m_Children, 0);
        }

        if (child && child->_data_type == NodeDataType::array)
        {
            // array
            if (child->_align)
            {
                align = true;
            }
            int32_t length;
            if (!_read_length<swap>(reader, &length))
            {
                return NULL;
            }
            value = PyList_New(length);
            child = (TypeTreeNodeObject *)PyList_GET_ITEM(child->m_Children, 1);
            for (int i = 0; i < length; i++)
            {
                PyObject *item = read_typetree_value<swap>(reader, child, config);
                if (!item)
                {
                    Py_DECREF(value);
                    return NULL;
                }
                PyList_SET_ITEM(value, i, item);
            }
        }
        else
        {
            // class
            value = PyDict_New();
            for (int i = 0; i < PyList_GET_SIZE(node->m_Children); i++)
            {
                child = (TypeTreeNodeObject *)PyList_GET_ITEM(node->m_Children, i);
                PyObject *child_value = read_typetree_value<swap>(reader, child, config);
                if (!child_value)
                {
                    Py_DECREF(value);
                    return NULL;
                }
                if (PyDict_SetItem(value, child->m_Name, child_value))
                {
                    Py_DECREF(value);
                    Py_DECREF(child_value);
                    return NULL;
                }
                // dict increases ref count, so we need to decref here
                Py_DECREF(child_value);
            }
            if (!config->as_dict)
            {
                value = parse_class<swap>(reader, value, node, config);
            }
        }
    }

    if (align)
    {
        align4(reader);
    }

    return value;
}

PyObject *read_typetree(PyObject *self, PyObject *args, PyObject *kwargs)
{
    const char *kwlist[] = {"data", "node", "endian", "as_dict", "assetsfile", "classes", "clean_name", NULL};
    PyObject *data;
    PyObject *node;
    PyObject *as_dict = Py_True;

    TypeTreeReaderConfigT config = {
        false,
        Py_None,
        Py_None,
        Py_None};

    char endian;
    bool swap;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "OOC|OOOO", (char **)kwlist, &data, &node, &endian, &as_dict, &config.assetfile, &config.classes, &config.clean_name))
    {
        return NULL;
    }

    config.as_dict = as_dict == Py_True;
    if (!config.as_dict)
    {
        if (PyCallable_Check(config.clean_name) == 0)
        {
            PyErr_SetString(PyExc_ValueError, "clean_name must be callable if not as dict");
            return NULL;
        }
        if (config.assetfile == Py_None)
        {
            PyErr_SetString(PyExc_ValueError, "assetsfile must be set if not as dict");
            return NULL;
        }
        if (config.classes == Py_None)
        {
            PyErr_SetString(PyExc_ValueError, "classes must be set if not as dict");
            return NULL;
        }
    }
    Py_INCREF(config.assetfile);
    Py_INCREF(config.classes);
    Py_INCREF(config.clean_name);

    volatile uint16_t bint = 0x0100;
    volatile bool is_big_endian = ((uint8_t *)&bint)[0] == 1;

    switch (endian)
    {
    case '<':
        if (is_big_endian)
        {
            swap = true;
        }
        else
        {
            swap = false;
        }
        break;
    case '>':
        if (is_big_endian)
        {
            swap = false;
        }
        else
        {
            swap = true;
        }
        break;
    default:
        PyErr_SetString(PyExc_ValueError, "Invalid endian");
        break;
    }
    Py_buffer view;

    if (PyObject_GetBuffer(data, &view, PyBUF_SIMPLE) == -1)
    {
        PyErr_SetString(PyExc_ValueError, "Failed to get buffer");
        return NULL;
    }
    ReaderT reader = {static_cast<uint8_t *>(view.buf), static_cast<uint8_t *>(view.buf) + view.len, static_cast<uint8_t *>(view.buf)};

    PyObject *value;
    if (swap)
    {
        value = read_typetree_value<true>(&reader, (TypeTreeNodeObject *)node, &config);
    }
    else
    {
        value = read_typetree_value<false>(&reader, (TypeTreeNodeObject *)node, &config);
    }

    PyBuffer_Release(&view);

    return value;
}

// TypeTreeNode impl
static void TypeTreeNode_dealloc(TypeTreeNodeObject *self)
{
    Py_XDECREF(self->m_Level);
    Py_XDECREF(self->m_Type);
    Py_XDECREF(self->m_Name);
    Py_XDECREF(self->m_ByteSize);
    Py_XDECREF(self->m_TypeFlags);
    Py_XDECREF(self->m_Version);
    Py_XDECREF(self->m_VariableCount);
    Py_XDECREF(self->m_Index);
    Py_XDECREF(self->m_MetaFlag);
    Py_XDECREF(self->m_RefTypeHash);
    Py_XDECREF(self->m_Children);
    Py_TYPE(self)->tp_free((PyObject *)self);
}

static const std::map<const char *, NodeDataType> typeToNodeDataType = {
    {"SInt8", NodeDataType::s8},
    {"UInt8", NodeDataType::u8},
    {"char", NodeDataType::u8},
    {"short", NodeDataType::s16},
    {"SInt16", NodeDataType::s16},
    {"unsigned short", NodeDataType::u16},
    {"UInt16", NodeDataType::u16},
    {"int", NodeDataType::s32},
    {"SInt32", NodeDataType::s32},
    {"unsigned int", NodeDataType::u32},
    {"UInt32", NodeDataType::u32},
    {"Type*", NodeDataType::u32},
    {"long long", NodeDataType::s64},
    {"SInt64", NodeDataType::s64},
    {"unsigned long long", NodeDataType::u64},
    {"UInt64", NodeDataType::u64},
    {"FileSignature", NodeDataType::u64},
    {"float", NodeDataType::f32},
    {"double", NodeDataType::f64},
    {"bool", NodeDataType::boolean},
    {"string", NodeDataType::str},
    {"TypelessData", NodeDataType::bytes},
    {"pair", NodeDataType::pair},
    {"Array", NodeDataType::array},
};

static int TypeTreeNode_init(TypeTreeNodeObject *self, PyObject *args, PyObject *kwargs)
{
    const char *kwlist[] = {
        "m_Level",
        "m_Type",
        "m_Name",
        "m_ByteSize",
        "m_Version",
        "m_Children",
        "m_TypeFlags",
        "m_VariableCount",
        "m_Index",
        "m_MetaFlag",
        "m_RefTypeHash",
        NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "OOOOO|OOOOOO", (char **)kwlist,
                                     &self->m_Level,
                                     &self->m_Type,
                                     &self->m_Name,
                                     &self->m_ByteSize,
                                     &self->m_Version,
                                     &self->m_Children,
                                     &self->m_TypeFlags,
                                     &self->m_VariableCount,
                                     &self->m_Index,
                                     &self->m_MetaFlag,
                                     &self->m_RefTypeHash))
    {
        return -1;
    }

    Py_INCREF(self->m_Level);
    Py_INCREF(self->m_Type);
    Py_INCREF(self->m_Name);
    Py_INCREF(self->m_ByteSize);
    Py_INCREF(self->m_Version);
    // optional fields
    if (self->m_Children == nullptr)
    {
        self->m_Children = PyList_New(0);
    }
    else
    {
        Py_XINCREF(self->m_Children);
    }

#define SET_NONE_IF_NULL(field)     \
    {                               \
        if (self->field == nullptr) \
        {                           \
            self->field = Py_None;  \
        }                           \
        Py_INCREF(self->field);     \
    }

    SET_NONE_IF_NULL(m_TypeFlags);
    SET_NONE_IF_NULL(m_VariableCount);
    SET_NONE_IF_NULL(m_Index);
    SET_NONE_IF_NULL(m_MetaFlag);
    SET_NONE_IF_NULL(m_RefTypeHash);

    if (self->m_MetaFlag != Py_None && PyLong_AsLong(self->m_MetaFlag) & 0x4000)
    {
        self->_align = true;
    }

    if (self->m_Type != Py_None)
    {
        const char *type = PyUnicode_AsUTF8(self->m_Type);
        self->_data_type = NodeDataType::unk;
        if (type[0] == 'P' && type[1] == 'P' && type[2] == 't' && type[3] == 'r' && type[4] == '<')
        {
            self->_data_type = NodeDataType::pptr;
        }
        else
        {
            for (auto it = typeToNodeDataType.begin(); it != typeToNodeDataType.end(); ++it)
            {
                if (strcmp(it->first, type) == 0)
                {
                    self->_data_type = it->second;
                    break;
                }
            }
        }
    }

    return 0;
}

static PyMemberDef TypeTreeNode_members[] = {
    {"m_Level", T_OBJECT_EX, offsetof(TypeTreeNodeObject, m_Level), 0, ""},
    {"m_Type", T_OBJECT_EX, offsetof(TypeTreeNodeObject, m_Type), 0, ""},
    {"m_Name", T_OBJECT_EX, offsetof(TypeTreeNodeObject, m_Name), 0, ""},
    {"m_ByteSize", T_OBJECT_EX, offsetof(TypeTreeNodeObject, m_ByteSize), 0, ""},
    {"m_TypeFlags", T_OBJECT_EX, offsetof(TypeTreeNodeObject, m_TypeFlags), 0, ""},
    {"m_Version", T_OBJECT_EX, offsetof(TypeTreeNodeObject, m_Version), 0, ""},
    {"m_Children", T_OBJECT_EX, offsetof(TypeTreeNodeObject, m_Children), 0, ""},
    {"m_VariableCount", T_OBJECT_EX, offsetof(TypeTreeNodeObject, m_VariableCount), 0, ""},
    {"m_Index", T_OBJECT_EX, offsetof(TypeTreeNodeObject, m_Index), 0, ""},
    {"m_MetaFlag", T_OBJECT_EX, offsetof(TypeTreeNodeObject, m_MetaFlag), 0, ""},
    {"m_RefTypeHash", T_OBJECT_EX, offsetof(TypeTreeNodeObject, m_RefTypeHash), 0, ""},
    {NULL} /* Sentinel */
};

static PyTypeObject TypeTreeNodeType = []() -> PyTypeObject
{
    PyTypeObject type = {PyObject_HEAD_INIT(NULL) 0};
    type.tp_name = "TypeTreeHelper.TypeTreeNode";
    type.tp_doc = "TypeTreeNode objects";
    type.tp_basicsize = sizeof(TypeTreeNodeObject);
    type.tp_itemsize = 0;
    type.tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE;
    type.tp_new = PyType_GenericNew;
    type.tp_init = (initproc)TypeTreeNode_init;
    type.tp_dealloc = (destructor)TypeTreeNode_dealloc;
    type.tp_members = TypeTreeNode_members;
    return type;
}();

int add_typetreenode_to_module(PyObject *m)
{
    if (PyType_Ready(&TypeTreeNodeType) < 0)
        return -1;
    Py_INCREF(&TypeTreeNodeType);
    PyModule_AddObject(m, "TypeTreeNode", (PyObject *)&TypeTreeNodeType);
    return 0;
}
