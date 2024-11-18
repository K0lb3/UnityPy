from typing import List, Tuple, Union

from UnityPy.classes import Component, PPtr
from UnityPy.classes.generated import ComponentPair, EditorExtension

class GameObject(EditorExtension):
  m_Component: Union[List[ComponentPair], List[Tuple[int, PPtr[Component]]]]
  m_IsActive: Union[bool, int]
  m_Layer: int
  m_Name: str
  m_Tag: int

  @property
  def m_Components(self) -> List[PPtr[Component]]: ...
  @property
  def m_Animator(self) -> Union[PPtr[Component], None]: ...
  @property
  def m_Animation(self) -> Union[PPtr[Component], None]: ...
  @property
  def m_Transform(self) -> Union[PPtr[Component], None]: ...
  @property
  def m_SkinnedMeshRenderer(self) -> Union[PPtr[Component], None]: ...
  @property
  def m_MeshRenderer(self) -> Union[PPtr[Component], None]: ...
  @property
  def m_MeshFilter(self) -> Union[PPtr[Component], None]: ...
