import io
import os
from collections import Counter
from collections.abc import Callable
from zipfile import ZipFile

from . import files
from .enums import FileType
from .helpers import ImportHelper

"""
 Number of dirs to ignore:
 e.g. IGNOR_DIR_COUNT = 2 will reduce
 'assets/assetbundles/images/story_picture/small/15.png'
 to
 'images/story_picture/small/15.png'
"""
IGNORE_DIR_COUNT = 0
DEFAULT_TYPES = ['MonoBehaviour', 'Texture2D', 'TextAsset']

def default_progress(skip_progress):
    return skip_progress

class Environment:
    files: dict
    resources: dict
    container: dict
    assets: dict
    path: str

    def __init__(self, *args):
        self.files = {}
        self.container = {}
        self.assets = {}
        self.resources = {}
        self.path = "."
        self.out_path = os.path.join(os.getcwd(), "output")
        self.ignore_dir_lvls = IGNORE_DIR_COUNT
        self.progress_function = default_progress

        if args:
            for arg in args:
                if isinstance(arg, str):
                    if os.path.isfile(arg):
                        if os.path.splitext(arg)[-1] in [".apk", ".zip"]:
                            self.load_zip_file(arg)
                        else:
                            self.path = os.path.dirname(arg)
                            self.load_file(arg)
                    elif os.path.isdir(arg):
                        self.path = arg
                        self.load_folder(arg)
                else:
                    self.path = None
                    self.load_file(data=arg)

        if len(self.files) == 1:
            self.file = list(self.files.values())[0]

    def load_files(self, files: list):
        """Loads all files (list) into the AssetsManager and merges .split files for common usage."""
        path = os.path.dirname(files[0])
        ImportHelper.merge_split_assets(path)
        to_read_file = ImportHelper.processing_split_files(files)
        self.load(to_read_file)

    def load_folder(self, path: str):
        """Loads all files in the given path and its subdirs into the AssetsManager."""
        ImportHelper.merge_split_assets(path, True)
        files = ImportHelper.list_all_files(path)
        to_read_file = ImportHelper.processing_split_files(files)
        self.load(to_read_file)

    def load(self, files: list):
        """Loads all files into the AssetsManager."""
        # for f in files:
        #    self.import_files[os.path.basename(f)] = f

        # self.Progress.reset()
        # use a for loop because list size can change
        # for i, f in enumerate(self.import_files.values()):
        for f in files:
            self.load_file(f)
            # self.Progress.report(i + 1, len(self.import_files))

    def save(self, pack="none"):
        """ Saves all changed assets.
            Mark assets as changed using `.mark_changed()`.
            pack = "none" (default) or "lz4"
        """
        for f in self.files:
            if self.files[f].is_changed:
                with open(os.path.join(self.out_path, os.path.basename(f)), 'wb') as out:
                    out.write(self.files[f].save(packer=pack))

    def process(self, obj_modify: Callable, types: list=DEFAULT_TYPES, **kwargs):
        """Accept modification function `obj_modify => obj_modify(obj, asset, local_path) to modify `types` """
        for asset in self.progress_function(self.assets):
            current_asset = self.assets[asset]

            if not current_asset.container: continue # TODO: fix it

            # check which mode we will have to use
            num_containers = sum(1 for obj in current_asset.container.values() if obj.type in types)
            num_objects = sum(1 for obj in current_asset.objects.values() if obj.type in types)
            if num_containers == 0 and num_objects == 0: continue

            # check if container contains all important assets, if yes, just ignore the container
            local_path = ''
            if num_objects <= num_containers * 2:
                for asset_path, obj in current_asset.container.items():
                    try:
                        local_path = os.path.join(*asset_path.split('/')[self.ignore_dir_lvls:])
                    except:
                        pass
                    if obj.type in types:
                        obj_modify(obj, asset, local_path=local_path, **kwargs)
            else: # otherwise use the container to generate a path for the normal objects
                extracted = []
                # find the most common path
                occurence_count = Counter(os.path.splitext(asset_path)[0] for asset_path in current_asset.container.keys())
                try:
                    local_path = os.path.join(*occurence_count.most_common(1)[0][0].split('/')[self.ignore_dir_lvls:])
                except:
                    pass
                for obj in current_asset.objects.values():
                    if obj.path_id not in extracted and obj.type in types:
                        extracted.extend(obj_modify(obj, asset, local_path=local_path, **kwargs))

    def load_file(self, full_name: str = "", data = None):
        typ, reader = ImportHelper.check_file_type(data if data else full_name)
        if not full_name:
            full_name = str(data[:256])
        if typ == FileType.AssetsFile:
            self.files[full_name] = files.SerializedFile(reader, self)
            self.assets[full_name] = self.files[full_name]
        elif typ == FileType.BundleFile:
            self.files[full_name] = files.BundleFile(reader, self)
        elif typ == FileType.WebFile:
            self.files[full_name] = files.WebFile(reader, self)
        elif typ == FileType.ZIP:
            self.load_zip_file(reader.stream)
        elif typ == FileType.ResourceFile:
            self.resources[os.path.basename(full_name)] = reader

    def load_zip_file(self, value):
        buffer = None
        if isinstance(value, str) and os.path.exists(value):
            buffer = open(value, "rb")
        elif isinstance(value, (bytes, bytearray)):
            buffer = ZipFile(io.BytesIO(value))
        elif isinstance(value, (io.BufferedReader, io.BufferedIOBase)):
            buffer = value

        z = ZipFile(buffer)

        for path in z.namelist():
            data = z.open(path).read()
            if data:
                self.load_file(path, data)

    @property
    def objects(self):
        def search(item):
            ret = []
            if not isinstance(item, Environment) and getattr(item, "objects", None):
                # serialized file
                return [val for val in item.objects.values()]

            elif getattr(item, "files", None):  # WebBundle and BundleFile
                # bundle
                for item in item.files.values():
                    ret.extend(search(item))
                return ret

            return ret

        return search(self)
