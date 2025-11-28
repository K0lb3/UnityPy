import os
from typing import Dict, List, Tuple

from .TypeTreeNode import TypeTreeNode

try:
    from TypeTreeGeneratorAPI import TypeTreeGenerator as TypeTreeGeneratorBase  # pyright: ignore[reportAssignmentType]
except ImportError:

    class TypeTreeGeneratorBase:
        def __init__(self, unity_version: str):
            raise ImportError("TypeTreeGeneratorAPI isn't installed!")

        def load_dll(self, dll: bytes): ...
        def load_il2cpp(self, il2cpp: bytes, metadata: bytes): ...
        def get_nodes_as_json(self, assembly: str, fullname: str) -> str: ...
        def get_nodes(self, assembly: str, fullname: str) -> List[TypeTreeNode]: ...


class TypeTreeGenerator(TypeTreeGeneratorBase):
    cache: Dict[Tuple[str, str], TypeTreeNode]

    def __init__(self, unity_version: str, *args, **kwargs):
        super().__init__(unity_version, *args, **kwargs)
        self.cache = {}

    def load_local_game(self, root_dir: str):
        root_files = os.listdir(root_dir)
        data_dir = os.path.join(root_dir, next(f for f in root_files if f.endswith("_Data")))
        if "GameAssembly.dll" in root_files:
            ga_fp = os.path.join(root_dir, "GameAssembly.dll")
            gm_fp = os.path.join(data_dir, "il2cpp_data", "Metadata", "global-metadata.dat")
            ga_raw = open(ga_fp, "rb").read()
            gm_raw = open(gm_fp, "rb").read()
            self.load_il2cpp(ga_raw, gm_raw)
        else:
            self.load_local_dll_folder(os.path.join(data_dir, "Managed"))

    def load_local_dll_folder(self, dll_dir: str):
        for f in os.listdir(dll_dir):
            if not f.endswith(".dll"):
                continue
            fp = os.path.join(dll_dir, f)
            with open(fp, "rb") as f:
                data = f.read()
                self.load_dll(data)

    def get_nodes_up(self, assembly: str, fullname: str) -> TypeTreeNode:
        key = (assembly, fullname)
        if key in self.cache:
            return self.cache[key]

        if not assembly.endswith(".dll"):
            assembly = f"{assembly}.dll"

        base_nodes = self.get_nodes(assembly, fullname)

        node = TypeTreeNode.from_list(
            [
                TypeTreeNode(
                    base_node.m_Level,
                    base_node.m_Type,
                    base_node.m_Name,
                    0,
                    0,
                    m_MetaFlag=base_node.m_MetaFlag,
                )
                for base_node in base_nodes
            ]
        )

        self.cache[key] = node
        return node


__all__ = ("TypeTreeGenerator",)
