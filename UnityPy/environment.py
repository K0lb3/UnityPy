import io
import os
import ntpath
import re
from typing import List, Callable, Dict, Union
from zipfile import ZipFile

from fsspec import AbstractFileSystem
from fsspec.implementations.local import LocalFileSystem


from .files import File, ObjectReader, SerializedFile
from .enums import FileType
from .helpers import ImportHelper
from .streams import EndianBinaryReader

reSplit = re.compile(r"(.*?([^\/\\]+?))\.split\d+")


class Environment:
    files: dict
    cabs: dict
    path: str
    local_files: List[str]
    local_files_simple: List[str]

    def __init__(self, *args, fs: AbstractFileSystem = None):
        self.files = {}
        self.cabs = {}
        self.path = None
        self.fs = fs or LocalFileSystem()
        self.local_files = []
        self.local_files_simple = []

        if args:
            for arg in args:
                if isinstance(arg, str):
                    if self.fs.isfile(arg):
                        if ntpath.splitext(arg)[-1] in [".apk", ".zip"]:
                            self.load_zip_file(arg)
                        else:
                            self.path = ntpath.dirname(arg)
                            if reSplit.match(arg):
                                self.load_files([arg])
                            else:
                                self.load_file(arg)
                    elif self.fs.isdir(arg):
                        self.path = arg
                        self.load_folder(arg)
                else:
                    self.path = None
                    self.load_file(file=arg)

        if len(self.files) == 1:
            self.file = list(self.files.values())[0]

        if self.path == "":
            self.path = os.getcwd()

    def load_files(self, files: List[str]):
        """Loads all files (list) into the Environment and merges .split files for common usage."""
        self.load_assets(files, lambda x: open(x, "rb"))

    def load_folder(self, path: str):
        """Loads all files in the given path and its subdirs into the Environment."""
        self.load_files(
            [
                self.fs.sep.join([root, f])
                for root, dirs, files in self.fs.walk(path)
                for f in files
            ]
        )

    def load(self, files: list):
        """Loads all files into the Environment."""
        self.files.update(
            {
                ntpath.basename(f): self.load_file(self.fs.open(f, "rb"), self, f)
                for f in files
                if self.fs.exists(f)
            }
        )

    def _load_split_file(self, basename):
        file = []
        for i in range(0, 999):
            item = f"{basename}.split{i}"
            if self.fs.exists(item):
                with self.fs.open(item, "rb") as f:
                    file.append(f.read())
            elif i:
                break
        return b"".join(file)

    def load_file(
        self,
        file: Union[io.IOBase, str],
        parent: Union["Environment", File] = None,
        name: str = None,
        is_dependency: bool = False,
    ):
        if not parent:
            parent = self

        if isinstance(file, str):
            split_match = reSplit.match(file)
            if split_match:
                basepath, basename = split_match.groups()
                name = basepath
                file = self._load_split_file(name)
            else:
                name = file
                if not os.path.exists(file):
                    # relative paths are in the asset directory, not the cwd
                    if not os.path.isabs(file):
                        file = os.path.join(self.path, file)
                    # for dependency loading of split files
                    if os.path.exists(f"{file}.split0"):
                        file = self._load_split_file(file)
                    # Unity paths are case insensitive, so we need to find "Resources/Foo.asset" when the record says "resources/foo.asset"
                    elif not os.path.exists(file):
                        file = ImportHelper.find_sensitive_path(self.path, file)
                    # nonexistent files might be packaging errors or references to Unity's global Library/
                    if file is None:
                        return
                if type(file) == str:
                    file = self.fs.open(file, "rb")

        typ, reader = ImportHelper.check_file_type(file)

        stream_name = (
            name
            if name
            else getattr(
                file,
                "name",
                str(file.__hash__()) if hasattr(file, "__hash__") else "",
            )
        )

        if typ == FileType.ZIP:
            f = self.load_zip_file(file)
        else:
            f = ImportHelper.parse_file(
                reader, self, name=stream_name, typ=typ, is_dependency=is_dependency
            )
        
        if isinstance(f, (SerializedFile, EndianBinaryReader)):
            self.register_cab(stream_name, f)

        self.files[stream_name] = f


    def load_zip_file(self, value):
        buffer = None
        if isinstance(value, str) and self.fs.exists(value):
            buffer = open(value, "rb")
        elif isinstance(value, (bytes, bytearray)):
            buffer = io.BytesIO(value)
        elif isinstance(value, (io.BufferedReader, io.BufferedIOBase)):
            buffer = value

        z = ZipFile(buffer)
        self.load_assets(z.namelist(), lambda x: z.open(x, "r"))
        z.close()

    def save(self, pack="none", out_path="output"):
        """Saves all changed assets.
        Mark assets as changed using `.mark_changed()`.
        pack = "none" (default) or "lz4"
        """
        for fname, fitem in self.files.items():
            if getattr(fitem, "is_changed", False):
                with open(
                    self.fs.sep.join([out_path, ntpath.basename(fname)]), "wb"
                ) as out:
                    out.write(fitem.save(packer=pack))

    @property
    def objects(self) -> List[ObjectReader]:
        """Returns a list of all objects in the Environment."""

        def search(item):
            ret = []
            if not isinstance(item, Environment) and getattr(item, "objects", None):
                # serialized file
                if getattr(item, "is_dependency", False):
                    return []
                return [val for val in item.objects.values()]

            elif getattr(item, "files", None):  # WebBundle and BundleFile
                # bundle
                for item in item.files.values():
                    ret.extend(search(item))
                return ret

            return ret

        return search(self)

    @property
    def container(self) -> Dict[str, ObjectReader]:
        """Returns a dictionary of all objects in the Environment."""
        return {
            path: obj
            for f in self.files.values()
            if isinstance(f, File) and not f.is_dependency
            for path, obj in f.container.items()
        }

    @property
    def assets(self) -> list:
        """
        Lists all assets / SerializedFiles within this environment.
        """

        def gen_all_asset_files(file, ret=[]):
            for f in getattr(file, "files", {}).values():
                if getattr(f, "is_dependency", False):
                    continue
                if isinstance(f, SerializedFile):
                    ret.append(f)
                else:
                    gen_all_asset_files(f, ret)
            return ret

        return gen_all_asset_files(self)

    def get(self, key: str, default=None):
        return getattr(self, key, default)

    def register_cab(self, name: str, item: File) -> None:
        """
        Registers a cab file.

        Parameters
        ----------
        name : str
            The name of the cab file.
        item : File
            The file to register.
        """
        self.cabs[simplify_name(name)] = item

    def get_cab(self, name: str) -> File:
        """
        Returns the cab file with the given name.

        Parameters
        ----------
        name : str
            The name of the cab file.

        Returns
        -------
        File
            The cab file.
        """
        return self.cabs.get(simplify_name(name), None)

    def load_assets(self, assets: List[str], open_f: Callable[[str], io.IOBase]):
        """
        Load all assets from a list of files via the given open_f function.

        Parameters
        ----------
        assets : List[str]
            List of files to load.
        open_f : Callable[[str], io.IOBase]
            Function to open the files.
            The function takes a file path and returns an io.IOBase object.
        """
        split_files = []
        for path in assets:
            splitMatch = reSplit.match(path)
            if splitMatch:
                basepath, basename = splitMatch.groups()

                if basepath in split_files:
                    continue

                split_files.append(basepath)
                data = self._load_split_file(basepath)
                path = basepath
            else:
                data = open_f(path).read()
            self.load_file(data, name=path)

    def find_file(self, name: str, is_dependency: bool = True) -> Union[File, None]:
        """
        Finds a file in the environment.

        Parameters
        ----------
        name : str
            The name of the file.
        is_dependency : bool
            Whether the file is a dependency.

        Returns
        -------
        File | None
            The file if it was found, otherwise None.
        """
        simple_name = simplify_name(name)
        cab = self.get_cab(simple_name)
        if cab:
            return cab

        if len(self.local_files) == 0 and self.path:
            for root, _, files in self.fs.walk(self.path):
                for name in files:
                    self.local_files.append(self.fs.sep.join([root, name]))

        if name in self.local_files:
            fp = name
        elif simple_name in self.local_files_simple:
            fp = self.local_files[self.local_files_simple.index(simple_name)]
        else:
            raise FileNotFoundError(f"File {name} not found in {self.path}")

        f = self.load_file(fp, name=name, is_dependency=is_dependency)
        return f


def simplify_name(name: str) -> str:
    """Simplifies a name by:
    - removing the extension
    - removing the path
    - converting to lowercase
    """
    return ntpath.basename(name).lower()
