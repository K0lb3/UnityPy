from enum import IntEnum


class TextureFormat(IntEnum):
	Alpha8 = 1
	ARGB4444 = 2
	RGB24 = 3
	RGBA32 = 4
	ARGB32 = 5
	RGB565 = 7
	R16 = 9
	
	RGBA4444 = 13
	BGRA32 = 14
	RHalf = 15
	RGHalf = 16
	RGBAHalf = 17
	RFloat = 18
	RGFloat = 19
	RGBAFloat = 20
	YUY2 = 21
	RGB9e5Float = 22
	BC6H = 24
	BC7 = 25
	BC4 = 26
	BC5 = 27
	
	RG16 = 62
	R8 = 63
	
	# Direct3D
	DXT1 = 10
	DXT5 = 12
	
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
	
	ETC_RGB4_3DS = 60
	ETC_RGBA8_3DS = 61
	
	ETC_RGB4Crunched = 64
	ETC2_RGBA8Crunched = 65
	
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
		elif self == TextureFormat.ETC_RGB4:
			return "RGB"
		elif self == TextureFormat.ETC2_RGB:
			return "RGB"
		elif self == TextureFormat.ETC_RGB4_3DS:
			return "RGB"
		elif self == TextureFormat.ETC_RGB4Crunched:
			return "RGB"
		return "RGBA"
	
	@property
	def q_format(self):
		if self in [TextureFormat.DXT1, TextureFormat.DXT1Crunched]:
			return QFORMAT.Q_FORMAT_S3TC_DXT1_RGB
		if self in [TextureFormat.DXT5, TextureFormat.DXT5Crunched]:
			return QFORMAT.Q_FORMAT_S3TC_DXT5_RGBA
		if self == TextureFormat.RHalf:
			return QFORMAT.Q_FORMAT_R_16F
		if self == TextureFormat.RGHalf:
			return QFORMAT.Q_FORMAT_RG_HF
		if self == TextureFormat.RGBAHalf:
			return QFORMAT.Q_FORMAT_RGBA_HF
		if self == TextureFormat.RFloat:
			return QFORMAT.Q_FORMAT_R_F
		if self == TextureFormat.RGFloat:
			return QFORMAT.Q_FORMAT_RG_F
		if self == TextureFormat.RGBAFloat:
			return QFORMAT.Q_FORMAT_RGBA_F
		if self == TextureFormat.RGB9e5Float:
			return QFORMAT.Q_FORMAT_RGB9_E5
		if self == TextureFormat.ATC_RGB4:
			return QFORMAT.Q_FORMAT_ATITC_RGB
		if self == TextureFormat.ATC_RGBA8:
			return QFORMAT.Q_FORMAT_ATC_RGBA_INTERPOLATED_ALPHA
		if self == TextureFormat.EAC_R:
			return QFORMAT.Q_FORMAT_EAC_R_UNSIGNED
		if self == TextureFormat.EAC_R_SIGNED:
			return QFORMAT.Q_FORMAT_EAC_R_SIGNED
		if self == TextureFormat.EAC_RG:
			return QFORMAT.Q_FORMAT_EAC_RG_UNSIGNED
		if self == TextureFormat.EAC_RG_SIGNED:
			return QFORMAT.Q_FORMAT_EAC_RG_SIGNED
	
	@property
	def glInternalFormat(self):
		if self == TextureFormat.RHalf:
			return KTXHeader.GL_R16F
		if self == TextureFormat.RGHalf:
			return KTXHeader.GL_RG16F
		if self == TextureFormat.RGBAHalf:
			return KTXHeader.GL_RGBA16F
		if self == TextureFormat.RFloat:
			return KTXHeader.GL_R32F
		if self == TextureFormat.RGFloat:
			return KTXHeader.GL_RG32F
		if self == TextureFormat.RGBAFloat:
			return KTXHeader.GL_RGBA32F
		if self == TextureFormat.BC4:
			return KTXHeader.GL_COMPRESSED_RED_RGTC1
		if self == TextureFormat.BC5:
			return KTXHeader.GL_COMPRESSED_RG_RGTC2
		if self == TextureFormat.BC6H:
			return KTXHeader.GL_COMPRESSED_RGB_BPTC_UNSIGNED_FLOAT
		if self == TextureFormat.BC7:
			return KTXHeader.GL_COMPRESSED_RGBA_BPTC_UNORM
		if self == TextureFormat.PVRTC_RGB2:
			return KTXHeader.GL_COMPRESSED_RGB_PVRTC_2BPPV1_IMG
		if self == TextureFormat.PVRTC_RGBA2:
			return KTXHeader.GL_COMPRESSED_RGBA_PVRTC_2BPPV1_IMG
		if self == TextureFormat.PVRTC_RGB4:
			return KTXHeader.GL_COMPRESSED_RGB_PVRTC_4BPPV1_IMG
		if self == TextureFormat.PVRTC_RGBA4:
			return KTXHeader.GL_COMPRESSED_RGBA_PVRTC_4BPPV1_IMG
		if self in [TextureFormat.ETC_RGB4Crunched, TextureFormat.ETC_RGB4_3DS, TextureFormat.ETC_RGB4]:
			return KTXHeader.GL_ETC1_RGB8_OES
		if self == TextureFormat.ATC_RGB4:
			return KTXHeader.GL_ATC_RGB_AMD
		if self == TextureFormat.ATC_RGBA8:
			return KTXHeader.GL_ATC_RGBA_INTERPOLATED_ALPHA_AMD
		if self == TextureFormat.EAC_R:
			return KTXHeader.GL_COMPRESSED_R11_EAC
		if self == TextureFormat.EAC_R_SIGNED:
			return KTXHeader.GL_COMPRESSED_SIGNED_R11_EAC
		if self == TextureFormat.EAC_RG:
			return KTXHeader.GL_COMPRESSED_RG11_EAC
		if self == TextureFormat.EAC_RG_SIGNED:
			return KTXHeader.GL_COMPRESSED_SIGNED_RG11_EAC
		if self == TextureFormat.ETC2_RGB:
			return KTXHeader.GL_COMPRESSED_RGB8_ETC2
		if self == TextureFormat.ETC2_RGBA1:
			return KTXHeader.GL_COMPRESSED_RGB8_PUNCHTHROUGH_ALPHA1_ETC2
		if self in [TextureFormat.ETC2_RGBA8Crunched, TextureFormat.ETC_RGBA8_3DS, TextureFormat.ETC2_RGBA8]:
			return KTXHeader.GL_COMPRESSED_RGBA8_ETC2_EAC
	
	@property
	def glBaseInternalFormat(self):
		if self == TextureFormat.RHalf:
			return KTXHeader.GL_RED
		if self == TextureFormat.RGHalf:
			return KTXHeader.GL_RG
		if self == TextureFormat.RGBAHalf:
			return KTXHeader.GL_RGBA
		if self == TextureFormat.RFloat:
			return KTXHeader.GL_RED
		if self == TextureFormat.RGFloat:
			return KTXHeader.GL_RG
		if self == TextureFormat.RGBAFloat:
			return KTXHeader.GL_RGBA
		if self == TextureFormat.BC4:
			return KTXHeader.GL_RED
		if self == TextureFormat.BC5:
			return KTXHeader.GL_RG
		if self == TextureFormat.BC6H:
			return KTXHeader.GL_RGB
		if self == TextureFormat.BC7:
			return KTXHeader.GL_RGBA
		if self == TextureFormat.PVRTC_RGB2:
			return KTXHeader.GL_RGB
		if self == TextureFormat.PVRTC_RGBA2:
			return KTXHeader.GL_RGBA
		if self == TextureFormat.PVRTC_RGB4:
			return KTXHeader.GL_RGB
		if self == TextureFormat.PVRTC_RGBA4:
			return KTXHeader.GL_RGBA
		if self in [TextureFormat.ETC_RGB4Crunched, TextureFormat.ETC_RGB4_3DS, TextureFormat.ETC_RGB4]:
			return KTXHeader.GL_RGB
		if self == TextureFormat.ATC_RGB4:
			return KTXHeader.GL_RGB
		if self == TextureFormat.ATC_RGBA8:
			return KTXHeader.GL_RGBA
		if self == TextureFormat.EAC_R:
			return KTXHeader.GL_RED
		if self == TextureFormat.EAC_R_SIGNED:
			return KTXHeader.GL_RED
		if self == TextureFormat.EAC_RG:
			return KTXHeader.GL_RG
		if self == TextureFormat.EAC_RG_SIGNED:
			return KTXHeader.GL_RG
		if self == TextureFormat.ETC2_RGB:
			return KTXHeader.GL_RGB
		if self == TextureFormat.ETC2_RGBA1:
			return KTXHeader.GL_RGBA
		if self in [TextureFormat.ETC2_RGBA8Crunched, TextureFormat.ETC_RGBA8_3DS, TextureFormat.ETC2_RGBA8]:
			return KTXHeader.GL_RGBA
	
	@property
	def texturetype(self):
		if self == TextureFormat.BC4:
			return texgenpack_texturetype.RGTC1
		if self == TextureFormat.BC5:
			return texgenpack_texturetype.RGTC2
		if self == TextureFormat.BC6H:
			return texgenpack_texturetype.BPTC_FLOAT
		if self == TextureFormat.BC7:
			return texgenpack_texturetype.BPTC
	
	@property
	def pvrPixelFormat(self):
		if self == TextureFormat.YUY2:
			return 17
		if self == TextureFormat.PVRTC_RGB2:
			return 0
		if self == TextureFormat.PVRTC_RGBA2:
			return 1
		if self == TextureFormat.PVRTC_RGB4:
			return 2
		if self == TextureFormat.PVRTC_RGBA4:
			return 3
		if self in [TextureFormat.ETC_RGB4Crunched, TextureFormat.ETC_RGB4_3DS, TextureFormat.ETC_RGB4]:
			return 6
		if self == TextureFormat.ETC2_RGB:
			return 22
		if self == TextureFormat.ETC2_RGBA1:
			return 24
		if self in [TextureFormat.ETC2_RGBA8Crunched, TextureFormat.ETC_RGBA8_3DS, TextureFormat.ETC2_RGBA8]:
			return 23
		if self == TextureFormat.ASTC_RGBA_4x4:
			return 27
		if self == TextureFormat.ASTC_RGBA_5x5:
			return 29
		if self == TextureFormat.ASTC_RGBA_6x6:
			return 31
		if self == TextureFormat.ASTC_RGBA_8x8:
			return 34
		if self == TextureFormat.ASTC_RGBA_10x10:
			return 38
		if self == TextureFormat.ASTC_RGBA_12x12:
			return 40


class texgenpack_texturetype(IntEnum):
	RGTC1 = 0
	RGTC2 = 1
	BPTC_FLOAT = 2
	BPTC = 3


class QFORMAT(IntEnum):
	# General formats
	Q_FORMAT_RGBA_8UI = 1
	Q_FORMAT_RGBA_8I = 2
	Q_FORMAT_RGB5_A1UI = 3
	Q_FORMAT_RGBA_4444 = 4
	Q_FORMAT_RGBA_16UI = 5
	Q_FORMAT_RGBA_16I = 6
	Q_FORMAT_RGBA_32UI = 7
	Q_FORMAT_RGBA_32I = 8
	
	Q_FORMAT_PALETTE_8_RGBA_8888 = 9
	Q_FORMAT_PALETTE_8_RGBA_5551 = 10
	Q_FORMAT_PALETTE_8_RGBA_4444 = 11
	Q_FORMAT_PALETTE_4_RGBA_8888 = 12
	Q_FORMAT_PALETTE_4_RGBA_5551 = 13
	Q_FORMAT_PALETTE_4_RGBA_4444 = 14
	Q_FORMAT_PALETTE_1_RGBA_8888 = 15
	Q_FORMAT_PALETTE_8_RGB_888 = 16
	Q_FORMAT_PALETTE_8_RGB_565 = 17
	Q_FORMAT_PALETTE_4_RGB_888 = 18
	Q_FORMAT_PALETTE_4_RGB_565 = 19
	
	Q_FORMAT_R2_GBA10UI = 20
	Q_FORMAT_RGB10_A2UI = 21
	Q_FORMAT_RGB10_A2I = 22
	Q_FORMAT_RGBA_F = 23
	Q_FORMAT_RGBA_HF = 24
	
	Q_FORMAT_RGB9_E5 = 25  # Last five bits are exponent bits (Read following section in GLES3 spec: "3.8.17 Shared Exponent Texture Color Conversion")
	Q_FORMAT_RGB_8UI = 26
	Q_FORMAT_RGB_8I = 27
	Q_FORMAT_RGB_565 = 28
	Q_FORMAT_RGB_16UI = 29
	Q_FORMAT_RGB_16I = 30
	Q_FORMAT_RGB_32UI = 31
	Q_FORMAT_RGB_32I = 32
	
	Q_FORMAT_RGB_F = 33
	Q_FORMAT_RGB_HF = 34
	Q_FORMAT_RGB_11_11_10_F = 35
	
	Q_FORMAT_RG_F = 36
	Q_FORMAT_RG_HF = 37
	Q_FORMAT_RG_32UI = 38
	Q_FORMAT_RG_32I = 39
	Q_FORMAT_RG_16I = 40
	Q_FORMAT_RG_16UI = 41
	Q_FORMAT_RG_8I = 42
	Q_FORMAT_RG_8UI = 43
	Q_FORMAT_RG_S88 = 44
	
	Q_FORMAT_R_32UI = 45
	Q_FORMAT_R_32I = 46
	Q_FORMAT_R_F = 47
	Q_FORMAT_R_16F = 48
	Q_FORMAT_R_16I = 49
	Q_FORMAT_R_16UI = 50
	Q_FORMAT_R_8I = 51
	Q_FORMAT_R_8UI = 52
	
	Q_FORMAT_LUMINANCE_ALPHA_88 = 53
	Q_FORMAT_LUMINANCE_8 = 54
	Q_FORMAT_ALPHA_8 = 55
	
	Q_FORMAT_LUMINANCE_ALPHA_F = 56
	Q_FORMAT_LUMINANCE_F = 57
	Q_FORMAT_ALPHA_F = 58
	Q_FORMAT_LUMINANCE_ALPHA_HF = 59
	Q_FORMAT_LUMINANCE_HF = 60
	Q_FORMAT_ALPHA_HF = 61
	Q_FORMAT_DEPTH_16 = 62
	Q_FORMAT_DEPTH_24 = 63
	Q_FORMAT_DEPTH_24_STENCIL_8 = 64
	Q_FORMAT_DEPTH_32 = 65
	
	Q_FORMAT_BGR_565 = 66
	Q_FORMAT_BGRA_8888 = 67
	Q_FORMAT_BGRA_5551 = 68
	Q_FORMAT_BGRX_8888 = 69
	Q_FORMAT_BGRA_4444 = 70
	# Compressed formats
	Q_FORMAT_ATITC_RGBA = 71
	Q_FORMAT_ATC_RGBA_EXPLICIT_ALPHA = 72
	Q_FORMAT_ATITC_RGB = 73
	Q_FORMAT_ATC_RGB = 74
	Q_FORMAT_ATC_RGBA_INTERPOLATED_ALPHA = 75
	Q_FORMAT_ETC1_RGB8 = 76
	Q_FORMAT_3DC_X = 77
	Q_FORMAT_3DC_XY = 78
	
	Q_FORMAT_ETC2_RGB8 = 79
	Q_FORMAT_ETC2_RGBA8 = 80
	Q_FORMAT_ETC2_RGB8_PUNCHTHROUGH_ALPHA1 = 81
	Q_FORMAT_ETC2_SRGB8 = 82
	Q_FORMAT_ETC2_SRGB8_ALPHA8 = 83
	Q_FORMAT_ETC2_SRGB8_PUNCHTHROUGH_ALPHA1 = 84
	Q_FORMAT_EAC_R_SIGNED = 85
	Q_FORMAT_EAC_R_UNSIGNED = 86
	Q_FORMAT_EAC_RG_SIGNED = 87
	Q_FORMAT_EAC_RG_UNSIGNED = 88
	
	Q_FORMAT_S3TC_DXT1_RGB = 89
	Q_FORMAT_S3TC_DXT1_RGBA = 90
	Q_FORMAT_S3TC_DXT3_RGBA = 91
	Q_FORMAT_S3TC_DXT5_RGBA = 92
	
	# YUV formats
	Q_FORMAT_AYUV_32 = 93
	Q_FORMAT_I444_24 = 94
	Q_FORMAT_YUYV_16 = 95
	Q_FORMAT_UYVY_16 = 96
	Q_FORMAT_I420_12 = 97
	Q_FORMAT_YV12_12 = 98
	Q_FORMAT_NV21_12 = 99
	Q_FORMAT_NV12_12 = 100
	
	# ASTC Format
	Q_FORMAT_ASTC_8 = 101
	Q_FORMAT_ASTC_16 = 102


class KTXHeader():
	IDENTIFIER = [0xAB, 0x4B, 0x54, 0x58, 0x20, 0x31, 0x31, 0xBB, 0x0D, 0x0A, 0x1A, 0x0A]
	ENDIANESS_LE = {1, 2, 3, 4}
	ENDIANESS = 0x04030201
	glType = 0
	glTypeSize = 1
	glFormat = 0
	pixelDepth = 0
	numberOfArrayElements = 0
	numberOfFaces = 1
	bytesOfKeyValueData = 0
	
	# constants for glInternalFormat
	GL_ETC1_RGB8_OES = 0x8D64
	
	GL_COMPRESSED_RGB_PVRTC_4BPPV1_IMG = 0x8C00
	GL_COMPRESSED_RGB_PVRTC_2BPPV1_IMG = 0x8C01
	GL_COMPRESSED_RGBA_PVRTC_4BPPV1_IMG = 0x8C02
	GL_COMPRESSED_RGBA_PVRTC_2BPPV1_IMG = 0x8C03
	
	GL_ATC_RGB_AMD = 0x8C92
	GL_ATC_RGBA_INTERPOLATED_ALPHA_AMD = 0x87EE
	
	GL_COMPRESSED_RGB8_ETC2 = 0x9274
	GL_COMPRESSED_RGB8_PUNCHTHROUGH_ALPHA1_ETC2 = 0x9276
	GL_COMPRESSED_RGBA8_ETC2_EAC = 0x9278
	GL_COMPRESSED_R11_EAC = 0x9270
	GL_COMPRESSED_SIGNED_R11_EAC = 0x9271
	GL_COMPRESSED_RG11_EAC = 0x9272
	GL_COMPRESSED_SIGNED_RG11_EAC = 0x9273
	
	GL_COMPRESSED_RED_RGTC1 = 0x8DBB
	GL_COMPRESSED_RG_RGTC2 = 0x8DBD
	GL_COMPRESSED_RGB_BPTC_UNSIGNED_FLOAT = 0x8E8F
	GL_COMPRESSED_RGBA_BPTC_UNORM = 0x8E8C
	
	GL_R16F = 0x822D
	GL_RG16F = 0x822F
	GL_RGBA16F = 0x881A
	GL_R32F = 0x822E
	GL_RG32F = 0x8230
	GL_RGBA32F = 0x8814
	
	# constants for glBaseInternalFormat
	GL_RED = 0x1903
	GL_RGB = 0x1907
	GL_RGBA = 0x1908
	GL_RG = 0x8227
