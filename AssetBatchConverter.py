import os, sys
from glob import glob
from UnityPy import AssetsManager
from collections import Counter
import zipfile
from tqdm import tqdm

TYPES = ['Sprite', 'Texture2D', 'TextAsset', 'MonoBehaviour']

ROOT = os.path.abspath(os.getcwd()) # base directory
DST = os.path.join(ROOT, "output") # destination folder
ASSETS = os.path.join(ROOT,"input\\*.*") # source folder or file

def main():
    os.makedirs(DST, exist_ok=True)
    for file_name in glob(ASSETS):
        extension = os.path.splitext(file_name)[1]
        src = os.path.realpath(os.path.join(ROOT, file_name))

        am = None
        if extension == ".zip":
            archive = zipfile.ZipFile(src, 'r')
            for zf in archive.namelist():
                am = AssetsManager(archive.open(zf))
                print("Parsing file:", zf)
        else:
            am = AssetsManager(src)
            print("Parsing file:", src)
        if am is None:
            continue
        #am.out_path = DST
        am.ignore_dir_lvls = 2
        am.progress_function = tqdm
        am.process(export_obj, TYPES)
        #am.save()

def make_path(*args):
    fp = os.path.join(*args)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    return fp

def export_obj(obj, asset: str, local_path: str) -> list:
    objfmt = str(obj.type)

    data = obj.read()
    name = data.name if (data.name is not None and data.name != '') else "unnamed asset"
    fname, extension = os.path.splitext(name)
    objname = "%s-%s-%d" % (fname, os.path.basename(asset), obj.path_id)

    if objfmt == "TextAsset":
        if data.script:
            fp = f"{make_path(DST, local_path, os.path.split(fname)[0], objname)}.txt"
            if not os.path.isfile(fp):
                with open(fp, "wb") as f:
                    f.write(data.script)

    elif objfmt == "Sprite":
        fp = f"{make_path(DST, local_path, fname)}.png"
        if not os.path.isfile(fp):
            data.image.save(fp)

    elif objfmt == "MonoBehaviour":
        # file_offset = data.reader.byte_base_offset + data.reader.byte_start
        # written_offset = data.reader.byte_start - data.reader.byte_header_offset
        script = data.script.read()
        if not script: return []
        fp = f"{make_path(DST, local_path, script.namespace, script.class_name, objname)}.dat"
        if not os.path.isfile(fp):
            with open(fp, "wb") as f:
                f.write(data.get_raw_data())

    elif objfmt == "Texture2D":
        fp = f"{make_path(DST, local_path, fname)}.png"
        if not os.path.isfile(fp):
            try:
                data.image.save(fp)
            except Exception as e:
                if data.m_TextureFormat.name is not None:
                    objfmt = data.m_TextureFormat.name
                print(repr(e), "in file:", objname, "object type:", objfmt)
                return []
    #else:
    #     fp = "%s-%s-%d" % (asset, obj.path_id, obj.type)

    #print("writing", obj.type, "to", fp, "format", objfmt)
    return [obj.path_id]


if __name__ == '__main__':
    main()
