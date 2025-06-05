import ntpath
from typing import TYPE_CHECKING

from ..streams import EndianBinaryReader

if TYPE_CHECKING:
    from ..files.SerializedFile import SerializedFile


def get_resource_data(res_path: str, assets_file: "SerializedFile", offset: int, size: int):
    basename = ntpath.basename(res_path)
    name, ext = ntpath.splitext(basename)
    possible_names = [
        basename,
        f"{name}.resource",
        f"{name}.assets.resS",
        f"{name}.resS",
    ]
    environment = assets_file.environment
    reader = None
    for possible_name in possible_names:
        reader = environment.get_cab(possible_name)
        if reader:
            break
    if not reader:
        assets_file.load_dependencies(possible_names)
        for possible_name in possible_names:
            reader = environment.get_cab(possible_name)
            if reader:
                break
        if not reader:
            raise FileNotFoundError(f"Resource file {basename} not found")
    return _get_resource_data(reader, offset, size)


def _get_resource_data(reader: EndianBinaryReader, offset: int, size: int):
    reader.Position = offset
    return reader.read_bytes(size)
