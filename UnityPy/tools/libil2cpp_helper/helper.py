from enum import Enum
from io import BytesIO
from struct import pack, unpack
from typing import List, Iterator, Tuple, Union, BinaryIO, get_origin, get_args

# save original int class
_int = int


class CustomIntWrapper(int):
    __size: int
    __format: str

    @classmethod
    def read_from(cls, f: BytesIO):
        return cls(
            unpack("<" + getattr(cls, "__format"), f.read(getattr(cls, "__size")))[0]
        )


def CustomIntWrapperFactory(name: str, __size: int, __format: str) -> CustomIntWrapper:
    return type(name, (CustomIntWrapper,), {"__size": __size, "__format": __format})


byte = CustomIntWrapperFactory("byte", 1, "B")
short = CustomIntWrapperFactory("short", 2, "h")
ushort = CustomIntWrapperFactory("ushort", 2, "H")
int = CustomIntWrapperFactory("int", 4, "i")
uint = CustomIntWrapperFactory("uint", 4, "I")
long = CustomIntWrapperFactory("long", 8, "q")
ulong = CustomIntWrapperFactory("ulong", 8, "Q")


class Version:
    Min: float
    Max: float

    def __new__(cls, Min: float = 0, Max: float = 99):
        spec = []
        if Min:
            spec.append(f"Min={Min}")
        if Max != 99:
            spec.append(f"Max={Max}")
        newclass = type(
            f"Version ({', '.join(spec)})", (Version,), {"Min": Min, "Max": Max}
        )
        return newclass

    @classmethod
    def check_compatiblity(cls, version):
        return cls.Min <= version <= cls.Max


class MetaDataClass:
    version: float
    size: int
    parseString: str

    def __init__(self, reader: BinaryIO = None) -> None:
        if not (self.version):
            raise NotImplementedError(
                "Using an unversioned MetaDataClass isn't possible."
            )
        if reader:
            self.read_from(reader)

    def read_from(self, reader: BytesIO):
        self.__dict__.update(
            zip(
                self.__annotations__.keys(),
                unpack(self.parseString, reader.read(self.size)),
            )
        )

    def write_to(self, writer: BytesIO):
        writer.write(
            pack(
                "<" + self.parseString,
                (self.get(key) for key in self.__annotations__.keys()),
            )
        )

    @classmethod
    def generate_versioned_subclass(cls, version: float):
        # fetch fields & calculate size
        compatible_fields = {}
        size = 0
        parseString = []
        for key, clz in cls.__annotations__.items():
            if get_origin(clz) == Union:
                clz, *version_checks = get_args(clz)
                if not any(
                    version_check.check_compatiblity(version)
                    for version_check in version_checks
                ):
                    continue
            compatible_fields[key] = clz
            size += getattr(clz, "__size")
            parseString.append(getattr(clz, "__format"))

        newclass = type(
            f"{cls.__name__} - V{version:.1f}",
            (MetaDataClass,),
            {
                "__annotations__": compatible_fields,
                "size": size,
                "version": version,
                "parseString": "".join(parseString),
            },
        )
        return newclass
