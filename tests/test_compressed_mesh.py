from types import SimpleNamespace

import pytest

from UnityPy.classes.generated import (
    AABB,
    ChannelInfo,
    CompressedMesh,
    Mesh,
    PackedBitVector,
    Vector3f,
    VertexData,
)
from UnityPy.helpers.MeshHelper import MeshHandler

VERSION = (2021, 3, 0, 0)


def pack_ints(values, bit_size):
    data = bytearray((len(values) * bit_size + 7) // 8)
    for i, value in enumerate(values):
        for bit in range(bit_size):
            if value >> bit & 1:
                pos = i * bit_size + bit
                data[pos // 8] |= 1 << (pos % 8)
    return PackedBitVector(m_Data=list(data), m_NumItems=len(values), m_BitSize=bit_size)


def pack_floats(values, bit_size, start=0.0, range_=1.0):
    top = (1 << bit_size) - 1
    packed = pack_ints([round((value - start) / range_ * top) for value in values], bit_size)
    packed.m_Start = start
    packed.m_Range = range_
    return packed


def compressed_mesh(vertex_count, m_UVInfo=0, **vectors):
    names = (
        "m_BoneIndices",
        "m_NormalSigns",
        "m_Normals",
        "m_TangentSigns",
        "m_Tangents",
        "m_Triangles",
        "m_UV",
        "m_Weights",
    )
    compressed = CompressedMesh(
        m_Vertices=pack_floats([0.0] * vertex_count * 3, 8),
        m_UVInfo=m_UVInfo,
        **{name: vectors.get(name, PackedBitVector(m_Data=[], m_NumItems=0)) for name in names},
    )
    mesh = Mesh(
        m_BindPose=[],
        m_CompressedMesh=compressed,
        m_IndexBuffer=[],
        m_IndexFormat=0,
        m_LocalAABB=AABB(m_Center=Vector3f(0, 0, 0), m_Extent=Vector3f(1, 1, 1)),
        m_MeshCompression=1,
        m_Name="mesh",
        m_SubMeshes=[],
        m_VertexData=VertexData(
            m_DataSize=b"",
            m_VertexCount=0,
            m_Channels=[ChannelInfo(dimension=0, format=0, offset=0, stream=0)],
        ),
    )
    mesh.object_reader = SimpleNamespace(version=VERSION)
    handler = MeshHandler(mesh)
    handler.process()
    return handler


def test_compressed_bone_weights():
    # vertex 0: three weights that do not reach 31/31, so the fourth weight is implied
    # vertex 1: one weight of 31/31, the remaining influences are empty
    handler = compressed_mesh(
        2,
        m_Weights=pack_ints([10, 10, 5, 31], 5),
        m_BoneIndices=pack_ints([0, 1, 2, 3, 7], 4),
    )
    expected = [(10 / 31, 10 / 31, 5 / 31, 6 / 31), (1.0, 0, 0, 0)]
    assert len(handler.m_BoneWeights) == len(expected)
    for weights, expected_weights in zip(handler.m_BoneWeights, expected):
        assert weights == pytest.approx(expected_weights)
        assert sum(weights) == pytest.approx(1.0)
    assert handler.m_BoneIndices == [(0, 1, 2, 3), (7, 0, 0, 0)]
