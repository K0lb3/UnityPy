from ..enums import TextureFormat
from enum import IntEnum
from PIL import Image, ImageOps
import math
from decrunch import File as CrunchFile
from decrunch_unity import File as CrunchFile_U
import etcpack
from ..enums import BuildTarget
from ..math import Half


class Texture2DConverter:
	# RAW Start
	pil_mode = "RGBA"
	pil_codec = "raw"
	pil_args = ("RGBA",)
	pil_swap = [] # for 4444 types to fix their channels
	# RAW End

	def ToImage(self) -> Image:
		mode = self.pil_mode
		codec = self.pil_codec
		args = self.pil_args
		size = (self.m_Width, self.m_Height)
		if not self.image_data and size == (0, 0):
			return None
		img = Image.frombytes(mode, size, self.image_data, codec, args)
		if self.pil_swap:
			channels = img.split()
			img = Image.merge(mode, [channels[x] for x in self.pil_swap])
		return img

	def DecompressCRN(self):
		#if (self.version[0] > 2017 or (self.version[0] == 2017 and self.version[1] >= 3) #2017.3 and up
		#		or self.m_TextureFormat == TextureFormat.ETC_RGB4Crunched
		#		or self.m_TextureFormat == TextureFormat.ETC2_RGBA8Crunched):
		#	# Unity Crunch
		#	self.image_data = bytes(CrunchFile_U(self.image_data).decode_level(0))
		#	self.image_data_size = len(self.image_data)
		#else: #normal crunch
		self.image_data = bytes(CrunchFile(self.image_data).decode_level(0))
		self.image_data_size = len(self.image_data)


	def __init__(self, m_Texture2D):
		self.image_data = m_Texture2D.image_data
		self.image_data_size = len(self.image_data)
		self.m_Width = m_Texture2D.m_Width
		self.m_Height = m_Texture2D.m_Height
		self.m_TextureFormat = m_Texture2D.m_TextureFormat
		self.version = m_Texture2D.version
		self.platform = m_Texture2D.platform

		if self.m_TextureFormat == TextureFormat.Alpha8:  # test pass
			self.pil_args = ('A',)

		if self.m_TextureFormat == TextureFormat.ARGB4444:  # test pass
			self.pil_args = ('RGBA;4B',)
			self.pil_swap = [2,1,0,3]

		elif self.m_TextureFormat == TextureFormat.RGB24:  # test pass
			self.pil_mode = 'RGB'
			self.pil_args = ('RGB',)

		elif self.m_TextureFormat == TextureFormat.RGBA32:  # test pass
			self.pil_args = ('RGBA',)

		elif self.m_TextureFormat == TextureFormat.ARGB32:  # test pass
			self.pil_args = ('ARGB',)

		elif self.m_TextureFormat == TextureFormat.RGB565:  # test pass
			self.pil_mode = 'RGB'
			self.pil_args = ('BGR;16',)
			self.SwapBytesForXbox(self.platform)

		elif self.m_TextureFormat == TextureFormat.R16:  # test pass
			self.pil_mode = 'RGBA'
			RGBA32 = bytearray(self.image_data_size * 2)
			for i in range(0, self.image_data_size, 2):
				f = Half.ToHalf(self.image_data, i)
				RGBA32[i * 2 + 0] = (math.ceil(f * 255))%256  # R
				RGBA32[i * 2 + 3] = 255  # A
			self.image_data = bytes(RGBA32)

		elif self.m_TextureFormat in [
				TextureFormat.DXT1,  # test pass
				TextureFormat.DXT1Crunched  # test pass
		]:
			self.pil_args = (1,)
			self.pil_codec = 'bcn'
			self.SwapBytesForXbox(self.platform)

		elif self.m_TextureFormat in [
				TextureFormat.DXT5,  # test pass
				TextureFormat.DXT5Crunched  # test pass
		]:
			self.pil_args = (3,)
			self.pil_codec = 'bcn'
			self.SwapBytesForXbox(self.platform)

		elif self.m_TextureFormat == TextureFormat.RGBA4444:  # test pass
			self.pil_args = ('RGBA;4B',)
			self.pil_swap = [3,2,1,0]

		elif self.m_TextureFormat == TextureFormat.BGRA32:  # test pass
			self.pil_args = ('BGRA',)
   
		elif self.m_TextureFormat == TextureFormat.BC4:  # test pass
			self.pil_args = (4,)
			self.pil_codec = 'bcn'
			self.pil_mode = ('L',)
   
		elif self.m_TextureFormat == TextureFormat.BC5:  # test pass
			self.pil_args = (5,)
			self.pil_codec = 'bcn'

		elif self.m_TextureFormat == TextureFormat.BC6H:  # test pass
			self.pil_args = (6,)
			self.pil_codec = 'bcn'

		elif self.m_TextureFormat == TextureFormat.BC7:  # test pass
			self.pil_args = (7,)
			self.pil_codec = 'bcn'
			self.pil_mode = ('RGBAF',)

		elif self.m_TextureFormat in [
				TextureFormat.ETC_RGB4Crunched,  # test pass
				TextureFormat.ETC_RGB4_3DS,  # test pass
				TextureFormat.ETC_RGB4  # test pass
		]:
			self.pil_args = (0,)
			self.pil_codec = 'etc2'
			self.pil_mode = 'RGB'

		elif self.m_TextureFormat == TextureFormat.ETC2_RGB:  # test pass
			self.pil_args = (1,)
			self.pil_codec = 'etc2'
			self.pil_mode = 'RGB'

		elif self.m_TextureFormat == TextureFormat.ETC2_RGBA1:  # test pass
			self.pil_args = (4,)
			self.pil_codec = 'etc2'

		elif self.m_TextureFormat in [
				TextureFormat.ETC2_RGBA8Crunched,  # test pass
				TextureFormat.ETC_RGBA8_3DS,  # test pass
				TextureFormat.ETC2_RGBA8  # test pass
		]:
			self.pil_args = (3,)
			self.pil_codec = 'etc2'

		elif self.m_TextureFormat == TextureFormat.RG16:  # test pass
			RGBA32 = bytearray(self.image_data_size * 2)
			for i in range(0, self.image_data_size, 2):
				RGBA32[i * 2 + 1] = self.image_data[i + 1]  # G
				RGBA32[i * 2 + 0] = self.image_data[i]  # R
				RGBA32[i * 2 + 3] = 255  # A
			self.image_data = bytes(RGBA32)

		elif self.m_TextureFormat == TextureFormat.R8:  # test pass
			self.pil_mode = 'RGB'
			self.pil_args = ('R',)
      
		elif self.m_TextureFormat == TextureFormat.RFloat: # test pass
			self.pil_mode = 'RGB'
			self.pil_args = ('RF',)


		elif self.m_TextureFormat == TextureFormat.RGBAFloat: # test pass
			self.pil_mode = 'RGBA'
			self.pil_args = ('RGBAF',)


	def SwapBytesForXbox(self, platform: BuildTarget):
		if platform == BuildTarget.XBOX360:  # swap bytes for Xbox confirmed, PS3 not encountered
			for i in range(0, self.image_data_size, 2):
				self.image_data[i:i+2] = self.image_data[i:i+2][::-1]


	def ConvertToImage(self, flip: bool) -> Image:
		if not self.image_data:
			raise EOFError("No Image Data")
			#return Image.new('RGBA')

		if 'Crunched' in self.m_TextureFormat.name:
			self.DecompressCRN()

		bitmap = self.ToImage()

		if bitmap and flip:
			bitmap = ImageOps.flip(bitmap)
		return bitmap