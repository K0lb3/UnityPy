from __future__ import annotations

from collections import namedtuple
from os.path import basename
from typing import TYPE_CHECKING, Dict, Optional

from ..helpers import ImportHelper
from ..streams import EndianBinaryReader, EndianBinaryWriter

if TYPE_CHECKING:
    from ..environment import Environment

DirectoryInfo = namedtuple("DirectoryInfo", "path offset size")


class File(object):
    name: str
    files: Dict[str, File]
    environment: Environment
    cab_file: str
    is_changed: bool
    signature: str
    packer: str
    is_dependency: bool
    parent: Optional[File]

    def __init__(
        self,
        parent: Optional[File] = None,
        name: Optional[str] = None,
        is_dependency: bool = False,
    ):
        self.files = {}
        self.is_changed = False
        self.cab_file = "CAB-UnityPy_Mod.resS"
        self.parent = parent
        self.environment = self.environment = (
            getattr(parent, "environment", parent) if parent else None
        )
        self.name = basename(name) if isinstance(name, str) else ""
        self.is_dependency = is_dependency

    def get_assets(self):
        if isinstance(self, SerializedFile.SerializedFile):
            return self

        for f in self.files.values():
            if isinstance(f, (BundleFile.BundleFile, WebFile.WebFile)):
                for asset in f.get_assets():
                    yield asset
            elif isinstance(f, SerializedFile.SerializedFile):
                yield f

    def get_filtered_objects(self, obj_types=[]):
        if len(obj_types) == 0:
            return self.get_objects()
        for f in self.files.values():
            if isinstance(f, (BundleFile.BundleFile, WebFile.WebFile)):
                for obj in f.objects:
                    if obj.type in obj_types:
                        yield obj
            elif isinstance(f, SerializedFile.SerializedFile):
                for obj in f.objects.values():
                    if obj.type in obj_types:
                        yield obj

    def get_objects(self):
        for f in self.files.values():
            if isinstance(f, (BundleFile.BundleFile, WebFile.WebFile)):
                for obj in f.objects:
                    yield obj
            elif isinstance(f, SerializedFile.SerializedFile):
                for obj in f.objects.values():
                    yield obj
            elif isinstance(f, ObjectReader.ObjectReader):
                yield f

    def read_files(self, reader: EndianBinaryReader, files: list):
        # read file data and convert it
        for node in files:
            reader.Position = node.offset
            name = node.path
            node_reader = EndianBinaryReader(
                reader.read(node.size), offset=(reader.BaseOffset + node.offset)
            )
            f = ImportHelper.parse_file(
                node_reader, self, name, is_dependency=self.is_dependency
            )

            if isinstance(f, (EndianBinaryReader, SerializedFile.SerializedFile)):
                if self.environment:
                    self.environment.register_cab(name, f)

            # required for BundleFiles
            f.flags = getattr(node, "flags", 0)
            self.files[name] = f

    def get_writeable_cab(self, name: str = None):
        """
        Creates a new cab file in the bundle that contains the given data.
        This is usefull for asset types that use resource files.
        """

        if not name:
            name = self.cab_file

        if not name:
            return None

        if name in self.files:
            if isinstance(self.files[name], EndianBinaryWriter):
                return self.files[name]
            else:
                raise ValueError(
                    "This cab already exists and isn't an EndianBinaryWriter"
                )

        writer = EndianBinaryWriter()
        # try to find another resource file to copy the flags from
        for fname, f in self.files.items():
            if fname.endswith(".resS"):
                writer.flags = f.flags
                writer.endian = f.endian
                break
        else:
            writer.flags = 0
        writer.name = name
        self.files[name] = writer
        return writer

    @property
    def container(self):
        return {
            path: obj
            for f in self.files.values()
            if isinstance(f, File)
            for path, obj in f.container.items()
        }

    def get(self, key, default=None):
        return getattr(self, key, default)

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
        if isinstance(self.parent, File):
            self.parent.mark_changed()
        self.is_changed = True


# recursive import requires the import down here
from . import BundleFile, ObjectReader, SerializedFile, WebFile
