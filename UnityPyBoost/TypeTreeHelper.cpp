#include <algorithm>
#include <cstdint>
#include <map>
#include <type_traits>
#include <string>
#include <regex>

#include "swap.hpp"
#include "TypeTreeHelper.hpp"

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
    bool has_registry;
} TypeTreeReaderConfigT;

std::string clean_name(const std::string &name)
{
    // # keep in sync with TypeTreeNode.py
    std::string cleaned_name = name;
    if (cleaned_name.empty())
    {
        return cleaned_name;
    }

    // Remove "(int&)" prefix
    if (cleaned_name.substr(0, 6) == "(int&)")
    {
        cleaned_name = cleaned_name.substr(6);
    }

    // Remove trailing "?"
    if (!cleaned_name.empty() && cleaned_name.back() == '?')
    {
        cleaned_name.pop_back();
    }

    // Replace certain characters with "_"
    cleaned_name = std::regex_replace(cleaned_name, std::regex("[ \\.:\\-\\[\\]]"), "_");

    // Append "_" if the name is "pass" or "from"
    if (cleaned_name == "pass" || cleaned_name == "from")
    {
        cleaned_name += "_";
    }

    // Prefix with "x" if the name starts with a digit
    if (!cleaned_name.empty() && isdigit(cleaned_name[0]))
    {
        cleaned_name = "x" + cleaned_name;
    }

    return cleaned_name;
}

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
    PyObject *value = *reader->ptr++ ? Py_True : Py_False;
    Py_INCREF(value);
    return value;
}

inline PyObject *read_bool_array(ReaderT *reader, int32_t count)
{
    if (reader->ptr + count > reader->end)
    {
        PyErr_SetString(PyExc_ValueError, "read_bool out of bounds");
        return NULL;
    }
    PyObject *list = PyList_New(count);
    for (auto i = 0; i < count; i++)
    {
        PyObject *value = *reader->ptr++ ? Py_True : Py_False;
        Py_INCREF(value);
        PyList_SET_ITEM(list, i, value);
    }
    return list;
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

inline PyObject *read_u8_array(ReaderT *reader, int32_t count)
{
    if (reader->ptr + count > reader->end)
    {
        PyErr_SetString(PyExc_ValueError, "read_u8 out of bounds");
        return NULL;
    }
    PyObject *list = PyList_New(count);
    for (auto i = 0; i < count; i++)
    {
        PyList_SET_ITEM(list, i, PyLong_FromUnsignedLong(*reader->ptr++));
    }
    return list;
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

inline PyObject *read_s8_array(ReaderT *reader, int32_t count)
{
    if (reader->ptr + count > reader->end)
    {
        PyErr_SetString(PyExc_ValueError, "read_s8 out of bounds");
        return NULL;
    }
    PyObject *list = PyList_New(count);
    int8_t *ptr = (int8_t *)reader->ptr;
    for (auto i = 0; i < count; i++)
    {
        PyList_SET_ITEM(list, i, PyLong_FromLong(*ptr++));
    }
    reader->ptr = (uint8_t *)ptr;
    return list;
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
inline PyObject *read_int_array(ReaderT *reader, int32_t count)
{
    static_assert(std::is_integral<T>::value, "Unsupported type for read_int_array");

    if (reader->ptr + sizeof(T) * count > reader->end)
    {
        PyErr_SetString(PyExc_ValueError, "read_int_array out of bounds");
        return NULL;
    }
    PyObject *list = PyList_New(count);
    T *ptr = (T *)reader->ptr;
    for (auto i = 0; i < count; i++)
    {
        T value = *ptr++;
        if constexpr (swap)
        {
            swap_any_inplace(&value);
        }
        if constexpr (std::is_signed<T>::value)
        {
            if constexpr (std::is_same<T, int64_t>::value)
            {
                PyList_SET_ITEM(list, i, PyLong_FromLongLong(value));
            }
            else
            {
                PyList_SET_ITEM(list, i, PyLong_FromLong((int32_t)value));
            }
        }
        else
        {
            if constexpr (std::is_same<T, uint64_t>::value)
            {
                PyList_SET_ITEM(list, i, PyLong_FromUnsignedLongLong(value));
            }
            else
            {
                PyList_SET_ITEM(list, i, PyLong_FromUnsignedLong((uint32_t)value));
            }
        }
    }
    reader->ptr = (uint8_t *)ptr;
    return list;
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

template <typename T, bool swap>
inline PyObject *read_float_array(ReaderT *reader, int32_t count)
{
    static_assert(std::is_floating_point<T>::value, "Unsupported type for read_float_array");

    if (reader->ptr + sizeof(T) * count > reader->end)
    {
        PyErr_SetString(PyExc_ValueError, "read_float_array out of bounds");
        return NULL;
    }
    T *ptr = (T *)reader->ptr;
    PyObject *list = PyList_New(count);
    for (auto i = 0; i < count; i++)
    {
        T value = *ptr++;
        if constexpr (swap)
        {
            swap_any_inplace(&value);
        }
        PyList_SET_ITEM(list, i, PyFloat_FromDouble(value));
    }
    reader->ptr = (uint8_t *)ptr;
    return list;
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
    PyObject *py_str = PyUnicode_DecodeUTF8((char *)reader->ptr, length, "surrogateescape");
    reader->ptr += length;
    align4(reader);
    return py_str;
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
    // PyTuple_Pack creates two strong references
    PyObject *pair = PyTuple_Pack(2, first, second);
    // so we need to decref both values here to bring their ref count back to 1
    Py_DECREF(first);
    Py_DECREF(second);
    return pair;
}

template <bool swap>
inline PyObject *read_pair_array(ReaderT *reader, TypeTreeNodeObject *node, TypeTreeReaderConfigT *config, int32_t count)
{
    if (PyList_GET_SIZE(node->m_Children) != 2)
    {
        PyErr_SetString(PyExc_ValueError, "Pair node must have 2 children");
        return NULL;
    }

    TypeTreeNodeObject *first_child = (TypeTreeNodeObject *)PyList_GET_ITEM(node->m_Children, 0);
    TypeTreeNodeObject *second_child = (TypeTreeNodeObject *)PyList_GET_ITEM(node->m_Children, 1);

    PyObject *list = PyList_New(count);
    for (auto i = 0; i < count; i++)
    {
        PyObject *first = read_typetree_value<swap>(reader, first_child, config);
        if (!first)
        {
            Py_DECREF(list);
            return NULL;
        }
        PyObject *second = read_typetree_value<swap>(reader, second_child, config);
        if (!second)
        {
            Py_DECREF(first);
            Py_DECREF(list);
            return NULL;
        }
        PyList_SET_ITEM(list, i, PyTuple_Pack(2, first, second)); // pack creates two strong references
        // so we need to decref both values here to bring their ref count back to 1
        Py_DECREF(first);
        Py_DECREF(second);
    }

    return list;
}

template <bool swap, bool as_dict>
inline PyObject *read_class(ReaderT *reader, TypeTreeNodeObject *node, TypeTreeReaderConfigT *config)
{
    bool changed_registry = false;
    PyObject *value = PyDict_New(); // value: 1 refcount
    for (int i = 0; i < PyList_GET_SIZE(node->m_Children); i++)
    {
        TypeTreeNodeObject *child = (TypeTreeNodeObject *)PyList_GET_ITEM(node->m_Children, i); // no refcount change
        if (child->_data_type == NodeDataType::ManagedReferencesRegistry)
        {
            if (config->has_registry)
            {
                continue;
            }
            else
            {
                changed_registry = true;
                config->has_registry = true;
            }
        }
        PyObject *child_value = read_typetree_value<swap>(reader, child, config); // child_value: 1 refcount
        if (!child_value)
        {
            Py_DECREF(value); // value: 0 refcount
            return NULL;
        }
        int set_item_result;
        if constexpr (as_dict == true)
        {
            set_item_result = PyDict_SetItem(value, child->m_Name, child_value); // child_value: 2 refcount
        }
        else
        {
            set_item_result = PyDict_SetItem(value, child->_clean_name, child_value); // child_value: 2 refcount
        }
        if (set_item_result != 0)
        {
            Py_DECREF(value);       // value: 0 refcount
            Py_DECREF(child_value); // child_value: 0 refcount
            return NULL;
        }
        // PyDict_SetItem increases ref count, so we need to decref here
        Py_DECREF(child_value); // child_value: 1 refcount
    }

    if (changed_registry)
    {
        config->has_registry = false;
    }

    return value;
}

#if PY_VERSION_HEX >= 0x030e0000
PyObject *get_annotations = nullptr;
#endif

inline PyObject *get_annotations(PyObject *clz)
{
#if PY_VERSION_HEX >= 0x030e0000
    if (get_annotations == nullptr)
    {
        // from annotationlib import get_annotations
        PyObject *annotationlib = PyImport_ImportModule("annotationlib");
        get_annotations = PyObject_GetAttrString(annotationlib, "get_annotations");
        Py_INCREF(get_annotations);
        Py_DECREF(annotationlib);
    }
    return PyObject_CallFunctionObjArgs(get_annotations, clz, NULL);
#else
    return PyObject_GetAttrString(clz, "__annotations__");
#endif
}

inline PyObject *parse_class(PyObject *kwargs, TypeTreeNodeObject *node, TypeTreeReaderConfigT *config)
{
    PyObject *instance = nullptr;
    PyObject *clz = nullptr;
    PyObject *args = PyTuple_New(0);
    PyObject *annotations = nullptr;
    PyObject *extras = nullptr;
    // dict iterator values
    PyObject *key, *value = nullptr;
    Py_ssize_t pos;

    if (node->_data_type == NodeDataType::PPtr)
    {
        clz = PyObject_GetAttrString(config->classes, "PPtr");
        if (clz == nullptr)
        {
            PyErr_SetString(PyExc_ValueError, "Failed to get PPtr class");
            goto PARSE_CLASS_CLEANUP;
        }
        PyDict_SetItemString(kwargs, "assetsfile", config->assetfile);
    }
    else
    {
        clz = PyObject_GetAttr(config->classes, node->m_Type);
        if (clz == nullptr)
        {
            clz = PyObject_GetAttrString(config->classes, "UnknownObject");
            if (clz == nullptr)
            {
                PyErr_SetString(PyExc_ValueError, "Failed to get UnknownObject class");
                goto PARSE_CLASS_CLEANUP;
            }
            PyDict_SetItemString(kwargs, "__node__", (PyObject *)node);
        }
    }

    instance = PyObject_Call(clz, args, kwargs);
    if (instance != nullptr)
    {
        goto PARSE_CLASS_CLEANUP;
    }
    PyErr_Clear();

    // possibly extra fields
    annotations = get_annotations(clz);
    if (annotations == nullptr)
    {
        PyErr_SetString(PyExc_ValueError, "Failed to get annotations");
        goto PARSE_CLASS_CLEANUP;
    }
    extras = PyDict_New();
    for (int i = 0; i < PyList_GET_SIZE(node->m_Children); i++)
    {
        TypeTreeNodeObject *child = (TypeTreeNodeObject *)PyList_GET_ITEM(node->m_Children, i); // - borrowed ref +/- 0
        if (PyDict_Contains(annotations, child->_clean_name) == 1)
        {
            continue;
        }
        PyObject *extra_value = PyDict_GetItem(kwargs, child->_clean_name); // - borrowed ref +/- 0
        PyDict_SetItem(extras, child->_clean_name, extra_value);            // +1
        PyDict_DelItem(kwargs, child->_clean_name);                         // -1
    }

    if (PyDict_Size(extras) == 0)
    {
        Py_DECREF(clz);                                                 // 1->0
        clz = PyObject_GetAttrString(config->classes, "UnknownObject"); // 0->1
        PyDict_SetItemString(kwargs, "__node__", (PyObject *)node);
    }

    instance = PyObject_Call(clz, args, kwargs);
    if (instance != nullptr)
    {
        pos = 0;
        while (PyDict_Next(extras, &pos, &key, &value))
        {
            PyObject_GenericSetAttr(instance, key, value);
        }
        goto PARSE_CLASS_CLEANUP;
    }
    PyErr_Clear();

    // if we still failed to create an instance, fallback to UnknownObject
    Py_DECREF(clz);
    clz = PyObject_GetAttrString(config->classes, "UnknownObject");
    PyDict_SetItemString(kwargs, "__node__", (PyObject *)node);
    // merge extras back into kwargs
    pos = 0;
    while (PyDict_Next(extras, &pos, &key, &value))
    {
        PyDict_SetItem(kwargs, key, value);
    }
    instance = PyObject_Call(clz, args, kwargs);

PARSE_CLASS_CLEANUP:
    Py_DECREF(args);
    Py_DECREF(kwargs);
    Py_XDECREF(clz);
    Py_XDECREF(annotations);
    Py_XDECREF(extras);
    return instance;
}

TypeTreeNodeObject *get_ref_type_node(PyObject *ref_object, PyObject *assetsfile)
{
    if (assetsfile == Py_None)
    {
        PyErr_SetString(PyExc_ValueError, "Reference Type found but no SerializedFile passed as assetsfile to read_typetree!");
        return NULL;
    }
    PyObject *ref_types = PyObject_GetAttrString(assetsfile, "ref_types");
    if (!ref_types || !PyList_Check(ref_types))
    {
        Py_XDECREF(ref_types);
        PyErr_SetString(PyExc_ValueError, "No SerializedFile.ref_types");
        return NULL;
    }

    PyObject *type = PyDict_GetItemString(ref_object, "type");
    if (!type)
    {
        Py_DECREF(ref_types);
        PyErr_SetString(PyExc_ValueError, "Failed to get 'type'");
        return NULL;
    }

    PyObject *cls = NULL;
    PyObject *ns = NULL;
    PyObject *asm_ = NULL;
    if (PyDict_Check(type))
    {
        cls = PyDict_GetItemString(type, "class");
        ns = PyDict_GetItemString(type, "ns");
        asm_ = PyDict_GetItemString(type, "asm");
        Py_XINCREF(cls);
        Py_XINCREF(ns);
        Py_XINCREF(asm_);
    }
    else
    {
        cls = PyObject_GetAttrString(type, "class");
        ns = PyObject_GetAttrString(type, "ns");
        asm_ = PyObject_GetAttrString(type, "asm");
    }

    if (!cls || !ns || !asm_)
    {
        Py_DECREF(ref_types);
        Py_XDECREF(cls);
        Py_XDECREF(ns);
        Py_XDECREF(asm_);
        PyErr_SetString(PyExc_ValueError, "Failed to get 'class', 'ns' or 'asm'");
        return NULL;
    }

    if (PyUnicode_GET_LENGTH(cls) == 0)
    {
        Py_DECREF(ref_types);
        Py_DECREF(cls);
        Py_DECREF(ns);
        Py_DECREF(asm_);
        return (TypeTreeNodeObject *)Py_None;
    }

    Py_ssize_t ref_types_len = PyList_Size(ref_types);
    TypeTreeNodeObject *ref_type_node = NULL;
    for (Py_ssize_t i = 0; i < ref_types_len; i++)
    {
        PyObject *ref_type = PyList_GetItem(ref_types, i);
        PyObject *m_ClassName = PyObject_GetAttrString(ref_type, "m_ClassName");
        PyObject *m_NameSpace = PyObject_GetAttrString(ref_type, "m_NameSpace");
        PyObject *m_AssemblyName = PyObject_GetAttrString(ref_type, "m_AssemblyName");
        if (!m_ClassName || !m_NameSpace || !m_AssemblyName)
        {
            Py_XDECREF(m_ClassName);
            Py_XDECREF(m_NameSpace);
            Py_XDECREF(m_AssemblyName);
            PyErr_SetString(PyExc_ValueError, "Failed to get 'm_ClassName', 'm_NameSpace' or 'm_AssemblyName'");
            break;
        }

        bool compare_cls = (PyUnicode_Compare(cls, m_ClassName) == 0) && (PyUnicode_Compare(ns, m_NameSpace) == 0) && (PyUnicode_Compare(asm_, m_AssemblyName) == 0);
        Py_DECREF(m_ClassName);
        Py_DECREF(m_NameSpace);
        Py_DECREF(m_AssemblyName);

        if (compare_cls)
        {
            ref_type_node = (TypeTreeNodeObject *)PyObject_GetAttrString(ref_type, "node");
            break;
        }
    }

    Py_DECREF(ref_types);
    Py_XDECREF(cls);
    Py_XDECREF(ns);
    Py_XDECREF(asm_);

    return ref_type_node;
}

template <bool swap>
PyObject *read_typetree_value_array(ReaderT *reader, TypeTreeNodeObject *node, TypeTreeReaderConfigT *config, uint32_t size);

const NodeDataType SUPPORTED_VALUE_ARRAY_READ_TYPES[] = {
    NodeDataType::u8,
    NodeDataType::u16,
    NodeDataType::u32,
    NodeDataType::u64,
    NodeDataType::s8,
    NodeDataType::s16,
    NodeDataType::s32,
    NodeDataType::s64,
    NodeDataType::f32,
    NodeDataType::f64,
    NodeDataType::boolean,
    NodeDataType::pair,
};

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
    case NodeDataType::ReferencedObject:
    {
        value = PyDict_New();
        PyObject *child_value;
        for (int i = 0; i < PyList_GET_SIZE(node->m_Children); i++)
        {
            TypeTreeNodeObject *child = (TypeTreeNodeObject *)PyList_GET_ITEM(node->m_Children, i);
            if (child->_data_type == NodeDataType::ReferencedObjectData)
            {
                TypeTreeNodeObject *ref_node = get_ref_type_node(value, config->assetfile);
                if (!ref_node)
                {
                    PyErr_SetString(PyExc_ValueError, "Failed to get ref type node");
                    Py_DECREF(value);
                    return NULL;
                }
                else if (ref_node == (TypeTreeNodeObject *)Py_None)
                {
                    Py_DECREF(ref_node);
                    continue;
                }
                child_value = read_typetree_value<swap>(reader, ref_node, config);
                Py_DECREF(ref_node);
            }
            else
            {
                child_value = read_typetree_value<swap>(reader, child, config);
            }

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
            PyObject *clz = PyObject_GetAttrString(config->classes, "UnknownObject");
            if (clz == NULL)
            {
                PyErr_SetString(PyExc_ValueError, "Failed to get class");
                Py_DECREF(value);
                return NULL;
            }
            PyObject *args = PyTuple_Pack(1, (PyObject *)node);
            PyObject *instance = PyObject_Call(clz, args, value);
            Py_DECREF(clz);
            Py_DECREF(args);
            Py_DECREF(value);
            value = instance;
        }
        break;
    }
    default:
        TypeTreeNodeObject *child = nullptr;
        if (PyList_GET_SIZE(node->m_Children) > 0)
        {
            child = (TypeTreeNodeObject *)PyList_GET_ITEM(node->m_Children, 0);
        }

        if (child && child->_data_type == NodeDataType::Array)
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

            child = (TypeTreeNodeObject *)PyList_GET_ITEM(child->m_Children, 1);
            if (std::find(std::begin(SUPPORTED_VALUE_ARRAY_READ_TYPES), std::end(SUPPORTED_VALUE_ARRAY_READ_TYPES), child->_data_type) == std::end(SUPPORTED_VALUE_ARRAY_READ_TYPES))
            {
                value = PyList_New(length);
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
                value = read_typetree_value_array<swap>(reader, child, config, length);
            }
        }
        else
        {
            // class
            if (config->as_dict)
            {
                value = read_class<swap, true>(reader, node, config);
            }
            if (!config->as_dict)
            {
                value = read_class<swap, false>(reader, node, config);
                value = parse_class(value, node, config);
            }
        }
    }

    if (align)
    {
        align4(reader);
    }

    return value;
}

template <bool swap>
PyObject *read_typetree_value_array(ReaderT *reader, TypeTreeNodeObject *node, TypeTreeReaderConfigT *config, int32_t count)
{
    bool align = node->_align;
    PyObject *value = nullptr;

    switch (node->_data_type)
    {
    case NodeDataType::u8:
        value = read_u8_array(reader, count);
        break;
    case NodeDataType::u16:
        value = read_int_array<uint16_t, swap>(reader, count);
        break;
    case NodeDataType::u32:
        value = read_int_array<uint32_t, swap>(reader, count);
        break;
    case NodeDataType::u64:
        value = read_int_array<uint64_t, swap>(reader, count);
        break;
    case NodeDataType::s8:
        value = read_s8_array(reader, count);
        break;
    case NodeDataType::s16:
        value = read_int_array<int16_t, swap>(reader, count);
        break;
    case NodeDataType::s32:
        value = read_int_array<int32_t, swap>(reader, count);
        break;
    case NodeDataType::s64:
        value = read_int_array<int64_t, swap>(reader, count);
        break;
    case NodeDataType::f32:
        value = read_float_array<float, swap>(reader, count);
        break;
    case NodeDataType::f64:
        value = read_float_array<double, swap>(reader, count);
        break;
    case NodeDataType::boolean:
        value = read_bool_array(reader, count);
        break;
    case NodeDataType::pair:
        value = read_pair_array<swap>(reader, node, config, count);
        break;
    default:
        value = PyErr_Format(PyExc_ValueError, "Unsupported type for read_typetree_value_array: %d", node->_data_type);
    }
    if (align)
    {
        align4(reader);
    }

    return value;
}

static inline void set_none_if_null_n_incref(PyObject **field)
{
    if (*field == nullptr)
    {
        *field = Py_None;
    }
    Py_INCREF(*field);
}

PyObject *read_typetree(PyObject *self, PyObject *args, PyObject *kwargs)
{
    const char *kwlist[] = {"data", "node", "endian", "as_dict", "assetsfile", "classes", NULL};
    Py_buffer view;
    PyObject *node = nullptr;
    int as_dict = 1;
    PyObject *value = nullptr;
    Py_ssize_t bytes_read = 0;
    ReaderT reader;

    volatile uint16_t bint = 0x0100;
    volatile bool is_big_endian = ((uint8_t *)&bint)[0] == 1;

    TypeTreeReaderConfigT config = {
        false,
        nullptr,
        nullptr,
        false,
    };

    char endian;
    bool swap;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "y*OC|pOO", (char **)kwlist, &view, &node, &endian, &as_dict, &config.assetfile, &config.classes))
    {
        goto READ_TYPETREE_CLEANUP;
    }

    set_none_if_null_n_incref(&config.assetfile);
    set_none_if_null_n_incref(&config.classes);

    config.as_dict = as_dict == 1;
    if (!config.as_dict)
    {
        if (config.classes == Py_None)
        {
            PyErr_SetString(PyExc_ValueError, "classes must be set if not as dict");
            goto READ_TYPETREE_CLEANUP;
        }
    }

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
    {
        Py_DECREF(config.assetfile);
        Py_DECREF(config.classes);
        PyErr_SetString(PyExc_ValueError, "Invalid endian");
        return NULL;
    }
    }

    reader = {static_cast<uint8_t *>(view.buf), static_cast<uint8_t *>(view.buf) + view.len, static_cast<uint8_t *>(view.buf)};

    if (swap)
    {
        value = read_typetree_value<true>(&reader, (TypeTreeNodeObject *)node, &config);
    }
    else
    {
        value = read_typetree_value<false>(&reader, (TypeTreeNodeObject *)node, &config);
    }

    bytes_read = reader.ptr - reader.start;

READ_TYPETREE_CLEANUP:
    if (view.buf)
    {
        PyBuffer_Release(&view);
    }
    Py_XDECREF(config.assetfile);
    Py_XDECREF(config.classes);

    return Py_BuildValue("(Nn)", value, bytes_read);
}

// TypeTreeNode impl
static void TypeTreeNode_finalize(TypeTreeNodeObject *self)
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
    Py_XDECREF(self->_clean_name);
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
    {"FileSize", NodeDataType::u64},
    {"float", NodeDataType::f32},
    {"double", NodeDataType::f64},
    {"bool", NodeDataType::boolean},
    {"string", NodeDataType::str},
    {"TypelessData", NodeDataType::bytes},
    {"pair", NodeDataType::pair},
    {"Array", NodeDataType::Array},
    {"ReferencedObject", NodeDataType::ReferencedObject},
    {"ReferencedObjectData", NodeDataType::ReferencedObjectData},
    {"ManagedReferencesRegistry", NodeDataType::ManagedReferencesRegistry},
};

static inline NodeDataType get_node_data_type(PyObject *py_type)
{
    if (py_type == Py_None)
    {
        return NodeDataType::unk;
    }

    const char *type = PyUnicode_AsUTF8(py_type);
    if (type[0] == 'P' && type[1] == 'P' && type[2] == 't' && type[3] == 'r' && type[4] == '<')
    {
        return NodeDataType::PPtr;
    }
    else
    {
        for (auto it = typeToNodeDataType.begin(); it != typeToNodeDataType.end(); ++it)
        {
            if (strcmp(it->first, type) == 0)
            {
                return it->second;
            }
        }
    }
    return NodeDataType::unk;
}

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

    // ensure all fields are set to 0
    // in case init fails, so that dealloc doesn't segfault
    self->m_Level = nullptr;
    self->m_Type = nullptr;
    self->m_Name = nullptr;
    self->m_ByteSize = nullptr;
    self->m_TypeFlags = nullptr;
    self->m_Version = nullptr;
    self->m_Children = nullptr;
    self->m_VariableCount = nullptr;
    self->m_Index = nullptr;
    self->m_MetaFlag = nullptr;
    self->m_RefTypeHash = nullptr;
    self->_clean_name = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O!O!O!O!O!|O!O!O!O!O!O!", (char **)kwlist,
                                     // required fields
                                     &PyLong_Type, &self->m_Level,
                                     &PyUnicode_Type, &self->m_Type,
                                     &PyUnicode_Type, &self->m_Name,
                                     &PyLong_Type, &self->m_ByteSize,
                                     &PyLong_Type, &self->m_Version,
                                     // optional fields
                                     &PyList_Type, &self->m_Children,
                                     &PyLong_Type, &self->m_TypeFlags,
                                     &PyLong_Type, &self->m_VariableCount,
                                     &PyLong_Type, &self->m_Index,
                                     &PyLong_Type, &self->m_MetaFlag,
                                     &PyLong_Type, &self->m_RefTypeHash))
    {
        return -1;
    }

    // incref to keep values alive
    Py_INCREF(self->m_Level);
    Py_INCREF(self->m_Type);
    Py_INCREF(self->m_Name);
    Py_INCREF(self->m_ByteSize);
    Py_INCREF(self->m_Version);

    // optional values - can still be nullptr
    if (self->m_Children == nullptr)
    {
        self->m_Children = PyList_New(0);
    }
    else
    {
        Py_INCREF(self->m_Children);
    }
    set_none_if_null_n_incref(&self->m_TypeFlags);
    set_none_if_null_n_incref(&self->m_VariableCount);
    set_none_if_null_n_incref(&self->m_Index);
    set_none_if_null_n_incref(&self->m_MetaFlag);
    set_none_if_null_n_incref(&self->m_RefTypeHash);

    // set private fields required for fast access
    self->_data_type = get_node_data_type(self->m_Type);
    self->_align = (self->m_MetaFlag != Py_None && PyLong_AsLong(self->m_MetaFlag) & 0x4000);

    std::string sname = PyUnicode_AsUTF8(self->m_Name);
    std::string sclean_name = clean_name(sname);
    self->_clean_name = PyUnicode_FromString(sclean_name.c_str()); // comes with strong ref
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
    {"_clean_name", T_OBJECT_EX, offsetof(TypeTreeNodeObject, _clean_name), 0, ""},
    {NULL} /* Sentinel */
};

static PyTypeObject TypeTreeNodeType = []() -> PyTypeObject
{
    PyTypeObject type = {
#if PY_VERSION_HEX >= 0x03080000
        PyVarObject_HEAD_INIT(NULL, 0)
#else
        PyObject_HEAD_INIT(NULL) 0
#endif
    };
    type.tp_name = "TypeTreeHelper.TypeTreeNode";
    type.tp_doc = "TypeTreeNode objects";
    type.tp_basicsize = sizeof(TypeTreeNodeObject);
    type.tp_itemsize = 0;
    type.tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE;
    type.tp_new = PyType_GenericNew;
    type.tp_init = (initproc)TypeTreeNode_init;
    type.tp_members = TypeTreeNode_members;
    type.tp_finalize = (destructor)TypeTreeNode_finalize;
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
