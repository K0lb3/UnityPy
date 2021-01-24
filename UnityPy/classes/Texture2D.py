from .Texture import Texture
from ..enums import TextureFormat
from ..export import Texture2DConverter
from ..helpers.ResourceReader import get_resource_data
from ..streams import EndianBinaryWriter


class Texture2D(Texture):
    @property
    def image(self):
        return Texture2DConverter.get_image_from_texture2d(self)

    @image.setter
    def image(self, img):
        # img is PIL.Image / image path / opened file
        # overwrite original image data with the RGB(A) image data and sets the correct new format
        img_data,tex_format = Texture2DConverter.image_to_texture(self, img)
        if img is None:
            raise Exception("No image provided")

        self.image_data = img_data
        self.m_CompleteImageSize = len(self.image_data)
        self.m_TextureFormat = tex_format
        
        self.m_StreamData.path = ""
        self.m_StreamData.offset = 0
        self.m_StreamData.size = 0

    def __init__(self, reader):
        super().__init__(reader=reader)
        version = self.version

        self.m_Width = reader.read_int()
        self.m_Height = reader.read_int()
        self.m_CompleteImageSize = reader.read_int()
        if version >= (2020,):  # 2020.1 and up
            self.mips_stripped = reader.read_int()
        self.m_TextureFormat = TextureFormat(reader.read_int())
        if version[:2] < (5, 2):  # 5.2 down
            self.m_MipMap = reader.read_boolean()
        else:
            self.m_MipCount = reader.read_int()

        if version >= (2, 6):  # 2.6 and up
            self.m_IsReadable = reader.read_boolean()  # 2.6 and up
        if version >= (2020,):  # 2020.1 and up
            self.is_pre_processed = reader.read_boolean()
        if version >= (2019, 3):  # 2019.3 and up
            self.ignore_master_texture_limit = reader.read_boolean()
        if (3,) <= version[:2] <= (5, 4):  # 3.0 - 5.4
            self.m_ReadAllowed = reader.read_boolean()
        if version >= (2018, 2):  # 2018.2 and up
            self.m_streaming_mipmaps = reader.read_boolean()

        reader.align_stream()
        if version >= (2018, 2):  # 2018.2 and up
            self.m_StreamingMipmapsPriority = reader.read_int()
        self.m_ImageCount = reader.read_int()
        self.m_TextureDimension = reader.read_int()
        self.m_TextureSettings = GLTextureSettings(reader, version)
        if version >= (3,):  # 3.0 and up
            self.m_LightmapFormat = reader.read_int()
        if version >= (3, 5):  # 3.5 and up
            self.m_ColorSpace = reader.read_int()

        image_data_size = reader.read_int()
        self.image_data = b""
        if image_data_size == 0 and version >= (5, 3):  # 5.3 and up
            self.m_StreamData = StreamingInfo(reader, version)
            if self.m_StreamData.size:
                self.image_data = get_resource_data(
                    self.m_StreamData.path,
                    self.assets_file,
                    self.m_StreamData.offset,
                    self.m_StreamData.size,
                )
        else:
            self.image_data = reader.read_bytes(image_data_size)

    def save(self, writer: EndianBinaryWriter = None):
        if writer is None:
            writer = EndianBinaryWriter(endian=self.reader.endian)
        version = self.version

        super().save(writer)
        writer.write_int(self.m_Width)
        writer.write_int(self.m_Height)
        writer.write_int(self.m_CompleteImageSize)
        if version >= (2020,):  # 2020.1 and up
            writer.write_int(self.mips_stripped)
        writer.write_int(self.m_TextureFormat.value)
        if version < (5, 2):  # 5.2 down
            writer.write_boolean(self.m_MipMap)
        else:
            writer.write_int(self.m_MipCount)
        writer.write_boolean(self.m_IsReadable)  # 2.6 and up
        if version >= (2020,):  # 2020.1 and up
            writer.write_boolean(self.is_pre_processed )
        if version >= (2019, 3):  # 2019.3 and up
            writer.write_boolean(self.ignore_master_texture_limit)
        if (3,) <= version[:2] <= (5, 4):  # 3.0 - 5.4
            writer.write_boolean(self.m_ReadAllowed)  # 3.0 - 5.4
        if version >= (2018, 2):  # 2018.2 and up
            writer.write_boolean(self.m_streaming_mipmaps)

        writer.align_stream()
        if version >= (2018, 2):  # 2018.2 and up
            writer.write_int(self.m_StreamingMipmapsPriority)
        writer.write_int(self.m_ImageCount)
        writer.write_int(self.m_TextureDimension)
        self.m_TextureSettings.save(writer, version)
        if version >= (3,):  # 3.0 and up
            writer.write_int(self.m_LightmapFormat)
        if version >= (3, 5):  # 3.5 and up
            writer.write_int(self.m_ColorSpace)

        writer.write_int(len(self.image_data))
        writer.write_bytes(self.image_data)

        self.m_StreamData.save(writer, version)

        self.set_raw_data(writer.bytes)


class StreamingInfo:
    offset: int = 0
    size: int = 0
    path: str = ""

    def __init__(self, reader, version):
        if version >= (2020,):  # 2020.1 and up
            self.offset = reader.read_u_long()
        else:
            self.offset = reader.read_u_int()
        self.size = reader.read_u_int()
        self.path = reader.read_aligned_string()

    def save(self, writer, version):
        if version >= (2020,):  # 2020.1 and up
            writer.write_u_long(self.offset)
        else:
            writer.write_u_int(self.offset)
        writer.write_int(self.size)
        writer.write_aligned_string(self.path)


class GLTextureSettings:
    def __init__(self, reader, version):
        self.m_FilterMode = reader.read_int()
        self.m_Aniso = reader.read_int()
        self.m_MipBias = reader.read_float()
        self.m_WrapMode = reader.read_int()  # m_WrapU
        if version >= (2017,):  # 2017.x and up
            self.m_WrapV = reader.read_int()
            self.m_WrapW = reader.read_int()

    def save(self, writer, version):
        writer.write_int(self.m_FilterMode)
        writer.write_int(self.m_Aniso)
        writer.write_float(self.m_MipBias)
        writer.write_int(self.m_WrapMode)  # m_WrapU
        if version >= (2017,):  # 2017.x and up
            writer.write_int(self.m_WrapV)
            writer.write_int(self.m_WrapW)
