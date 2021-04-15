import os
import UnityPy
from collections import Counter
import zipfile
import json

TYPES = [
    # Images
    'Sprite',
    'Texture2D',
    # Text (filish)
    'TextAsset',
    'Shader',
    'MonoBehaviour',
    'Mesh'
    # Font
    'Font',
    # Audio
    'AudioClip',
]

ROOT = os.path.dirname(os.path.realpath(__file__))

# source folder
ASSETS = os.path.join(ROOT, 'assets')
# destination folder
DST = os.path.join(ROOT, 'extracted')
# number of dirs to ignore
# e.g. IGNOR_DIR_COUNT = 2 will reduce
# 'assets/assetbundles/images/story_picture/small/15.png'
# to
# 'images/story_picture/small/15.png'

IGNOR_DIR_COUNT = 2

os.makedirs(DST, exist_ok=True)


def main():
    for root, dirs, files in os.walk(ASSETS, topdown=False):
        if '.git' in root:
            continue
        for f in files:
            print(f)
            extension = os.path.splitext(f)[1]
            src = os.path.realpath(os.path.join(root, f))

            if extension == ".zip":
                archive = zipfile.ZipFile(src, 'r')
                for zf in archive.namelist():
                    extract_assets(archive.open(zf))
            else:
                extract_assets(src)


def extract_assets(src):
    # load source
    env = UnityPy.load(src)

    # iterate over assets
    for asset in env.assets:
        # assets without container / internal path will be ignored for now
        if not asset.container:
            continue
        # filter objects and put Texture2Ds at the end of the list
        objs = sorted((obj for obj in asset.get_objects(
        ) if obj.type.name in TYPES), key=lambda x: 1 if x.type == "Texture2D" else 0)
        cobjs = sorted(((key, obj) for key, obj in asset.container.items(
        ) if obj.type.name in TYPES), key=lambda x: 1 if x[1].type == "Texture2D" else 0)
        # check which mode we will have to use
        num_cont = sum(cobjs)
        num_objs = len(objs)

        # check if container contains all important assets, if yes, just ignore the container
        if num_objs <= num_cont * 2:
            for asset_path, obj in cobjs:
                fp = os.path.join(DST, *asset_path.split('/')
                                  [IGNOR_DIR_COUNT:])
                export_obj(obj, fp)

        # otherwise use the container to generate a path for the normal objects
        else:
            extracted = []
            # find the most common path
            occurence_count = Counter(os.path.splitext(asset_path)[
                                      0] for asset_path in asset.container.keys())
            local_path = os.path.join(
                DST, *occurence_count.most_common(1)[0][0].split('/')[IGNOR_DIR_COUNT:])

            for obj in objs:
                if obj.path_id not in extracted:
                    extracted.extend(export_obj(
                        obj, local_path, append_name=True))


def export_obj(obj, fp: str, append_name: bool = False) -> list:
    if obj.type not in TYPES:
        return []

    data = obj.read()
    if append_name:
        fp = os.path.join(fp, data.name)

    fp, extension = os.path.splitext(fp)
    os.makedirs(os.path.dirname(fp), exist_ok=True)

    # streamlineable types
    export = None
    if obj.type == 'TextAsset':
        if not extension:
            extension = '.txt'
        export = data.script

    elif obj.type == "Font":
        if data.m_FontData:
            extension = ".ttf"
            if data.m_FontData[0:4] == b"OTTO":
                extension = ".otf"
            export = data.m_FontData
        else:
            return [obj.path_id]

    elif obj.type == "Mesh":
        extension = ".obf"
        export = data.export().encode("utf8")

    elif obj.type == "Shader":
        extension = ".txt"
        export = data.export().encode("utf8")

    elif obj.type == "MonoBehaviour":
        # The data structure of MonoBehaviours is custom
        # and is stored as nodes
        # If this structure doesn't exist,
        # it might still help to at least save the binary data,
        # which can then be inspected in detail.
        if obj.serialized_type.nodes:
            extension = ".json"
            export = json.dumps(
                obj.read_typetree(),
                indent=4,
                ensure_ascii=False
            ).encode("utf8")
        else:
            extension = ".bin"
            export = data.raw_data

    if export:
        with open(f"{fp}{extension}", "wb") as f:
            f.write(export)

    # non-streamlineable types
    if obj.type == "Sprite":
        data.image.save(f"{fp}.png")

        return [obj.path_id, data.m_RD.texture.path_id, getattr(data.m_RD.alphaTexture, 'path_id', None)]

    elif obj.type == "Texture2D":
        if not os.path.exists(fp) and data.m_Width:
            # textures can have size 0.....
            data.image.save(f"{fp}.png")

    elif obj.type == "AudioClip":
        samples = data.samples
        if len(samples) == 0:
            pass
        elif len(samples) == 1:
            with open(f"{fp}.wav", "wb") as f:
                f.write(list(data.samples.values())[0])
        else:
            os.makedirs(fp, exist_ok=True)
            for name, clip_data in samples.items():
                with open(os.path.join(fp, f"{name}.wav"), "wb") as f:
                    f.write(clip_data)
    return [obj.path_id]


if __name__ == '__main__':
    main()
