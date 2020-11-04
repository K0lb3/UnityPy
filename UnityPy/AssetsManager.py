import io
import logging
import os
from zipfile import ZipFile

from .EndianBinaryReader import EndianBinaryReader
from .Progress import Progress
from .files import BundleFile, SerializedFile, WebFile
from .helpers import ImportHelper

FileType = ImportHelper.FileType

# create logger
logger = logging.getLogger("UnityPy")
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)


class AssetsManager:
    assets: dict
    resource_file_readers: dict
    import_files: dict
    Progress: Progress

    def __init__(self, *args):
        self.assets = {}
        self.resource_file_readers = {}
        self.import_files = {}
        self.path = "."
        self.Progress = Progress()

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
                    self.load_file(arg)

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
        for f in files:
            self.import_files[os.path.basename(f)] = f

        self.Progress.reset()
        # use a for loop because list size can change
        for i, f in enumerate(self.import_files.values()):
            self.load_file(f)
            self.Progress.report(i + 1, len(self.import_files))

    def load_file(self, full_name: str = "", data=None):
        typ, reader = ImportHelper.check_file_type(data if data else full_name)
        if not full_name:
            full_name = str(data)[:256]
        if typ == FileType.AssetsFile:
            self.load_assets_file(full_name, reader)
        elif typ == FileType.BundleFile:
            self.load_bundle_file(full_name, reader)
        elif typ == FileType.WebFile:
            self.load_web_file(full_name, reader)
        elif typ == FileType.ZIP:
            self.load_zip_file(reader.stream)

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
            self.load_file(path, z.open(path).read())

    def load_assets_file(self, full_name: str, reader: EndianBinaryReader):
        file_name = os.path.basename(full_name)
        if file_name not in self.assets:
            logging.info(f"Loading {full_name}")
            try:
                assets_file = SerializedFile(self, reader)
                self.assets[file_name] = assets_file

                for sharedFile in assets_file.externals:
                    shared_file_path = os.path.join(
                        os.path.dirname(full_name), sharedFile.name
                    )
                    shared_file_name = sharedFile.name

                    if shared_file_name not in self.import_files:
                        if not os.path.exists(shared_file_path):
                            find_files = [
                                f
                                for f in ImportHelper.list_all_files(
                                    os.path.dirname(full_name)
                                )
                                if shared_file_name in f
                            ]
                            if find_files:
                                shared_file_path = find_files[0]

                        if os.path.exists(shared_file_path):
                            self.import_files[shared_file_name] = shared_file_path

                return assets_file

            except Exception as e:
                reader.dispose()
                logging.error(f"Unable to load assets file {file_name}", e)
        else:
            reader.dispose()

    def load_assets_from_memory(
        self,
        full_name: str,
        reader: EndianBinaryReader,
        original_path: str,
        unity_version=None,
    ):
        file_name = os.path.basename(full_name)
        if file_name.endswith((".resS", ".resource", ".config", ".xml", ".dat")):
            self.resource_file_readers[file_name] = reader
            return False
        elif file_name not in self.assets:
            try:
                assets_file = SerializedFile(self, full_name, reader)
                assets_file.original_path = original_path
                if assets_file.header.version < 7:
                    assets_file.set_version(unity_version)
                self.assets[file_name] = assets_file
            except Exception as e:
                logging.error(
                    f"Unable to load assets file {file_name} from {original_path}", e
                )
                self.resource_file_readers[file_name] = reader
                return False
        return True

    def load_bundle_file(
        self, full_name: str, reader: EndianBinaryReader, parent_path=None
    ):
        file_name = os.path.basename(full_name)
        logging.info(f"Loading {full_name}")
        bundle_file = None
        try:
            bundle_file = BundleFile(reader, full_name)
            for f in bundle_file.files:
                dummy_path = os.path.join(os.path.dirname(full_name), f.name)
                self.load_assets_from_memory(
                    dummy_path,
                    EndianBinaryReader(f.stream),
                    full_name if parent_path else bundle_file.version_engine,
                )
        except Exception as e:
            string = f"Unable to load bundle file {file_name}"
            if parent_path:
                string += f" from {os.path.basename(parent_path)}"
            string += "\n" + str(e)
            logging.error(string, e)
        finally:
            reader.dispose()
        return bundle_file

    def load_web_file(self, full_name: str, reader: EndianBinaryReader):
        file_name = os.path.basename(full_name)
        logging.info(f"Loading {full_name}")
        dispose = True
        web_file = None
        try:
            web_file = WebFile(reader)
            for f in web_file.files:
                dummy_path = os.path.join(os.path.dirname(full_name), f.name)
                typ, reader = ImportHelper.check_file_type(f.stream)
                if typ == FileType.AssetsFile:
                    dispose = self.load_assets_from_memory(
                        dummy_path, reader, full_name
                    )
                elif typ == FileType.BundleFile:
                    self.load_bundle_file(dummy_path, reader, full_name)
                elif typ == FileType.WebFile:
                    self.load_web_file(dummy_path, reader)
        except Exception as e:
            logging.error(f"Unable to load web file {file_name}", e)
        finally:
            if dispose:
                reader.dispose()
        return web_file

    def clear(self):
        for assetsFile in self.assets:
            assetsFile.Objects = []
            assetsFile.reader.Close()
        self.assets = {}

        for resourceFileReader in self.resource_file_readers:
            resourceFileReader.Value.Close()

        self.resource_file_readers = {}
