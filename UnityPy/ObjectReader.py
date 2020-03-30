from . import classes


class ObjectReader:
    def __init__(self, reader, assets_file, object_info):
        self.assets_file = assets_file
        self.path_id = object_info.path_id
        self.byte_start = object_info.byte_start
        self.byte_size = object_info.byte_size
        self.serialized_type = object_info.serialized_type
        self.platform = assets_file.target_platform
        self.version2 = assets_file.header.version
        self.type = object_info.class_id
        self.version = assets_file.version
        self.build_type = assets_file.build_type
        self.reader = reader

    @property
    def container(self):
        return (
            self.assets_file._container[self.path_id]
            if self.path_id in self.assets_file._container
            else None
        )

    def reset(self):
        self.reader.Position = self.byte_start

    def read(self):
        return getattr(classes, self.type.name, classes.Object)(self)

    def __getattr__(self, item: str):
        if hasattr(self.reader, item):
            return getattr(self.reader, item)

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.type.name)
