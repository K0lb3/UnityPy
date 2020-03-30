from ..streams import EndianBinaryReader


class RefInt:
    v: int

    def __init__(self, value):
        self._value = value

    def __add__(self, other):
        return self._value + other

    def __sub__(self, other):
        self._value -= other
        return self._value

    def __int__(self):
        return self._value

    def __getattr__(self, item):
        return self._value

    def __getitem__(self, item):
        return self._value

    def __setattr__(self, key, value):
        self.__dict__["_value"] = value

    def __setitem__(self, key, value):
        self._value = value

    def __mod__(self, other):
        return self._value % other

    def __ge__(self, other):
        return self._value >= other

    def __gt__(self, other):
        return self._value > other

    def __le__(self, other):
        return self._value <= other

    def __lt__(self, other):
        return self._value < other

    def __eq__(self, other):
        return self._value == other


def get_members(members: list, level: int, index: int) -> list:
    member2 = [members[0]]
    for i in range(index + 1, len(members)):
        member = members[i]
        if member.level <= level:
            return member2
        member2.append(member)
    return member2


class TypeTreeHelper:
    def __init__(self, reader: EndianBinaryReader):
        self.reader = reader
        self.READ = {
            "SInt8": self.reader.read_byte,
            "UInt8": self.reader.read_u_byte,
            "short": self.reader.read_short,
            "SInt16": self.reader.read_short,
            "unsigned short": self.reader.read_u_short,
            "UInt16": self.reader.read_u_short,
            "int": self.reader.read_int,
            "SInt32": self.reader.read_int,
            "unsigned int": self.reader.read_u_int,
            "UInt32": self.reader.read_u_int,
            "Type*": self.reader.read_u_int,
            "long long": self.reader.read_long,
            "SInt64": self.reader.read_long,
            "unsigned long long": self.reader.read_u_long,
            "UInt64": self.reader.read_u_long,
            "float": self.reader.read_float,
            "double": self.reader.read_double,
            "bool": self.reader.read_boolean,
        }

        self.READ2 = {
            "string": self.read_string,
            "map": self.read_map,
            "TypelessData": self.read_typeless_data,
        }

    def read_u_type(self, members: list) -> dict:
        i = RefInt(0)
        obj = {}
        while i.v < len(members):
            member = members[i.v]
            obj[member.name] = self.read_value(members, i)
            i.v += 1
        return obj

    def read_string(self, i, align, *args):
        value = self.reader.read_aligned_string()
        i.v += 3
        return value, align

    def read_map(self, i, align, members, level):
        if (members[i + 1].meta_flag & 0x4000) != 0:
            align = True
        size = self.reader.read_int()
        map_ = get_members(members, level, i)[4:]
        i.v += len(map_) + 3
        first = get_members(map_, map_[0].level, 0)
        second = map_[len(first) :]
        value = {}
        for j in range(size):
            tmp1 = RefInt(0)
            tmp2 = RefInt(0)
            v1 = self.read_value(
                first, tmp1
            )  # python reads the value first and then the key, so it has to be this way
            if isinstance(v1, dict):
                value[first] = tmp1
                value["values"] = self.read_value(second, tmp2)
            else:
                value[v1] = self.read_value(second, tmp2)
        return value, align

    def read_typeless_data(self, i, align, *args):
        size = self.reader.read_int()
        value = self.reader.read_bytes(size)
        i.v += 2
        return value, align

    def read_value(self, members: list, i) -> object:
        if type(i) != RefInt:
            i = RefInt(i)
        member = members[i.v]
        level = member.level
        var_type_str = member.type
        align = (member.meta_flag & 0x4000) != 0

        value = self.READ.get(var_type_str)
        if value:
            value = value()
        else:
            value = self.READ2.get(var_type_str)
            if value:
                value, align = value(i, align, members, level)
            else:
                if i != len(members) and members[i.v + 1].type == "Array":
                    if (members[i.v + 1].meta_flag & 0x4000) != 0:
                        align = True
                    size = self.reader.read_int()
                    vector = get_members(members, level, i)[3:]
                    i.v += len(vector) + 2
                    value = [self.read_value(vector, 0) for j in range(size)]
                else:
                    eclass = get_members(members, level, i)
                    eclass.pop(0)
                    i.v += len(eclass)
                    j = RefInt(0)
                    value = {}
                    while j < len(eclass):
                        classmember = eclass[j.v]
                        name = classmember.name
                        value[name] = self.read_value(eclass, j)
                        j.v += 1
        if align:
            self.reader.align_stream()
        return value

    def read_type_string(self, sb: list, members: list):
        i = RefInt(0)
        while i < len(members):
            self.read_string_value(sb, members, i)
            i.v += 1
        return sb

    def read_string_value(self, sb: list, members, i: RefInt):
        if type(i) != RefInt:
            i = RefInt(i)
        member = members[i.v]
        level = member.level
        var_type_str = member.type
        var_name_str = member.name
        append = True
        align = (member.meta_flag & 0x4000) != 0
        value = self.READ.get(var_type_str)
        if value:
            value = value()

        elif var_type_str == "string":
            append = False
            string = self.reader.read_aligned_string()
            sb.append(
                '{0}{1} {2} = "{3}"\r\n'.format(
                    "\t" * level, var_type_str, var_name_str, string
                )
            )
            i.v += 3

        elif var_type_str == "vector":
            if (members[i + 1].meta_flag & 0x4000) != 0:
                align = True
            append = False
            sb.append("{0}{1} {2}\r\n".format("\t" * level, var_type_str, var_name_str))
            sb.append("{0}{1} {2}\r\n".format("\t" * (level + 1), "Array", "Array"))
            size = self.reader.read_int()
            sb.append(
                "{0}{1} {2} = {3}\r\n".format("\t" * (level + 1), "int", "size", size)
            )
            vector = get_members(members, level, i.v)[3:]
            i.v += len(vector) + 2
            for j in range(size):
                sb.append("{0}[{1}]\r\n".format("\t" * (level + 2), j))
                tmp = RefInt(0)
                self.read_string_value(sb, vector, tmp)

        elif var_type_str == "map":
            if (members[i + 1].meta_flag & 0x4000) != 0:
                align = True
            append = False
            sb.append("{0}{1} {2}\r\n".format("\t" * level, var_type_str, var_name_str))
            sb.append("{0}{1} {2}\r\n".format("\t" * (level + 1), "Array", "Array"))
            size = self.reader.read_int()
            sb.append(
                "{0}{1} {2} = {3}\r\n".format("\t" * (level + 1), "int", "size", size)
            )
            map_ = get_members(members, level, i.v)[4:]
            i.v += len(map_) + 3
            first = get_members(map_, map_[0].level, 0)
            second = map_[len(first) :]
            for j in range(size):
                sb.append("{0}[{1}]\r\n".format("\t" * (level + 2), j))
                sb.append("{0}{1} {2}\r\n".format("\t" * (level + 2), "pair", "data"))
                tmp1 = RefInt(0)
                tmp2 = RefInt(0)
                self.read_string_value(sb, first, tmp1)
                self.read_string_value(sb, second, tmp2)

        elif var_type_str == "TypelessData":
            append = False
            size = self.reader.read_int()
            value = self.reader.read_bytes(size)
            i.v += 2
            sb.append("{0}{1} {2}\r\n".format("\t" * level, var_type_str, var_name_str))
            sb.append("{0}{1} {2} = {3}\r\n".format("\t" * level, "int", "size", size))

        else:
            if i != len(members) and members[i + 1].type == "Array":
                if (members[i + 1].meta_flag & 0x4000) != 0:
                    align = True
                append = False
                sb.append(
                    "{0}{1} {2}\r\n".format("\t" * level, var_type_str, var_name_str)
                )
                sb.append("{0}{1} {2}\r\n".format("\t" * (level + 1), "Array", "Array"))
                size = self.reader.read_int()
                sb.append(
                    "{0}{1} {2} = {3}\r\n".format(
                        "\t" * (level + 1), "int", "size", size
                    )
                )
                vector = get_members(members, level, i.v)
                i.v += len(vector) - 1
                vector = vector[3:]  # vector.RemoveRange(0, 3)
                for j in range(size):
                    sb.append("{0}[{1}]\r\n".format("\t" * (level + 2), j))
                    tmp = RefInt(0)
                    self.read_string_value(sb, vector, tmp)
            else:
                append = False
                sb.append(
                    "{0}{1} {2}\r\n".format("\t" * level, var_type_str, var_name_str)
                )
                eclass = get_members(members, level, i.v)
                eclass.pop(0)  # .RemoveAt(0)
                i.v += len(eclass)
                j = RefInt(0)
                while j < len(eclass):
                    self.read_string_value(sb, eclass, j)
                    j.v += 1

        if append:
            sb.append(
                "{0}{1} {2} = {3}\r\n".format(
                    "\t" * level, var_type_str, var_name_str, value
                )
            )
        if align:
            self.reader.align_stream()

        return sb


"""
	def write_u_type(self, obj: dict, members: list) -> bytes:
		stream = io.BytesIO()
		write = EndianBinaryReader(stream)
		for i, member in enumerate(members):
			var_name_str = member.name
			write_value(obj[var_name_str], members, write, RefInt(i))
		pos = stream.tell()
		stream.seek(0)
		ret = stream.read()
		stream.seek(pos)
		return ret
	
	def write_value(value: dict, members: list, write: EndianBinaryReader, i):
		member = members[i.v]
		level = member.level
		var_type_str = member.type
		align = (member.meta_flag & 0x4000) != 0
		if var_type_str == "SInt8":
			write.write_s_byte(value)
		elif var_type_str == "UInt8":
			write.write_byte(value)
		elif var_type_str in ["short", "SInt16"]:
			write.write_short(value)
		elif var_type_str in ["UInt16", "unsigned short"]:
			write.write_u_short(value)
		elif var_type_str in ["int", "SInt32"]:
			write.write_int(value)
		elif var_type_str in ["UInt32", "unsigned int", "Type*"]:
			write.write_u_int(value)
		elif var_type_str in ["long long", "SInt64"]:
			write.write_long(value)
		elif var_type_str in ["UInt64", "unsigned long long"]:
			write.write_u_long(value)
		elif var_type_str == "float":
			write.write_float(value)
		elif var_type_str == "double":
			write.write_double(value)
		elif var_type_str == "bool":
			write.write_bool(value)
		elif var_type_str == "string":
			write.write_aligned_string(value)
			i.v += 3
		elif var_type_str == "map":
			if (members[i + 1].meta_flag & 0x4000) != 0:
				align = True
			dic = list(value.items())
			size = len(dic)
			write.Write(size)
			map_ = get_members(members, level, i)
			i.v += len(map_) - 1
			map_ = map_[4:]  # map.RemoveRange(0, 4)
			first = get_members(map_, map_[0].level, 0)
			map_ = map_[len(first):]  # .RemoveRange(0, len(first))
			second = map_
			for j in range(size):
				tmp1 = RefInt(0)
				tmp2 = RefInt(0)
				write_value(dic[j][0], first, write, tmp1)  # key
				write_value(dic[j][1], second, write, tmp2)  # value
		elif var_type_str == "TypelessData":
			byts = bytes(value)
			size = len(byts)
			write.Write(size)
			write.Write(bytes)
			i.v += 2
		else:
			if i != len(members) and members[i + 1].type == "Array":  # Array
				if (members[i.v + 1].meta_flag & 0x4000) != 0:
					align = True
				list_ = value
				size = len(list_)
				write.Write(size)
				vector = get_members(members, level, i)
				i.v += len(vector) - 1
				vector = vector[3:]  # vector.RemoveRange(0, 3)
				for j in range(size):
					tmp = RefInt(0)
					write_value(list_[j], vector, write, tmp)
			else:  # Class
				eclass = get_members(members, level, i)
				eclass.pop(0)  # .RemoveAt(0)
				i.v += len(eclass)
				obj = value
				j = RefInt(0)
				while j < len(eclass):
					classmember = eclass[j.v]
					name = classmember.name
					write_value(obj[name], eclass, write, j)
		if align:
			write.align_stream(4)


"""
