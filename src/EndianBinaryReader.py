import struct
import io

# dummies for now
Quaternion = object
Vector2 = object
Vector3 = object
Vector4 = object
Matrix4x4 = object
Color = object


class EndianBinaryReader():
	endian = '>'
	Position = 0
	
	def __init__(self, input, endian = '>'):
		if type(input) == bytes:
			self.stream = io.BytesIO(input)
		else:
			self.stream = input
		
		self.endian = endian
		self.Length = self.stream.seek(0, 2)
		self.Position = 0
	
	# Position
	def getPosition(self):
		return self.stream.tell()
	
	def setPosition(self, value):
		self.stream.seek(value)
	
	Position = property(getPosition, setPosition)
	
	@property
	def bytes(self):
		lastPos = self.Position
		self.Position = 0
		return bytes(self.read())
		self.Position = lastPos
	
	def Dispose(self):
		self.stream.close()
		pass
	
	def read(self, *args):
		return self.stream.read(*args)
	
	def ReadByte(self) -> int:
		return struct.unpack(self.endian + "b", self.read(1))[0]
	
	def ReadSByte(self) -> int:
		return struct.unpack(self.endian + "B", self.read(1))[0]
	
	def ReadBytes(self, num) -> bytes:
		return self.read(num)
	
	def ReadInt16(self) -> int:
		return struct.unpack(self.endian + "h", self.read(2))[0]
	
	# return int.from_bytes(self.read(2), 'little' if self.endian == '<' else 'big', signed = True)
	
	def ReadInt32(self) -> int:
		return struct.unpack(self.endian + "i", self.read(4))[0]
	
	# return int.from_bytes(self.read(4), 'little' if self.endian == '<' else 'big', signed = True)
	
	def ReadInt64(self) -> int:
		return struct.unpack(self.endian + "q", self.read(8))[0]
	
	# return int.from_bytes(self.read(8), 'little' if self.endian == '<' else 'big', signed = True)
	
	def ReadUInt16(self) -> int:
		return struct.unpack(self.endian + "H", self.read(2))[0]
	
	# return int.from_bytes(self.read(2), 'little' if self.endian == '<' else 'big', signed = False)
	
	def ReadUInt32(self) -> int:
		return struct.unpack(self.endian + "I", self.read(4))[0]
	
	# return int.from_bytes(self.read(4), 'little' if self.endian == '<' else 'big', signed = False)
	
	def ReadUInt64(self) -> int:
		return struct.unpack(self.endian + "Q", self.read(8))[0]
	
	# return int.from_bytes(self.read(8), 'little' if self.endian == '<' else 'big', signed = False)
	
	def ReadSingle(self) -> float:
		return struct.unpack(self.endian + "f", self.read(4))[0]
	
	def ReadDouble(self) -> float:
		return struct.unpack(self.endian + "d", self.read(8))[0]
	
	def ReadBoolean(self) -> bool:
		return bool(struct.unpack(self.endian + "?", self.read(1))[0])
	
	def ReadString(self, size = None, encoding = "utf-8") -> str:
		if size is None:
			ret = self.ReadStringToNull()
		else:
			ret = struct.unpack(self.endian + "%is" %
			                    (size), self.read(size))[0]
		try:
			return ret.decode(encoding)
		except UnicodeDecodeError:
			return ret
	
	def ReadStringToNull(self, maxLength = 32767) -> str:
		ret = []
		c = b""
		while c != b"\0" and len(ret) < maxLength and self.Position != self.Length:
			ret.append(c)
			c = self.read(1)
			if not c:
				raise ValueError("Unterminated string: %r" % (ret))
		return b"".join(ret).decode('utf8', 'replace')
	
	def ReadAlignedString(self):
		length = self.ReadInt32()
		if (length > 0 and length <= self.Length - self.Position):
			stringData = self.ReadBytes(length)
			result = stringData.decode('utf8', 'backslashreplace')
			self.AlignStream(4)
			return result
		return ""
	
	def AlignStream(self, alignment = 4):
		pos = self.Position
		mod = pos % alignment
		if mod != 0:
			self.Position += alignment - mod
	
	def ReadQuaternion(self):
		return Quaternion(self.ReadSingle(), self.ReadSingle(), self.ReadSingle(), self.ReadSingle())
	
	def ReadVector2(self):
		return Vector2(self.ReadSingle(), self.ReadSingle())
	
	def ReadVector3(self):
		return Vector3(self.ReadSingle(), self.ReadSingle(), self.ReadSingle())
	
	def ReadVector4(self):
		return Vector4(self.ReadSingle(), self.ReadSingle(), self.ReadSingle(), self.ReadSingle())
	
	def ReadRectangleF(self):
		return (self.ReadSingle(), self.ReadSingle(), self.ReadSingle(), self.ReadSingle())
	
	def ReadColor4(self):
		return Color(self.ReadSingle(), self.ReadSingle(), self.ReadSingle(), self.ReadSingle())
	
	def ReadMatrix(self):
		return Matrix4x4(self.ReadSingleArray(16))
	
	def ReadArray(self, command, length: int):
		return [command() for i in range(length)]
	
	def ReadBooleanArray(self):
		return self.ReadArray(self.ReadBoolean, self.ReadInt32())
	
	def ReadUInt16Array(self):
		return self.ReadArray(self.ReadUInt16, self.ReadInt32())
	
	def ReadInt32Array(self, length = 0):
		return self.ReadArray(self.ReadInt32, length if length else self.ReadInt32())
	
	def ReadUInt32Array(self, length = 0):
		return self.ReadArray(self.ReadUInt32, length if length else self.ReadInt32())
	
	def ReadSingleArray(self, length = 0):
		return self.ReadArray(self.ReadSingle, length if length else self.ReadInt32())
	
	def ReadStringArray(self):
		return self.ReadArray(self.ReadAlignedString, self.ReadInt32())
	
	def ReadVector2Array(self):
		return self.ReadArray(self.ReadVector2, self.ReadInt32())
	
	def ReadVector4Array(self):
		return self.ReadArray(self.ReadVector4, self.ReadInt32())
	
	def ReadMatrixArray(self):
		return self.ReadArray(self.ReadMatrix, self.ReadInt32())

# def write(self, *args):
# 	pass
# 	#self.stream.write(*args)

# def Write(self, value):
# 	if type(value) == int:
# 		self.WriteInt(value)
# 	self.write(value)

# def WriteByte(self, value):
# 	self.write(struct.pack(self.endian + "b", value))

# def WriteSByte(self, value):
# 	self.write(struct.pack(self.endian + "B", value))

# def WriteShort(self, value):
# 	self.write(struct.pack(self.endian + "h", value))
# 	#self.write(int.to_bytes(value, 2, 'little' if self.endian == '<' else 'big', signed = True))

# def WriteUShort(self, value):
# 	self.write(struct.pack(self.endian + "H", value))
# 	#self.write(int.to_bytes(value, 2, 'little' if self.endian == '<' else 'big', signed = False))

# def WriteInt(self, value):
# 	self.write(struct.pack(self.endian + "i", value))
# 	#self.write(int.to_bytes(value, 4, 'little' if self.endian == '<' else 'big', signed = True))

# def WriteUInt(self, value):
# 	self.write(struct.pack(self.endian + "I", value))
# 	#self.write(int.to_bytes(value, 4, 'little' if self.endian == '<' else 'big', signed = False))

# def WriteLong(self, value):
# 	self.write(struct.pack(self.endian + "q", value))
# 	#self.write(int.to_bytes(value, 8, 'little' if self.endian == '<' else 'big', signed = True))

# def WriteULong(self, value):
# 	self.write(struct.pack(self.endian + "Q", value))
# 	#self.write(int.to_bytes(value, 8, 'little' if self.endian == '<' else 'big', signed = False))

# def WriteFloat(self, value):
# 	self.write(struct.pack(self.endian + "f", value))

# def WriteDouble(self, value):
# 	self.write(struct.pack(self.endian + "d", value))

# def WriteBool(self, value):
# 	self.write(struct.pack(self.endian + "?", value))

# def WriteAlignedString(self, value):
# 	byts = value.encode('utf8')
# 	self.write(len(byts))
# 	self.write(byts)
# 	self.AlignStream(4)
