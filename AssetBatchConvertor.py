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

os.makedirs(DST, exist_ok=True)

debug = True

def main():
    for root, dirs, files in os.walk(ASSETS, topdown=False):
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
                extracted = []
                local_path = []
                # check which mode we will have to use
                num_cont = sum(1 for obj in asset.container.values() if obj.type in TYPES)
                num_objs = sum(1 for obj in asset.objects.values() if obj.type in TYPES)

                # first we extract the assets in the container
                for asset_path, obj in asset.container.items():
                    fp = os.path.join(DST, *asset_path.split('/'))
                    export_obj(obj, fp)

                    local_path.append(
                        os.path.splitext(asset_path)[0]
                        if asset_path.endswith(".prefab")
                        else
                        os.path.dirname(asset_path)
                        )
                
                # way more assets without path then with path,
                # therefore we get the general path from the container
                # and then extract all assets depending on that
                if num_objs > num_cont * 2:
                    if len(local_path) > 1:
                        if len(set(local_path)) == 1:
                            local_path = local_path[0]
                        else:
                            local_path = mode(local_path)
                    else:
                        local_path = os.path.join(DST, *local_path[0].split('/'))

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
    try:
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
                data.image.save(fp)
        
        return [obj.path_id]
    
    except Exception as e:
        print(fp, e)
        return([])


if __name__ == '__main__':
    main()