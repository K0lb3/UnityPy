from typing import List, Optional, Tuple

from PIL.Image import Image

from UnityPy.classes import PPtr
from UnityPy.classes.generated import (GUID, MonoBehaviour, NamedObject, Rectf,
                                       SpriteAtlas, SpriteBone,
                                       SpriteRenderData)
from UnityPy.classes.math import Vector2f, Vector4f

class Sprite(NamedObject):
  m_Extrude: int
  m_Name: str
  m_Offset: Vector2f
  m_PixelsToUnits: float
  m_RD: SpriteRenderData
  m_Rect: Rectf
  m_AtlasTags: Optional[List[str]] = None
  m_Bones: Optional[List[SpriteBone]] = None
  m_Border: Optional[Vector4f] = None
  m_IsPolygon: Optional[bool] = None
  m_PhysicsShape: Optional[List[List[Vector2f]]] = None
  m_Pivot: Optional[Vector2f] = None
  m_RenderDataKey: Optional[Tuple[GUID, int]] = None
  m_ScriptableObjects: Optional[List[PPtr[MonoBehaviour]]] = None
  m_SpriteAtlas: Optional[PPtr[SpriteAtlas]] = None

  @property
  def image(self) -> Image: ...
