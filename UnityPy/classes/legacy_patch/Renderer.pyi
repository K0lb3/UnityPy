from UnityPy.classes import PPtr
from UnityPy.classes.generated import Component
from UnityPy.classes.legacy_patch import GameObject

class Renderer(Component):
  m_GameObject: PPtr[GameObject]

  def export(self, export_dir: str) -> None: ...
