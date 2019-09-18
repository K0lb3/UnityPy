from UnityPy import AssetsManager

from decrunch import File as CrunchFile
from decrunch_unity import File as CrunchFile_U

def DecompressCRN(image_data,i):
    if i == 1:
        # Unity Crunch
        image_data = bytes(CrunchFile_U(image_data).decode_level(0))
        image_data_size = len(image_data)
    else: #normal crunch
        image_data = bytes(CrunchFile(image_data).decode_level(0))
        image_data_size = len(image_data)

a = AssetsManager()
fp = "S:\\Datamines\\Disgea RPG\\Assets\\raw\\assetbundle\\images\\chara\\illust\\1"
a.load_file(fp)
d=list(list(a.assets.values())[0].container.values())[0].read()
img = d.m_RD.texture.read()
DecompressCRN(img.image_data, 1)