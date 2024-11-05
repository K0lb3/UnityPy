from __future__ import annotations

import re
from itertools import groupby
from typing import TYPE_CHECKING, List, Optional, Tuple, TypeVar, Union

from ..enums import (
    PassType,
    SerializedPropertyType,
    ShaderCompilerPlatform,
    ShaderGpuProgramType,
    TextureDimension,
)
from ..helpers import CompressionHelper
from ..streams import EndianBinaryReader

if TYPE_CHECKING:
    from ..classes import (
        SerializedPass,
        SerializedProperties,
        SerializedProperty,
        SerializedShader,
        SerializedShaderState,
        SerializedSubProgram,
        SerializedSubShader,
        SerializedTagMap,
        Shader,
    )

HEADER = """
//////////////////////////////////////////
//
// NOTE: This is *not* a valid shader file
//
///////////////////////////////////////////
"""[1:]

T = TypeVar("T")


def export_shader(m_Shader: Shader) -> str:
    if m_Shader.m_SubProgramBlob:  # 5.3 - 5.4
        decompressedBytes = CompressionHelper.decompress_lz4(
            bytes(m_Shader.m_SubProgramBlob), m_Shader.decompressedSize
        )

        blobReader = EndianBinaryReader(decompressedBytes)
        program = ShaderProgram(blobReader, m_Shader.object_reader.version)

        return HEADER + program.Export(bytes(m_Shader.m_Script).decode("utf8"))

    if m_Shader.compressedBlob:  # 5.5 and up
        return HEADER + ConvertSerializedShader(m_Shader)

    return HEADER + bytes(m_Shader.m_Script).decode("utf8")


def ConvertSerializedShader(m_Shader: Shader) -> str:
    shaderPrograms = []

    platformNumber = len(m_Shader.platforms)
    compressed_blob = bytes(m_Shader.compressedBlob)

    def get_entry(array: Union[List[T], List[List[T]]], index: int) -> T:
        item = array[index]
        if isinstance(item, List):
            return item[0]
        return item

    for i in range(platformNumber):
        if i >= len(m_Shader.compressedLengths) or i >= len(
            m_Shader.decompressedLengths
        ):
            # m_Shader.platforms shouldn't be longer than m_shader.[de]compressedLengths, but it is
            break

        compressedSize = get_entry(m_Shader.compressedLengths, i)
        decompressedSize = get_entry(m_Shader.decompressedLengths, i)
        offset = get_entry(m_Shader.offsets, i)

        compressedBytes = compressed_blob[offset : offset + compressedSize]
        decompressedBytes = CompressionHelper.decompress_lz4(
            compressedBytes, decompressedSize
        )

        shaderPrograms.append(
            ShaderProgram(
                EndianBinaryReader(decompressedBytes, endian="<"),
                m_Shader.object_reader.version,
            )
        )

    return ConvertSerializedShaderParsedForm(
        m_Shader.m_ParsedForm, m_Shader.platforms, shaderPrograms
    )


def ConvertSerializedShaderParsedForm(
    m_ParsedForm: SerializedShader,
    platforms: List[int],
    shaderPrograms: List[ShaderProgram],
) -> str:
    sb: List[str] = [
        'Shader "{0}" {{\n'.format(m_ParsedForm.m_Name),
        ConvertSerializedProperties(m_ParsedForm.m_PropInfo),
        *[
            ConvertSerializedSubShader(m_SubShader, platforms, shaderPrograms)
            for m_SubShader in m_ParsedForm.m_SubShaders
        ],
    ]

    if m_ParsedForm.m_FallbackName:
        sb.append('Fall back "{0}"\n'.format(m_ParsedForm.m_FallbackName))

    if m_ParsedForm.m_CustomEditorName:
        sb.append('CustomEditor "{0}"\n'.format(m_ParsedForm.m_CustomEditorName))

    sb.append("}")
    return "".join(sb)


def ConvertSerializedSubShader(
    m_SubShader: SerializedSubShader,
    platforms: List[int],
    shaderPrograms: List[ShaderProgram],
) -> str:
    sb = ["SubShader {\n"]

    if m_SubShader.m_LOD != 0:
        sb.append(" LOD {0}\n".format(m_SubShader.m_LOD))

    sb.append(ConvertSerializedTagMap(m_SubShader.m_Tags, 1))

    sb.extend(
        ConvertSerializedPass(m_Passe, platforms, shaderPrograms)
        for m_Passe in m_SubShader.m_Passes
    )
    sb.append("}\n")
    return "".join(sb)


def ConvertSerializedPass(
    m_Passe: SerializedPass, platforms: List[int], shaderPrograms: List[ShaderProgram]
) -> str:
    sb = []
    if m_Passe.m_Type == PassType.kPassTypeNormal:
        sb.append(" Pass ")
    elif m_Passe.m_Type == PassType.kPassTypeUse:
        sb.append(" UsePass ")
    elif m_Passe.m_Type == PassType.kPassTypeGrab:
        sb.append(" GrabPass ")

    if m_Passe.m_Type == PassType.kPassTypeUse:
        sb.append('"{0}"\n'.format(m_Passe.m_UseName))
    else:
        sb.append("{\n")

        if m_Passe.m_Type == PassType.kPassTypeGrab:
            if m_Passe.m_TextureName:
                sb.append(' "{0}"\n'.format(m_Passe.m_TextureName))

        else:
            sb.append(ConvertSerializedShaderState(m_Passe.m_State))

            if len(m_Passe.progVertex.m_SubPrograms) > 0:
                sb.append('Program "vp" {\n')
                sb.append(
                    ConvertSerializedSubPrograms(
                        m_Passe.progVertex.m_SubPrograms, platforms, shaderPrograms
                    )
                )
                sb.append("}\n")

            if len(m_Passe.progFragment.m_SubPrograms) > 0:
                sb.append('Program "fp" {\n')
                sb.append(
                    ConvertSerializedSubPrograms(
                        m_Passe.progFragment.m_SubPrograms, platforms, shaderPrograms
                    )
                )
                sb.append("}\n")

            if len(m_Passe.progGeometry.m_SubPrograms) > 0:
                sb.append('Program "gp" {\n')
                sb.append(
                    ConvertSerializedSubPrograms(
                        m_Passe.progGeometry.m_SubPrograms, platforms, shaderPrograms
                    )
                )
                sb.append("}\n")

            if len(m_Passe.progHull.m_SubPrograms) > 0:
                sb.append('Program "hp" {\n')
                sb.append(
                    ConvertSerializedSubPrograms(
                        m_Passe.progHull.m_SubPrograms, platforms, shaderPrograms
                    )
                )
                sb.append("}\n")

            if len(m_Passe.progDomain.m_SubPrograms) > 0:
                sb.append('Program "dp" {\n')
                sb.append(
                    ConvertSerializedSubPrograms(
                        m_Passe.progDomain.m_SubPrograms, platforms, shaderPrograms
                    )
                )
                sb.append("}\n")

        sb.append("}\n")

    return "".join(sb)


def ConvertSerializedSubPrograms(
    m_SubPrograms: List[SerializedSubProgram],
    platforms: List[int],
    shaderPrograms: List[ShaderProgram],
) -> str:
    sb = []

    def indexFunc(x: SerializedSubProgram):
        return x.m_BlobIndex

    def typeFunc(x: SerializedSubProgram):
        return x.m_GpuProgramType

    groups = groupby(sorted(m_SubPrograms, key=indexFunc), indexFunc)

    for _, _group in groups:
        group = list(_group)
        programs = groupby(sorted(group, key=typeFunc), typeFunc)

        for programKey, _programList in programs:
            subPrograms = list(_programList)
            isTier = len(subPrograms) > 1
            for i in range(len(platforms)):
                if i >= len(shaderPrograms):
                    # platforms shouldn't be longer than shaderPrograms, but it is
                    break

                platform = platforms[i]

                if CheckGpuProgramUsable(platform, programKey):
                    for subProgram in subPrograms:
                        sb.append(
                            'SubProgram "{0} '.format(GetPlatformString(platform))
                        )

                        if isTier:
                            sb.append(
                                "hw_tier{0:02} ".format(subProgram.m_ShaderHardwareTier)
                            )

                        sb.append('" {\n')
                        sb.append(
                            shaderPrograms[i]
                            .m_SubPrograms[subProgram.m_BlobIndex]
                            .Export()
                        )

                        sb.append("\n}\n")

                    break

    return "".join(sb)


def ConvertSerializedShaderState(m_State: SerializedShaderState) -> str:
    sb = []
    if m_State.m_Name:
        sb.append(' Name "{0}"\n'.format(m_State.m_Name))

    if m_State.m_LOD != 0:
        sb.append("  LOD {0}\n".format(m_State.m_LOD))

    sb.append(ConvertSerializedTagMap(m_State.m_Tags, 2))

    # sb.append(ConvertSerializedShaderRTBlendState(m_State.rtBlend))

    if m_State.alphaToMask.val > 0:
        sb.append(" AlphaToMask On\n")

    if m_State.zClip and m_State.zClip.val != 1:
        sb.append(" ZClip Off\n")

    if m_State.zTest.val != 4:
        sb.append(" ZTest ")
        if m_State.zTest.val == 0:  # kFuncDisabled
            sb.append("Off")
        elif m_State.zTest.val == 1:  # kFuncNever
            sb.append("Never")
        elif m_State.zTest.val == 2:  # kFuncLess
            sb.append("Less")
        elif m_State.zTest.val == 3:  # kFuncEqual
            sb.append("Equal")
        elif m_State.zTest.val == 5:  # kFuncGreater
            sb.append("Greater")
        elif m_State.zTest.val == 6:  # kFuncNotEqual
            sb.append("NotEqual")
        elif m_State.zTest.val == 7:  # kFuncGEqual
            sb.append("GEqual")
        elif m_State.zTest.val == 8:  # kFuncAlways
            sb.append("Always")

        sb.append("\n")

    if m_State.zWrite.val != 1:  # ZWrite On
        sb.append(" ZWrite Off\n")

    if m_State.culling.val != 2:  # Cull Back
        sb.append(" Cull ")
        if m_State.culling.val == 0:  # kCullOff
            sb.append("Off")
        elif m_State.culling.val == 1:  # kCullFront
            sb.append("Front")

        sb.append("\n")

    if m_State.offsetFactor.val != 0 or m_State.offsetUnits.val != 0:
        sb.append(
            " Offset {0}, {1}\n".format(
                m_State.offsetFactor.val, m_State.offsetUnits.val
            )
        )

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


def ConvertSerializedTagMap(m_Tags: SerializedTagMap, intent: int) -> str:
    if m_Tags.tags:
        return "".join(
            [
                " " * intent,
                "Tags { ",
                *[f'"{key}" = "{value}" ' for key, value in m_Tags.tags],
                "}\n",
            ]
        )
    return ""


def ConvertSerializedProperties(m_PropInfo: SerializedProperties) -> str:
    return "\n".join(
        [
            "Properties {\n",
            *[ConvertSerializedProperty(m_Prop) for m_Prop in m_PropInfo.m_Props],
            "}\n",
        ]
    )


def ConvertSerializedProperty(m_Prop: SerializedProperty) -> str:
    sb = ["[{0}] ".format(m_Attribute) for m_Attribute in m_Prop.m_Attributes]
    sb.append('{0} ("{1}", '.format(m_Prop.m_Name, m_Prop.m_Description))

    if m_Prop.m_Type == SerializedPropertyType.kColor:
        sb.append("Color")
    elif m_Prop.m_Type == SerializedPropertyType.kVector:
        sb.append("Vector")
    elif m_Prop.m_Type == SerializedPropertyType.kFloat:
        sb.append("Float")
    elif m_Prop.m_Type == SerializedPropertyType.kRange:
        sb.append(
            "Range({0:g}, {1:g})".format(m_Prop.m_DefValue_1_, m_Prop.m_DefValue_2_)
        )
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

    if m_Prop.m_Type in [SerializedPropertyType.kColor, SerializedPropertyType.kVector]:
        sb.append(
            "({0:g},{1:g},{2:g},{3:g})".format(
                m_Prop.m_DefValue_0_,
                m_Prop.m_DefValue_1_,
                m_Prop.m_DefValue_2_,
                m_Prop.m_DefValue_3_,
            )
        )
    elif m_Prop.m_Type in [
        SerializedPropertyType.kFloat,
        SerializedPropertyType.kRange,
    ]:
        sb.append(m_Prop.m_DefValue_0_)
    elif m_Prop.m_Type == SerializedPropertyType.kTexture:
        sb.append('"{0}" {{ }}'.format(m_Prop.m_DefTexture.m_DefaultName))
    else:
        raise ValueError(m_Prop.m_Type)

    sb.append("\n")
    return "".join(map(str, sb))


def CheckGpuProgramUsable(platform: int, programType: int) -> bool:
    if platform == ShaderCompilerPlatform.kShaderCompPlatformGL:
        return programType == ShaderGpuProgramType.kShaderGpuProgramGLLegacy
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformD3D9:
        return (
            programType == ShaderGpuProgramType.kShaderGpuProgramDX9VertexSM20
            or programType == ShaderGpuProgramType.kShaderGpuProgramDX9VertexSM30
            or programType == ShaderGpuProgramType.kShaderGpuProgramDX9PixelSM20
            or programType == ShaderGpuProgramType.kShaderGpuProgramDX9PixelSM30
        )
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformXbox360:
        return (
            programType == ShaderGpuProgramType.kShaderGpuProgramConsoleVS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleFS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleHS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleDS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleGS
        )
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformD3D11:
        return (
            programType == ShaderGpuProgramType.kShaderGpuProgramDX11VertexSM40
            or programType == ShaderGpuProgramType.kShaderGpuProgramDX11VertexSM50
            or programType == ShaderGpuProgramType.kShaderGpuProgramDX11PixelSM40
            or programType == ShaderGpuProgramType.kShaderGpuProgramDX11PixelSM50
            or programType == ShaderGpuProgramType.kShaderGpuProgramDX11GeometrySM40
            or programType == ShaderGpuProgramType.kShaderGpuProgramDX11GeometrySM50
            or programType == ShaderGpuProgramType.kShaderGpuProgramDX11HullSM50
            or programType == ShaderGpuProgramType.kShaderGpuProgramDX11DomainSM50
        )
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformGLES20:
        return programType == ShaderGpuProgramType.kShaderGpuProgramGLES
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformNaCl:
        raise NotImplementedError
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformFlash:
        raise NotImplementedError
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformD3D11_9x:
        return (
            programType == ShaderGpuProgramType.kShaderGpuProgramDX10Level9Vertex
            or programType == ShaderGpuProgramType.kShaderGpuProgramDX10Level9Pixel
        )
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformGLES3Plus:
        return (
            programType == ShaderGpuProgramType.kShaderGpuProgramGLES31AEP
            or programType == ShaderGpuProgramType.kShaderGpuProgramGLES31
            or programType == ShaderGpuProgramType.kShaderGpuProgramGLES3
        )
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformPSP2:
        return (
            programType == ShaderGpuProgramType.kShaderGpuProgramConsoleVS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleFS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleHS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleDS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleGS
        )
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformPS4:
        return (
            programType == ShaderGpuProgramType.kShaderGpuProgramConsoleVS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleFS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleHS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleDS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleGS
        )
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformXboxOne:
        return (
            programType == ShaderGpuProgramType.kShaderGpuProgramConsoleVS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleFS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleHS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleDS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleGS
        )
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformPSM:
        raise NotImplementedError
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformMetal:
        return (
            programType == ShaderGpuProgramType.kShaderGpuProgramMetalVS
            or programType == ShaderGpuProgramType.kShaderGpuProgramMetalVS
        )
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformOpenGLCore:
        return (
            programType == ShaderGpuProgramType.kShaderGpuProgramGLCore32
            or programType == ShaderGpuProgramType.kShaderGpuProgramGLCore41
            or programType == ShaderGpuProgramType.kShaderGpuProgramGLCore43
        )
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformN3DS:
        return (
            programType == ShaderGpuProgramType.kShaderGpuProgramConsoleVS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleFS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleHS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleDS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleGS
        )
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformWiiU:
        return (
            programType == ShaderGpuProgramType.kShaderGpuProgramConsoleVS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleFS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleHS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleDS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleGS
        )
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformVulkan:
        return programType == ShaderGpuProgramType.kShaderGpuProgramSPIRV
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformSwitch:
        return (
            programType == ShaderGpuProgramType.kShaderGpuProgramConsoleVS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleFS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleHS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleDS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleGS
        )
    elif platform == ShaderCompilerPlatform.kShaderCompPlatformXboxOneD3D12:
        return (
            programType == ShaderGpuProgramType.kShaderGpuProgramConsoleVS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleFS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleHS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleDS
            or programType == ShaderGpuProgramType.kShaderGpuProgramConsoleGS
        )
    else:
        raise NotImplementedError


def GetPlatformString(platform: int):
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
    m_SubPrograms: List[ShaderSubProgram]

    def __init__(self, reader: EndianBinaryReader, version: Tuple[int, int, int, int]):
        subProgramCapacity = reader.read_int()
        self.m_SubPrograms = [None] * subProgramCapacity

        if version >= (2019, 3):  # 2019.3 and up
            entrySize = 12
        else:
            entrySize = 8

        for i in range(subProgramCapacity):
            reader.Position = 4 + i * entrySize
            offset = reader.read_int()
            reader.Position = offset
            self.m_SubPrograms[i] = ShaderSubProgram(reader)

    def Export(self, shader: str) -> str:
        shader = re.sub(
            r"GpuProgramIndex (.+)",
            lambda math: self.m_SubPrograms[int(math.group(1))].Export(),
            shader,
        )

        return shader


class ShaderSubProgram:
    m_Version: int
    m_ProgramCode: ShaderGpuProgramType
    m_Keywords: List[str]
    m_ProgramCode: List[bytes]
    m_LocalKeywords: Optional[List[str]]

    def __init__(self, reader: EndianBinaryReader):
        # LoadGpuProgramFromData
        # 201509030 - Unity 5.3
        # 201510240 - Unity 5.4
        # 201608170 - Unity 5.5
        # 201609010 - Unity 5.6, 2017.1 & 2017.2
        # 201708220 - Unity 2017.3, Unity 2017.4 & Unity 2018.1
        # 201802150 - Unity 2018.2 & Unity 2018.3
        # 201806140 - Unity 2019.1~2020.1
        # 202012090 - Unity 2021.2

        self.m_Version = reader.read_int()
        self.m_ProgramType = ShaderGpuProgramType(reader.read_int())
        reader.Position += 12

        if self.m_Version >= 201608170:
            reader.Position += 4

        m_KeywordSize = reader.read_int()
        self.m_Keywords = [reader.read_aligned_string() for _ in range(m_KeywordSize)]

        if 201806140 <= self.m_Version < 202012090:
            m_LocalKeywordsSize = reader.read_int()
            self.m_LocalKeywords = [
                reader.read_aligned_string() for _ in range(m_LocalKeywordsSize)
            ]
        else:
            self.m_LocalKeywords = None

        self.m_ProgramCode = reader.read_byte_array()
        reader.align_stream()

    def Export(self) -> str:
        sb = []

        if len(self.m_Keywords) > 0:
            sb.append("Keywords { ")
            for keyword in self.m_Keywords:
                sb.append('"{0}" '.format(keyword))

            sb.append("}\n")

        if (
            getattr(self, "m_LocalKeywords") is not None
            and len(self.m_LocalKeywords) > 0
        ):
            sb.append("Local Keywords { ")
            for keyword in self.m_LocalKeywords:
                sb.append('"{0}" '.format(keyword))

            sb.append("}\n")

        sb.append('"')

        if len(self.m_ProgramCode) > 0:
            if self.m_ProgramType in [
                ShaderGpuProgramType.kShaderGpuProgramGLLegacy,
                ShaderGpuProgramType.kShaderGpuProgramGLES31AEP,
                ShaderGpuProgramType.kShaderGpuProgramGLES31,
                ShaderGpuProgramType.kShaderGpuProgramGLES3,
                ShaderGpuProgramType.kShaderGpuProgramGLES,
                ShaderGpuProgramType.kShaderGpuProgramGLCore32,
                ShaderGpuProgramType.kShaderGpuProgramGLCore41,
                ShaderGpuProgramType.kShaderGpuProgramGLCore43,
            ]:
                sb.append(bytes(self.m_ProgramCode).decode("utf8"))
            elif self.m_ProgramType in [
                ShaderGpuProgramType.kShaderGpuProgramDX9VertexSM20,
                ShaderGpuProgramType.kShaderGpuProgramDX9VertexSM30,
                ShaderGpuProgramType.kShaderGpuProgramDX9PixelSM20,
                ShaderGpuProgramType.kShaderGpuProgramDX9PixelSM30,
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
                ShaderGpuProgramType.kShaderGpuProgramDX11DomainSM50,
            ]:
                sb.append("// shader disassembly not supported on DXBC")
            elif self.m_ProgramType in [
                ShaderGpuProgramType.kShaderGpuProgramMetalVS,
                ShaderGpuProgramType.kShaderGpuProgramMetalFS,
            ]:
                reader = EndianBinaryReader(self.m_ProgramCode, endian="<")
                fourCC = reader.read_u_int()
                if fourCC == 0xF00DCAFE:
                    offset = reader.read_int()
                    reader.Position = offset

                _entryName = reader.read_string_to_null()
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
                ShaderGpuProgramType.kShaderGpuProgramConsoleGS,
            ]:
                sb.append(bytes(self.m_ProgramCode).decode("utf8"))
            else:
                sb.append(
                    "//shader disassembly not supported on {0}".format(
                        self.m_ProgramType
                    )
                )

        sb.append('"')
        return "".join(sb)
