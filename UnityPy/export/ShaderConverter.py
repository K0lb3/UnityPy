import traceback
from ..streams import EndianBinaryReader
from ..helpers import CompressionHelper
import re
from itertools import groupby
from ..enums import ShaderCompilerPlatform, ShaderGpuProgramType, SerializedPropertyType
from ..enums import TextureDimension, PassType

HEADER = '''
//////////////////////////////////////////
//
// NOTE: This is *not* a valid shader file
//
///////////////////////////////////////////
'''[1:]


def export_shader(m_Shader):
    if hasattr(m_Shader, "m_SubProgramBlob"): # 5.3 - 5.4
        decompressedBytes = CompressionHelper.decompress_lz4(
            m_Shader.m_SubProgramBlob, m_Shader.decompressedSize)

        blobReader = EndianBinaryReader(decompressedBytes)
        program = ShaderProgram(blobReader, m_Shader.version)

        return HEADER + program.Export(bytes(m_Shader.m_Script).decode("utf8"))

    if hasattr(m_Shader, "compressedBlob"): # 5.5 and up
        return HEADER + ConvertSerializedShader(m_Shader)

    return HEADER + bytes(m_Shader.m_Script).decode("utf8")

def ConvertSerializedShader(m_Shader):
    shaderPrograms = []

    platformNumber = len(m_Shader.platforms)
    for i in range(platformNumber):
        compressedSize = m_Shader.compressedLengths[i]
        decompressedSize = m_Shader.decompressedLengths[i]

        compressedBytes = m_Shader.compressedBlob[int(m_Shader.offsets[i]):int(m_Shader.offsets[i]) + compressedSize]
        decompressedBytes = CompressionHelper.decompress_lz4(compressedBytes, decompressedSize)

        shaderPrograms.append(ShaderProgram(EndianBinaryReader(decompressedBytes, endian="<"), m_Shader.version))

    return ConvertSerializedShaderParsedForm(m_Shader.m_ParsedForm, m_Shader.platforms, shaderPrograms)

def ConvertSerializedShaderParsedForm(m_ParsedForm, platforms, shaderPrograms):
    sb = []

    sb.append("Shader \"{0}\" {{\n".format(m_ParsedForm.m_Name))

    sb.append(ConvertSerializedProperties(m_ParsedForm.m_PropInfo))

    for m_SubShader in m_ParsedForm.m_SubShaders:
        sb.append(ConvertSerializedSubShader(m_SubShader, platforms, shaderPrograms))

    if m_ParsedForm.m_FallbackName:
        sb.append("Fall back \"{0}\"\n".format(m_ParsedForm.m_FallbackName))

    if m_ParsedForm.m_CustomEditorName:
        sb.append("CustomEditor \"{0}\"\n".format(m_ParsedForm.m_CustomEditorName))

    sb.append("}")
    return "".join(sb)

def ConvertSerializedSubShader(m_SubShader, platforms, shaderPrograms):
    sb = []

    sb.append("SubShader {\n")
    if m_SubShader.m_LOD != 0:
        sb.append(" LOD {0}\n".format(m_SubShader.m_LOD))

    sb.append(ConvertSerializedTagMap(m_SubShader.m_Tags, 1))

    for m_Passe in m_SubShader.m_Passes:
        sb.append(ConvertSerializedPass(m_Passe, platforms, shaderPrograms))

    sb.append("}\n")
    return "".join(sb)

def ConvertSerializedPass(m_Passe, platforms, shaderPrograms):
    sb = []
    if m_Passe.m_Type == PassType.kPassTypeNormal:
        sb.append(" Pass ")
    elif m_Passe.m_Type == PassType.kPassTypeUse:
        sb.append(" UsePass ")
    elif m_Passe.m_Type == PassType.kPassTypeGrab:
        sb.append(" GrabPass ")

    if m_Passe.m_Type == PassType.kPassTypeUse:
        sb.append("\"{0}\"\n".format(m_Passe.m_UseName))
    else:
        sb.append("{\n")

        if m_Passe.m_Type == PassType.kPassTypeGrab:
            if m_Passe.m_TextureName:
                sb.append(" \"{0}\"\n".format(m_Passe.m_TextureName))

        else:
            sb.append(ConvertSerializedShaderState(m_Passe.m_State))

            if len(m_Passe.progVertex.m_SubPrograms) > 0:
                sb.append("Program \"vp\" {\n")
                sb.append(ConvertSerializedSubPrograms(m_Passe.progVertex.m_SubPrograms, platforms, shaderPrograms))
                sb.append("}\n")

            if len(m_Passe.progFragment.m_SubPrograms) > 0:
                sb.append("Program \"fp\" {\n")
                sb.append(ConvertSerializedSubPrograms(m_Passe.progFragment.m_SubPrograms, platforms, shaderPrograms))
                sb.append("}\n")

            if len(m_Passe.progGeometry.m_SubPrograms) > 0:
                sb.append("Program \"gp\" {\n")
                sb.append(ConvertSerializedSubPrograms(m_Passe.progGeometry.m_SubPrograms, platforms, shaderPrograms))
                sb.append("}\n")

            if len(m_Passe.progHull.m_SubPrograms) > 0:
                sb.append("Program \"hp\" {\n")
                sb.append(ConvertSerializedSubPrograms(m_Passe.progHull.m_SubPrograms, platforms, shaderPrograms))
                sb.append("}\n")

            if len(m_Passe.progDomain.m_SubPrograms) > 0:
                sb.append("Program \"dp\" {\n")
                sb.append(ConvertSerializedSubPrograms(m_Passe.progDomain.m_SubPrograms, platforms, shaderPrograms))
                sb.append("}\n")

        sb.append("}\n")

    return "".join(sb)

def ConvertSerializedSubPrograms(m_SubPrograms, platforms, shaderPrograms):
    sb = []

    indexFunc = lambda x: x.m_BlobIndex
    typeFunc = lambda x: x.m_GpuProgramType

    groups = groupby(sorted(m_SubPrograms, key=indexFunc), indexFunc)

    for _, _group in groups:
        group = list(_group)
        programs = groupby(sorted(group, key=typeFunc), typeFunc)

        for programKey, _programList in programs:
            subPrograms = list(_programList)
            isTier = len(subPrograms) > 1
            for i in range(len(platforms)):
                platform = platforms[i]

                if CheckGpuProgramUsable(platform, programKey):
                    for subProgram in subPrograms:
                        sb.append("SubProgram \"{0} ".format(GetPlatformString(platform)))

                        if isTier:
                            sb.append("hw_tier{0:02} ".format(subProgram.m_ShaderHardwareTier))

                        sb.append("\" {\n")
                        sb.append(shaderPrograms[i].m_SubPrograms[subProgram.m_BlobIndex].Export())

                        sb.append("\n}\n")

                    break

    return "".join(sb)


def ConvertSerializedShaderState(m_State):
    sb = []
    if m_State.m_Name:
        sb.append(" Name \"{0}\"\n".format(m_State.m_Name))

    if m_State.m_LOD != 0:
        sb.append("  LOD {0}\n".format(m_State.m_LOD))

    sb.append(ConvertSerializedTagMap(m_State.m_Tags, 2))

    sb.append(ConvertSerializedShaderRTBlendState(m_State.rtBlend))

    if m_State.alphaToMask.val > 0:
        sb.append(" AlphaToMask On\n")

    if m_State.zClip and m_State.zClip.val != 1:
        sb.append(" ZClip Off\n")

    if m_State.zTest.val != 4:
        sb.append(" ZTest ")
        if m_State.zTest.val == 0: # kFuncDisabled
            sb.append("Off")
        elif m_State.zTest.val == 1: # kFuncNever
            sb.append("Never")
        elif m_State.zTest.val == 2: # kFuncLess
            sb.append("Less")
        elif m_State.zTest.val == 3: # kFuncEqual
            sb.append("Equal")
        elif m_State.zTest.val == 5: # kFuncGreater
            sb.append("Greater")
        elif m_State.zTest.val == 6: # kFuncNotEqual
            sb.append("NotEqual")
        elif m_State.zTest.val == 7: # kFuncGEqual
            sb.append("GEqual")
        elif m_State.zTest.val == 8: # kFuncAlways
            sb.append("Always")

        sb.append("\n")

    if m_State.zWrite.val != 1: # ZWrite On
        sb.append(" ZWrite Off\n")

    if m_State.culling.val != 2: # Cull Back
        sb.append(" Cull ")
        if m_State.culling.val == 0: # kCullOff
            sb.append("Off")
        elif m_State.culling.val == 1: # kCullFront
            sb.append("Front")

        sb.append("\n")

    if m_State.offsetFactor.val != 0 or m_State.offsetUnits.val != 0:
        sb.append(" Offset {0}, {1}\n".format(m_State.offsetFactor.val, m_State.offsetUnits.val))

    # TODO Stencil

    # TODO Fog

    if m_State.lighting:
        sb.append("  Lighting {0}\n".format(m_State.lighting and "On" or "Off"))

    sb.append("  GpuProgramID {0}\n".format(m_State.gpuProgramID))
    return "".join(sb)


def ConvertSerializedShaderRTBlendState(rbBlend):
    # TODO Blend
    sb = []
    return "".join(sb)

def ConvertSerializedTagMap(m_Tags, intent: int):
    sb = []
    if len(m_Tags.tags) > 0:
        sb.append(" "*intent)
        sb.append("Tags { ")
        for key, value in m_Tags.tags.items():
            sb.append("\"{0}\" = \"{1}\" ".format(key, value))
        sb.append("}\n")

    return "".join(sb)

def ConvertSerializedProperties(m_PropInfo):
    sb = []

    sb.append("Properties {\n")
    for m_Prop in m_PropInfo.m_Props:
        sb.append(ConvertSerializedProperty(m_Prop))

    sb.append("}\n")
    return "".join(sb)

def ConvertSerializedProperty(m_Prop):
    sb = []
    for m_Attribute in m_Prop.m_Attributes:
        sb.append("[{0}] ".format(m_Attribute))

    sb.append("{0} (\"{1}\", ".format(m_Prop.m_Name, m_Prop.m_Description))

    if m_Prop.m_Type == SerializedPropertyType.kColor:
        sb.append("Color")
    elif m_Prop.m_Type == SerializedPropertyType.kVector:
        sb.append("Vector")
    elif m_Prop.m_Type == SerializedPropertyType.kFloat:
        sb.append("Float")
    elif m_Prop.m_Type == SerializedPropertyType.kRange:
        sb.append("Range({0:g}, {1:g})".format(m_Prop.m_DefValue[1], m_Prop.m_DefValue[2]))
    elif m_Prop.m_Type == SerializedPropertyType.kTexture:
        if m_Prop.m_DefTexture.m_TexDim == TextureDimension.kTexDimAny:
            sb.append("any")
        elif m_Prop.m_DefTexture.m_TexDim == TextureDimension.kTexDim2D:
            sb.append("2D")
        elif m_Prop.m_DefTexture.m_TexDim == TextureDimension.kTexDim3D:
            sb.append("3D")
        elif m_Prop.m_DefTexture.m_TexDim == TextureDimension.kTexDimCUBE:
            sb.append("Cube")
        elif m_Prop.m_DefTexture.m_TexDim == TextureDimension.kTexDim2DArray:
            sb.append("2DArray")
        elif m_Prop.m_DefTexture.m_TexDim == TextureDimension.kTexDimCubeArray:
            sb.append("CubeArray")

    sb.append(") = ")

    if m_Prop.m_Type in [
        SerializedPropertyType.kColor,
        SerializedPropertyType.kVector
    ]:
        sb.append("({0:g},{1:g},{2:g},{3:g})".format(m_Prop.m_DefValue[0], m_Prop.m_DefValue[1], m_Prop.m_DefValue[2],m_Prop.m_DefValue[3]))
    elif m_Prop.m_Type in [
        SerializedPropertyType.kFloat,
        SerializedPropertyType.kRange
    ]:
        sb.append(m_Prop.m_DefValue[0])
    elif m_Prop.m_Type == SerializedPropertyType.kTexture:
        sb.append("\"{0}\" {{ }}".format(m_Prop.m_DefTexture.m_DefaultName))
    else:
        raise ValueError(m_Prop.m_Type)

    sb.append("\n")
    return "".join(map(str,sb))

def CheckGpuProgramUsable(platform, programType):
    if platform == ShaderCompilerPlatform.kShaderCompPlatformGL:
        return programType == ShaderGpuProgramType.kShaderGpuProgramGLLegacy
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformD3D9:
        return ( programType == ShaderGpuProgramType.kShaderGpuProgramDX9VertexSM20
            or programType == ShaderGpuProgramType.kShaderGpuProgramDX9VertexSM30
            or programType == ShaderGpuProgramType.kShaderGpuProgramDX9PixelSM20
            or programType == ShaderGpuProgramType.kShaderGpuProgramDX9PixelSM30 )
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformXbox360:
        return ( programType == ShaderGpuProgramType.kShaderGpuProgramConsoleVS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleFS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleHS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleDS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleGS )
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformD3D11:
        return ( programType == ShaderGpuProgramType.kShaderGpuProgramDX11VertexSM40
            or programType == ShaderGpuProgramType.kShaderGpuProgramDX11VertexSM50
            or programType == ShaderGpuProgramType.kShaderGpuProgramDX11PixelSM40
            or programType == ShaderGpuProgramType.kShaderGpuProgramDX11PixelSM50
            or programType == ShaderGpuProgramType.kShaderGpuProgramDX11GeometrySM40
            or programType == ShaderGpuProgramType.kShaderGpuProgramDX11GeometrySM50
            or programType == ShaderGpuProgramType.kShaderGpuProgramDX11HullSM50
            or programType == ShaderGpuProgramType.kShaderGpuProgramDX11DomainSM50 )
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformGLES20:
        return programType == ShaderGpuProgramType.kShaderGpuProgramGLES
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformNaCl:
        raise NotImplementedError
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformFlash:
        raise NotImplementedError
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformD3D11_9x:
        return ( programType == ShaderGpuProgramType.kShaderGpuProgramDX10Level9Vertex
            or programType == ShaderGpuProgramType.kShaderGpuProgramDX10Level9Pixel )
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformGLES3Plus:
        return ( programType == ShaderGpuProgramType.kShaderGpuProgramGLES31AEP
            or programType == ShaderGpuProgramType.kShaderGpuProgramGLES31
            or programType == ShaderGpuProgramType.kShaderGpuProgramGLES3 )
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformPSP2:
        return ( programType == ShaderGpuProgramType.kShaderGpuProgramConsoleVS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleFS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleHS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleDS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleGS )
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformPS4:
        return ( programType == ShaderGpuProgramType.kShaderGpuProgramConsoleVS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleFS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleHS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleDS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleGS )
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformXboxOne:
        return ( programType == ShaderGpuProgramType.kShaderGpuProgramConsoleVS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleFS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleHS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleDS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleGS )
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformPSM:
        raise NotImplementedError
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformMetal:
        return ( programType == ShaderGpuProgramType.kShaderGpuProgramMetalVS
            or programType == ShaderGpuProgramType.kShaderGpuProgramMetalVS )
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformOpenGLCore:
        return ( programType == ShaderGpuProgramType.kShaderGpuProgramGLCore32
            or programType == ShaderGpuProgramType.kShaderGpuProgramGLCore41
            or programType == ShaderGpuProgramType.kShaderGpuProgramGLCore43 )
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformN3DS:
        return ( programType == ShaderGpuProgramType.kShaderGpuProgramConsoleVS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleFS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleHS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleDS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleGS )
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformWiiU:
        return ( programType == ShaderGpuProgramType.kShaderGpuProgramConsoleVS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleFS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleHS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleDS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleGS )
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformVulkan:
        return programType == ShaderGpuProgramType.kShaderGpuProgramSPIRV
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformSwitch:
        return ( programType == ShaderGpuProgramType.kShaderGpuProgramConsoleVS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleFS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleHS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleDS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleGS )
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformXboxOneD3D12:
        return ( programType == ShaderGpuProgramType.kShaderGpuProgramConsoleVS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleFS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleHS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleDS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleGS )
    else:
        raise NotImplementedError


def GetPlatformString(platform):
    if platform == ShaderCompilerPlatform.kShaderCompPlatformGL:
        return "openGL"
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformD3D9:
        return "d3d9"
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformXbox360:
        return "xbox360"
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformPS3:
        return "ps3"
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformD3D11:
        return "d3d11"
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformGLES20:
        return "gles"
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformNaCl:
        return "glesdesktop"
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformFlash:
        return "flash"
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformD3D11_9x:
        return "d3d11_9x"
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformGLES3Plus:
        return "gles3"
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformPSP2:
        return "psp2"
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformPS4:
        return "ps4"
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformXboxOne:
        return "xboxone"
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformPSM:
        return "psm"
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformMetal:
        return "metal"
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformOpenGLCore:
        return "glcore"
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformN3DS:
        return "n3ds"
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformWiiU:
        return "wiiu"
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformVulkan:
        return "vulkan"
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformSwitch:
        return "switch"
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformXboxOneD3D12:
        return "xboxone+_d3d12"
    else:
        return "unknown"


class ShaderProgram:
    def __init__(self, reader: EndianBinaryReader, version):
        subProgramCapacity = reader.read_int()
        self.m_SubPrograms = []

        if version >=(2019, 3): # 2019.3 and up
            entrySize = 12
        else:
            entrySize = 8

        for i in range(subProgramCapacity):
            reader.Position = 4 + i * entrySize
            offset = reader.read_int()
            reader.Position = offset
            self.m_SubPrograms.append(ShaderSubProgram(reader))

    def Export(self, shader):
        shader = re.sub(r"GpuProgramIndex (.+)",
        lambda math: self.m_SubPrograms[int(math.group(1))].Export(),
        shader)

        return shader


class ShaderSubProgram:
    def __init__(self, reader: EndianBinaryReader):
        #LoadGpuProgramFromData
        #201509030 - Unity 5.3
        #201510240 - Unity 5.4
        #201608170 - Unity 5.5
        #201609010 - Unity 5.6, 2017.1 & 2017.2
        #201708220 - Unity 2017.3, Unity 2017.4 & Unity 2018.1
        #201802150 - Unity 2018.2 & Unity 2018.3
        #201806140 - Unity 2019.1~2020.1

        self.m_Version = reader.read_int()
        self.m_ProgramType = ShaderGpuProgramType(reader.read_int())
        reader.Position += 12

        if self.m_Version >= 201608170:
            reader.Position += 4

        m_KeywordSize = reader.read_int()
        self.m_Keywords = []

        for i in range(m_KeywordSize):
            self.m_Keywords.append(reader.read_aligned_string())

        if self.m_Version >= 201806140:
            m_LocalKeywordsSize = reader.read_int()
            self.m_LocalKeywords = []

            for i in range(m_LocalKeywordsSize):
                self.m_LocalKeywords.append(reader.read_aligned_string())

        self.m_ProgramCode = reader.read_byte_array()
        reader.align_stream()

    def Export(self):
        sb = []

        if len(self.m_Keywords) > 0:
            sb.append("Keywords { ")
            for keyword in self.m_Keywords:
                sb.append("\"{0}\" ".format(keyword))

            sb.append("}\n")

        if hasattr(self, 'm_LocalKeywords') and len(self.m_LocalKeywords) > 0:
            sb.append("Local Keywords { ")
            for keyword in self.m_LocalKeywords:
                sb.append("\"{0}\" ".format(keyword))

            sb.append("}\n")

        sb.append("\"")

        if len(self.m_ProgramCode) > 0:
            if self.m_ProgramType in [
                ShaderGpuProgramType.kShaderGpuProgramGLLegacy,
                ShaderGpuProgramType.kShaderGpuProgramGLES31AEP,
                ShaderGpuProgramType.kShaderGpuProgramGLES31,
                ShaderGpuProgramType.kShaderGpuProgramGLES3,
                ShaderGpuProgramType.kShaderGpuProgramGLES,
                ShaderGpuProgramType.kShaderGpuProgramGLCore32,
                ShaderGpuProgramType.kShaderGpuProgramGLCore41,
                ShaderGpuProgramType.kShaderGpuProgramGLCore43
            ]:
                sb.append(bytes(self.m_ProgramCode).decode("utf8"))
            elif self.m_ProgramType in [
                ShaderGpuProgramType.kShaderGpuProgramDX9VertexSM20,
                ShaderGpuProgramType.kShaderGpuProgramDX9VertexSM30,
                ShaderGpuProgramType.kShaderGpuProgramDX9PixelSM20,
                ShaderGpuProgramType.kShaderGpuProgramDX9PixelSM30
            ]:
                sb.append("// shader disassembly not supported on DXBC")
            elif self.m_ProgramType in [
                ShaderGpuProgramType.kShaderGpuProgramDX10Level9Vertex,
                ShaderGpuProgramType.kShaderGpuProgramDX10Level9Pixel,
                ShaderGpuProgramType.kShaderGpuProgramDX11VertexSM40,
                ShaderGpuProgramType.kShaderGpuProgramDX11VertexSM50,
                ShaderGpuProgramType.kShaderGpuProgramDX11PixelSM40,
                ShaderGpuProgramType.kShaderGpuProgramDX11PixelSM50,
                ShaderGpuProgramType.kShaderGpuProgramDX11GeometrySM40,
                ShaderGpuProgramType.kShaderGpuProgramDX11GeometrySM50,
                ShaderGpuProgramType.kShaderGpuProgramDX11HullSM50,
                ShaderGpuProgramType.kShaderGpuProgramDX11DomainSM50
            ]:
                sb.append("// shader disassembly not supported on DXBC")
            elif self.m_ProgramType in [
                ShaderGpuProgramType.kShaderGpuProgramMetalVS,
                ShaderGpuProgramType.kShaderGpuProgramMetalFS
            ]:
                reader = EndianBinaryReader(self.m_ProgramCode)
                fourCC = reader.read_u_int()
                if fourCC == 0xf00dcafe:
                    offset = reader.read_int()
                    reader.Position = offset

                entryName = reader.read_string_to_null()
                buff = reader.read_bytes(int(reader.Length - reader.Position))
                sb.append(bytes(buff).decode("utf8"))
            elif self.m_ProgramType == ShaderGpuProgramType.kShaderGpuProgramSPIRV:
                # TODO SpirVShaderConverter
                pass
            elif self.m_ProgramType in [
                ShaderGpuProgramType.kShaderGpuProgramConsoleVS,
                ShaderGpuProgramType.kShaderGpuProgramConsoleFS,
                ShaderGpuProgramType.kShaderGpuProgramConsoleHS,
                ShaderGpuProgramType.kShaderGpuProgramConsoleDS,
                ShaderGpuProgramType.kShaderGpuProgramConsoleGS
            ]:
                sb.append(bytes(self.m_ProgramCode).decode("utf8"))
            else:
                sb.append("//shader disassembly not supported on {0}".format(self.m_ProgramType))

        sb.append('"')
        return "".join(sb)
