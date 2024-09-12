from ..generated import Renderer


def export(self, export_dir: str) -> None:
    from ...export import MeshRendererExporter

    MeshRendererExporter.export_mesh_renderer(self, export_dir)


Renderer.export = export

__all__ = ("Renderer",)
