from ..generated import Shader


def _Shader_export(self: Shader) -> str:
    from ...export.ShaderConverter import export_shader

    return export_shader(self)


Shader.export = _Shader_export

__all__ = ("Shader",)
