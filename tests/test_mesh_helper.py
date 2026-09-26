import os

import pytest

import UnityPy
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


def test_mesh_with_submesh_indices_but_no_index_buffer():
    mesh = load_mesh()
    assert any(submesh.indexCount for submesh in mesh.m_SubMeshes)
    mesh.m_IndexBuffer = []
    with pytest.raises(ValueError):
        triangles(mesh)
