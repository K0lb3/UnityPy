from typing import List, Optional, Union

from UnityPy.classes.generated import (AABB, BlendShapeData, BoneInfluence,
                                       BoneWeights4, CompressedMesh,
                                       MeshBlendShape, MeshBlendShapeVertex,
                                       MinMaxAABB, NamedObject, StreamingInfo,
                                       SubMesh, VariableBoneCountWeights,
                                       VertexData)
from UnityPy.classes.math import (ColorRGBA, Matrix4x4f, Vector2f, Vector3f,
                                  Vector4f)

class Mesh(NamedObject):
  m_BindPose: List[Matrix4x4f]
  m_CompressedMesh: CompressedMesh
  m_IndexBuffer: List[int]
  m_LocalAABB: AABB
  m_MeshCompression: int
  m_MeshUsageFlags: int
  m_Name: str
  m_SubMeshes: List[SubMesh]
  m_BakedConvexCollisionMesh: Optional[List[int]] = None
  m_BakedTriangleCollisionMesh: Optional[List[int]] = None
  m_BoneNameHashes: Optional[List[int]] = None
  m_BonesAABB: Optional[List[MinMaxAABB]] = None
  m_CollisionTriangles: Optional[List[int]] = None
  m_CollisionVertexCount: Optional[int] = None
  m_Colors: Optional[List[ColorRGBA]] = None
  m_CookingOptions: Optional[int] = None
  m_IndexFormat: Optional[int] = None
  m_IsReadable: Optional[bool] = None
  m_KeepIndices: Optional[bool] = None
  m_KeepVertices: Optional[bool] = None
  m_MeshMetrics_0_: Optional[float] = None
  m_MeshMetrics_1_: Optional[float] = None
  m_Normals: Optional[List[Vector3f]] = None
  m_RootBoneNameHash: Optional[int] = None
  m_ShapeVertices: Optional[List[MeshBlendShapeVertex]] = None
  m_Shapes: Optional[Union[BlendShapeData, List[MeshBlendShape]]] = None
  m_Skin: Optional[Union[List[BoneInfluence], List[BoneWeights4]]] = None
  m_StreamCompression: Optional[int] = None
  m_StreamData: Optional[StreamingInfo] = None
  m_Tangents: Optional[List[Vector4f]] = None
  m_UV: Optional[List[Vector2f]] = None
  m_UV1: Optional[List[Vector2f]] = None
  m_Use16BitIndices: Optional[int] = None
  m_VariableBoneCountWeights: Optional[VariableBoneCountWeights] = None
  m_VertexData: Optional[VertexData] = None
  m_Vertices: Optional[List[Vector3f]] = None

  def export(self, format: str = "obj") -> str: ...
