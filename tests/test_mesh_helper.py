import os
import struct
from types import SimpleNamespace

import pytest

import UnityPy
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
from UnityPy.export.MeshExporter import export_mesh_obj
from UnityPy.helpers import MeshHelper
from UnityPy.helpers.MeshHelper import MeshHandler

SAMPLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")


def load_mesh():
    env = UnityPy.load(os.path.join(SAMPLES, "xinzexi_2_n_tex"))
    return next(obj.parse_as_object() for obj in env.objects if obj.type.name == "Mesh")


def triangles(mesh):
    handler = MeshHandler(mesh)
    handler.process()
    return handler.get_triangles()


def test_mesh_without_submeshes_and_indices():
    # vertices only, as in a placeholder mesh
    mesh = load_mesh()
    mesh.m_IndexBuffer = []
    mesh.m_SubMeshes = []
    assert triangles(mesh) == []
    obj = mesh.export()
    assert "\nv " in obj or obj.startswith("v ")
    assert "\nf " not in obj


def test_mesh_with_empty_submeshes_and_no_indices():
    mesh = load_mesh()
    mesh.m_IndexBuffer = []
    for submesh in mesh.m_SubMeshes:
        submesh.firstByte = 0
        submesh.indexCount = 0
    assert triangles(mesh) == [[] for _ in mesh.m_SubMeshes]


def build_normalized_channel_mesh():
    # one vertex: Float x3 position, UNorm8 x4 color, UNorm16 x2 uv0, SNorm16 x2 uv1
    vertex = struct.pack(
        "<3f4B2H2h", 0, 0, 0, 255, 128, 0, 255, 65535, 32768, -32767, 16384
    )
    # VertexFormat since 2019: 0 Float, 2 UNorm8, 4 UNorm16, 5 SNorm16
    channels = [
        ChannelInfo(dimension=3, format=0, offset=0, stream=0),  # position
        ChannelInfo(dimension=0, format=0, offset=0, stream=0),  # normal
        ChannelInfo(dimension=0, format=0, offset=0, stream=0),  # tangent
        ChannelInfo(dimension=4, format=2, offset=12, stream=0),  # color
        ChannelInfo(dimension=2, format=4, offset=16, stream=0),  # uv0
        ChannelInfo(dimension=2, format=5, offset=20, stream=0),  # uv1
    ]
    empty = PackedBitVector(m_Data=[], m_NumItems=0)
    names = (
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
    aabb = AABB(m_Center=Vector3f(0, 0, 0), m_Extent=Vector3f(1, 1, 1))
    mesh = Mesh(
        m_BindPose=[],
        m_CompressedMesh=CompressedMesh(**{name: empty for name in names}),
        m_IndexBuffer=[],
        m_IndexFormat=0,
        m_LocalAABB=aabb,
        m_MeshCompression=0,
        m_Name="mesh",
        m_SubMeshes=[
            SubMesh(
                firstByte=0,
                firstVertex=0,
                indexCount=0,
                localAABB=aabb,
                vertexCount=1,
                baseVertex=0,
                topology=0,
            )
        ],
        m_VertexData=VertexData(m_DataSize=vertex, m_VertexCount=1, m_Channels=channels),
    )
    mesh.object_reader = SimpleNamespace(version=(2021, 3, 0, 0))
    return mesh


@pytest.mark.parametrize("use_boost", [True, False])
def test_normalized_vertex_channels_are_returned_as_floats(monkeypatch, use_boost):
    if not use_boost:
        monkeypatch.setattr(MeshHelper, "UnityPyBoost", None)
    mesh = build_normalized_channel_mesh()
    handler = MeshHandler(mesh)
    handler.process()
    assert handler.m_Colors == [(1.0, 128 / 255, 0.0, 1.0)]
    assert handler.m_UV0 == [(1.0, 32768 / 65535)]
    assert handler.m_UV1 == [(-1.0, 16384 / 32767)]
    obj = export_mesh_obj(mesh)
    assert "vt 65535 32768" not in obj


def test_mesh_with_submesh_indices_but_no_index_buffer():
    mesh = load_mesh()
    assert any(submesh.indexCount for submesh in mesh.m_SubMeshes)
    mesh.m_IndexBuffer = []
    with pytest.raises(ValueError):
        triangles(mesh)
