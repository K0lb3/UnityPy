from PIL import Image

from ..enums import TextureFormat, BuildTarget

try:
	from decrunch import File as CrunchFile
except ImportError:
	print('Couldn\'t import decrunch.Decrunch is required to process crunched textures.')
try:
	import etcpack
except ImportError:
	print('Couldn\'t import etcoack. etcpack is required to decompress ETC1/2 textures.')
try:
	import pvrtc_decoder
except ImportError:
	print('Coudn\'t import pvrtc_decoder. pvrt_decoder is required to decompress ETC1/2 textures.')
try:
	import astc_decomp
except ImportError:
	print('Couldn\'t import astc_decomp. astc_decomp is required to decompress ASTC textures.')


def get_image_from_texture2d(texture_2d, flip=True) -> Image:
	# init variables
	mode = "RGBA"
	codec = "raw"
	args = ("RGBA",)
	swap = []  # for 4444 types to fix their channels

	image_data = texture_2d.image_data
	texture_format = texture_2d.m_TextureFormat
	platform = texture_2d.platform

	# INT8
	if texture_format == TextureFormat.Alpha8:
		args = ('A',)

	elif texture_format == TextureFormat.R8:
		mode = 'RGB'
		args = ('R',)

	elif texture_format == TextureFormat.RG16:
		image_data_size = len(image_data)
		rgba32 = bytearray(image_data_size * 2)
		for i in range(0, image_data_size, 2):
			rgba32[i * 2 + 1] = image_data[i + 1]  # G
			rgba32[i * 2 + 0] = image_data[i]  # R
			rgba32[i * 2 + 3] = 255  # A
		image_data = bytes(rgba32)

	if texture_format == TextureFormat.ARGB4444:
		args = ('RGBA;4B',)
		swap = [2, 1, 0, 3]

	elif texture_format == TextureFormat.RGB24:
		mode = 'RGB'
		args = ('RGB',)

	elif texture_format == TextureFormat.RGBA32:
		args = ('RGBA',)

	elif texture_format == TextureFormat.ARGB32:
		args = ('ARGB',)

	elif texture_format == TextureFormat.RGBA4444:
		args = ('RGBA;4B',)
		swap = [3, 2, 1, 0]

	elif texture_format == TextureFormat.BGRA32:
		args = ('BGRA',)

	# INT16
	elif texture_format == TextureFormat.R16:
		mode = 'RGB'
		args = ('R;16',)
	# rgba32 = bytearray(image_data_size * 2)
	# for i in range(0, image_data_size, 2):
	# 	f = Half.ToHalf(image_data, i)
	# 	rgba32[i * 2 + 0] = (math.ceil(f * 255))%256  # R
	# 	rgba32[i * 2 + 3] = 255  # A
	# image_data = bytes(rgba32)

	elif texture_format == TextureFormat.RGB565:  # test passed
		mode = 'RGB'
		args = ('BGR;16',)
		image_data = swap_bytes_for_xbox(image_data, platform)

	# FLOAT
	elif texture_format == TextureFormat.RFloat:
		mode = 'RGB'
		args = ('RF',)

	elif texture_format == TextureFormat.RGBAFloat:
		mode = 'RGBA'
		args = ('RGBAF',)

	# BCN
	elif texture_format in [  # test passed
		TextureFormat.DXT1,
		TextureFormat.DXT1Crunched
	]:
		args = (1,)
		codec = 'bcn'
		image_data = swap_bytes_for_xbox(image_data, platform)

	elif texture_format in [  # test passed
		TextureFormat.DXT5,
		TextureFormat.DXT5Crunched
	]:
		args = (3,)
		codec = 'bcn'
		image_data = swap_bytes_for_xbox(image_data, platform)

	elif texture_format == TextureFormat.BC4:
		args = (4,)
		codec = 'bcn'
		mode = 'L'

	elif texture_format == TextureFormat.BC5:
		args = (5,)
		codec = 'bcn'

	elif texture_format == TextureFormat.BC6H:
		args = (6,)
		codec = 'bcn'

	elif texture_format == TextureFormat.BC7:
		args = (7,)
		codec = 'bcn'

	# ETC
	elif texture_format in [  # test passed
		TextureFormat.ETC_RGB4Crunched,
		TextureFormat.ETC_RGB4_3DS,
		TextureFormat.ETC_RGB4
	]:
		args = (0,)
		codec = 'etc2'
		mode = 'RGB'

	elif texture_format == TextureFormat.ETC2_RGB:  # test passed
		args = (1,)
		codec = 'etc2'
		mode = 'RGB'

	elif texture_format == TextureFormat.ETC2_RGBA1:
		args = (4,)
		codec = 'etc2'

	elif texture_format in [  # test passed
		TextureFormat.ETC2_RGBA8Crunched,
		TextureFormat.ETC_RGBA8_3DS,
		TextureFormat.ETC2_RGBA8
	]:
		args = (3,)
		codec = 'etc2'

	# PVRTC
	elif texture_format == TextureFormat.PVRTC_RGB2:
		args = (0,)
		codec = 'pvrtc'
		mode = 'RGBA'

	elif texture_format == TextureFormat.PVRTC_RGBA2:
		args = (0,)
		codec = 'pvrtc'
		mode = 'RGBA'

	elif texture_format == TextureFormat.PVRTC_RGB4:  # test passed
		args = (0,)
		codec = 'pvrtc'
		mode = 'RGBA'

	elif texture_format == TextureFormat.PVRTC_RGBA4:
		args = (0,)
		codec = 'pvrtc'
		mode = 'RGBA'

	# ASTC
	elif texture_format in [
		TextureFormat.ASTC_RGB_4x4,  # test pass
		TextureFormat.ASTC_RGBA_4x4,  # test pass
	]:
		codec = 'astc'
		args = (4, 4)

	elif texture_format in [
		TextureFormat.ASTC_RGB_5x5,  # test pass
		TextureFormat.ASTC_RGBA_5x5,  # test pass
	]:
		codec = 'astc'
		args = (5, 5)

	elif texture_format in [
		TextureFormat.ASTC_RGB_6x6,  # test pass
		TextureFormat.ASTC_RGBA_6x6,  # test pass
	]:
		codec = 'astc'
		args = (6, 6)

	elif texture_format in [
		TextureFormat.ASTC_RGB_8x8,  # test pass
		TextureFormat.ASTC_RGBA_8x8,  # test pass
	]:
		codec = 'astc'
		args = (8, 8)

	elif texture_format in [
		TextureFormat.ASTC_RGB_10x10,  # test pass
		TextureFormat.ASTC_RGBA_10x10,  # test pass
	]:
		codec = 'astc'
		args = (10, 10)

	elif texture_format in [
		TextureFormat.ASTC_RGB_12x12,  # test pass
		TextureFormat.ASTC_RGBA_12x12,  # test pass
	]:
		codec = 'astc'
		args = (12, 12)

	if not image_data:
		raise EOFError("No Image Data")
	# return Image.new('RGBA')

	if 'Crunched' in texture_format.name:
		# if (version[0] > 2017 or (version[0] == 2017 and version[1] >= 3) #2017.3 and up
		#		or m_TextureFormat == TextureFormat.ETC_RGB4Crunched
		#		or m_TextureFormat == TextureFormat.ETC2_RGBA8Crunched):
		#	# Unity Crunch
		#	image_data = bytes(CrunchFile_U(image_data).decode_level(0))
		#	image_data_size = len(image_data)
		# else: #normal crunch
		# decrunch is using a modified crunch which uses the original crunch and only uses the Unity Version for etc1/2
		image_data = bytes(CrunchFile(image_data).decode_level(0))

	img = Image.frombytes(mode, (texture_2d.m_Width, texture_2d.m_Height), image_data, codec, args)
	if swap:
		channels = img.split()
		img = Image.merge(mode, [channels[x] for x in swap])

	if img and flip:
		return img.transpose(Image.FLIP_TOP_BOTTOM)
	return img


def swap_bytes_for_xbox(image_data, platform: BuildTarget):
	if platform == BuildTarget.XBOX360:  # swap bytes for Xbox confirmed, PS3 not encountered
		for i in range(0, len(image_data), 2):
			image_data[i:i + 2] = image_data[i:i + 2][::-1]
	return image_data
