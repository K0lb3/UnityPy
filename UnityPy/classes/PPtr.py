from ..streams import EndianBinaryReader, EndianBinaryWriter


def save_ptr(obj, writer: EndianBinaryWriter, version):
    if isinstance(obj, PPtr):
        writer.write_int(obj.file_id)
    else:
        writer.write_int(0)  # it's usually 0......
    if version < 14:
        writer.write_int(obj.path_id)
    else:
        writer.write_long(obj.path_id)


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

                files = self.assets_file.parent.files
                if external_name not in files:
                    external_name = external_name.upper()
                manager = self.assets_file.parent.files[external_name]

                """
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
                """

        if manager and self.path_id in manager.objects:
            self._obj = manager.objects[self.path_id]
        else:
            self._obj = False

        return self._obj

    def __getattr__(self, key):
        return getattr(self.get_obj(), key)

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self._obj.__class__.__repr__(self.get_obj()) if self.get_obj() else "Not Found")

    def __bool__(self):
        return True if self.get_obj() else False
