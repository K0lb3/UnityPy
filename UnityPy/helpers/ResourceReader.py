import os

from .ImportHelper import find_all_files


def get_resource_data(*args):
    """
    Input:
    Option 1:
        path - file path
        assets_file - SerializedFile
        offset -
        size -
    Option 2:
        reader - EndianBinaryReader
        offset -
        size -
    """
    if len(args) == 4:
        need_search = True
        path = args[0]
        assets_file = args[1]
    elif len(args) == 3:
        need_search = False
        reader = args[0]
    offset = args[-2]
    size = args[-1]

    if need_search:
        resource_file_name = path

        reader = assets_file.environment.resources.get(resource_file_name)
        if not reader:
            reader = assets_file.environment.resources.get(
                os.path.basename(resource_file_name)
            )
        if not reader:
            reader = assets_file.environment.resources.get(
                os.path.basename(resource_file_name.replace('.assets.resS', '.resource'))
            )

        if reader:
            reader.Position = offset
            return reader.read_bytes(size)

        if not assets_file.environment.path:
            return
        current_directory = os.path.dirname(assets_file.environment.path)
        resource_file_path = os.path.join(current_directory, resource_file_name)
        if not os.path.isfile(resource_file_path):
            find_files = find_all_files(current_directory, resource_file_name)
            if find_files:
                resource_file_path = find_files[0]

        if os.path.isfile(resource_file_path):
            with open(resource_file_path, "rb") as f:
                f.seek(offset)
                return f.read(size)
        else:
            raise FileNotFoundError(
                f"Can't find the resource file {resource_file_name}"
            )

    else:
        reader.Position = offset
        return reader.read_bytes(size)
