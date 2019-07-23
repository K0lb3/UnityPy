import os, sys, struct, io
import subprocess
import tempfile
from PIL import Image, ImageOps
from .enums import TextureFormat

####	CONSTANTS
EAC_SERIES = {
		41: TextureFormat.EAC_R,
		43: TextureFormat.EAC_RG,
		42: TextureFormat.EAC_R_SIGNED,
		44: TextureFormat.EAC_RG_SIGNED,
}

####	PATHS
Ext_Path = os.path.join(os.path.dirname(os.path.realpath(__file__)), *[os.pardir, 'external'])
sys.path.insert(0, os.path.join(Ext_Path, *['external', 'pythread']))  # required for texgenpack
texgenPath = os.path.join(Ext_Path, *['external', "texgenpack.exe"])  # .ktx images
etcpackPath = os.path.join(Ext_Path, *['external', 'unity-game-resource-unpacker', 'etcpack.exe'])


def processUnimplementedTexture2D(data):
	outputFile = tempfile.TemporaryFile()
	outputFile.close()
	try:
		compressonatorPath = os.path.join(os.environ["COMPRESSONATOR_ROOT"], "CompressonatorCLI.exe")
		if data.format in [35, 36]:  # ATC_RGB4, ATC_RGBA8
			tmpFile = tempfile.NamedTemporaryFile(suffix = ".dds", delete = False)
			writeWithDDSHeader(tmpFile, data, data.format)
			
			process = subprocess.Popen([
					compressonatorPath,
					tmpFile.name,
					outputFile.name + '.png'
			], stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = False)
			output, err = process.communicate()
			
			try:
				idata = open(outputFile.name + '.png', 'rb').read()
				img = Image.open(io.BytesIO(idata))
				tmpFile.close()
				os.unlink(tmpFile.name)
				os.unlink(outputFile.name + '.png')
			except:
				print('Missing ATC converted image %s' % data.name)
		
		
		elif data.format in EAC_SERIES:
			tmpFile = tempfile.NamedTemporaryFile(suffix = ".pkm", delete = False)
			tmpFile.write(getPKMHeader(data.width, data.height, data.format) + data.image_data)
			
			process = subprocess.Popen([
					etcpackPath,
					tmpFile.name,
					tempfile.gettempdir()
			], stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = False)
			output, err = process.communicate()
			# b'		1 file(s) moved.\r\n[malitc-1]Decompressing. Output file: d:\\Projects\\Langrisser\\lib\\UnityAssetExtractor\\SAtemp\\tmpar_tnpw0.ppm\r\n'
			output = output.decode('utf8')
			tempout = output[output.index('file: ') + 6:-2]
			
			idata = open(tempout, 'rb').read()
			img = Image.open(io.BytesIO(idata))
			
			tmpFile.close()
			os.unlink(tmpFile.name)
			os.unlink(tempout)
		
		else:
			raise NotImplementedError
	
	except KeyError:
		print('To Decompress ATC images Compressonator is required.')
		raise KeyError
	
	except Exception as e:
		outputFile.close()
		raise e
	
	if process.returncode != 0:
		print("\nError running command: \n", output)
		return
	
	img = ImageOps.flip(img)
	return img


def writeWithDDSHeader(imgFile, texture2d, format):
	imgFile.write(bytes("DDS ", "ascii"))
	imgFile.write(struct.pack("I", 124))  # dwSize
	imgFile.write(struct.pack("I", 0x1 | 0x2 | 0x4 | 0x1000 | 0x20000 | 0x80000))  # dwFlags
	imgFile.write(struct.pack("I", texture2d.height))  # dwHeight
	imgFile.write(struct.pack("I", texture2d.width))  # dwWidth
	imgFile.write(struct.pack("I", texture2d.complete_image_size))  # dwPitchOrLinearSize
	imgFile.write(struct.pack("I", 0))  # dwDepth
	imgFile.write(struct.pack("I", texture2d.__dict__['_obj']['m_MipCount']))  # dwMipMapCount
	
	for i in range(0, 11):
		imgFile.write(struct.pack("I", 0))  # dwReserved1[11];
	
	# DDS_PIXELFORMAT
	imgFile.write(struct.pack("I", 32))  # dwSize
	imgFile.write(struct.pack("I", 0x1 | 0x4))  # dwFlags
	
	if format == 35:
		imgFile.write(bytes("ATC ", "ascii"))  # dwFourCC
	elif format == 36:
		imgFile.write(bytes("ATCI", "ascii"))  # dwFourCC
	else:
		print("writeWithDDSHeader called with invalid format", format)
		sys.exit()
	
	imgFile.write(struct.pack("I", 0))  # dwRGBBitCount
	imgFile.write(struct.pack("I", 0))  # dwRBitMask
	imgFile.write(struct.pack("I", 0))  # dwGBitMask
	imgFile.write(struct.pack("I", 0))  # dwBBitMask
	imgFile.write(struct.pack("I", 0))  # dwABitMask
	
	imgFile.write(struct.pack("I", 0x8 | 0x400000 | 0x1000))  # dwCaps
	imgFile.write(struct.pack("I", 0))  # dwCaps2
	imgFile.write(struct.pack("I", 0))  # dwCaps3
	imgFile.write(struct.pack("I", 0))  # dwCaps4
	imgFile.write(struct.pack("I", 0))  # dwReversed2
	
	imgFile.write(bytes(texture2d.image_data))


def writeWithKTXHeader(imgFile, texture2d, format):
	imgFile.write(bytearray([0xAB, 0x4B, 0x54, 0x58, 0x20, 0x31, 0x31, 0xBB, 0x0D, 0x0A, 0x1A, 0x0A]))  # identifier
	imgFile.write(struct.pack("I", 0x04030201))  # endianness
	imgFile.write(struct.pack("I", 0))  # glType
	imgFile.write(struct.pack("I", 1))  # glTypeSize
	imgFile.write(struct.pack("I", 0))  # glFormat
	
	if format == 34:  # ETC_RGB4
		imgFile.write(struct.pack("I", 0x8D64))  # glInternalFormat
		imgFile.write(struct.pack("I", 0))  # glBaseInternalFormat
		
		block_size = 64
		block_width = 4
		block_height = 4
	elif format == 47:  # ETC2_RGB8
		imgFile.write(struct.pack("I", 0x9278))  # glInternalFormat
		imgFile.write(struct.pack("I", 0))  # glBaseInternalFormat
		
		block_size = 128
		block_width = 4
		block_height = 4
	else:
		print("writeWithKTXHeader called with invalid format", format)
		sys.exit()
	
	imgFile.write(struct.pack("I", texture2d.width))  # pixelWidth
	imgFile.write(struct.pack("I", texture2d.height))  # pixelHeight
	imgFile.write(struct.pack("I", 0))  # pixelDepth
	imgFile.write(struct.pack("I", 0))  # numberOfArrayElements
	imgFile.write(struct.pack("I", 1))  # numberOfFaces
	imgFile.write(struct.pack("I", texture2d.__dict__['_obj']['m_MipCount']))  # numberOfMipmapLevels
	imgFile.write(struct.pack("I", 0))  # bytesOfKeyValueData
	
	# https://github.com/hglm/texgenpack/blob/master/file.c
	# https://github.com/hglm/texgenpack/blob/master/texture.c
	extended_width = (texture2d.width + block_width - 1)
	extended_height = (texture2d.height + block_height - 1)
	imageSize = int(extended_height / block_height) * int(extended_width / block_width) * int(block_size / 8)
	
	imgFile.write(struct.pack("I", imageSize))
	imgFile.write(bytes(texture2d.image_data))


def getPKMHeader(width, height, tformat):
	header = b"\x50\x4B\x4D\x20"
	
	version = b"20"
	if tformat == TextureFormat.ETC_RGB4:
		version = b"10"
		formatD = 0
	elif tformat == TextureFormat.ETC2_RGB:
		formatD = 1
	elif tformat == TextureFormat.ETC2_RGBA8:
		formatD = 3
	elif tformat == TextureFormat.ETC2_RGBA1:
		formatD = 4
	elif tformat == TextureFormat.EAC_R:
		formatD = 5
	elif tformat == TextureFormat.EAC_RG:
		formatD = 6
	elif tformat == TextureFormat.EAC_R_SIGNED:
		formatD = 7
	elif tformat == TextureFormat.EAC_RG_SIGNED:
		formatD = 8
	else:
		formatD = 0
	
	formatB = formatD.to_bytes(2, byteorder = "big")
	widthB = width.to_bytes(2, byteorder = "big")
	heightB = height.to_bytes(2, byteorder = "big")
	
	return (header + version + formatB + widthB + heightB + widthB + heightB)


'''
		if data.format in [34, 47]:  # ETC_RGB4, ETC2_RGBA8
			tmpFile = tempfile.NamedTemporaryFile(suffix=".ktx", delete=False)
			
			writeWithKTXHeader(tmpFile, data, data.format)

			process = subprocess.Popen([
				texgenPath,
				"--decompress",
				tmpFile.name,
				outputFile.name+'.png'
			], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
			output, err = process.communicate()

			idata = open(outputFile.name+'.png','rb').read()
			img = Image.open(io.BytesIO(idata))
			tmpFile.close()
			os.unlink(tmpFile.name)
			os.unlink(outputFile.name+'.png')


def ConvertToKTX(self, imgFile):
	imgFile.write(bytearray(KTXHeader.IDENTIFIER))
	imgFile.write(struct.pack("I",KTXHeader.ENDIANESS))
	imgFile.write(struct.pack("I", KTXHeader.glType))
	imgFile.write(struct.pack("I", KTXHeader.glTypeSize))
	imgFile.write(struct.pack("I", KTXHeader.glFormat))

	imgFile.write(struct.pack("I", self.format.glInternalFormat))  # glInternalFormat
	imgFile.write(struct.pack("I", self.format.glBaseInternalFormat))  # glInternalFormat

	imgFile.write(struct.pack("I", self.width))  # pixelWidth
	imgFile.write(struct.pack("I", self.height))  # pixelHeight
	imgFile.write(struct.pack("I", KTXHeader.pixelDepth))
	imgFile.write(struct.pack("I", KTXHeader.numberOfArrayElements))
	imgFile.write(struct.pack("I", KTXHeader.numberOfFaces))
	imgFile.write(struct.pack("I", self.__dict__['_obj']['m_MipCount']))  # numberOfMipmapLevels
	imgFile.write(struct.pack("I", KTXHeader.bytesOfKeyValueData))

	# https://github.com/hglm/texgenpack/blob/master/file.c
	# https://github.com/hglm/texgenpack/blob/master/texture.c
	#block_width = 4
	#block_height = 4
	#	block_size = 64
	#	block_size = 128
	#extended_width = (texture2d.width + block_width - 1)
	#extended_height = (texture2d.height + block_height - 1)
	#imageSize = int(extended_height / block_height) * int(extended_width / block_width) * int(block_size / 8)

	imgFile.write(struct.pack("I", len(self.image_data)))	# image_data_size
	imgFile.write(bytes(self.image_data))	# image_data

def PVRToBitmap(pvrdata):
	#bitmap = new Bitmap(m_Width, m_Height)
	rect = (0, 0, m_Width, m_Height)
	var bmd = bitmap.LockBits(rect, ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb)
	var len = Math.Abs(bmd.Stride) * bmd.Height
	if (!DecompressPVR(pvrdata, bmd.Scan0, len))
		bitmap.UnlockBits(bmd)
		bitmap.Dispose()
		return null
	bitmap.UnlockBits(bmd)
	return bitmap

def TextureConverter(self):
	var bitmap = new Bitmap(m_Width, m_Height)
	var rect = new Rectangle(0, 0, m_Width, m_Height)
	var bmd = bitmap.LockBits(rect, ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb)
	var len = Math.Abs(bmd.Stride) * bmd.Height
	var fixAlpha = glBaseInternalFormat == KTXHeader.GL_RED || glBaseInternalFormat == KTXHeader.GL_RG
	if (!Ponvert(image_data, bmd.Scan0, m_Width, m_Height, image_data_size, (int)q_format, len, fixAlpha))
		bitmap.UnlockBits(bmd)
		bitmap.Dispose()
		return null
	bitmap.UnlockBits(bmd)
	return bitmap

def DecompressCRN(self)
	IntPtr uncompressedData
	int uncompressedSize
	bool result
	if (version[0] > 2017 || (version[0] == 2017 && version[1] >= 3) //2017.3 and up
		|| m_TextureFormat == TextureFormat.ETC_RGB4Crunched
		|| m_TextureFormat == TextureFormat.ETC2_RGBA8Crunched)
		result = DecompressUnityCRN(image_data, image_data_size, out uncompressedData, out uncompressedSize)
	else
		result = DecompressCRN(image_data, image_data_size, out uncompressedData, out uncompressedSize)

	if (result)
		var uncompressedBytes = new byte[uncompressedSize]
		Marshal.Copy(uncompressedData, uncompressedBytes, 0, uncompressedSize)
		Marshal.FreeHGlobal(uncompressedData)
		image_data = uncompressedBytes
		image_data_size = uncompressedSize


def Texgenpack(self):
	var bitmap = new Bitmap(m_Width, m_Height)
	var rect = new Rectangle(0, 0, m_Width, m_Height)
	var bmd = bitmap.LockBits(rect, ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb)
	Decode((int)texturetype, image_data, m_Width, m_Height, bmd.Scan0)
	bitmap.UnlockBits(bmd)
	return bitmap'''
