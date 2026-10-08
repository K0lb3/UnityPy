"""Synthetic shader records exercise decompression, parsing and text export."""

import io
import struct
from types import SimpleNamespace

import lz4.block
import pytest

from UnityPy.enums import PassType, ShaderCompilerPlatform, ShaderGpuProgramType
from UnityPy.export.ShaderConverter import ShaderProgram, export_shader
from UnityPy.streams import EndianBinaryReader


def aligned_string(value):
    data = value.encode("utf8")
    return struct.pack("<i", len(data)) + data + bytes(-len(data) % 4)


def program_record(code, record_version, program_type=ShaderGpuProgramType.kShaderGpuProgramGLES3):
    data = struct.pack("<5i", record_version, program_type, 0, 0, 0)
    if record_version >= 201608170:
        data += struct.pack("<i", 0)
    data += struct.pack("<i", 1) + aligned_string("SYNTHETIC_GLOBAL")
    if 201806140 <= record_version < 202012090:
        data += struct.pack("<i", 1) + aligned_string("SYNTHETIC_LOCAL")
    data += struct.pack("<i", len(code)) + code
    return data + bytes(-len(data) % 4)


def entry_table(entries, version):
    data = struct.pack("<i", len(entries))
    for offset, length, segment in entries:
        data += struct.pack("<ii", offset, length)
        if version >= (2019, 3):
            data += struct.pack("<i", segment)
    return data


def single_segment(record, version, copies=1):
    header_size = 4 + copies * (12 if version >= (2019, 3) else 8)
    entries = [(header_size, len(record), 0)] * copies
    return entry_table(entries, version) + record


def shader(segments, version, program_count, nested=True):
    offsets, compressed_sizes, decompressed_sizes = [], [], []
    payload = b"prefix"
    for segment in segments:
        compressed = lz4.block.compress(segment, store_size=False)
        offsets.append(len(payload))
        compressed_sizes.append(len(compressed))
        decompressed_sizes.append(len(segment))
        payload += compressed + b"gap"

    tags = SimpleNamespace(tags=[])
    state = SimpleNamespace(
        m_Name="",
        m_LOD=0,
        m_Tags=tags,
        alphaToMask=SimpleNamespace(val=0),
        zClip=SimpleNamespace(val=1),
        zTest=SimpleNamespace(val=4),
        zWrite=SimpleNamespace(val=1),
        culling=SimpleNamespace(val=2),
        offsetFactor=SimpleNamespace(val=0),
        offsetUnits=SimpleNamespace(val=0),
        lighting=False,
        gpuProgramID=0,
    )
    subprograms = [
        SimpleNamespace(
            m_BlobIndex=index,
            m_GpuProgramType=ShaderGpuProgramType.kShaderGpuProgramGLES3,
            m_ShaderHardwareTier=0,
        )
        for index in range(program_count)
    ]
    empty_program = SimpleNamespace(m_SubPrograms=[])
    shader_pass = SimpleNamespace(
        m_Type=PassType.kPassTypeNormal,
        m_State=state,
        progVertex=SimpleNamespace(m_SubPrograms=subprograms),
        progFragment=empty_program,
        progGeometry=empty_program,
        progHull=empty_program,
        progDomain=empty_program,
    )
    parsed_form = SimpleNamespace(
        m_Name="SyntheticShader",
        m_PropInfo=SimpleNamespace(m_Props=[]),
        m_SubShaders=[SimpleNamespace(m_LOD=0, m_Tags=tags, m_Passes=[shader_pass])],
        m_FallbackName="",
        m_CustomEditorName="",
    )
    return SimpleNamespace(
        m_SubProgramBlob=None,
        compressedBlob=payload,
        platforms=[ShaderCompilerPlatform.kShaderCompPlatformGLES3Plus],
        offsets=[offsets] if nested else offsets,
        compressedLengths=[compressed_sizes] if nested else compressed_sizes,
        decompressedLengths=[decompressed_sizes] if nested else decompressed_sizes,
        object_reader=SimpleNamespace(version=version),
        m_ParsedForm=parsed_form,
    )


@pytest.mark.parametrize(
    "version,record_version",
    [
        ((5, 3, 0, 0), 201509030),
        ((2018, 4, 0, 0), 201802150),
        ((2019, 2, 0, 0), 201806140),
        ((2019, 3, 0, 0), 201806140),
        ((2022, 3, 0, 0), 202012090),
    ],
)
def test_single_reader_constructor_preserves_entry_layouts(version, record_version):
    code = b"void single_segment() {}"
    data = single_segment(program_record(code, record_version), version)
    program = ShaderProgram(EndianBinaryReader(data, endian="<"), version)
    subprogram = program.m_SubPrograms[0]
    assert subprogram.m_ProgramCode == code
    assert subprogram.m_Keywords == ["SYNTHETIC_GLOBAL"]
    assert subprogram.m_LocalKeywords == (["SYNTHETIC_LOCAL"] if record_version == 201806140 else None)
    assert code.decode() in program.Export("GpuProgramIndex 0")


@pytest.mark.parametrize(
    "version,record_version,nested",
    [
        ((2018, 4, 0, 0), 201802150, False),
        ((2019, 3, 0, 0), 201806140, True),
        ((2022, 3, 0, 0), 202012090, True),
    ],
)
def test_single_segment_shader_export(version, record_version, nested):
    code = b"void single_export() {}"
    segment = single_segment(program_record(code, record_version), version)
    text = export_shader(shader([segment], version, 1, nested=nested))
    assert 'Shader "SyntheticShader"' in text
    assert text.count(code.decode()) == 1


@pytest.mark.parametrize("version,record_version", [((2019, 3, 0, 0), 201806140), ((2022, 3, 0, 0), 202012090)])
def test_shader_export_reads_segment_local_offsets_in_index_order(version, record_version):
    codes = [
        b"void third_segment() {}",
        b"void table_segment() {}",
        b"void second_segment() {}",
        b"void second_segment_later() {}",
    ]
    records = [program_record(code, record_version) for code in codes]
    header_size = 4 + 4 * 12
    table = entry_table(
        [
            (0, len(records[0]), 2),
            (header_size, len(records[1]), 0),
            (0, len(records[2]), 1),
            (len(records[2]), len(records[3]), 1),
        ],
        version,
    )
    segments = [table + records[1], records[2] + records[3], records[0]]
    text = export_shader(shader(segments, version, 4))
    assert all(text.count(code.decode()) == 1 for code in codes)
    positions = [text.index(code.decode()) for code in codes]
    assert positions == sorted(positions)


def test_shader_export_keeps_platform_segment_lists_separate():
    version = (2022, 3, 0, 0)
    gles_code, glcore_code = b"void gles_program() {}", b"void glcore_program() {}"
    gles_record = program_record(gles_code, 202012090)
    glcore_record = program_record(glcore_code, 202012090, ShaderGpuProgramType.kShaderGpuProgramGLCore32)
    first = shader([entry_table([(0, len(gles_record), 1)], version), gles_record], version, 1)
    second = shader([entry_table([(0, len(glcore_record), 1)], version), glcore_record], version, 1)
    first.offsets.append([offset + len(first.compressedBlob) for offset in second.offsets[0]])
    first.compressedBlob += second.compressedBlob
    first.compressedLengths.extend(second.compressedLengths)
    first.decompressedLengths.extend(second.decompressedLengths)
    first.platforms.append(ShaderCompilerPlatform.kShaderCompPlatformOpenGLCore)
    first.m_ParsedForm.m_SubShaders[0].m_Passes[0].progVertex.m_SubPrograms.append(
        SimpleNamespace(
            m_BlobIndex=0,
            m_GpuProgramType=ShaderGpuProgramType.kShaderGpuProgramGLCore32,
            m_ShaderHardwareTier=0,
        )
    )
    text = export_shader(first)
    assert text.count(gles_code.decode()) == 1
    assert text.count(glcore_code.decode()) == 1


def test_entries_may_share_a_program_record():
    version = (2019, 3, 0, 0)
    code = b"void shared_program() {}"
    segment = single_segment(program_record(code, 201806140), version, copies=2)
    program = ShaderProgram(EndianBinaryReader(segment, endian="<"), version)
    assert [subprogram.m_ProgramCode for subprogram in program.m_SubPrograms] == [code, code]


@pytest.mark.parametrize("stream_backed", [False, True])
def test_shared_record_in_nonzero_segment_with_reader_backends(stream_backed):
    version = (2022, 3, 0, 0)
    code = b"void shared_nonzero_record() {}"
    record = program_record(code, 202012090)
    table = entry_table([(4, len(record), 2), (4, len(record), 2)], version)
    segments = [table, b"unused", b"pad!" + record]
    readers = [EndianBinaryReader(io.BytesIO(part) if stream_backed else part, endian="<") for part in segments]
    program = ShaderProgram(readers[0], version, readers)

    assert [item.m_ProgramCode for item in program.m_SubPrograms] == [code, code]
    assert [item.m_Keywords for item in program.m_SubPrograms] == [["SYNTHETIC_GLOBAL"], ["SYNTHETIC_GLOBAL"]]
    text = program.Export("GpuProgramIndex 0\nGpuProgramIndex 1")
    assert text.count(code.decode()) == 2


@pytest.mark.parametrize("segment", [-1, 1])
def test_unavailable_segment_is_reported(segment):
    version = (2019, 3, 0, 0)
    table = entry_table([(0, 4, segment)], version)
    with pytest.raises(ValueError, match=f"missing segment {segment}"):
        ShaderProgram(EndianBinaryReader(table, endian="<"), version)


@pytest.mark.parametrize("field", ["offsets", "compressedLengths", "decompressedLengths"])
def test_mismatched_segment_arrays_are_not_silently_truncated(field):
    version = (2019, 3, 0, 0)
    record = program_record(b"void incomplete_metadata() {}", 201806140)
    source = shader([entry_table([(0, len(record), 1)], version), record], version, 1)
    getattr(source, field)[0].pop()
    with pytest.raises(ValueError, match="inconsistent segment arrays"):
        export_shader(source)
