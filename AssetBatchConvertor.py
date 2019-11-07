import os
import time

import json
from UnityPy import AssetsManager
from statistics import mode 
TYPES = ['Sprite','Texture2D','TextAsset']

ROOT = os.path.dirname(os.path.realpath(__file__))

# source folder
ASSETS=os.path.join(ROOT,'assetbundle')
# destination folder
DST = os.path.join(ROOT, 'extracted')
# number of dirs to ignore
# e.g. IGNOR_DIR_COUNT = 2 will reduce
# 'assets/assetbundles/images/story_picture/small/15.png'
# to
# 'images/story_picture/small/15.png'

IGNOR_DIR_COUNT = 2

os.makedirs(DST, exist_ok=True)

debug = True

def main():
    for root, dirs, files in os.walk(ASSETS, topdown=False):
        if '.git' in root:
            continue
        for f in files:
            print(f)
            # load file
            src = os.path.realpath(os.path.join(root, f))
            b = AssetsManager()
            b.load_file(src)

            # iterate over assets
            for asset in b.assets.values():
                # assets without container / internal path will be ignored for now
                if not asset.container:
                    continue
                
                # check which mode we will have to use
                num_cont = sum(1 for obj in asset.container.values() if obj.type in TYPES)
                num_objs = sum(1 for obj in asset.objects.values() if obj.type in TYPES)

                # check if container contains all important assets, if yes, just ignore the container
                if num_objs <= num_cont * 2:
                    for asset_path, obj in asset.container.items():
                        fp = os.path.join(DST, *asset_path.split('/')[IGNOR_DIR_COUNT:])
                        export_obj(obj, fp)

                # otherwise use the container to generate a path for the normal objects
                else:
                    local_path = []
                    extracted = []

                    for asset_path in asset.container.keys():
                        local_path.append(
                            os.path.splitext(asset_path)[0]
                        )

                    if len(local_path) > 1:
                        if len(set(local_path)) == 1:
                            local_path = local_path[0]
                        else:
                            local_path = mode(local_path)
                    else:
                        local_path = local_path[0]
                    local_path = os.path.join(DST, *local_path.split('/')[IGNOR_DIR_COUNT:])


                    for obj in asset.objects.values():
                        if obj.path_id not in extracted:
                            extracted.extend(export_obj(obj, local_path, append_name=True))


def export_obj(obj, fp : str, append_name : bool = False) -> list:
    if obj.type not in TYPES:
        return []
    data = obj.read()
    if append_name:
        fp = os.path.join(fp, data.name)
    
    fp, extension = os.path.splitext(fp)
    os.makedirs(os.path.dirname(fp), exist_ok=True)

    if obj.type == 'TextAsset':
        if not extension:
            extension = '.txt'
        with open(f"{fp}{extension}", 'wb') as f:
            f.write(data.script)

    elif obj.type == "Sprite":
        extension = ".png"
        data.image.save(f"{fp}{extension}")

        return [obj.path_id, data.m_RD.texture.path_id, getattr(data.m_RD.alphaTexture,'path_id', None)]

    elif obj.type == "Texture2D":
        extension = ".png"
        fp = f"{fp}{extension}"
        if not os.path.exists(fp):
            try:
                data.image.save(fp)
            except EOFError:
                pass
    
    return [obj.path_id]


if __name__ == '__main__':
    main()