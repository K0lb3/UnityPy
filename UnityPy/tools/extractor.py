from io import BytesIO
import os
import json
import UnityPy
from UnityPy.classes import (
    Object,
    PPtr,
    MonoBehaviour,
    TextAsset,
    Font,
    Shader,
    Mesh,
    Sprite,
    Texture2D,
    AudioClip,
    GameObject,
)
from UnityPy.enums.ClassIDType import ClassIDType
from typing import Union, List, Dict, Callable
from pathlib import Path


def export_obj(
    obj: Union[Object, PPtr],
    fp: Path,
    append_name: bool = False,
    append_path_id: bool = False,
    export_unknown_as_typetree: bool = False,
    asset_filter: Callable[[Object], bool] = None,
) -> List[int]:
    """Exports the given object to the given filepath.

    Args:
        obj (Object, PPtr): A valid Unity object or a reference to one.
        fp (Path): A valid filepath where the object should be exported to.
        append_name (bool, optional): Decides if the obj name will be appended to the filepath. Defaults to False.
        append_path_id (bool, optional): Decides if the obj path id will be appended to the filepath. Defaults to False.
        export_unknown_as_typetree (bool, optional): If set, then unimplemented objects will be exported via their typetree or dumped as bin. Defaults to False.
        asset_filter (func(Object)->bool, optional): Determines whether to export an object. Defaults to all objects.

    Returns:
        list: a list of exported object path_ids
    """
    # figure out export function
    export_func = EXPORT_TYPES.get(obj.type)
    if not export_func:
        if export_unknown_as_typetree:
            export_func = exportMonoBehaviour
        else:
            return []

    # set filepath
    obj = obj.read()

    # a filter that returned True during an earlier extract_assets check can return False now with more info from read()
    if asset_filter and not asset_filter(obj):
        return []

    if append_name:
        fp = os.path.join(fp, obj.name if obj.name else obj.type.name)

    fp, extension = os.path.splitext(fp)

    if append_path_id:
        fp = f"{fp}_{obj.path_id}"

    # export
    return export_func(obj, fp, extension)


def extract_assets(
    src: Union[Path, BytesIO, bytes, bytearray],
    dst: Path,
    use_container: bool = True,
    ignore_first_container_dirs: int = 0,
    append_path_id: bool = False,
    export_unknown_as_typetree: bool = False,
    asset_filter: Callable[[Object], bool] = None,
) -> List[int]:
    """Extracts some or all assets from the given source.

    Args:
        src (Union[Path, BytesIO, bytes, bytearray]): [description]
        dst (Path): [description]
        use_container (bool, optional): [description]. Defaults to True.
        ignore_first_container_dirs (int, optional): [description]. Defaults to 0.
        append_path_id (bool, optional): [description]. Defaults to False.
        export_unknown_as_typetree (bool, optional): [description]. Defaults to False.
        asset_filter (func(object)->bool, optional): Determines whether to export an object. Defaults to all objects.

    Returns:
        List[int]: [description]
    """
    # load source
    env = UnityPy.load(src)
    exported = []

    export_types_keys = list(EXPORT_TYPES.keys())

    def defaulted_export_index(type: ClassIDType):
        try:
            return export_types_keys.index(type)
        except (IndexError, ValueError):
            return 999

    if use_container:
        container = sorted(
            env.container.items(), key=lambda x: defaulted_export_index(x[1].type)
        )
        for obj_path, obj in container:
            # The filter here can only access metadata. The same filter may produce a different result later in extract_obj after obj.read()
            if asset_filter is not None and not asset_filter(obj):
                continue
            # the check of the various sub directories is required to avoid // in the path
            obj_dest = os.path.join(
                dst,
                *(x for x in obj_path.split("/")[:ignore_first_container_dirs] if x),
            )
            os.makedirs(os.path.dirname(obj_dest), exist_ok=True)
            exported.extend(
                export_obj(
                    obj,
                    obj_dest,
                    append_path_id=append_path_id,
                    export_unknown_as_typetree=export_unknown_as_typetree,
                    asset_filter=asset_filter,
                )
            )

    else:
        objects = sorted(env.objects, key=lambda x: defaulted_export_index(x.type))
        for obj in objects:
            if asset_filter is not None and not asset_filter(obj):
                continue
            if (obj.assets_file, obj.path_id) not in exported:
                exported.extend(
                    export_obj(
                        obj,
                        dst,
                        append_name=True,
                        append_path_id=append_path_id,
                        export_unknown_as_typetree=export_unknown_as_typetree,
                        asset_filter=asset_filter,
                    )
                )

    return exported


###############################################################################
#                      EXPORT FUNCTIONS                                       #
###############################################################################


def exportTextAsset(obj: TextAsset, fp: str, extension: str = ".txt") -> List[int]:
    if not extension:
        extension = ".txt"
    with open(f"{fp}{extension}", "wb") as f:
        f.write(obj.script)
    return [(obj.assets_file, obj.path_id)]


def exportFont(obj: Font, fp: str, extension: str = "") -> List[int]:
    # TODO - export glyphs
    if obj.m_FontData:
        extension = ".ttf"
        if obj.m_FontData[0:4] == b"OTTO":
            extension = ".otf"
        with open(f"{fp}{extension}", "wb") as f:
            f.write(obj.m_FontData)
    return [(obj.assets_file, obj.path_id)]


def exportMesh(obj: Mesh, fp: str, extension=".obj") -> List[int]:
    if not extension:
        extension = ".obj"
    with open(f"{fp}{extension}", "wt", encoding="utf8", newline="") as f:
        f.write(obj.export())
    return [(obj.assets_file, obj.path_id)]


def exporShader(obj: Shader, fp: str, extension=".txt") -> List[int]:
    if not extension:
        extension = ".txt"
    with open(f"{fp}{extension}", "wt", encoding="utf8", newline="") as f:
        f.write(obj.export())
    return [(obj.assets_file, obj.path_id)]


def exportMonoBehaviour(
    obj: Union[MonoBehaviour, Object], fp: str, extension: str = ""
) -> List[int]:
    export = None
    # TODO - add generic way to add external typetrees
    if obj.serialized_type and obj.serialized_type.nodes:
        extension = ".json"
        export = json.dumps(obj.read_typetree(), indent=4, ensure_ascii=False).encode(
            "utf8", errors="surrogateescape"
        )
    elif isinstance(obj, MonoBehaviour):
        # no set typetree
        # check if we have a script
        script = obj.m_Script
        if script:
            # looks like we have a script
            script = script.read()
            # check if there is a locally stored typetree for it
            nodes = MONOBEHAVIOUR_TYPETREES.get(script.m_AssemblyName, {}).get(
                script.m_ClassName, None
            )
            if nodes:
                # we have a typetree
                # adjust the name
                # name = (
                #     f"{script.m_ClassName}-{obj.name}"
                #     if obj.name
                #     else script.m_ClassName
                # )
                extension = ".json"
                export = json.dumps(
                    obj.read_typetree(nodes), indent=4, ensure_ascii=False
                ).encode("utf8", errors="surrogateescape")
    if not export:
        extension = ".bin"
        export = obj.raw_data
    with open(f"{fp}{extension}", "wb") as f:
        f.write(export)
    return [(obj.assets_file, obj.path_id)]


def exportAudioClip(obj: AudioClip, fp: str, extension: str = "") -> List[int]:
    samples = obj.samples
    if len(samples) == 0:
        pass
    elif len(samples) == 1:
        with open(f"{fp}.wav", "wb") as f:
            f.write(list(samples.values())[0])
    else:
        os.makedirs(fp, exist_ok=True)
        for name, clip_data in samples.items():
            with open(os.path.join(fp, f"{name}.wav"), "wb") as f:
                f.write(clip_data)
    return [(obj.assets_file, obj.path_id)]


def exportSprite(obj: Sprite, fp: str, extension: str = ".png") -> List[int]:
    if not extension:
        extension = ".png"
    obj.image.save(f"{fp}{extension}")
    exported = [
        (obj.assets_file, obj.path_id),
        (obj.m_RD.texture.assets_file, obj.m_RD.texture.path_id),
    ]
    alpha_assets_file = getattr(obj.m_RD.alphaTexture, "assets_file", None)
    alpha_path_id = getattr(obj.m_RD.alphaTexture, "path_id", None)
    if alpha_path_id and alpha_assets_file:
        exported.append((alpha_assets_file, alpha_path_id))
    return exported


def exportTexture2D(obj: Texture2D, fp: str, extension: str = ".png") -> List[int]:
    if not extension:
        extension = ".png"
    if obj.m_Width:
        # textures can be empty
        obj.image.save(f"{fp}{extension}")
    return [(obj.assets_file, obj.path_id)]


def exportGameObject(obj: GameObject, fp: str, extension: str = "") -> List[int]:
    exported = [(obj.assets_file, obj.path_id)]
    refs = crawl_obj(obj)
    if refs:
        os.makedirs(fp, exist_ok=True)
    for ref_id, ref in refs.items():
        # Don't export already exported objects a second time
        # and prevent circular calls by excluding other GameObjects.
        # The other GameObjects were already exported in the this call.
        if (ref.assets_file, ref_id) in exported or ref.type == ClassIDType.GameObject:
            continue
        try:
            exported.extend(export_obj(ref, fp, True, True))
        except Exception as e:
            print(f"Failed to export {ref_id}")
            print(e)
    return exported


EXPORT_TYPES = {
    # following types can include other objects
    ClassIDType.GameObject: exportGameObject,
    ClassIDType.Sprite: exportSprite,
    # following types don't include other objects
    ClassIDType.AudioClip: exportAudioClip,
    ClassIDType.Font: exportFont,
    ClassIDType.Mesh: exportMesh,
    ClassIDType.MonoBehaviour: exportMonoBehaviour,
    ClassIDType.Shader: exporShader,
    ClassIDType.TextAsset: exportTextAsset,
    ClassIDType.Texture2D: exportTexture2D,
}

MONOBEHAVIOUR_TYPETREES: Dict["Assembly-Name.dll", Dict["Class-Name", List[Dict]]] = {}


def crawl_obj(obj: Object, ret: dict = None) -> Dict[int, Union[Object, PPtr]]:
    """Crawls through the data struture of the object and returns a list of all the components."""
    if not ret:
        ret = {}

    if isinstance(obj, PPtr):
        if obj.path_id == 0 and obj.file_id == 0 and obj.index == -2:
            return ret
        try:
            obj = obj.read()
        except AttributeError:
            return ret
    else:
        return ret
    ret[obj.path_id] = obj

    # MonoBehaviour really on their typetree
    # while Object denotes that the class of the object isn't implemented yet
    if isinstance(obj, (MonoBehaviour, Object)):
        obj.read_typetree()
        data = obj.type_tree.__dict__.values()
    else:
        data = obj.__dict__.values()

    for value in flatten(data):
        if isinstance(value, (Object, PPtr)):
            if value.path_id in ret:
                continue
            crawl_obj(value, ret)

    return ret


def flatten(l):
    for el in list(l):
        if isinstance(el, (list, tuple)):
            yield from flatten(el)
        elif isinstance(el, dict):
            yield from flatten(el.values())
        else:
            yield el
