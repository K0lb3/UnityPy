import os, glob
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
        reader = search_resource(res_path = args[0], assets_file = args[1])
    elif len(args) == 3:
        reader = args[0]
    else:
        raise TypeError(f"3 or 4 arguments required, but only {len(args)} given")

    reader.Position = args[-2]
    return reader.read_bytes(args[-1])

def search_resource(res_path, assets_file):
    # try to find the resource in the Unity packages
    base_name = os.path.basename(res_path)
    base_name2 = base_name.replace('.assets.resS', '.resource')

    for p in [res_path, base_name, base_name2]:
        reader = assets_file.parent.files.get(p)
        if reader:
            if isinstance(reader, File.File):
                # in case the import helper accidently detected a resource file as something else
                reader = reader.reader
            return reader

    # try to find it in the dir environment
    c = assets_file
    path = getattr(assets_file,"path",None)
    while not path:
        c = c.parent
        if c == None:
            raise FileNotFoundError(
                f"Can't find the resource file {res_path}"
            )            
        path = getattr(c,"path",None)
    current_directory = path
    resource_file_path = os.path.join(current_directory, *res_path.split("/"))
    if not os.path.isfile(resource_file_path):
        resource_file_path = search_resource_file(current_directory, base_name)
    if not os.path.isfile(resource_file_path):
        resource_file_path = search_resource_file(current_directory, base_name.replace('.assets.resS', '.resource'))

    if os.path.isfile(resource_file_path):
        return EndianBinaryReader(open(resource_file_path, "rb"))
    else:
        raise FileNotFoundError(
            f"Can't find the resource file {res_path}"
        )

def search_resource_file(path, name):
    print("real file", path,name)
    files = glob.glob(os.path.join(path, "**", name), recursive = True)
    return files[0] if len(files) else ""