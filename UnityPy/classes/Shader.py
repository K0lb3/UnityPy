from enum import IntEnum

from .NamedObject import NamedObject


class Shader(NamedObject):
    def __init__(self, reader):
        super().__init__(reader=reader)
        version = reader.version
        if version >= (5, 5):  # 5.5 and up
            self.m_ParsedForm = SerializedShader(reader)
            self.platforms = [
                ShaderCompilerPlatform(x) for x in reader.read_u_int_array()
            ]

            if version >= (2019, 3):  # 2019.3 and up
                offsets = reader.read_u_int_array_array()[0]
                compressedLengths = reader.read_u_int_array_array()[0]
                decompressedLengths = reader.read_u_int_array_array()[0]
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
        self.m_VectorParams = [VectorParameter(reader) for _ in range(numVectorParams)]

        numMatrixParams = reader.read_int()
        self.m_MatrixParams = [MatrixParameter(reader) for _ in range(numMatrixParams)]


class SamplerParameter:
    def __init__(self, reader):
        self.sampler = reader.read_u_int()
        self.bindPoint = reader.read_int()


class TextureDimension(IntEnum):
    kTexDimUnknown = (-1,)
    kTexDimNone = (0,)
    kTexDimAny = (1,)
    kTexDim2D = (2,)
    kTexDim3D = (3,)
    kTexDimCUBE = (4,)
    kTexDim2DArray = (5,)
    kTexDimCubeArray = (6,)
    kTexDimForce32Bit = (2147483647,)


class SerializedTextureProperty:
    def __init__(self, reader):
        self.m_DefaultName = reader.read_aligned_string()
        self.m_TexDim = TextureDimension(reader.read_int())


class SerializedPropertyType(IntEnum):
    kColor = (0,)
    kVector = (1,)
    kFloat = (2,)
    kRange = (3,)
    kTexture = (4,)


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
        self.m_Channels = [ShaderBindChannel(reader) for _ in range(numChannels)]
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


class ConstantBuffer:
    def __init__(self, reader):
        version = reader.version

        self.m_NameIndex = reader.read_int()

        numMatrixParams = reader.read_int()
        self.m_MatrixParams = [MatrixParameter(reader) for _ in range(numMatrixParams)]

        numVectorParams = reader.read_int()
        self.m_VectorParams = [VectorParameter(reader) for _ in range(numVectorParams)]
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


class ShaderGpuProgramType(IntEnum):
    kShaderGpuProgramUnknown = (0,)
    kShaderGpuProgramGLLegacy = (1,)
    kShaderGpuProgramGLES31AEP = (2,)
    kShaderGpuProgramGLES31 = (3,)
    kShaderGpuProgramGLES3 = (4,)
    kShaderGpuProgramGLES = (5,)
    kShaderGpuProgramGLCore32 = (6,)
    kShaderGpuProgramGLCore41 = (7,)
    kShaderGpuProgramGLCore43 = (8,)
    kShaderGpuProgramDX9VertexSM20 = (9,)
    kShaderGpuProgramDX9VertexSM30 = (10,)
    kShaderGpuProgramDX9PixelSM20 = (11,)
    kShaderGpuProgramDX9PixelSM30 = (12,)
    kShaderGpuProgramDX10Level9Vertex = (13,)
    kShaderGpuProgramDX10Level9Pixel = (14,)
    kShaderGpuProgramDX11VertexSM40 = (15,)
    kShaderGpuProgramDX11VertexSM50 = (16,)
    kShaderGpuProgramDX11PixelSM40 = (17,)
    kShaderGpuProgramDX11PixelSM50 = (18,)
    kShaderGpuProgramDX11GeometrySM40 = (19,)
    kShaderGpuProgramDX11GeometrySM50 = (20,)
    kShaderGpuProgramDX11HullSM50 = (21,)
    kShaderGpuProgramDX11DomainSM50 = (22,)
    kShaderGpuProgramMetalVS = (23,)
    kShaderGpuProgramMetalFS = (24,)
    kShaderGpuProgramSPIRV = (25,)
    kShaderGpuProgramConsole = (26,)


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
        self.m_VectorParams = [VectorParameter(reader) for _ in range(numVectorParams)]

        numMatrixParams = reader.read_int()
        self.m_MatrixParams = [MatrixParameter(reader) for _ in range(numMatrixParams)]

        numTextureParams = reader.read_int()
        self.m_TextureParams = [
            TextureParameter(reader) for _ in range(numTextureParams)
        ]

        numBufferParams = reader.read_int()
        self.m_BufferParams = [BufferBinding(reader) for _ in range(numBufferParams)]

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
            self.m_Samplers = [SamplerParameter(reader) for _ in range(numSamplers)]
        if version >= (2017, 2):  # 2017.2 and up
            self.m_ShaderRequirements = reader.read_int()


class SerializedProgram:
    def __init__(self, reader):
        numSubPrograms = reader.read_int()
        self.m_SubPrograms = [
            SerializedSubProgram(reader) for _ in range(numSubPrograms)
        ]


class PassType(IntEnum):
    kPassTypeNormal = (0,)
    kPassTypeUse = (1,)
    kPassTypeGrab = 2


class SerializedPass:
    def __init__(self, reader):
        version = reader.version
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
        self.m_SubShaders = [SerializedSubShader(reader) for _ in range(numSubShaders)]
        self.m_Name = reader.read_aligned_string()
        self.m_CustomEditorName = reader.read_aligned_string()
        self.m_FallbackName = reader.read_aligned_string()
        numDependencies = reader.read_int()
        self.m_Dependencies = [
            SerializedShaderDependency(reader) for _ in range(numDependencies)
        ]
        self.m_DisableNoSubshadersMessage = reader.read_boolean()
        reader.align_stream()


class ShaderCompilerPlatform(IntEnum):
    kShaderCompPlatformNone = (-1,)
    kShaderCompPlatformGL = (0,)
    kShaderCompPlatformD3D9 = (1,)
    kShaderCompPlatformXbox360 = (2,)
    kShaderCompPlatformPS3 = (3,)
    kShaderCompPlatformD3D11 = (4,)
    kShaderCompPlatformGLES20 = (5,)
    kShaderCompPlatformNaCl = (6,)
    kShaderCompPlatformFlash = (7,)
    kShaderCompPlatformD3D11_9x = (8,)
    kShaderCompPlatformGLES3Plus = (9,)
    kShaderCompPlatformPSP2 = (10,)
    kShaderCompPlatformPS4 = (11,)
    kShaderCompPlatformXboxOne = (12,)
    kShaderCompPlatformPSM = (13,)
    kShaderCompPlatformMetal = (14,)
    kShaderCompPlatformOpenGLCore = (15,)
    kShaderCompPlatformN3DS = (16,)
    kShaderCompPlatformWiiU = (17,)
    kShaderCompPlatformVulkan = (18,)
    kShaderCompPlatformSwitch = (19,)
    kShaderCompPlatformXboxOneD3D12 = (20,)
