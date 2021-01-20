from enum import IntEnum

from .Mesh import BoneWeights4, SubMesh, VertexData
from .NamedObject import NamedObject
from .PPtr import PPtr, save_ptr
from ..export import SpriteHelper
from ..enums import SpriteMeshType
from ..streams import EndianBinaryWriter


class Sprite(NamedObject):
    @property
    def image(self):
        return SpriteHelper.get_image_from_sprite(self)

    def __init__(self, reader):
        super().__init__(reader=reader)
        version = self.version

        self.m_Rect = reader.read_rectangle_f()
        self.m_Offset = reader.read_vector2()
        if version >= (4, 5):  # 4.5 and up
            self.m_Border = reader.read_vector4()

        self.m_PixelsToUnits = reader.read_float()
        if version >= (5, 4, 2) or (
            version >= (5, 4, 1, 3) and self.build_type.IsPatch
        ):  # 5.4.1p3 and up
            self.m_Pivot = reader.read_vector2()

        self.m_Extrude = reader.read_u_int()
        if version >= (5, 3):  # 5.3 and up
            self.m_IsPolygon = reader.read_boolean()
            reader.align_stream()

        if version >= (2017,):  # 2017 and up
            first = reader.read_bytes(16)  # GUID
            second = reader.read_long()
            self.m_RenderDataKey = (first, second)
            self.m_AtlasTags = reader.read_string_array()
            self.m_SpriteAtlas = PPtr(reader)  # SpriteAtlas

        self.m_RD = SpriteRenderData(reader)

        if version >= (2017,):  # 2017 and up
            m_PhysicsShapeSize = reader.read_int()
            self.m_PhysicsShape = [
                reader.read_vector2_array() for _ in range(m_PhysicsShapeSize)
            ]

        if version >= (2018,):  # 2018 and up
            m_BonesSize = reader.read_int()
            self.m_Bones = [
                reader.read_vector2_array() for _ in range(m_BonesSize)
            ]

    def save(self, writer: EndianBinaryWriter = None):
        if writer is None:
            writer = EndianBinaryWriter(endian=self.reader.endian)
        version = self.version

        super().save(writer)
        writer.write_rectangle_f(self.m_Rect)
        writer.write_vector2(self.m_Offset)
        if version >= (4, 5):  # 4.5 and up
            writer.write_vector4(self.m_Border)

        writer.write_float(self.m_PixelsToUnits)
        if version >= (5, 4, 2) or (
            version >= (5, 4, 1, 3) and self.build_type.IsPatch
        ):  # 5.4.1p3 and up
            writer.write_vector2(self.m_Pivot)

        writer.write_u_int(self.m_Extrude)
        if version >= (5, 3):  # 5.3 and up
            writer.write_boolean(self.m_IsPolygon)
            writer.align_stream()

        if version >= (2017,):  # 2017 and up
            writer.write_bytes(self.m_RenderDataKey[0])  # GUID
            writer.write_long(self.m_RenderDataKey[1])
            writer.write_string_array(self.m_AtlasTags)
            self.m_SpriteAtlas.save(writer)  # SpriteAtlas

        self.m_RD.save(writer, version)

        if version >= (2017,):  # 2017 and up
            writer.write_int(len(self.m_PhysicsShape))
            for phys in self.m_PhysicsShape:
                writer.write_vector2_array(phys)

        if version >= (2018,):  # 2018 and up
            writer.write_int(len(self.m_Bones))
            for bone in self.m_Bones:
                writer.write_vector2_array(bone)

        self.set_raw_data(writer.bytes)


class SecondarySpriteTexture:
    def __init__(self, reader):
        self.texture = PPtr(reader)  # Texture2D
        self.name = reader.read_string_to_null()

    def save(self, writer):
        self.texture.save(writer)
        writer.write_string_to_null(self.name)


class SpritePackingRotation(IntEnum):
    kSPRNone = (0,)
    kSPRFlipHorizontal = (1,)
    kSPRFlipVertical = (2,)
    kSPRRotate180 = (3,)
    kSPRRotate90 = 4


class SpritePackingMode(IntEnum):
    kSPMTight = (0,)
    kSPMRectangle = 1


class SpriteSettings:
    def __init__(self, reader):
        self.value = reader.read_u_int()

    @property
    def value(self):
        return self.m_settingsRaw

    @value.setter
    def value(self, _value):
        self.m_settingsRaw = _value

        self.packed = self.m_settingsRaw & 1  # 1
        self.packingMode = SpritePackingMode((self.m_settingsRaw >> 1) & 1)  # 1
        self.packingRotation = SpritePackingRotation((self.m_settingsRaw >> 2) & 0xF)  # 4
        self.meshType = SpriteMeshType((self.m_settingsRaw >> 6) & 1)  # 1
        # rest of the bits are reserved

    def save(self, writer):
        writer.write_u_int(self.m_settingsRaw)


class SpriteVertex:
    def __init__(self, reader):
        version = reader.version

        self.pos = reader.read_vector3()
        if version[:2] <= (4, 3):  # 4.3 and down
            self.uv = reader.read_vector2()

    def save(self, writer, version):
        writer.write_vector3(self.pos)
        if version[:2] <= (4, 3):  # 4.3 and down
            writer.write__vector2(self.uv)

class SpriteRenderData:
    def __init__(self, reader):
        version = reader.version

        self.texture = PPtr(reader)  # Texture2D
        if version >= (5, 2):  # 5.2 and up
            self.alphaTexture = PPtr(reader)  # Texture2D

        if version >= (2019,):  # 2019 and up
            secondaryTexturesSize = reader.read_int()
            self.secondaryTextures = [
                SecondarySpriteTexture(reader) for _ in range(secondaryTexturesSize)
            ]

        if version >= (5, 6):  # 5.6 and up
            SubMeshesSize = reader.read_int()
            self.m_SubMeshes = [SubMesh(reader) for _ in range(SubMeshesSize)]
            IndexBufferSize = reader.read_int()
            self.m_IndexBuffer = reader.read_bytes(IndexBufferSize)
            reader.align_stream()
            self.m_VertexData = VertexData(reader)
        else:
            verticesSize = reader.read_int()
            self.vertices = [SpriteVertex(reader) for _ in range(verticesSize)]
            self.indices = reader.read_u_short_array()
            reader.align_stream()

        if version >= (2018,):  # 2018 and up
            self.m_Bindpose = reader.read_matrix_array()
            if version < (2018, 2):  # 2018.2 down
                self.m_SourceSkinSize = reader.read_int()
                self.m_SourceSkin = [BoneWeights4(reader)]

        self.textureRect = reader.read_rectangle_f()
        self.textureRectOffset = reader.read_vector2()
        if version >= (5, 6):  # 5.6 and up
            self.atlasRectOffset = reader.read_vector2()

        self.settingsRaw = SpriteSettings(reader)
        if version >= (4, 5):  # 4.5 and up
            self.uvTransform = reader.read_vector4()

        if version >= (2017,):  # 2017 and up
            self.downscaleMultiplier = reader.read_float()

    def save(self, writer, version):
        self.texture.save(writer)  # Texture2D
        if version >= (5, 2):  # 5.2 and up
            self.alphaTexture.save(writer)  # Texture2D

        if version >= (2019,):  # 2019 and up
            writer.write_int(len(self.secondaryTextures))
            for tex in self.secondaryTextures:
                tex.save(writer)

        if version >= (5, 6):  # 5.6 and up
            writer.write_int(len(self.m_SubMeshes))
            for mesh in self.m_SubMeshes:
                mesh.save(writer, version)
            writer.write_int(len(self.m_IndexBuffer))
            writer.write_bytes(self.m_IndexBuffer)
            writer.align_stream()
            self.m_VertexData.save(writer, version)
        else:
            writer.write_int(len(self.vertices))
            for vertex in self.vertices:
                vertex.save(writer, version)
            writer.write_u_short_array(self.indices)
            writer.align_stream()

        if version >= (2018,):  # 2018 and up
            writer.write_matrix_array(self.m_Bindpose)
            if version < (2018, 2):  # 2018.2 down
                writer.write_int(self.m_SourceSkinSize)
                self.m_SourceSkin[0].save(writer)

        writer.write_rectangle_f(self.textureRect)
        writer.write_vector2(self.textureRectOffset)
        if version >= (5, 6):  # 5.6 and up
            writer.write_vector2(self.atlasRectOffset)

        self.settingsRaw.save(writer)
        if version >= (4, 5):  # 4.5 and up
            writer.write_vector4(self.uvTransform)

        if version >= (2017,):  # 2017 and up
            writer.write_float(self.downscaleMultiplier)
