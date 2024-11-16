from UnityPy.classes import PPtr
from UnityPy.classes.generated import Component
from UnityPy.classes.legacy_patch import GameObject


def export(self, export_dir: str) -> None: ...

_Renderer_export = export

class Renderer(Component):
  m_GameObject: PPtr[GameObject]
  export = _Renderer_export
  ...
