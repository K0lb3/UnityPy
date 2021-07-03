from enum import IntEnum

from .NamedObject import NamedObject
from ..export.ShaderConverter import export_shader
from ..enums import ShaderCompilerPlatform, ShaderGpuProgramType, SerializedPropertyType
from ..enums import TextureDimension, PassType


class Shader(NamedObject):
    def export(self):
        return export_shader(self)

    def __init__(self, reader):
        super().__init__(reader=reader)
        version = reader.version
        if version >= (5, 5):  # 5.5 and up
            self.m_ParsedForm = SerializedShader(reader)
            self.platforms = [
                ShaderCompilerPlatform(x) for x in reader.read_u_int_array()
            ]

            if version >= (2019, 3):  # 2019.3 and up
                self.offsets = reader.read_u_int_array_array()[0]
                self.compressedLengths = reader.read_u_int_array_array()[0]
                self.decompressedLengths = reader.read_u_int_array_array()[0]
            else:
                self.offsets = reader.read_u_int_array()
                self.compressedLengths = reader.read_u_int_array()
                self.decompressedLengths = reader.read_u_int_array()
            self.compressedBlob = reader.read_bytes(reader.read_int())
        else:
            self.m_Script = reader.read_bytes(reader.read_int())
            reader.align_stream()
            self.m_PathName = reader.read_aligned_string()
            if version >= (5, 3):  # 5.3 - 5.4
                self.decompressedSize = reader.read_u_int()
                self.m_SubProgramBlob = reader.read_bytes(reader.read_int())


class StructParameter:
    def __init__(self, reader):
        self.m_NameIndex = reader.read_int()
        self.m_Index = reader.read_int()
        self.m_ArraySize = reader.read_int()
        self.m_StructSize = reader.read_int()

        numVectorParams = reader.read_int()
        self.m_VectorParams = [VectorParameter(
            reader) for _ in range(numVectorParams)]

        numMatrixParams = reader.read_int()
        self.m_MatrixParams = [MatrixParameter(
            reader) for _ in range(numMatrixParams)]


class SamplerParameter:
    def __init__(self, reader):
        self.sampler = reader.read_u_int()
        self.bindPoint = reader.read_int()


class SerializedTextureProperty:
    def __init__(self, reader):
        self.m_DefaultName = reader.read_aligned_string()
        self.m_TexDim = TextureDimension(reader.read_int())


class SerializedProperty:
    def __init__(self, reader):
        self.m_Name = reader.read_aligned_string()
        self.m_Description = reader.read_aligned_string()
        self.m_Attributes = reader.read_string_array()
        self.m_Type = SerializedPropertyType(reader.read_int())
        self.m_Flags = reader.read_u_int()
        self.m_DefValue = reader.read_float_array(4)
        self.m_DefTexture = SerializedTextureProperty(reader)


class SerializedProperties:
    def __init__(self, reader):
        numProps = reader.read_int()
        self.m_Props = [SerializedProperty(reader) for _ in range(numProps)]


class SerializedShaderFloatValue:
    def __init__(self, reader):
        self.val = reader.read_float()
        self.name = reader.read_aligned_string()


class SerializedShaderRTBlendState:
    def __init__(self, reader):
        self.srcBlend = SerializedShaderFloatValue(reader)
        self.destBlend = SerializedShaderFloatValue(reader)
        self.srcBlendAlpha = SerializedShaderFloatValue(reader)
        self.destBlendAlpha = SerializedShaderFloatValue(reader)
        self.blendOp = SerializedShaderFloatValue(reader)
        self.blendOpAlpha = SerializedShaderFloatValue(reader)
        self.colMask = SerializedShaderFloatValue(reader)


class SerializedStencilOp:
    def __init__(self, reader):
        self.pass_ = SerializedShaderFloatValue(reader)
        self.fail = SerializedShaderFloatValue(reader)
        self.zFail = SerializedShaderFloatValue(reader)
        self.comp = SerializedShaderFloatValue(reader)


class SerializedShaderVectorValue:
    def __init__(self, reader):
        self.x = SerializedShaderFloatValue(reader)
        self.y = SerializedShaderFloatValue(reader)
        self.z = SerializedShaderFloatValue(reader)
        self.w = SerializedShaderFloatValue(reader)
        self.name = reader.read_aligned_string()


class FogMode(IntEnum):
    kFogUnknown = (-1,)
    kFogDisabled = (0,)
    kFogLinear = (1,)
    kFogExp = (2,)
    kFogExp2 = (3,)


class SerializedShaderState:
    def __init__(self, reader):
        version = reader.version

        self.m_Name = reader.read_aligned_string()
        self.rtBlend = [SerializedShaderRTBlendState(reader) for _ in range(8)]
        self.rtSeparateBlend = reader.read_boolean()
        reader.align_stream()
        if version >= (2017, 2):  # 2017.2 and up
            self.zClip = SerializedShaderFloatValue(reader)
        self.zTest = SerializedShaderFloatValue(reader)
        self.zWrite = SerializedShaderFloatValue(reader)
        self.culling = SerializedShaderFloatValue(reader)
        if version >= (2020,):  # 2020.1 and up
            self.conservative = SerializedShaderFloatValue(reader)
        self.offsetFactor = SerializedShaderFloatValue(reader)
        self.offsetUnits = SerializedShaderFloatValue(reader)
        self.alphaToMask = SerializedShaderFloatValue(reader)
        self.stencilOp = SerializedStencilOp(reader)
        self.stencilOpFront = SerializedStencilOp(reader)
        self.stencilOpBack = SerializedStencilOp(reader)
        self.stencilReadMask = SerializedShaderFloatValue(reader)
        self.stencilWriteMask = SerializedShaderFloatValue(reader)
        self.stencilRef = SerializedShaderFloatValue(reader)
        self.fogStart = SerializedShaderFloatValue(reader)
        self.fogEnd = SerializedShaderFloatValue(reader)
        self.fogDensity = SerializedShaderFloatValue(reader)
        self.fogColor = SerializedShaderVectorValue(reader)
        self.fogMode = FogMode(reader.read_int())
        self.gpuProgramID = reader.read_int()
        self.m_Tags = SerializedTagMap(reader)
        self.m_LOD = reader.read_int()
        self.lighting = reader.read_boolean()
        reader.align_stream()


class ShaderBindChannel:
    def __init__(self, reader):
        self.source = reader.read_byte()
        self.target = reader.read_byte()


class ParserBindChannels:
    def __init__(self, reader):
        numChannels = reader.read_int()
        self.m_Channels = [ShaderBindChannel(
            reader) for _ in range(numChannels)]
        reader.align_stream()
        self.m_SourceMap = reader.read_u_int()


class VectorParameter:
    def __init__(self, reader):
        self.m_NameIndex = reader.read_int()
        self.m_Index = reader.read_int()
        self.m_ArraySize = reader.read_int()
        self.m_Type = reader.read_byte()
        self.m_Dim = reader.read_byte()
        reader.align_stream()


class MatrixParameter:
    def __init__(self, reader):
        self.m_NameIndex = reader.read_int()
        self.m_Index = reader.read_int()
        self.m_ArraySize = reader.read_int()
        self.m_Type = reader.read_byte()
        self.m_RowCount = reader.read_byte()
        reader.align_stream()


class TextureParameter:
    def __init__(self, reader):
        version = reader.version
        self.m_NameIndex = reader.read_int()
        self.m_Index = reader.read_int()
        self.m_SamplerIndex = reader.read_int()
        if version >= (2017, 3):  # 2017.3 and up
            self.m_MultiSampled = reader.read_boolean()
        self.m_Dim = reader.read_byte()
        reader.align_stream()


class BufferBinding:
    def __init__(self, reader):
        self.m_NameIndex = reader.read_int()
        self.m_Index = reader.read_int()
        if reader.version >= (2020,):  # 2020.1 and up
            m_ArraySize = reader.read_int()


class ConstantBuffer:
    def __init__(self, reader):
        version = reader.version

        self.m_NameIndex = reader.read_int()

        numMatrixParams = reader.read_int()
        self.m_MatrixParams = [MatrixParameter(
            reader) for _ in range(numMatrixParams)]

        numVectorParams = reader.read_int()
        self.m_VectorParams = [VectorParameter(
            reader) for _ in range(numVectorParams)]
        if version >= (2017, 3):  # 2017.3 and up
            numStructParams = reader.read_int()
            self.m_StructParams = [
                StructParameter(reader) for _ in range(numStructParams)
            ]
        self.m_Size = reader.read_int()


class UAVParameter:
    def __init__(self, reader):
        self.m_NameIndex = reader.read_int()
        self.m_Index = reader.read_int()
        self.m_OriginalIndex = reader.read_int()


class SerializedSubProgram:
    def __init__(self, reader):
        version = reader.version

        self.m_BlobIndex = reader.read_u_int()
        self.m_Channels = ParserBindChannels(reader)

        if version >= (2019,):  # 2019 and up
            self.m_GlobalKeywordIndices = reader.read_u_short_array()
            reader.align_stream()
            self.m_LocalKeywordIndices = reader.read_u_short_array()
            reader.align_stream()
        else:
            self.m_KeywordIndices = reader.read_u_short_array()
            if version >= (2017,):  # 2017 and up
                reader.align_stream()

        self.m_ShaderHardwareTier = reader.read_byte()
        self.m_GpuProgramType = ShaderGpuProgramType(reader.read_byte())
        reader.align_stream()

        numVectorParams = reader.read_int()
        self.m_VectorParams = [VectorParameter(
            reader) for _ in range(numVectorParams)]

        numMatrixParams = reader.read_int()
        self.m_MatrixParams = [MatrixParameter(
            reader) for _ in range(numMatrixParams)]

        numTextureParams = reader.read_int()
        self.m_TextureParams = [
            TextureParameter(reader) for _ in range(numTextureParams)
        ]

        numBufferParams = reader.read_int()
        self.m_BufferParams = [BufferBinding(
            reader) for _ in range(numBufferParams)]

        numConstantBuffers = reader.read_int()
        self.m_ConstantBuffers = [
            ConstantBuffer(reader) for _ in range(numConstantBuffers)
        ]

        numConstantBufferBindings = reader.read_int()
        self.m_ConstantBufferBindings = [
            BufferBinding(reader) for _ in range(numConstantBufferBindings)
        ]

        numUAVParams = reader.read_int()
        self.m_UAVParams = [UAVParameter(reader) for _ in range(numUAVParams)]

        if version >= (2017,):  # 2017 and up
            numSamplers = reader.read_int()
            self.m_Samplers = [SamplerParameter(
                reader) for _ in range(numSamplers)]
        if version >= (2017, 2):  # 2017.2 and up
            self.m_ShaderRequirements = reader.read_int()


class SerializedProgram:
    def __init__(self, reader):
        numSubPrograms = reader.read_int()
        self.m_SubPrograms = [
            SerializedSubProgram(reader) for _ in range(numSubPrograms)
        ]


class SerializedPass:
    def __init__(self, reader):
        version = reader.version

        if version >= (2020, 2):  # 2020.2 and up
            numEditorDataHash = reader.read_int()
            m_EditorDataHash = [
                reader.read_bytes(16)  # Hash128(reader)
                for _ in range(numEditorDataHash)
            ]
            reader.align_stream()
            m_Platforms = reader.read_byte_array()
            reader.align_stream()
            m_LocalKeywordMask = reader.read_u_short_array()
            reader.align_stream()
            m_GlobalKeywordMask = reader.read_u_short_array()
            reader.align_stream()

        numIndices = reader.read_int()
        self.m_NameIndices = {}
        for _ in range(numIndices):
            key = reader.read_aligned_string()
            self.m_NameIndices[key] = reader.read_int()
        self.m_Type = PassType(reader.read_int())
        self.m_State = SerializedShaderState(reader)
        self.m_ProgramMask = reader.read_u_int()
        self.progVertex = SerializedProgram(reader)
        self.progFragment = SerializedProgram(reader)
        self.progGeometry = SerializedProgram(reader)
        self.progHull = SerializedProgram(reader)
        self.progDomain = SerializedProgram(reader)
        if version >= (2019, 3):  # 2019.3 and up
            self.progRayTracing = SerializedProgram(reader)
        self.m_HasInstancingVariant = reader.read_boolean()
        if version >= (2018,):  # 2018 and up
            self.m_HasProceduralInstancingVariant = reader.read_boolean()
        reader.align_stream()
        self.m_UseName = reader.read_aligned_string()
        self.m_Name = reader.read_aligned_string()
        self.m_TextureName = reader.read_aligned_string()
        self.m_Tags = SerializedTagMap(reader)


class SerializedTagMap:
    def __init__(self, reader):
        numTags = reader.read_int()
        self.tags = {}
        for _ in range(numTags):
            key = reader.read_aligned_string()
            self.tags[key] = reader.read_aligned_string()


class SerializedSubShader:
    def __init__(self, reader):
        numPasses = reader.read_int()
        self.m_Passes = [SerializedPass(reader) for _ in range(numPasses)]
        self.m_Tags = SerializedTagMap(reader)
        self.m_LOD = reader.read_int()


class SerializedShaderDependency:
    def __init__(self, reader):
        self.from_ = reader.read_aligned_string()
        self.to = reader.read_aligned_string()


class SerializedShader:
    def __init__(self, reader):
        self.m_PropInfo = SerializedProperties(reader)
        numSubShaders = reader.read_int()
        self.m_SubShaders = [SerializedSubShader(
            reader) for _ in range(numSubShaders)]
        self.m_Name = reader.read_aligned_string()
        self.m_CustomEditorName = reader.read_aligned_string()
        self.m_FallbackName = reader.read_aligned_string()
        numDependencies = reader.read_int()
        self.m_Dependencies = [
            SerializedShaderDependency(reader) for _ in range(numDependencies)
        ]
        self.m_DisableNoSubshadersMessage = reader.read_boolean()
        reader.align_stream()
