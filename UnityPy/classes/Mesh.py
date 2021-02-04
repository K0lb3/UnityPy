import math

from .AnimationClip import AABB, PackedFloatVector, PackedIntVector
from .NamedObject import NamedObject
from .Texture2D import StreamingInfo
from ..helpers.ResourceReader import get_resource_data
from ..math import Matrix4x4, Vector3
from ..streams import EndianBinaryWriter
from ..enums import GfxPrimitiveType
import struct
from enum import IntEnum
from ..export.MeshExporter import export_mesh


class MinMaxAABB:
    def __init__(self, reader):
        self.m_Min = reader.read_vector3()
        self.m_Max = reader.read_vector3()

    def save(self, writer):
        writer.write_vector3(self.m_Min)
        writer.write_vector3(self.m_Max)


class CompressedMesh:
    def __init__(self, reader):
        version = reader.version
        self.m_Vertices = PackedFloatVector(reader)
        self.m_UV = PackedFloatVector(reader)
        if version[0] < 5:  # 5 down
            self.m_BindPoses = PackedFloatVector(reader)
        self.m_Normals = PackedFloatVector(reader)
        self.m_Tangents = PackedFloatVector(reader)
        self.m_Weights = PackedIntVector(reader)
        self.m_NormalSigns = PackedIntVector(reader)
        self.m_TangentSigns = PackedIntVector(reader)
        if version >= (5,):  # 5 and up
            self.m_FloatColors = PackedFloatVector(reader)
        self.m_BoneIndices = PackedIntVector(reader)
        self.m_Triangles = PackedIntVector(reader)
        if version >= (3, 5):  # 3.5 and up
            if version[0] < 5:  # 5 down
                self.m_Colors = PackedIntVector(reader)
            else:
                self.m_UVInfo = reader.read_u_int()

    def save(self, writer, version):
        self.m_Vertices.save(writer)
        self.m_UV.save(writer)
        if version < (5,):  # 5 down
            self.m_BindPoses.save(writer)
        self.m_Normals.save(writer)
        self.m_Tangents.save(writer)
        self.m_Weights.save(writer)
        self.m_NormalSigns.save(writer)
        self.m_TangentSigns.save(writer)
        if version >= (5,):  # 5 and up
            self.m_FloatColors.save(writer)
        self.m_BoneIndices.save(writer)
        self.m_Triangles.save(writer)
        if version >= (3, 5):  # 3.5 and up
            if version < (5,):  # 5 down
                self.m_Colors.save(writer)
            else:
                writer.write_u_int(m_UVInfo)


class StreamInfo:
    def __init__(self, **kwargs):
        if "reader" in kwargs:
            reader = kwargs["reader"]
            version = reader.version
            self.channelMask = reader.read_u_int()
            self.offset = reader.read_u_int()

            if version < (4,):  # 4.0 down
                self.stride = reader.read_u_int()
                self.align = reader.read_u_int()
            else:
                self.stride = reader.read_byte()
                self.dividerOp = reader.read_byte()
                self.frequency = reader.read_u_short()
        else:
            self.__dict__ = kwargs

    def save(self, writer, version):
        writer.write_u_int(self.channelMask)
        writer.write_u_int(self.offset)

        if version < (4,):  # 4.0 down
            writer.write_u_int(self.stride)
            writer.write_u_int(self.align)
        else:
            writer.write_byte(self.stride)
            writer.write_byte(self.dividerOp)
            writer.write_u_short(self.frequency)


class ChannelInfo:
    def __init__(self, reader):
        self.stream = reader.read_byte()
        self.offset = reader.read_byte()
        self.format = reader.read_byte()
        self.dimension = reader.read_byte()

    def save(self, writer):
        writer.write_byte(self.stream)
        writer.write_byte(self.offset)
        writer.write_byte(self.format)
        writer.write_byte(self.dimension)


class VertexData:
    def __init__(self, reader):
        self.reader = reader
        version = reader.version

        if version < (2018,):  # 2018 down
            self.m_CurrentChannels = reader.read_u_int()

        self.m_VertexCount = reader.read_u_int()

        if version >= (4,):  # 4.0 and up
            m_ChannelsSize = reader.read_int()
            self.m_Channels = [ChannelInfo(reader)
                               for _ in range(m_ChannelsSize)]

        if version < (5,):  # 5.0 down
            if version < (4,):  # 4.0 down
                m_StreamsSize = 4
            else:
                m_StreamsSize = reader.read_int()

            self.m_Streams = [StreamInfo(reader=reader)
                              for _ in range(m_StreamsSize)]

            if version < (4,):  # 4.0 down
                self.GetChannels()
        else:  # 5.0 and up
            self.GetStreams()

        self.m_DataSize = reader.read_bytes(reader.read_int())
        reader.align_stream()

    def save(self, writer: EndianBinaryWriter, version):
        if version < (2018,):  # 2018 down
            writer.write_u_int(self.m_CurrentChannels)

        writer.write_u_int(self.m_VertexCount)

        if version >= (4,):  # 4.0 and up
            writer.write_int(len(self.m_Channels))
            for ch in self.m_Channels:
                ch.save(writer)

        if (4,) <= version[:2] < (5,):  # 4.0 and up to 5.0
            writer.write_int(len(m_Streams))

            for stream in self.m_Streams:
                stream.save(writer=writer, varsion=version)

            if version < (4,):  # 4.0 down
                raise Exception("Unsupported version")
        else:  # 5.0 and up
            # for stream in self.m_Streams:
            #    stream.save(writer)
            pass

        writer.write_int(len(self.m_DataSize))
        writer.write_bytes(self.m_DataSize)
        writer.align_stream()

    def GetStreams(self):
        streamCount = 1 + (
            0 if not self.m_Channels else max(
                [x.stream for x in self.m_Channels])
        )
        self.m_Streams = {}
        offset = 0
        for s in range(streamCount):
            chnMask = 0
            stride = 0
            for chn, m_Channel in enumerate(self.m_Channels):
                if m_Channel.stream == s:
                    if m_Channel.dimension > 0:
                        chnMask |= 1 << chn  # Shift 1UInt << chn
                    stride += m_Channel.dimension * MeshHelper.GetFormatSize(
                        self.reader.version,
                        m_Channel.format
                    )
            self.m_Streams[s] = StreamInfo(
                channelMask=chnMask,
                offset=offset,
                stride=stride,
                dividerOp=0,
                frequency=0,
            )
            offset += self.m_VertexCount * stride
            # static size_t align_streamSize (size_t size) { return (size + (kVertexStreamAlign-1)) & ~(kVertexStreamAlign-1)
            offset = (offset + (16 - 1)) & ~(
                16 - 1
            )  # (offset + (16u - 1u)) & ~(16u - 1u);

    def GetChannels(self):
        self.m_Channels = []  # ChannelInfo[6]
        for i in range(6):
            self.m_Channels.append(ChannelInfo(self.reader))
        for s, m_Stream in enumerate(self.m_Streams):
            channelMask = bytearray(m_Stream.channelMask)  # BitArray
            offset = 0
            for i in range(6):
                if channelMask[i]:
                    m_Channel = self.m_Channels[i]
                    m_Channel.stream = s
                    m_Channel.offset = offset
                    if i in [0, 1]:
                        # 0 - kShaderChannelVertex
                        # 1 - kShaderChannelNormal
                        m_Channel.format = 0  # kChannelFormatFloat
                        m_Channel.dimension = 3
                    elif i == 2:  # kShaderChannelColor
                        m_Channel.format = 2  # kChannelFormatColor
                        m_Channel.dimension = 4
                    elif i in [3, 4]:
                        # 3 - kShaderChannelTexCoord0
                        # 4 - kShaderChannelTexCoord1
                        m_Channel.format = 0  # kChannelFormatFloat
                        m_Channel.dimension = 2
                    elif i == 5:  # kShaderChannelTangent
                        m_Channel.format = 0  # kChannelFormatFloat
                        m_Channel.dimension = 4
                    offset += m_Channel.dimension * MeshHelper.GetChannelFormatSize(
                        m_Channel.format
                    )

    def FixChannel(self):
        if any(
            [x.dimension > 4 for x in self.m_Channels]
        ):  # m_Channels.FirstOrDefault(x => x.dimension > 4) != null: #
            fixStream = max(
                [x.stream for x in self.m_Channels]
            )  # m_Channels.Max(x => x.stream)
            fixChannels = [
                x for x in self.m_Channels if x.dimension > 0 and x.stream == fixStream
            ]
            stride = 0
            for i, curChannel in enumerate(fixChannels):
                preChannel = fixChannels[i - 1]
                offset = curChannel.offset - preChannel.offset
                preChannel.dimension = offset / MeshHelper.GetChannelFormatSize(
                    preChannel.format
                )
                stride += offset
            # Fix Last
            m_Channel = fixChannels[-1]
            streamSize = len(self.m_DataSize) - \
                self.m_Streams[fixStream].offset
            totalStride = streamSize / self.m_VertexCount
            channelStride = totalStride - stride
            m_Channel.dimension = channelStride / MeshHelper.GetChannelFormatSize(
                m_Channel.format
            )
            self.GetStreams()


class BoneWeights4:
    def __init__(self, reader=None):
        if reader:
            self.weight = reader.read_float_array(4)
            self.boneIndex = reader.read_int_array(4)
        else:
            self.weight = [0.0] * 4
            self.boneIndex = [0] * 4

    def save(self, writer):
        writer.write_float_array(self.weight)
        writer.write_int_array(self.boneIndex)


class BlendShapeVertex:
    def __init__(self, reader):
        self.vertex = reader.read_vector3()
        self.normal = reader.read_vector3()
        self.tangent = reader.read_vector3()
        self.index = reader.read_u_int()


class MeshBlendShape:
    def __init__(self, reader):
        version = reader.version

        if version < (4, 3):  # 4.3 down
            self.name = reader.read_aligned_string()
        self.firstVertex = reader.read_u_int()
        self.vertexCount = reader.read_u_int()
        if version < (4, 3):  # 4.3 down
            self.aabbMinDelta = reader.read_vector3()
            self.aabbMaxDelta = reader.read_vector3()
        self.hasNormals = reader.read_boolean()
        self.hasTangents = reader.read_boolean()
        if version >= (4, 3):  # 4.3 and up
            reader.align_stream()


class MeshBlendShapeChannel:
    def __init__(self, reader):
        self.name = reader.read_aligned_string()
        self.nameHash = reader.read_u_int()
        self.frameIndex = reader.read_int()
        self.frameCount = reader.read_int()


class BlendShapeData:
    def __init__(self, reader):
        version = reader.version

        if version >= (4, 3):  # 4.3 and up
            numVerts = reader.read_int()
            self.vertices = [BlendShapeVertex(reader) for _ in range(numVerts)]

            numShapes = reader.read_int()
            self.shapes = [MeshBlendShape(reader) for _ in range(numShapes)]

            numChannels = reader.read_int()
            self.channels = [MeshBlendShapeChannel(
                reader) for _ in range(numChannels)]
            self.fullWeights = reader.read_float_array()
        else:
            m_ShapesSize = reader.read_int()
            self.m_Shapes = [MeshBlendShape(reader)
                             for _ in range(m_ShapesSize)]
            reader.align_stream()
            m_ShapeVerticesSize = reader.read_int()
            self.m_ShapeVertices = [
                BlendShapeVertex(reader) for _ in range(m_ShapeVerticesSize)
            ]


class SubMesh:
    def __init__(self, reader):
        version = reader.version
        self.firstByte = reader.read_u_int()
        self.indexCount = reader.read_u_int()
        self.topology = GfxPrimitiveType(reader.read_int())

        if version < (4,):  # 4.0 down
            self.triangleCount = reader.read_u_int()

        if version >= (2017, 3):  # 2017.3 and up
            self.baseVertex = reader.read_u_int()

        if version >= (3,):  # 3.0 and up
            self.firstVertex = reader.read_u_int()
            self.vertexCount = reader.read_u_int()
            self.localAABB = AABB(reader)

    def save(self, writer, version):
        writer.write_u_int(self.firstByte)
        writer.write_u_int(self.indexCount)
        writer.write_int(self.topology)

        if version < (4,):  # 4.0 down
            writer.write_u_int(self.triangleCount)

        if version >= (2017, 3):  # 2017.3 and up
            writer.write_u_int(self.baseVertex)

        if version >= (3,):  # 3.0 and up
            writer.write_u_int(self.firstVertex)
            writer.write_u_int(self.vertexCount)
            self.localAABB.save(writer)


class Mesh(NamedObject):
    m_StreamData: None

    def export(self):
        return export_mesh(self)

    def __init__(self, reader):
        super().__init__(reader=reader)
        version = reader.version

        self.m_Use16BitIndices = True
        self.m_Indices = []
        self.m_BindPose = []
        self.m_BoneNameHashes = []
        self.m_Vertices = []
        self.m_Skin = []
        self.m_Normals = []
        self.m_Colors = []
        self.m_UV0 = []
        self.m_UV1 = []
        self.m_UV2 = []
        self.m_UV3 = []
        self.m_UV4 = []
        self.m_UV5 = []
        self.m_UV6 = []
        self.m_UV7 = []
        self.m_Tangents = []

        if version < (3, 5):  # 3.5 down
            self.m_Use16BitIndices = reader.read_int() > 0

        if version[:2] <= (2, 5):  # 2.5 and down
            m_IndexBuffer_size = reader.read_int()

            if self.m_Use16BitIndices:
                self.m_IndexBuffer = [
                    reader.read_u_short()
                    for _ in range(math.ceil(m_IndexBuffer_size / 2))
                ]
                reader.align_stream()
            else:
                self.m_IndexBuffer = reader.read_u_int_array(
                    math.ceil(m_IndexBuffer_size / 4))

        m_SubMeshesSize = reader.read_int()
        self.m_SubMeshes = [SubMesh(reader) for _ in range(m_SubMeshesSize)]

        if version >= (4, 1):  # 4.1 and up
            self.m_Shapes = BlendShapeData(reader)

        if version >= (4, 3):  # 4.3 and up
            self.m_BindPose = reader.read_matrix_array()
            self.m_BoneNameHashes = reader.read_u_int_array()
            self.m_RootBoneNameHash = reader.read_u_int()

        if version >= (2, 6):  # 2.6.0 and up
            if version >= (2019,):  # 2019 and up
                m_BonesAABBSize = reader.read_int()
                self.m_BonesAABB = [MinMaxAABB(reader)
                                    for _ in range(m_BonesAABBSize)]
                self.m_VariableBoneCountWeights = reader.read_u_int_array()

            self.m_MeshCompression = reader.read_byte()
            if version >= (4,):  #
                if version < (5,):  #
                    self.m_StreamCompression = reader.read_byte()
                self.m_IsReadable = reader.read_boolean()
                self.m_KeepVertices = reader.read_boolean()
                self.m_KeepIndices = reader.read_boolean()
            reader.align_stream()

            # Unity fixed it in 2017.3.1p1 and later versions
            if (
                version >= (2017, 4)  # 2017.4
                # fixed after 2017.3.1px
                or version[:3] == (2017, 3, 1) and self.build_type.IsPatch
                # 2017.3.xfx with no compression
                or version[:2] == (2017, 3) and self.m_MeshCompression == 0
            ):
                self.m_IndexFormat = reader.read_int()
                self.m_Use16BitIndices = self.m_IndexFormat == 0

            m_IndexBuffer_size = reader.read_int()
            if self.m_Use16BitIndices:
                self.m_IndexBuffer = [
                    reader.read_u_short() for _ in range(math.ceil(m_IndexBuffer_size / 2))
                ]
                reader.align_stream()
            else:
                self.m_IndexBuffer = reader.read_u_int_array(
                    math.ceil(m_IndexBuffer_size / 4))

        if version < (3, 5):  # 3.4.2 and earlier
            self.m_VertexCount = reader.read_int()
            self.m_Vertices = reader.read_float_array(
                m_VertexCount * 3)  # Vector3

            self.m_SkinSize = reader.read_int()
            self.m_Skin = [BoneWeights4(reader) for _ in range(m_SkinSize)]

            self.m_BindPose = reader.read_matrix_array()
            self.m_UV0 = reader.read_float_array(
                reader.read_int() * 2)  # Vector2
            self.m_UV1 = reader.read_float_array(
                reader.read_int() * 2)  # Vector2

            if version[:2] <= (2, 5):  # 2.5 and down
                m_TangentSpace_size = reader.read_int()
                self.m_Normals = [0] * (m_TangentSpace_size * 3)
                self.m_Tangets = [0] * (m_TangentSpace_size * 4)
                for v in range(m_TangentSpace_size):
                    self.m_Normals[v * 3] = reader.read_float()
                    self.m_Normals[v * 3 + 1] = reader.read_float()
                    self.m_Normals[v * 3 + 2] = reader.read_float()
                    self.m_Tangents[v * 3] = reader.read_float()
                    self.m_Tangents[v * 3 + 1] = reader.read_float()
                    self.m_Tangents[v * 3 + 2] = reader.read_float()
                    # handedness
                    self.m_Tangents[v * 3 + 3] = reader.read_float()
            else:  # 2.6.0 and later
                self.m_Tangents = reader.read_float_array(
                    reader.read_int() * 4
                )  # Vector4
                self.m_Normals = reader.read_float_array(
                    reader.read_int() * 3
                )  # Vector3
        else:
            if version[:2] < (2018, 2):  # 2018.2 down
                m_SkinSize = reader.read_int()
                self.m_Skin = [BoneWeights4(reader) for _ in range(m_SkinSize)]

            if version[:2] <= (4, 2):  # 4.2 and down
                self.m_BindPose = reader.read_matrix_array()

            self.m_VertexData = VertexData(reader)

        if version >= (2, 6):  # 2.6.0 and later
            self.m_CompressedMesh = CompressedMesh(reader)

        self.m_LocalAABB = AABB(reader)

        if version[:2] <= (3, 4):  # 3.4.2 and earlier
            m_Colors_size = reader.read_int()
            self.mColors = [
                reader.read_byte()/0xFF
                for _ in range(m_Colors_size * 4)
            ]

            m_CollisionTriangles_size = reader.read_int()
            reader.Position += m_CollisionTriangles_size * 4  # UInt32 indices
            m_CollisionVertexCount = reader.read_int()

        self.m_MeshUsageFlags = reader.read_int()
        if version >= (5,):  # 5.0 and up
            self.m_BakedConvexCollisionMesh = reader.read_bytes(
                reader.read_int()
            )
            reader.align_stream()
            self.m_BakedTriangleCollisionMesh = reader.read_bytes(
                reader.read_int())
            reader.align_stream()

        if version >= (2018, 2):  # 2018.2 and up
            self.m_MeshMetrics = [reader.read_float(), reader.read_float()]

        if version >= (2018, 3):  # 2018.3 and up
            reader.align_stream()
            self.m_StreamData = StreamingInfo(reader, version)

        try:
            self.ProcessData()
        except:
            pass

    def ProcessData(self):
        if self.m_StreamData and self.m_StreamData.path:
            if self.m_VertexData.m_VertexCount > 0:  #
                self.m_VertexData.m_DataSize = get_resource_data(
                    self.m_StreamData.path,
                    self.assets_file,
                    self.m_StreamData.offset,
                    self.m_StreamData.size,
                )
        # Fix channel after 2018.3
        version = self.version
        if version >= (2018, 3):  #
            self.m_VertexData.FixChannel()
        if version >= (3, 5):  # 3.5 and up
            self.ReadVertexData()

        if version >= (2, 6):  # 2.6.0 and later
            self.DecompressCompressedMesh()

        self.GetTriangles()

    def ReadVertexData(self):
        version = self.version
        m_VertexData = self.m_VertexData
        m_VertexCount = self.m_VertexCount = m_VertexData.m_VertexCount

        for chn, m_Channel in enumerate(m_VertexData.m_Channels):
            if m_Channel.dimension > 0:
                m_Stream = m_VertexData.m_Streams[m_Channel.stream]
                channelMask = bin(m_Stream.channelMask)[::-1]
                if channelMask[chn] == "1":
                    if version[0] < 2018 and chn == 2 and m_Channel.format == 2:
                        m_Channel.dimension = 4

                    componentByteSize = MeshHelper.GetFormatSize(
                        version, m_Channel.format)
                    componentBytes = bytearray(
                        m_VertexCount * m_Channel.dimension * componentByteSize)
                    for v in range(m_VertexCount):
                        vertexOffset = m_Stream.offset + m_Channel.offset + m_Stream.stride * v
                        for d in range(m_Channel.dimension):
                            componentOffsetSrc = vertexOffset + componentByteSize * d  # src offset
                            componentOffsetDst = componentByteSize * \
                                (v * m_Channel.dimension + d)  # dst offst

                            buff = m_VertexData.m_DataSize[componentOffsetSrc:
                                                           componentOffsetSrc + componentByteSize]
                            if self.reader.endian == "<" and componentByteSize > 1:  # swap bytes
                                buff = buff[::-1]

                            componentBytes[componentOffsetDst: componentOffsetDst +
                                           componentByteSize] = buff
                            #Buffer.BlockCopy(m_VertexData.m_DataSize, componentOffset, componentBytes, componentByteSize * (v * m_Channel.dimension + d), componentByteSize);
                            # (Array src, int srcOffset, Array dst, int dstOffset, int count);

                    if MeshHelper.IsIntFormat(version, m_Channel.format):
                        componentsIntArray = MeshHelper.BytesToIntArray(
                            componentBytes, componentByteSize)
                    else:
                        componentsFloatArray = MeshHelper.BytesToFloatArray(
                            componentBytes, componentByteSize)

                    if version[0] >= 2018:
                        if chn == 0: 	# kShaderChannelVertex
                            self.m_Vertices = componentsFloatArray
                        elif chn == 1: 	# kShaderChannelNormal
                            self.m_Normals = componentsFloatArray
                        elif chn == 2: 	# kShaderChannelTangent
                            self.m_Tangents = componentsFloatArray
                        elif chn == 3: 	# kShaderChannelColor
                            self.m_Colors = componentsFloatArray
                        elif chn == 4: 	# kShaderChannelTexCoord0
                            self.m_UV0 = componentsFloatArray
                        elif chn == 5: 	# kShaderChannelTexCoord1
                            self.m_UV1 = componentsFloatArray
                        elif chn == 6: 	# kShaderChannelTexCoord2
                            self.m_UV2 = componentsFloatArray
                        elif chn == 7: 	# kShaderChannelTexCoord3
                            self.m_UV3 = componentsFloatArray
                        elif chn == 8: 	# kShaderChannelTexCoord4
                            self.m_UV4 = componentsFloatArray
                        elif chn == 9: 	# kShaderChannelTexCoord5
                            self.m_UV5 = componentsFloatArray
                        elif chn == 10: 	# kShaderChannelTexCoord6
                            self.m_UV6 = componentsFloatArray
                        elif chn == 11: 	# kShaderChannelTexCoord7
                            self.m_UV7 = componentsFloatArray
                        # 2018.2 and up
                        elif chn == 12:  # kShaderChannelBlendWeight
                            if not self.m_Skin:
                                self.InitMSkin()
                            for i in range(m_VertexCount):
                                for j in range(m_Channel.dimension):
                                    self.m_Skin[i].weight[j] = componentsFloatArray[i *
                                                                                    m_Channel.dimension + j]
                        elif chn == 13:  # kShaderChannelBlendIndices
                            if not self.m_Skin:
                                self.InitMSkin()
                            for i in range(m_VertexCount):
                                for j in range(m_Channel.dimension):
                                    self.m_Skin[i].boneIndex[j] = componentsIntArray[i *
                                                                                     m_Channel.dimension + j]
                    else:
                        if chn == 0: 	# kShaderChannelVertex
                            self.m_Vertices = componentsFloatArray
                        elif chn == 1: 	# kShaderChannelNormal
                            self.m_Normals = componentsFloatArray
                        elif chn == 2: 	# kShaderChannelColor
                            self.m_Colors = componentsFloatArray
                        elif chn == 3: 	# kShaderChannelTexCoord0
                            self.m_UV0 = componentsFloatArray
                        elif chn == 4: 	# kShaderChannelTexCoord1
                            self.m_UV1 = componentsFloatArray
                        elif chn == 5:
                            if version[0] >= 5:  # kShaderChannelTexCoord2
                                self.m_UV2 = componentsFloatArray
                            else:  # kShaderChannelTangent
                                self.m_Tangents = componentsFloatArray
                        elif chn == 6: 	# kShaderChannelTexCoord3
                            self.m_UV3 = componentsFloatArray
                        elif chn == 7: 	# kShaderChannelTangent
                            self.m_Tangents = componentsFloatArray

    def DecompressCompressedMesh(self):
        # Vertex
        version = self.version
        m_CompressedMesh = self.m_CompressedMesh
        if m_CompressedMesh.m_Vertices.m_NumItems > 0:
            self.m_VertexCount = m_CompressedMesh.m_Vertices.m_NumItems / 3
            self.m_Vertices = m_CompressedMesh.m_Vertices.UnpackFloats(3, 4)
        m_VertexCount = self.m_VertexCount
        # UV
        if m_CompressedMesh.m_UV.m_NumItems > 0:  #
            self.m_UV0 = m_CompressedMesh.m_UV.UnpackFloats(
                2, 4, 0, m_VertexCount)
            if m_CompressedMesh.m_UV.m_NumItems >= m_VertexCount * 4:  #
                self.m_UV1 = m_CompressedMesh.m_UV.UnpackFloats(
                    2, 4, m_VertexCount * 2, m_VertexCount
                )
            if m_CompressedMesh.m_UV.m_NumItems >= m_VertexCount * 6:  #
                self.m_UV2 = m_CompressedMesh.m_UV.UnpackFloats(
                    2, 4, m_VertexCount * 4, m_VertexCount
                )
            if m_CompressedMesh.m_UV.m_NumItems >= m_VertexCount * 8:  #
                self.m_UV3 = m_CompressedMesh.m_UV.UnpackFloats(
                    2, 4, m_VertexCount * 6, m_VertexCount
                )
        # BindPose
        if version < (5,):  # 5.0 down
            if m_CompressedMesh.m_BindPoses.m_NumItems > 0:  #
                m_BindPoses_Unpacked = m_CompressedMesh.m_BindPoses.UnpackFloats(
                    16, 4 * 16
                )
                self.m_BindPose = [
                    Matrix4x4(m_BindPoses_Unpacked[i: i + 16])
                    for i in range(0, m_CompressedMesh.m_BindPoses.m_NumItems, 16)
                ]

        # Normal
        if m_CompressedMesh.m_Normals.m_NumItems > 0:
            normalData = m_CompressedMesh.m_Normals.UnpackFloats(2, 4 * 2)
            signs = m_CompressedMesh.m_NormalSigns.UnpackInts()
            self.m_Normals = []  # float[m_CompressedMesh.m_Normals.m_NumItems / 2 * 3]
            for i in range(0, math.ceil(m_CompressedMesh.m_Normals.m_NumItems / 2)):
                x = normalData[i + 0]
                y = normalData[i + 1]
                zsqr = 1 - x * x - y * y
                if zsqr >= 0:
                    z = math.sqrt(zsqr)
                else:
                    z = 0
                    normal = Vector3(x, y, z)
                    normal.normalize()
                    x = normal.X
                    y = normal.Y
                    z = normal.Z
                if signs[i] == 0:
                    z = -z
                self.m_Normals.extend([x, y, z])
        # Tangent
        if m_CompressedMesh.m_Tangents.m_NumItems > 0:
            tangentData = m_CompressedMesh.m_Tangents.UnpackFloats(2, 4 * 2)
            signs = m_CompressedMesh.m_TangentSigns.UnpackInts()
            self.m_Tangents = (
                []
            )  # float[m_CompressedMesh.m_Tangents.m_NumItems / 2 * 4]
            for i in range(0, math.ceil(m_CompressedMesh.m_Tangents.m_NumItems / 2)):
                x = tangentData[i * 2 + 0]
                y = tangentData[i * 2 + 1]
                zsqr = 1 - x * x - y * y
                if zsqr >= 0:
                    z = math.sqrt(zsqr)
                else:
                    z = 0
                    vector3f = Vector3(x, y, z)
                    vector3f.Normalize()
                    x = vector3f.X
                    y = vector3f.Y
                    z = vector3f.Z
                if signs[i * 2 + 0] == 0:  #
                    z = -z
                w = 1.0 if signs[i * 2 + 1] > 0 else -1.0
                self.m_Tangents.extend([x, y, z, w])

        # FloatColor
        if version >= (5,):  # 5.0 and up
            if m_CompressedMesh.m_FloatColors.m_NumItems > 0:  #
                self.m_Colors = m_CompressedMesh.m_FloatColors.UnpackFloats(
                    1, 4)
        # Skin
        if m_CompressedMesh.m_Weights.m_NumItems > 0:
            weights = m_CompressedMesh.m_Weights.UnpackInts()
            boneIndices = m_CompressedMesh.m_BoneIndices.UnpackInts()

            self.InitMSkin()

            bonePos = 0
            boneIndexPos = 0
            j = 0
            sum = 0

            for i in range(m_CompressedMesh.m_Weights.m_NumItems):
                # read bone index and weight.
                self.m_Skin[bonePos].weight[j] = weights[i] / 31.0
                self.m_Skin[bonePos].boneIndex[j] = boneIndices[boneIndexPos]
                boneIndexPos += 1
                j += 1
                sum += weights[i]

                # the weights add up to one. fill the rest for this vertex with zero, and continue with next one.
                if sum >= 31:  #
                    while j < 4:
                        self.m_Skin[bonePos].weight[j] = 0
                        self.m_Skin[bonePos].boneIndex[j] = 0
                        bonePos += 1
                        j += 1
                    j = 0
                    sum = 0
                # we read three weights, but they don't add up to one. calculate the fourth one, and read
                # missing bone index. continue with next vertex.
                elif j == 3:  #
                    self.m_Skin[bonePos].weight[j] = (31 - sum) / 31.0
                    self.m_Skin[bonePos].boneIndex[j] = boneIndices[boneIndexPos]
                    boneIndexPos += 1
                    bonePos += 1
                    j = 0
                    sum = 0

        # IndexBuffer
        if m_CompressedMesh.m_Triangles.m_NumItems > 0:  #
            self.m_IndexBuffer = m_CompressedMesh.m_Triangles.UnpackUInts()
        # Color
        if (
            hasattr(m_CompressedMesh, "m_Colors")
            and m_CompressedMesh.m_Colors.m_NumItems > 0
        ):
            m_CompressedMesh.m_Colors.m_NumItems *= 4
            m_CompressedMesh.m_Colors.m_BitSize /= 4
            tempColors = m_CompressedMesh.m_Colors.UnpackInts()
            self.m_Colors = [color / 255 for color in tempColors]

    def GetTriangles(self):
        m_IndexBuffer = self.m_IndexBuffer
        m_Indices = self.m_Indices

        for m_SubMesh in self.m_SubMeshes:
            firstIndex = m_SubMesh.firstByte // 2
            if not self.m_Use16BitIndices:
                firstIndex /= 2

            indexCount = m_SubMesh.indexCount
            topology = m_SubMesh.topology
            if topology == GfxPrimitiveType.kPrimitiveTriangles:
                m_Indices.extend(
                    m_IndexBuffer[firstIndex: firstIndex + indexCount*3])

            elif self.version[0] < 4 or topology == GfxPrimitiveType.kPrimitiveTriangleStrip:
                # de-stripify :
                triIndex = 0
                for i in range(indexCount-2):
                    a, b, c = m_IndexBuffer[firstIndex + i: firstIndex + i + 3]

                    # skip degenerates
                    if (a == b or a == c or b == c):
                        continue

                    # do the winding flip-flop of strips :
                    m_Indices.extend(
                        [b, a, c] if ((i & 1) == 1) else [a, b, c]
                    )
                    triIndex += 3
                # fix indexCount
                m_SubMesh.indexCount = triIndex

            elif topology == GfxPrimitiveType.kPrimitiveQuads:
                for q in range(0, indexCount, 4):
                    m_Indices.extend([
                        m_IndexBuffer[firstIndex + q],
                        m_IndexBuffer[firstIndex + q + 1],
                        m_IndexBuffer[firstIndex + q + 2],
                        m_IndexBuffer[firstIndex + q],
                        m_IndexBuffer[firstIndex + q + 2],
                        m_IndexBuffer[firstIndex + q + 3]
                    ])
                # fix indexCount
                m_SubMesh.indexCount = indexCount // 2 * 3

            else:
                raise NotImplementedError(
                    "Failed getting triangles. Submesh topology is lines or points.")

    def InitMSkin(self):
        self.m_Skin = [BoneWeights4() for _ in range(self.m_VertexCount)]


class MeshHelper:
    @staticmethod
    def GetFormatSize(version, format: int) -> int:
        if version[0] < 2017:
            if format == VertexChannelFormat.kChannelFormatFloat:
                return 4
            elif format == VertexChannelFormat.kChannelFormatFloat16:
                return 2
            elif format == VertexChannelFormat.kChannelFormatColor:  # in 4.x is size 4
                return 1
            elif format == VertexChannelFormat.kChannelFormatByte:
                return 1
            elif format == VertexChannelFormat.kChannelFormatUInt32:  # in 5.x
                return 4
        elif version[0] < 2019:
            if format == VertexFormat.kVertexFormatFloat:
                return 4
            elif format == VertexFormat.kVertexFormatFloat16:
                return 2
            elif format == VertexFormat.kVertexFormatColor:
                return 1
            elif format == VertexFormat.kVertexFormatUNorm8:
                return 1
            elif format == VertexFormat.kVertexFormatSNorm8:
                return 1
            elif format == VertexFormat.kVertexFormatUNorm16:
                return 2
            elif format == VertexFormat.kVertexFormatSNorm16:
                return 2
            elif format == VertexFormat.kVertexFormatUInt8:
                return 1
            elif format == VertexFormat.kVertexFormatSInt8:
                return 1
            elif format == VertexFormat.kVertexFormatUInt16:
                return 2
            elif format == VertexFormat.kVertexFormatSInt16:
                return 2
            elif format == VertexFormat.kVertexFormatUInt32:
                return 4
            elif format == VertexFormat.kVertexFormatSInt32:
                return 4
        else:
            if format == VertexFormatV2019.kVertexFormatFloat:
                return 4
            elif format == VertexFormatV2019.kVertexFormatFloat16:
                return 2
            elif format == VertexFormatV2019.kVertexFormatUNorm8:
                return 1
            elif format == VertexFormatV2019.kVertexFormatSNorm8:
                return 1
            elif format == VertexFormatV2019.kVertexFormatUNorm16:
                return 2
            elif format == VertexFormatV2019.kVertexFormatSNorm16:
                return 2
            elif format == VertexFormatV2019.kVertexFormatUInt8:
                return 1
            elif format == VertexFormatV2019.kVertexFormatSInt8:
                return 1
            elif format == VertexFormatV2019.kVertexFormatUInt16:
                return 2
            elif format == VertexFormatV2019.kVertexFormatSInt16:
                return 2
            elif format == VertexFormatV2019.kVertexFormatUInt32:
                return 4
            elif format == VertexFormatV2019.kVertexFormatSInt32:
                return 4
        raise ValueError(format)

    @staticmethod
    def IsIntFormat(version, format: int) -> bool:
        if version[0] < 2017:
            return format == 4
        elif version[0] < 2019:
            return format >= 7
        else:
            return format >= 6

    @staticmethod
    def BytesToFloatArray(inputBytes, size):
        return [
            inputBytes[i]/255.0 if size == 1 else
            struct.unpack(">e", inputBytes[i * 2: i * 2 + 2])[0] if size == 2 else
            struct.unpack(">f", inputBytes[i * 4: i * 4 + 4])[0] if size == 4 else
            0
            for i in range(len(inputBytes)//size)
        ]

    @staticmethod
    def BytesToIntArray(inputBytes, size):
        return [
            int.from_bytes(inputBytes[i: i + size],
                           byteorder="big", signed=True)
            for i in range(0, len(inputBytes), size)
        ]


class VertexChannelFormat(IntEnum):
    kChannelFormatFloat = 0
    kChannelFormatFloat16 = 1
    kChannelFormatColor = 2
    kChannelFormatByte = 3
    kChannelFormatUInt32 = 4


class VertexFormat(IntEnum):
    kVertexFormatFloat = 0
    kVertexFormatFloat16 = 1
    kVertexFormatColor = 2
    kVertexFormatUNorm8 = 3
    kVertexFormatSNorm8 = 4
    kVertexFormatUNorm16 = 5
    kVertexFormatSNorm16 = 6
    kVertexFormatUInt8 = 7
    kVertexFormatSInt8 = 8
    kVertexFormatUInt16 = 9
    kVertexFormatSInt16 = 10
    kVertexFormatUInt32 = 11
    kVertexFormatSInt32 = 12


class VertexFormatV2019(IntEnum):
    kVertexFormatFloat = 0
    kVertexFormatFloat16 = 1
    kVertexFormatUNorm8 = 2
    kVertexFormatSNorm8 = 3
    kVertexFormatUNorm16 = 4
    kVertexFormatSNorm16 = 5
    kVertexFormatUInt8 = 6
    kVertexFormatSInt8 = 7
    kVertexFormatUInt16 = 8
    kVertexFormatSInt16 = 9
    kVertexFormatUInt32 = 10
    kVertexFormatSInt32 = 11
