from __future__ import annotations

from abc import ABC, ABCMeta
from typing import TYPE_CHECKING, Any, Dict, Optional

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

    def __copy__(self) -> Object:
        clz = self.__class__
        data = {
            key: value
            for key, value in self.__dict__.items()
            if isinstance(key, str)
            and (not key.startswith("__") or key == "__node__")
            and not callable(value)
        }
        try:
            # covers UnknownObject
            return clz(**data)
        except TypeError:
            from ..helpers.TypeTreeHelper import get_annotation_keys

            keys = set(self.__dict__.keys())
            annotation_keys = get_annotation_keys(clz)
            extra_keys = keys - annotation_keys
            instance = clz(**{key: data[key] for key in annotation_keys})
            for key in extra_keys:
                setattr(instance, key, data[key])
            return instance


__all__ = [
    "Object",
]
