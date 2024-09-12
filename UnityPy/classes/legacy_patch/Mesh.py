from ..generated import Mesh


def _Mesh_export(self: Mesh, format: str = "obj"):
    from ...export.MeshExporter import export_mesh

    return export_mesh(self, format)


Mesh.export = _Mesh_export


__all__ = ("Mesh",)
