from ..enums import ClassIDType
from . import SerializedFile
from .. import classes


class ObjectReader:
    byte_start: int
    byte_size: int
    type_id: int
    class_id: int
    type: ClassIDType
    path_id: int
    # serialized_type: SerializedType
    _read_until: int
    
    # saves where the parser stopped
    # in case that not all data is read
    # and the obj.data is changed, the unknown data can be added again
    
    def __init__(self, assets_file, reader):
        self.assets_file = assets_file
        self.reader = reader
        self.data = b""
        self.version = assets_file.version
        self.version2 = assets_file.header.version
        self.platform = assets_file.target_platform
        self.build_type = assets_file.build_type
        
        header = assets_file.header
        types = assets_file.types
        
        if assets_file.big_id_enabled:
            self.path_id = reader.read_long()
        elif header.version < 14:
            self.path_id = reader.read_int()
        else:
            reader.align_stream()
            self.path_id = reader.read_long()
        
        if header.version >= 22:
            self.byte_start_offset = (self.reader.real_offset(), 8)
            self.byte_start = reader.read_long()
        else:
            self.byte_start_offset = (self.reader.real_offset(), 4)
            self.byte_start = reader.read_u_int()
        
        self.byte_start += header.data_offset
        self.byte_header_offset = header.data_offset
        self.byte_base_offset = self.reader.BaseOffset
        
        self.byte_size_offset = (self.reader.real_offset(), 4)
        self.byte_size = reader.read_u_int()
        
        self.type_id = reader.read_int()
        if header.version < 16:
            self.class_id = reader.read_u_short()
            if types:
                self.serialized_type = (
                    x for x in types if x.class_id == self.type_id).__next__()
            else:
                self.serialized_type = SerializedFile.SerializedType(reader, self.assets_file)
        else:
            typ = types[self.type_id]
            self.serialized_type = typ
            self.class_id = typ.class_id
        
        self.type = ClassIDType(self.class_id)
        
        if header.version < 11:
            self.is_destroyed = reader.read_u_short()
        
        if 11 <= header.version < 17:
            script_type_index = reader.read_short()
            if self.serialized_type:
                self.serialized_type.script_type_index = script_type_index
        
        if header.version == 15 or header.version == 16:
            self.stripped = reader.read_byte()
    
    def write(self, header, writer, data_writer):
        if self.assets_file.big_id_enabled:
            writer.write_long(self.path_id)
        elif header.version < 14:
            writer.write_int(self.path_id)
        else:
            writer.align_stream()
            writer.write_long(self.path_id)
        
        if self.data:
            data = self.data
            # in some cases the parser doesn't read all of the object data
            # games might still require the missing data
            # so following code appends the missing data back to edited objects
            end_pos = self.byte_start + self.byte_size
            if self._read_until != end_pos:
                self.reader.Position = self._read_until
                data += self.reader.read_bytes(end_pos - self._read_until)
        else:
            self.reset()
            data = self.reader.read(self.byte_size)
        
        if header.version >= 22:
            writer.write_long(data_writer.Position)
        else:
            writer.write_u_int(data_writer.Position)
        
        writer.write_u_int(len(data))
        data_writer.write(data)
        
        writer.write_int(self.type_id)
        
        if header.version < 16:
            writer.write_u_short(self.class_id)
        
        if header.version < 11:
            writer.write_u_short(self.is_destroyed)
        
        if 11 <= header.version < 17:
            writer.write_short(self.serialized_type.script_type_index)
        
        if header.version == 15 or header.version == 16:
            writer.write_byte(self.stripped)
    
    def set_raw_data(self, data):
        self.data = data
        self.assets_file.mark_changed()
    
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
        try:
            obj = getattr(classes, self.type.name, classes.Object)(self)
        except Exception as e:
            raise e
        # TODO: only specific exceptions here?
        except:
            # HACK: in case the parsing via the class fails this solution
            #       uses the type tree to set the variables and then changes the class
            obj = classes.Object(self)
            obj.__class__ = getattr(classes, self.type.name, classes.Object)
            for key, val in obj.__dict__.items():
                if " " in key:
                    obj.__dict__[key.replace(" ", "_")] = val
                    delattr(obj, key)
        self._read_until = self.reader.Position
        return obj
    
    def get(self, key, default = None):
        return getattr(self, key, default)

    def __getattr__(self, item: str):
        if hasattr(self.reader, item):
            return getattr(self.reader, item)
    
    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.type.name)
