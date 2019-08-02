import logging
from enum import IntEnum

from .object import Object, field


class TextureFormat(IntEnum):
	Alpha8 = 1
	ARGB4444 = 2
	RGB24 = 3
	RGBA32 = 4
	ARGB32 = 5
	RGB565 = 7
	
	# Direct3D
	DXT1 = 10
	DXT5 = 12
	
	RGBA4444 = 13
	BGRA32 = 14
	
	BC6H = 24
	BC7 = 25
	
	DXT1Crunched = 28
	DXT5Crunched = 29
	
	# PowerVR
	PVRTC_RGB2 = PVRTC_2BPP_RGB = 30
	PVRTC_RGBA2 = PVRTC_2BPP_RGBA = 31
	PVRTC_RGB4 = PVRTC_4BPP_RGB = 32
	PVRTC_RGBA4 = PVRTC_4BPP_RGBA = 33
	
	# Ericsson (Android)
	ETC_RGB4 = 34
	ATC_RGB4 = 35
	ATC_RGBA8 = 36
	
	# Adobe ATF
	ATF_RGB_DXT1 = 38
	ATF_RGBA_JPG = 39
	ATF_RGB_JPG = 40
	
	# Ericsson
	EAC_R = 41
	EAC_R_SIGNED = 42
	EAC_RG = 43
	EAC_RG_SIGNED = 44
	ETC2_RGB = 45
	ETC2_RGBA1 = 46
	ETC2_RGBA8 = 47
	
	# OpenGL / GLES
	ASTC_RGB_4x4 = 48
	ASTC_RGB_5x5 = 49
	ASTC_RGB_6x6 = 50
	ASTC_RGB_8x8 = 51
	ASTC_RGB_10x10 = 52
	ASTC_RGB_12x12 = 53
	ASTC_RGBA_4x4 = 54
	ASTC_RGBA_5x5 = 55
	ASTC_RGBA_6x6 = 56
	ASTC_RGBA_8x8 = 57
	ASTC_RGBA_10x10 = 58
	ASTC_RGBA_12x12 = 59
	
	@property
	def pixel_format(self):
		if self == TextureFormat.RGB24:
			return "RGB"
		elif self == TextureFormat.ARGB32:
			return "ARGB"
		elif self == TextureFormat.RGB565:
			return "RGB;16"
		elif self == TextureFormat.Alpha8:
			return "A"
		elif self == TextureFormat.RGBA4444:
			return "RGBA;4B"
		elif self == TextureFormat.ARGB4444:
			return "RGBA;4B"
		return "RGBA"


IMPLEMENTED_FORMATS = (
		TextureFormat.Alpha8,
		TextureFormat.ARGB4444,
		TextureFormat.RGBA4444,
		TextureFormat.RGB565,
		TextureFormat.RGB24,
		TextureFormat.RGBA32,
		TextureFormat.ARGB32,
		TextureFormat.DXT1,
		TextureFormat.DXT1Crunched,
		TextureFormat.DXT5,
		TextureFormat.DXT5Crunched,
		TextureFormat.BC7,
)


class Sprite(Object):
	border = field("m_Border")
	extrude = field("m_Extrude")
	offset = field("m_Offset")
	rd = field("m_RD")
	rect = field("m_Rect")
	pixels_per_unit = field("m_PixelsToUnits")


class Material(Object):
	global_illumination_flags = field("m_LightmapFlags")
	render_queue = field("m_CustomRenderQueue")
	shader = field("m_Shader")
	shader_keywords = field("m_ShaderKeywords")
	
	@property
	def saved_properties(self):
		def _unpack_prop(value):
			for vk, vv in value:
				if isinstance(vk, str):  # Unity 5.6+
					yield vk, vv
				else:  # Unity <= 5.4
					yield vk["name"], vv
		
		return {k: dict(_unpack_prop(v)) for k, v in self._obj["m_SavedProperties"].items()}


class Texture(Object):
	height = field("m_Height")
	width = field("m_Width")


class Texture2D(Texture):
	data = field("image data")
	lightmap_format = field("m_LightmapFormat")
	texture_settings = field("m_TextureSettings")
	color_space = field("m_ColorSpace")
	is_readable = field("m_IsReadable")
	read_allowed = field("m_ReadAllowed")
	format = field("m_TextureFormat", TextureFormat)
	texture_dimension = field("m_TextureDimension")
	mipmap = field("m_MipMap")
	complete_image_size = field("m_CompleteImageSize")
	stream_data = field("m_StreamData", default = False)
	
	def __repr__(self):
		return "<%s %s (%s %ix%i)>" % (
				self.__class__.__name__, self.name, self.format.name, self.width, self.height
		)
	
	@property
	def image_data(self):
		if self.stream_data and self.stream_data.asset:
			if not hasattr(self, "_data"):
				self._data = self.stream_data.get_data()
			return self._data
		return self.data
	
	@property
	def image(self):
		from PIL import Image
		from decrunch import File as CrunchFile
		
		if self.format not in IMPLEMENTED_FORMATS:
			raise NotImplementedError("Unimplemented _format %r" % (self.format))
		
		if self.format in (TextureFormat.DXT1, TextureFormat.DXT1Crunched):
			codec = "bcn"
			args = (1,)
		elif self.format in (TextureFormat.DXT5, TextureFormat.DXT5Crunched):
			codec = "bcn"
			args = (3,)
		elif self.format == TextureFormat.BC7:
			codec = "bcn"
			args = (7,)
		else:
			codec = "raw"
			args = (self.format.pixel_format,)
		
		mode = "RGB" if self.format.pixel_format in ("RGB", "RGB;16") else "RGBA"
		size = (self.width, self.height)
		
		data = self.image_data
		if self.format in (TextureFormat.DXT1Crunched, TextureFormat.DXT5Crunched):
			data = CrunchFile(self.image_data).decode_level(0)
		
		# Pillow wants bytes, not bytearrays
		data = bytes(data)
		
		if not data and size == (0, 0):
			return None
		
		return Image.frombytes(mode, size, data, codec, args)


class StreamingInfo(Object):
	offset = field("offset")
	size = field("size")
	path = field("path")
	
	def get_data(self):
		if not self.asset:
			logging.warning("No data available for StreamingInfo")
			return b""
		self.asset._buf.seek(self.asset._buf_ofs + self.offset)
		return self.asset._buf.read(self.size)
