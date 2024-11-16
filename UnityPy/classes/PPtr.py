from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, Optional, TypeVar, cast

from attr import define

if TYPE_CHECKING:
    from ..enums.ClassIDType import ClassIDType
    from ..files.ObjectReader import ObjectReader
    from ..files.SerializedFile import SerializedFile

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

    # backwards compatibility - to be removed in UnityPy 2
    def read(self):
        return self.deref_parse_as_object()

    # backwards compatibility - to be removed in UnityPy 2
    def read_typetree(self):
        return self.deref_parse_as_dict()

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
            if external_id >= len(assetsfile.externals):
                raise FileNotFoundError("Failed to resolve pointer - invalid m_FileID!")
            external = assetsfile.externals[external_id]

            # resolve external name to assetsfile
            container = assetsfile.parent
            if container is None:
                # TODO - use default fs
                raise FileNotFoundError(
                    f"PPtr points to {external.path} but no container is set!"
                )

            external_clean_path = external.path
            if external_clean_path.startswith("archive:/"):
                external_clean_path = external_clean_path[9:]
            if external_clean_path.startswith("assets/"):
                external_clean_path = external_clean_path[7:]
            external_clean_path = external_clean_path.rsplit("/")[-1].lower()

            for key, file in container.files.items():
                if key.lower() == external_clean_path:
                    assetsfile = file
                    break
            else:
                env = assetsfile.environment
                cab = env.find_file(external_clean_path)
                if cab:
                    assetsfile = cab
                else:
                    raise FileNotFoundError(
                        f"Failed to resolve pointer - {external.path} not found!"
                    )

        return cast("ObjectReader[T]", assetsfile.objects[self.m_PathID])

    def deref_parse_as_object(self, assetsfile: Optional[SerializedFile] = None) -> T:
        return self.deref(assetsfile).parse_as_object()

    def deref_parse_as_dict(
        self, assetsfile: Optional[SerializedFile] = None
    ) -> dict[str, Any]:
        return self.deref(assetsfile).parse_as_dict()

    def __bool__(self):
        return self.m_PathID != 0

    def __hash__(self) -> int:
        return hash((self.m_FileID, self.m_PathID))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PPtr):
            return False
        return self.m_FileID == other.m_FileID and self.m_PathID == other.m_PathID
