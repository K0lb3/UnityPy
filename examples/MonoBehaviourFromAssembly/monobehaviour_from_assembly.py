# py3
# requirements:
#   pythonnet 3+
#       pip install git+https://github.com/pythonnet/pythonnet/
#   TypeTreeGenerator
#       https://github.com/K0lb3/TypeTreeGenerator
#       requires .NET 5.0 SDK
#           https://dotnet.microsoft.com/download/dotnet/5.0
#   Requires .NET 3.1
#           https://dotnet.microsoft.com/en-us/download/dotnet/3.1/runtime?cid=getdotnetcore
#
#   pythonnet 2 and TypeTreeGenerator created with net4.8 works on Windows,
#   so it can do without pythonnet_init,
#   all other systems need pythonnet 3 and either .net 5 or .net core 3 and pythonnet_init


############################
#
#   Warning: This example isn't for beginners
#
############################

import os
import UnityPy
from typing import Dict
import json

ROOT = os.path.dirname(os.path.realpath(__file__))
TYPETREE_GENERATOR_PATH = os.path.join(ROOT, "TypeTreeGenerator")

def main():
    # dump the trees for all classes in the assembly
    dll_folder = os.path.join(ROOT, "DummyDll")
    tree_path = os.path.join(ROOT, "assembly_typetrees.json") 
    trees = dump_assembly_trees(dll_folder, tree_path)
    # by dumping it as json, it can be redistributed,
    # so that other people don't have to setup pythonnet3
    # People who don't like to share their decrypted dlls could also share the relevant structures this way.

    export_monobehaviours(asset_path, trees)

def export_monobehaviours(asset_path: str, trees: dict):
    for r, d, fs in os.walk(asset_path):
        for f in fs:
            try:
                env = UnityPy.load(os.path.join(r, f))
            except:
                continue
            for obj in env.objects:
                if obj.type == "MonoBehaviour":
                    d = obj.read()
                    if obj.serialized_type and obj.serialized_type.node:
                        tree = obj.read_typetree()
                    else:
                        if not d.m_Script:
                            continue
                            # RIP, no referenced script
                            # can only dump raw
                        script = d.m_Script.read()
                        # on-demand solution without already dumped tree
                        #nodes = generate_tree(
                        #    g, script.m_AssemblyName, script.m_ClassName, script.m_Namespace
                        #)
                        if script.m_ClassName not in trees:
                            # class not found in known trees,
                            # might have to add the classes of the other dlls
                            continue
                        nodes = FakeNode(**trees[script.m_ClassName])
                        tree = obj.read_typetree(nodes)
                
                # save tree as json whereever you like
                    
                    

def dump_assembly_trees(dll_folder: str, out_path: str):
    # init pythonnet, so that it uses the correct .net for the generator
    pythonnet_init()
    # create generator
    g = create_generator(dll_folder)

    # generate a typetree for all existing classes in the Assembly-CSharp
    # while this could also be done dynamically for each required class,
    # it's faster and easier overall to just fetch all at once
    trees = generate_tree(g, "Assembly-CSharp.dll", "", "")

    if out_path:
        with open("typetrees.json", "wt", encoding="utf8") as f:
            json.dump(trees, f, ensure_ascii=False)
    return trees



def pythonnet_init():
    """correctly sets-up pythonnet for the typetree generator"""
    # prepare correct runtime
    from clr_loader import get_coreclr
    from pythonnet import set_runtime

    rt = get_coreclr( runtime_config=
        os.path.join(TYPETREE_GENERATOR_PATH, "TypeTreeGenerator.runtimeconfig.json")
    )
    set_runtime(rt)


def create_generator(dll_folder: str):
    """Loads TypeTreeGenerator library and returns an instance of the Generator class."""
    # temporarily add the typetree generator dir to paths,
    # so that pythonnet can find its files
    import sys

    sys.path.append(TYPETREE_GENERATOR_PATH)

    #
    import clr

    clr.AddReference("TypeTreeGenerator")

    # import Generator class from the loaded library
    from Generator import Generator

    # create an instance of the Generator class
    g = Generator()
    # load the dll folder into the generator
    g.loadFolder(dll_folder)
    return g


class FakeNode:
    """A fake/minimal Node class for use in UnityPy."""

    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)


def generate_tree(
    g: "Generator",
    assembly: str,
    class_name: str,
    namespace: str,
    unity_version=[2018, 4, 3, 1],
) -> Dict[str, Dict]:
    """Generates the typetree structure / nodes for the specified class."""
    # C# System
    from System import Array

    unity_version_cs = Array[int](unity_version)

    # fetch all type definitions
    def_iter = g.getTypeDefs(assembly, class_name, namespace)

    # create the nodes
    trees = {}
    for d in def_iter:
        try:
            nodes = g.convertToTypeTreeNodes(d, unity_version_cs)
        except Exception as e:
            # print(d.Name, e)
            continue
        trees[d.Name] = [
            {
                "level" : node.m_Level,
                "type" : node.m_Type,
                "name" : node.m_Name,
                "meta_flag" : node.m_MetaFlag,
            }
            for node in nodes
        ]
    return trees


if __name__ == "__main__":
    main()
