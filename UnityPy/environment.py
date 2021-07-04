import io
import os
from zipfile import ZipFile

from . import files
from .files import File
from .enums import FileType
from .helpers import ImportHelper
from .streams import EndianBinaryReader
from .files import SerializedFile

class Environment:
    files: dict
    path: str

    def __init__(self, *args):
        self.files = {}
        self.path = "."

        if args:
            for arg in args:
                if isinstance(arg, str):
                    if os.path.isfile(arg):
                        if os.path.splitext(arg)[-1] in [".apk", ".zip"]:
                            self.load_zip_file(arg)
                        else:
                            self.path = os.path.dirname(arg)
                            self.load_files([arg])
                    elif os.path.isdir(arg):
                        self.path = arg
                        self.load_folder(arg)
                else:
                    self.path = None
                    self.files[str(len(self.files))
                               ] = self.load_file(stream=arg)

        if len(self.files) == 1:
            self.file = list(self.files.values())[0]

    def load_files(self, files: list):
        """Loads all files (list) into the AssetsManager and merges .split files for common usage."""
        # ImportHelper.merge_split_assets(path)
        # to_read_file = ImportHelper.processing_split_files(files)
        self.load(files)

    def load_folder(self, path: str):
        """Loads all files in the given path and its subdirs into the AssetsManager."""
        ImportHelper.merge_split_assets(path, True)
        files = ImportHelper.list_all_files(path)
        to_read_file = ImportHelper.processing_split_files(files)
        self.load(to_read_file)

    def load(self, files: list):
        """Loads all files into the AssetsManager."""
        for f in files:
            with open(f, "rb") as handle:
                self.files[f[len(self.path):].lstrip(
                    "/\\")] = self.load_file(handle, self)

    def load_file(self, stream, parent=None):
        if not parent:
            parent = self
        typ, reader = ImportHelper.check_file_type(stream)
        try:
            if typ == FileType.AssetsFile:
                return files.SerializedFile(reader, parent)
            elif typ == FileType.BundleFile:
                return files.BundleFile(reader, parent)
            elif typ == FileType.WebFile:
                return files.WebFile(reader, parent)
            elif typ == FileType.ZIP:
                self.load_zip_file(stream)
            elif typ == FileType.ResourceFile:
                return EndianBinaryReader(stream)
        except:
            # just to be sure
            # cuz the SerializedFile detection isn't perfect
            return EndianBinaryReader(stream)

    def load_zip_file(self, value):
        buffer = None
        if isinstance(value, str) and os.path.exists(value):
            buffer = open(value, "rb")
        elif isinstance(value, (bytes, bytearray)):
            buffer = ZipFile(io.BytesIO(value))
        elif isinstance(value, (io.BufferedReader, io.BufferedIOBase)):
            buffer = value

        z = ZipFile(buffer)
        for path in z.namelist():
            stream = z.open(path)
            if stream._orig_file_size == 0:
                continue
            *path, name = path.split("/")
            cur = self
            for d in path:
                if d not in cur.files:
                    cur.files[d] = files.File(self)
                cur = cur.files[d]
            cur.files[name] = self.load_file(stream, cur)
        z.close()

    @property
    def objects(self):
        def search(item):
            ret = []
            if not isinstance(item, Environment) and getattr(item, "objects", None):
                # serialized file
                return [val for val in item.objects.values()]

            elif getattr(item, "files", None):  # WebBundle and BundleFile
                # bundle
                for item in item.files.values():
                    ret.extend(search(item))
                return ret

            return ret

        return search(self)

    @property
    def container(self):
        return {
            path: obj
            for f in self.files.values()
            if isinstance(f, File)
            for path, obj in f.container.items()
        }

    @property
    def assets(self) -> list:
        """
        Lists all assets / SerializedFiles within this environment.
        """
        def gen_all_asset_files(file, ret  = []):
            for f in getattr(file, "files", {}).values():
                if isinstance(f, SerializedFile):
                    ret.append(f)
                else:
                    gen_all_asset_files(f, ret)
            return ret
        return gen_all_asset_files(self)

    def get(self, key, default=None):
        return getattr(self, key, default)
