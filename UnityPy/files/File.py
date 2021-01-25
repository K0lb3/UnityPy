from ..enums import FileType
from ..helpers import CompressionHelper, ImportHelper
from ..streams import EndianBinaryReader, EndianBinaryWriter

from collections import namedtuple
DirectoryInfo = namedtuple("DirectoryInfo", "path offset size")

class File(object):
    name: str
    files: dict
    is_changed: bool
    signature: str
    packer: str
    #parent: File
    
    def __init__(self, parent = None):
        self.files = {}
        self.is_changed = False
        self.parent  = parent

    def get_objects(self):
        for f in self.files.values():
            if isinstance(f, (BundleFile.BundleFile, WebFile.WebFile)):
                for obj in f.objects:
                    yield obj
            elif isinstance(f, SerializedFile.SerializedFile):
                for obj in f.objects.values():
                    yield obj
            elif isinstance(f, SerializedFile.ObjectReader):
                yield f

    def read_files(self, reader : EndianBinaryReader, files : list):
        # read file data and convert it
        for node in files:
            reader.Position = node.offset
            name = node.path
            f = EndianBinaryReader(reader.read(node.size), offset=(reader.BaseOffset + node.offset))
            #f._flag = getattr(node, "flags", None)  # required for save
            typ, _ = ImportHelper.check_file_type(f)
            if typ == FileType.BundleFile:
                f = BundleFile.BundleFile(f, self)
            elif typ == FileType.WebFile:
                f = WebFile.WebFile(f, self)
            elif typ == FileType.AssetsFile:
                # pre-check if resource file
                if not name.endswith((".resS", ".resource", ".config", ".xml", ".dat")):
                    # try to load the file as serialized file
                    try:
                        f = SerializedFile.SerializedFile(f, self)
                    except ValueError:
                        pass
            # required for BundleFiles
            f.flags = getattr(node,"flags",0)
            self.files[name] = f

    @property
    def container(self):
        return {
            path : obj
            for f in self.files.values()
            if isinstance(f, File)
            for path,obj in f.container.items()
        }


    def keys(self):
        return self.files.keys()

    def items(self):
        return self.files.items()

    def values(self):
        return self.files.values()

    def __getitem__(self, item):
        return self.files[item]

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def mark_changed(self):
        self.is_changed = True

from . import BundleFile, SerializedFile, WebFile