from __future__ import annotations

import math
import struct
from typing import TYPE_CHECKING, List, Optional, Tuple, Union, cast

from ..classes.generated import (
    ChannelInfo,
    Mesh,
    SpriteRenderData,
    StreamInfo,
    Vector2f,
    Vector3f,
    Vector4f,
)
from ..enums.MeshTopology import MeshTopology
from ..enums.VertexFormat import (
    VERTEX_CHANNEL_FORMAT_STRUCT_TYPE_MAP,
    VERTEX_FORMAT_2017_STRUCT_TYPE_MAP,
    VERTEX_FORMAT_STRUCT_TYPE_MAP,
    VertexChannelFormat,
    VertexFormat,
    VertexFormat2017,
)
from .PackedBitVector import unpack_floats, unpack_ints
from .ResourceReader import get_resource_data

try:
    from UnityPy import UnityPyBoost
except ImportError:
    UnityPyBoost = None

Tuple2f = Tuple[float, float]
Tuple3f = Tuple[float, float, float]
Tuple4f = Tuple[float, float, float, float]


def vector_list_to_tuples(
    data: Union[List[Vector2f], List[Vector3f], List[Vector4f]],
) -> List[tuple]:
    if isinstance(data[0], Vector2f):
        return [(v.x, v.y) for v in data]
    elif isinstance(data[0], Vector3f):
        if TYPE_CHECKING:
            data = cast(List[Vector3f], data)
        return [(v.x, v.y, v.z) for v in data]
    elif isinstance(data[0], Vector4f):
        if TYPE_CHECKING:
            data = cast(List[Vector4f], data)
        return [(v.x, v.y, v.z, v.w) for v in data]
    else:
        raise ValueError("Unknown vector type")


def lists_to_tuples(data: List[list]) -> List[tuple]:
    return [tuple(v) for v in data]


def zeros(m: int, n: int) -> List[list]:
    return [[0] * n for _ in range(m)]


def normalize(*vector: float) -> Tuple[float, ...]:
    length = math.sqrt(sum(v**2 for v in vector))
    if length > 0.00001:
        inv_norm = 1.0 / length
        return tuple(v * inv_norm for v in vector)
    return (0,) * len(vector)


class MeshHandler:
    src: Union[Mesh, SpriteRenderData]
    endianess: str = "<"
    version: Tuple[int, int, int, int]
    m_VertexCount: int = 0
    m_Vertices: Optional[List[Tuple3f]] = None
    # normals can be stored as Tuple4f,
    # in such cases the 4th dimension is always 0 and can be discarded
    m_Normals: Optional[Union[List[Tuple3f], List[Tuple4f]]] = None
    m_Colors: Optional[List[Tuple4f]] = None
    m_UV0: Optional[List[Tuple2f]] = None
    m_UV1: Optional[List[Tuple2f]] = None
    m_UV2: Optional[List[Tuple2f]] = None
    m_UV3: Optional[List[Tuple2f]] = None
    m_UV4: Optional[List[Tuple2f]] = None
    m_UV5: Optional[List[Tuple2f]] = None
    m_UV6: Optional[List[Tuple2f]] = None
    m_UV7: Optional[List[Tuple2f]] = None
    m_Tangents: Optional[List[Tuple4f]] = None
    m_BoneIndices: Optional[List[Tuple[int, int, int, int]]] = None
    m_BoneWeights: Optional[List[Tuple4f]] = None
    m_IndexBuffer: Optional[List[int]] = None
    m_Use16BitIndices: bool = True

    def __init__(
        self,
        src: Union[Mesh, SpriteRenderData],
        version: Optional[Tuple[int, int, int, int]] = None,
        endianess: str = "<",
    ):
        self.src = src
        self.endianess = endianess
        if version is not None:
            self.version = version
        elif not isinstance(src, SpriteRenderData) and src.object_reader is not None:
            self.version = src.object_reader.version
        else:
            raise ValueError("No version provided and no object reader found")

    def process(self):
        mesh = self.src
        vertex_data = mesh.m_VertexData
        assert vertex_data is not None

        m_Channels: list[ChannelInfo]
        m_Streams: list[StreamInfo]

        if self.version[0] < 4:
            assert (
                vertex_data.m_Streams_0_ is not None
                and vertex_data.m_Streams_1_ is not None
                and vertex_data.m_Streams_2_ is not None
                and vertex_data.m_Streams_3_ is not None
            )
            m_Streams = [
                vertex_data.m_Streams_0_,
                vertex_data.m_Streams_1_,
                vertex_data.m_Streams_2_,
                vertex_data.m_Streams_3_,
            ]
            assert all(stream is not None for stream in m_Streams)
            m_Channels = self.get_channels(m_Streams)
        elif self.version[0] == 4:
            assert vertex_data.m_Streams is not None and vertex_data.m_Channels is not None
            m_Streams = vertex_data.m_Streams
            m_Channels = vertex_data.m_Channels
        else:
            assert vertex_data.m_Channels is not None
            m_Channels = vertex_data.m_Channels
            m_Streams = self.get_streams(m_Channels, vertex_data.m_VertexCount)

        if (
            isinstance(mesh, Mesh) and mesh.m_StreamData and mesh.m_StreamData.path
            # and mesh.m_VertexData
            # and mesh.m_VertexData.m_VertexCount
        ):
            stream_data = mesh.m_StreamData
            assert mesh.object_reader, "No object reader assigned to the input Mesh!"
            data = get_resource_data(
                stream_data.path,
                mesh.object_reader.assets_file,
                stream_data.offset,
                stream_data.size,
            )
            vertex_data.m_DataSize = data

        # try to copy data directly from mesh
        if isinstance(mesh, Mesh):
            if mesh.m_Use16BitIndices is not None:
                self.m_Use16BitIndices = bool(mesh.m_Use16BitIndices)
            elif (
                (self.version >= (2017, 4))
                or
                # version == (2017, 3, 1) & patched - px string
                (self.version[:2] == (2017, 3) and mesh.m_MeshCompression == 0)
            ):
                self.m_Use16BitIndices = mesh.m_IndexFormat == 0
            self.copy_from_mesh()
        elif isinstance(mesh, SpriteRenderData):
            self.copy_from_spriterenderdata()
        else:
            raise ValueError(f"Unknown mesh type {type(mesh)}")

        if self.m_IndexBuffer:
            raw_indices = bytes(self.m_IndexBuffer)
            if self.m_Use16BitIndices:
                char = "H"
                index_size = 2
            else:
                char = "I"
                index_size = 4

            self.m_IndexBuffer = cast(
                List[int],
                struct.unpack(f"<{len(raw_indices) // index_size}{char}", raw_indices),
            )

        if self.version >= (3, 5):
            self.read_vertex_data(m_Channels, m_Streams)

        if isinstance(mesh, Mesh) and self.version >= (2, 6):
            self.decompress_compressed_mesh()

        if self.m_VertexCount == 0 and self.m_Vertices:
            self.m_VertexCount = len(self.m_Vertices)

    def copy_from_mesh(self):
        """Copy data from mesh to handler if it's not already set."""
        mesh = self.src
        if TYPE_CHECKING:
            assert isinstance(mesh, Mesh)

        if self.m_IndexBuffer is None and mesh.m_IndexBuffer:
            self.m_IndexBuffer = mesh.m_IndexBuffer

        if self.m_Vertices is None and mesh.m_Vertices:
            self.m_Vertices = vector_list_to_tuples(mesh.m_Vertices)

        if self.m_Normals is None and mesh.m_Normals:
            self.m_Normals = vector_list_to_tuples(mesh.m_Normals)

        if self.m_Tangents is None and mesh.m_Tangents:
            self.m_Tangents = vector_list_to_tuples(mesh.m_Tangents)

        if self.m_UV0 is None and mesh.m_UV:
            self.m_UV0 = vector_list_to_tuples(mesh.m_UV)

        if self.m_UV1 is None and mesh.m_UV1:
            self.m_UV1 = vector_list_to_tuples(mesh.m_UV1)

        if self.m_Colors is None and mesh.m_Colors:
            self.m_Colors = [
                (color.r / 255.0, color.g / 255.0, color.b / 255.0, color.a / 255.0) for color in mesh.m_Colors
            ]

        if self.m_BoneWeights is None and mesh.m_Skin:
            # BoneInfluence == BoneWeight in terms of usage in UnityPy due to int simplification
            self.m_BoneIndices = [
                (skin.boneIndex_0_, skin.boneIndex_1_, skin.boneIndex_2_, skin.boneIndex_3_) for skin in mesh.m_Skin
            ]
            self.m_BoneWeights = [
                (skin.weight_0_, skin.weight_1_, skin.weight_2_, skin.weight_3_) for skin in mesh.m_Skin
            ]

    def copy_from_spriterenderdata(self):
        rd = self.src
        if TYPE_CHECKING:
            assert isinstance(rd, SpriteRenderData)

        if self.m_IndexBuffer is None:
            if rd.m_IndexBuffer:
                self.m_IndexBuffer = rd.m_IndexBuffer
            elif rd.indices:
                self.m_IndexBuffer = rd.indices

        if self.m_Vertices is None and rd.vertices:
            vertices = rd.vertices
            self.m_Vertices = [(v.pos.x, v.pos.y, v.pos.z) for v in vertices]

            if vertices[0].uv is not None:
                self.m_UV0 = [(v.uv.x, v.uv.y) for v in vertices]  # type: ignore

        # if self.m_BindPose is None and rd.m_BindPose:
        #     self.m_BindPose = rd.m_BindPose

    def get_streams(self, m_Channels: list[ChannelInfo], m_VertexCount: int) -> list[StreamInfo]:
        streamCount = 1 + max(x.stream for x in m_Channels)
        m_Streams: list[StreamInfo] = []
        offset = 0
        for s in range(streamCount):
            chnMask = 0
            stride = 0
            for chn, m_Channel in enumerate(m_Channels):
                if m_Channel.stream == s:
                    if m_Channel.dimension > 0:
                        chnMask |= 1 << chn
                        component_size = self.get_channel_component_size(m_Channel)
                        stride += (m_Channel.dimension & 0xF) * component_size

            m_Streams.append(
                StreamInfo(
                    channelMask=chnMask,
                    offset=offset,
                    stride=stride,
                    dividerOp=0,
                    frequency=0,
                )
            )
            offset += m_VertexCount * stride
            offset = (offset + (16 - 1)) & ~(16 - 1)
        return m_Streams

    def get_channels(self, m_Streams: list[StreamInfo]) -> list[ChannelInfo]:
        m_Channels = [
            ChannelInfo(
                dimension=0,
                format=0,
                offset=0,
                stream=0,
            )
            for _ in range(6)
        ]
        for s, m_Stream in enumerate(m_Streams):
            channelMask = m_Stream.channelMask  # uint
            offset = 0
            for i in range(6):
                if channelMask & (1 << i):
                    m_Channel = m_Channels[i]
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

                    component_size = self.get_channel_component_size(m_Channel)
                    offset += m_Channel.dimension * component_size

        return m_Channels

    def read_vertex_data(self, m_Channels: list[ChannelInfo], m_Streams: list[StreamInfo]) -> None:
        m_VertexData = self.src.m_VertexData
        if m_VertexData is None:
            return

        # could be empty for fully compressed meshes
        # in that case data will be read from CompressedMesh via decompress_compressed_mesh
        # also avoids a crash in UnityPyBoost.unpack_vertexdata with empty data
        if m_VertexData.m_VertexCount == 0 or not m_VertexData.m_DataSize:
            return

        self.m_VertexCount = m_VertexCount = m_VertexData.m_VertexCount
        # m_VertexDataRaw = m_VertexData.m_DataSize

        for chn, m_Channel in enumerate(m_Channels):
            if m_Channel.dimension == 0:
                continue

            m_Stream = m_Streams[m_Channel.stream]
            # m_StreamData = m_VertexDataRaw[
            #     m_Stream.offset : m_Stream.offset + m_VertexCount * m_Stream.stride
            # ]

            channelMask = bin(m_Stream.channelMask)[::-1]
            if channelMask[chn] == "1":
                if (
                    self.version[0] < 2018 and chn == 2 and m_Channel.format == 2
                ):  # kShaderChannelColor && kChannelFormatColor
                    # new instance to not modify the original
                    m_Channel = ChannelInfo(
                        dimension=4,
                        format=2,
                        offset=m_Channel.offset,
                        stream=m_Channel.stream,
                    )

                component_dtype = self.get_channel_dtype(m_Channel)
                component_byte_size = self.get_channel_component_size(m_Channel)
                # channel_byte_size = m_Channel.dimension * component_byte_size

                swap = self.endianess == "<" and component_byte_size > 1
                channel_dimension = m_Channel.dimension & 0xF

                if UnityPyBoost:
                    componentBytes = UnityPyBoost.unpack_vertexdata(
                        m_VertexData.m_DataSize,
                        component_byte_size,
                        m_VertexCount,
                        m_Stream.offset,
                        m_Stream.stride,
                        m_Channel.offset,
                        channel_dimension,
                        swap,
                    )
                else:
                    componentBytes = bytearray(m_VertexCount * channel_dimension * component_byte_size)

                    vertexBaseOffset = m_Stream.offset + m_Channel.offset
                    for v in range(m_VertexCount):
                        vertexOffset = vertexBaseOffset + m_Stream.stride * v
                        for d in range(channel_dimension):
                            componentOffset = vertexOffset + component_byte_size * d
                            vertexDataSrc = componentOffset
                            componentDataSrc = component_byte_size * (v * channel_dimension + d)
                            buff = m_VertexData.m_DataSize[vertexDataSrc : vertexDataSrc + component_byte_size]
                            if swap:  # swap bytes
                                buff = buff[::-1]
                            componentBytes[componentDataSrc : componentDataSrc + component_byte_size] = buff

                component_data = list(struct.iter_unpack(f">{channel_dimension}{component_dtype}", componentBytes))
                self.assign_channel_vertex_data(chn, component_data)

    def assign_channel_vertex_data(self, channel: int, component_data: list):
        if self.version[0] >= 2018:
            if channel == 0:  # kShaderChannelVertex
                self.m_Vertices = component_data
            elif channel == 1:  # kShaderChannelNormal
                self.m_Normals = component_data
            elif channel == 2:  # kShaderChannelTangent
                self.m_Tangents = component_data
            elif channel == 3:  # kShaderChannelColor
                self.m_Colors = component_data
            elif channel == 4:  # kShaderChannelTexCoord0
                self.m_UV0 = component_data
            elif channel == 5:  # kShaderChannelTexCoord1
                self.m_UV1 = component_data
            elif channel == 6:  # kShaderChannelTexCoord2
                self.m_UV2 = component_data
            elif channel == 7:  # kShaderChannelTexCoord3
                self.m_UV3 = component_data
            elif channel == 8:  # kShaderChannelTexCoord4
                self.m_UV4 = component_data
            elif channel == 9:  # kShaderChannelTexCoord5
                self.m_UV5 = component_data
            elif channel == 10:  # kShaderChannelTexCoord6
                self.m_UV6 = component_data
            elif channel == 11:  # kShaderChannelTexCoord7
                self.m_UV7 = component_data
            # 2018.2 and up
            elif channel == 12:  # kShaderChannelBlendWeight
                self.m_BoneWeights = component_data
            elif channel == 13:  # kShaderChannelBlendIndices
                self.m_BoneIndices = component_data
            else:
                raise ValueError(f"Unknown channel {channel}")
        else:
            if channel == 0:  # kShaderChannelVertex
                self.m_Vertices = component_data
            elif channel == 1:  # kShaderChannelNormal
                self.m_Normals = component_data
            elif channel == 2:  # kShaderChannelColor
                self.m_Colors = component_data
            elif channel == 3:  # kShaderChannelTexCoord0
                self.m_UV0 = component_data
            elif channel == 4:  # kShaderChannelTexCoord1
                self.m_UV1 = component_data
            elif channel == 5:
                if self.version[0] >= 5:  # kShaderChannelTexCoord2
                    self.m_UV2 = component_data
                else:  # kShaderChannelTangent
                    self.m_Tangents = component_data
            elif channel == 6:  # kShaderChannelTexCoord3
                self.m_UV3 = component_data
            elif channel == 7:  # kShaderChannelTangent
                self.m_Tangents = component_data
            else:
                raise ValueError(f"Unknown channel {channel}")

    def get_channel_dtype(self, m_Channel: ChannelInfo):
        if self.version[0] < 2017:
            format = VertexChannelFormat(m_Channel.format)
            component_dtype = VERTEX_CHANNEL_FORMAT_STRUCT_TYPE_MAP[format]
        elif self.version[0] < 2019:
            format = VertexFormat2017(m_Channel.format)
            component_dtype = VERTEX_FORMAT_2017_STRUCT_TYPE_MAP[format]
        else:
            format = VertexFormat(m_Channel.format)
            component_dtype = VERTEX_FORMAT_STRUCT_TYPE_MAP[format]

        return component_dtype

    def get_channel_component_size(self, m_Channel: ChannelInfo):
        dtype = self.get_channel_dtype(m_Channel)
        return struct.Struct(dtype).size

    def decompress_compressed_mesh(self):
        # TODO: m_Triangles????

        version = self.version
        assert isinstance(self.src, Mesh)
        m_CompressedMesh = self.src.m_CompressedMesh

        # Vertex
        self.m_VertexCount = m_VertexCount = m_CompressedMesh.m_Vertices.m_NumItems // 3

        if m_CompressedMesh.m_Vertices.m_NumItems > 0:
            self.m_Vertices = unpack_floats(m_CompressedMesh.m_Vertices, shape=(3,))

        # UV
        if m_CompressedMesh.m_UV.m_NumItems > 0:
            m_UVInfo = m_CompressedMesh.m_UVInfo
            if m_UVInfo is not None and m_UVInfo != 0:
                kInfoBitsPerUV = 4
                kUVDimensionMask = 3
                kUVChannelExists = 4
                kMaxTexCoordShaderChannels = 8

                uvSrcOffset = 0

                for uv_channel in range(kMaxTexCoordShaderChannels):
                    texCoordBits = m_UVInfo >> (uv_channel * kInfoBitsPerUV)
                    texCoordBits &= (1 << kInfoBitsPerUV) - 1
                    if (texCoordBits & kUVChannelExists) != 0:
                        uvDim = 1 + int(texCoordBits & kUVDimensionMask)
                        m_UV = unpack_floats(
                            m_CompressedMesh.m_UV,
                            uvSrcOffset,
                            m_VertexCount * uvDim,
                            shape=(uvDim,),
                        )
                        setattr(self, f"m_UV{uv_channel}", m_UV)
                        uvSrcOffset = uvDim * m_VertexCount
            else:
                self.m_UV0 = unpack_floats(m_CompressedMesh.m_UV, 0, m_VertexCount * 2, shape=(2,))
                if m_CompressedMesh.m_UV.m_NumItems >= m_VertexCount * 4:
                    self.m_UV1 = unpack_floats(
                        m_CompressedMesh.m_UV,
                        m_VertexCount * 2,
                        m_VertexCount * 2,
                        shape=(2,),
                    )

        # BindPose
        if version[0] < 5:  # 5.0 down
            m_BindPoses = m_CompressedMesh.m_BindPoses
            if m_BindPoses and m_BindPoses.m_NumItems > 0:
                self.m_BindPose = unpack_floats(
                    m_BindPoses,
                    shape=(
                        4,
                        4,
                    ),
                )

        # Normal
        if m_CompressedMesh.m_Normals.m_NumItems > 0:
            normalData = unpack_floats(m_CompressedMesh.m_Normals, shape=(2,))
            signs = unpack_ints(m_CompressedMesh.m_NormalSigns)

            normals = zeros(self.m_VertexCount, 3)
            for srcNrm, sign, dstNrm in zip(normalData, signs, normals):
                x, y = srcNrm
                zsqr = 1 - x * x - y * y
                if zsqr >= 0:
                    z = math.sqrt(zsqr)
                    dstNrm[:] = x, y, z
                else:
                    z = 0
                    dstNrm[:] = normalize(x, y, z)
                if sign == 0:
                    dstNrm[2] *= -1
            self.m_Normals = lists_to_tuples(normals)

        # Tangent
        if m_CompressedMesh.m_Tangents.m_NumItems > 0:
            tangentData = unpack_floats(m_CompressedMesh.m_Tangents, shape=(2,))
            signs = unpack_ints(m_CompressedMesh.m_TangentSigns, shape=(2,))

            tangents = zeros(self.m_VertexCount, 4)
            for srcTan, (sign_z, sign_w), dstTan in zip(tangentData, signs, tangents):
                x, y = srcTan
                zsqr = 1 - x * x - y * y
                z = 0
                w = 0
                if zsqr >= 0:
                    z = math.sqrt(zsqr)
                else:
                    x, y, z = normalize(x, y, z)
                if sign_z == 0:
                    z = -z
                w = 1.0 if sign_w > 0 else -1.0
                dstTan[:] = x, y, z, w
            self.m_Tangents = lists_to_tuples(tangents)

        # FloatColor
        if version[0] >= 5:  # 5.0 and up
            m_FloatColors = m_CompressedMesh.m_FloatColors
            if m_FloatColors and m_FloatColors.m_NumItems > 0:
                self.m_Colors = unpack_floats(m_FloatColors, shape=(4,))
        # Skin
        if m_CompressedMesh.m_Weights.m_NumItems > 0:
            weightsData = unpack_ints(m_CompressedMesh.m_Weights)
            boneIndicesData = unpack_ints(m_CompressedMesh.m_BoneIndices)

            vertexIndex = 0
            j = 0
            sum = 0

            boneWeights = zeros(self.m_VertexCount, 4)
            boneIndices = zeros(self.m_VertexCount, 4)

            boneIndicesIterator = iter(boneIndicesData)
            for weight, boneIndex in zip(weightsData, boneIndicesIterator):
                # read bone index and weight
                boneWeights[vertexIndex][j] = weight / 31
                boneIndices[vertexIndex][j] = boneIndex

                j += 1
                sum += weight

                # the weights add up to one, continue with the next vertex.
                if sum >= 31:
                    j = 4
                    # set weights and boneIndices to 0,
                    # already done on init
                    vertexIndex += 1
                    j = 0
                    sum = 0
                # we read three weights, but they don't add up to one. calculate the fourth one, and read
                # missing bone index. continue with next vertex.
                elif j == 3:  #
                    boneWeights[vertexIndex][j] = 1 - sum
                    boneIndices[vertexIndex][j] = next(boneIndicesIterator)

                    vertexIndex += 1
                    j = 0
                    sum = 0

            self.m_BoneWeights = lists_to_tuples(boneWeights)
            self.m_BoneIndices = lists_to_tuples(boneIndices)

        # IndexBuffer
        if m_CompressedMesh.m_Triangles.m_NumItems > 0:  #
            self.m_IndexBuffer = unpack_ints(m_CompressedMesh.m_Triangles)
        # Color
        if m_CompressedMesh.m_Colors and m_CompressedMesh.m_Colors.m_NumItems > 0:
            rgba_colors = unpack_ints(m_CompressedMesh.m_Colors)
            self.m_Colors = [
                (
                    ((rgba >> 24) & 0xFF) / 255,
                    ((rgba >> 16) & 0xFF) / 255,
                    ((rgba >> 8) & 0xFF) / 255,
                    (rgba & 0xFF) / 255,
                )
                for rgba in rgba_colors
            ]

    def get_triangles(self) -> List[List[Tuple[int, ...]]]:
        assert self.m_IndexBuffer is not None
        assert self.src.m_SubMeshes is not None

        submeshes: List[List[Tuple[int, ...]]] = []

        for m_SubMesh in self.src.m_SubMeshes:
            firstIndex = m_SubMesh.firstByte // 2
            if not self.m_Use16BitIndices:
                firstIndex //= 2

            indexCount = m_SubMesh.indexCount
            topology = m_SubMesh.topology

            triangles: List[Tuple[int, ...]]

            if topology == MeshTopology.Triangles:
                triangles = [
                    tuple(self.m_IndexBuffer[i : i + 3]) for i in range(firstIndex, firstIndex + indexCount, 3)
                ]

            elif self.version[0] < 4 or topology == MeshTopology.TriangleStrip:
                triangles = [()] * (indexCount - 2)
                triIndex = 0
                for i in range(firstIndex, firstIndex + indexCount - 2):
                    a, b, c = self.m_IndexBuffer[i : i + 3]
                    # skip degenerates
                    if a == b or a == c or b == c:
                        continue
                    # do the winding flip-flop of strips
                    if (i - firstIndex) & 1:
                        triangles[triIndex] = (b, a, c)
                    else:
                        triangles[triIndex] = (a, b, c)
                    triIndex += 1
                triangles = triangles[:triIndex]
                m_SubMesh.indexCount = len(triangles) * 3

            elif topology == MeshTopology.Quads:
                # one quad is two triangles, so // 4 * 2 = // 2
                triangles = [()] * (indexCount // 2)
                triIndex = 0
                for i in range(firstIndex, firstIndex + indexCount, 4):
                    a, b, c, d = self.m_IndexBuffer[i : i + 4]
                    triangles[triIndex] = (a, b, c)
                    triangles[triIndex + 1] = (a, c, d)
                    triIndex += 2

            else:
                raise ValueError("Failed getting triangles. Submesh topology is lines or points.")

            submeshes.append(triangles)

        return submeshes


# COMPRESSION_BIT_SIZES = {
#     "high": {
#         "vertex": 10,
#         "uv": 8,
#         "normal": 6,
#     },
#     "medium": {
#         "vertex": 16,
#         "uv": 10,
#         "normal": 8
#     },
#     "low": {
#         "vertex": 20,
#         "uv": 16,
#         "normal": 8
#     },
# }
