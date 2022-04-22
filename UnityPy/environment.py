from functools import reduce
import io
import os
from zipfile import ZipFile
import re
from . import files
from .files import File
from .enums import FileType
from .helpers import ImportHelper
from .streams import EndianBinaryReader
from .files import SerializedFile

reSplit = re.compile(r"(.+[/\\](\w+?\.split))\d+")


class Environment:
    files: dict
    cabs: dict
    path: str

    def __init__(self, *args):
        self.files = {}
        self.cabs = {}
        self.path = None
        self.out_path = os.path.join(os.getcwd(), "output")

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
                    self.files[str(len(self.files))] = self.load_file(stream=arg)

        if len(self.files) == 1:
            self.file = list(self.files.values())[0]

        if self.path == "":
            self.path = os.getcwd()

    def load_files(self, files: list):
        """Loads all files (list) into the AssetsManager and merges .split files for common usage."""
        # filter split files
        i = 0
        split_files = []
        for path in files:
            splitMatch = reSplit.match(path)
            if splitMatch:
                data = []
                basepath, basename = splitMatch.groups()

                if basepath in split_files:
                    continue

                split_files.append(basepath)
                data = []
                for i in range(0, 999):
                    item = f"{basepath}.split{i}"
                    if item in files:
                        with open(item, "rb") as f:
                            data.append(f.read())
                    elif i:
                        break
                data = b"".join(data)

                self.files[basepath] = self.load_file(data, self, basename)
            else:
                self.files[path] = self.cabs[os.path.basename(path)] = self.load_file(
                    open(path, "rb").read(), self, path
                )

    def load_folder(self, path: str):
        """Loads all files in the given path and its subdirs into the AssetsManager."""
        self.load_files(
            [
                os.path.join(root, f)
                for root, dirs, files in os.walk(path)
                for f in files
            ]
        )

    def reduce_path(self, fp: str) -> str:
        return fp[len(self.path) :].lstrip("/\\")

    def load(self, files: list):
        """Loads all files into the AssetsManager."""
        self.files.update(
            {
                self.reduce_path(f): self.load_file(open(f, "rb"), self, f)
                for f in files
                if os.path.exists(f)
            }
        )

    def load_file(self, stream, parent=None, name: str = None):
        if not parent:
            parent = self
        typ, reader = ImportHelper.check_file_type(stream)
        try:
            stream_name = (
                name
                if name
                else getattr(
                    stream,
                    "name",
                    str(stream.__hash__()) if hasattr(stream, "__hash__") else "",
                )
            )
            if typ == FileType.AssetsFile:
                f = files.SerializedFile(reader, parent, name=stream_name)
                self.register_cab(stream_name, f)
                return f
            elif typ == FileType.BundleFile:
                return files.BundleFile(reader, parent, name=stream_name)
            elif typ == FileType.WebFile:
                return files.WebFile(reader, parent, name=stream_name)
            elif typ == FileType.ZIP:
                self.load_zip_file(stream)
            elif typ == FileType.ResourceFile:
                f = EndianBinaryReader(stream)
                self.register_cab(stream_name, f)
                return f
        except Exception as e:
            # just to be sure
            # cuz the SerializedFile detection isn't perfect
            print("Error loading, reverting to EndianBinaryReader:\n", e)
            return EndianBinaryReader(stream)

    def load_zip_file(self, value):
        buffer = None
        if isinstance(value, str) and os.path.exists(value):
            buffer = open(value, "rb")
        elif isinstance(value, (bytes, bytearray)):
            buffer = io.BytesIO(value)
        elif isinstance(value, (io.BufferedReader, io.BufferedIOBase)):
            buffer = value

        z = ZipFile(buffer)
        split_files = []
        namelist = z.namelist()
        for path in namelist:
            splitMatch = reSplit.match(path)
            if splitMatch:
                data = []
                basepath, basename = splitMatch.groups()

                if basepath in split_files:
                    continue

                split_files.append(basepath)
                data = []
                for i in range(0, 999):
                    item = f"{basepath}.split{i}"
                    if item in namelist:
                        with z.open(item) as f:
                            data.append(f.read())
                    elif i:
                        break
                data = b"".join(data)

                self.files[basepath] = self.cabs[basename] = self.load_file(data, self)
            else:
                self.files[path] = self.cabs[os.path.basename(path)] = self.load_file(
                    z.open(path).read(), self
                )

        z.close()

    def save(self, pack="none"):
        """Saves all changed assets.
        Mark assets as changed using `.mark_changed()`.
        pack = "none" (default) or "lz4"
        """
        for f in self.files:
            if self.files[f].is_changed:
                with open(
                    os.path.join(self.out_path, os.path.basename(f)), "wb"
                ) as out:
                    out.write(self.files[f].save(packer=pack))

    @property
    def objects(self) -> list:
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

        def gen_all_asset_files(file, ret=[]):
            for f in getattr(file, "files", {}).values():
                if isinstance(f, SerializedFile):
                    ret.append(f)
                else:
                    gen_all_asset_files(f, ret)
            return ret

        return gen_all_asset_files(self)

    def get(self, key: str, default=None):
        return getattr(self, key, default)

    def register_cab(self, name: str, item: object) -> None:
        self.cabs[os.path.basename(name.lower())] = item

    def get_cab(self, name: str) -> object:
        return self.cabs.get(os.path.basename(name.lower()), None)
