from __future__ import annotations
from abc import ABC, ABCMeta
from typing import TYPE_CHECKING, Dict, Any, Optional

if TYPE_CHECKING:
    from ..files.ObjectReader import ObjectReader
    from ..files.SerializedFile import SerializedFile


class Object(ABC, metaclass=ABCMeta):
    object_reader: Optional[ObjectReader] = None

    def __init__(self, **kwargs: Dict[str, Any]) -> None:
        self.__dict__.update(**kwargs)

    def set_object_reader(self, object_info: ObjectReader[Any]):
        self.object_reader = object_info

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"

    @property
    def assets_file(self) -> Optional[SerializedFile]:
        if self.object_reader:
            return self.object_reader.assets_file
        return None

    def save(self) -> None:
        if self.object_reader is None:
            raise ValueError("ObjectReader not set")

        self.object_reader.save_typetree(self)
