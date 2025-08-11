from __future__ import annotations

import re
from enum import IntEnum
from typing import Optional, Tuple, Union

VersionPattern = re.compile(r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<build>\d+)(?P<type_str>.+?)?(?P<type_number>\d+)?$")


class UnityVersionType(IntEnum):
    a = 0  # Alpha
    b = 1  # Beta
    c = 2  # China
    f = 3  # Final
    p = 4  # Patch
    x = 5  # Experimental
    u = 255  # Unknown


class UnityVersion(int):
    # https://github.com/AssetRipper/VersionUtilities/blob/master/VersionUtilities/UnityVersion.cs
    _type_str: Optional[str]

    @property
    def major(self):
        return (self >> 48) & 0xFFFF

    @property
    def minor(self):
        return (self >> 32) & 0xFFFF

    @property
    def build(self):
        return (self >> 16) & 0xFFFF

    @property
    def type(self):
        return UnityVersionType((self >> 8) & 0xFF)

    @property
    def type_str(self):
        return getattr(self, "_type_str", self.type.name)

    @property
    def type_number(self):
        return self & 0xFF

    @classmethod
    def from_list(
        cls, major: int = 0, minor: int = 0, build: int = 0, type: int = UnityVersionType.f, type_number: int = 0
    ):
        return cls((major << 48) | (minor << 32) | (build << 16) | (type << 8) | type_number)

    @classmethod
    def from_str(cls, version: str):
        # formats:
        #   old: 5.0.0, <major>.<minor>.<build>
        #   new: 2018.1.1f2 <major>.<minor>.<build><type_str><type_number>
        match = VersionPattern.match(version)
        if not match:
            raise ValueError(f"Invalid version string: {version}")
        major = int(match.group("major"))
        minor = int(match.group("minor"))
        build = int(match.group("build"))
        type_str = match.group("type_str")
        type_number = int(match.group("type_number") or 0)

        if type_str is None:
            return cls.from_list(major, minor, build)

        type = getattr(UnityVersionType, type_str.lower(), UnityVersionType.u)
        obj = cls.from_list(major, minor, build, type, type_number)
        if type is UnityVersionType.u:
            obj._type_str = type_str
        return obj

    def __repr__(self) -> str:
        return f"UnityVersion {self.major}.{self.minor}{self.type_str}{self.type_number}"

    def __getitem__(self, idx: int) -> int:
        if idx == 0:
            return self.major
        elif idx == 1:
            return self.minor
        elif idx == 2:
            return self.build
        elif idx == 3:
            return self.type.value
        elif idx == 4:
            return self.type_number
        raise IndexError("Invalid UnityVersion index")

    def as_tuple(self) -> Tuple[int, int, int, int, int]:
        return (self.major, self.minor, self.build, self.type.value, self.type_number)

    def __eq__(self, other: Union[int, UnityVersion, Tuple[int, ...]]) -> bool:
        if isinstance(other, int):
            return super().__eq__(other)
        elif isinstance(other, tuple):
            return self.as_tuple() == other
        raise NotImplementedError("Unsupported comparison")

    def __ne__(self, other: Union[int, UnityVersion, Tuple[int, ...]]) -> bool:
        return not self.__eq__(other)

    def __lt__(self, other: Union[int, UnityVersion, Tuple[int, ...]]) -> bool:
        if isinstance(other, int):
            return super().__lt__(other)
        elif isinstance(other, tuple):
            return self.as_tuple() < other
        raise NotImplementedError("Unsupported comparison")

    def __le__(self, other: Union[int, UnityVersion, Tuple[int, ...]]) -> bool:
        return self.__lt__(other) or self.__eq__(other)

    def __gt__(self, other: Union[int, UnityVersion, Tuple[int, ...]]) -> bool:
        if isinstance(other, int):
            return super().__gt__(other)
        elif isinstance(other, tuple):
            return self.as_tuple() > other
        raise NotImplementedError("Unsupported comparison")

    def __ge__(self, other: Union[int, UnityVersion, Tuple[int, ...]]) -> bool:
        return self.__gt__(other) or self.__eq__(other)

    def __hash__(self) -> int:
        return super().__hash__()


__all__ = ["UnityVersion", "UnityVersionType"]
