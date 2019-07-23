from EndianBinaryReader import EndianBinaryReader
import io


class RefInt():
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
		self.__dict__['_value'] = value
	
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


def GetMembers(members: list, level: int, index: int) -> list:
	if type(index) == RefInt:
		index = index.v
	member2 = [members[0]]
	for i in range(index + 1, len(members)):
		member = members[i]
		if member.m_Level <= level:
			return member2
		member2.append(member)
	return member2


def WriteUType(obj: dict, members: list) -> bytes:
	stream = io.BytesIO()
	write = EndianBinaryReader(stream)
	for i, member in enumerate(members):
		varNameStr = member.m_Name
		WriteValue(obj[varNameStr], members, write, i)
	pos = stream.tell()
	stream.seek(0)
	ret = stream.read()
	stream.seek(pos)
	return ret


def ReadTypeString(sb: list, members: list, reader: EndianBinaryReader):
	i = RefInt(0)
	while i < len(members):
		ReadStringValue(sb, members, reader, i)
		i.v += 1
	return sb


def ReadStringValue(sb: list, members, reader: EndianBinaryReader, i: RefInt):
	if type(i) != RefInt:
		i = RefInt(i)
	member = members[i.v]
	level = member.m_Level
	varTypeStr = member.m_Type
	varNameStr = member.m_Name
	value = None
	append = True
	align = (member.m_MetaFlag & 0x4000) != 0
	if varTypeStr == "SInt8":
		value = reader.ReadSByte()
	elif varTypeStr == "UInt8":
		value = reader.ReadByte()
	elif varTypeStr in ["short", "SInt16"]:
		value = reader.ReadInt16()
	elif varTypeStr in ["UInt16", "unsigned short"]:
		value = reader.ReadUInt16()
	elif varTypeStr in ["int", "SInt32"]:
		value = reader.ReadInt32()
	elif varTypeStr in ["UInt32", "unsigned int", "Type*"]:
		value = reader.ReadUInt32()
	elif varTypeStr in ["long long", "SInt64"]:
		value = reader.ReadInt64()
	elif varTypeStr in ["UInt64", "unsigned long long"]:
		value = reader.ReadUInt64()
	elif varTypeStr == "float":
		value = reader.ReadSingle()
	elif varTypeStr == "double":
		value = reader.ReadDouble()
	elif varTypeStr == "bool":
		value = reader.ReadBoolean()
	elif varTypeStr == "string":
		append = False
		string = reader.ReadAlignedString()
		sb.append("{0}{1} {2} = \"{3}\"\r\n".format('\t' * (level), varTypeStr, varNameStr, string))
		i.v += 3
	elif varTypeStr == "vector":
		if ((members[i + 1].m_MetaFlag & 0x4000) != 0):
			align = True
		append = False
		sb.append("{0}{1} {2}\r\n".format('\t' * (level), varTypeStr, varNameStr))
		sb.append("{0}{1} {2}\r\n".format('\t' * (level + 1), "Array", "Array"))
		size = reader.ReadInt32()
		sb.append("{0}{1} {2} = {3}\r\n".format('\t' * (level + 1), "int", "size", size))
		vector = GetMembers(members, level, i)
		i.v += len(vector) - 1
		vector = vector[3:]  # vector.RemoveRange(0, 3)
		for j in range(size):
			sb.append("{0}[{1}]\r\n".format('\t' * (level + 2), j))
			tmp = RefInt(0)
			ReadStringValue(sb, vector, reader, tmp)
	
	elif varTypeStr == "map":
		if ((members[i + 1].m_MetaFlag & 0x4000) != 0):
			align = True
		append = False
		sb.append("{0}{1} {2}\r\n".format('\t' * (level), varTypeStr, varNameStr))
		sb.append("{0}{1} {2}\r\n".format('\t' * (level + 1), "Array", "Array"))
		size = reader.ReadInt32()
		sb.append("{0}{1} {2} = {3}\r\n".format('\t' * (level + 1), "int", "size", size))
		map = GetMembers(members, level, i)
		i.v += len(map) - 1
		map = map[4:]  # map.RemoveRange(0, 4)
		first = GetMembers(map, map[0].m_Level, 0)
		map = map[len(first):]  # .RemoveRange(0, len(first))
		second = map
		for j in range(size):
			sb.append("{0}[{1}]\r\n".format('\t' * (level + 2), j))
			sb.append("{0}{1} {2}\r\n".format('\t' * (level + 2), "pair", "data"))
			tmp1 = RefInt(0)
			tmp2 = RefInt(0)
			ReadStringValue(sb, first, reader, tmp1)
			ReadStringValue(sb, second, reader, tmp2)
	
	elif varTypeStr == "TypelessData":
		append = False
		size = reader.ReadInt32()
		reader.ReadBytes(size)
		i.v += 2
		sb.append("{0}{1} {2}\r\n".format('\t' * level, varTypeStr, varNameStr))
		sb.append("{0}{1} {2} = {3}\r\n".format('\t' * level, "int", "size", size))
	else:
		if (i != len(members) and members[i + 1].m_Type == "Array"):
			if ((members[i + 1].m_MetaFlag & 0x4000) != 0):
				align = True
			append = False
			sb.append("{0}{1} {2}\r\n".format('\t' * (level), varTypeStr, varNameStr))
			sb.append("{0}{1} {2}\r\n".format('\t' * (level + 1), "Array", "Array"))
			size = reader.ReadInt32()
			sb.append("{0}{1} {2} = {3}\r\n".format('\t' * (level + 1), "int", "size", size))
			vector = GetMembers(members, level, i)
			i.v += len(vector) - 1
			vector = vector[3:]  # vector.RemoveRange(0, 3)
			for j in range(size):
				sb.append("{0}[{1}]\r\n".format('\t' * (level + 2), j))
				tmp = RefInt(0)
				ReadStringValue(sb, vector, reader, tmp)
		else:
			append = False
			sb.append("{0}{1} {2}\r\n".format('\t' * (level), varTypeStr, varNameStr))
			eclass = GetMembers(members, level, i.v)
			eclass.pop(0)  # .RemoveAt(0)
			i.v += len(eclass)
			j = RefInt(0)
			while j < len(eclass):
				ReadStringValue(sb, eclass, reader, j)
				j.v += 1
	
	if append:
		sb.append("{0}{1} {2} = {3}\r\n".format('\t' * (level), varTypeStr, varNameStr, value))
	if align:
		reader.AlignStream()
	
	return sb


def ReadUType(members: list, reader) -> dict:
	# (List<TypeTreeNode> members, BinaryReader reader)
	i = RefInt(0)
	obj = {}
	while i.v < len(members):
		member = members[i.v]
		obj[member.m_Name] = ReadValue(members, reader, i)
		i.v += 1
	return obj


def ReadValue(members: list, reader: EndianBinaryReader, i) -> object:
	if type(i) != RefInt:
		i = RefInt(i)
	member = members[i.v]
	level = member.m_Level
	varTypeStr = member.m_Type
	align = (member.m_MetaFlag & 0x4000) != 0
	if varTypeStr == "SInt8":
		value = reader.ReadSByte()
	elif varTypeStr == "UInt8":
		value = reader.ReadByte()
	elif varTypeStr in ["short", "SInt16"]:
		value = reader.ReadInt16()
	elif varTypeStr in ["UInt16", "unsigned short"]:
		value = reader.ReadUInt16()
	elif varTypeStr in ["int", "SInt32"]:
		value = reader.ReadInt32()
	elif varTypeStr in ["UInt32", "unsigned int", "Type*"]:
		value = reader.ReadUInt32()
	elif varTypeStr in ["long long", "SInt64"]:
		value = reader.ReadInt64()
	elif varTypeStr in ["UInt64", "unsigned long long"]:
		value = reader.ReadUInt64()
	elif varTypeStr == "float":
		value = reader.ReadSingle()
	elif varTypeStr == "double":
		value = reader.ReadDouble()
	elif varTypeStr == "bool":
		value = reader.ReadBoolean()
	elif varTypeStr == "string":
		value = reader.ReadAlignedString()
		i.v += 3
	elif varTypeStr == "map":
		if ((members[i + 1].m_MetaFlag & 0x4000) != 0):
			align = True
		size = reader.ReadInt32()
		dic = {}
		map = GetMembers(members, level, i)
		i.v += len(map) - 1
		map = map[4:]  # map.RemoveRange(0, 4)
		first = GetMembers(map, map[0].m_Level, 0)
		map = map[len(first):]  # .RemoveRange(0, len(first))
		second = map
		for j in range(size):
			tmp1 = RefInt(0)
			tmp2 = RefInt(0)
			v1 = ReadValue(first, reader, tmp1)  # python reads the value first and then the key, so it has to be this way
			dic[v1] = ReadValue(second, reader, tmp2)
		value = dic
	elif varTypeStr == "TypelessData":
		size = reader.ReadInt32()
		value = reader.ReadBytes(size)
		i.v += 2
	else:
		if (i != len(members) and members[i.v + 1].m_Type == "Array"):  # Array
			if ((members[i.v + 1].m_MetaFlag & 0x4000) != 0):
				align = True
			size = reader.ReadInt32()
			_list = []
			vector = GetMembers(members, level, i)
			i.v += len(vector) - 1
			vector = vector[3:]  # vector.RemoveRange(0, 3)
			for j in range(size):
				tmp = RefInt(0)
				_list.append(ReadValue(vector, reader, tmp))
			value = _list
		else:  # Class
			eclass = GetMembers(members, level, i)
			eclass.pop(0)  # .RemoveAt(0)
			i.v += len(eclass)
			obj = {}
			j = RefInt(0)
			while j < len(eclass):
				# for j in range(len(eclass)):
				classmember = eclass[j.v]
				name = classmember.m_Name
				obj[name] = ReadValue(eclass, reader, j)
				j.v += 1
			value = obj
	if align:
		reader.AlignStream()
	return value


def WriteValue(value: dict, members: list, write: EndianBinaryReader, i):
	member = members[i.v]
	level = member.m_Level
	varTypeStr = member.m_Type
	align = (member.m_MetaFlag & 0x4000) != 0
	if varTypeStr == "SInt8":
		write.WriteSByte(value)
	elif varTypeStr == "UInt8":
		write.WriteByte(value)
	elif varTypeStr in ["short", "SInt16"]:
		write.WriteShort(value)
	elif varTypeStr in ["UInt16", "unsigned short"]:
		write.WriteUShort(value)
	elif varTypeStr in ["int", "SInt32"]:
		write.WriteInt(value)
	elif varTypeStr in ["UInt32", "unsigned int", "Type*"]:
		write.WriteUInt(value)
	elif varTypeStr in ["long long", "SInt64"]:
		write.WriteLong(value)
	elif varTypeStr in ["UInt64", "unsigned long long"]:
		write.WriteULong(value)
	elif varTypeStr == "float":
		write.WriteFloat(value)
	elif varTypeStr == "double":
		write.WriteDouble(value)
	elif varTypeStr == "bool":
		write.WriteBool(value)
	elif varTypeStr == "string":
		write.WriteAlignedString(value)
		i.v += 3
	elif varTypeStr == "map":
		if ((members[i + 1].m_MetaFlag & 0x4000) != 0):
			align = True
		dic = value.items()
		size = len(dic)
		write.Write(size)
		map = GetMembers(members, level, i)
		i.v += len(map) - 1
		map = map[4:]  # map.RemoveRange(0, 4)
		first = GetMembers(map, map[0].m_Level, 0)
		map = map[len(first):]  # .RemoveRange(0, len(first))
		second = map
		for j in range(size):
			tmp1 = RefInt(0)
			tmp2 = RefInt(0)
			WriteValue(dic[j][0], first, write, tmp1)  # key
			WriteValue(dic[j][1], second, write, tmp2)  # value
	elif varTypeStr == "TypelessData":
		byts = bytes(value)
		size = len(byts)
		write.Write(size)
		write.Write(bytes)
		i.v += 2
	else:
		if (i != len(members) and members[i + 1].m_Type == "Array"):  # Array
			if ((members[i.v + 1].m_MetaFlag & 0x4000) != 0):
				align = True
			list = value
			size = len(list)
			write.Write(size)
			vector = GetMembers(members, level, i)
			i.v += len(vector) - 1
			vector = vector[3:]  # vector.RemoveRange(0, 3)
			for j in range(size):
				tmp = RefInt(0)
				WriteValue(list[j], vector, write, tmp)
		else:  # Class
			eclass = GetMembers(members, level, i)
			eclass.pop(0)  # .RemoveAt(0)
			i.v += len(eclass)
			obj = value
			j = RefInt(0)
			# for j, classmember in enumerate(eclass):
			while j < len(eclass):
				classmember = eclass[j.v]
				name = classmember.m_Name
				WriteValue(obj[name], eclass, write, j)
	if align:
		write.AlignStream(4)


def ReadValuePy(dic, members: list, reader: EndianBinaryReader, i: RefInt = RefInt(0)):
	if type(i) != RefInt:
		i = RefInt(i)
	member = members[i.v]
	level = member.m_Level
	varTypeStr = member.m_Type
	varNameStr = member.m_Name
	value = None
	append = True
	align = (member.m_MetaFlag & 0x4000) != 0
	if varTypeStr == "SInt8":
		value = reader.ReadSByte()
	elif varTypeStr == "UInt8":
		value = reader.ReadByte()
	elif varTypeStr in ["short", "SInt16"]:
		value = reader.ReadInt16()
	elif varTypeStr in ["UInt16", "unsigned short"]:
		value = reader.ReadUInt16()
	elif varTypeStr in ["int", "SInt32"]:
		value = reader.ReadInt32()
	elif varTypeStr in ["UInt32", "unsigned int", "Type*"]:
		value = reader.ReadUInt32()
	elif varTypeStr in ["long long", "SInt64"]:
		value = reader.ReadInt64()
	elif varTypeStr in ["UInt64", "unsigned long long"]:
		value = reader.ReadUInt64()
	elif varTypeStr == "float":
		value = reader.ReadSingle()
	elif varTypeStr == "double":
		value = reader.ReadDouble()
	elif varTypeStr == "bool":
		value = reader.ReadBoolean()
	elif varTypeStr == "string":
		append = False
		string = reader.ReadAlignedString()
		value = string
		i.v += 3
	elif varTypeStr == "vector":
		if ((members[i + 1].m_MetaFlag & 0x4000) != 0):
			align = True
		append = False
		size = reader.ReadInt32()
		vector = GetMembers(members, level, i)
		i.v += len(vector) - 1
		vector = vector[3:]  # vector.RemoveRange(0, 3)
		value = {}
		for j in range(size):
			tmp = RefInt(0)
			ReadValuePy(value, vector, reader, tmp)
	
	elif varTypeStr == "map":
		if ((members[i + 1].m_MetaFlag & 0x4000) != 0):
			align = True
		append = False
		size = reader.ReadInt32()
		map = GetMembers(members, level, i)
		i.v += len(map) - 1
		map = map[4:]  # map.RemoveRange(0, 4)
		first = GetMembers(map, map[0].m_Level, 0)
		map = map[len(first):]  # .RemoveRange(0, len(first))
		second = map
		value = []
		for j in range(size):
			tmp1 = RefInt(0)
			tmp2 = RefInt(0)
			value.append([
					ReadValuePy({}, first, reader, tmp1),
					ReadValuePy({}, second, reader, tmp2)
			])
	
	elif varTypeStr == "TypelessData":
		append = False
		size = reader.ReadInt32()
		reader.ReadBytes(size)
		i.v += 2
	else:
		if (i != len(members) and members[i + 1].m_Type == "Array"):
			if ((members[i + 1].m_MetaFlag & 0x4000) != 0):
				align = True
			append = False
			size = reader.ReadInt32()
			vector = GetMembers(members, level, i)
			i.v += len(vector) - 1
			vector = vector[3:]  # vector.RemoveRange(0, 3)
			value = []
			for j in range(size):
				tmp = RefInt(0)
				value.append(ReadValuePy({}, vector, reader, tmp))
		else:
			append = False
			eclass = GetMembers(members, level, i.v)
			eclass.pop(0)  # .RemoveAt(0)
			i.v += len(eclass)
			j = RefInt(0)
			value = {}
			while j < len(eclass):
				ReadValuePy(value, eclass, reader, j)
				j.v += 1
	
	if align:
		reader.AlignStream()
	
	dic[varNameStr] = value
	return dic
