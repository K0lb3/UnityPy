from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from ..helpers.MeshHelper import MeshHandler

if TYPE_CHECKING:
    from ..classes.generated import Mesh


def export_mesh(m_Mesh: Mesh, format: str = "obj") -> str:
    if format == "obj":
        return export_mesh_obj(m_Mesh)
    raise NotImplementedError(f"Export format {format} not implemented")


def export_mesh_obj(mesh: Mesh, material_names: Optional[List[str]] = None) -> str:
    handler = MeshHandler(mesh)
    handler.process()

    m_Mesh = handler
    if m_Mesh.m_VertexCount <= 0:
        return False

    sb = [f"g {mesh.m_Name}\n"]
    if material_names:
        sb.append(f"mtllib {mesh.m_Name}.mtl\n")
    # region Vertices
    if not m_Mesh.m_Vertices:
        return False

    sb.extend(
        "v {0:.9G} {1:.9G} {2:.9G}\n".format(-pos[0], pos[1], pos[2]).replace(
            "nan", "0"
        )
        for pos in m_Mesh.m_Vertices
    )
    # endregion

    # region UV
    if m_Mesh.m_UV0:
        sb.extend(
            "vt {0:.9G} {1:.9G}\n".format(uv[0], uv[1]).replace("nan", "0")
            for uv in m_Mesh.m_UV0
        )
    # endregion

    # region Normals
    if m_Mesh.m_Normals:
        sb.extend(
            "vn {0:.9G} {1:.9G} {2:.9G}\n".format(-n[0], n[1], n[2]).replace("nan", "0")
            for n in m_Mesh.m_Normals
        )
    # endregion

    # region Face
    for i, triangles in enumerate(m_Mesh.get_triangles()):
        sb.append(f"g {mesh.m_Name}_{i}\n")
        if material_names and i < len(material_names) and material_names[i]:
            sb.append(f"usemtl {material_names[i]}\n")
        sb.extend(
            "f {0}/{0}/{0} {1}/{1}/{1} {2}/{2}/{2}\n".format(c + 1, b + 1, a + 1)
            for a, b, c in triangles
        )
    # endregion
    return "".join(sb)
