from __future__ import annotations
from typing import TypeVar, Generic, TYPE_CHECKING, Optional, Any, cast

from attr import define

if TYPE_CHECKING:
    from ..files.ObjectReader import ObjectReader
    from ..files.SerializedFile import SerializedFile
    from ..enums.ClassIDType import ClassIDType

T = TypeVar("T")


@define(slots=True, kw_only=True)
class PPtr(Generic[T]):
    m_FileID: int
    m_PathID: int
    assetsfile: Optional[SerializedFile] = None

    @property
    def file_id(self) -> int:
        # backwards compatibility
        return self.m_FileID

    @property
    def path_id(self) -> int:
        # backwards compatibility
        return self.m_PathID

    @property
    def type(self) -> ClassIDType:
        return self.deref().type

    def read(self):
        # backwards compatibility
        return self.deref_parse_as_object()

    def deref(self, assetsfile: Optional[SerializedFile] = None) -> ObjectReader[T]:
        assetsfile = assetsfile or self.assetsfile
        if assetsfile is None:
            raise ValueError("PPtr can't deref without an assetsfile!")

        if self.m_PathID == 0:
            raise ValueError("PPtr can't deref with m_PathID == 0!")

        if self.m_FileID == 0:
            pass
        else:
            # resolve file id to external name
            external_id = self.m_FileID - 1
            if external_id >= len(assetsfile.m_Externals):
                raise FileNotFoundError("Failed to resolve pointer - invalid m_FileID!")
            external = assetsfile.m_Externals[external_id]

            # resolve external name to assetsfile
            container = assetsfile.parent
            if container is None:
                # TODO - use default fs
                raise FileNotFoundError(
                    f"PPtr points to {external.path} but no container is set!"
                )

            for child in container.childs:
                if isinstance(child, SerializedFile) and child.name == external.path:
                    assetsfile = child
                    break
            else:
                raise FileNotFoundError(
                    f"Failed to resolve pointer - {external.path} not found!"
                )

        return cast("ObjectReader[T]", assetsfile.objects[self.m_PathID])

    def deref_parse_as_object(self, assetsfile: Optional[SerializedFile] = None) -> T:
        return self.deref(assetsfile).read()

    def deref_parse_as_dict(
        self, assetsfile: Optional[SerializedFile] = None
    ) -> dict[str, Any]:
        ret = self.deref(assetsfile).parse_as_dict()
        assert isinstance(ret, dict)
        return ret

    def __bool__(self):
        return self.m_PathID != 0
