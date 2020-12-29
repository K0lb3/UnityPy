from ..streams import EndianBinaryReader, EndianBinaryWriter
from ..helpers import ImportHelper
from .. import files
from ..enums import FileType

def save_ptr(obj, writer: EndianBinaryWriter, version):
    if isinstance(obj, PPtr):
        writer.write_int(obj.file_id)
    else:
        writer.write_int(0)  # it's usually 0......
    if version < 14:
        writer.write_int(obj.path_id)
    else:
        writer.write_long(obj.path_id)

cached_managers = dict()

class PPtr:
    def __init__(self, reader: EndianBinaryReader):
        self._version = reader.version2
        self.index = -2
        self.file_id = reader.read_int()
        self.path_id = reader.read_int() if self._version < 14 else reader.read_long()
        self.assets_file = reader.assets_file
        self._obj = None

    def save(self, writer: EndianBinaryWriter):
        save_ptr(self, writer, self._version)

    def get_obj(self):
        if self._obj != None:
            return self._obj
        manager = None
        if self.file_id == 0:
            manager = self.assets_file

        elif self.file_id > 0 and self.file_id - 1 < len(self.assets_file.externals):
            if self.index == -2:
                external_name = self.assets_file.externals[self.file_id - 1].name
                parent = self.assets_file.parent
                if parent is not None:
                    if external_name not in parent.files:
                        external_name = external_name.upper()
                    if external_name in parent.files:
                        manager = parent.files[external_name]
                else:
                    if external_name not in cached_managers:
                        typ, reader = ImportHelper.check_file_type(external_name)
                        if typ == FileType.AssetsFile:
                            cached_managers[external_name] = files.SerializedFile(reader)
                    if external_name in cached_managers:
                        manager = cached_managers[external_name]


        if manager and self.path_id in manager.objects:
            self._obj = manager.objects[self.path_id]
        else:
            self._obj = None

        return self._obj

    def __getattr__(self, key):
        obj = self.get_obj()
        if obj is None:
            raise AttributeError(key)
        return getattr(obj, key)

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self._obj.__class__.__repr__(self.get_obj()) if self.get_obj() else "Not Found")

    def __bool__(self):
        return True if self.get_obj() else False
