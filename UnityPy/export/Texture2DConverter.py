from ..enums import TextureFormat
from enum import IntEnum
from PIL import Image, ImageOps
import math
try:
	from decrunch import File as CrunchFile
	#from decrunch_unity import File as CrunchFile_U
except ImportError:
    print('Couldn\'t import decrunch.\Decrunch is required to process crunched textures.')
try:
	import etcpack
except ImportError:
	print('Couldn\'t import etcoack. etcpack is required to decompress ETC1/2 textures.')
try:
	import pvrtc_decoder
except ImportError:
	print('Couldn\'t import pvrtc_decoder. pvrt_decoder is required to decompress ETC1/2 textures.')
try:
	import astc_decomp
except ImportError:
	print('Couldn\'t import astc_decomp. astc_decomp is required to decompress ASTC textures.')
from ..enums import BuildTarget
from ..math import Half


"""
TESTED FORMATS
Alpha8
ARGB32
ARGB4444
DXT1
DXT5
ETC_RGB4
ETC2_RGB
ETC2_RGBA
ETC2_RGBACrunched
PVRTC_RGB4
RGB24
RGB565
RGBA32
RGBA4444
"""

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

		# INT8
		if self.m_TextureFormat == TextureFormat.Alpha8:  
			self.pil_args = ('A',)

		elif self.m_TextureFormat == TextureFormat.R8:  
			self.pil_mode = 'RGB'
			self.pil_args = ('R',)

		elif self.m_TextureFormat == TextureFormat.RG16:  
			RGBA32 = bytearray(self.image_data_size * 2)
			for i in range(0, self.image_data_size, 2):
				RGBA32[i * 2 + 1] = self.image_data[i + 1]  # G
				RGBA32[i * 2 + 0] = self.image_data[i]  # R
				RGBA32[i * 2 + 3] = 255  # A
			self.image_data = bytes(RGBA32)
   
		if self.m_TextureFormat == TextureFormat.ARGB4444:  
			self.pil_args = ('RGBA;4B',)
			self.pil_swap = [2,1,0,3]

		elif self.m_TextureFormat == TextureFormat.RGB24:  
			self.pil_mode = 'RGB'
			self.pil_args = ('RGB',)

		elif self.m_TextureFormat == TextureFormat.RGBA32:  
			self.pil_args = ('RGBA',)

		elif self.m_TextureFormat == TextureFormat.ARGB32:  
			self.pil_args = ('ARGB',)

		elif self.m_TextureFormat == TextureFormat.RGBA4444:  
			self.pil_args = ('RGBA;4B',)
			self.pil_swap = [3,2,1,0]
   
		elif self.m_TextureFormat == TextureFormat.BGRA32:  
			self.pil_args = ('BGRA',)
   
		# INT16
		elif self.m_TextureFormat == TextureFormat.R16:
			self.pil_mode = 'RGB'
			self.pil_args = ('R;16',)
			# RGBA32 = bytearray(self.image_data_size * 2)
			# for i in range(0, self.image_data_size, 2):
			# 	f = Half.ToHalf(self.image_data, i)
			# 	RGBA32[i * 2 + 0] = (math.ceil(f * 255))%256  # R
			# 	RGBA32[i * 2 + 3] = 255  # A
			# self.image_data = bytes(RGBA32)

		elif self.m_TextureFormat == TextureFormat.RGB565:  # test passed
			self.pil_mode = 'RGB'
			self.pil_args = ('BGR;16',)
			self.SwapBytesForXbox(self.platform)

		# FLOAT
		elif self.m_TextureFormat == TextureFormat.RFloat: 
			self.pil_mode = 'RGB'
			self.pil_args = ('RF',)


		elif self.m_TextureFormat == TextureFormat.RGBAFloat: 
			self.pil_mode = 'RGBA'
			self.pil_args = ('RGBAF',)

		# BCN
		elif self.m_TextureFormat in [ # test passed
				TextureFormat.DXT1,  
				TextureFormat.DXT1Crunched  
		]:
			self.pil_args = (1,)
			self.pil_codec = 'bcn'
			self.SwapBytesForXbox(self.platform)

		elif self.m_TextureFormat in [ # test passed
				TextureFormat.DXT5,  
				TextureFormat.DXT5Crunched  
		]:
			self.pil_args = (3,)
			self.pil_codec = 'bcn'
			self.SwapBytesForXbox(self.platform)

   
		elif self.m_TextureFormat == TextureFormat.BC4:  
			self.pil_args = (4,)
			self.pil_codec = 'bcn'
			self.pil_mode = 'L'
   
		elif self.m_TextureFormat == TextureFormat.BC5:  
			self.pil_args = (5,)
			self.pil_codec = 'bcn'

		elif self.m_TextureFormat == TextureFormat.BC6H:  
			self.pil_args = (6,)
			self.pil_codec = 'bcn'

		elif self.m_TextureFormat == TextureFormat.BC7:  
			self.pil_args = (7,)
			self.pil_codec = 'bcn'


		# ETC
		elif self.m_TextureFormat in [ # test passed
				TextureFormat.ETC_RGB4Crunched,  
				TextureFormat.ETC_RGB4_3DS,  
				TextureFormat.ETC_RGB4  
		]:
			self.pil_args = (0)
			self.pil_codec = 'etc2'
			self.pil_mode = 'RGB'

		elif self.m_TextureFormat == TextureFormat.ETC2_RGB: # test passed
			self.pil_args = (1)
			self.pil_codec = 'etc2'
			self.pil_mode = 'RGB'

		elif self.m_TextureFormat == TextureFormat.ETC2_RGBA1:  
			self.pil_args = (4)
			self.pil_codec = 'etc2'

		elif self.m_TextureFormat in [	# test passed
				TextureFormat.ETC2_RGBA8Crunched,  
				TextureFormat.ETC_RGBA8_3DS,  
				TextureFormat.ETC2_RGBA8  
		]:
			self.pil_args = (3)
			self.pil_codec = 'etc2'

		# PVRTC
		elif self.m_TextureFormat == TextureFormat.PVRTC_RGB2:  
			self.pil_args = (0)
			self.pil_codec = 'pvrtc'
			self.pil_mode = 'RGBA'

		elif self.m_TextureFormat == TextureFormat.PVRTC_RGBA2:  
			self.pil_args = (0)
			self.pil_codec = 'pvrtc'
			self.pil_mode = 'RGBA'

		elif self.m_TextureFormat == TextureFormat.PVRTC_RGB4:	# test passed
			self.pil_args = (0)
			self.pil_codec = 'pvrtc'
			self.pil_mode = 'RGBA'

		elif self.m_TextureFormat == TextureFormat.PVRTC_RGBA4:  
			self.pil_args = (0)
			self.pil_codec = 'pvrtc'
			self.pil_mode = 'RGBA'

		# ASTC
		elif self.m_TextureFormat in [
				TextureFormat.ASTC_RGB_4x4,  # test pass
				TextureFormat.ASTC_RGBA_4x4,  # test pass
		]:
			self.pil_codec = 'astc'
			self.pil_args = (4, 4)

		elif self.m_TextureFormat in [
				TextureFormat.ASTC_RGB_5x5,  # test pass
				TextureFormat.ASTC_RGBA_5x5,  # test pass
		]:
			self.pil_codec = 'astc'
			self.pil_args = (5, 5)

		elif self.m_TextureFormat in [
				TextureFormat.ASTC_RGB_6x6,  # test pass
				TextureFormat.ASTC_RGBA_6x6,  # test pass
		]:
			self.pil_codec = 'astc'
			self.pil_args = (6, 6)

		elif self.m_TextureFormat in [
				TextureFormat.ASTC_RGB_8x8,  # test pass
				TextureFormat.ASTC_RGBA_8x8,  # test pass
		]:
			self.pil_codec = 'astc'
			self.pil_args = (8, 8)

		elif self.m_TextureFormat in [
				TextureFormat.ASTC_RGB_10x10,  # test pass
				TextureFormat.ASTC_RGBA_10x10,  # test pass
		]:
			self.pil_codec = 'astc'
			self.pil_args = (10, 10)

		elif self.m_TextureFormat in [
				TextureFormat.ASTC_RGB_12x12,  # test pass
				TextureFormat.ASTC_RGBA_12x12,  # test pass
		]:
			self.pil_codec = 'astc'
			self.pil_args = (12, 12)

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