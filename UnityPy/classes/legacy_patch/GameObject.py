from __future__ import annotations

from typing import List, Union

from ...enums import ClassIDType
from ..generated import Component, GameObject, PPtr


def _GameObject_Components(self) -> List[PPtr[Component]]:
    if self.m_Component is None:
        return []
    if isinstance(self.m_Component[0], tuple):
        return [c.m_GameObject for i, c in self.m_Component]
    else:
        return [c.component for c in self.m_Component]


def _GameObject_GetComponent(self, type: ClassIDType) -> Union[PPtr[Component], None]:
    for component in self.m_Components:
        if component.type == type:
            return component
    return None


GameObject.m_Components = property(_GameObject_Components)
GameObject.m_Animator = property(
    lambda self: _GameObject_GetComponent(self, ClassIDType.Animator)
)
GameObject.m_Animation = property(
    lambda self: _GameObject_GetComponent(self, ClassIDType.Animation)
)
GameObject.m_Transform = property(
    lambda self: _GameObject_GetComponent(self, ClassIDType.Transform)
)
GameObject.m_MeshRenderer = property(
    lambda self: _GameObject_GetComponent(self, ClassIDType.MeshRenderer)
)
GameObject.m_SkinnedMeshRenderer = property(
    lambda self: _GameObject_GetComponent(self, ClassIDType.SkinnedMeshRenderer)
)
GameObject.m_MeshFilter = property(
    lambda self: _GameObject_GetComponent(self, ClassIDType.MeshFilter)
)
