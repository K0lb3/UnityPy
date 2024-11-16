from typing import List, Tuple, Union

from UnityPy.classes import Component, PPtr
from UnityPy.classes.generated import ComponentPair, EditorExtension
from UnityPy.enums import ClassIDType

def _GameObject_Components(self) -> List[PPtr[Component]]: ...
def _GameObject_GetComponent(self, type: ClassIDType) -> Union[PPtr[Component], None]: ...

class GameObject(EditorExtension):
  m_Component: Union[List[ComponentPair], List[Tuple[int, PPtr[Component]]]]
  m_IsActive: Union[bool, int]
  m_Layer: int
  m_Name: str
  m_Tag: int
  m_Components = property(_GameObject_Components)
  m_Animator = property(
      lambda self: _GameObject_GetComponent(self, ClassIDType.Animator)
  )
  m_Animation = property(
      lambda self: _GameObject_GetComponent(self, ClassIDType.Animation)
  )
  m_Transform = property(
      lambda self: _GameObject_GetComponent(self, ClassIDType.Transform)
  )
  m_MeshRenderer = property(
      lambda self: _GameObject_GetComponent(self, ClassIDType.MeshRenderer)
  )
  m_SkinnedMeshRenderer = property(
      lambda self: _GameObject_GetComponent(self, ClassIDType.SkinnedMeshRenderer)
  )
  m_MeshFilter = property(
      lambda self: _GameObject_GetComponent(self, ClassIDType.MeshFilter)
  )
  ...
