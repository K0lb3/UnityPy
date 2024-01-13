from .Texture import Texture
from ..enums import TextureFormat
from ..export import Texture2DConverter
from ..helpers.ResourceReader import get_resource_data
from ..streams import EndianBinaryWriter
from PIL import Image
from io import BufferedIOBase, RawIOBase, IOBase


class Texture2D(Texture):
    @property
    def image(self):
        return Texture2DConverter.get_image_from_texture2d(self)

    @image.setter
    def image(self, img):
        # img is PIL.Image / image path / opened file
        # overwrite original image data with the RGB(A) image data and sets the correct new format
        if img is None:
            raise Exception("No image provided")

        if (
            isinstance(img, str)
            or isinstance(img, BufferedIOBase)
            or isinstance(img, RawIOBase)
            or isinstance(img, IOBase)
        ):
            img = Image.open(img)

        img_data, tex_format = Texture2DConverter.image_to_texture2d(
            img, self.m_TextureFormat
        )

        # disable mipmaps as we don't store them ourselves by default
        if self.version[:2] < (5, 2):  # 5.2 down
            self.m_MipMap = False
        else:
            self.m_MipCount = 1

        self.image_data = img_data
        self.m_MipCount = 1
        # width * height * channel count
        self.m_CompleteImageSize = len(
            img_data
        )  # img.width * img.height * len(img.getbands())
        self.m_TextureFormat = tex_format

    @property
    def image_data(self):
        if not self._image_data and self.m_StreamData is not None:
            self._image_data = get_resource_data(
                self.m_StreamData.path,
                self.assets_file,
                self.m_StreamData.offset,
                self.m_StreamData.size,
            )
        return self._image_data

    def reset_streamdata(self):
        if not self.m_StreamData:
            return
        self.m_StreamData.offset = 0
        self.m_StreamData.size = 0
        self.m_StreamData.path = ""

    @image_data.setter
    def image_data(self, data: bytes):
        self._image_data = data
        # ignore writing to cab for now until it's more stable
        # if self.version >= (5, 3) and self.m_StreamData.path:
        #     cab = self.assets_file.get_writeable_cab()
        #     if cab:
        #         self.m_StreamData.offset = cab.Position
        #         cab.write(data)
        #         self.m_StreamData.size = len(data)
        #         self.m_StreamData.path = cab.path
        #     else:
        #         self.reset_streamdata()
        self.reset_streamdata()

    def set_image(
        self,
        img,
        target_format: TextureFormat = None,
        in_cab: bool = False,
        mipmap_count: int = 1,
    ):
        if img is None:
            raise Exception("No image provided")
        if not target_format:
            target_format = self.m_TextureFormat

        img_data, tex_format = Texture2DConverter.image_to_texture2d(img, target_format)
        if mipmap_count > 1:
            width = self.m_Width
            height = self.m_Height
            re_img = img
            for i in range(mipmap_count - 1):
                width //= 2
                height //= 2
                if width < 4 or height < 4:
                    mipmap_count = i + 1
                    break
                re_img = re_img.resize((width, height), Image.BICUBIC)
                img_data += Texture2DConverter.image_to_texture2d(
                    re_img, target_format
                )[0]

        if self.version[:2] < (5, 2):  # 5.2 down
            self.m_MipMap = mipmap_count > 1
        else:
            self.m_MipCount = mipmap_count

        if in_cab:
            self.image_data = img_data
        else:
            self._image_data = img_data
            self.reset_streamdata()

        # width * height * channel count
        self.m_CompleteImageSize = len(
            img_data
        )  # img.width * img.height * len(img.getbands())
        self.m_TextureFormat = tex_format

    def __init__(self, reader):
        super().__init__(reader=reader)
        version = self.version

        self.m_Width = reader.read_int()
        self.m_Height = reader.read_int()
        self.m_CompleteImageSize = reader.read_int()
        if version >= (2020, 1):  # 2020.1 and up
            self.m_MipsStripped = reader.read_int()
        self.m_TextureFormat = TextureFormat(reader.read_int())
        if version < (5, 2):  # 3.4.0 - 5.1.5f1
            self.m_MipMap = reader.read_boolean()
        else:  # 5.2.0f2 and up
            self.m_MipCount = reader.read_int()

        if version >= (2, 6):  # 2.6 and up
            self.m_IsReadable = reader.read_boolean()  # 2.6 and up
        if version >= (2020,):  # 2020.1 and up
            self.m_IsPreProcessed = reader.read_boolean()
        if (2019, 3) <= version < (2022, 2, 0):  # 2019.3.0f6 - 2022.2.0a18
            self.m_IgnoreMasterTextureLimit = reader.read_boolean()
        if version >= (2022, 2, 0):  # 2022.2.0f1 and up
            self.m_IgnoreMipmapLimit = reader.read_boolean()
            self.m_MipmapLimitGroupName = reader.read_aligned_string()
        if (3,) <= version[:2] <= (5, 4):  # 3.0 - 5.4
            self.m_ReadAllowed = reader.read_boolean()
        if version >= (2018, 2):  # 2018.2 and up
            self.m_StreamingMipmaps = reader.read_boolean()

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
        if version >= (2020, 2):  # 2020.2 and up
            self.m_PlatformBlob = reader.read_byte_array()
            reader.align_stream()

        image_data_size = reader.read_int()
        self._image_data = b""

        if image_data_size != 0:
            self._image_data = reader.read_bytes(image_data_size)

        self.m_StreamData = None
        if version >= (5, 3):  # 5.3 and up
            # always read the StreamingInfo for resaving
            self.m_StreamData = StreamingInfo(reader, version)
            # don't read the data directly,
            # as we don't want the parser break if the file is missing

    def save(self, writer: EndianBinaryWriter = None):
        if writer is None:
            writer = EndianBinaryWriter(endian=self.reader.endian)
        version = self.version

        super().save(writer)
        writer.write_int(self.m_Width)
        writer.write_int(self.m_Height)
        writer.write_int(self.m_CompleteImageSize)
        if version >= (2020,):  # 2020.1 and up
            writer.write_int(self.m_MipsStripped)
        writer.write_int(self.m_TextureFormat.value)
        if version < (5, 2):  # 5.2 down
            writer.write_boolean(self.m_MipMap)
        else:
            writer.write_int(self.m_MipCount)

        if version >= (2, 6):  # 2.6 and up
            writer.write_boolean(self.m_IsReadable)  # 2.6 and up
        if version >= (2020,):  # 2020.1 and up
            writer.write_boolean(self.m_IsPreProcessed)
        if (2019, 3) <= version < (2022, 2, 0):  # 2019.3.0f6 - 2022.2.0a18
            writer.write_boolean(self.m_IgnoreMasterTextureLimit)
        if version >= (2022, 2, 0):  # 2022.2.0f1 and up
            writer.write_boolean(self.m_IgnoreMipmapLimit)
            writer.write_aligned_string(self.m_MipmapLimitGroupName)
        if (3,) <= version[:2] <= (5, 4):  # 3.0 - 5.4
            writer.write_boolean(self.m_ReadAllowed)  # 3.0 - 5.4
        if version >= (2018, 2):  # 2018.2 and up
            writer.write_boolean(self.m_StreamingMipmaps)

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
        if version >= (2020, 2):  # 2020.2 and up
            writer.write_byte_array(self.m_PlatformBlob)
            writer.align_stream()

        if version[:2] < (5, 3):
            # version without m_StreamData
            writer.write_int(len(self.image_data))
            writer.write_bytes(self.image_data)
        else:
            # decide if m_StreamData is used
            if self.m_StreamData.path:
                # used -> don't save the image_data
                writer.write_int(0)
            else:
                writer.write_int(len(self.image_data))
                writer.write_bytes(self.image_data)

            self.m_StreamData.save(writer, version)

        self.set_raw_data(writer.bytes)


class StreamingInfo:
    offset: int
    size: int
    path: str

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
