"""Generates the classes for the UnityPy objects from the TypeTree of the TPK files."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

# import UnityPy from the parent directory instead of the installed package
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)
from UnityPy.helpers.Tpk import TPKTYPETREE, TpkUnityNode  # noqa: E402
from UnityPy.helpers.TypeTreeNode import clean_name  # noqa: E402

NODES = TPKTYPETREE.NodeBuffer.Nodes
STRINGS = TPKTYPETREE.StringBuffer.Strings

BASE_TYPE_MAP = {
    "char": "str",
    "short": "int",
    "int": "int",
    "long long": "int",
    "unsigned short": "int",
    "unsigned int": "int",
    "unsigned long long": "int",
    "UInt8": "int",
    "UInt16": "int",
    "UInt32": "int",
    "UInt64": "int",
    "SInt8": "int",
    "SInt16": "int",
    "SInt32": "int",
    "SInt64": "int",
    "Type*": "int",
    "FileSize": "int",
    "float": "float",
    "double": "float",
    "bool": "bool",
    "string": "str",
    "TypelessData": "bytes",
}

GENERATED_HEADER = """
# type: ignore
from __future__ import annotations

from abc import ABC
from typing import List, Optional, Tuple, TypeVar, Union

from attrs import define as attrs_define

from .math import (
  ColorRGBA,
  Matrix3x4f,
  Matrix4x4f,
  Quaternionf,
  Vector2f,
  Vector3f,
  Vector4f,
  float3,
  float4,
)
from .Object import Object
from .PPtr import PPtr

T = TypeVar("T")


def unitypy_define(cls: T) -> T:
  \"\"\"
  A hacky solution to bypass multiple problems related to attrs and inheritance.

  The class inheritance is very lax and based on the typetrees.
  Some of the child classes might not have the same attributes as the parent class,
  which would make type-hinting more tricky, and breaks attrs.define.

  Therefore this function bypasses the issue
  by redefining the bases for problematic classes for the attrs.define call.
  \"\"\"
  bases = cls.__bases__
  if bases[0] in (object, Object, ABC):
    cls = attrs_define(cls, slots=True, unsafe_hash=True)
  else:
    cls.__bases__ = (Object,)
    cls = attrs_define(cls, slots=False, unsafe_hash=True)
    cls.__bases__ = bases
  return cls
"""[0:]

# LIST_BASE_TYPE_MAP = {
#     "short": "np.int16",
#     "int": "np.int32",
#     "long long": "np.int64",
#     "unsigned short": "np.uint16",
#     "unsigned int": "np.uint32",
#     "unsigned long long": "np.int64",
#     "UInt8": "np.uint8",
#     "UInt16": "np.uint16",
#     "UInt32": "np.uint32",
#     "UInt64": "np.uint64",
#     "SInt8": "np.int8",
#     "SInt16": "npt.int16",
#     "SInt32": "np.int32",
#     "SInt64": "np.int64",
#     "Type*": "np.uint32",
#     "FileSize": "np.uint64",
#     "float": "np.float32",
#     "double": "np.float64",
#     "bool": "np.bool",
# }

MATH_CLASSES = {
    "ColorRGBA",
    "Matrix3x4f",
    "Matrix4x4f",
    "Quaternionf",
    "Vector2f",
    "Vector3f",
    "Vector4f",
    "float3",
    "float4",
}

FORBIDDEN_CLASSES = {"bool", "float", "int", "void"} | MATH_CLASSES

CLASS_CACHE_ID: Dict[Tuple[int, str], NodeClass] = {}
CLASS_CACHE_NAME: Dict[str, NodeClass] = {}
TYPE_CACHE: Dict[int, str] = {}


@dataclass
class NodeClassField:
    ids: Set[int]
    name: str
    types: Set[str] = field(default_factory=set)
    optional: bool = True

    def generate_str(self) -> str:
        if len(self.types) == 1:
            typ = next(iter(self.types))
        else:
            typ = f"Union[{', '.join(self.types)}]"

        if self.optional:
            return f"  {self.clean_name}: Optional[{typ}] = None"
        else:
            return f"  {self.clean_name}: {typ}"

    @property
    def clean_name(self) -> str:
        return clean_name(self.name)


@dataclass
class NodeClass:
    ids: Set[int]
    name: str
    aliases: Set[str] = field(default_factory=set)
    fields: Dict[str, NodeClassField] = field(default_factory=dict)
    field_ids: Set[int] = field(default_factory=set)
    key_fields: Set[str] = field(default_factory=set)
    abstract: bool = False
    base: Optional[str] = None

    @staticmethod
    def sort_fields(field: NodeClassField) -> Tuple[bool, str]:
        return (field.optional, field.clean_name)

    def generate_str(self) -> str:
        # order fields by 1. non-optional>optional, 2. name
        parents: List[str] = []

        if self.base:
            parents.append(self.base)

        if self.abstract:
            parents.append("ABC")

        parentsString = f"({', '.join(parents)})" if parents else ""

        if len(self.fields) == 0:
            field_strings = ["  pass"]
        else:
            field_strings = map(
                NodeClassField.generate_str,
                sorted(self.fields.values(), key=NodeClass.sort_fields),
            )
        return "\n".join(
            [
                "@unitypy_define",
                f"class {self.name}{parentsString}:",
                *field_strings,
            ]
        )


def implement_node_class(
    node_id: int,
    node: Optional[TpkUnityNode] = None,
    override_name: Optional[str] = None,
) -> NodeClass:
    if node is None:
        node = NODES[node_id]
    cls_name = override_name or STRINGS[node.TypeName]

    cls = CLASS_CACHE_ID.get((node_id, cls_name))
    if cls is not None:
        return cls

    cls = CLASS_CACHE_NAME.get(cls_name)
    first_impl = False
    if cls is None:
        first_impl = True
        cls = NodeClass(ids={node_id}, name=cls_name)
        CLASS_CACHE_NAME[cls_name] = cls
    else:
        cls.ids.add(node_id)

    CLASS_CACHE_ID[(node_id, cls_name)] = cls
    if override_name and override_name != STRINGS[node.TypeName]:
        cls.aliases.add(STRINGS[node.TypeName])

    field_names: Set[str] = set()
    for subnode_id in node.SubNodes:
        subnode = NODES[subnode_id]
        # TEST1
        # subname = clean_name(STRINGS[subnode.Name])
        subname = STRINGS[subnode.Name]

        field_names.add(subname)

        if subnode_id in cls.field_ids:
            continue

        field = cls.fields.get(subname)
        if field is None:
            field = NodeClassField({subnode_id}, subname)
            cls.fields[subname] = field
        else:
            field.ids.add(subnode_id)

        field_type = generate_field_type(subnode_id, subnode)
        field.types.add(field_type)

    cls.field_ids |= set(node.SubNodes)

    if first_impl:
        cls.key_fields = set(cls.fields.keys())
        for field in cls.fields.values():
            field.optional = False
    else:
        deprecated_field_names = cls.key_fields - field_names
        cls.key_fields -= deprecated_field_names
        for deprecated_name in deprecated_field_names:
            cls.fields[deprecated_name].optional = True

    return cls


def generate_field_type(node_id: int, node: Optional[TpkUnityNode] = None) -> str:
    res = TYPE_CACHE.get(node_id)
    if res is not None:
        return res

    if node is None:
        node = NODES[node_id]

    typename = STRINGS[node.TypeName]

    py_typ = BASE_TYPE_MAP.get(typename)
    if py_typ:
        res = py_typ

    elif typename == "pair":
        # Children:
        #   Typ1 first
        #   Typ2 second
        typ1 = generate_field_type(node.SubNodes[0])
        typ2 = generate_field_type(node.SubNodes[1])
        res = f"Tuple[{typ1}, {typ2}]"

    elif typename.startswith("PPtr<"):
        res = typename.replace("<", "[").replace(">", "]")

    else:
        # map & vector
        subnode0 = NODES[node.SubNodes[0]] if len(node.SubNodes) > 0 else None
        if subnode0 and STRINGS[subnode0.TypeName] == "Array":
            # Children:
            #   Array Array
            #       SInt32 size
            #       Typ data
            subtype_node = NODES[subnode0.SubNodes[1]]
            subtype_name = STRINGS[subtype_node.TypeName]
            if subtype_name in BASE_TYPE_MAP:
                res = f"List[{BASE_TYPE_MAP[subtype_name]}]"
            else:
                res = f"List[{generate_field_type(subnode0.SubNodes[1], subtype_node)}]"
        else:
            # custom class
            implement_node_class(node_id, node)
            res = typename

    TYPE_CACHE[node_id] = res
    return res


def main():
    main_classes: Set[str] = set()
    deps: Dict[str, List[str]] = {}

    for _class_id, class_info in TPKTYPETREE.ClassInformation.items():
        abstract = True
        base = None
        cls_name: Optional[str] = None

        for _version, unity_class in class_info.Classes:
            if unity_class is None:
                continue
            cls_name = STRINGS[unity_class.Name]
            base = STRINGS[unity_class.Base]

            if unity_class.ReleaseRootNode is not None:
                abstract = False
                cls = implement_node_class(unity_class.ReleaseRootNode, override_name=cls_name)
                cls.base = base

        if isinstance(cls_name, str):
            if abstract:
                CLASS_CACHE_NAME[cls_name] = NodeClass({0}, name=cls_name, base=base, abstract=True)

            main_classes.add(cls_name)
            if base:
                if base in deps:
                    deps[base].append(cls_name)
                else:
                    deps[base] = [cls_name]

    CLASS_CACHE_NAME.pop("Object")
    sorted_classes: List[str] = []

    stack = [*sorted(deps.pop("Object"))]
    while stack:
        cls_name = stack.pop(0)
        sorted_classes.append(cls_name)
        if cls_name in deps:
            stack = sorted(deps.pop(cls_name)) + stack

    sorted_classes += sorted(set(CLASS_CACHE_NAME.keys()) - set(sorted_classes) - FORBIDDEN_CLASSES)
    i = 0
    names = set()
    while i < len(sorted_classes):
        name = sorted_classes[i]
        if name in names:
            sorted_classes.pop(i)
        else:
            names.add(name)
            i += 1

    fp = os.path.join(ROOT, "UnityPy", "classes", "generated.py")
    with open(fp, "w", encoding="utf8") as f:
        f.write(GENERATED_HEADER)
        f.write("\n\n")

        f.write("\n\n".join(cls.generate_str() for cls in map(CLASS_CACHE_NAME.__getitem__, sorted_classes)))
        f.write("\n")


if __name__ == "__main__":
    import time

    t1 = time.time_ns()
    main()
    t2 = time.time_ns()
    print(t2 - t1 / 10**9)
