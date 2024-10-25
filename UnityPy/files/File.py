from __future__ import annotations

from abc import ABC, ABCMeta, abstractmethod
from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterator,
    List,
    Optional,
    Self,
    Type,
    TypeVar,
    cast,
)

from attrs import define

from ..streams import EndianBinaryReader, EndianBinaryWriter

if TYPE_CHECKING:
    from .ObjectInfo import ObjectInfo

PARSEABLE_FILETYPES: List[Type[File]] = []

T = TypeVar("T")


def parseable_filetype(cls: Type[T]) -> Type[T]:
    """Decorator to register a class as parseable."""
    assert issubclass(cls, File)
    PARSEABLE_FILETYPES.append(cls)
    return cls


def parse_file(
    reader: EndianBinaryReader,
    name: str,
    path: str,
    parent: Optional[ContainerFile] = None,
    is_dependency: bool = False,
) -> Optional[File]:
    start_pos = reader.tell()
    for cls in PARSEABLE_FILETYPES:
        try:
            probe_result = cls.probe(reader)
        except (EOFError, UnicodeDecodeError, IndexError):
            probe_result = False

        reader.seek(start_pos)

        if probe_result:
            file = cls(name, path, parent, is_dependency)
            file.parse(reader)
            return file


class File(ABC, metaclass=ABCMeta):
    name: str
    path: str
    parent: Optional[ContainerFile]
    is_dependency: bool
    reader: Optional[EndianBinaryReader]

    def __init__(
        self,
        name: str,
        path: str,
        parent: Optional[ContainerFile] = None,
        is_dependency: bool = False,
        reader: Optional[EndianBinaryReader] = None,
    ):
        self.name = name
        self.path = path
        self.parent = parent
        self.is_dependency = is_dependency
        self.reader = reader

    @classmethod
    @abstractmethod
    def probe(cls, reader: EndianBinaryReader) -> bool:
        """Check if the file is of this type.

        Args:
            reader (EndianBinaryReader): The reader to read from.

        Returns:
            bool: Whether the file is of this type.
        """
        pass

    @abstractmethod
    def parse(self, reader: Optional[EndianBinaryReader] = None) -> Self:
        """Parse the file from the reader.

        Args:
            reader (EndianBinaryReader): The reader to read from.
        """
        pass

    @abstractmethod
    def dump(self, writer: Optional[EndianBinaryWriter] = None) -> EndianBinaryWriter:
        """Dump the file to the writer.

        Args:
            writer (EndianBinaryWriter): The writer to write to.
        """
        pass

    def __enter__(self):
        return self

    def __exit__(self):
        pass

    @abstractmethod
    def get_objects(self) -> List[ObjectInfo[Any]]:
        """Get all objects contained in this file and its childs.

        Returns:
            List[Object]: The objects in this file.
        """
        pass

    @abstractmethod
    def get_containers(self) -> Dict[str, List[ObjectInfo[Any]]]:
        """Get all containers contained in this file and its childs.

        Returns:
            List[Tuple[str, Object]]: The containers in this file.
        """
        pass

    def _opt_get_set_reader(
        self, reader: Optional[EndianBinaryReader] = None
    ) -> EndianBinaryReader:
        if reader is not None:
            self.reader = reader
        if self.reader is None:
            raise ValueError("No reader provided")
        return self.reader


class ResourceFile(File):
    reader: EndianBinaryReader  # type: ignore

    @classmethod
    def probe(cls, reader: EndianBinaryReader) -> bool:
        return True

    def parse(self, reader: Optional[EndianBinaryReader] = None) -> Self:
        if reader is not None:
            self.reader = reader  # type: ignore
        return self

    def dump(self, writer: Optional[EndianBinaryWriter] = None) -> EndianBinaryWriter:
        if writer is None:
            writer = EndianBinaryWriter(endian="<")
        writer.write_bytes(self.reader.get_bytes())
        return writer

    def get_objects(self) -> List[ObjectInfo[Any]]:
        raise ValueError("ResourceFile does not contain objects")

    def get_containers(self) -> Dict[str, List[ObjectInfo[Any]]]:
        raise ValueError("ResourceFile does not contain containers")


@define(slots=True)
class DirectoryInfo:
    offset: int
    size: int
    path: str
    flags: Optional[int] = None


# TODO: refractor name to avoid confusion with get_container / container paths
class ContainerFile(File, ABC, metaclass=ABCMeta):
    childs: List[File]
    directory_infos: List[DirectoryInfo]
    directory_reader: Optional[EndianBinaryReader]

    # @abstractmethod
    # def get_serialized_files(self) -> List[SerializedFile]:
    #     """Get all serialized files contained in this file and its childs.

    #     Returns:
    #         List[SerializedFile]: The serialized files in this file.
    #     """
    #     pass
    def __init__(
        self,
        name: str,
        path: str,
        parent: Optional[ContainerFile] = None,
        is_dependency: bool = False,
        reader: Optional[EndianBinaryReader] = None,
    ):
        super().__init__(name, path, parent, is_dependency, reader)
        self.childs = []
        self.directory_infos = []
        self.directory_reader = None

    def parse_files(self):
        """Parse the directory infos and all files in this file."""
        if self.directory_reader is None:
            raise ValueError("directory_reader is not set")

        for info in self.directory_infos:
            path_parts = info.path.split("/")
            name = path_parts[-1]
            path = f"{self.path}/{info.path}"

            # subreader = self.directory_reader.create_sub_reader(info.offset, info.size)
            # subreader.seek(0)
            self.directory_reader.seek(info.offset)
            file = parse_file(
                self.directory_reader, name, path, self, self.is_dependency
            )
            self.childs.append(
                file
                if file is not None
                else ResourceFile(name, path, self, False, self.directory_reader)
            )

    def traverse(self) -> Iterator[File]:
        if not self.childs and self.directory_infos:
            self.parse_files()
        for child in self.childs:
            if isinstance(child, ContainerFile):
                yield from child.traverse()
            elif isinstance(child, ResourceFile):
                continue
            yield child

    def get_objects(self) -> List[ObjectInfo[Any]]:
        return [obj for child in self.traverse() for obj in child.get_objects()]

    def get_containers(self) -> Dict[str, List[ObjectInfo[Any]]]:
        containers: Dict[str, List[ObjectInfo[Any]]] = defaultdict(list)
        for child in self.traverse():
            for container_path, obj in child.get_containers().items():
                containers[container_path].extend(obj)

        return cast(Dict[str, List[ObjectInfo[Any]]], containers)
