import io
import ntpath
import os
import re
from typing import TYPE_CHECKING, BinaryIO, Callable, Dict, List, Optional, Union, cast
from zipfile import ZipFile

from fsspec import AbstractFileSystem
from fsspec.implementations.local import LocalFileSystem

from .enums import FileType
from .files import BundleFile, File, ObjectReader, SerializedFile, WebFile
from .helpers.ContainerHelper import ContainerHelper
from .helpers.ImportHelper import (
    FileSourceType,
    check_file_type,
    find_sensitive_path,
    parse_file,
)
from .streams import EndianBinaryReader

if TYPE_CHECKING:
    from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator

reSplit = re.compile(r"(.*?([^\/\\]+?))\.split\d+")


class Environment:
    files: Dict[str, Union[SerializedFile, BundleFile, WebFile, EndianBinaryReader]]
    cabs: Dict[str, Union[SerializedFile, EndianBinaryReader]]
    path: str
    local_files: List[str]
    local_files_simple: List[str]
    typetree_generator: Optional["TypeTreeGenerator"] = None

    def __init__(self, *args: FileSourceType, fs: Optional[AbstractFileSystem] = None, path: Optional[str] = None):
        self.files = {}
        self.cabs = {}
        self.fs = fs or LocalFileSystem()
        self.local_files = []
        self.local_files_simple = []

        if path is None:
            # if no path is given, use the current working directory
            if isinstance(self.fs, LocalFileSystem):
                self.path = os.getcwd()
            else:
                self.path = ""
        else:
            self.path = path

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
                    self.load_file(file=arg)

        if len(self.files) == 1:
            self.file = list(self.files.values())[0]

    def load_files(self, files: List[str]):
        """Loads all files (list) into the Environment and merges .split files for common usage."""
        self.load_assets(files, lambda x: open(x, "rb"))

    def load_folder(self, path: str):
        """Loads all files in the given path and its subdirs into the Environment."""
        self.load_files([self.fs.sep.join([root, f]) for root, dirs, files in self.fs.walk(path) for f in files])

    def load(self, files: List[str]):
        """Loads all files into the Environment."""
        self.files.update(
            {ntpath.basename(f): self.load_file(self.fs.open(f, "rb"), self, f) for f in files if self.fs.exists(f)}
        )

    def _load_split_file(self, basename: str) -> bytes:
        file: List[bytes] = []
        for i in range(0, 999):
            item = f"{basename}.split{i}"
            if self.fs.exists(item):
                with self.fs.open(item, "rb") as f:
                    file.append(f.read())  # type: ignore
            elif i:
                break
        return b"".join(file)

    def load_file(
        self,
        file: FileSourceType,
        parent: Optional[Union["Environment", File]] = None,
        name: Optional[str] = None,
        is_dependency: bool = False,
    ):
        if not parent:
            parent = self

        if isinstance(file, str):
            split_match = reSplit.match(file)
            if split_match:
                basepath, _basename = split_match.groups()
                assert isinstance(basepath, str)
                name = basepath
                file = self._load_split_file(basepath)
            else:
                name = file
                if not os.path.exists(file):
                    # relative paths are in the asset directory, not the cwd
                    if not os.path.isabs(file):
                        file = os.path.join(self.path, file)
                    # for dependency loading of split files
                    if os.path.exists(f"{file}.split0"):
                        file = self._load_split_file(file)
                    # Unity paths are case insensitive,
                    # so we need to find "Resources/Foo.asset" when the record says "resources/foo.asset"
                    elif not os.path.exists(file):
                        file_path = find_sensitive_path(self.path, file)
                        if file_path:
                            file = file_path
                        else:
                            return None
                            # raise FileNotFoundError(f"File {file} not found in {self.path}")

                if isinstance(file, str):
                    file = self.fs.open(file, "rb")

        typ, reader = check_file_type(file)

        stream_name = (
            name
            if name
            else getattr(
                file,
                "name",
                str(file.__hash__()) if hasattr(file, "__hash__") else "",  # type: ignore
            )
        )

        if typ == FileType.ZIP:
            f = self.load_zip_file(file)
        else:
            f = parse_file(reader, self, name=stream_name, typ=typ, is_dependency=is_dependency)

        if isinstance(f, (SerializedFile, EndianBinaryReader)):
            self.register_cab(stream_name, f)

        self.files[stream_name] = f
        return f

    def load_zip_file(self, value):
        if isinstance(value, str) and self.fs.exists(value):
            buffer = cast(io.BufferedReader, self.fs.open(value, "rb"))
        elif isinstance(value, (bytes, bytearray, memoryview)):
            buffer = io.BytesIO(value)
        elif isinstance(value, (io.BufferedReader, io.BufferedIOBase)):
            buffer = value
        else:
            raise TypeError("Unsupported type for loading zip file")

        z = ZipFile(buffer)
        self.load_assets(z.namelist(), lambda x: z.open(x, "r"))  # type: ignore
        z.close()

    def save(self, pack="none", out_path="output"):
        """Saves all changed assets.
        Mark assets as changed using `.mark_changed()`.
        pack = "none" (default) or "lz4"
        """
        for fname, fitem in self.files.items():
            if getattr(fitem, "is_changed", False):
                with open(self.fs.sep.join([out_path, ntpath.basename(fname)]), "wb") as out:
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
                for sub_item in item.files.values():
                    ret.extend(search(sub_item))
                return ret

            return ret

        return search(self)

    @property
    def container(self) -> ContainerHelper:
        """Returns a dictionary of all objects in the Environment."""
        container = []
        for f in self.cabs.values():
            if isinstance(f, SerializedFile) and not f.is_dependency:
                container.extend(f.container.container)

        return ContainerHelper(container)

    @property
    def assets(self) -> list:
        """
        Lists all assets / SerializedFiles within this environment.
        """

        def gen_all_asset_files(file, ret: Optional[list] = None):
            if ret is None:
                ret = []

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

    def register_cab(self, name: str, item: Union[SerializedFile, EndianBinaryReader]) -> None:
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

    def get_cab(self, name: str) -> Union[SerializedFile, EndianBinaryReader, None]:
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

    def load_assets(self, assets: List[str], open_f: Callable[[str], BinaryIO]):
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
                basepath, _basename = splitMatch.groups()

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
        fp = self.fs.sep.join([self.path, name])
        if self.fs.exists(fp):
            return self.load_file(fp, name=name, is_dependency=is_dependency)

        if len(self.local_files) == 0 and self.path:
            for root, _, files in self.fs.walk(self.path):
                for f in files:
                    self.local_files.append(self.fs.sep.join([root, f]))
                    self.local_files_simple.append(self.fs.sep.join([root, simplify_name(f)]))

        if name in self.local_files:
            fp = name
        elif simple_name in self.local_files_simple:
            fp = self.local_files[self.local_files_simple.index(simple_name)]
        else:
            fp = next((f for f in self.local_files if f.endswith(name)), None)
            if not fp:
                fp = next(
                    (f for f in self.local_files_simple if f.endswith(simple_name)),
                    None,
                )
            if not fp:
                raise FileNotFoundError(f"File {name} not found in {self.path}")

        return self.load_file(fp, name=name, is_dependency=is_dependency)


def simplify_name(name: str) -> str:
    """Simplifies a name by:
    - removing the extension
    - removing the path
    - converting to lowercase
    """
    return ntpath.basename(name).lower()
