import ntpath
from ..streams import EndianBinaryReader
from ..files import File


def get_resource_data(*args):
    """
    Input:
    Option 1:
        0 - path - file path
        1 - assets_file - SerializedFile
        2 - offset -
        3 - size -
    Option 2:
        0 - reader - EndianBinaryReader
        1 - offset -
        2 - size -

    -> -2 = offset, -1 = size
    """
    if len(args) == 4:
        res_path, assets_file, offset, size = args
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
    elif len(args) == 3:
        reader, offset, size = args
    else:
        raise TypeError(f"3 or 4 arguments required, but only {len(args)} given")

    reader.Position = offset
    return reader.read_bytes(size)
