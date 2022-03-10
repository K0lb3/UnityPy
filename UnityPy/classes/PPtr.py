from ..files import ObjectReader
from ..streams import EndianBinaryWriter
from ..helpers import ImportHelper
from .. import files
from ..enums import FileType, ClassIDType
import os
from .. import environment


def save_ptr(obj, writer: EndianBinaryWriter):
    if isinstance(obj, PPtr):
        writer.write_int(obj.file_id)
    else:
        writer.write_int(0)  # it's usually 0......
    if obj._version < 14:
        writer.write_int(obj.path_id)
    else:
        writer.write_long(obj.path_id)


cached_managers = dict()


class PPtr:
    def __init__(self, reader: ObjectReader):
        self._version = reader.version2
        self.index = -2
        self.file_id = reader.read_int()
        self.path_id = reader.read_int() if self._version < 14 else reader.read_long()
        self.assets_file = reader.assets_file
        self._obj = None

    def save(self, writer: EndianBinaryWriter):
        save_ptr(self, writer)

    def get_obj(self):
        if self._obj != None:
            return self._obj
        manager = None
        if self.file_id == 0:
            manager = self.assets_file

        elif self.file_id > 0 and self.file_id - 1 < len(self.assets_file.externals):
            if self.index == -2:
                environment = self.assets_file.environment
                external_name = self.assets_file.externals[self.file_id - 1].name
                # try to find it in the already registered cabs
                manager = environment.get_cab(external_name)

                if not manager:
                    # guess we have to try to find it as file then
                    path = environment.path
                    if path:
                        basename = os.path.basename(external_name)
                        possible_names = [basename, basename.lower(), basename.upper()]
                        for root, dirs, files in os.walk(path):
                            for name in files:
                                if name in possible_names:
                                    manager = environment.load_file(
                                        os.path.join(root, name)
                                    )
                                    break
                            else:
                                # else is reached if the previous loop didn't break
                                continue
                            break
                        print(external_name, "not found")
                # else:
                #     if external_name not in cached_managers:
                #         typ, reader = ImportHelper.check_file_type(external_name)
                #         if typ == FileType.AssetsFile:
                #             cached_managers[external_name] = files.SerializedFile(reader)
                #     if external_name in cached_managers:
                #         manager = cached_managers[external_name]

        if manager and self.path_id in manager.objects:
            self._obj = manager.objects[self.path_id]
        else:
            self._obj = None

        return self._obj

    @property
    def type(self):
        obj = self.get_obj()
        if obj is None:
            return ClassIDType.UnknownType
        return obj.type

    def __getattr__(self, key):
        obj = self.get_obj()
        return getattr(obj, key)

    def __repr__(self):
        return "<%s %s>" % (
            self.__class__.__name__,
            self._obj.__class__.__repr__(self.get_obj())
            if self.get_obj()
            else "Not Found",
        )

    def __bool__(self):
        return True if self.get_obj() else False
