import struct
from types import SimpleNamespace

import pytest

from UnityPy.classes.generated import (
    AABB,
    ChannelInfo,
    CompressedMesh,
    Mesh,
    PackedBitVector,
    SubMesh,
    Vector3f,
    VertexData,
)
from UnityPy.enums.MeshTopology import MeshTopology
from UnityPy.export.MeshExporter import export_mesh_obj
from UnityPy.helpers.MeshHelper import MeshHandler

VERSION = (2021, 3, 0, 0)
VERTEX_COUNT = 12


def bounds():
    return AABB(m_Center=Vector3f(0, 0, 0), m_Extent=Vector3f(12, 1, 1))


def submesh(index_bits, first_index, count, topology=MeshTopology.Triangles, base_vertex=0):
    return SubMesh(
        firstByte=first_index * (index_bits // 8),
        firstVertex=0,
        indexCount=count,
        localAABB=bounds(),
        vertexCount=VERTEX_COUNT,
        baseVertex=base_vertex,
        topology=topology,
    )


def mesh(index_bits, indices, submeshes):
    compressed = CompressedMesh(
        **{
            name: PackedBitVector(m_Data=[], m_NumItems=0)
            for name in (
                "m_BoneIndices",
                "m_NormalSigns",
                "m_Normals",
                "m_TangentSigns",
                "m_Tangents",
                "m_Triangles",
                "m_UV",
                "m_Vertices",
                "m_Weights",
            )
        }
    )
    vertices = b"".join(struct.pack("<8f", i, i % 2, 0, 0, 0, 1, i / VERTEX_COUNT, 0) for i in range(VERTEX_COUNT))
    result = Mesh(
        m_BindPose=[],
        m_CompressedMesh=compressed,
        m_IndexBuffer=list(struct.pack(f"<{len(indices)}{'H' if index_bits == 16 else 'I'}", *indices)),
        m_IndexFormat=0 if index_bits == 16 else 1,
        m_LocalAABB=bounds(),
        m_MeshCompression=0,
        m_Name="mesh",
        m_SubMeshes=submeshes,
        m_VertexData=VertexData(
            m_DataSize=vertices,
            m_VertexCount=VERTEX_COUNT,
            m_Channels=[
                ChannelInfo(dimension=3, format=0, offset=0, stream=0),
                ChannelInfo(dimension=3, format=0, offset=12, stream=0),
                ChannelInfo(dimension=0, format=0, offset=0, stream=0),
                ChannelInfo(dimension=0, format=0, offset=0, stream=0),
                ChannelInfo(dimension=2, format=0, offset=24, stream=0),
            ],
        ),
    )
    result.object_reader = SimpleNamespace(version=VERSION)
    return result


def handler_for(source):
    handler = MeshHandler(source)
    handler.process()
    return handler


@pytest.mark.parametrize("index_bits", [16, 32])
@pytest.mark.parametrize("base_vertex, expected", [(0, [(0, 1, 2)]), (None, [(0, 1, 2)]), (5, [(5, 6, 7)])])
def test_base_vertex_and_first_byte(index_bits, base_vertex, expected):
    indices = [9, 10, 11, 0, 1, 2]
    source = mesh(index_bits, indices, [submesh(index_bits, 3, 3, base_vertex=base_vertex)])
    handler = handler_for(source)

    assert handler.get_triangles() == [expected]
    assert handler.m_IndexBuffer == tuple(indices)


@pytest.mark.parametrize("index_bits", [16, 32])
@pytest.mark.parametrize(
    "topology, indices, expected",
    [
        (MeshTopology.Triangles, [0, 1, 2, 2, 3, 0], [(5, 6, 7), (7, 8, 5)]),
        (MeshTopology.Quads, [0, 1, 2, 3], [(5, 6, 7), (5, 7, 8)]),
        (MeshTopology.TriangleStrip, [0, 1, 2, 2, 3, 4, 5], [(5, 6, 7), (8, 7, 9), (8, 9, 10)]),
    ],
)
def test_base_vertex_preserves_topology_conversion(index_bits, topology, indices, expected):
    source = mesh(
        index_bits,
        [11, 11, 11] + indices,
        [submesh(index_bits, 3, len(indices), topology, base_vertex=5)],
    )
    assert handler_for(source).get_triangles() == [expected]


def test_submesh_without_base_vertex():
    source = mesh(16, [0, 1, 2], [SimpleNamespace(firstByte=0, indexCount=3, topology=MeshTopology.Triangles)])
    assert handler_for(source).get_triangles() == [[(0, 1, 2)]]


def test_base_vertex_is_applied_independently_to_each_submesh():
    source = mesh(16, [0, 1, 2], [submesh(16, 0, 3), submesh(16, 0, 3, base_vertex=5)])
    handler = handler_for(source)

    assert handler.get_triangles() == [[(0, 1, 2)], [(5, 6, 7)]]
    assert handler.get_triangles() == [[(0, 1, 2)], [(5, 6, 7)]]
    assert handler.m_IndexBuffer == (0, 1, 2)


@pytest.mark.parametrize("index_bits", [16, 32])
def test_obj_faces_reference_vertices_after_base_vertex(index_bits):
    source = mesh(index_bits, [9, 10, 11, 0, 1, 2], [submesh(index_bits, 3, 3, base_vertex=5)])
    lines = export_mesh_obj(source).splitlines()
    faces = [line for line in lines if line.startswith("f ")]
    vertices = [line for line in lines if line.startswith("v ")]

    assert faces == ["f 8/8/8 7/7/7 6/6/6"]
    referenced_vertices = [vertices[int(reference.split("/")[0]) - 1] for reference in faces[0].split()[1:]]
    assert referenced_vertices == ["v -7 1 0", "v -6 0 0", "v -5 1 0"]


def test_16_bit_indices_address_vertices_above_65535():
    source = mesh(16, [0, 1, 2], [submesh(16, 0, 3, base_vertex=65536)])
    prefix = struct.pack("<8f", 0, 0, 0, 0, 0, 1, 0, 0) * 65536
    selected = b"".join(struct.pack("<8f", x, y, 0, 0, 0, 1, 0, 0) for x, y in [(31, 1), (32, 0), (33, 1)])
    source.m_VertexData.m_DataSize = prefix + selected
    source.m_VertexData.m_VertexCount = 65539
    source.m_SubMeshes[0].firstVertex = 65536
    source.m_SubMeshes[0].vertexCount = 3
    source.m_LocalAABB = AABB(m_Center=Vector3f(16.5, 0.5, 0), m_Extent=Vector3f(16.5, 0.5, 0))
    source.m_SubMeshes[0].localAABB = AABB(m_Center=Vector3f(32, 0.5, 0), m_Extent=Vector3f(1, 0.5, 0))

    handler = handler_for(source)
    assert handler.m_Use16BitIndices is True
    assert handler.m_IndexBuffer == (0, 1, 2)
    assert handler.get_triangles() == [[(65536, 65537, 65538)]]
    lines = export_mesh_obj(source).splitlines()
    assert [line for line in lines if line.startswith("f ")] == [
        "f 65539/65539/65539 65538/65538/65538 65537/65537/65537"
    ]
    assert [line for line in lines if line.startswith("v ")][-3:] == ["v -31 1 0", "v -32 0 0", "v -33 1 0"]


@pytest.mark.parametrize("index_bits", [16, 32])
def test_compressed_indices_receive_base_vertex(index_bits):
    source = mesh(index_bits, [], [submesh(index_bits, 0, 3, base_vertex=5)])
    source.m_MeshCompression = 1
    # Three unsigned 3-bit values [0, 1, 2], packed from the least significant bit.
    source.m_CompressedMesh.m_Triangles = PackedBitVector(m_Data=[0x88, 0x00], m_NumItems=3, m_BitSize=3)

    handler = handler_for(source)
    assert source.m_IndexBuffer == []
    assert handler.m_IndexBuffer == [0, 1, 2]
    assert handler.get_triangles() == [[(5, 6, 7)]]
    assert "f 8/8/8 7/7/7 6/6/6\n" in export_mesh_obj(source)
