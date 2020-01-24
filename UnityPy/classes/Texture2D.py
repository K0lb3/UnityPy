from .Texture import Texture
from ..ResourceReader import ResourceReader
from ..enums import TextureFormat
from ..export import Texture2DConverter


class Texture2D(Texture):

	@property
	def image(self):
		return Texture2DConverter.get_image_from_texture2d(self)

	def __init__(self, reader):
		super().__init__(reader=reader)
		version = self.version
		self.m_Width = reader.read_int()
		self.m_Height = reader.read_int()
		self.m_CompleteImageSize = reader.read_int()
		self.m_TextureFormat = TextureFormat(reader.read_int())
		if version[0] < 5 or (version[0] == 5 and version[1] < 2):  # 5.2 down
			self.m_MipMap = reader.read_boolean()
		else:
			self.m_MipCount = reader.read_int()
		self.m_IsReadable = reader.read_boolean()  # 2.6.0 and up
		self.m_ReadAllowed = reader.read_boolean()  # 3.0.0 - 5.4
		# bool m_StreamingMipmaps 2018.2 and up
		reader.align_stream()
		if version[0] > 2018 or (version[0] == 2018 and version[1] >= 2):  # 2018.2 and up
			self.m_StreamingMipmapsPriority = reader.read_int()
		self.m_ImageCount = reader.read_int()
		self.m_TextureDimension = reader.read_int()
		self.m_TextureSettings = GLTextureSettings(reader)
		if version[0] >= 3:  # 3.0 and up
			self.m_LightmapFormat = reader.read_int()
		if version[0] > 3 or (version[0] == 3 and version[1] >= 5):  # 3.5.0 and up
			self.m_ColorSpace = reader.read_int()
		image_data_size = reader.read_int()
		if image_data_size == 0 and ((version[0] == 5 and version[1] >= 3) or version[0] > 5):  # 5.3.0 and up
			m_StreamData = StreamingInfo(reader)

		if 'm_StreamData' in locals() and m_StreamData.path:
			resource_reader = ResourceReader(m_StreamData.path, self.assets_file, m_StreamData.offset,
											 m_StreamData.size)
		else:
			resource_reader = ResourceReader(reader, reader.Position, image_data_size)
		self.image_data = resource_reader.get_data()


class StreamingInfo:
	offset: int = 0
	size: int = 0
	path: str = ""

	def __init__(self, reader):
		self.offset = reader.read_u_int()
		self.size = reader.read_u_int()
		self.path = reader.read_aligned_string()


class GLTextureSettings:
	def __init__(self, reader):
		version = reader.version

		self.m_FilterMode = reader.read_int()
		self.m_Aniso = reader.read_int()
		self.m_MipBias = reader.read_float()
		if version[0] >= 2017:  # 2017.x and up
			self.m_WrapMode = reader.read_int()  # m_WrapU
			self.m_WrapV = reader.read_int()
			self.m_WrapW = reader.read_int()
		else:
			self.m_WrapMode = reader.read_int()
