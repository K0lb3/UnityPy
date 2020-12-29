import os, glob

def search_resource(path, name):
    files = glob.glob(os.path.join(path, "**", name), recursive = True)
    return files[0] if len(files) else ""

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
        base_name = os.path.basename(resource_file_name)
        if not reader:
            reader = assets_file.environment.resources.get(base_name)
        if not reader:
            reader = assets_file.environment.resources.get(
                base_name.replace('.assets.resS', '.resource')
            )

        if reader:
            reader.Position = offset
            return reader.read_bytes(size)

        current_directory = ''
        if not assets_file.environment.path:
            current_directory = os.getcwd()
        else:
            current_directory = os.path.dirname(assets_file.environment.path)
        resource_file_path = os.path.join(current_directory, resource_file_name)
        if not os.path.isfile(resource_file_path):
            resource_file_path = search_resource(current_directory, base_name)
        if not os.path.isfile(resource_file_path):
            resource_file_path = search_resource(current_directory, base_name.replace('.assets.resS', '.resource'))

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
