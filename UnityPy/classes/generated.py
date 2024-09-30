# type: ignore
from __future__ import annotations

from abc import ABC
from typing import List, Optional, Tuple, TypeVar, Union

from attrs import define as attrs_define

from .math import (
  ColorRGBA,
  Matrix3x4f,
  Matrix4x4f,
  Quaternionf,
  Vector2f,
  Vector3f,
  Vector4f,
  float3,
  float4,
)
from .Object import Object
from .PPtr import PPtr

T = TypeVar("T")


def unitypy_define(cls: T) -> T:
  """
  A hacky solution to bypass multiple problems related to attrs and inheritance.

  The class inheritance is very lax and based on the typetrees.
  Some of the child classes might not have the same attributes as the parent class,
  which would make type-hinting more tricky, and breaks attrs.define.

  Therefore this function bypasses the issue
  by redifining the bases for problematic classes for the attrs.define call.
  """
  bases = cls.__bases__
  if bases[0] in (object, Object, ABC):
    cls = attrs_define(cls, slots=True, unsafe_hash=True)
  else:
    cls.__bases__ = (Object,)
    cls = attrs_define(cls, slots=False, unsafe_hash=True)
    cls.__bases__ = bases
  return cls


@unitypy_define
class AnnotationManager(Object):
  m_CurrentPreset_m_AnnotationList: List[Annotation]
  m_RecentlyChanged: List[Annotation]
  m_FadeGizmoSize: Optional[float] = None
  m_FadeGizmos: Optional[bool] = None
  m_IconSize: Optional[float] = None
  m_ShowGrid: Optional[bool] = None
  m_ShowSelectionOutline: Optional[bool] = None
  m_ShowSelectionWire: Optional[bool] = None
  m_Use3dGizmos: Optional[bool] = None
  m_WorldIconSize: Optional[float] = None


@unitypy_define
class AssetDatabaseV1(Object):
  m_AssetBundleNames: List[Tuple[int, AssetBundleFullName]]
  m_AssetTimeStamps: List[Tuple[str, AssetTimeStamp]]
  m_Assets: List[Tuple[GUID, Asset]]
  m_Metrics: AssetDatabaseMetrics
  m_UnityShadersVersion: int
  m_lastValidVersionHashes: Optional[List[Tuple[int, int]]] = None
  m_lastValidVersions: Optional[List[Tuple[AssetImporterHashKey, int]]] = None


@unitypy_define
class AssetMetaData(Object):
  assetStoreRef: int
  guid: GUID
  labels: List[str]
  originalName: str
  pathName: str
  licenseType: Optional[int] = None
  originalChangeset: Optional[int] = None
  originalDigest: Optional[Union[Hash128, MdFour]] = None
  originalParent: Optional[GUID] = None
  timeCreated: Optional[int] = None


@unitypy_define
class AssetServerCache(Object):
  m_CachesInitialized: int
  m_CommitItemSelection: List[GUID]
  m_DeletedItems: List[Tuple[GUID, DeletedItem]]
  m_Items: List[Tuple[GUID, Item]]
  m_LastCommitMessage: str
  m_LatestServerChangeset: int
  m_ModifiedItems: List[Tuple[GUID, Item]]
  m_WorkingItemMetaData: List[Tuple[GUID, CachedAssetMetaData]]


@unitypy_define
class AudioBuildInfo(Object):
  m_AudioClipCount: int
  m_AudioMixerCount: int
  m_IsAudioDisabled: bool


@unitypy_define
class BuiltAssetBundleInfoSet(Object):
  bundleInfos: List[BuiltAssetBundleInfo]


@unitypy_define
class Derived(Object):
  pass


@unitypy_define
class SubDerived(Derived):
  pass


@unitypy_define
class DifferentMarshallingTestObject(Object):
  pass


@unitypy_define
class EditorBuildSettings(Object):
  m_Scenes: List[Scene]
  m_UseUCBPForAssetBundles: Optional[bool] = None
  m_configObjects: Optional[List[Tuple[str, PPtr[Object]]]] = None


@unitypy_define
class EditorExtension(Object, ABC):
  pass


@unitypy_define
class Component(EditorExtension):
  m_GameObject: PPtr[GameObject]


@unitypy_define
class Behaviour(Component):
  m_GameObject: PPtr[GameObject]


@unitypy_define
class Animation(Behaviour):
  m_AnimatePhysics: bool
  m_Animation: PPtr[AnimationClip]
  m_Animations: List[PPtr[AnimationClip]]
  m_CullingType: int
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_PlayAutomatically: bool
  m_WrapMode: int
  m_UpdateMode: Optional[int] = None
  m_UserAABB: Optional[AABB] = None


@unitypy_define
class Animator(Behaviour):
  m_ApplyRootMotion: bool
  m_Avatar: PPtr[Avatar]
  m_Controller: Union[PPtr[AnimatorController], PPtr[RuntimeAnimatorController]]
  m_CullingMode: int
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_AllowConstantClipSamplingOptimization: Optional[bool] = None
  m_AnimatePhysics: Optional[bool] = None
  m_HasTransformHierarchy: Optional[bool] = None
  m_KeepAnimatorControllerStateOnDisable: Optional[bool] = None
  m_KeepAnimatorStateOnDisable: Optional[bool] = None
  m_LinearVelocityBlending: Optional[bool] = None
  m_StabilizeFeet: Optional[bool] = None
  m_UpdateMode: Optional[int] = None
  m_WriteDefaultValuesOnDisable: Optional[bool] = None


@unitypy_define
class ArticulationBody(Behaviour):
  m_AnchorPosition: Vector3f
  m_AnchorRotation: Quaternionf
  m_AngularDamping: float
  m_ArticulationJointType: int
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_Immovable: bool
  m_JointFriction: float
  m_LinearDamping: float
  m_LinearX: int
  m_LinearY: int
  m_LinearZ: int
  m_Mass: float
  m_ParentAnchorPosition: Vector3f
  m_ParentAnchorRotation: Quaternionf
  m_SwingY: int
  m_SwingZ: int
  m_Twist: int
  m_XDrive: ArticulationDrive
  m_YDrive: ArticulationDrive
  m_ZDrive: ArticulationDrive
  m_CenterOfMass: Optional[Vector3f] = None
  m_CollisionDetectionMode: Optional[int] = None
  m_ComputeParentAnchor: Optional[bool] = None
  m_ExcludeLayers: Optional[BitField] = None
  m_ImplicitCom: Optional[bool] = None
  m_ImplicitTensor: Optional[bool] = None
  m_IncludeLayers: Optional[BitField] = None
  m_InertiaRotation: Optional[Quaternionf] = None
  m_InertiaTensor: Optional[Vector3f] = None
  m_MatchAnchors: Optional[bool] = None
  m_UseGravity: Optional[bool] = None


@unitypy_define
class AudioBehaviour(Behaviour):
  m_GameObject: PPtr[GameObject]


@unitypy_define
class AudioListener(AudioBehaviour):
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_ExtensionPropertyValues: Optional[List[ExtensionPropertyValue]] = None


@unitypy_define
class AudioSource(AudioBehaviour):
  BypassEffects: bool
  DopplerLevel: float
  Loop: bool
  MaxDistance: float
  MinDistance: float
  Mute: bool
  Pan2D: float
  Priority: int
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_Pitch: float
  m_PlayOnAwake: bool
  m_Volume: float
  m_audioClip: PPtr[AudioClip]
  panLevelCustomCurve: AnimationCurve
  rolloffCustomCurve: AnimationCurve
  rolloffMode: int
  spreadCustomCurve: AnimationCurve
  BypassListenerEffects: Optional[bool] = None
  BypassReverbZones: Optional[bool] = None
  OutputAudioMixerGroup: Optional[PPtr[AudioMixerGroup]] = None
  Spatialize: Optional[bool] = None
  SpatializePostEffects: Optional[bool] = None
  m_ExtensionPropertyValues: Optional[List[ExtensionPropertyValue]] = None
  m_Resource: Optional[PPtr[AudioResource]] = None
  reverbZoneMixCustomCurve: Optional[AnimationCurve] = None


@unitypy_define
class AudioFilter(Behaviour):
  m_GameObject: PPtr[GameObject]


@unitypy_define
class AudioChorusFilter(AudioFilter):
  m_Delay: float
  m_Depth: float
  m_DryMix: float
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_Rate: float
  m_WetMix1: float
  m_WetMix2: float
  m_WetMix3: float
  m_FeedBack: Optional[float] = None


@unitypy_define
class AudioDistortionFilter(AudioFilter):
  m_DistortionLevel: float
  m_Enabled: int
  m_GameObject: PPtr[GameObject]


@unitypy_define
class AudioEchoFilter(AudioFilter):
  m_DecayRatio: float
  m_Delay: Union[int, float]
  m_DryMix: float
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_WetMix: float


@unitypy_define
class AudioHighPassFilter(AudioFilter):
  m_CutoffFrequency: float
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_HighpassResonanceQ: float


@unitypy_define
class AudioLowPassFilter(AudioFilter):
  lowpassLevelCustomCurve: AnimationCurve
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_LowpassResonanceQ: float
  m_CutoffFrequency: Optional[float] = None


@unitypy_define
class AudioReverbFilter(AudioFilter):
  m_DecayHFRatio: float
  m_DecayTime: float
  m_Density: float
  m_Diffusion: float
  m_DryLevel: float
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_HFReference: float
  m_LFReference: float
  m_ReflectionsDelay: float
  m_ReflectionsLevel: float
  m_ReverbDelay: float
  m_ReverbLevel: float
  m_ReverbPreset: int
  m_Room: float
  m_RoomHF: float
  m_RoomLF: float
  m_RoomRolloff: Optional[float] = None


@unitypy_define
class AudioReverbZone(Behaviour):
  m_DecayHFRatio: float
  m_DecayTime: float
  m_Density: float
  m_Diffusion: float
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_HFReference: float
  m_LFReference: float
  m_MaxDistance: float
  m_MinDistance: float
  m_Reflections: int
  m_ReflectionsDelay: float
  m_Reverb: int
  m_ReverbDelay: float
  m_ReverbPreset: int
  m_Room: int
  m_RoomHF: int
  m_RoomLF: int
  m_RoomRolloffFactor: Optional[float] = None


@unitypy_define
class Camera(Behaviour):
  far_clip_plane: float
  field_of_view: float
  m_BackGroundColor: ColorRGBA
  m_ClearFlags: int
  m_CullingMask: BitField
  m_Depth: float
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_NormalizedViewPortRect: Rectf
  m_RenderingPath: int
  m_TargetTexture: PPtr[RenderTexture]
  near_clip_plane: float
  orthographic: bool
  orthographic_size: float
  m_AllowDynamicResolution: Optional[bool] = None
  m_AllowMSAA: Optional[bool] = None
  m_Anamorphism: Optional[float] = None
  m_Aperture: Optional[float] = None
  m_BarrelClipping: Optional[float] = None
  m_BladeCount: Optional[int] = None
  m_Curvature: Optional[Vector2f] = None
  m_FocalLength: Optional[float] = None
  m_FocusDistance: Optional[float] = None
  m_ForceIntoRT: Optional[bool] = None
  m_GateFitMode: Optional[int] = None
  m_HDR: Optional[bool] = None
  m_Iso: Optional[int] = None
  m_LensShift: Optional[Vector2f] = None
  m_OcclusionCulling: Optional[bool] = None
  m_SensorSize: Optional[Vector2f] = None
  m_ShutterSpeed: Optional[float] = None
  m_StereoConvergence: Optional[float] = None
  m_StereoMirrorMode: Optional[bool] = None
  m_StereoSeparation: Optional[float] = None
  m_TargetDisplay: Optional[int] = None
  m_TargetEye: Optional[int] = None
  m_projectionMatrixMode: Optional[int] = None


@unitypy_define
class ScriptableCamera(Camera):
  far_clip_plane: float
  field_of_view: float
  m_AllowDynamicResolution: bool
  m_AllowMSAA: bool
  m_BackGroundColor: ColorRGBA
  m_ClearFlags: int
  m_CullingMask: BitField
  m_Depth: float
  m_Enabled: int
  m_FocalLength: float
  m_ForceIntoRT: bool
  m_GameObject: PPtr[GameObject]
  m_GateFitMode: int
  m_HDR: bool
  m_LensShift: Vector2f
  m_NormalizedViewPortRect: Rectf
  m_OcclusionCulling: bool
  m_RenderingPath: int
  m_Script: PPtr[MonoScript]
  m_SensorSize: Vector2f
  m_StereoConvergence: float
  m_StereoSeparation: float
  m_TargetDisplay: int
  m_TargetEye: int
  m_TargetTexture: PPtr[RenderTexture]
  m_projectionMatrixMode: int
  near_clip_plane: float
  orthographic: bool
  orthographic_size: float


@unitypy_define
class Canvas(Behaviour):
  m_Camera: PPtr[Camera]
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_PixelPerfect: bool
  m_RenderMode: int
  m_AdditionalShaderChannelsFlag: Optional[int] = None
  m_Alpha: Optional[float] = None
  m_Normals: Optional[bool] = None
  m_OverridePixelPerfect: Optional[bool] = None
  m_OverrideSorting: Optional[bool] = None
  m_PlaneDistance: Optional[float] = None
  m_PositionUVs: Optional[bool] = None
  m_ReceivesEvents: Optional[bool] = None
  m_SortingBucketNormalizedSize: Optional[float] = None
  m_SortingLayerID: Optional[int] = None
  m_SortingOrder: Optional[int] = None
  m_TargetDisplay: Optional[int] = None
  m_UpdateRectTransformForStandalone: Optional[int] = None
  m_VertexColorAlwaysGammaSpace: Optional[bool] = None


@unitypy_define
class CanvasGroup(Behaviour):
  m_Alpha: float
  m_BlocksRaycasts: bool
  m_GameObject: PPtr[GameObject]
  m_IgnoreParentGroups: bool
  m_Interactable: bool
  m_Enabled: Optional[int] = None


@unitypy_define
class Cloth(Behaviour):
  m_GameObject: PPtr[GameObject]
  m_BendingStiffness: Optional[float] = None
  m_CapsuleColliders: Optional[List[PPtr[CapsuleCollider]]] = None
  m_Coefficients: Optional[List[ClothConstrainCoefficients]] = None
  m_CollisionMassScale: Optional[float] = None
  m_Damping: Optional[float] = None
  m_Enabled: Optional[int] = None
  m_ExternalAcceleration: Optional[Vector3f] = None
  m_Friction: Optional[float] = None
  m_RandomAcceleration: Optional[Vector3f] = None
  m_SelfAndInterCollisionIndices: Optional[List[int]] = None
  m_SelfCollisionDistance: Optional[float] = None
  m_SelfCollisionStiffness: Optional[float] = None
  m_SleepThreshold: Optional[float] = None
  m_SolverFrequency: Optional[Union[int, float]] = None
  m_SphereColliders: Optional[
    Union[
      List[ClothSphereColliderPair],
      List[Tuple[PPtr[SphereCollider], PPtr[SphereCollider]]],
    ]
  ] = None
  m_StretchingStiffness: Optional[float] = None
  m_UseContinuousCollision: Optional[bool] = None
  m_UseGravity: Optional[bool] = None
  m_UseTethers: Optional[bool] = None
  m_UseVirtualParticles: Optional[bool] = None
  m_VirtualParticleIndices: Optional[List[int]] = None
  m_VirtualParticleWeights: Optional[List[Vector3f]] = None
  m_WorldAccelerationScale: Optional[float] = None
  m_WorldVelocityScale: Optional[float] = None


@unitypy_define
class InteractiveCloth(Cloth):
  m_AttachedColliders: List[ClothAttachment]
  m_AttachmentResponse: float
  m_AttachmentTearFactor: float
  m_BendingStiffness: float
  m_CollisionResponse: float
  m_Damping: float
  m_Density: float
  m_Enabled: int
  m_ExternalAcceleration: Vector3f
  m_Friction: float
  m_GameObject: PPtr[GameObject]
  m_Mesh: PPtr[Mesh]
  m_Pressure: float
  m_RandomAcceleration: Vector3f
  m_SelfCollision: bool
  m_StretchingStiffness: float
  m_TearFactor: float
  m_Thickness: float
  m_UseGravity: bool


@unitypy_define
class SkinnedCloth(Cloth):
  m_BendingStiffness: float
  m_Coefficients: List[ClothConstrainCoefficients]
  m_Damping: float
  m_Enabled: int
  m_ExternalAcceleration: Vector3f
  m_GameObject: PPtr[GameObject]
  m_RandomAcceleration: Vector3f
  m_SelfCollision: bool
  m_StretchingStiffness: float
  m_Thickness: float
  m_UseGravity: bool
  m_WorldAccelerationScale: float
  m_WorldVelocityScale: float


@unitypy_define
class CloudServiceHandlerBehaviour(Behaviour):
  m_Enabled: int
  m_GameObject: PPtr[GameObject]


@unitypy_define
class Collider2D(Behaviour):
  m_GameObject: PPtr[GameObject]


@unitypy_define
class BoxCollider2D(Collider2D):
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_IsTrigger: bool
  m_Material: PPtr[PhysicsMaterial2D]
  m_Size: Vector2f
  m_AutoTiling: Optional[bool] = None
  m_CallbackLayers: Optional[BitField] = None
  m_Center: Optional[Vector2f] = None
  m_CompositeOperation: Optional[int] = None
  m_CompositeOrder: Optional[int] = None
  m_ContactCaptureLayers: Optional[BitField] = None
  m_Density: Optional[float] = None
  m_EdgeRadius: Optional[float] = None
  m_ExcludeLayers: Optional[BitField] = None
  m_ForceReceiveLayers: Optional[BitField] = None
  m_ForceSendLayers: Optional[BitField] = None
  m_IncludeLayers: Optional[BitField] = None
  m_LayerOverridePriority: Optional[int] = None
  m_Offset: Optional[Vector2f] = None
  m_SpriteTilingProperty: Optional[SpriteTilingProperty] = None
  m_UsedByComposite: Optional[bool] = None
  m_UsedByEffector: Optional[bool] = None


@unitypy_define
class CapsuleCollider2D(Collider2D):
  m_Density: float
  m_Direction: int
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_IsTrigger: bool
  m_Material: PPtr[PhysicsMaterial2D]
  m_Offset: Vector2f
  m_Size: Vector2f
  m_UsedByEffector: bool
  m_CallbackLayers: Optional[BitField] = None
  m_CompositeOperation: Optional[int] = None
  m_CompositeOrder: Optional[int] = None
  m_ContactCaptureLayers: Optional[BitField] = None
  m_ExcludeLayers: Optional[BitField] = None
  m_ForceReceiveLayers: Optional[BitField] = None
  m_ForceSendLayers: Optional[BitField] = None
  m_IncludeLayers: Optional[BitField] = None
  m_LayerOverridePriority: Optional[int] = None
  m_UsedByComposite: Optional[bool] = None


@unitypy_define
class CircleCollider2D(Collider2D):
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_IsTrigger: bool
  m_Material: PPtr[PhysicsMaterial2D]
  m_Radius: float
  m_CallbackLayers: Optional[BitField] = None
  m_Center: Optional[Vector2f] = None
  m_CompositeOperation: Optional[int] = None
  m_CompositeOrder: Optional[int] = None
  m_ContactCaptureLayers: Optional[BitField] = None
  m_Density: Optional[float] = None
  m_ExcludeLayers: Optional[BitField] = None
  m_ForceReceiveLayers: Optional[BitField] = None
  m_ForceSendLayers: Optional[BitField] = None
  m_IncludeLayers: Optional[BitField] = None
  m_LayerOverridePriority: Optional[int] = None
  m_Offset: Optional[Vector2f] = None
  m_UsedByComposite: Optional[bool] = None
  m_UsedByEffector: Optional[bool] = None


@unitypy_define
class CompositeCollider2D(Collider2D):
  m_ColliderPaths: List[SubCollider]
  m_CompositePaths: Polygon2D
  m_Density: float
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_GenerationType: int
  m_GeometryType: int
  m_IsTrigger: bool
  m_Material: PPtr[PhysicsMaterial2D]
  m_Offset: Vector2f
  m_UsedByEffector: bool
  m_VertexDistance: float
  m_CallbackLayers: Optional[BitField] = None
  m_CompositeGameObject: Optional[PPtr[GameObject]] = None
  m_CompositeOperation: Optional[int] = None
  m_CompositeOrder: Optional[int] = None
  m_ContactCaptureLayers: Optional[BitField] = None
  m_EdgeRadius: Optional[float] = None
  m_ExcludeLayers: Optional[BitField] = None
  m_ForceReceiveLayers: Optional[BitField] = None
  m_ForceSendLayers: Optional[BitField] = None
  m_IncludeLayers: Optional[BitField] = None
  m_LayerOverridePriority: Optional[int] = None
  m_OffsetDistance: Optional[float] = None
  m_UseDelaunayMesh: Optional[bool] = None
  m_UsedByComposite: Optional[bool] = None


@unitypy_define
class CustomCollider2D(Collider2D):
  m_CustomShapes: PhysicsShapeGroup2D
  m_Density: float
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_IsTrigger: bool
  m_Material: PPtr[PhysicsMaterial2D]
  m_Offset: Vector2f
  m_UsedByEffector: bool
  m_CallbackLayers: Optional[BitField] = None
  m_CompositeOperation: Optional[int] = None
  m_CompositeOrder: Optional[int] = None
  m_ContactCaptureLayers: Optional[BitField] = None
  m_ExcludeLayers: Optional[BitField] = None
  m_ForceReceiveLayers: Optional[BitField] = None
  m_ForceSendLayers: Optional[BitField] = None
  m_IncludeLayers: Optional[BitField] = None
  m_LayerOverridePriority: Optional[int] = None
  m_UsedByComposite: Optional[bool] = None


@unitypy_define
class EdgeCollider2D(Collider2D):
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_IsTrigger: bool
  m_Material: PPtr[PhysicsMaterial2D]
  m_Points: List[Vector2f]
  m_AdjacentEndPoint: Optional[Vector2f] = None
  m_AdjacentStartPoint: Optional[Vector2f] = None
  m_CallbackLayers: Optional[BitField] = None
  m_CompositeOperation: Optional[int] = None
  m_CompositeOrder: Optional[int] = None
  m_ContactCaptureLayers: Optional[BitField] = None
  m_Density: Optional[float] = None
  m_EdgeRadius: Optional[float] = None
  m_ExcludeLayers: Optional[BitField] = None
  m_ForceReceiveLayers: Optional[BitField] = None
  m_ForceSendLayers: Optional[BitField] = None
  m_IncludeLayers: Optional[BitField] = None
  m_LayerOverridePriority: Optional[int] = None
  m_Offset: Optional[Vector2f] = None
  m_UseAdjacentEndPoint: Optional[bool] = None
  m_UseAdjacentStartPoint: Optional[bool] = None
  m_UsedByComposite: Optional[bool] = None
  m_UsedByEffector: Optional[bool] = None


@unitypy_define
class PolygonCollider2D(Collider2D):
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_IsTrigger: bool
  m_Material: PPtr[PhysicsMaterial2D]
  m_AutoTiling: Optional[bool] = None
  m_CallbackLayers: Optional[BitField] = None
  m_CompositeOperation: Optional[int] = None
  m_CompositeOrder: Optional[int] = None
  m_ContactCaptureLayers: Optional[BitField] = None
  m_Density: Optional[float] = None
  m_ExcludeLayers: Optional[BitField] = None
  m_ForceReceiveLayers: Optional[BitField] = None
  m_ForceSendLayers: Optional[BitField] = None
  m_IncludeLayers: Optional[BitField] = None
  m_LayerOverridePriority: Optional[int] = None
  m_Offset: Optional[Vector2f] = None
  m_Points: Optional[Polygon2D] = None
  m_Poly: Optional[Polygon2D] = None
  m_SpriteTilingProperty: Optional[SpriteTilingProperty] = None
  m_UseDelaunayMesh: Optional[bool] = None
  m_UsedByComposite: Optional[bool] = None
  m_UsedByEffector: Optional[bool] = None


@unitypy_define
class PolygonColliderBase2D(Collider2D):
  m_GameObject: PPtr[GameObject]


@unitypy_define
class TilemapCollider2D(Collider2D):
  m_Density: float
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_IsTrigger: bool
  m_Material: PPtr[PhysicsMaterial2D]
  m_Offset: Vector2f
  m_UsedByEffector: bool
  m_CallbackLayers: Optional[BitField] = None
  m_CompositeOperation: Optional[int] = None
  m_CompositeOrder: Optional[int] = None
  m_ContactCaptureLayers: Optional[BitField] = None
  m_ExcludeLayers: Optional[BitField] = None
  m_ExtrusionFactor: Optional[float] = None
  m_ForceReceiveLayers: Optional[BitField] = None
  m_ForceSendLayers: Optional[BitField] = None
  m_IncludeLayers: Optional[BitField] = None
  m_LayerOverridePriority: Optional[int] = None
  m_MaximumTileChangeCount: Optional[int] = None
  m_UseDelaunayMesh: Optional[bool] = None
  m_UsedByComposite: Optional[bool] = None


@unitypy_define
class ConstantForce(Behaviour):
  m_Enabled: int
  m_Force: Vector3f
  m_GameObject: PPtr[GameObject]
  m_RelativeForce: Vector3f
  m_RelativeTorque: Vector3f
  m_Torque: Vector3f


@unitypy_define
class Effector2D(Behaviour):
  m_GameObject: PPtr[GameObject]


@unitypy_define
class AreaEffector2D(Effector2D):
  m_AngularDrag: float
  m_ColliderMask: BitField
  m_Drag: float
  m_Enabled: int
  m_ForceMagnitude: float
  m_ForceTarget: int
  m_ForceVariation: float
  m_GameObject: PPtr[GameObject]
  m_ForceAngle: Optional[float] = None
  m_ForceDirection: Optional[float] = None
  m_UseColliderMask: Optional[bool] = None
  m_UseGlobalAngle: Optional[bool] = None


@unitypy_define
class BuoyancyEffector2D(Effector2D):
  m_AngularDrag: float
  m_ColliderMask: BitField
  m_Density: float
  m_Enabled: int
  m_FlowAngle: float
  m_FlowMagnitude: float
  m_FlowVariation: float
  m_GameObject: PPtr[GameObject]
  m_LinearDrag: float
  m_SurfaceLevel: float
  m_UseColliderMask: bool


@unitypy_define
class PlatformEffector2D(Effector2D):
  m_ColliderMask: BitField
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_OneWay: Optional[bool] = None
  m_RotationalOffset: Optional[float] = None
  m_SideAngleVariance: Optional[float] = None
  m_SideArc: Optional[float] = None
  m_SideBounce: Optional[bool] = None
  m_SideFriction: Optional[bool] = None
  m_SurfaceArc: Optional[float] = None
  m_UseColliderMask: Optional[bool] = None
  m_UseOneWay: Optional[bool] = None
  m_UseOneWayGrouping: Optional[bool] = None
  m_UseSideBounce: Optional[bool] = None
  m_UseSideFriction: Optional[bool] = None


@unitypy_define
class PointEffector2D(Effector2D):
  m_AngularDrag: float
  m_ColliderMask: BitField
  m_DistanceScale: float
  m_Drag: float
  m_Enabled: int
  m_ForceMagnitude: float
  m_ForceMode: int
  m_ForceSource: int
  m_ForceTarget: int
  m_ForceVariation: float
  m_GameObject: PPtr[GameObject]
  m_UseColliderMask: Optional[bool] = None


@unitypy_define
class SurfaceEffector2D(Effector2D):
  m_ColliderMask: BitField
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_Speed: float
  m_SpeedVariation: float
  m_ForceScale: Optional[float] = None
  m_UseBounce: Optional[bool] = None
  m_UseColliderMask: Optional[bool] = None
  m_UseContactForce: Optional[bool] = None
  m_UseFriction: Optional[bool] = None


@unitypy_define
class FlareLayer(Behaviour):
  m_Enabled: int
  m_GameObject: PPtr[GameObject]


@unitypy_define
class GUIElement(Behaviour):
  m_GameObject: PPtr[GameObject]


@unitypy_define
class GUIText(GUIElement):
  m_Alignment: int
  m_Anchor: int
  m_Enabled: int
  m_Font: PPtr[Font]
  m_FontSize: int
  m_FontStyle: int
  m_GameObject: PPtr[GameObject]
  m_LineSpacing: float
  m_Material: PPtr[Material]
  m_PixelCorrect: bool
  m_PixelOffset: Vector2f
  m_TabSize: float
  m_Text: str
  m_Color: Optional[ColorRGBA] = None
  m_RichText: Optional[bool] = None


@unitypy_define
class GUITexture(GUIElement):
  m_BottomBorder: int
  m_Color: ColorRGBA
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_LeftBorder: int
  m_PixelInset: Rectf
  m_RightBorder: int
  m_Texture: PPtr[Texture]
  m_TopBorder: int


@unitypy_define
class GUILayer(Behaviour):
  m_Enabled: int
  m_GameObject: PPtr[GameObject]


@unitypy_define
class GridLayout(Behaviour):
  m_GameObject: PPtr[GameObject]


@unitypy_define
class Grid(GridLayout):
  m_CellGap: Vector3f
  m_CellLayout: int
  m_CellSize: Vector3f
  m_CellSwizzle: int
  m_Enabled: int
  m_GameObject: PPtr[GameObject]


@unitypy_define
class Tilemap(GridLayout):
  m_AnimatedTiles: List[Tuple[int3_storage, TileAnimationData]]
  m_AnimationFrameRate: float
  m_Color: ColorRGBA
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_Origin: int3_storage
  m_Size: int3_storage
  m_TileAnchor: Vector3f
  m_TileAssetArray: List[TilemapRefCountedData]
  m_TileColorArray: List[TilemapRefCountedData]
  m_TileMatrixArray: List[TilemapRefCountedData]
  m_TileOrientation: int
  m_TileOrientationMatrix: Matrix4x4f
  m_TileSpriteArray: List[TilemapRefCountedData]
  m_Tiles: List[Tuple[int3_storage, Tile]]
  m_TileObjectToInstantiateArray: Optional[List[TilemapRefCountedData]] = None


@unitypy_define
class Halo(Behaviour):
  m_Color: ColorRGBA
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_Size: float


@unitypy_define
class HaloLayer(Behaviour):
  m_Enabled: int
  m_GameObject: PPtr[GameObject]


@unitypy_define
class IConstraint(Behaviour):
  m_GameObject: PPtr[GameObject]


@unitypy_define
class AimConstraint(IConstraint):
  m_AffectRotationX: bool
  m_AffectRotationY: bool
  m_AffectRotationZ: bool
  m_AimVector: Vector3f
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_RotationAtRest: Vector3f
  m_RotationOffset: Vector3f
  m_Sources: List[ConstraintSource]
  m_UpType: int
  m_UpVector: Vector3f
  m_Weight: float
  m_WorldUpObject: PPtr[Transform]
  m_WorldUpVector: Vector3f
  m_Active: Optional[bool] = None
  m_IsContraintActive: Optional[bool] = None


@unitypy_define
class LookAtConstraint(IConstraint):
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_Roll: float
  m_RotationAtRest: Vector3f
  m_RotationOffset: Vector3f
  m_Sources: List[ConstraintSource]
  m_UseUpObject: bool
  m_Weight: float
  m_WorldUpObject: PPtr[Transform]
  m_Active: Optional[bool] = None
  m_IsContraintActive: Optional[bool] = None


@unitypy_define
class ParentConstraint(IConstraint):
  m_AffectRotationX: bool
  m_AffectRotationY: bool
  m_AffectRotationZ: bool
  m_AffectTranslationX: bool
  m_AffectTranslationY: bool
  m_AffectTranslationZ: bool
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_RotationAtRest: Vector3f
  m_RotationOffsets: List[Vector3f]
  m_Sources: List[ConstraintSource]
  m_TranslationAtRest: Vector3f
  m_TranslationOffsets: List[Vector3f]
  m_Weight: float
  m_Active: Optional[bool] = None
  m_IsContraintActive: Optional[bool] = None


@unitypy_define
class PositionConstraint(IConstraint):
  m_AffectTranslationX: bool
  m_AffectTranslationY: bool
  m_AffectTranslationZ: bool
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_Sources: List[ConstraintSource]
  m_TranslationAtRest: Vector3f
  m_TranslationOffset: Vector3f
  m_Weight: float
  m_Active: Optional[bool] = None
  m_IsContraintActive: Optional[bool] = None


@unitypy_define
class RotationConstraint(IConstraint):
  m_AffectRotationX: bool
  m_AffectRotationY: bool
  m_AffectRotationZ: bool
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_RotationAtRest: Vector3f
  m_RotationOffset: Vector3f
  m_Sources: List[ConstraintSource]
  m_Weight: float
  m_Active: Optional[bool] = None
  m_IsContraintActive: Optional[bool] = None


@unitypy_define
class ScaleConstraint(IConstraint):
  m_AffectScalingX: bool
  m_AffectScalingY: bool
  m_AffectScalingZ: bool
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_ScaleAtRest: Vector3f
  m_ScaleOffset: Vector3f
  m_Sources: List[ConstraintSource]
  m_Weight: float
  m_Active: Optional[bool] = None
  m_IsContraintActive: Optional[bool] = None


@unitypy_define
class Joint2D(Behaviour):
  m_GameObject: PPtr[GameObject]


@unitypy_define
class AnchoredJoint2D(Joint2D):
  m_GameObject: PPtr[GameObject]


@unitypy_define
class DistanceJoint2D(AnchoredJoint2D):
  m_Anchor: Vector2f
  m_ConnectedAnchor: Vector2f
  m_ConnectedRigidBody: PPtr[Rigidbody2D]
  m_Distance: float
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_AutoConfigureConnectedAnchor: Optional[bool] = None
  m_AutoConfigureDistance: Optional[bool] = None
  m_BreakAction: Optional[int] = None
  m_BreakForce: Optional[float] = None
  m_BreakTorque: Optional[float] = None
  m_CollideConnected: Optional[bool] = None
  m_EnableCollision: Optional[bool] = None
  m_MaxDistanceOnly: Optional[bool] = None


@unitypy_define
class FixedJoint2D(AnchoredJoint2D):
  m_Anchor: Vector2f
  m_AutoConfigureConnectedAnchor: bool
  m_BreakForce: float
  m_BreakTorque: float
  m_ConnectedAnchor: Vector2f
  m_ConnectedRigidBody: PPtr[Rigidbody2D]
  m_DampingRatio: float
  m_EnableCollision: bool
  m_Enabled: int
  m_Frequency: float
  m_GameObject: PPtr[GameObject]
  m_BreakAction: Optional[int] = None


@unitypy_define
class FrictionJoint2D(AnchoredJoint2D):
  m_Anchor: Vector2f
  m_AutoConfigureConnectedAnchor: bool
  m_BreakForce: float
  m_BreakTorque: float
  m_ConnectedAnchor: Vector2f
  m_ConnectedRigidBody: PPtr[Rigidbody2D]
  m_EnableCollision: bool
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_MaxForce: float
  m_MaxTorque: float
  m_BreakAction: Optional[int] = None


@unitypy_define
class HingeJoint2D(AnchoredJoint2D):
  m_Anchor: Vector2f
  m_AngleLimits: Union[JointAngleLimit2D, JointAngleLimits2D]
  m_ConnectedAnchor: Vector2f
  m_ConnectedRigidBody: PPtr[Rigidbody2D]
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_Motor: JointMotor2D
  m_UseLimits: bool
  m_UseMotor: bool
  m_AutoConfigureConnectedAnchor: Optional[bool] = None
  m_BreakAction: Optional[int] = None
  m_BreakForce: Optional[float] = None
  m_BreakTorque: Optional[float] = None
  m_CollideConnected: Optional[bool] = None
  m_EnableCollision: Optional[bool] = None
  m_UseConnectedAnchor: Optional[bool] = None


@unitypy_define
class SliderJoint2D(AnchoredJoint2D):
  m_Anchor: Vector2f
  m_Angle: float
  m_ConnectedAnchor: Vector2f
  m_ConnectedRigidBody: PPtr[Rigidbody2D]
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_Motor: JointMotor2D
  m_TranslationLimits: JointTranslationLimits2D
  m_UseLimits: bool
  m_UseMotor: bool
  m_AutoConfigureAngle: Optional[bool] = None
  m_AutoConfigureConnectedAnchor: Optional[bool] = None
  m_BreakAction: Optional[int] = None
  m_BreakForce: Optional[float] = None
  m_BreakTorque: Optional[float] = None
  m_CollideConnected: Optional[bool] = None
  m_EnableCollision: Optional[bool] = None


@unitypy_define
class SpringJoint2D(AnchoredJoint2D):
  m_Anchor: Vector2f
  m_ConnectedAnchor: Vector2f
  m_ConnectedRigidBody: PPtr[Rigidbody2D]
  m_DampingRatio: float
  m_Distance: float
  m_Enabled: int
  m_Frequency: float
  m_GameObject: PPtr[GameObject]
  m_AutoConfigureConnectedAnchor: Optional[bool] = None
  m_AutoConfigureDistance: Optional[bool] = None
  m_BreakAction: Optional[int] = None
  m_BreakForce: Optional[float] = None
  m_BreakTorque: Optional[float] = None
  m_CollideConnected: Optional[bool] = None
  m_EnableCollision: Optional[bool] = None


@unitypy_define
class WheelJoint2D(AnchoredJoint2D):
  m_Anchor: Vector2f
  m_ConnectedAnchor: Vector2f
  m_ConnectedRigidBody: PPtr[Rigidbody2D]
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_Motor: JointMotor2D
  m_Suspension: JointSuspension2D
  m_UseMotor: bool
  m_AutoConfigureConnectedAnchor: Optional[bool] = None
  m_BreakAction: Optional[int] = None
  m_BreakForce: Optional[float] = None
  m_BreakTorque: Optional[float] = None
  m_CollideConnected: Optional[bool] = None
  m_EnableCollision: Optional[bool] = None


@unitypy_define
class RelativeJoint2D(Joint2D):
  m_AngularOffset: float
  m_AutoConfigureOffset: bool
  m_BreakForce: float
  m_BreakTorque: float
  m_ConnectedRigidBody: PPtr[Rigidbody2D]
  m_CorrectionScale: float
  m_EnableCollision: bool
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_LinearOffset: Vector2f
  m_MaxForce: float
  m_MaxTorque: float
  m_BreakAction: Optional[int] = None


@unitypy_define
class TargetJoint2D(Joint2D):
  m_Anchor: Vector2f
  m_AutoConfigureTarget: bool
  m_BreakForce: float
  m_BreakTorque: float
  m_ConnectedRigidBody: PPtr[Rigidbody2D]
  m_DampingRatio: float
  m_EnableCollision: bool
  m_Enabled: int
  m_Frequency: float
  m_GameObject: PPtr[GameObject]
  m_MaxForce: float
  m_Target: Vector2f
  m_BreakAction: Optional[int] = None


@unitypy_define
class LensFlare(Behaviour):
  m_Brightness: float
  m_Color: ColorRGBA
  m_Directional: bool
  m_Enabled: int
  m_Flare: PPtr[Flare]
  m_GameObject: PPtr[GameObject]
  m_IgnoreLayers: BitField
  m_FadeSpeed: Optional[float] = None


@unitypy_define
class Light(Behaviour):
  m_Color: ColorRGBA
  m_Cookie: PPtr[Texture]
  m_CookieSize: float
  m_CullingMask: BitField
  m_DrawHalo: bool
  m_Enabled: int
  m_Flare: PPtr[Flare]
  m_GameObject: PPtr[GameObject]
  m_Intensity: float
  m_Lightmapping: int
  m_Range: float
  m_RenderMode: int
  m_Shadows: ShadowSettings
  m_SpotAngle: float
  m_Type: int
  m_ActuallyLightmapped: Optional[bool] = None
  m_AreaSize: Optional[Vector2f] = None
  m_BakedIndex: Optional[int] = None
  m_BakingOutput: Optional[LightBakingOutput] = None
  m_BounceIntensity: Optional[float] = None
  m_BoundingSphereOverride: Optional[Vector4f] = None
  m_CCT: Optional[float] = None
  m_ColorTemperature: Optional[float] = None
  m_EnableSpotReflector: Optional[bool] = None
  m_FalloffTable: Optional[FalloffTable] = None
  m_ForceVisible: Optional[bool] = None
  m_InnerSpotAngle: Optional[float] = None
  m_LightShadowCasterMode: Optional[int] = None
  m_LightUnit: Optional[int] = None
  m_LuxAtDistance: Optional[float] = None
  m_RenderingLayerMask: Optional[int] = None
  m_Shape: Optional[int] = None
  m_UseBoundingSphereOverride: Optional[bool] = None
  m_UseColorTemperature: Optional[bool] = None
  m_UseViewFrustumForShadowCasterCull: Optional[bool] = None


@unitypy_define
class LightProbeGroup(Behaviour):
  m_GameObject: PPtr[GameObject]
  m_Enabled: Optional[int] = None


@unitypy_define
class LightProbeProxyVolume(Behaviour):
  m_BoundingBoxMode: int
  m_BoundingBoxOrigin: Vector3f
  m_BoundingBoxSize: Vector3f
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_ProbePositionMode: int
  m_RefreshMode: int
  m_ResolutionMode: int
  m_ResolutionProbesPerUnit: float
  m_ResolutionX: int
  m_ResolutionY: int
  m_ResolutionZ: int
  m_DataFormat: Optional[int] = None
  m_QualityMode: Optional[int] = None


@unitypy_define
class MonoBehaviour(Behaviour):
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_Name: str
  m_Script: PPtr[MonoScript]


@unitypy_define
class NavMeshAgent(Behaviour):
  m_Acceleration: float
  m_AngularSpeed: float
  m_AutoRepath: bool
  m_AutoTraverseOffMeshLink: bool
  m_BaseOffset: float
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_Height: float
  m_ObstacleAvoidanceType: int
  m_Radius: float
  m_Speed: float
  m_StoppingDistance: float
  m_WalkableMask: int
  avoidancePriority: Optional[int] = None
  m_AgentTypeID: Optional[int] = None
  m_AutoBraking: Optional[bool] = None


@unitypy_define
class NavMeshObstacle(Behaviour):
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_Carve: Optional[bool] = None
  m_CarveOnlyStationary: Optional[bool] = None
  m_Center: Optional[Vector3f] = None
  m_Extents: Optional[Vector3f] = None
  m_Height: Optional[float] = None
  m_MoveThreshold: Optional[float] = None
  m_Radius: Optional[float] = None
  m_Shape: Optional[int] = None
  m_TimeToStationary: Optional[float] = None


@unitypy_define
class NetworkView(Behaviour):
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_Observed: PPtr[Component]
  m_StateSynchronization: int
  m_ViewID: NetworkViewID


@unitypy_define
class OffMeshLink(Behaviour):
  m_Activated: bool
  m_BiDirectional: bool
  m_CostOverride: float
  m_End: PPtr[Transform]
  m_GameObject: PPtr[GameObject]
  m_Start: PPtr[Transform]
  m_AgentTypeID: Optional[int] = None
  m_AreaIndex: Optional[int] = None
  m_AutoUpdatePositions: Optional[bool] = None
  m_DtPolyRef: Optional[int] = None
  m_Enabled: Optional[int] = None
  m_NavMeshLayer: Optional[int] = None


@unitypy_define
class ParticleSystemForceField(Behaviour):
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_Parameters: ParticleSystemForceFieldParameters


@unitypy_define
class PhysicsUpdateBehaviour2D(Behaviour):
  m_GameObject: PPtr[GameObject]


@unitypy_define
class ConstantForce2D(PhysicsUpdateBehaviour2D):
  m_Enabled: int
  m_Force: Vector2f
  m_GameObject: PPtr[GameObject]
  m_RelativeForce: Vector2f
  m_Torque: float


@unitypy_define
class PlayableDirector(Behaviour):
  m_DirectorUpdateMode: int
  m_Enabled: int
  m_ExposedReferences: ExposedReferenceTable
  m_GameObject: PPtr[GameObject]
  m_InitialState: int
  m_InitialTime: float
  m_PlayableAsset: PPtr[Object]
  m_SceneBindings: List[DirectorGenericBinding]
  m_WrapMode: int


@unitypy_define
class Projector(Behaviour):
  m_AspectRatio: float
  m_Enabled: int
  m_FarClipPlane: float
  m_FieldOfView: float
  m_GameObject: PPtr[GameObject]
  m_IgnoreLayers: BitField
  m_Material: PPtr[Material]
  m_NearClipPlane: float
  m_Orthographic: bool
  m_OrthographicSize: float


@unitypy_define
class ReflectionProbe(Behaviour):
  m_BackGroundColor: ColorRGBA
  m_BakedTexture: PPtr[Texture]
  m_BoxOffset: Vector3f
  m_BoxProjection: bool
  m_BoxSize: Vector3f
  m_ClearFlags: int
  m_CullingMask: BitField
  m_CustomBakedTexture: PPtr[Texture]
  m_Enabled: int
  m_FarClip: float
  m_GameObject: PPtr[GameObject]
  m_HDR: bool
  m_Importance: int
  m_IntensityMultiplier: float
  m_Mode: int
  m_NearClip: float
  m_RefreshMode: int
  m_RenderDynamicObjects: bool
  m_Resolution: int
  m_ShadowDistance: float
  m_TimeSlicingMode: int
  m_Type: int
  m_UpdateFrequency: int
  m_UseOcclusionCulling: bool
  m_BlendDistance: Optional[float] = None


@unitypy_define
class Skybox(Behaviour):
  m_CustomSkybox: PPtr[Material]
  m_Enabled: int
  m_GameObject: PPtr[GameObject]


@unitypy_define
class SortingGroup(Behaviour):
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_SortingLayer: int
  m_SortingOrder: int
  m_SortAtRoot: Optional[bool] = None
  m_SortingLayerID: Optional[int] = None


@unitypy_define
class StreamingController(Behaviour):
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_StreamingMipmapBias: float


@unitypy_define
class Terrain(Behaviour):
  m_BakeLightProbesForTrees: bool
  m_ChunkDynamicUVST: Vector4f
  m_DetailObjectDensity: float
  m_DetailObjectDistance: float
  m_DrawHeightmap: bool
  m_DrawTreesAndFoliage: bool
  m_DynamicUVST: Vector4f
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_HeightmapMaximumLOD: int
  m_HeightmapPixelError: float
  m_LightmapIndex: int
  m_LightmapIndexDynamic: int
  m_LightmapTilingOffset: Vector4f
  m_LightmapTilingOffsetDynamic: Vector4f
  m_MaterialTemplate: PPtr[Material]
  m_ReflectionProbeUsage: int
  m_SplatMapDistance: float
  m_TerrainData: PPtr[TerrainData]
  m_TreeBillboardDistance: float
  m_TreeCrossFadeLength: float
  m_TreeDistance: float
  m_TreeMaximumFullLODCount: int
  m_AllowAutoConnect: Optional[bool] = None
  m_CastShadows: Optional[bool] = None
  m_DefaultSmoothness: Optional[float] = None
  m_DrawInstanced: Optional[bool] = None
  m_EnableHeightmapRayTracing: Optional[bool] = None
  m_EnableTreesAndDetailsRayTracing: Optional[bool] = None
  m_ExplicitProbeSetHash: Optional[Hash128] = None
  m_GroupingID: Optional[int] = None
  m_HeightmapMinimumLODSimplification: Optional[int] = None
  m_IgnoreQualitySettings: Optional[bool] = None
  m_LegacyShininess: Optional[float] = None
  m_LegacySpecular: Optional[ColorRGBA] = None
  m_MaterialType: Optional[int] = None
  m_PreserveTreePrototypeLayers: Optional[bool] = None
  m_RenderingLayerMask: Optional[int] = None
  m_ShadowCastingMode: Optional[int] = None
  m_StaticShadowCaster: Optional[bool] = None
  m_TreeMotionVectorModeOverride: Optional[int] = None
  m_UseDefaultSmoothness: Optional[bool] = None


@unitypy_define
class VideoPlayer(Behaviour):
  m_AspectRatio: int
  m_AudioOutputMode: int
  m_ControlledAudioTrackCount: int
  m_DataSource: int
  m_DirectAudioMutes: List[bool]
  m_DirectAudioVolumes: List[float]
  m_Enabled: int
  m_EnabledAudioTracks: List[bool]
  m_FrameReadyEventEnabled: bool
  m_GameObject: PPtr[GameObject]
  m_Looping: bool
  m_PlayOnAwake: bool
  m_PlaybackSpeed: float
  m_RenderMode: int
  m_SkipOnDrop: bool
  m_TargetAudioSources: List[PPtr[AudioSource]]
  m_TargetCamera: PPtr[Camera]
  m_TargetCameraAlpha: float
  m_TargetMaterialProperty: str
  m_TargetMaterialRenderer: PPtr[Renderer]
  m_TargetTexture: PPtr[RenderTexture]
  m_Url: str
  m_VideoClip: PPtr[VideoClip]
  m_WaitForFirstFrame: bool
  m_TargetCamera3DLayout: Optional[int] = None
  m_TargetMaterialName: Optional[str] = None
  m_TimeReference: Optional[int] = None
  m_TimeUpdateMode: Optional[int] = None
  m_VideoShaders: Optional[List[PPtr[Shader]]] = None


@unitypy_define
class VisualEffect(Behaviour):
  m_Asset: PPtr[VisualEffectAsset]
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_PropertySheet: VFXPropertySheetSerializedBase
  m_ResetSeedOnPlay: Union[bool, int]
  m_StartSeed: int
  m_AllowInstancing: Optional[int] = None
  m_InitialEventName: Optional[str] = None
  m_InitialEventNameOverriden: Optional[int] = None


@unitypy_define
class WindZone(Behaviour):
  m_Enabled: int
  m_GameObject: PPtr[GameObject]
  m_Mode: int
  m_Radius: float
  m_WindMain: float
  m_WindPulseFrequency: float
  m_WindPulseMagnitude: float
  m_WindTurbulence: float


@unitypy_define
class CanvasRenderer(Component):
  m_GameObject: PPtr[GameObject]
  m_CullTransparentMesh: Optional[bool] = None


@unitypy_define
class Collider(Component):
  m_GameObject: Optional[PPtr[GameObject]] = None
  m_MaxLimitX: Optional[float] = None
  m_MaxLimitY: Optional[float] = None
  m_MaxLimitZ: Optional[float] = None
  m_MinLimitX: Optional[float] = None
  m_Type: Optional[int] = None
  m_X: Optional[xform] = None
  m_XMotionType: Optional[int] = None
  m_YMotionType: Optional[int] = None
  m_ZMotionType: Optional[int] = None


@unitypy_define
class BoxCollider(Collider):
  m_Center: Vector3f
  m_Enabled: bool
  m_GameObject: PPtr[GameObject]
  m_IsTrigger: bool
  m_Material: Union[PPtr[PhysicMaterial], PPtr[PhysicsMaterial]]
  m_Size: Vector3f
  m_ExcludeLayers: Optional[BitField] = None
  m_IncludeLayers: Optional[BitField] = None
  m_LayerOverridePriority: Optional[int] = None
  m_ProvidesContacts: Optional[bool] = None


@unitypy_define
class CapsuleCollider(Collider):
  m_Center: Vector3f
  m_Direction: int
  m_Enabled: bool
  m_GameObject: PPtr[GameObject]
  m_Height: float
  m_IsTrigger: bool
  m_Material: Union[PPtr[PhysicMaterial], PPtr[PhysicsMaterial]]
  m_Radius: float
  m_ExcludeLayers: Optional[BitField] = None
  m_IncludeLayers: Optional[BitField] = None
  m_LayerOverridePriority: Optional[int] = None
  m_ProvidesContacts: Optional[bool] = None


@unitypy_define
class CharacterController(Collider):
  m_Center: Vector3f
  m_GameObject: PPtr[GameObject]
  m_Height: float
  m_MinMoveDistance: float
  m_Radius: float
  m_SkinWidth: float
  m_SlopeLimit: float
  m_StepOffset: float
  m_Enabled: Optional[bool] = None
  m_ExcludeLayers: Optional[BitField] = None
  m_IncludeLayers: Optional[BitField] = None
  m_IsTrigger: Optional[bool] = None
  m_LayerOverridePriority: Optional[int] = None
  m_Material: Optional[Union[PPtr[PhysicMaterial], PPtr[PhysicsMaterial]]] = None
  m_ProvidesContacts: Optional[bool] = None


@unitypy_define
class MeshCollider(Collider):
  m_Convex: bool
  m_Enabled: bool
  m_GameObject: PPtr[GameObject]
  m_IsTrigger: bool
  m_Material: Union[PPtr[PhysicMaterial], PPtr[PhysicsMaterial]]
  m_Mesh: PPtr[Mesh]
  m_CookingOptions: Optional[int] = None
  m_ExcludeLayers: Optional[BitField] = None
  m_IncludeLayers: Optional[BitField] = None
  m_InflateMesh: Optional[bool] = None
  m_LayerOverridePriority: Optional[int] = None
  m_ProvidesContacts: Optional[bool] = None
  m_SkinWidth: Optional[float] = None
  m_SmoothSphereCollisions: Optional[bool] = None


@unitypy_define
class RaycastCollider(Collider):
  m_Center: Vector3f
  m_Enabled: bool
  m_GameObject: PPtr[GameObject]
  m_IsTrigger: bool
  m_Length: float
  m_Material: PPtr[PhysicMaterial]


@unitypy_define
class SphereCollider(Collider):
  m_Center: Vector3f
  m_Enabled: bool
  m_GameObject: PPtr[GameObject]
  m_IsTrigger: bool
  m_Material: Union[PPtr[PhysicMaterial], PPtr[PhysicsMaterial]]
  m_Radius: float
  m_ExcludeLayers: Optional[BitField] = None
  m_IncludeLayers: Optional[BitField] = None
  m_LayerOverridePriority: Optional[int] = None
  m_ProvidesContacts: Optional[bool] = None


@unitypy_define
class TerrainCollider(Collider):
  m_Enabled: bool
  m_GameObject: PPtr[GameObject]
  m_TerrainData: PPtr[TerrainData]
  m_CreateTreeColliders: Optional[bool] = None
  m_EnableTreeColliders: Optional[bool] = None
  m_ExcludeLayers: Optional[BitField] = None
  m_IncludeLayers: Optional[BitField] = None
  m_IsTrigger: Optional[bool] = None
  m_LayerOverridePriority: Optional[int] = None
  m_Material: Optional[Union[PPtr[PhysicMaterial], PPtr[PhysicsMaterial]]] = None
  m_ProvidesContacts: Optional[bool] = None


@unitypy_define
class WheelCollider(Collider):
  m_Center: Vector3f
  m_ForwardFriction: WheelFrictionCurve
  m_GameObject: PPtr[GameObject]
  m_Mass: float
  m_Radius: float
  m_SidewaysFriction: WheelFrictionCurve
  m_SuspensionDistance: float
  m_SuspensionSpring: JointSpring
  m_Enabled: Optional[bool] = None
  m_ExcludeLayers: Optional[BitField] = None
  m_ForceAppPointDistance: Optional[float] = None
  m_IncludeLayers: Optional[BitField] = None
  m_LayerOverridePriority: Optional[int] = None
  m_ProvidesContacts: Optional[bool] = None
  m_WheelDampingRate: Optional[float] = None


@unitypy_define
class FakeComponent(Component):
  m_GameObject: PPtr[GameObject]


@unitypy_define
class Joint(Component):
  m_GameObject: PPtr[GameObject]


@unitypy_define
class CharacterJoint(Joint):
  m_Anchor: Vector3f
  m_Axis: Vector3f
  m_BreakForce: float
  m_BreakTorque: float
  m_ConnectedBody: PPtr[Rigidbody]
  m_GameObject: PPtr[GameObject]
  m_HighTwistLimit: SoftJointLimit
  m_LowTwistLimit: SoftJointLimit
  m_Swing1Limit: SoftJointLimit
  m_Swing2Limit: SoftJointLimit
  m_SwingAxis: Vector3f
  m_AutoConfigureConnectedAnchor: Optional[bool] = None
  m_ConnectedAnchor: Optional[Vector3f] = None
  m_ConnectedArticulationBody: Optional[PPtr[ArticulationBody]] = None
  m_ConnectedMassScale: Optional[float] = None
  m_EnableCollision: Optional[bool] = None
  m_EnablePreprocessing: Optional[bool] = None
  m_EnableProjection: Optional[bool] = None
  m_Enabled: Optional[bool] = None
  m_MassScale: Optional[float] = None
  m_ProjectionAngle: Optional[float] = None
  m_ProjectionDistance: Optional[float] = None
  m_SwingLimitSpring: Optional[SoftJointLimitSpring] = None
  m_TwistLimitSpring: Optional[SoftJointLimitSpring] = None


@unitypy_define
class ConfigurableJoint(Joint):
  m_Anchor: Vector3f
  m_AngularXDrive: JointDrive
  m_AngularXMotion: int
  m_AngularYLimit: SoftJointLimit
  m_AngularYMotion: int
  m_AngularYZDrive: JointDrive
  m_AngularZLimit: SoftJointLimit
  m_AngularZMotion: int
  m_Axis: Vector3f
  m_BreakForce: float
  m_BreakTorque: float
  m_ConfiguredInWorldSpace: bool
  m_ConnectedBody: PPtr[Rigidbody]
  m_GameObject: PPtr[GameObject]
  m_HighAngularXLimit: SoftJointLimit
  m_LinearLimit: SoftJointLimit
  m_LowAngularXLimit: SoftJointLimit
  m_ProjectionAngle: float
  m_ProjectionDistance: float
  m_ProjectionMode: int
  m_RotationDriveMode: int
  m_SecondaryAxis: Vector3f
  m_SlerpDrive: JointDrive
  m_TargetAngularVelocity: Vector3f
  m_TargetPosition: Vector3f
  m_TargetRotation: Quaternionf
  m_TargetVelocity: Vector3f
  m_XDrive: JointDrive
  m_XMotion: int
  m_YDrive: JointDrive
  m_YMotion: int
  m_ZDrive: JointDrive
  m_ZMotion: int
  m_AngularXLimitSpring: Optional[SoftJointLimitSpring] = None
  m_AngularYZLimitSpring: Optional[SoftJointLimitSpring] = None
  m_AutoConfigureConnectedAnchor: Optional[bool] = None
  m_ConnectedAnchor: Optional[Vector3f] = None
  m_ConnectedArticulationBody: Optional[PPtr[ArticulationBody]] = None
  m_ConnectedMassScale: Optional[float] = None
  m_EnableCollision: Optional[bool] = None
  m_EnablePreprocessing: Optional[bool] = None
  m_Enabled: Optional[bool] = None
  m_LinearLimitSpring: Optional[SoftJointLimitSpring] = None
  m_MassScale: Optional[float] = None
  m_SwapBodies: Optional[bool] = None


@unitypy_define
class FixedJoint(Joint):
  m_BreakForce: float
  m_BreakTorque: float
  m_ConnectedBody: PPtr[Rigidbody]
  m_GameObject: PPtr[GameObject]
  m_ConnectedArticulationBody: Optional[PPtr[ArticulationBody]] = None
  m_ConnectedMassScale: Optional[float] = None
  m_EnableCollision: Optional[bool] = None
  m_EnablePreprocessing: Optional[bool] = None
  m_Enabled: Optional[bool] = None
  m_MassScale: Optional[float] = None


@unitypy_define
class HingeJoint(Joint):
  m_Anchor: Vector3f
  m_Axis: Vector3f
  m_BreakForce: float
  m_BreakTorque: float
  m_ConnectedBody: PPtr[Rigidbody]
  m_GameObject: PPtr[GameObject]
  m_Limits: JointLimits
  m_Motor: JointMotor
  m_Spring: JointSpring
  m_UseLimits: bool
  m_UseMotor: bool
  m_UseSpring: bool
  m_AutoConfigureConnectedAnchor: Optional[bool] = None
  m_ConnectedAnchor: Optional[Vector3f] = None
  m_ConnectedArticulationBody: Optional[PPtr[ArticulationBody]] = None
  m_ConnectedMassScale: Optional[float] = None
  m_EnableCollision: Optional[bool] = None
  m_EnablePreprocessing: Optional[bool] = None
  m_Enabled: Optional[bool] = None
  m_ExtendedLimits: Optional[bool] = None
  m_MassScale: Optional[float] = None
  m_UseAcceleration: Optional[bool] = None


@unitypy_define
class SpringJoint(Joint):
  m_Anchor: Vector3f
  m_BreakForce: float
  m_BreakTorque: float
  m_ConnectedBody: PPtr[Rigidbody]
  m_Damper: float
  m_GameObject: PPtr[GameObject]
  m_MaxDistance: float
  m_MinDistance: float
  m_Spring: float
  m_AutoConfigureConnectedAnchor: Optional[bool] = None
  m_Axis: Optional[Vector3f] = None
  m_ConnectedAnchor: Optional[Vector3f] = None
  m_ConnectedArticulationBody: Optional[PPtr[ArticulationBody]] = None
  m_ConnectedMassScale: Optional[float] = None
  m_EnableCollision: Optional[bool] = None
  m_EnablePreprocessing: Optional[bool] = None
  m_Enabled: Optional[bool] = None
  m_MassScale: Optional[float] = None
  m_Tolerance: Optional[float] = None


@unitypy_define
class LODGroup(Component):
  m_Enabled: bool
  m_GameObject: PPtr[GameObject]
  m_LODs: List[LOD]
  m_LocalReferencePoint: Vector3f
  m_Size: float
  m_AnimateCrossFading: Optional[bool] = None
  m_FadeMode: Optional[int] = None
  m_LastLODIsBillboard: Optional[bool] = None
  m_ScreenRelativeTransitionHeight: Optional[float] = None


@unitypy_define
class MeshFilter(Component):
  m_GameObject: PPtr[GameObject]
  m_Mesh: PPtr[Mesh]


@unitypy_define
class MultiplayerRolesData(Component):
  m_ComponentsRolesMasks: List[ObjectRolePair]
  m_GameObject: PPtr[GameObject]
  m_GameObjectRolesMask: int


@unitypy_define
class OcclusionArea(Component):
  m_Center: Vector3f
  m_GameObject: PPtr[GameObject]
  m_IsViewVolume: bool
  m_Size: Vector3f
  m_IsTargetVolume: Optional[bool] = None
  m_TargetResolution: Optional[int] = None


@unitypy_define
class OcclusionPortal(Component):
  m_Center: Vector3f
  m_GameObject: PPtr[GameObject]
  m_Open: bool
  m_Size: Vector3f


@unitypy_define
class ParticleAnimator(Component):
  Does_Animate_Color: bool
  autodestruct: bool
  colorAnimation_0_: ColorRGBA
  colorAnimation_1_: ColorRGBA
  colorAnimation_2_: ColorRGBA
  colorAnimation_3_: ColorRGBA
  colorAnimation_4_: ColorRGBA
  damping: float
  force: Vector3f
  localRotationAxis: Vector3f
  m_GameObject: PPtr[GameObject]
  rndForce: Vector3f
  sizeGrow: float
  stopSimulation: bool
  worldRotationAxis: Vector3f


@unitypy_define
class ParticleEmitter(Component):
  m_GameObject: PPtr[GameObject]


@unitypy_define
class EllipsoidParticleEmitter(ParticleEmitter):
  Simulate_in_Worldspace: bool
  angularVelocity: float
  emitterVelocityScale: float
  localVelocity: Vector3f
  m_Ellipsoid: Vector3f
  m_Emit: bool
  m_Enabled: bool
  m_GameObject: PPtr[GameObject]
  m_MinEmitterRange: float
  m_OneShot: bool
  maxEmission: float
  maxEnergy: float
  maxSize: float
  minEmission: float
  minEnergy: float
  minSize: float
  rndAngularVelocity: float
  rndRotation: bool
  rndVelocity: Vector3f
  tangentVelocity: Vector3f
  worldVelocity: Vector3f


@unitypy_define
class MeshParticleEmitter(ParticleEmitter):
  Simulate_in_Worldspace: bool
  angularVelocity: float
  emitterVelocityScale: float
  localVelocity: Vector3f
  m_Emit: bool
  m_Enabled: bool
  m_GameObject: PPtr[GameObject]
  m_InterpolateTriangles: bool
  m_MaxNormalVelocity: float
  m_Mesh: PPtr[Mesh]
  m_MinNormalVelocity: float
  m_OneShot: bool
  m_Systematic: bool
  maxEmission: float
  maxEnergy: float
  maxSize: float
  minEmission: float
  minEnergy: float
  minSize: float
  rndAngularVelocity: float
  rndRotation: bool
  rndVelocity: Vector3f
  tangentVelocity: Vector3f
  worldVelocity: Vector3f


@unitypy_define
class ParticleSystem(Component):
  ClampVelocityModule: ClampVelocityModule
  CollisionModule: CollisionModule
  ColorBySpeedModule: ColorBySpeedModule
  ColorModule: ColorModule
  EmissionModule: EmissionModule
  ForceModule: ForceModule
  InitialModule: InitialModule
  RotationBySpeedModule: RotationBySpeedModule
  RotationModule: RotationModule
  ShapeModule: ShapeModule
  SizeBySpeedModule: SizeBySpeedModule
  SizeModule: SizeModule
  SubModule: SubModule
  UVModule: UVModule
  VelocityModule: VelocityModule
  lengthInSec: float
  looping: bool
  m_GameObject: PPtr[GameObject]
  moveWithTransform: Union[bool, int]
  playOnAwake: bool
  prewarm: bool
  randomSeed: int
  startDelay: Union[MinMaxCurve, float]
  CustomDataModule: Optional[CustomDataModule] = None
  ExternalForcesModule: Optional[ExternalForcesModule] = None
  InheritVelocityModule: Optional[InheritVelocityModule] = None
  LifetimeByEmitterSpeedModule: Optional[LifetimeByEmitterSpeedModule] = None
  LightsModule: Optional[LightsModule] = None
  NoiseModule: Optional[NoiseModule] = None
  TrailModule: Optional[TrailModule] = None
  TriggerModule: Optional[TriggerModule] = None
  autoRandomSeed: Optional[bool] = None
  cullingMode: Optional[int] = None
  emitterVelocityMode: Optional[int] = None
  moveWithCustomTransform: Optional[PPtr[Transform]] = None
  ringBufferLoopRange: Optional[Vector2f] = None
  ringBufferMode: Optional[int] = None
  scalingMode: Optional[int] = None
  simulationSpeed: Optional[float] = None
  speed: Optional[float] = None
  stopAction: Optional[int] = None
  useRigidbodyForVelocity: Optional[bool] = None
  useUnscaledTime: Optional[bool] = None


@unitypy_define
class Pipeline(Component):
  m_GameObject: PPtr[GameObject]


@unitypy_define
class Renderer(Component):
  m_GameObject: PPtr[GameObject]


@unitypy_define
class BillboardRenderer(Renderer):
  m_Billboard: PPtr[BillboardAsset]
  m_CastShadows: int
  m_Enabled: bool
  m_GameObject: PPtr[GameObject]
  m_LightmapIndex: int
  m_LightmapIndexDynamic: int
  m_LightmapTilingOffset: Vector4f
  m_LightmapTilingOffsetDynamic: Vector4f
  m_Materials: List[PPtr[Material]]
  m_ProbeAnchor: PPtr[Transform]
  m_ReceiveShadows: Union[bool, int]
  m_ReflectionProbeUsage: int
  m_SortingOrder: int
  m_StaticBatchRoot: PPtr[Transform]
  m_DynamicOccludee: Optional[int] = None
  m_LightProbeUsage: Optional[int] = None
  m_LightProbeVolumeOverride: Optional[PPtr[GameObject]] = None
  m_MotionVectors: Optional[int] = None
  m_RayTraceProcedural: Optional[int] = None
  m_RayTracingAccelStructBuildFlags: Optional[int] = None
  m_RayTracingAccelStructBuildFlagsOverride: Optional[int] = None
  m_RayTracingMode: Optional[int] = None
  m_RendererPriority: Optional[int] = None
  m_RenderingLayerMask: Optional[int] = None
  m_SmallMeshCulling: Optional[int] = None
  m_SortingLayer: Optional[int] = None
  m_SortingLayerID: Optional[int] = None
  m_StaticBatchInfo: Optional[StaticBatchInfo] = None
  m_StaticShadowCaster: Optional[int] = None
  m_SubsetIndices: Optional[List[int]] = None
  m_UseLightProbes: Optional[bool] = None


@unitypy_define
class ClothRenderer(Renderer):
  m_CastShadows: bool
  m_Enabled: bool
  m_GameObject: PPtr[GameObject]
  m_LightmapIndex: int
  m_LightmapTilingOffset: Vector4f
  m_Materials: List[PPtr[Material]]
  m_PauseWhenNotVisible: bool
  m_ReceiveShadows: bool
  m_StaticBatchRoot: PPtr[Transform]
  m_SubsetIndices: List[int]
  m_LightProbeAnchor: Optional[PPtr[Transform]] = None
  m_SortingLayer: Optional[int] = None
  m_SortingLayerID: Optional[int] = None
  m_SortingOrder: Optional[int] = None
  m_UseLightProbes: Optional[bool] = None


@unitypy_define
class LineRenderer(Renderer):
  m_CastShadows: Union[bool, int]
  m_Enabled: bool
  m_GameObject: PPtr[GameObject]
  m_LightmapIndex: int
  m_LightmapTilingOffset: Vector4f
  m_Materials: List[PPtr[Material]]
  m_Parameters: LineParameters
  m_Positions: List[Vector3f]
  m_ReceiveShadows: Union[bool, int]
  m_StaticBatchRoot: PPtr[Transform]
  m_UseWorldSpace: bool
  m_ApplyActiveColorSpace: Optional[bool] = None
  m_DynamicOccludee: Optional[int] = None
  m_LightProbeAnchor: Optional[PPtr[Transform]] = None
  m_LightProbeUsage: Optional[int] = None
  m_LightProbeVolumeOverride: Optional[PPtr[GameObject]] = None
  m_LightmapIndexDynamic: Optional[int] = None
  m_LightmapTilingOffsetDynamic: Optional[Vector4f] = None
  m_Loop: Optional[bool] = None
  m_MaskInteraction: Optional[int] = None
  m_MotionVectors: Optional[int] = None
  m_ProbeAnchor: Optional[PPtr[Transform]] = None
  m_RayTraceProcedural: Optional[int] = None
  m_RayTracingAccelStructBuildFlags: Optional[int] = None
  m_RayTracingAccelStructBuildFlagsOverride: Optional[int] = None
  m_RayTracingMode: Optional[int] = None
  m_ReflectionProbeUsage: Optional[int] = None
  m_RendererPriority: Optional[int] = None
  m_RenderingLayerMask: Optional[int] = None
  m_SmallMeshCulling: Optional[int] = None
  m_SortingLayer: Optional[int] = None
  m_SortingLayerID: Optional[int] = None
  m_SortingOrder: Optional[int] = None
  m_StaticBatchInfo: Optional[StaticBatchInfo] = None
  m_StaticShadowCaster: Optional[int] = None
  m_SubsetIndices: Optional[List[int]] = None
  m_UseLightProbes: Optional[bool] = None


@unitypy_define
class RendererFake(LineRenderer):
  m_CastShadows: int
  m_DynamicOccludee: int
  m_Enabled: bool
  m_GameObject: PPtr[GameObject]
  m_LightProbeUsage: int
  m_LightProbeVolumeOverride: PPtr[GameObject]
  m_LightmapIndex: int
  m_LightmapIndexDynamic: int
  m_LightmapTilingOffset: Vector4f
  m_LightmapTilingOffsetDynamic: Vector4f
  m_Loop: bool
  m_Materials: List[PPtr[Material]]
  m_MotionVectors: int
  m_Parameters: LineParameters
  m_Positions: List[Vector3f]
  m_ProbeAnchor: PPtr[Transform]
  m_ReceiveShadows: int
  m_ReflectionProbeUsage: int
  m_RendererPriority: int
  m_RenderingLayerMask: int
  m_SortingLayer: int
  m_SortingLayerID: int
  m_SortingOrder: int
  m_StaticBatchInfo: StaticBatchInfo
  m_StaticBatchRoot: PPtr[Transform]
  m_UseWorldSpace: bool
  m_RayTraceProcedural: Optional[int] = None
  m_RayTracingMode: Optional[int] = None


@unitypy_define
class MeshRenderer(Renderer):
  m_CastShadows: Union[bool, int]
  m_Enabled: bool
  m_GameObject: PPtr[GameObject]
  m_LightmapIndex: int
  m_LightmapTilingOffset: Vector4f
  m_Materials: List[PPtr[Material]]
  m_ReceiveShadows: Union[bool, int]
  m_StaticBatchRoot: PPtr[Transform]
  m_AdditionalVertexStreams: Optional[PPtr[Mesh]] = None
  m_DynamicOccludee: Optional[int] = None
  m_EnlightenVertexStream: Optional[PPtr[Mesh]] = None
  m_LightProbeAnchor: Optional[PPtr[Transform]] = None
  m_LightProbeUsage: Optional[int] = None
  m_LightProbeVolumeOverride: Optional[PPtr[GameObject]] = None
  m_LightmapIndexDynamic: Optional[int] = None
  m_LightmapTilingOffsetDynamic: Optional[Vector4f] = None
  m_MotionVectors: Optional[int] = None
  m_ProbeAnchor: Optional[PPtr[Transform]] = None
  m_RayTraceProcedural: Optional[int] = None
  m_RayTracingAccelStructBuildFlags: Optional[int] = None
  m_RayTracingAccelStructBuildFlagsOverride: Optional[int] = None
  m_RayTracingMode: Optional[int] = None
  m_ReflectionProbeUsage: Optional[int] = None
  m_RendererPriority: Optional[int] = None
  m_RenderingLayerMask: Optional[int] = None
  m_SmallMeshCulling: Optional[int] = None
  m_SortingLayer: Optional[int] = None
  m_SortingLayerID: Optional[int] = None
  m_SortingOrder: Optional[int] = None
  m_StaticBatchInfo: Optional[StaticBatchInfo] = None
  m_StaticShadowCaster: Optional[int] = None
  m_SubsetIndices: Optional[List[int]] = None
  m_UseLightProbes: Optional[bool] = None


@unitypy_define
class ParticleRenderer(Renderer):
  UV_Animation: UVAnimation
  m_CameraVelocityScale: float
  m_CastShadows: Union[bool, int]
  m_Enabled: bool
  m_GameObject: PPtr[GameObject]
  m_LengthScale: float
  m_LightmapIndex: int
  m_LightmapTilingOffset: Vector4f
  m_Materials: List[PPtr[Material]]
  m_MaxParticleSize: float
  m_ReceiveShadows: Union[bool, int]
  m_StaticBatchRoot: PPtr[Transform]
  m_StretchParticles: int
  m_VelocityScale: float
  m_DynamicOccludee: Optional[int] = None
  m_LightProbeAnchor: Optional[PPtr[Transform]] = None
  m_LightProbeUsage: Optional[int] = None
  m_LightProbeVolumeOverride: Optional[PPtr[GameObject]] = None
  m_LightmapIndexDynamic: Optional[int] = None
  m_LightmapTilingOffsetDynamic: Optional[Vector4f] = None
  m_MotionVectors: Optional[int] = None
  m_ProbeAnchor: Optional[PPtr[Transform]] = None
  m_ReflectionProbeUsage: Optional[int] = None
  m_RenderingLayerMask: Optional[int] = None
  m_SortingLayer: Optional[int] = None
  m_SortingLayerID: Optional[int] = None
  m_SortingOrder: Optional[int] = None
  m_StaticBatchInfo: Optional[StaticBatchInfo] = None
  m_SubsetIndices: Optional[List[int]] = None
  m_UseLightProbes: Optional[bool] = None


@unitypy_define
class ParticleSystemRenderer(Renderer):
  m_CameraVelocityScale: float
  m_CastShadows: Union[bool, int]
  m_Enabled: bool
  m_GameObject: PPtr[GameObject]
  m_LengthScale: float
  m_LightmapIndex: int
  m_LightmapTilingOffset: Vector4f
  m_Materials: List[PPtr[Material]]
  m_MaxParticleSize: float
  m_Mesh: PPtr[Mesh]
  m_ReceiveShadows: Union[bool, int]
  m_RenderMode: int
  m_SortMode: int
  m_SortingFudge: float
  m_StaticBatchRoot: PPtr[Transform]
  m_VelocityScale: float
  m_AllowRoll: Optional[bool] = None
  m_ApplyActiveColorSpace: Optional[bool] = None
  m_DynamicOccludee: Optional[int] = None
  m_EnableGPUInstancing: Optional[bool] = None
  m_Flip: Optional[Vector3f] = None
  m_FreeformStretching: Optional[bool] = None
  m_LightProbeAnchor: Optional[PPtr[Transform]] = None
  m_LightProbeUsage: Optional[int] = None
  m_LightProbeVolumeOverride: Optional[PPtr[GameObject]] = None
  m_LightmapIndexDynamic: Optional[int] = None
  m_LightmapTilingOffsetDynamic: Optional[Vector4f] = None
  m_MaskInteraction: Optional[int] = None
  m_Mesh1: Optional[PPtr[Mesh]] = None
  m_Mesh2: Optional[PPtr[Mesh]] = None
  m_Mesh3: Optional[PPtr[Mesh]] = None
  m_MeshDistribution: Optional[int] = None
  m_MeshWeighting: Optional[float] = None
  m_MeshWeighting1: Optional[float] = None
  m_MeshWeighting2: Optional[float] = None
  m_MeshWeighting3: Optional[float] = None
  m_MinParticleSize: Optional[float] = None
  m_MotionVectors: Optional[int] = None
  m_NormalDirection: Optional[float] = None
  m_Pivot: Optional[Vector3f] = None
  m_ProbeAnchor: Optional[PPtr[Transform]] = None
  m_RayTraceProcedural: Optional[int] = None
  m_RayTracingAccelStructBuildFlags: Optional[int] = None
  m_RayTracingAccelStructBuildFlagsOverride: Optional[int] = None
  m_RayTracingMode: Optional[int] = None
  m_ReflectionProbeUsage: Optional[int] = None
  m_RenderAlignment: Optional[int] = None
  m_RendererPriority: Optional[int] = None
  m_RenderingLayerMask: Optional[int] = None
  m_RotateWithStretchDirection: Optional[bool] = None
  m_ShadowBias: Optional[float] = None
  m_SmallMeshCulling: Optional[int] = None
  m_SortingLayer: Optional[int] = None
  m_SortingLayerID: Optional[int] = None
  m_SortingOrder: Optional[int] = None
  m_StaticBatchInfo: Optional[StaticBatchInfo] = None
  m_StaticShadowCaster: Optional[int] = None
  m_SubsetIndices: Optional[List[int]] = None
  m_TrailVertexStreams: Optional[List[int]] = None
  m_UseCustomTrailVertexStreams: Optional[bool] = None
  m_UseCustomVertexStreams: Optional[bool] = None
  m_UseLightProbes: Optional[bool] = None
  m_VertexStreamMask: Optional[int] = None
  m_VertexStreams: Optional[List[int]] = None


@unitypy_define
class SkinnedMeshRenderer(Renderer):
  m_AABB: AABB
  m_Bones: List[PPtr[Transform]]
  m_CastShadows: Union[bool, int]
  m_DirtyAABB: bool
  m_Enabled: bool
  m_GameObject: PPtr[GameObject]
  m_LightmapIndex: int
  m_LightmapTilingOffset: Vector4f
  m_Materials: List[PPtr[Material]]
  m_Mesh: PPtr[Mesh]
  m_Quality: int
  m_ReceiveShadows: Union[bool, int]
  m_StaticBatchRoot: PPtr[Transform]
  m_UpdateWhenOffscreen: bool
  m_BlendShapeWeights: Optional[List[float]] = None
  m_DynamicOccludee: Optional[int] = None
  m_LightProbeAnchor: Optional[PPtr[Transform]] = None
  m_LightProbeUsage: Optional[int] = None
  m_LightProbeVolumeOverride: Optional[PPtr[GameObject]] = None
  m_LightmapIndexDynamic: Optional[int] = None
  m_LightmapTilingOffsetDynamic: Optional[Vector4f] = None
  m_MotionVectors: Optional[int] = None
  m_ProbeAnchor: Optional[PPtr[Transform]] = None
  m_RayTraceProcedural: Optional[int] = None
  m_RayTracingAccelStructBuildFlags: Optional[int] = None
  m_RayTracingAccelStructBuildFlagsOverride: Optional[int] = None
  m_RayTracingMode: Optional[int] = None
  m_ReflectionProbeUsage: Optional[int] = None
  m_RendererPriority: Optional[int] = None
  m_RenderingLayerMask: Optional[int] = None
  m_RootBone: Optional[PPtr[Transform]] = None
  m_SkinnedMotionVectors: Optional[bool] = None
  m_SmallMeshCulling: Optional[int] = None
  m_SortingLayer: Optional[int] = None
  m_SortingLayerID: Optional[int] = None
  m_SortingOrder: Optional[int] = None
  m_StaticBatchInfo: Optional[StaticBatchInfo] = None
  m_StaticShadowCaster: Optional[int] = None
  m_SubsetIndices: Optional[List[int]] = None
  m_UseLightProbes: Optional[bool] = None


@unitypy_define
class SpriteMask(Renderer):
  m_BackSortingLayer: int
  m_BackSortingOrder: int
  m_CastShadows: int
  m_Enabled: bool
  m_FrontSortingLayer: int
  m_FrontSortingOrder: int
  m_GameObject: PPtr[GameObject]
  m_IsCustomRangeActive: bool
  m_LightProbeUsage: int
  m_LightProbeVolumeOverride: PPtr[GameObject]
  m_LightmapIndex: int
  m_LightmapIndexDynamic: int
  m_LightmapTilingOffset: Vector4f
  m_LightmapTilingOffsetDynamic: Vector4f
  m_MaskAlphaCutoff: float
  m_Materials: List[PPtr[Material]]
  m_MotionVectors: int
  m_ProbeAnchor: PPtr[Transform]
  m_ReceiveShadows: int
  m_ReflectionProbeUsage: int
  m_SortingLayer: int
  m_SortingLayerID: int
  m_SortingOrder: int
  m_Sprite: PPtr[Sprite]
  m_StaticBatchInfo: StaticBatchInfo
  m_StaticBatchRoot: PPtr[Transform]
  m_BackSortingLayerID: Optional[int] = None
  m_DynamicOccludee: Optional[int] = None
  m_FrontSortingLayerID: Optional[int] = None
  m_MaskSource: Optional[int] = None
  m_RayTraceProcedural: Optional[int] = None
  m_RayTracingAccelStructBuildFlags: Optional[int] = None
  m_RayTracingAccelStructBuildFlagsOverride: Optional[int] = None
  m_RayTracingMode: Optional[int] = None
  m_RendererPriority: Optional[int] = None
  m_RenderingLayerMask: Optional[int] = None
  m_SmallMeshCulling: Optional[int] = None
  m_SpriteSortPoint: Optional[int] = None
  m_StaticShadowCaster: Optional[int] = None


@unitypy_define
class SpriteRenderer(Renderer):
  m_CastShadows: Union[bool, int]
  m_Color: ColorRGBA
  m_Enabled: bool
  m_GameObject: PPtr[GameObject]
  m_LightmapIndex: int
  m_LightmapTilingOffset: Vector4f
  m_Materials: List[PPtr[Material]]
  m_ReceiveShadows: Union[bool, int]
  m_SortingOrder: int
  m_Sprite: PPtr[Sprite]
  m_StaticBatchRoot: PPtr[Transform]
  m_AdaptiveModeThreshold: Optional[float] = None
  m_DrawMode: Optional[int] = None
  m_DynamicOccludee: Optional[int] = None
  m_FlipX: Optional[bool] = None
  m_FlipY: Optional[bool] = None
  m_LightProbeAnchor: Optional[PPtr[Transform]] = None
  m_LightProbeUsage: Optional[int] = None
  m_LightProbeVolumeOverride: Optional[PPtr[GameObject]] = None
  m_LightmapIndexDynamic: Optional[int] = None
  m_LightmapTilingOffsetDynamic: Optional[Vector4f] = None
  m_MaskInteraction: Optional[int] = None
  m_MotionVectors: Optional[int] = None
  m_ProbeAnchor: Optional[PPtr[Transform]] = None
  m_RayTraceProcedural: Optional[int] = None
  m_RayTracingAccelStructBuildFlags: Optional[int] = None
  m_RayTracingAccelStructBuildFlagsOverride: Optional[int] = None
  m_RayTracingMode: Optional[int] = None
  m_ReflectionProbeUsage: Optional[int] = None
  m_RendererPriority: Optional[int] = None
  m_RenderingLayerMask: Optional[int] = None
  m_Size: Optional[Vector2f] = None
  m_SmallMeshCulling: Optional[int] = None
  m_SortingLayer: Optional[int] = None
  m_SortingLayerID: Optional[int] = None
  m_SpriteSortPoint: Optional[int] = None
  m_SpriteTileMode: Optional[int] = None
  m_StaticBatchInfo: Optional[StaticBatchInfo] = None
  m_StaticShadowCaster: Optional[int] = None
  m_SubsetIndices: Optional[List[int]] = None
  m_UseLightProbes: Optional[bool] = None
  m_WasSpriteAssigned: Optional[bool] = None


@unitypy_define
class SpriteShapeRenderer(Renderer):
  m_CastShadows: int
  m_Color: ColorRGBA
  m_DynamicOccludee: int
  m_Enabled: bool
  m_GameObject: PPtr[GameObject]
  m_LightProbeUsage: int
  m_LightProbeVolumeOverride: PPtr[GameObject]
  m_LightmapIndex: int
  m_LightmapIndexDynamic: int
  m_LightmapTilingOffset: Vector4f
  m_LightmapTilingOffsetDynamic: Vector4f
  m_LocalAABB: AABB
  m_MaskInteraction: int
  m_Materials: List[PPtr[Material]]
  m_MotionVectors: int
  m_ProbeAnchor: PPtr[Transform]
  m_ReceiveShadows: int
  m_ReflectionProbeUsage: int
  m_RenderingLayerMask: int
  m_ShapeTexture: PPtr[Texture2D]
  m_SortingLayer: int
  m_SortingLayerID: int
  m_SortingOrder: int
  m_Sprites: List[PPtr[Sprite]]
  m_StaticBatchInfo: StaticBatchInfo
  m_StaticBatchRoot: PPtr[Transform]
  m_RayTraceProcedural: Optional[int] = None
  m_RayTracingAccelStructBuildFlags: Optional[int] = None
  m_RayTracingAccelStructBuildFlagsOverride: Optional[int] = None
  m_RayTracingMode: Optional[int] = None
  m_RendererPriority: Optional[int] = None
  m_SmallMeshCulling: Optional[int] = None
  m_SpriteSortPoint: Optional[int] = None
  m_StaticShadowCaster: Optional[int] = None


@unitypy_define
class TilemapRenderer(Renderer):
  m_CastShadows: int
  m_ChunkSize: int3_storage
  m_DynamicOccludee: int
  m_Enabled: bool
  m_GameObject: PPtr[GameObject]
  m_LightProbeUsage: int
  m_LightProbeVolumeOverride: PPtr[GameObject]
  m_LightmapIndex: int
  m_LightmapIndexDynamic: int
  m_LightmapTilingOffset: Vector4f
  m_LightmapTilingOffsetDynamic: Vector4f
  m_MaskInteraction: int
  m_Materials: List[PPtr[Material]]
  m_MaxChunkCount: int
  m_MaxFrameAge: int
  m_MotionVectors: int
  m_ProbeAnchor: PPtr[Transform]
  m_ReceiveShadows: int
  m_ReflectionProbeUsage: int
  m_SortOrder: int
  m_SortingLayer: int
  m_SortingLayerID: int
  m_SortingOrder: int
  m_StaticBatchInfo: StaticBatchInfo
  m_StaticBatchRoot: PPtr[Transform]
  m_ChunkCullingBounds: Optional[Vector3f] = None
  m_DetectChunkCullingBounds: Optional[int] = None
  m_Mode: Optional[int] = None
  m_RayTraceProcedural: Optional[int] = None
  m_RayTracingAccelStructBuildFlags: Optional[int] = None
  m_RayTracingAccelStructBuildFlagsOverride: Optional[int] = None
  m_RayTracingMode: Optional[int] = None
  m_RendererPriority: Optional[int] = None
  m_RenderingLayerMask: Optional[int] = None
  m_SmallMeshCulling: Optional[int] = None
  m_StaticShadowCaster: Optional[int] = None


@unitypy_define
class TrailRenderer(Renderer):
  m_Autodestruct: bool
  m_CastShadows: Union[bool, int]
  m_Enabled: bool
  m_GameObject: PPtr[GameObject]
  m_LightmapIndex: int
  m_LightmapTilingOffset: Vector4f
  m_Materials: List[PPtr[Material]]
  m_MinVertexDistance: float
  m_ReceiveShadows: Union[bool, int]
  m_StaticBatchRoot: PPtr[Transform]
  m_Time: float
  m_ApplyActiveColorSpace: Optional[bool] = None
  m_Colors: Optional[Gradient] = None
  m_DynamicOccludee: Optional[int] = None
  m_Emitting: Optional[bool] = None
  m_EndWidth: Optional[float] = None
  m_LightProbeAnchor: Optional[PPtr[Transform]] = None
  m_LightProbeUsage: Optional[int] = None
  m_LightProbeVolumeOverride: Optional[PPtr[GameObject]] = None
  m_LightmapIndexDynamic: Optional[int] = None
  m_LightmapTilingOffsetDynamic: Optional[Vector4f] = None
  m_MaskInteraction: Optional[int] = None
  m_MotionVectors: Optional[int] = None
  m_Parameters: Optional[LineParameters] = None
  m_ProbeAnchor: Optional[PPtr[Transform]] = None
  m_RayTraceProcedural: Optional[int] = None
  m_RayTracingAccelStructBuildFlags: Optional[int] = None
  m_RayTracingAccelStructBuildFlagsOverride: Optional[int] = None
  m_RayTracingMode: Optional[int] = None
  m_ReflectionProbeUsage: Optional[int] = None
  m_RendererPriority: Optional[int] = None
  m_RenderingLayerMask: Optional[int] = None
  m_SmallMeshCulling: Optional[int] = None
  m_SortingLayer: Optional[int] = None
  m_SortingLayerID: Optional[int] = None
  m_SortingOrder: Optional[int] = None
  m_StartWidth: Optional[float] = None
  m_StaticBatchInfo: Optional[StaticBatchInfo] = None
  m_StaticShadowCaster: Optional[int] = None
  m_SubsetIndices: Optional[List[int]] = None
  m_UseLightProbes: Optional[bool] = None


@unitypy_define
class UIRenderer(Renderer):
  m_GameObject: PPtr[GameObject]
  m_CastShadows: Optional[int] = None
  m_DynamicOccludee: Optional[int] = None
  m_Enabled: Optional[bool] = None
  m_LightProbeUsage: Optional[int] = None
  m_LightProbeVolumeOverride: Optional[PPtr[GameObject]] = None
  m_LightmapIndex: Optional[int] = None
  m_LightmapIndexDynamic: Optional[int] = None
  m_LightmapTilingOffset: Optional[Vector4f] = None
  m_LightmapTilingOffsetDynamic: Optional[Vector4f] = None
  m_Materials: Optional[List[PPtr[Material]]] = None
  m_MotionVectors: Optional[int] = None
  m_ProbeAnchor: Optional[PPtr[Transform]] = None
  m_RayTraceProcedural: Optional[int] = None
  m_RayTracingAccelStructBuildFlags: Optional[int] = None
  m_RayTracingAccelStructBuildFlagsOverride: Optional[int] = None
  m_RayTracingMode: Optional[int] = None
  m_ReceiveShadows: Optional[int] = None
  m_ReflectionProbeUsage: Optional[int] = None
  m_RendererPriority: Optional[int] = None
  m_RenderingLayerMask: Optional[int] = None
  m_SmallMeshCulling: Optional[int] = None
  m_SortingLayer: Optional[int] = None
  m_SortingLayerID: Optional[int] = None
  m_SortingOrder: Optional[int] = None
  m_StaticBatchInfo: Optional[StaticBatchInfo] = None
  m_StaticBatchRoot: Optional[PPtr[Transform]] = None
  m_StaticShadowCaster: Optional[int] = None


@unitypy_define
class VFXRenderer(Renderer):
  m_CastShadows: int
  m_DynamicOccludee: int
  m_Enabled: bool
  m_GameObject: PPtr[GameObject]
  m_LightProbeUsage: int
  m_LightProbeVolumeOverride: PPtr[GameObject]
  m_LightmapIndex: int
  m_LightmapIndexDynamic: int
  m_LightmapTilingOffset: Vector4f
  m_LightmapTilingOffsetDynamic: Vector4f
  m_MotionVectors: int
  m_ProbeAnchor: PPtr[Transform]
  m_ReceiveShadows: int
  m_ReflectionProbeUsage: int
  m_RendererPriority: int
  m_RenderingLayerMask: int
  m_SortingLayer: int
  m_SortingLayerID: int
  m_SortingOrder: int
  m_StaticBatchInfo: StaticBatchInfo
  m_StaticBatchRoot: PPtr[Transform]
  m_Materials: Optional[List[PPtr[Material]]] = None
  m_RayTraceProcedural: Optional[int] = None
  m_RayTracingAccelStructBuildFlags: Optional[int] = None
  m_RayTracingAccelStructBuildFlagsOverride: Optional[int] = None
  m_RayTracingMode: Optional[int] = None
  m_SmallMeshCulling: Optional[int] = None
  m_StaticShadowCaster: Optional[int] = None


@unitypy_define
class Rigidbody(Component):
  m_AngularDrag: float
  m_CollisionDetection: int
  m_Constraints: int
  m_Drag: float
  m_GameObject: PPtr[GameObject]
  m_Interpolate: int
  m_IsKinematic: bool
  m_Mass: float
  m_UseGravity: bool
  m_CenterOfMass: Optional[Vector3f] = None
  m_ExcludeLayers: Optional[BitField] = None
  m_ImplicitCom: Optional[bool] = None
  m_ImplicitTensor: Optional[bool] = None
  m_IncludeLayers: Optional[BitField] = None
  m_InertiaRotation: Optional[Quaternionf] = None
  m_InertiaTensor: Optional[Vector3f] = None


@unitypy_define
class Rigidbody2D(Component):
  m_CollisionDetection: int
  m_GameObject: PPtr[GameObject]
  m_GravityScale: float
  m_Interpolate: int
  m_Mass: float
  m_SleepingMode: int
  m_AngularDamping: Optional[float] = None
  m_AngularDrag: Optional[float] = None
  m_BodyType: Optional[int] = None
  m_Constraints: Optional[int] = None
  m_ExcludeLayers: Optional[BitField] = None
  m_FixedAngle: Optional[bool] = None
  m_IncludeLayers: Optional[BitField] = None
  m_IsKinematic: Optional[bool] = None
  m_LinearDamping: Optional[float] = None
  m_LinearDrag: Optional[float] = None
  m_Material: Optional[PPtr[PhysicsMaterial2D]] = None
  m_Simulated: Optional[bool] = None
  m_UseAutoMass: Optional[bool] = None
  m_UseFullKinematicContacts: Optional[bool] = None


@unitypy_define
class TextMesh(Component):
  m_Alignment: int
  m_Anchor: int
  m_CharacterSize: float
  m_Font: PPtr[Font]
  m_FontSize: int
  m_FontStyle: int
  m_GameObject: PPtr[GameObject]
  m_LineSpacing: float
  m_OffsetZ: float
  m_TabSize: float
  m_Text: str
  m_Color: Optional[ColorRGBA] = None
  m_RichText: Optional[bool] = None


@unitypy_define
class Transform(Component):
  m_Children: List[PPtr[Transform]]
  m_Father: PPtr[Transform]
  m_GameObject: PPtr[GameObject]
  m_LocalPosition: Vector3f
  m_LocalRotation: Quaternionf
  m_LocalScale: Vector3f


@unitypy_define
class RectTransform(Transform):
  m_AnchorMax: Vector2f
  m_AnchorMin: Vector2f
  m_GameObject: PPtr[GameObject]
  m_Pivot: Vector2f
  m_SizeDelta: Vector2f
  m_AnchoredPosition: Optional[Vector2f] = None
  m_Children: Optional[List[PPtr[Transform]]] = None
  m_Father: Optional[PPtr[Transform]] = None
  m_LocalPosition: Optional[Vector3f] = None
  m_LocalRotation: Optional[Quaternionf] = None
  m_LocalScale: Optional[Vector3f] = None
  m_Position: Optional[Vector2f] = None


@unitypy_define
class Tree(Component):
  m_GameObject: PPtr[GameObject]
  m_SpeedTreeWindAsset: Optional[PPtr[SpeedTreeWindAsset]] = None


@unitypy_define
class WorldAnchor(Component):
  m_GameObject: PPtr[GameObject]


@unitypy_define
class WorldParticleCollider(Component):
  m_BounceFactor: float
  m_CollidesWith: BitField
  m_CollisionEnergyLoss: float
  m_GameObject: PPtr[GameObject]
  m_MinKillVelocity: float
  m_SendCollisionMessage: bool


@unitypy_define
class GameObject(EditorExtension):
  m_Component: Union[List[ComponentPair], List[Tuple[int, PPtr[Component]]]]
  m_IsActive: Union[bool, int]
  m_Layer: int
  m_Name: str
  m_Tag: int


@unitypy_define
class NamedObject(EditorExtension, ABC):
  pass


@unitypy_define
class AnimatorState(NamedObject):
  m_CycleOffset: float
  m_IKOnFeet: bool
  m_Mirror: bool
  m_Motion: PPtr[Motion]
  m_Name: str
  m_Position: Vector3f
  m_Speed: float
  m_StateMachineBehaviours: List[PPtr[MonoBehaviour]]
  m_Tag: str
  m_Transitions: List[PPtr[AnimatorStateTransition]]
  m_WriteDefaultValues: bool
  m_CycleOffsetParameter: Optional[str] = None
  m_CycleOffsetParameterActive: Optional[bool] = None
  m_MirrorParameter: Optional[str] = None
  m_MirrorParameterActive: Optional[bool] = None
  m_SpeedParameter: Optional[str] = None
  m_SpeedParameterActive: Optional[bool] = None
  m_TimeParameter: Optional[str] = None
  m_TimeParameterActive: Optional[bool] = None


@unitypy_define
class AnimatorStateMachine(NamedObject):
  m_AnyStatePosition: Vector3f
  m_AnyStateTransitions: List[PPtr[AnimatorStateTransition]]
  m_ChildStateMachines: List[ChildAnimatorStateMachine]
  m_ChildStates: List[ChildAnimatorState]
  m_DefaultState: PPtr[AnimatorState]
  m_EntryPosition: Vector3f
  m_EntryTransitions: List[PPtr[AnimatorTransition]]
  m_ExitPosition: Vector3f
  m_Name: str
  m_ParentStateMachinePosition: Vector3f
  m_StateMachineBehaviours: List[PPtr[MonoBehaviour]]
  m_StateMachineTransitions: List[
    Tuple[PPtr[AnimatorStateMachine], List[PPtr[AnimatorTransition]]]
  ]


@unitypy_define
class AnimatorTransitionBase(NamedObject):
  m_Conditions: List[AnimatorCondition]
  m_DstState: PPtr[AnimatorState]
  m_DstStateMachine: PPtr[AnimatorStateMachine]
  m_IsExit: bool
  m_Mute: bool
  m_Name: str
  m_Solo: bool


@unitypy_define
class AnimatorStateTransition(AnimatorTransitionBase):
  m_CanTransitionToSelf: bool
  m_Conditions: List[AnimatorCondition]
  m_DstState: PPtr[AnimatorState]
  m_DstStateMachine: PPtr[AnimatorStateMachine]
  m_ExitTime: float
  m_HasExitTime: bool
  m_InterruptionSource: int
  m_IsExit: bool
  m_Mute: bool
  m_Name: str
  m_OrderedInterruption: bool
  m_Solo: bool
  m_TransitionDuration: float
  m_TransitionOffset: float
  m_HasFixedDuration: Optional[bool] = None


@unitypy_define
class AnimatorTransition(AnimatorTransitionBase):
  m_Conditions: List[AnimatorCondition]
  m_DstState: PPtr[AnimatorState]
  m_DstStateMachine: PPtr[AnimatorStateMachine]
  m_IsExit: bool
  m_Mute: bool
  m_Name: str
  m_Solo: bool


@unitypy_define
class AssetBundle(NamedObject):
  m_Container: List[Tuple[str, AssetInfo]]
  m_MainAsset: AssetInfo
  m_Name: str
  m_PreloadTable: List[PPtr[Object]]
  m_AssetBundleName: Optional[str] = None
  m_ClassCompatibility: Optional[List[Tuple[int, int]]] = None
  m_ClassVersionMap: Optional[List[Tuple[int, int]]] = None
  m_Dependencies: Optional[List[str]] = None
  m_ExplicitDataLayout: Optional[int] = None
  m_IsStreamedSceneAssetBundle: Optional[bool] = None
  m_PathFlags: Optional[int] = None
  m_RuntimeCompatibility: Optional[int] = None
  m_SceneHashes: Optional[List[Tuple[str, str]]] = None
  m_ScriptCompatibility: Optional[List[AssetBundleScriptInfo]] = None


@unitypy_define
class AssetBundleManifest(NamedObject):
  AssetBundleInfos: List[Tuple[int, AssetBundleInfo]]
  AssetBundleNames: List[Tuple[int, str]]
  AssetBundlesWithVariant: List[int]
  m_Name: str


@unitypy_define
class AssetImportInProgressProxy(NamedObject):
  m_Name: str


@unitypy_define
class AssetImporter(NamedObject, ABC):
  pass


@unitypy_define
class ASTCImporter(AssetImporter):
  m_AssetBundleName: str
  m_AssetBundleVariant: str
  m_Name: str
  m_UserData: str


@unitypy_define
class AndroidAssetPackImporter(AssetImporter):
  m_AssetBundleName: str
  m_AssetBundleVariant: str
  m_ExternalObjects: List[Tuple[SourceAssetIdentifier, PPtr[Object]]]
  m_Name: str
  m_UsedFileIDs: List[int]
  m_UserData: str


@unitypy_define
class AssemblyDefinitionImporter(AssetImporter):
  m_AssetBundleName: str
  m_AssetBundleVariant: str
  m_ExternalObjects: List[Tuple[SourceAssetIdentifier, PPtr[Object]]]
  m_Name: str
  m_UserData: str
  m_UsedFileIDs: Optional[List[int]] = None


@unitypy_define
class AssemblyDefinitionReferenceImporter(AssetImporter):
  m_AssetBundleName: str
  m_AssetBundleVariant: str
  m_ExternalObjects: List[Tuple[SourceAssetIdentifier, PPtr[Object]]]
  m_Name: str
  m_UsedFileIDs: List[int]
  m_UserData: str


@unitypy_define
class AudioImporter(AssetImporter):
  m_3D: bool
  m_ForceToMono: bool
  m_Name: str
  audio_preview_data: Optional[bytes] = None
  m_Ambisonic: Optional[bool] = None
  m_AssetBundleName: Optional[str] = None
  m_AssetBundleVariant: Optional[str] = None
  m_DefaultSettings: Optional[SampleSettings] = None
  m_ExternalObjects: Optional[List[Tuple[SourceAssetIdentifier, PPtr[Object]]]] = None
  m_FileIDToRecycleName: Optional[List[Tuple[int, str]]] = None
  m_Format: Optional[int] = None
  m_LoadInBackground: Optional[bool] = None
  m_Loopable: Optional[bool] = None
  m_NewHashIdentity: Optional[MdFour] = None
  m_Normalize: Optional[bool] = None
  m_OldHashIdentity: Optional[MdFour] = None
  m_Output: Optional[Union[AudioImporterOutput, Output]] = None
  m_PlatformSettingOverrides: Optional[
    Union[List[Tuple[str, SampleSettings]], List[Tuple[int, SampleSettings]]]
  ] = None
  m_PreloadAudioData: Optional[bool] = None
  m_PreviewData: Optional[PreviewData] = None
  m_PreviewDataLength: Optional[int] = None
  m_Quality: Optional[float] = None
  m_Stream: Optional[int] = None
  m_UseHardware: Optional[bool] = None
  m_UsedFileIDs: Optional[List[int]] = None
  m_UserData: Optional[str] = None


@unitypy_define
class BuildArchiveImporter(AssetImporter):
  m_AssetBundleName: str
  m_AssetBundleVariant: str
  m_ExternalObjects: List[Tuple[SourceAssetIdentifier, PPtr[Object]]]
  m_Name: str
  m_UsedFileIDs: List[int]
  m_UserData: str


@unitypy_define
class BuildInstructionImporter(AssetImporter):
  m_AssetBundleName: str
  m_AssetBundleVariant: str
  m_ExternalObjects: List[Tuple[SourceAssetIdentifier, PPtr[Object]]]
  m_Name: str
  m_UsedFileIDs: List[int]
  m_UserData: str


@unitypy_define
class BuildMetaDataImporter(AssetImporter):
  m_AssetBundleName: str
  m_AssetBundleVariant: str
  m_ExternalObjects: List[Tuple[SourceAssetIdentifier, PPtr[Object]]]
  m_Name: str
  m_UsedFileIDs: List[int]
  m_UserData: str


@unitypy_define
class C4DImporter(AssetImporter):
  m_AssetBundleName: str
  m_AssetBundleVariant: str
  m_ExternalObjects: List[Tuple[SourceAssetIdentifier, PPtr[Object]]]
  m_Name: str
  m_UsedFileIDs: List[int]
  m_UserData: str


@unitypy_define
class ComputeShaderImporter(AssetImporter):
  m_Name: str
  m_UserData: str
  m_AssetBundleName: Optional[str] = None
  m_AssetBundleVariant: Optional[str] = None
  m_CurrentAPIMask: Optional[int] = None
  m_CurrentBuildTarget: Optional[int] = None
  m_ExternalObjects: Optional[List[Tuple[SourceAssetIdentifier, PPtr[Object]]]] = None
  m_PreprocessorOverride: Optional[int] = None
  m_UsedFileIDs: Optional[List[int]] = None


@unitypy_define
class DDSImporter(AssetImporter):
  m_Name: str
  m_AssetBundleName: Optional[str] = None
  m_AssetBundleVariant: Optional[str] = None
  m_FileIDToRecycleName: Optional[List[Tuple[int, str]]] = None
  m_IsReadable: Optional[bool] = None
  m_NewHashIdentity: Optional[MdFour] = None
  m_OldHashIdentity: Optional[MdFour] = None
  m_UserData: Optional[str] = None


@unitypy_define
class DefaultImporter(AssetImporter):
  m_Name: str
  m_AssetBundleName: Optional[str] = None
  m_AssetBundleVariant: Optional[str] = None
  m_ExternalObjects: Optional[List[Tuple[SourceAssetIdentifier, PPtr[Object]]]] = None
  m_FileIDToRecycleName: Optional[List[Tuple[int, str]]] = None
  m_NewHashIdentity: Optional[MdFour] = None
  m_OldHashIdentity: Optional[MdFour] = None
  m_UsedFileIDs: Optional[List[int]] = None
  m_UserData: Optional[str] = None


@unitypy_define
class IHVImageFormatImporter(AssetImporter):
  m_AssetBundleName: str
  m_AssetBundleVariant: str
  m_IsReadable: bool
  m_Name: str
  m_TextureSettings: GLTextureSettings
  m_UserData: str
  m_ExternalObjects: Optional[List[Tuple[SourceAssetIdentifier, PPtr[Object]]]] = None
  m_IgnoreMipmapLimit: Optional[bool] = None
  m_MipmapLimitGroupName: Optional[str] = None
  m_StreamingMipmaps: Optional[bool] = None
  m_StreamingMipmapsPriority: Optional[int] = None
  m_UsedFileIDs: Optional[List[int]] = None
  m_sRGBTexture: Optional[bool] = None


@unitypy_define
class KTXImporter(AssetImporter):
  m_AssetBundleName: str
  m_AssetBundleVariant: str
  m_Name: str
  m_UserData: str


@unitypy_define
class LibraryAssetImporter(AssetImporter):
  m_Name: str
  m_AssetBundleName: Optional[str] = None
  m_AssetBundleVariant: Optional[str] = None
  m_ExternalObjects: Optional[List[Tuple[SourceAssetIdentifier, PPtr[Object]]]] = None
  m_FileIDToRecycleName: Optional[List[Tuple[int, str]]] = None
  m_NewHashIdentity: Optional[MdFour] = None
  m_OldHashIdentity: Optional[MdFour] = None
  m_UsedFileIDs: Optional[List[int]] = None
  m_UserData: Optional[str] = None


@unitypy_define
class LocalizationImporter(AssetImporter):
  m_AssetBundleName: str
  m_AssetBundleVariant: str
  m_ExternalObjects: List[Tuple[SourceAssetIdentifier, PPtr[Object]]]
  m_Name: str
  m_UserData: str
  m_UsedFileIDs: Optional[List[int]] = None


@unitypy_define
class ModelImporter(AssetImporter, ABC):
  pass


@unitypy_define
class FBXImporter(ModelImporter):
  m_AddColliders: bool
  m_AnimationCompression: int
  m_AnimationPositionError: float
  m_AnimationRotationError: float
  m_AnimationScaleError: float
  m_AnimationWrapMode: int
  m_BakeSimulation: bool
  m_ClipAnimations: List[ClipAnimationInfo]
  m_GlobalScale: float
  m_HasExtraRoot: bool
  m_ImportedRoots: List[PPtr[GameObject]]
  m_MeshCompression: int
  m_Name: str
  m_UseFileUnits: bool
  normalSmoothAngle: float
  bakeAxisConversion: Optional[bool] = None
  blendShapeNormalImportMode: Optional[int] = None
  generateSecondaryUV: Optional[bool] = None
  indexFormat: Optional[int] = None
  keepQuads: Optional[bool] = None
  legacyComputeAllNormalsFromSmoothingGroupsWhenMeshHasBlendShapes: Optional[bool] = (
    None
  )
  m_AddHumanoidExtraRootOnlyWhenUsingAvatar: Optional[bool] = None
  m_AdditionalBone: Optional[bool] = None
  m_AnimationDoRetargetingWarnings: Optional[bool] = None
  m_AnimationImportErrors: Optional[str] = None
  m_AnimationImportWarnings: Optional[str] = None
  m_AnimationRetargetingWarnings: Optional[str] = None
  m_AnimationType: Optional[int] = None
  m_AssetBundleName: Optional[str] = None
  m_AssetBundleVariant: Optional[str] = None
  m_AutoGenerateAvatarMappingIfUnspecified: Optional[bool] = None
  m_AutoMapExternalMaterials: Optional[bool] = None
  m_AvatarSetup: Optional[int] = None
  m_ContainsAnimation: Optional[bool] = None
  m_CopyAvatar: Optional[bool] = None
  m_ExternalObjects: Optional[List[Tuple[SourceAssetIdentifier, PPtr[Object]]]] = None
  m_ExtraExposedTransformPaths: Optional[List[str]] = None
  m_ExtraUserProperties: Optional[List[str]] = None
  m_FileIDToRecycleName: Optional[List[Tuple[int, str]]] = None
  m_FileIdsGeneration: Optional[int] = None
  m_FileScale: Optional[float] = None
  m_FileScaleFactor: Optional[float] = None
  m_FileScaleUnit: Optional[str] = None
  m_FirstImportVersion: Optional[int] = None
  m_GenerateAnimations: Optional[int] = None
  m_GenerateMaterials: Optional[int] = None
  m_HasEmbeddedTextures: Optional[bool] = None
  m_HasPreviousCalculatedGlobalScale: Optional[bool] = None
  m_HumanDescription: Optional[HumanDescription] = None
  m_HumanoidOversampling: Optional[int] = None
  m_ImportAnimatedCustomProperties: Optional[bool] = None
  m_ImportAnimation: Optional[bool] = None
  m_ImportBlendShapeDeformPercent: Optional[bool] = None
  m_ImportBlendShapes: Optional[bool] = None
  m_ImportCameras: Optional[bool] = None
  m_ImportConstraints: Optional[bool] = None
  m_ImportLights: Optional[bool] = None
  m_ImportMaterials: Optional[bool] = None
  m_ImportPhysicalCameras: Optional[bool] = None
  m_ImportVisibility: Optional[bool] = None
  m_ImportedTakeInfos: Optional[List[TakeInfo]] = None
  m_InternalIDToNameTable: Optional[List[Tuple[Tuple[int, int], str]]] = None
  m_IsReadable: Optional[bool] = None
  m_LODScreenPercentages: Optional[List[float]] = None
  m_LastHumanDescriptionAvatarSource: Optional[PPtr[Avatar]] = None
  m_LegacyGenerateAnimations: Optional[int] = None
  m_MaterialImportMode: Optional[int] = None
  m_MaterialLocation: Optional[int] = None
  m_MaterialName: Optional[int] = None
  m_MaterialSearch: Optional[int] = None
  m_Materials: Optional[List[SourceAssetIdentifier]] = None
  m_MeshSettings_generateSecondaryUV: Optional[bool] = None
  m_MeshSettings_normalImportMode: Optional[int] = None
  m_MeshSettings_secondaryUVAngleDistortion: Optional[float] = None
  m_MeshSettings_secondaryUVAreaDistortion: Optional[float] = None
  m_MeshSettings_secondaryUVHardAngle: Optional[float] = None
  m_MeshSettings_secondaryUVPackMargin: Optional[float] = None
  m_MeshSettings_swapUVChannels: Optional[bool] = None
  m_MeshSettings_tangentImportMode: Optional[int] = None
  m_MotionNodeName: Optional[str] = None
  m_NewHashIdentity: Optional[MdFour] = None
  m_NodeNameCollisionStrategy: Optional[int] = None
  m_OldHashIdentity: Optional[MdFour] = None
  m_OptimizeGameObjects: Optional[bool] = None
  m_PreserveHierarchy: Optional[bool] = None
  m_PreviousCalculatedGlobalScale: Optional[float] = None
  m_ReferencedClips: Optional[List[GUID]] = None
  m_RemapMaterialsIfMaterialImportModeIsNone: Optional[bool] = None
  m_RemoveConstantScaleCurves: Optional[bool] = None
  m_ResampleCurves: Optional[bool] = None
  m_ResampleRotations: Optional[bool] = None
  m_RigImportErrors: Optional[str] = None
  m_RigImportWarnings: Optional[str] = None
  m_SortHierarchyByName: Optional[bool] = None
  m_SplitAnimations: Optional[bool] = None
  m_StrictVertexDataChecks: Optional[bool] = None
  m_SupportsEmbeddedMaterials: Optional[bool] = None
  m_UseFileScale: Optional[bool] = None
  m_UseSRGBMaterialColor: Optional[bool] = None
  m_UsedFileIDs: Optional[List[int]] = None
  m_UserData: Optional[str] = None
  maxBonesPerVertex: Optional[int] = None
  meshOptimizationFlags: Optional[int] = None
  minBoneWeight: Optional[float] = None
  normalCalculationMode: Optional[int] = None
  normalImportMode: Optional[int] = None
  normalSmoothingSource: Optional[int] = None
  optimizeBones: Optional[bool] = None
  optimizeMesh: Optional[bool] = None
  optimizeMeshForGPU: Optional[bool] = None
  secondaryUVAngleDistortion: Optional[float] = None
  secondaryUVAreaDistortion: Optional[float] = None
  secondaryUVHardAngle: Optional[float] = None
  secondaryUVMarginMethod: Optional[int] = None
  secondaryUVMinLightmapResolution: Optional[float] = None
  secondaryUVMinObjectScale: Optional[float] = None
  secondaryUVPackMargin: Optional[float] = None
  skinWeightsMode: Optional[int] = None
  splitTangentsAcrossUV: Optional[bool] = None
  swapUVChannels: Optional[bool] = None
  tangentImportMode: Optional[int] = None
  weldVertices: Optional[bool] = None


@unitypy_define
class Mesh3DSImporter(ModelImporter):
  m_AddColliders: bool
  m_AnimationCompression: int
  m_AnimationPositionError: float
  m_AnimationRotationError: float
  m_AnimationScaleError: float
  m_AnimationWrapMode: int
  m_BakeSimulation: bool
  m_ClipAnimations: List[ClipAnimationInfo]
  m_GlobalScale: float
  m_HasExtraRoot: bool
  m_ImportedRoots: List[PPtr[GameObject]]
  m_MeshCompression: int
  m_Name: str
  m_UseFileUnits: bool
  normalSmoothAngle: float
  bakeAxisConversion: Optional[bool] = None
  blendShapeNormalImportMode: Optional[int] = None
  generateSecondaryUV: Optional[bool] = None
  indexFormat: Optional[int] = None
  keepQuads: Optional[bool] = None
  legacyComputeAllNormalsFromSmoothingGroupsWhenMeshHasBlendShapes: Optional[bool] = (
    None
  )
  m_AddHumanoidExtraRootOnlyWhenUsingAvatar: Optional[bool] = None
  m_AdditionalBone: Optional[bool] = None
  m_AnimationDoRetargetingWarnings: Optional[bool] = None
  m_AnimationImportErrors: Optional[str] = None
  m_AnimationImportWarnings: Optional[str] = None
  m_AnimationRetargetingWarnings: Optional[str] = None
  m_AnimationType: Optional[int] = None
  m_AssetBundleName: Optional[str] = None
  m_AssetBundleVariant: Optional[str] = None
  m_AutoGenerateAvatarMappingIfUnspecified: Optional[bool] = None
  m_AutoMapExternalMaterials: Optional[bool] = None
  m_AvatarSetup: Optional[int] = None
  m_ContainsAnimation: Optional[bool] = None
  m_CopyAvatar: Optional[bool] = None
  m_ExternalObjects: Optional[List[Tuple[SourceAssetIdentifier, PPtr[Object]]]] = None
  m_ExtraExposedTransformPaths: Optional[List[str]] = None
  m_ExtraUserProperties: Optional[List[str]] = None
  m_FileIDToRecycleName: Optional[List[Tuple[int, str]]] = None
  m_FileIdsGeneration: Optional[int] = None
  m_FileScale: Optional[float] = None
  m_FileScaleFactor: Optional[float] = None
  m_FileScaleUnit: Optional[str] = None
  m_FirstImportVersion: Optional[int] = None
  m_GenerateAnimations: Optional[int] = None
  m_GenerateMaterials: Optional[int] = None
  m_HasEmbeddedTextures: Optional[bool] = None
  m_HasPreviousCalculatedGlobalScale: Optional[bool] = None
  m_HumanDescription: Optional[HumanDescription] = None
  m_HumanoidOversampling: Optional[int] = None
  m_ImportAnimatedCustomProperties: Optional[bool] = None
  m_ImportAnimation: Optional[bool] = None
  m_ImportBlendShapeDeformPercent: Optional[bool] = None
  m_ImportBlendShapes: Optional[bool] = None
  m_ImportCameras: Optional[bool] = None
  m_ImportConstraints: Optional[bool] = None
  m_ImportLights: Optional[bool] = None
  m_ImportMaterials: Optional[bool] = None
  m_ImportPhysicalCameras: Optional[bool] = None
  m_ImportVisibility: Optional[bool] = None
  m_ImportedTakeInfos: Optional[List[TakeInfo]] = None
  m_InternalIDToNameTable: Optional[List[Tuple[Tuple[int, int], str]]] = None
  m_IsReadable: Optional[bool] = None
  m_LODScreenPercentages: Optional[List[float]] = None
  m_LastHumanDescriptionAvatarSource: Optional[PPtr[Avatar]] = None
  m_LegacyGenerateAnimations: Optional[int] = None
  m_MaterialImportMode: Optional[int] = None
  m_MaterialLocation: Optional[int] = None
  m_MaterialName: Optional[int] = None
  m_MaterialSearch: Optional[int] = None
  m_Materials: Optional[List[SourceAssetIdentifier]] = None
  m_MeshSettings_generateSecondaryUV: Optional[bool] = None
  m_MeshSettings_normalImportMode: Optional[int] = None
  m_MeshSettings_secondaryUVAngleDistortion: Optional[float] = None
  m_MeshSettings_secondaryUVAreaDistortion: Optional[float] = None
  m_MeshSettings_secondaryUVHardAngle: Optional[float] = None
  m_MeshSettings_secondaryUVPackMargin: Optional[float] = None
  m_MeshSettings_swapUVChannels: Optional[bool] = None
  m_MeshSettings_tangentImportMode: Optional[int] = None
  m_MotionNodeName: Optional[str] = None
  m_NewHashIdentity: Optional[MdFour] = None
  m_NodeNameCollisionStrategy: Optional[int] = None
  m_OldHashIdentity: Optional[MdFour] = None
  m_OptimizeGameObjects: Optional[bool] = None
  m_PreserveHierarchy: Optional[bool] = None
  m_PreviousCalculatedGlobalScale: Optional[float] = None
  m_ReferencedClips: Optional[List[GUID]] = None
  m_RemapMaterialsIfMaterialImportModeIsNone: Optional[bool] = None
  m_RemoveConstantScaleCurves: Optional[bool] = None
  m_ResampleCurves: Optional[bool] = None
  m_ResampleRotations: Optional[bool] = None
  m_RigImportErrors: Optional[str] = None
  m_RigImportWarnings: Optional[str] = None
  m_SortHierarchyByName: Optional[bool] = None
  m_SplitAnimations: Optional[bool] = None
  m_StrictVertexDataChecks: Optional[bool] = None
  m_SupportsEmbeddedMaterials: Optional[bool] = None
  m_UseFileScale: Optional[bool] = None
  m_UseSRGBMaterialColor: Optional[bool] = None
  m_UsedFileIDs: Optional[List[int]] = None
  m_UserData: Optional[str] = None
  maxBonesPerVertex: Optional[int] = None
  meshOptimizationFlags: Optional[int] = None
  minBoneWeight: Optional[float] = None
  normalCalculationMode: Optional[int] = None
  normalImportMode: Optional[int] = None
  normalSmoothingSource: Optional[int] = None
  optimizeBones: Optional[bool] = None
  optimizeMesh: Optional[bool] = None
  optimizeMeshForGPU: Optional[bool] = None
  secondaryUVAngleDistortion: Optional[float] = None
  secondaryUVAreaDistortion: Optional[float] = None
  secondaryUVHardAngle: Optional[float] = None
  secondaryUVMarginMethod: Optional[int] = None
  secondaryUVMinLightmapResolution: Optional[float] = None
  secondaryUVMinObjectScale: Optional[float] = None
  secondaryUVPackMargin: Optional[float] = None
  skinWeightsMode: Optional[int] = None
  splitTangentsAcrossUV: Optional[bool] = None
  swapUVChannels: Optional[bool] = None
  tangentImportMode: Optional[int] = None
  weldVertices: Optional[bool] = None


@unitypy_define
class SketchUpImporter(ModelImporter):
  generateSecondaryUV: bool
  keepQuads: bool
  m_AddColliders: bool
  m_AdditionalBone: bool
  m_AnimationCompression: int
  m_AnimationDoRetargetingWarnings: bool
  m_AnimationImportErrors: str
  m_AnimationImportWarnings: str
  m_AnimationPositionError: float
  m_AnimationRetargetingWarnings: str
  m_AnimationRotationError: float
  m_AnimationScaleError: float
  m_AnimationType: int
  m_AnimationWrapMode: int
  m_AssetBundleName: str
  m_AssetBundleVariant: str
  m_AssetHash: Hash128
  m_BakeSimulation: bool
  m_ClipAnimations: List[ClipAnimationInfo]
  m_ExtraExposedTransformPaths: List[str]
  m_FileScale: float
  m_FileUnit: int
  m_GenerateBackFace: bool
  m_GlobalScale: float
  m_HasExtraRoot: bool
  m_HumanDescription: HumanDescription
  m_ImportAnimation: bool
  m_ImportBlendShapes: bool
  m_ImportedRoots: List[PPtr[GameObject]]
  m_ImportedTakeInfos: List[TakeInfo]
  m_IsReadable: bool
  m_LODScreenPercentages: List[float]
  m_LastHumanDescriptionAvatarSource: PPtr[Avatar]
  m_Latitude: float
  m_LegacyGenerateAnimations: int
  m_Longitude: float
  m_MaterialName: int
  m_MaterialSearch: int
  m_MergeCoplanarFaces: bool
  m_MeshCompression: int
  m_MotionNodeName: str
  m_Name: str
  m_NorthCorrection: float
  m_OptimizeGameObjects: bool
  m_ReferencedClips: List[GUID]
  m_SelectedNodes: List[int]
  m_SketchUpImportData: SketchUpImportData
  m_UseFileScale: bool
  m_UseFileUnits: bool
  m_UserData: str
  normalImportMode: int
  normalSmoothAngle: float
  secondaryUVAngleDistortion: float
  secondaryUVAreaDistortion: float
  secondaryUVHardAngle: float
  secondaryUVPackMargin: float
  swapUVChannels: bool
  tangentImportMode: int
  weldVertices: bool
  bakeAxisConversion: Optional[bool] = None
  blendShapeNormalImportMode: Optional[int] = None
  indexFormat: Optional[int] = None
  legacyComputeAllNormalsFromSmoothingGroupsWhenMeshHasBlendShapes: Optional[bool] = (
    None
  )
  m_AddHumanoidExtraRootOnlyWhenUsingAvatar: Optional[bool] = None
  m_AutoGenerateAvatarMappingIfUnspecified: Optional[bool] = None
  m_AutoMapExternalMaterials: Optional[bool] = None
  m_AvatarSetup: Optional[int] = None
  m_ContainsAnimation: Optional[bool] = None
  m_CopyAvatar: Optional[bool] = None
  m_ExternalObjects: Optional[List[Tuple[SourceAssetIdentifier, PPtr[Object]]]] = None
  m_ExtraUserProperties: Optional[List[str]] = None
  m_FileIDToRecycleName: Optional[List[Tuple[int, str]]] = None
  m_FileIdsGeneration: Optional[int] = None
  m_FileScaleFactor: Optional[float] = None
  m_FileScaleUnit: Optional[str] = None
  m_HasEmbeddedTextures: Optional[bool] = None
  m_HasPreviousCalculatedGlobalScale: Optional[bool] = None
  m_HumanoidOversampling: Optional[int] = None
  m_ImportAnimatedCustomProperties: Optional[bool] = None
  m_ImportBlendShapeDeformPercent: Optional[bool] = None
  m_ImportCameras: Optional[bool] = None
  m_ImportConstraints: Optional[bool] = None
  m_ImportLights: Optional[bool] = None
  m_ImportMaterials: Optional[bool] = None
  m_ImportPhysicalCameras: Optional[bool] = None
  m_ImportVisibility: Optional[bool] = None
  m_InternalIDToNameTable: Optional[List[Tuple[Tuple[int, int], str]]] = None
  m_MaterialImportMode: Optional[int] = None
  m_MaterialLocation: Optional[int] = None
  m_Materials: Optional[List[SourceAssetIdentifier]] = None
  m_NodeNameCollisionStrategy: Optional[int] = None
  m_PreserveHierarchy: Optional[bool] = None
  m_PreviousCalculatedGlobalScale: Optional[float] = None
  m_RemapMaterialsIfMaterialImportModeIsNone: Optional[bool] = None
  m_RemoveConstantScaleCurves: Optional[bool] = None
  m_ResampleCurves: Optional[bool] = None
  m_ResampleRotations: Optional[bool] = None
  m_RigImportErrors: Optional[str] = None
  m_RigImportWarnings: Optional[str] = None
  m_SortHierarchyByName: Optional[bool] = None
  m_StrictVertexDataChecks: Optional[bool] = None
  m_SupportsEmbeddedMaterials: Optional[bool] = None
  m_UseSRGBMaterialColor: Optional[bool] = None
  m_UsedFileIDs: Optional[List[int]] = None
  maxBonesPerVertex: Optional[int] = None
  meshOptimizationFlags: Optional[int] = None
  minBoneWeight: Optional[float] = None
  normalCalculationMode: Optional[int] = None
  normalSmoothingSource: Optional[int] = None
  optimizeBones: Optional[bool] = None
  optimizeMeshForGPU: Optional[bool] = None
  secondaryUVMarginMethod: Optional[int] = None
  secondaryUVMinLightmapResolution: Optional[float] = None
  secondaryUVMinObjectScale: Optional[float] = None
  skinWeightsMode: Optional[int] = None
  splitTangentsAcrossUV: Optional[bool] = None


@unitypy_define
class MonoImporter(AssetImporter):
  executionOrder: int
  icon: PPtr[Texture2D]
  m_DefaultReferences: List[Tuple[str, PPtr[Object]]]
  m_Name: str
  m_AssetBundleName: Optional[str] = None
  m_AssetBundleVariant: Optional[str] = None
  m_ExternalObjects: Optional[List[Tuple[SourceAssetIdentifier, PPtr[Object]]]] = None
  m_FileIDToRecycleName: Optional[List[Tuple[int, str]]] = None
  m_NewHashIdentity: Optional[MdFour] = None
  m_OldHashIdentity: Optional[MdFour] = None
  m_UsedFileIDs: Optional[List[int]] = None
  m_UserData: Optional[str] = None


@unitypy_define
class MovieImporter(AssetImporter):
  m_Name: str
  m_Quality: float
  m_AssetBundleName: Optional[str] = None
  m_AssetBundleVariant: Optional[str] = None
  m_ExternalObjects: Optional[List[Tuple[SourceAssetIdentifier, PPtr[Object]]]] = None
  m_FileIDToRecycleName: Optional[List[Tuple[int, str]]] = None
  m_LinearTexture: Optional[bool] = None
  m_NewHashIdentity: Optional[MdFour] = None
  m_OldHashIdentity: Optional[MdFour] = None
  m_UsedFileIDs: Optional[List[int]] = None
  m_UserData: Optional[str] = None


@unitypy_define
class MultiArtifactTestImporter(AssetImporter):
  m_AssetBundleName: str
  m_AssetBundleVariant: str
  m_ExternalObjects: List[Tuple[SourceAssetIdentifier, PPtr[Object]]]
  m_Name: str
  m_UsedFileIDs: List[int]
  m_UserData: str


@unitypy_define
class NativeFormatImporter(AssetImporter):
  m_Name: str
  m_AssetBundleName: Optional[str] = None
  m_AssetBundleVariant: Optional[str] = None
  m_ExternalObjects: Optional[List[Tuple[SourceAssetIdentifier, PPtr[Object]]]] = None
  m_FileIDToRecycleName: Optional[List[Tuple[int, str]]] = None
  m_MainObjectFileID: Optional[int] = None
  m_NewHashIdentity: Optional[MdFour] = None
  m_OldHashIdentity: Optional[MdFour] = None
  m_UsedFileIDs: Optional[List[int]] = None
  m_UserData: Optional[str] = None


@unitypy_define
class PVRImporter(AssetImporter):
  m_Name: str
  m_AssetBundleName: Optional[str] = None
  m_AssetBundleVariant: Optional[str] = None
  m_FileIDToRecycleName: Optional[List[Tuple[int, str]]] = None
  m_NewHashIdentity: Optional[MdFour] = None
  m_OldHashIdentity: Optional[MdFour] = None
  m_UserData: Optional[str] = None


@unitypy_define
class PackageManifestImporter(AssetImporter):
  m_AssetBundleName: str
  m_AssetBundleVariant: str
  m_ExternalObjects: List[Tuple[SourceAssetIdentifier, PPtr[Object]]]
  m_Name: str
  m_UsedFileIDs: List[int]
  m_UserData: str


@unitypy_define
class PluginImporter(AssetImporter):
  m_AssetBundleName: str
  m_AssetBundleVariant: str
  m_ExecutionOrder: List[Tuple[str, int]]
  m_IconMap: List[Tuple[str, PPtr[Texture2D]]]
  m_IsPreloaded: bool
  m_Name: str
  m_Output: PluginImportOutput
  m_PlatformData: Union[
    List[Tuple[str, PlatformSettingsData]],
    List[Tuple[Tuple[str, str], PlatformSettingsData]],
  ]
  m_UserData: str
  m_DefineConstraints: Optional[List[str]] = None
  m_ExternalObjects: Optional[List[Tuple[SourceAssetIdentifier, PPtr[Object]]]] = None
  m_IsExplicitlyReferenced: Optional[bool] = None
  m_IsOverridable: Optional[bool] = None
  m_UsedFileIDs: Optional[List[int]] = None
  m_ValidateReferences: Optional[bool] = None


@unitypy_define
class PrefabImporter(AssetImporter):
  m_AddedObjectFileIDs: List[int]
  m_AssetBundleName: str
  m_AssetBundleVariant: str
  m_ExternalObjects: List[Tuple[SourceAssetIdentifier, PPtr[Object]]]
  m_IsPrefabVariant: bool
  m_Name: str
  m_UserData: str
  m_UnableToImportOnPreviousDomainReload: Optional[bool] = None
  m_UsedFileIDs: Optional[List[int]] = None
  m_VariantParentGUID: Optional[GUID] = None


@unitypy_define
class PreviewImporter(AssetImporter):
  m_AssetBundleName: str
  m_AssetBundleVariant: str
  m_ExternalObjects: List[Tuple[SourceAssetIdentifier, PPtr[Object]]]
  m_Name: str
  m_UsedFileIDs: List[int]
  m_UserData: str


@unitypy_define
class RayTracingShaderImporter(AssetImporter):
  m_AssetBundleName: str
  m_AssetBundleVariant: str
  m_ExternalObjects: List[Tuple[SourceAssetIdentifier, PPtr[Object]]]
  m_Name: str
  m_UsedFileIDs: List[int]
  m_UserData: str
  m_CurrentAPIMask: Optional[int] = None


@unitypy_define
class ReferencesArtifactGenerator(AssetImporter):
  m_AssetBundleName: str
  m_AssetBundleVariant: str
  m_ExternalObjects: List[Tuple[SourceAssetIdentifier, PPtr[Object]]]
  m_Name: str
  m_UsedFileIDs: List[int]
  m_UserData: str


@unitypy_define
class RoslynAdditionalFileImporter(AssetImporter):
  m_AssetBundleName: str
  m_AssetBundleVariant: str
  m_ExternalObjects: List[Tuple[SourceAssetIdentifier, PPtr[Object]]]
  m_Name: str
  m_UsedFileIDs: List[int]
  m_UserData: str


@unitypy_define
class RoslynAnalyzerConfigImporter(AssetImporter):
  m_AssetBundleName: str
  m_AssetBundleVariant: str
  m_ExternalObjects: List[Tuple[SourceAssetIdentifier, PPtr[Object]]]
  m_Name: str
  m_UsedFileIDs: List[int]
  m_UserData: str


@unitypy_define
class RuleSetFileImporter(AssetImporter):
  m_AssetBundleName: str
  m_AssetBundleVariant: str
  m_ExternalObjects: List[Tuple[SourceAssetIdentifier, PPtr[Object]]]
  m_Name: str
  m_UsedFileIDs: List[int]
  m_UserData: str


@unitypy_define
class ScriptedImporter(AssetImporter):
  m_AssetBundleName: str
  m_AssetBundleVariant: str
  m_Name: str
  m_Script: PPtr[MonoScript]
  m_UserData: str
  m_ExternalObjects: Optional[List[Tuple[SourceAssetIdentifier, PPtr[Object]]]] = None
  m_FileIDToRecycleName: Optional[List[Tuple[int, str]]] = None
  m_InternalIDToNameTable: Optional[List[Tuple[Tuple[int, int], str]]] = None
  m_UsedFileIDs: Optional[List[int]] = None


@unitypy_define
class ShaderImporter(AssetImporter):
  m_Name: str
  m_AssetBundleName: Optional[str] = None
  m_AssetBundleVariant: Optional[str] = None
  m_DefaultTextures: Optional[List[Tuple[str, PPtr[Texture]]]] = None
  m_ExternalObjects: Optional[List[Tuple[SourceAssetIdentifier, PPtr[Object]]]] = None
  m_FileIDToRecycleName: Optional[List[Tuple[int, str]]] = None
  m_NewHashIdentity: Optional[MdFour] = None
  m_NonModifiableTextures: Optional[List[Tuple[str, PPtr[Texture]]]] = None
  m_OldHashIdentity: Optional[MdFour] = None
  m_PreprocessorOverride: Optional[int] = None
  m_UsedFileIDs: Optional[List[int]] = None
  m_UserData: Optional[str] = None


@unitypy_define
class ShaderIncludeImporter(AssetImporter):
  m_AssetBundleName: str
  m_AssetBundleVariant: str
  m_ExternalObjects: List[Tuple[SourceAssetIdentifier, PPtr[Object]]]
  m_Name: str
  m_UsedFileIDs: List[int]
  m_UserData: str


@unitypy_define
class SpeedTreeImporter(AssetImporter):
  m_AlphaTestRef: float
  m_AssetBundleName: str
  m_AssetBundleVariant: str
  m_BestWindQuality: int
  m_BillboardTransitionCrossFadeWidth: float
  m_EnableSmoothLODTransition: bool
  m_FadeOutWidth: float
  m_HasBillboard: bool
  m_HueVariation: ColorRGBA
  m_LODSettings: List[PerLODSettings]
  m_MainColor: ColorRGBA
  m_Name: str
  m_ScaleFactor: float
  m_UserData: str
  m_AnimateCrossFading: Optional[bool] = None
  m_EnableBumpMapping: Optional[bool] = None
  m_EnableHueVariation: Optional[bool] = None
  m_EnableLightProbes: Optional[bool] = None
  m_EnableShadowCasting: Optional[bool] = None
  m_EnableShadowReceiving: Optional[bool] = None
  m_EnableSubsurfaceScattering: Optional[bool] = None
  m_ExternalObjects: Optional[List[Tuple[SourceAssetIdentifier, PPtr[Object]]]] = None
  m_FileIDType: Optional[int] = None
  m_GenerateColliders: Optional[bool] = None
  m_GenerateRigidbody: Optional[bool] = None
  m_MaterialLocation: Optional[int] = None
  m_MaterialVersion: Optional[int] = None
  m_Materials: Optional[List[SourceAssetIdentifier]] = None
  m_MotionVectorModeEnumValue: Optional[int] = None
  m_ReflectionProbeEnumValue: Optional[int] = None
  m_SelectedWindQuality: Optional[int] = None
  m_Shininess: Optional[float] = None
  m_SpecColor: Optional[ColorRGBA] = None
  m_SupportsEmbeddedMaterials: Optional[bool] = None
  m_UnitConversionEnumValue: Optional[int] = None
  m_UsedFileIDs: Optional[List[int]] = None


@unitypy_define
class SpriteAtlasImporter(AssetImporter):
  m_AssetBundleName: str
  m_AssetBundleVariant: str
  m_ExternalObjects: List[Tuple[SourceAssetIdentifier, PPtr[Object]]]
  m_Name: str
  m_UsedFileIDs: List[int]
  m_UserData: str
  m_BindAsDefault: Optional[bool] = None
  m_PackingSettings: Optional[PackingSettings] = None
  m_PlatformSettings: Optional[List[TextureImporterPlatformSettings]] = None
  m_SecondaryTextureSettings: Optional[List[Tuple[str, SecondaryTextureSettings]]] = (
    None
  )
  m_TextureSettings: Optional[TextureSettings] = None
  m_VariantMultiplier: Optional[float] = None


@unitypy_define
class StyleSheetImporter(AssetImporter):
  m_AssetBundleName: str
  m_AssetBundleVariant: str
  m_Name: str
  m_UserData: str


@unitypy_define
class SubstanceImporter(AssetImporter):
  m_Name: str
  m_AssetBundleName: Optional[str] = None
  m_AssetBundleVariant: Optional[str] = None
  m_DeletedPrototypes: Optional[List[str]] = None
  m_ExternalObjects: Optional[List[Tuple[SourceAssetIdentifier, PPtr[Object]]]] = None
  m_FileIDToRecycleName: Optional[List[Tuple[int, str]]] = None
  m_IsFirstImport: Optional[int] = None
  m_MaterialImportOutputs: Optional[List[MaterialImportOutput]] = None
  m_MaterialInstances: Optional[List[MaterialInstanceSettings]] = None
  m_NewHashIdentity: Optional[MdFour] = None
  m_OldHashIdentity: Optional[MdFour] = None
  m_UsedFileIDs: Optional[List[int]] = None
  m_UserData: Optional[str] = None


@unitypy_define
class TextScriptImporter(AssetImporter):
  m_Name: str
  m_AssetBundleName: Optional[str] = None
  m_AssetBundleVariant: Optional[str] = None
  m_ExternalObjects: Optional[List[Tuple[SourceAssetIdentifier, PPtr[Object]]]] = None
  m_FileIDToRecycleName: Optional[List[Tuple[int, str]]] = None
  m_NewHashIdentity: Optional[MdFour] = None
  m_OldHashIdentity: Optional[MdFour] = None
  m_UsedFileIDs: Optional[List[int]] = None
  m_UserData: Optional[str] = None


@unitypy_define
class TextureImporter(AssetImporter):
  m_BorderMipMap: int
  m_ConvertToNormalMap: int
  m_EnableMipMap: int
  m_ExternalNormalMap: int
  m_FadeOut: int
  m_GenerateCubemap: int
  m_GrayScaleToAlpha: int
  m_HeightScale: float
  m_IsReadable: int
  m_Lightmap: int
  m_MaxTextureSize: int
  m_MipMapFadeDistanceEnd: int
  m_MipMapFadeDistanceStart: int
  m_MipMapMode: int
  m_NPOTScale: int
  m_Name: str
  m_NormalMapFilter: int
  m_TextureFormat: int
  m_TextureSettings: GLTextureSettings
  m_TextureType: int
  correctGamma: Optional[int] = None
  m_Alignment: Optional[int] = None
  m_AllowsAlphaSplitting: Optional[int] = None
  m_AlphaIsTransparency: Optional[int] = None
  m_AlphaTestReferenceValue: Optional[float] = None
  m_AlphaUsage: Optional[int] = None
  m_ApplyGammaDecoding: Optional[int] = None
  m_AssetBundleName: Optional[str] = None
  m_AssetBundleVariant: Optional[str] = None
  m_BuildTargetSettings: Optional[List[BuildTargetSettings]] = None
  m_CompressionQuality: Optional[int] = None
  m_CompressionQualitySet: Optional[int] = None
  m_CookieLightType: Optional[int] = None
  m_CorrectGamma: Optional[int] = None
  m_CubemapConvolution: Optional[int] = None
  m_CubemapConvolutionExponent: Optional[float] = None
  m_CubemapConvolutionSteps: Optional[int] = None
  m_ExternalObjects: Optional[List[Tuple[SourceAssetIdentifier, PPtr[Object]]]] = None
  m_FileIDToRecycleName: Optional[List[Tuple[int, str]]] = None
  m_FlipGreenChannel: Optional[int] = None
  m_FlipbookColumns: Optional[int] = None
  m_FlipbookRows: Optional[int] = None
  m_IgnoreMasterTextureLimit: Optional[int] = None
  m_IgnoreMipmapLimit: Optional[int] = None
  m_IgnorePngGamma: Optional[Union[bool, int]] = None
  m_InternalIDToNameTable: Optional[List[Tuple[Tuple[int, int], str]]] = None
  m_LinearTexture: Optional[int] = None
  m_MaxTextureSizeSet: Optional[int] = None
  m_MipMapsPreserveCoverage: Optional[int] = None
  m_MipmapLimitGroupName: Optional[str] = None
  m_NewHashIdentity: Optional[MdFour] = None
  m_OldHashIdentity: Optional[MdFour] = None
  m_Output: Optional[TextureImportOutput] = None
  m_PSDRemoveMatte: Optional[bool] = None
  m_PSDShowRemoveMatteOption: Optional[bool] = None
  m_PlatformSettings: Optional[
    Union[List[TextureImporterPlatformSettings], List[PlatformSettings]]
  ] = None
  m_PushPullDilation: Optional[int] = None
  m_RGBM: Optional[int] = None
  m_RecommendedTextureFormat: Optional[int] = None
  m_SeamlessCubemap: Optional[int] = None
  m_SingleChannelComponent: Optional[int] = None
  m_SourceTextureInformation: Optional[SourceTextureInformation] = None
  m_SpriteBorder: Optional[Vector4f] = None
  m_SpriteExtrude: Optional[int] = None
  m_SpriteGenerateFallbackPhysicsShape: Optional[int] = None
  m_SpriteMeshType: Optional[int] = None
  m_SpriteMode: Optional[int] = None
  m_SpritePackingTag: Optional[str] = None
  m_SpritePivot: Optional[Vector2f] = None
  m_SpritePixelsToUnits: Optional[float] = None
  m_SpriteSheet: Optional[SpriteSheetMetaData] = None
  m_SpriteTessellationDetail: Optional[float] = None
  m_StreamingMipmaps: Optional[int] = None
  m_StreamingMipmapsPriority: Optional[int] = None
  m_Swizzle: Optional[int] = None
  m_TextureFormatSet: Optional[int] = None
  m_TextureShape: Optional[int] = None
  m_UsedFileIDs: Optional[List[int]] = None
  m_UserData: Optional[str] = None
  m_VTOnly: Optional[int] = None
  m_sRGBTexture: Optional[int] = None


@unitypy_define
class TrueTypeFontImporter(AssetImporter):
  m_FontNames: List[str]
  m_FontSize: int
  m_ForceTextureCase: int
  m_IncludeFontData: bool
  m_Name: str
  m_AscentCalculationMode: Optional[int] = None
  m_AssetBundleName: Optional[str] = None
  m_AssetBundleVariant: Optional[str] = None
  m_CharacterPadding: Optional[int] = None
  m_CharacterSpacing: Optional[int] = None
  m_CustomCharacters: Optional[str] = None
  m_ExternalObjects: Optional[List[Tuple[SourceAssetIdentifier, PPtr[Object]]]] = None
  m_FallbackFontReferences: Optional[List[PPtr[Font]]] = None
  m_FileIDToRecycleName: Optional[List[Tuple[int, str]]] = None
  m_FontColor: Optional[ColorRGBA] = None
  m_FontName: Optional[str] = None
  m_FontRenderingMode: Optional[int] = None
  m_NewHashIdentity: Optional[MdFour] = None
  m_OldHashIdentity: Optional[MdFour] = None
  m_Output: Optional[Output] = None
  m_RenderMode: Optional[int] = None
  m_ShouldRoundAdvanceValue: Optional[bool] = None
  m_Style: Optional[int] = None
  m_Use2xBehaviour: Optional[bool] = None
  m_UseLegacyBoundsCalculation: Optional[bool] = None
  m_UsedFileIDs: Optional[List[int]] = None
  m_UserData: Optional[str] = None


@unitypy_define
class VideoClipImporter(AssetImporter):
  m_AssetBundleName: str
  m_AssetBundleVariant: str
  m_ColorSpace: int
  m_Deinterlace: int
  m_EncodeAlpha: bool
  m_EndFrame: int
  m_FlipHorizontal: bool
  m_FlipVertical: bool
  m_FrameRange: int
  m_Name: str
  m_Output: VideoClipImporterOutput
  m_StartFrame: int
  m_TargetSettings: Union[
    List[Tuple[int, VideoClipImporterTargetSettings]],
    List[Tuple[str, VideoClipImporterTargetSettings]],
  ]
  m_UserData: str
  m_AudioImportMode: Optional[int] = None
  m_ExternalObjects: Optional[List[Tuple[SourceAssetIdentifier, PPtr[Object]]]] = None
  m_FrameCount: Optional[int] = None
  m_FrameRate: Optional[float] = None
  m_ImportAudio: Optional[bool] = None
  m_IsColorLinear: Optional[bool] = None
  m_OriginalHeight: Optional[int] = None
  m_OriginalWidth: Optional[int] = None
  m_PixelAspectRatioDenominator: Optional[int] = None
  m_PixelAspectRatioNumerator: Optional[int] = None
  m_Quality: Optional[float] = None
  m_SourceAudioChannelCount: Optional[List[int]] = None
  m_SourceAudioSampleRate: Optional[List[int]] = None
  m_SourceFileSize: Optional[int] = None
  m_SourceHasAlpha: Optional[bool] = None
  m_UseLegacyImporter: Optional[bool] = None
  m_UsedFileIDs: Optional[List[int]] = None


@unitypy_define
class VisualEffectImporter(AssetImporter):
  m_AssetBundleName: str
  m_AssetBundleVariant: str
  m_ExternalObjects: List[Tuple[SourceAssetIdentifier, PPtr[Object]]]
  m_Name: str
  m_UserData: str
  m_Template: Optional[VFXTemplate] = None
  m_UsedFileIDs: Optional[List[int]] = None


@unitypy_define
class AudioContainerElement(NamedObject):
  m_AudioClip: PPtr[AudioClip]
  m_Enabled: bool
  m_Name: str
  m_Volume: float


@unitypy_define
class AudioMixer(NamedObject):
  m_EnableSuspend: bool
  m_MasterGroup: PPtr[AudioMixerGroup]
  m_MixerConstant: AudioMixerConstant
  m_Name: str
  m_OutputGroup: PPtr[AudioMixerGroup]
  m_Snapshots: List[PPtr[AudioMixerSnapshot]]
  m_StartSnapshot: PPtr[AudioMixerSnapshot]
  m_SuspendThreshold: float
  m_UpdateMode: Optional[int] = None


@unitypy_define
class AudioMixerController(AudioMixer):
  m_EnableSuspend: bool
  m_MasterGroup: PPtr[AudioMixerGroup]
  m_MixerConstant: AudioMixerConstant
  m_Name: str
  m_OutputGroup: PPtr[AudioMixerGroup]
  m_Snapshots: List[PPtr[AudioMixerSnapshot]]
  m_StartSnapshot: PPtr[AudioMixerSnapshot]
  m_SuspendThreshold: float
  m_UpdateMode: Optional[int] = None


@unitypy_define
class AudioMixerEffectController(NamedObject):
  m_Bypass: bool
  m_EffectID: GUID
  m_EffectName: str
  m_EnableWetMix: bool
  m_MixLevel: GUID
  m_Name: str
  m_Parameters: List[Parameter]
  m_SendTarget: PPtr[AudioMixerEffectController]


@unitypy_define
class AudioMixerGroup(NamedObject):
  m_AudioMixer: PPtr[AudioMixer]
  m_Children: List[PPtr[AudioMixerGroup]]
  m_GroupID: GUID
  m_Name: str


@unitypy_define
class AudioMixerGroupController(AudioMixerGroup):
  m_AudioMixer: PPtr[AudioMixer]
  m_Children: List[PPtr[AudioMixerGroup]]
  m_GroupID: GUID
  m_Name: str


@unitypy_define
class AudioMixerSnapshot(NamedObject):
  m_AudioMixer: PPtr[AudioMixer]
  m_Name: str
  m_SnapshotID: GUID


@unitypy_define
class AudioMixerSnapshotController(AudioMixerSnapshot):
  m_AudioMixer: PPtr[AudioMixer]
  m_Name: str
  m_SnapshotID: GUID


@unitypy_define
class AudioResource(NamedObject):
  m_Name: str


@unitypy_define
class AudioRandomContainer(AudioResource):
  m_AutomaticTriggerMode: int
  m_AutomaticTriggerTime: float
  m_AutomaticTriggerTimeRandomizationEnabled: bool
  m_AutomaticTriggerTimeRandomizationRange: Vector2f
  m_AvoidRepeatingLast: int
  m_Elements: List[PPtr[AudioContainerElement]]
  m_LoopCount: int
  m_LoopCountRandomizationEnabled: bool
  m_LoopCountRandomizationRange: Vector2f
  m_LoopMode: int
  m_Name: str
  m_Pitch: float
  m_PitchRandomizationEnabled: bool
  m_PitchRandomizationRange: Vector2f
  m_PlaybackMode: int
  m_TriggerMode: int
  m_Volume: float
  m_VolumeRandomizationEnabled: bool
  m_VolumeRandomizationRange: Vector2f


@unitypy_define
class SampleClip(AudioResource):
  m_Name: str


@unitypy_define
class AudioClip(SampleClip):
  m_Name: str
  m_3D: Optional[bool] = None
  m_Ambisonic: Optional[bool] = None
  m_AudioData: Optional[List[int]] = None
  m_BitsPerSample: Optional[int] = None
  m_Channels: Optional[int] = None
  m_CompressionFormat: Optional[int] = None
  m_Format: Optional[int] = None
  m_Frequency: Optional[int] = None
  m_IsTrackerFormat: Optional[bool] = None
  m_Legacy3D: Optional[bool] = None
  m_Length: Optional[float] = None
  m_LoadInBackground: Optional[bool] = None
  m_LoadType: Optional[int] = None
  m_PreloadAudioData: Optional[bool] = None
  m_Resource: Optional[StreamedResource] = None
  m_Stream: Optional[int] = None
  m_SubsoundIndex: Optional[int] = None
  m_Type: Optional[int] = None
  m_UseHardware: Optional[bool] = None


@unitypy_define
class Avatar(NamedObject):
  m_Avatar: AvatarConstant
  m_AvatarSize: int
  m_Name: str
  m_TOS: List[Tuple[int, str]]
  m_HumanDescription: Optional[HumanDescription] = None


@unitypy_define
class AvatarMask(NamedObject):
  m_Elements: List[TransformMaskElement]
  m_Mask: List[int]
  m_Name: str


@unitypy_define
class AvatarSkeletonMask(NamedObject):
  elements: List[AvatarSkeletonMaskElement]
  m_Name: str


@unitypy_define
class BaseAnimationTrack(NamedObject, ABC):
  pass


@unitypy_define
class NewAnimationTrack(BaseAnimationTrack):
  m_ClassID: int
  m_Curves: List[Channel]
  m_Name: str


@unitypy_define
class BillboardAsset(NamedObject):
  bottom: float
  height: float
  imageTexCoords: List[Vector4f]
  indices: List[int]
  m_Name: str
  material: PPtr[Material]
  vertices: List[Vector2f]
  width: float
  rotated: Optional[List[int]] = None


@unitypy_define
class BuildReport(NamedObject):
  m_Appendices: List[PPtr[Object]]
  m_BuildSteps: List[BuildStepInfo]
  m_Files: List[BuildReportFile]
  m_Name: str
  m_Summary: BuildSummary


@unitypy_define
class CachedSpriteAtlas(NamedObject):
  frames: List[Tuple[Tuple[GUID, int], SpriteRenderData]]
  textures: List[PPtr[Texture2D]]
  alphaTextures: Optional[List[PPtr[Texture2D]]] = None


@unitypy_define
class CachedSpriteAtlasRuntimeData(NamedObject):
  alphaTextures: List[PPtr[Texture2D]]
  frames: List[Tuple[Tuple[GUID, int], SpriteAtlasData]]
  textures: List[PPtr[Texture2D]]
  currentPackingHash: Optional[Hash128] = None


@unitypy_define
class ComputeShader(NamedObject):
  m_Name: str
  constantBuffers: Optional[List[ComputeShaderCB]] = None
  kernels: Optional[List[ComputeShaderKernel]] = None
  variants: Optional[
    Union[List[ComputeShaderVariant], List[ComputeShaderPlatformVariant]]
  ] = None


@unitypy_define
class DefaultAsset(NamedObject):
  m_Name: str
  m_IsWarning: Optional[bool] = None
  m_Message: Optional[str] = None


@unitypy_define
class BrokenPrefabAsset(DefaultAsset):
  m_BrokenParentPrefab: PPtr[BrokenPrefabAsset]
  m_IsPrefabFileValid: bool
  m_IsVariant: bool
  m_IsWarning: bool
  m_Message: str
  m_Name: str


@unitypy_define
class SceneAsset(DefaultAsset):
  m_Name: str
  m_IsWarning: Optional[bool] = None
  m_Message: Optional[str] = None


@unitypy_define
class EditorProjectAccess(NamedObject):
  m_Name: str


@unitypy_define
class Flare(NamedObject):
  m_Elements: List[FlareElement]
  m_FlareTexture: PPtr[Texture]
  m_Name: str
  m_TextureLayout: int
  m_UseFog: bool


@unitypy_define
class Font(NamedObject):
  m_Ascent: float
  m_AsciiStartOffset: int
  m_CharacterRects: List[CharacterInfo]
  m_ConvertCase: int
  m_DefaultMaterial: PPtr[Material]
  m_DefaultStyle: int
  m_FontData: List[str]
  m_FontNames: List[str]
  m_FontSize: float
  m_KerningValues: List[Tuple[Tuple[int, int], float]]
  m_LineSpacing: float
  m_Name: str
  m_Texture: PPtr[Texture]
  m_CharacterPadding: Optional[int] = None
  m_CharacterSpacing: Optional[int] = None
  m_Descent: Optional[float] = None
  m_FallbackFonts: Optional[List[PPtr[Font]]] = None
  m_FontCountX: Optional[int] = None
  m_FontCountY: Optional[int] = None
  m_FontRenderingMode: Optional[int] = None
  m_GridFont: Optional[bool] = None
  m_Kerning: Optional[float] = None
  m_PerCharacterKerning: Optional[List[Tuple[int, float]]] = None
  m_PixelScale: Optional[float] = None
  m_ShouldRoundAdvanceValue: Optional[bool] = None
  m_Tracking: Optional[float] = None
  m_UseLegacyBoundsCalculation: Optional[bool] = None


@unitypy_define
class GameObjectRecorder(NamedObject):
  m_Name: str


@unitypy_define
class GraphicsStateCollection(NamedObject):
  m_DeviceRenderer: int
  m_Name: str
  m_QualityLevelName: str
  m_RenderPassInfoMap: List[Tuple[int, RenderPassInfo]]
  m_RenderStateMap: List[Tuple[int, RenderStateInfo]]
  m_RuntimePlatform: int
  m_VariantInfoMap: List[Tuple[Hash128, VariantInfo]]
  m_Version: int
  m_VertexLayoutInfoMap: List[Tuple[int, VertexLayoutInfo]]


@unitypy_define
class HumanTemplate(NamedObject):
  m_BoneTemplate: List[Tuple[str, str]]
  m_Name: str


@unitypy_define
class ImportLog(NamedObject):
  m_Logs: List[ImportLog_ImportLogEntry]
  m_Name: str


@unitypy_define
class LightProbes(NamedObject):
  m_Name: str
  bakedCoefficients: Optional[List[LightmapData]] = None
  bakedPositions: Optional[List[Vector3f]] = None
  hullRays: Optional[List[Vector3f]] = None
  m_BakedCoefficients: Optional[List[SphericalHarmonicsL2]] = None
  m_BakedLightOcclusion: Optional[List[LightProbeOcclusion]] = None
  m_Data: Optional[LightProbeData] = None
  m_HasBeenEdited: Optional[bool] = None
  tetrahedra: Optional[List[Tetrahedron]] = None


@unitypy_define
class LightingDataAsset(NamedObject):
  m_BakedAmbientProbeInLinear: SphericalHarmonicsL2
  m_BakedReflectionProbeCubemaps: List[PPtr[Texture]]
  m_BakedReflectionProbes: List[SceneObjectIdentifier]
  m_EnlightenData: List[int]
  m_EnlightenSceneMapping: EnlightenSceneMapping
  m_EnlightenSceneMappingRendererIDs: List[SceneObjectIdentifier]
  m_LightProbes: PPtr[LightProbes]
  m_LightmappedRendererData: List[RendererData]
  m_LightmappedRendererDataIDs: List[SceneObjectIdentifier]
  m_Lightmaps: List[LightmapData]
  m_Lights: List[SceneObjectIdentifier]
  m_Name: str
  m_AOTextures: Optional[List[PPtr[Texture2D]]] = None
  m_BakedLightIndices: Optional[List[int]] = None
  m_BakedReflectionProbeCubemapCacheFiles: Optional[List[str]] = None
  m_EnlightenDataVersion: Optional[int] = None
  m_LightBakingOutputs: Optional[List[LightBakingOutput]] = None
  m_LightmapsCacheFiles: Optional[List[str]] = None
  m_LightmapsMode: Optional[int] = None
  m_Scene: Optional[PPtr[SceneAsset]] = None
  m_SceneGUID: Optional[GUID] = None


@unitypy_define
class LightingDataAssetParent(NamedObject):
  m_Name: str


@unitypy_define
class LightingSettings(NamedObject):
  m_AlbedoBoost: float
  m_BounceScale: float
  m_EnableBakedLightmaps: bool
  m_EnableRealtimeLightmaps: bool
  m_Name: str
  m_RealtimeEnvironmentLighting: bool
  m_UsingShadowmask: bool
  m_AO: Optional[bool] = None
  m_AOMaxDistance: Optional[float] = None
  m_BakeBackend: Optional[int] = None
  m_BakeResolution: Optional[float] = None
  m_CompAOExponent: Optional[float] = None
  m_CompAOExponentDirect: Optional[float] = None
  m_ExportTrainingData: Optional[bool] = None
  m_ExtractAO: Optional[bool] = None
  m_FilterMode: Optional[int] = None
  m_FinalGather: Optional[bool] = None
  m_FinalGatherFiltering: Optional[bool] = None
  m_FinalGatherRayCount: Optional[int] = None
  m_ForceUpdates: Optional[bool] = None
  m_ForceWhiteAlbedo: Optional[bool] = None
  m_GIWorkflowMode: Optional[int] = None
  m_IndirectOutputScale: Optional[float] = None
  m_LightmapMaxSize: Optional[int] = None
  m_LightmapParameters: Optional[PPtr[LightmapParameters]] = None
  m_LightmapsBakeMode: Optional[int] = None
  m_MixedBakeMode: Optional[int] = None
  m_PVRBounces: Optional[int] = None
  m_PVRCulling: Optional[bool] = None
  m_PVRDenoiserTypeAO: Optional[int] = None
  m_PVRDenoiserTypeDirect: Optional[int] = None
  m_PVRDenoiserTypeIndirect: Optional[int] = None
  m_PVRDirectSampleCount: Optional[int] = None
  m_PVREnvironmentMIS: Optional[int] = None
  m_PVREnvironmentReferencePointCount: Optional[int] = None
  m_PVREnvironmentSampleCount: Optional[int] = None
  m_PVRFilterTypeAO: Optional[int] = None
  m_PVRFilterTypeDirect: Optional[int] = None
  m_PVRFilterTypeIndirect: Optional[int] = None
  m_PVRFilteringAtrousPositionSigmaAO: Optional[float] = None
  m_PVRFilteringAtrousPositionSigmaDirect: Optional[float] = None
  m_PVRFilteringAtrousPositionSigmaIndirect: Optional[float] = None
  m_PVRFilteringGaussRadiusAO: Optional[int] = None
  m_PVRFilteringGaussRadiusDirect: Optional[int] = None
  m_PVRFilteringGaussRadiusIndirect: Optional[int] = None
  m_PVRFilteringMode: Optional[int] = None
  m_PVRSampleCount: Optional[int] = None
  m_PVRSampling: Optional[int] = None
  m_Padding: Optional[int] = None
  m_RealtimeResolution: Optional[float] = None
  m_TextureCompression: Optional[bool] = None
  m_TrainingDataDestination: Optional[str] = None


@unitypy_define
class LightmapParameters(NamedObject):
  AOAntiAliasingSamples: int
  AOQuality: int
  antiAliasingSamples: int
  backFaceTolerance: float
  bakedLightmapTag: int
  blurRadius: int
  clusterResolution: float
  directLightQuality: int
  edgeStitching: int
  irradianceBudget: int
  irradianceQuality: int
  isTransparent: int
  m_Name: str
  modellingTolerance: float
  resolution: float
  systemTag: int
  limitLightmapCount: Optional[bool] = None
  maxLightmapCount: Optional[int] = None
  pushoff: Optional[float] = None


@unitypy_define
class LocalizationAsset(NamedObject):
  Editor_Asset: bool
  Locale_ISO_Code: str
  String_Table: List[Tuple[str, str]]
  m_Name: str


@unitypy_define
class Material(NamedObject):
  m_Name: str
  m_SavedProperties: UnityPropertySheet
  m_Shader: PPtr[Shader]
  disabledShaderPasses: Optional[List[str]] = None
  m_BuildTextureStacks: Optional[List[BuildTextureStackReference]] = None
  m_CustomRenderQueue: Optional[int] = None
  m_DoubleSidedGI: Optional[bool] = None
  m_EnableInstancingVariants: Optional[bool] = None
  m_InvalidKeywords: Optional[List[str]] = None
  m_LightmapFlags: Optional[int] = None
  m_ShaderKeywords: Optional[Union[str, List[str]]] = None
  m_ValidKeywords: Optional[List[str]] = None
  stringTagMap: Optional[List[Tuple[str, str]]] = None


@unitypy_define
class ProceduralMaterial(Material):
  m_Name: str
  m_SavedProperties: UnityPropertySheet
  m_Shader: PPtr[Shader]
  disabledShaderPasses: Optional[List[str]] = None
  m_AnimationUpdateRate: Optional[int] = None
  m_BuildTextureStacks: Optional[List[BuildTextureStackReference]] = None
  m_CacheSize: Optional[int] = None
  m_CustomRenderQueue: Optional[int] = None
  m_DoubleSidedGI: Optional[bool] = None
  m_EnableInstancingVariants: Optional[bool] = None
  m_Flags: Optional[int] = None
  m_GenerateMipmaps: Optional[bool] = None
  m_Hash: Optional[Hash128] = None
  m_Height: Optional[int] = None
  m_Inputs: Optional[List[SubstanceInput]] = None
  m_InvalidKeywords: Optional[List[str]] = None
  m_LightmapFlags: Optional[int] = None
  m_LoadingBehavior: Optional[int] = None
  m_MaximumSize: Optional[int] = None
  m_PrototypeName: Optional[str] = None
  m_ShaderKeywords: Optional[Union[str, List[str]]] = None
  m_SubstancePackage: Optional[PPtr[SubstanceArchive]] = None
  m_Textures: Optional[List[PPtr[ProceduralTexture]]] = None
  m_ValidKeywords: Optional[List[str]] = None
  m_Width: Optional[int] = None
  stringTagMap: Optional[List[Tuple[str, str]]] = None


@unitypy_define
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


@unitypy_define
class Motion(NamedObject, ABC):
  pass


@unitypy_define
class AnimationClip(Motion):
  m_Bounds: AABB
  m_Compressed: bool
  m_CompressedRotationCurves: List[CompressedAnimationCurve]
  m_Events: List[AnimationEvent]
  m_FloatCurves: List[FloatCurve]
  m_Name: str
  m_PositionCurves: List[Vector3Curve]
  m_RotationCurves: List[QuaternionCurve]
  m_SampleRate: float
  m_ScaleCurves: List[Vector3Curve]
  m_WrapMode: int
  m_AnimationType: Optional[int] = None
  m_ClipBindingConstant: Optional[AnimationClipBindingConstant] = None
  m_EulerCurves: Optional[List[Vector3Curve]] = None
  m_HasGenericRootTransform: Optional[bool] = None
  m_HasMotionFloatCurves: Optional[bool] = None
  m_Legacy: Optional[bool] = None
  m_MuscleClip: Optional[ClipMuscleConstant] = None
  m_MuscleClipSize: Optional[int] = None
  m_PPtrCurves: Optional[List[PPtrCurve]] = None
  m_UseHighQualityCurve: Optional[bool] = None


@unitypy_define
class PreviewAnimationClip(AnimationClip):
  m_Bounds: AABB
  m_ClipBindingConstant: AnimationClipBindingConstant
  m_Compressed: bool
  m_CompressedRotationCurves: List[CompressedAnimationCurve]
  m_EulerCurves: List[Vector3Curve]
  m_Events: List[AnimationEvent]
  m_FloatCurves: List[FloatCurve]
  m_Legacy: bool
  m_MuscleClip: ClipMuscleConstant
  m_MuscleClipSize: int
  m_Name: str
  m_PPtrCurves: List[PPtrCurve]
  m_PositionCurves: List[Vector3Curve]
  m_RotationCurves: List[QuaternionCurve]
  m_SampleRate: float
  m_ScaleCurves: List[Vector3Curve]
  m_UseHighQualityCurve: bool
  m_WrapMode: int
  m_HasGenericRootTransform: Optional[bool] = None
  m_HasMotionFloatCurves: Optional[bool] = None


@unitypy_define
class BlendTree(Motion):
  m_Childs: Union[List[Child], List[ChildMotion]]
  m_MaxThreshold: float
  m_MinThreshold: float
  m_Name: str
  m_UseAutomaticThresholds: bool
  m_BlendEvent: Optional[str] = None
  m_BlendEventY: Optional[str] = None
  m_BlendParameter: Optional[str] = None
  m_BlendParameterY: Optional[str] = None
  m_BlendType: Optional[int] = None
  m_NormalizedBlendValues: Optional[bool] = None


@unitypy_define
class NavMeshData(NamedObject):
  m_HeightMeshes: List[HeightMeshData]
  m_Heightmaps: List[HeightmapData]
  m_Name: str
  m_NavMeshTiles: List[NavMeshTileData]
  m_OffMeshLinks: List[AutoOffMeshLinkData]
  m_AgentTypeID: Optional[int] = None
  m_NavMeshBuildSettings: Optional[NavMeshBuildSettings] = None
  m_NavMeshParams: Optional[NavMeshParams] = None
  m_Position: Optional[Vector3f] = None
  m_Rotation: Optional[Quaternionf] = None
  m_SourceBounds: Optional[AABB] = None


@unitypy_define
class NavMeshObsolete(NamedObject):
  m_Name: str


@unitypy_define
class OcclusionCullingData(NamedObject):
  m_Name: str
  m_PVSData: List[int]
  m_Scenes: List[OcclusionScene]


@unitypy_define
class PhysicsMaterial(NamedObject):
  m_Name: str
  bounceCombine: Optional[int] = None
  bounciness: Optional[float] = None
  dynamicFriction: Optional[float] = None
  frictionCombine: Optional[int] = None
  m_BounceCombine: Optional[int] = None
  m_Bounciness: Optional[float] = None
  m_DynamicFriction: Optional[float] = None
  m_FrictionCombine: Optional[int] = None
  m_StaticFriction: Optional[float] = None
  staticFriction: Optional[float] = None


@unitypy_define
class PhysicsMaterial2D(NamedObject):
  bounciness: float
  friction: float
  m_Name: str
  m_BounceCombine: Optional[int] = None
  m_FrictionCombine: Optional[int] = None


@unitypy_define
class PreloadData(NamedObject):
  m_Assets: List[PPtr[Object]]
  m_Name: str
  m_Dependencies: Optional[List[str]] = None
  m_ExplicitDataLayout: Optional[bool] = None


@unitypy_define
class Preset(NamedObject):
  m_Name: str
  m_Properties: List[PropertyModification]
  m_TargetType: PresetType
  m_CoupledProperties: Optional[List[PropertyModification]] = None
  m_CoupledType: Optional[PresetType] = None
  m_ExcludedProperties: Optional[List[str]] = None


@unitypy_define
class RayTracingShader(NamedObject):
  m_MaxRecursionDepth: int
  m_Name: str
  variants: List[RayTracingShaderVariant]
  m_EnableRayPayloadSizeChecks: Optional[bool] = None


@unitypy_define
class RoslynAdditionalFileAsset(NamedObject):
  m_Name: str


@unitypy_define
class RoslynAnalyzerConfigAsset(NamedObject):
  m_Name: str


@unitypy_define
class RuntimeAnimatorController(NamedObject):
  m_AnimationClips: List[PPtr[AnimationClip]]
  m_Controller: ControllerConstant
  m_ControllerSize: int
  m_Name: str
  m_TOS: List[Tuple[int, str]]


@unitypy_define
class AnimatorController(RuntimeAnimatorController):
  m_AnimationClips: List[PPtr[AnimationClip]]
  m_Controller: ControllerConstant
  m_ControllerSize: int
  m_Name: str
  m_TOS: List[Tuple[int, str]]
  m_MultiThreadedStateMachine: Optional[bool] = None
  m_StateMachineBehaviourVectorDescription: Optional[
    StateMachineBehaviourVectorDescription
  ] = None
  m_StateMachineBehaviours: Optional[List[PPtr[MonoBehaviour]]] = None


@unitypy_define
class AnimatorOverrideController(RuntimeAnimatorController):
  m_Clips: List[AnimationClipOverride]
  m_Controller: PPtr[RuntimeAnimatorController]
  m_Name: str


@unitypy_define
class Shader(NamedObject):
  m_Name: str
  compressedBlob: Optional[List[int]] = None
  compressedLengths: Optional[Union[List[int], List[List[int]]]] = None
  decompressedLengths: Optional[Union[List[int], List[List[int]]]] = None
  decompressedSize: Optional[int] = None
  m_AssetGUID: Optional[GUID] = None
  m_Dependencies: Optional[List[PPtr[Shader]]] = None
  m_NonModifiableTextures: Optional[List[Tuple[str, PPtr[Texture]]]] = None
  m_ParsedForm: Optional[SerializedShader] = None
  m_PathName: Optional[str] = None
  m_Script: Optional[str] = None
  m_ShaderIsBaked: Optional[bool] = None
  m_SubProgramBlob: Optional[List[int]] = None
  offsets: Optional[Union[List[int], List[List[int]]]] = None
  platforms: Optional[List[int]] = None
  stageCounts: Optional[List[int]] = None


@unitypy_define
class ShaderVariantCollection(NamedObject):
  m_Name: str
  m_Shaders: List[Tuple[PPtr[Shader], ShaderInfo]]


@unitypy_define
class SpeedTreeWindAsset(NamedObject):
  m_Name: str
  m_Config8: Optional[SpeedTreeWindConfig8] = None
  m_Config9: Optional[SpeedTreeWindConfig9] = None
  m_Wind: Optional[SpeedTreeWind] = None
  m_eVersion: Optional[int] = None


@unitypy_define
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


@unitypy_define
class SpriteAtlas(NamedObject):
  m_IsVariant: bool
  m_Name: str
  m_PackedSpriteNamesToIndex: List[str]
  m_PackedSprites: List[PPtr[Sprite]]
  m_RenderDataMap: List[Tuple[Tuple[GUID, int], SpriteAtlasData]]
  m_Tag: str


@unitypy_define
class SpriteAtlasAsset(NamedObject):
  m_ImporterData: Union[SpriteAtlasEditorData, SpriteAtlasAssetData]
  m_IsVariant: bool
  m_MasterAtlas: PPtr[SpriteAtlas]
  m_Name: str
  m_ScriptablePacker: Optional[PPtr[Object]] = None


@unitypy_define
class SubstanceArchive(NamedObject):
  m_Name: str
  m_PackageData: Optional[List[int]] = None


@unitypy_define
class TerrainData(NamedObject):
  m_DetailDatabase: DetailDatabase
  m_Heightmap: Heightmap
  m_Name: str
  m_SplatDatabase: SplatDatabase
  m_PreloadShaders: Optional[List[PPtr[Shader]]] = None


@unitypy_define
class TerrainLayer(NamedObject):
  m_DiffuseRemapMax: Vector4f
  m_DiffuseRemapMin: Vector4f
  m_DiffuseTexture: PPtr[Texture2D]
  m_MaskMapRemapMax: Vector4f
  m_MaskMapRemapMin: Vector4f
  m_MaskMapTexture: PPtr[Texture2D]
  m_Metallic: float
  m_Name: str
  m_NormalMapTexture: PPtr[Texture2D]
  m_NormalScale: float
  m_Smoothness: float
  m_Specular: ColorRGBA
  m_TileOffset: Vector2f
  m_TileSize: Vector2f
  m_SmoothnessSource: Optional[int] = None


@unitypy_define
class TextAsset(NamedObject):
  m_Name: str
  m_Script: str
  m_PathName: Optional[str] = None


@unitypy_define
class AssemblyDefinitionAsset(TextAsset):
  m_Name: str
  m_Script: str


@unitypy_define
class AssemblyDefinitionReferenceAsset(TextAsset):
  m_Name: str
  m_Script: str


@unitypy_define
class MonoScript(TextAsset):
  m_AssemblyName: str
  m_ClassName: str
  m_ExecutionOrder: int
  m_Name: str
  m_Namespace: str
  m_PropertiesHash: Union[Hash128, int]
  m_IsEditorScript: Optional[bool] = None


@unitypy_define
class PackageManifest(TextAsset):
  m_Name: str
  m_Script: str


@unitypy_define
class RuleSetFileAsset(TextAsset):
  m_Name: str
  m_Script: str


@unitypy_define
class ShaderInclude(TextAsset):
  m_Name: str
  m_Script: Optional[str] = None


@unitypy_define
class Texture(NamedObject, ABC):
  pass


@unitypy_define
class BaseVideoTexture(Texture, ABC):
  pass


@unitypy_define
class WebCamTexture(BaseVideoTexture):
  m_Name: str
  m_DownscaleFallback: Optional[bool] = None
  m_ForcedFallbackFormat: Optional[int] = None
  m_IsAlphaChannelOptional: Optional[bool] = None


@unitypy_define
class CubemapArray(Texture):
  image_data: bytes
  m_ColorSpace: int
  m_CubemapCount: int
  m_DataSize: int
  m_Format: int
  m_IsReadable: bool
  m_MipCount: int
  m_Name: str
  m_TextureSettings: GLTextureSettings
  m_Width: int
  m_DownscaleFallback: Optional[bool] = None
  m_ForcedFallbackFormat: Optional[int] = None
  m_IsAlphaChannelOptional: Optional[bool] = None
  m_StreamData: Optional[StreamingInfo] = None
  m_UsageMode: Optional[int] = None


@unitypy_define
class LowerResBlitTexture(Texture):
  m_Name: str
  m_DownscaleFallback: Optional[bool] = None
  m_ForcedFallbackFormat: Optional[int] = None
  m_IsAlphaChannelOptional: Optional[bool] = None


@unitypy_define
class MovieTexture(Texture):
  m_Name: str
  m_AudioClip: Optional[PPtr[AudioClip]] = None
  m_ColorSpace: Optional[int] = None
  m_DownscaleFallback: Optional[bool] = None
  m_ForcedFallbackFormat: Optional[int] = None
  m_IsAlphaChannelOptional: Optional[bool] = None
  m_Loop: Optional[bool] = None
  m_MovieData: Optional[List[int]] = None


@unitypy_define
class ProceduralTexture(Texture):
  m_Name: str
  AlphaSource: Optional[int] = None
  AlphaSourceIsGrayscale: Optional[bool] = None
  Format: Optional[int] = None
  Type: Optional[int] = None
  m_AlphaSourceIsInverted: Optional[bool] = None
  m_AlphaSourceUID: Optional[int] = None
  m_BakedData: Optional[List[int]] = None
  m_BakedParameters: Optional[TextureParameters] = None
  m_ColorSpace: Optional[int] = None
  m_DownscaleFallback: Optional[bool] = None
  m_ForcedFallbackFormat: Optional[int] = None
  m_IsAlphaChannelOptional: Optional[bool] = None
  m_LightmapFormat: Optional[int] = None
  m_Mipmaps: Optional[int] = None
  m_SubstanceMaterial: Optional[PPtr[ProceduralMaterial]] = None
  m_SubstanceTextureUID: Optional[int] = None
  m_TextureParameters: Optional[TextureParameters] = None
  m_TextureSettings: Optional[GLTextureSettings] = None


@unitypy_define
class RenderTexture(Texture):
  m_ColorFormat: int
  m_Height: int
  m_MipMap: bool
  m_Name: str
  m_TextureSettings: GLTextureSettings
  m_Width: int
  m_AntiAliasing: Optional[int] = None
  m_BindMS: Optional[bool] = None
  m_DepthFormat: Optional[int] = None
  m_DepthStencilFormat: Optional[int] = None
  m_Dimension: Optional[int] = None
  m_DownscaleFallback: Optional[bool] = None
  m_EnableCompatibleFormat: Optional[bool] = None
  m_EnableRandomWrite: Optional[bool] = None
  m_ForcedFallbackFormat: Optional[int] = None
  m_GenerateMips: Optional[bool] = None
  m_IsAlphaChannelOptional: Optional[bool] = None
  m_IsCubemap: Optional[bool] = None
  m_IsPowerOfTwo: Optional[bool] = None
  m_MipCount: Optional[int] = None
  m_SRGB: Optional[bool] = None
  m_ShadowSamplingMode: Optional[int] = None
  m_UseDynamicScale: Optional[bool] = None
  m_UseDynamicScaleExplicit: Optional[bool] = None
  m_VolumeDepth: Optional[int] = None


@unitypy_define
class CustomRenderTexture(RenderTexture):
  m_AntiAliasing: int
  m_ColorFormat: int
  m_CubemapFaceMask: int
  m_CurrentUpdateZoneSpace: int
  m_Dimension: int
  m_DoubleBuffered: bool
  m_GenerateMips: bool
  m_Height: int
  m_InitColor: ColorRGBA
  m_InitMaterial: PPtr[Material]
  m_InitTexture: PPtr[Texture]
  m_InitializationMode: int
  m_Material: PPtr[Material]
  m_MipMap: bool
  m_Name: str
  m_SRGB: bool
  m_ShaderPass: int
  m_TextureSettings: GLTextureSettings
  m_UpdateMode: int
  m_UpdatePeriod: float
  m_UpdateZoneSpace: int
  m_UpdateZones: List[UpdateZoneInfo]
  m_VolumeDepth: int
  m_Width: int
  m_WrapUpdateZones: bool
  m_BindMS: Optional[bool] = None
  m_DepthFormat: Optional[int] = None
  m_DepthStencilFormat: Optional[int] = None
  m_DownscaleFallback: Optional[bool] = None
  m_EnableCompatibleFormat: Optional[bool] = None
  m_EnableRandomWrite: Optional[bool] = None
  m_ForcedFallbackFormat: Optional[int] = None
  m_InitSource: Optional[int] = None
  m_IsAlphaChannelOptional: Optional[bool] = None
  m_MipCount: Optional[int] = None
  m_ShadowSamplingMode: Optional[int] = None
  m_UseDynamicScale: Optional[bool] = None
  m_UseDynamicScaleExplicit: Optional[bool] = None


@unitypy_define
class SparseTexture(Texture):
  m_ColorSpace: int
  m_Format: int
  m_Height: int
  m_MipCount: int
  m_Name: str
  m_TextureSettings: GLTextureSettings
  m_Width: int
  m_DownscaleFallback: Optional[bool] = None
  m_ForcedFallbackFormat: Optional[int] = None
  m_IsAlphaChannelOptional: Optional[bool] = None


@unitypy_define
class Texture2D(Texture):
  image_data: bytes
  m_CompleteImageSize: int
  m_Height: int
  m_ImageCount: int
  m_IsReadable: bool
  m_LightmapFormat: int
  m_Name: str
  m_TextureDimension: int
  m_TextureFormat: int
  m_TextureSettings: GLTextureSettings
  m_Width: int
  m_ColorSpace: Optional[int] = None
  m_DownscaleFallback: Optional[bool] = None
  m_ForcedFallbackFormat: Optional[int] = None
  m_IgnoreMasterTextureLimit: Optional[bool] = None
  m_IgnoreMipmapLimit: Optional[bool] = None
  m_IsAlphaChannelOptional: Optional[bool] = None
  m_IsPreProcessed: Optional[bool] = None
  m_MipCount: Optional[int] = None
  m_MipMap: Optional[bool] = None
  m_MipmapLimitGroupName: Optional[str] = None
  m_MipsStripped: Optional[int] = None
  m_PlatformBlob: Optional[List[int]] = None
  m_ReadAllowed: Optional[bool] = None
  m_StreamData: Optional[StreamingInfo] = None
  m_StreamingMipmaps: Optional[bool] = None
  m_StreamingMipmapsPriority: Optional[int] = None


@unitypy_define
class Cubemap(Texture2D):
  image_data: bytes
  m_CompleteImageSize: int
  m_Height: int
  m_ImageCount: int
  m_IsReadable: bool
  m_LightmapFormat: int
  m_Name: str
  m_TextureDimension: int
  m_TextureFormat: int
  m_TextureSettings: GLTextureSettings
  m_Width: int
  m_ColorSpace: Optional[int] = None
  m_DownscaleFallback: Optional[bool] = None
  m_ForcedFallbackFormat: Optional[int] = None
  m_IgnoreMasterTextureLimit: Optional[bool] = None
  m_IgnoreMipmapLimit: Optional[bool] = None
  m_IsAlphaChannelOptional: Optional[bool] = None
  m_IsPreProcessed: Optional[bool] = None
  m_MipCount: Optional[int] = None
  m_MipMap: Optional[bool] = None
  m_MipmapLimitGroupName: Optional[str] = None
  m_MipsStripped: Optional[int] = None
  m_PlatformBlob: Optional[List[int]] = None
  m_ReadAllowed: Optional[bool] = None
  m_SourceTextures: Optional[List[PPtr[Texture2D]]] = None
  m_StreamData: Optional[StreamingInfo] = None
  m_StreamingMipmaps: Optional[bool] = None
  m_StreamingMipmapsPriority: Optional[int] = None


@unitypy_define
class Texture2DArray(Texture):
  image_data: bytes
  m_ColorSpace: int
  m_DataSize: int
  m_Depth: int
  m_Format: int
  m_Height: int
  m_IsReadable: bool
  m_MipCount: int
  m_Name: str
  m_TextureSettings: GLTextureSettings
  m_Width: int
  m_DownscaleFallback: Optional[bool] = None
  m_ForcedFallbackFormat: Optional[int] = None
  m_IgnoreMipmapLimit: Optional[bool] = None
  m_IsAlphaChannelOptional: Optional[bool] = None
  m_MipmapLimitGroupName: Optional[str] = None
  m_MipsStripped: Optional[int] = None
  m_StreamData: Optional[StreamingInfo] = None
  m_UsageMode: Optional[int] = None


@unitypy_define
class Texture3D(Texture):
  image_data: bytes
  m_Height: int
  m_Name: str
  m_TextureSettings: GLTextureSettings
  m_Width: int
  m_ColorSpace: Optional[int] = None
  m_CompleteImageSize: Optional[int] = None
  m_DataSize: Optional[int] = None
  m_Depth: Optional[int] = None
  m_DownscaleFallback: Optional[bool] = None
  m_ForcedFallbackFormat: Optional[int] = None
  m_Format: Optional[int] = None
  m_ImageCount: Optional[int] = None
  m_IsAlphaChannelOptional: Optional[bool] = None
  m_IsReadable: Optional[bool] = None
  m_LightmapFormat: Optional[int] = None
  m_MipCount: Optional[int] = None
  m_MipMap: Optional[bool] = None
  m_ReadAllowed: Optional[bool] = None
  m_StreamData: Optional[StreamingInfo] = None
  m_TextureDimension: Optional[int] = None
  m_TextureFormat: Optional[int] = None
  m_UsageMode: Optional[int] = None


@unitypy_define
class VideoClip(NamedObject):
  Height: int
  Width: int
  m_AudioChannelCount: List[int]
  m_AudioLanguage: List[str]
  m_AudioSampleRate: List[int]
  m_ExternalResources: StreamedResource
  m_Format: int
  m_FrameCount: int
  m_FrameRate: float
  m_HasSplitAlpha: bool
  m_Name: str
  m_OriginalPath: str
  m_ProxyHeight: int
  m_ProxyWidth: int
  m_PixelAspecRatioDen: Optional[int] = None
  m_PixelAspecRatioNum: Optional[int] = None
  m_VideoShaders: Optional[List[PPtr[Shader]]] = None
  m_sRGB: Optional[bool] = None


@unitypy_define
class VisualEffectObject(NamedObject, ABC):
  pass


@unitypy_define
class VisualEffectAsset(VisualEffectObject):
  m_Infos: VisualEffectInfo
  m_Name: str
  m_Systems: List[VFXSystemDesc]


@unitypy_define
class VisualEffectSubgraph(VisualEffectObject, ABC):
  pass


@unitypy_define
class VisualEffectSubgraphBlock(VisualEffectSubgraph):
  m_Name: str


@unitypy_define
class VisualEffectSubgraphOperator(VisualEffectSubgraph):
  m_Name: str


@unitypy_define
class VisualEffectResource(NamedObject):
  m_Graph: PPtr[MonoBehaviour]
  m_Infos: Union[VisualEffectSettings, VisualEffectInfo]
  m_Name: str
  m_ShaderSources: Optional[List[VFXShaderSourceDesc]] = None
  m_Systems: Optional[List[VFXEditorSystemDesc]] = None


@unitypy_define
class EditorExtensionImpl(Object):
  gFlattenedTypeTree: Optional[List[int]] = None
  m_DataTemplate: Optional[PPtr[DataTemplate]] = None
  m_Object: Optional[PPtr[EditorExtension]] = None
  m_OverrideVariable: Optional[bitset] = None
  m_TemplateFather: Optional[PPtr[EditorExtensionImpl]] = None


@unitypy_define
class EditorSettings(Object):
  m_AssetNamingUsesSpace: Optional[bool] = None
  m_AssetPipelineMode: Optional[int] = None
  m_AsyncShaderCompilation: Optional[bool] = None
  m_Bc7TextureCompressor: Optional[int] = None
  m_CacheServerDownloadBatchSize: Optional[int] = None
  m_CacheServerEnableAuth: Optional[bool] = None
  m_CacheServerEnableDownload: Optional[bool] = None
  m_CacheServerEnableTls: Optional[bool] = None
  m_CacheServerEnableUpload: Optional[bool] = None
  m_CacheServerEndpoint: Optional[str] = None
  m_CacheServerMode: Optional[int] = None
  m_CacheServerNamespacePrefix: Optional[str] = None
  m_CacheServerValidationMode: Optional[int] = None
  m_CachingShaderPreprocessor: Optional[bool] = None
  m_CollabEditorSettings: Optional[CollabEditorSettings] = None
  m_DefaultBehaviorMode: Optional[int] = None
  m_DisableCookiesInLightmapper: Optional[bool] = None
  m_EnableEditorAsyncCPUTextureLoading: Optional[bool] = None
  m_EnableEnlightenBakedGI: Optional[bool] = None
  m_EnableRoslynAnalyzers: Optional[bool] = None
  m_EnableTextureStreamingInEditMode: Optional[bool] = None
  m_EnableTextureStreamingInPlayMode: Optional[bool] = None
  m_EnterPlayModeOptions: Optional[int] = None
  m_EnterPlayModeOptionsEnabled: Optional[bool] = None
  m_EtcTextureBestCompressor: Optional[int] = None
  m_EtcTextureCompressorBehavior: Optional[int] = None
  m_EtcTextureFastCompressor: Optional[int] = None
  m_EtcTextureNormalCompressor: Optional[int] = None
  m_ExternalVersionControlSupport: Optional[Union[str, int]] = None
  m_GameObjectNamingDigits: Optional[int] = None
  m_GameObjectNamingScheme: Optional[int] = None
  m_InspectorUseIMGUIDefaultInspector: Optional[bool] = None
  m_LineEndingsForNewScripts: Optional[int] = None
  m_PrefabModeAllowAutoSave: Optional[bool] = None
  m_PrefabRegularEnvironment: Optional[PPtr[SceneAsset]] = None
  m_PrefabUIEnvironment: Optional[PPtr[SceneAsset]] = None
  m_ProjectGenerationIncludedExtensions: Optional[str] = None
  m_ProjectGenerationRootNamespace: Optional[str] = None
  m_RecalculateEnvironmentLighting: Optional[bool] = None
  m_ReferencedClipsExactNaming: Optional[bool] = None
  m_RefreshImportMode: Optional[int] = None
  m_SerializationMode: Optional[int] = None
  m_SerializeInlineMappingsOnOneLine: Optional[bool] = None
  m_ShowLightmapResolutionOverlay: Optional[bool] = None
  m_SpritePackerCacheSize: Optional[int] = None
  m_SpritePackerMode: Optional[int] = None
  m_SpritePackerPaddingPower: Optional[int] = None
  m_UseLegacyProbeSampleCount: Optional[bool] = None
  m_UserGeneratedProjectSuffix: Optional[str] = None
  m_WebSecurityEmulationEnabled: Optional[int] = None
  m_WebSecurityEmulationHostUrl: Optional[str] = None


@unitypy_define
class EditorUserBuildSettings(Object):
  m_ActiveBuildTarget: int
  m_AllowDebugging: bool
  m_ArchitectureFlags: int
  m_BuildLocation: List[str]
  m_ConnectProfiler: bool
  m_Development: bool
  m_InstallInBuildFolder: bool
  m_SelectedAndroidSubtarget: int
  m_SelectedBuildTargetGroup: int
  m_SelectedStandaloneTarget: int
  m_ActiveBuildPlatformGroupName: Optional[str] = None
  m_ActiveBuildTargetGroup: Optional[int] = None
  m_ActivePlatformGuid: Optional[GUID] = None
  m_ActiveProfilePath: Optional[str] = None
  m_ActiveStandaloneBuildSubtarget: Optional[int] = None
  m_AndroidBuildSystem: Optional[int] = None
  m_AndroidBuildType: Optional[int] = None
  m_AndroidCreateSymbols: Optional[int] = None
  m_AndroidCreateSymbolsZip: Optional[bool] = None
  m_AndroidCurrentDeploymentTargetId: Optional[str] = None
  m_AndroidDebugMinification: Optional[int] = None
  m_AndroidDeviceSocketAddress: Optional[str] = None
  m_AndroidReleaseMinification: Optional[int] = None
  m_AndroidUseLegacySdkTools: Optional[bool] = None
  m_BuildAppBundle: Optional[bool] = None
  m_BuildScriptsOnly: Optional[bool] = None
  m_BuildWithDeepProfilingSupport: Optional[bool] = None
  m_CompressFilesInPackage: Optional[bool] = None
  m_CompressWithPsArc: Optional[bool] = None
  m_CreateRomFileForSwitch: Optional[bool] = None
  m_CreateSolutionFileForSwitch: Optional[bool] = None
  m_DatalessPlayer: Optional[bool] = None
  m_EnableDebugPadForSwitch: Optional[bool] = None
  m_EnableHeadlessMode: Optional[bool] = None
  m_EnableHeapInspectorForSwitch: Optional[bool] = None
  m_EnableHostIOForSwitch: Optional[bool] = None
  m_EnableMemoryTrackerForSwitch: Optional[bool] = None
  m_EnableRomCompressionForSwitch: Optional[bool] = None
  m_ExplicitArrayBoundsChecks: Optional[bool] = None
  m_ExplicitDivideByZeroChecks: Optional[bool] = None
  m_ExplicitNullChecks: Optional[bool] = None
  m_ExportAsGoogleAndroidProject: Optional[bool] = None
  m_FacebookAccessToken: Optional[str] = None
  m_FacebookCreatePackageForSubmission: Optional[bool] = None
  m_ForceInstallation: Optional[bool] = None
  m_ForceOptimizeScriptCompilation: Optional[bool] = None
  m_GenerateMetroReferenceProjects: Optional[bool] = None
  m_GenerateNintendoSwitchShaderInfo: Optional[bool] = None
  m_GenerateWSAReferenceProjects: Optional[bool] = None
  m_HTCSScriptDebuggingForSwitch: Optional[bool] = None
  m_Il2CppCodeGeneration: Optional[int] = None
  m_MovePackageToDiscOuterEdge: Optional[bool] = None
  m_NVNAftermath: Optional[bool] = None
  m_NVNDrawValidation: Optional[bool] = None
  m_NVNDrawValidationHeavy: Optional[bool] = None
  m_NVNDrawValidationLight: Optional[bool] = None
  m_NVNGraphicsDebuggerForSwitch: Optional[bool] = None
  m_NVNShaderDebugging: Optional[bool] = None
  m_NeedSubmissionMaterials: Optional[bool] = None
  m_OverrideMaxTextureSize: Optional[int] = None
  m_OverrideTextureCompression: Optional[int] = None
  m_PS4HardwareTarget: Optional[int] = None
  m_PS5KeepPackageFiles: Optional[bool] = None
  m_PS5WorkspaceName: Optional[str] = None
  m_PathOnRemoteDevice: Optional[str] = None
  m_PlatformSettings: Optional[List[Tuple[str, PlatformSettingsData]]] = None
  m_RedirectWritesToHostMountForSwitch: Optional[bool] = None
  m_RemoteDeviceAddress: Optional[str] = None
  m_RemoteDeviceExports: Optional[str] = None
  m_RemoteDeviceInfo: Optional[bool] = None
  m_RemoteDeviceUsername: Optional[str] = None
  m_RomCompressionConfigForSwitch: Optional[str] = None
  m_RomCompressionLevelForSwitch: Optional[int] = None
  m_RomCompressionTypeForSwitch: Optional[int] = None
  m_SaveADFForSwitch: Optional[bool] = None
  m_SelectedAndroidETC2Fallback: Optional[int] = None
  m_SelectedBlackBerryBuildType: Optional[int] = None
  m_SelectedBlackBerrySubtarget: Optional[int] = None
  m_SelectedBuildPlatformGroupName: Optional[str] = None
  m_SelectedBuildTarget: Optional[int] = None
  m_SelectedCompressionType: Optional[List[Tuple[str, int]]] = None
  m_SelectedEmbeddedLinuxArchitecture: Optional[int] = None
  m_SelectedFacebookTarget: Optional[int] = None
  m_SelectedIOSBuildType: Optional[int] = None
  m_SelectedMetroBuildAndRunDeployTarget: Optional[int] = None
  m_SelectedMetroBuildType: Optional[int] = None
  m_SelectedMetroSDK: Optional[int] = None
  m_SelectedMetroTarget: Optional[int] = None
  m_SelectedPS3Subtarget: Optional[int] = None
  m_SelectedPS4Subtarget: Optional[int] = None
  m_SelectedPS5CompressionLevel: Optional[int] = None
  m_SelectedPS5CompressionType: Optional[int] = None
  m_SelectedPS5Subtarget: Optional[int] = None
  m_SelectedPSMSubtarget: Optional[int] = None
  m_SelectedPSP2Subtarget: Optional[int] = None
  m_SelectedQNXArchitecture: Optional[int] = None
  m_SelectedQNXOsVersion: Optional[int] = None
  m_SelectedStandaloneBuildSubtarget: Optional[int] = None
  m_SelectedTizenSubtarget: Optional[int] = None
  m_SelectedWSAArchitecture: Optional[str] = None
  m_SelectedWSABuildAndRunDeployTarget: Optional[int] = None
  m_SelectedWSAMinUWPSDK: Optional[str] = None
  m_SelectedWSASDK: Optional[int] = None
  m_SelectedWSASubtarget: Optional[int] = None
  m_SelectedWSAUWPBuildType: Optional[int] = None
  m_SelectedWSAUWPSDK: Optional[str] = None
  m_SelectedWSAUWPVSVersion: Optional[str] = None
  m_SelectedWebGLSubtarget: Optional[int] = None
  m_SelectedWiiDebugLevel: Optional[int] = None
  m_SelectedWiiSubtarget: Optional[int] = None
  m_SelectedWiiUBootMode: Optional[int] = None
  m_SelectedWiiUBuildOutput: Optional[int] = None
  m_SelectedWiiUDebugLevel: Optional[int] = None
  m_SelectedWindowsBuildAndRunDeployTarget: Optional[int] = None
  m_SelectedXboxOneDeployDrive: Optional[int] = None
  m_SelectedXboxOneDeployMethod: Optional[int] = None
  m_SelectedXboxRunMethod: Optional[int] = None
  m_SelectedXboxSubtarget: Optional[int] = None
  m_SymlinkLibraries: Optional[bool] = None
  m_SymlinkSources: Optional[bool] = None
  m_SymlinkTrampoline: Optional[bool] = None
  m_UseLegacyNvnPoolAllocatorForSwitch: Optional[bool] = None
  m_WSADotNetNativeEnabled: Optional[List[bool]] = None
  m_WaitForPlayerConnection: Optional[bool] = None
  m_WaitForSwitchMemoryTrackerOnStartup: Optional[bool] = None
  m_WebGLClientBrowserPath: Optional[str] = None
  m_WebGLClientBrowserType: Optional[int] = None
  m_WebGLClientPlatform: Optional[int] = None
  m_WebGLOptimizationLevel: Optional[int] = None
  m_WebGLUsePreBuiltUnityEngine: Optional[bool] = None
  m_WebPlayerDeployOnline: Optional[bool] = None
  m_WebPlayerNaClSupport: Optional[bool] = None
  m_WebPlayerOfflineDeployment: Optional[bool] = None
  m_WebPlayerStreamed: Optional[bool] = None
  m_WiiUEnableNetAPI: Optional[bool] = None
  m_WindowsDevicePortalAddress: Optional[str] = None
  m_WindowsDevicePortalUsername: Optional[str] = None
  m_WsaHolographicRemoting: Optional[bool] = None
  m_XboxCompressedXex: Optional[bool] = None
  m_XboxOneNetworkSharePath: Optional[str] = None
  m_XboxOneStreamingInstallLaunchChunkRange: Optional[int] = None
  m_XboxOneUsername: Optional[str] = None
  m_macosXcodeBuildConfig: Optional[int] = None


@unitypy_define
class EditorUserSettings(Object):
  m_VCAutomaticAdd: bool
  m_VCDebugCmd: bool
  m_VCDebugCom: bool
  m_VCDebugOut: bool
  m_ArtifactGarbageCollection: Optional[bool] = None
  m_AssetPipelineMode: Optional[int] = None
  m_AssetPipelineMode2: Optional[int] = None
  m_CacheServerMode: Optional[int] = None
  m_CacheServers: Optional[List[str]] = None
  m_CompressAssetsOnImport: Optional[bool] = None
  m_ConfigSettings: Optional[List[Tuple[str, ConfigSetting]]] = None
  m_ConfigValues: Optional[List[Tuple[str, str]]] = None
  m_DesiredImportWorkerCount: Optional[int] = None
  m_IdleImportWorkerShutdownDelay: Optional[int] = None
  m_SemanticMergeMode: Optional[int] = None
  m_StandbyImportWorkerCount: Optional[int] = None
  m_VCAllowAsyncUpdate: Optional[bool] = None
  m_VCHierarchyOverlayIcons: Optional[bool] = None
  m_VCOtherOverlayIcons: Optional[bool] = None
  m_VCOverlayIcons: Optional[bool] = None
  m_VCOverwriteFailedCheckoutAssets: Optional[bool] = None
  m_VCPassword: Optional[str] = None
  m_VCProjectOverlayIcons: Optional[bool] = None
  m_VCScanLocalPackagesOnConnect: Optional[bool] = None
  m_VCServer: Optional[str] = None
  m_VCShowFailedCheckout: Optional[bool] = None
  m_VCUserName: Optional[str] = None
  m_VCWorkspace: Optional[str] = None


@unitypy_define
class EmptyObject(Object):
  pass


@unitypy_define
class GUIDSerializer(Object):
  guidToPath: List[Tuple[GUID, str]]


@unitypy_define
class GameManager(Object, ABC):
  pass


@unitypy_define
class GlobalGameManager(GameManager, ABC):
  pass


@unitypy_define
class AnimationManager(GlobalGameManager):
  pass


@unitypy_define
class AudioManager(GlobalGameManager):
  Default_Speaker_Mode: int
  Doppler_Factor: float
  Rolloff_Scale: float
  m_DSPBufferSize: int
  m_Volume: float
  m_AmbisonicDecoderPlugin: Optional[str] = None
  m_DisableAudio: Optional[bool] = None
  m_RealVoiceCount: Optional[int] = None
  m_RequestedDSPBufferSize: Optional[int] = None
  m_SampleRate: Optional[int] = None
  m_SpatializerPlugin: Optional[str] = None
  m_SpeedOfSound: Optional[float] = None
  m_VirtualVoiceCount: Optional[int] = None
  m_VirtualizeEffects: Optional[bool] = None


@unitypy_define
class BuildSettings(GlobalGameManager):
  enableDynamicBatching: bool
  hasAdvancedVersion: bool
  hasPROVersion: bool
  hasPublishingRights: bool
  hasShadows: bool
  isEducationalBuild: bool
  m_Version: str
  buildGUID: Optional[Union[str, GUID]] = None
  buildTags: Optional[List[str]] = None
  enableMultipleDisplays: Optional[bool] = None
  enabledVRDevices: Optional[List[str]] = None
  hasClusterRendering: Optional[bool] = None
  hasLocalLightShadows: Optional[bool] = None
  hasOculusPlugin: Optional[bool] = None
  hasRenderTexture: Optional[bool] = None
  hasSoftShadows: Optional[bool] = None
  isDebugBuild: Optional[bool] = None
  isEmbedded: Optional[bool] = None
  isNoWatermarkBuild: Optional[bool] = None
  isPrototypingBuild: Optional[bool] = None
  isTrial: Optional[bool] = None
  isWsaHolographicRemotingEnabled: Optional[bool] = None
  levels: Optional[List[str]] = None
  m_AuthToken: Optional[str] = None
  m_GraphicsAPIs: Optional[List[int]] = None
  preloadedPlugins: Optional[List[str]] = None
  runtimeClassHashes: Optional[
    Union[List[Tuple[int, int]], List[Tuple[int, Hash128]]]
  ] = None
  scenes: Optional[List[str]] = None
  scriptHashes: Optional[List[Tuple[Hash128, Hash128]]] = None
  usesOnMouseEvents: Optional[bool] = None


@unitypy_define
class CloudWebServicesManager(GlobalGameManager):
  pass


@unitypy_define
class ClusterInputManager(GlobalGameManager):
  m_Inputs: List[ClusterInput]


@unitypy_define
class CrashReportManager(GlobalGameManager):
  pass


@unitypy_define
class DelayedCallManager(GlobalGameManager):
  pass


@unitypy_define
class GraphicsSettings(GlobalGameManager):
  m_AlwaysIncludedShaders: List[PPtr[Shader]]
  m_AllowEnlightenSupportForUpgradedProject: Optional[bool] = None
  m_CameraRelativeLightCulling: Optional[bool] = None
  m_CameraRelativeShadowCulling: Optional[bool] = None
  m_CurrentRenderPipelineGlobalSettings: Optional[PPtr[Object]] = None
  m_CustomRenderPipeline: Optional[PPtr[MonoBehaviour]] = None
  m_DefaultRenderingLayerMask: Optional[int] = None
  m_Deferred: Optional[BuiltinShaderSettings] = None
  m_DeferredReflections: Optional[BuiltinShaderSettings] = None
  m_DepthNormals: Optional[BuiltinShaderSettings] = None
  m_LegacyDeferred: Optional[BuiltinShaderSettings] = None
  m_LensFlare: Optional[BuiltinShaderSettings] = None
  m_LightHalo: Optional[BuiltinShaderSettings] = None
  m_LightProbeOutsideHullStrategy: Optional[int] = None
  m_LightsUseCCT: Optional[bool] = None
  m_LightsUseColorTemperature: Optional[bool] = None
  m_LightsUseLinearIntensity: Optional[bool] = None
  m_LogWhenShaderIsCompiled: Optional[bool] = None
  m_MotionVectors: Optional[BuiltinShaderSettings] = None
  m_PreloadShadersBatchTimeLimit: Optional[int] = None
  m_PreloadedShaders: Optional[List[PPtr[ShaderVariantCollection]]] = None
  m_SRPDefaultSettings: Optional[List[Tuple[str, PPtr[Object]]]] = None
  m_ScreenSpaceShadows: Optional[BuiltinShaderSettings] = None
  m_ShaderDefinesPerShaderCompiler: Optional[List[PlatformShaderDefines]] = None
  m_ShaderSettings: Optional[PlatformShaderSettings] = None
  m_ShaderSettings_Tier1: Optional[PlatformShaderSettings] = None
  m_ShaderSettings_Tier2: Optional[PlatformShaderSettings] = None
  m_ShaderSettings_Tier3: Optional[PlatformShaderSettings] = None
  m_SpritesDefaultMaterial: Optional[PPtr[Material]] = None
  m_TierSettings_Tier1: Optional[TierGraphicsSettings] = None
  m_TierSettings_Tier2: Optional[TierGraphicsSettings] = None
  m_TierSettings_Tier3: Optional[TierGraphicsSettings] = None
  m_TransparencySortAxis: Optional[Vector3f] = None
  m_TransparencySortMode: Optional[int] = None
  m_VideoShadersIncludeMode: Optional[int] = None


@unitypy_define
class InputManager(GlobalGameManager):
  m_Axes: List[InputAxis]
  m_UsePhysicalKeys: Optional[bool] = None


@unitypy_define
class MasterServerInterface(GlobalGameManager):
  pass


@unitypy_define
class MonoManager(GlobalGameManager):
  m_Scripts: List[PPtr[MonoScript]]
  m_AssemblyNames: Optional[List[str]] = None
  m_AssemblyTypes: Optional[List[int]] = None
  m_RuntimeClassHashes: Optional[List[Tuple[int, Hash128]]] = None
  m_ScriptHashes: Optional[List[Tuple[Hash128, Hash128]]] = None


@unitypy_define
class MultiplayerManager(GlobalGameManager):
  m_ActiveMultiplayerRole: Optional[int] = None
  m_ActiveMultiplayerRoles: Optional[int] = None


@unitypy_define
class NavMeshProjectSettings(GlobalGameManager):
  areas: List[NavMeshAreaData]
  m_LastAgentTypeID: Optional[int] = None
  m_SettingNames: Optional[List[str]] = None
  m_Settings: Optional[List[NavMeshBuildSettings]] = None


@unitypy_define
class NetworkManager(GlobalGameManager):
  m_AssetToPrefab: List[Tuple[GUID, PPtr[GameObject]]]
  m_DebugLevel: int
  m_Sendrate: float


@unitypy_define
class NotificationManager(GlobalGameManager):
  pass


@unitypy_define
class PerformanceReportingManager(GlobalGameManager):
  pass


@unitypy_define
class Physics2DSettings(GlobalGameManager):
  m_DefaultMaterial: PPtr[PhysicsMaterial2D]
  m_Gravity: Vector2f
  m_LayerCollisionMatrix: List[int]
  m_PositionIterations: int
  m_VelocityIterations: int
  m_AngularSleepTolerance: Optional[float] = None
  m_AutoSimulation: Optional[bool] = None
  m_AutoSyncTransforms: Optional[bool] = None
  m_BaumgarteScale: Optional[float] = None
  m_BaumgarteTimeOfImpactScale: Optional[float] = None
  m_BounceThreshold: Optional[float] = None
  m_CallbacksOnDisable: Optional[bool] = None
  m_ChangeStopsCallbacks: Optional[bool] = None
  m_ContactThreshold: Optional[float] = None
  m_DefaultContactOffset: Optional[float] = None
  m_DeleteStopsCallbacks: Optional[bool] = None
  m_JobOptions: Optional[PhysicsJobOptions2D] = None
  m_LinearSleepTolerance: Optional[float] = None
  m_MaxAngularCorrection: Optional[float] = None
  m_MaxLinearCorrection: Optional[float] = None
  m_MaxRotationSpeed: Optional[float] = None
  m_MaxSubStepCount: Optional[int] = None
  m_MaxTranslationSpeed: Optional[float] = None
  m_MinPenetrationForPenalty: Optional[float] = None
  m_MinSubStepFPS: Optional[float] = None
  m_QueriesHitTriggers: Optional[bool] = None
  m_QueriesStartInColliders: Optional[bool] = None
  m_RaycastsHitTriggers: Optional[bool] = None
  m_RaycastsStartInColliders: Optional[bool] = None
  m_ReuseCollisionCallbacks: Optional[bool] = None
  m_SimulationLayers: Optional[BitField] = None
  m_SimulationMode: Optional[int] = None
  m_TimeToSleep: Optional[float] = None
  m_UseSubStepContacts: Optional[bool] = None
  m_UseSubStepping: Optional[bool] = None
  m_VelocityThreshold: Optional[float] = None


@unitypy_define
class PhysicsManager(GlobalGameManager):
  m_BounceThreshold: float
  m_DefaultMaterial: Union[PPtr[PhysicMaterial], PPtr[PhysicsMaterial]]
  m_Gravity: Vector3f
  m_LayerCollisionMatrix: List[int]
  m_AutoSimulation: Optional[bool] = None
  m_AutoSyncTransforms: Optional[bool] = None
  m_BroadphaseType: Optional[int] = None
  m_ClothGravity: Optional[Vector3f] = None
  m_ClothInterCollisionDistance: Optional[float] = None
  m_ClothInterCollisionSettingsToggle: Optional[bool] = None
  m_ClothInterCollisionStiffness: Optional[float] = None
  m_ContactPairsMode: Optional[int] = None
  m_ContactsGeneration: Optional[int] = None
  m_CurrentBackendId: Optional[int] = None
  m_DefaultContactOffset: Optional[float] = None
  m_DefaultMaxAngluarSpeed: Optional[float] = None
  m_DefaultMaxAngularSpeed: Optional[float] = None
  m_DefaultMaxDepenetrationVelocity: Optional[float] = None
  m_DefaultSolverIterations: Optional[int] = None
  m_DefaultSolverVelocityIterations: Optional[int] = None
  m_EnableAdaptiveForce: Optional[bool] = None
  m_EnableEnhancedDeterminism: Optional[bool] = None
  m_EnablePCM: Optional[bool] = None
  m_EnableUnifiedHeightmaps: Optional[bool] = None
  m_FastMotionThreshold: Optional[float] = None
  m_FrictionType: Optional[int] = None
  m_ImprovedPatchFriction: Optional[bool] = None
  m_InvokeCollisionCallbacks: Optional[bool] = None
  m_MaxAngularVelocity: Optional[float] = None
  m_MinPenetrationForPenalty: Optional[float] = None
  m_QueriesHitBackfaces: Optional[bool] = None
  m_QueriesHitTriggers: Optional[bool] = None
  m_RaycastsHitTriggers: Optional[bool] = None
  m_ReuseCollisionCallbacks: Optional[bool] = None
  m_ScratchBufferChunkCount: Optional[int] = None
  m_SimulationMode: Optional[int] = None
  m_SleepAngularVelocity: Optional[float] = None
  m_SleepThreshold: Optional[float] = None
  m_SleepVelocity: Optional[float] = None
  m_SolverIterationCount: Optional[int] = None
  m_SolverType: Optional[int] = None
  m_SolverVelocityIterations: Optional[int] = None
  m_WorldBounds: Optional[AABB] = None
  m_WorldSubdivisions: Optional[int] = None


@unitypy_define
class PlayerSettings(GlobalGameManager):
  AndroidProfiler: bool
  allowedAutorotateToLandscapeLeft: bool
  allowedAutorotateToLandscapeRight: bool
  allowedAutorotateToPortrait: bool
  allowedAutorotateToPortraitUpsideDown: bool
  companyName: str
  defaultScreenHeight: int
  defaultScreenHeightWeb: int
  defaultScreenOrientation: int
  defaultScreenWidth: int
  defaultScreenWidthWeb: int
  productName: str
  runInBackground: bool
  targetDevice: int
  use32BitDisplayBuffer: bool
  useMacAppStoreValidation: bool
  useOSAutorotation: bool
  usePlayerLog: bool
  AID: Optional[Hash128] = None
  AndroidEnableSustainedPerformanceMode: Optional[bool] = None
  AndroidFilterTouchesWhenObscured: Optional[bool] = None
  AndroidLicensePublicKey: Optional[str] = None
  D3DHDRBitDepth: Optional[int] = None
  Force_IOS_Speakers_When_Recording: Optional[bool] = None
  Override_IPod_Music: Optional[bool] = None
  Prepare_IOS_For_Recording: Optional[bool] = None
  accelerometerFrequency: Optional[int] = None
  activeInputHandler: Optional[int] = None
  allowFullscreenSwitch: Optional[bool] = None
  allowHDRDisplaySupport: Optional[bool] = None
  androidApplicationEntry: Optional[int] = None
  androidAutoRotationBehavior: Optional[int] = None
  androidBlitType: Optional[int] = None
  androidDefaultWindowHeight: Optional[int] = None
  androidDefaultWindowWidth: Optional[int] = None
  androidFullscreenMode: Optional[int] = None
  androidMaxAspectRatio: Optional[float] = None
  androidMinAspectRatio: Optional[float] = None
  androidMinimumWindowHeight: Optional[int] = None
  androidMinimumWindowWidth: Optional[int] = None
  androidPredictiveBackSupport: Optional[bool] = None
  androidRenderOutsideSafeArea: Optional[bool] = None
  androidResizableWindow: Optional[bool] = None
  androidResizeableActivity: Optional[bool] = None
  androidShowActivityIndicatorOnLoading: Optional[int] = None
  androidStartInFullscreen: Optional[bool] = None
  androidSupportedAspectRatio: Optional[int] = None
  androidUseSwappy: Optional[bool] = None
  androidVulkanAllowFilterList: Optional[List[AndroidDeviceFilterData]] = None
  androidVulkanDenyFilterList: Optional[List[AndroidDeviceFilterData]] = None
  bakeCollisionMeshes: Optional[bool] = None
  bundleIdentifier: Optional[str] = None
  bundleVersion: Optional[str] = None
  captureSingleScreen: Optional[bool] = None
  cloudEnabled: Optional[bool] = None
  cloudProjectId: Optional[str] = None
  cpuConfiguration: Optional[List[int]] = None
  cursorHotspot: Optional[Vector2f] = None
  d3d11ForceExclusiveMode: Optional[bool] = None
  d3d11FullscreenMode: Optional[int] = None
  d3d9FullscreenMode: Optional[int] = None
  debugUnloadMode: Optional[int] = None
  dedicatedServerOptimizations: Optional[bool] = None
  defaultCursor: Optional[PPtr[Texture2D]] = None
  defaultIsFullScreen: Optional[bool] = None
  defaultIsNativeResolution: Optional[bool] = None
  deferSystemGesturesMode: Optional[int] = None
  disableDepthAndStencilBuffers: Optional[bool] = None
  disableOldInputManagerSupport: Optional[bool] = None
  displayResolutionDialog: Optional[int] = None
  enableFrameTimingStats: Optional[bool] = None
  enableGamepadInput: Optional[bool] = None
  enableHWStatistics: Optional[bool] = None
  enableNativePlatformBackendsForNewInputSystem: Optional[bool] = None
  enableNewInputSystem: Optional[bool] = None
  enableOpenGLProfilerGPURecorders: Optional[bool] = None
  forceSRGBBlit: Optional[bool] = None
  forceSingleInstance: Optional[bool] = None
  framebufferDepthMemorylessMode: Optional[int] = None
  fullscreenMode: Optional[int] = None
  gpuSkinning: Optional[bool] = None
  graphicsJobMode: Optional[int] = None
  graphicsJobs: Optional[bool] = None
  hdrBitDepth: Optional[int] = None
  hideHomeButton: Optional[bool] = None
  hmiLoadingImage: Optional[PPtr[Texture2D]] = None
  iPhoneBundleIdentifier: Optional[str] = None
  ignoreAlphaClear: Optional[bool] = None
  insecureHttpOption: Optional[int] = None
  invalidatedPatternTexture: Optional[PPtr[Texture2D]] = None
  iosAllowHTTPDownload: Optional[bool] = None
  iosAppInBackgroundBehavior: Optional[int] = None
  iosShowActivityIndicatorOnLoading: Optional[int] = None
  iosUseCustomAppBackgroundBehavior: Optional[bool] = None
  isWsaHolographicRemotingEnabled: Optional[bool] = None
  legacyClampBlendShapeWeights: Optional[bool] = None
  loadStoreDebugModeEnabled: Optional[bool] = None
  m_ActiveColorSpace: Optional[int] = None
  m_ColorGamuts: Optional[List[int]] = None
  m_HolographicPauseOnTrackingLoss: Optional[bool] = None
  m_HolographicTrackingLossScreen: Optional[PPtr[Texture2D]] = None
  m_MTRendering: Optional[bool] = None
  m_MobileMTRendering: Optional[bool] = None
  m_MobileRenderingPath: Optional[int] = None
  m_RenderingPath: Optional[int] = None
  m_ShowUnitySplashLogo: Optional[bool] = None
  m_ShowUnitySplashScreen: Optional[bool] = None
  m_SplashScreenAnimation: Optional[int] = None
  m_SplashScreenBackgroundAnimationZoom: Optional[float] = None
  m_SplashScreenBackgroundColor: Optional[ColorRGBA] = None
  m_SplashScreenBackgroundLandscape: Optional[PPtr[Texture2D]] = None
  m_SplashScreenBackgroundLandscapeAspect: Optional[float] = None
  m_SplashScreenBackgroundLandscapeUvs: Optional[Rectf] = None
  m_SplashScreenBackgroundPortrait: Optional[PPtr[Texture2D]] = None
  m_SplashScreenBackgroundPortraitAspect: Optional[float] = None
  m_SplashScreenBackgroundPortraitUvs: Optional[Rectf] = None
  m_SplashScreenDrawMode: Optional[int] = None
  m_SplashScreenLogoAnimationZoom: Optional[float] = None
  m_SplashScreenLogoStyle: Optional[int] = None
  m_SplashScreenLogos: Optional[List[SplashScreenLogo]] = None
  m_SplashScreenOverlayOpacity: Optional[float] = None
  m_SplashScreenStyle: Optional[int] = None
  m_SpriteBatchVertexThreshold: Optional[int] = None
  m_StackTraceTypes: Optional[List[int]] = None
  m_StereoRenderingPath: Optional[int] = None
  m_Stereoscopic3D: Optional[bool] = None
  m_SupportedAspectRatios: Optional[AspectRatios] = None
  m_UnitySplashLogo: Optional[PPtr[Sprite]] = None
  m_UseDX11: Optional[bool] = None
  m_VirtualRealitySplashScreen: Optional[PPtr[Texture2D]] = None
  macAppStoreCategory: Optional[str] = None
  macFullscreenMode: Optional[int] = None
  macRetinaSupport: Optional[bool] = None
  meshDeformation: Optional[int] = None
  metalFramebufferOnly: Optional[bool] = None
  metroEnableIndependentInputSource: Optional[bool] = None
  metroEnableLowLatencyPresentationAPI: Optional[bool] = None
  metroInputSource: Optional[int] = None
  mipStripping: Optional[bool] = None
  mobileMTRenderingBaked: Optional[bool] = None
  muteOtherAudioSources: Optional[bool] = None
  n3dsDisableStereoscopicView: Optional[bool] = None
  n3dsEnableSharedListOpt: Optional[bool] = None
  n3dsEnableVSync: Optional[bool] = None
  numberOfMipsStripped: Optional[int] = None
  numberOfMipsStrippedPerMipmapLimitGroup: Optional[List[Tuple[str, int]]] = None
  organizationId: Optional[str] = None
  platformRequiresReadableAssets: Optional[bool] = None
  playerDataPath: Optional[str] = None
  playerMinOpenGLESVersion: Optional[int] = None
  preloadedAssets: Optional[List[PPtr[Object]]] = None
  preserveFramebufferAlpha: Optional[bool] = None
  productGUID: Optional[GUID] = None
  projectId: Optional[str] = None
  projectName: Optional[str] = None
  protectGraphicsMemory: Optional[bool] = None
  ps3SplashScreen: Optional[PPtr[Texture2D]] = None
  psp2AcquireBGM: Optional[bool] = None
  psp2PowerMode: Optional[int] = None
  qualitySettingsNames: Optional[List[str]] = None
  resetResolutionOnWindowResize: Optional[bool] = None
  resizableWindow: Optional[bool] = None
  resolutionScalingMode: Optional[int] = None
  singlePassStereoRendering: Optional[bool] = None
  stadiaPresentMode: Optional[int] = None
  stadiaTargetFramerate: Optional[int] = None
  stripPhysics: Optional[bool] = None
  submitAnalytics: Optional[bool] = None
  switchAllowGpuScratchShrinking: Optional[bool] = None
  switchGpuScratchPoolGranularity: Optional[int] = None
  switchMaxWorkerMultiple: Optional[int] = None
  switchNVNDefaultPoolsGranularity: Optional[int] = None
  switchNVNGraphicsFirmwareMemory: Optional[int] = None
  switchNVNMaxPublicSamplerIDCount: Optional[int] = None
  switchNVNMaxPublicTextureIDCount: Optional[int] = None
  switchNVNOtherPoolsGranularity: Optional[int] = None
  switchNVNShaderPoolsGranularity: Optional[int] = None
  switchQueueCommandMemory: Optional[int] = None
  switchQueueComputeMemory: Optional[int] = None
  switchQueueControlMemory: Optional[int] = None
  targetGlesGraphics: Optional[int] = None
  targetIOSGraphics: Optional[int] = None
  targetPixelDensity: Optional[int] = None
  targetPlatform: Optional[int] = None
  targetResolution: Optional[int] = None
  tizenShowActivityIndicatorOnLoading: Optional[int] = None
  tvOSBundleVersion: Optional[str] = None
  uiUse16BitDepthBuffer: Optional[bool] = None
  unsupportedMSAAFallback: Optional[int] = None
  uploadClearedTextureDataAfterCreationFromScript: Optional[bool] = None
  use24BitDepthBuffer: Optional[bool] = None
  useAlphaInDashboard: Optional[bool] = None
  useFlipModelSwapchain: Optional[bool] = None
  useHDRDisplay: Optional[bool] = None
  useOnDemandResources: Optional[bool] = None
  videoMemoryForVertexBuffers: Optional[int] = None
  virtualRealitySupported: Optional[bool] = None
  virtualTexturingSupportEnabled: Optional[bool] = None
  visibleInBackground: Optional[bool] = None
  visionOSBundleVersion: Optional[str] = None
  vrSettings: Optional[VRSettings] = None
  vulkanEnableCommandBufferRecycling: Optional[bool] = None
  vulkanEnableLateAcquireNextImage: Optional[bool] = None
  vulkanEnablePreTransform: Optional[bool] = None
  vulkanEnableSetSRGBWrite: Optional[bool] = None
  vulkanNumSwapchainBuffers: Optional[int] = None
  vulkanUseSWCommandBuffers: Optional[bool] = None
  wiiHio2Usage: Optional[int] = None
  wiiLoadingScreenBackground: Optional[ColorRGBA] = None
  wiiLoadingScreenFileName: Optional[str] = None
  wiiLoadingScreenPeriod: Optional[int] = None
  wiiLoadingScreenRect: Optional[Rectf] = None
  wiiLoadingScreenRectPlacement: Optional[int] = None
  wiiUAllowScreenCapture: Optional[bool] = None
  wiiUControllerCount: Optional[int] = None
  wiiUGamePadMSAA: Optional[int] = None
  wiiUSupportsBalanceBoard: Optional[bool] = None
  wiiUSupportsClassicController: Optional[bool] = None
  wiiUSupportsMotionPlus: Optional[bool] = None
  wiiUSupportsNunchuk: Optional[bool] = None
  wiiUSupportsProController: Optional[bool] = None
  wiiUTVResolution: Optional[int] = None
  windowsGamepadBackendHint: Optional[int] = None
  wsaTransparentSwapchain: Optional[bool] = None
  xboxEnableAvatar: Optional[bool] = None
  xboxEnableEnableRenderThreadRunsJobs: Optional[bool] = None
  xboxEnableFitness: Optional[bool] = None
  xboxEnableGuest: Optional[bool] = None
  xboxEnableHeadOrientation: Optional[bool] = None
  xboxEnableKinect: Optional[bool] = None
  xboxEnableKinectAutoTracking: Optional[bool] = None
  xboxEnablePIXSampling: Optional[bool] = None
  xboxEnableSpeech: Optional[bool] = None
  xboxOneDisableEsram: Optional[bool] = None
  xboxOneDisableKinectGpuReservation: Optional[bool] = None
  xboxOneEnable7thCore: Optional[bool] = None
  xboxOneEnableTypeOptimization: Optional[bool] = None
  xboxOneLoggingLevel: Optional[int] = None
  xboxOneMonoLoggingLevel: Optional[int] = None
  xboxOnePresentImmediateThreshold: Optional[int] = None
  xboxOneResolution: Optional[int] = None
  xboxOneSResolution: Optional[int] = None
  xboxOneXResolution: Optional[int] = None
  xboxPIXTextureCapture: Optional[bool] = None
  xboxSkinOnGPU: Optional[bool] = None
  xboxSpeechDB: Optional[int] = None


@unitypy_define
class QualitySettings(GlobalGameManager):
  Beautiful: Optional[QualitySetting] = None
  Fantastic: Optional[QualitySetting] = None
  Fast: Optional[QualitySetting] = None
  Fastest: Optional[QualitySetting] = None
  Good: Optional[QualitySetting] = None
  Simple: Optional[QualitySetting] = None
  m_CurrentQuality: Optional[int] = None
  m_DefaultMobileQuality: Optional[int] = None
  m_DefaultStandaloneQuality: Optional[int] = None
  m_DefaultWebPlayerQuality: Optional[int] = None
  m_EditorQuality: Optional[int] = None
  m_QualitySettings: Optional[List[QualitySetting]] = None
  m_StrippedMaximumLODLevel: Optional[int] = None
  m_TextureMipmapLimitGroupNames: Optional[List[str]] = None


@unitypy_define
class ResourceManager(GlobalGameManager):
  m_Container: List[Tuple[str, PPtr[Object]]]
  m_DependentAssets: Optional[List[ResourceManager_Dependency]] = None


@unitypy_define
class RuntimeInitializeOnLoadManager(GlobalGameManager):
  m_AfterAssembliesLoadedMethodExecutionOrders: Optional[List[int]] = None
  m_AfterAssembliesLoadedUnityMethodExecutionOrders: Optional[List[int]] = None
  m_AfterMethodExecutionOrders: Optional[List[int]] = None
  m_AfterUnityMethodExecutionOrders: Optional[List[int]] = None
  m_AssemblyNames: Optional[List[str]] = None
  m_BeforeMethodExecutionOrders: Optional[List[int]] = None
  m_BeforeSplashScreenMethodExecutionOrders: Optional[List[int]] = None
  m_BeforeSplashScreenUnityMethodExecutionOrders: Optional[List[int]] = None
  m_BeforeUnityMethodExecutionOrders: Optional[List[int]] = None
  m_ClassInfos: Optional[List[ClassInfo]] = None
  m_ClassMethodInfos: Optional[List[ClassMethodInfo]] = None
  m_MethodExecutionOrders: Optional[List[int]] = None
  m_NamespaceNames: Optional[List[str]] = None
  m_SubsystemRegistrationMethodExecutionOrders: Optional[List[int]] = None
  m_SubsystemRegistrationUnityMethodExecutionOrders: Optional[List[int]] = None
  m_UnityMethodExecutionOrders: Optional[List[int]] = None


@unitypy_define
class ShaderNameRegistry(GlobalGameManager):
  m_PreloadShaders: bool
  m_Shaders: NameToObjectMap


@unitypy_define
class StreamingManager(GlobalGameManager):
  pass


@unitypy_define
class TagManager(GlobalGameManager):
  tags: List[str]
  Builtin_Layer_0: Optional[str] = None
  Builtin_Layer_1: Optional[str] = None
  Builtin_Layer_2: Optional[str] = None
  Builtin_Layer_3: Optional[str] = None
  Builtin_Layer_4: Optional[str] = None
  Builtin_Layer_5: Optional[str] = None
  Builtin_Layer_6: Optional[str] = None
  Builtin_Layer_7: Optional[str] = None
  User_Layer_10: Optional[str] = None
  User_Layer_11: Optional[str] = None
  User_Layer_12: Optional[str] = None
  User_Layer_13: Optional[str] = None
  User_Layer_14: Optional[str] = None
  User_Layer_15: Optional[str] = None
  User_Layer_16: Optional[str] = None
  User_Layer_17: Optional[str] = None
  User_Layer_18: Optional[str] = None
  User_Layer_19: Optional[str] = None
  User_Layer_20: Optional[str] = None
  User_Layer_21: Optional[str] = None
  User_Layer_22: Optional[str] = None
  User_Layer_23: Optional[str] = None
  User_Layer_24: Optional[str] = None
  User_Layer_25: Optional[str] = None
  User_Layer_26: Optional[str] = None
  User_Layer_27: Optional[str] = None
  User_Layer_28: Optional[str] = None
  User_Layer_29: Optional[str] = None
  User_Layer_30: Optional[str] = None
  User_Layer_31: Optional[str] = None
  User_Layer_8: Optional[str] = None
  User_Layer_9: Optional[str] = None
  layers: Optional[List[str]] = None
  m_RenderingLayers: Optional[List[str]] = None
  m_SortingLayers: Optional[List[SortingLayerEntry]] = None


@unitypy_define
class TimeManager(GlobalGameManager):
  Fixed_Timestep: Union[RationalTime, float]
  Maximum_Allowed_Timestep: float
  m_TimeScale: float
  Maximum_Particle_Timestep: Optional[float] = None


@unitypy_define
class UnityAdsManager(GlobalGameManager):
  pass


@unitypy_define
class UnityAnalyticsManager(GlobalGameManager):
  m_Enabled: Optional[bool] = None
  m_InitializeOnStartup: Optional[bool] = None
  m_TestConfigUrl: Optional[str] = None
  m_TestEventUrl: Optional[str] = None
  m_TestMode: Optional[bool] = None


@unitypy_define
class UnityConnectSettings(GlobalGameManager):
  UnityAnalyticsSettings: UnityAnalyticsSettings
  UnityPurchasingSettings: UnityPurchasingSettings
  CrashReportingSettings: Optional[CrashReportingSettings] = None
  PerformanceReportingSettings: Optional[PerformanceReportingSettings] = None
  UnityAdsSettings: Optional[UnityAdsSettings] = None
  m_ConfigUrl: Optional[str] = None
  m_DashboardUrl: Optional[str] = None
  m_Enabled: Optional[bool] = None
  m_EventOldUrl: Optional[str] = None
  m_EventUrl: Optional[str] = None
  m_TestConfigUrl: Optional[str] = None
  m_TestEventUrl: Optional[str] = None
  m_TestInitMode: Optional[int] = None
  m_TestMode: Optional[bool] = None


@unitypy_define
class VFXManager(GlobalGameManager):
  m_CopyBufferShader: PPtr[ComputeShader]
  m_FixedTimeStep: float
  m_IndirectShader: PPtr[ComputeShader]
  m_MaxDeltaTime: float
  m_RenderPipeSettingsPath: str
  m_SortShader: PPtr[ComputeShader]
  m_BatchEmptyLifetime: Optional[int] = None
  m_CompiledVersion: Optional[int] = None
  m_EmptyShader: Optional[PPtr[Shader]] = None
  m_MaxCapacity: Optional[int] = None
  m_MaxScrubTime: Optional[float] = None
  m_RuntimeResources: Optional[PPtr[MonoBehaviour]] = None
  m_RuntimeVersion: Optional[int] = None
  m_StripUpdateShader: Optional[PPtr[ComputeShader]] = None


@unitypy_define
class LevelGameManager(GameManager, ABC):
  pass


@unitypy_define
class HaloManager(LevelGameManager):
  pass


@unitypy_define
class LightmapSettings(LevelGameManager):
  m_Lightmaps: List[LightmapData]
  m_LightmapsMode: int
  m_BakedColorSpace: Optional[int] = None
  m_EnlightenSceneMapping: Optional[EnlightenSceneMapping] = None
  m_GISettings: Optional[GISettings] = None
  m_LightProbes: Optional[PPtr[LightProbes]] = None
  m_LightingSettings: Optional[PPtr[LightingSettings]] = None
  m_RuntimeCPUUsage: Optional[int] = None
  m_ShadowMaskMode: Optional[int] = None
  m_UseDualLightmapsInForward: Optional[bool] = None
  m_UseShadowmask: Optional[bool] = None


@unitypy_define
class NavMeshSettings(LevelGameManager):
  m_NavMesh: Optional[PPtr[NavMesh]] = None
  m_NavMeshData: Optional[PPtr[NavMeshData]] = None


@unitypy_define
class OcclusionCullingSettings(LevelGameManager):
  m_OcclusionCullingData: PPtr[OcclusionCullingData]
  m_Portals: List[PPtr[OcclusionPortal]]
  m_SceneGUID: GUID
  m_StaticRenderers: List[PPtr[Renderer]]


@unitypy_define
class RenderSettings(LevelGameManager):
  m_FlareStrength: float
  m_Fog: bool
  m_FogColor: ColorRGBA
  m_FogDensity: float
  m_FogMode: int
  m_HaloStrength: float
  m_HaloTexture: PPtr[Texture2D]
  m_LinearFogEnd: float
  m_LinearFogStart: float
  m_SkyboxMaterial: PPtr[Material]
  m_SpotCookie: PPtr[Texture2D]
  m_AmbientEquatorColor: Optional[ColorRGBA] = None
  m_AmbientGroundColor: Optional[ColorRGBA] = None
  m_AmbientIntensity: Optional[float] = None
  m_AmbientLight: Optional[ColorRGBA] = None
  m_AmbientMode: Optional[int] = None
  m_AmbientProbe: Optional[SphericalHarmonicsL2] = None
  m_AmbientProbeInGamma: Optional[SphericalHarmonicsL2] = None
  m_AmbientSkyColor: Optional[ColorRGBA] = None
  m_CustomReflection: Optional[Union[PPtr[Cubemap], PPtr[Texture]]] = None
  m_DefaultReflectionMode: Optional[int] = None
  m_DefaultReflectionResolution: Optional[int] = None
  m_FlareFadeSpeed: Optional[float] = None
  m_GeneratedSkyboxReflection: Optional[PPtr[Cubemap]] = None
  m_IndirectSpecularColor: Optional[ColorRGBA] = None
  m_ReflectionBounces: Optional[int] = None
  m_ReflectionIntensity: Optional[float] = None
  m_SubtractiveShadowColor: Optional[ColorRGBA] = None
  m_Sun: Optional[PPtr[Light]] = None
  m_UseRadianceAmbientProbe: Optional[bool] = None


@unitypy_define
class HierarchyState(Object):
  expanded: List[PPtr[Object]]
  selection: List[PPtr[Object]]
  scrollposition_x: Optional[float] = None
  scrollposition_x: Optional[float] = None
  scrollposition_y: Optional[float] = None
  scrollposition_y: Optional[float] = None


@unitypy_define
class InspectorExpandedState(Object):
  m_ExpandedData: List[ExpandedData]


@unitypy_define
class MarshallingTestObject(Object):
  m_Prop: int


@unitypy_define
class MemorySettings(Object):
  pass


@unitypy_define
class NScreenBridge(Object):
  pass


@unitypy_define
class NativeObjectType(Object):
  m_Inner: NativeType


@unitypy_define
class PackedAssets(Object):
  m_Contents: List[BuildReportPackedAssetInfo]
  m_Overhead: int
  m_ShortPath: str
  m_File: Optional[int] = None


@unitypy_define
class PlatformModuleSetup(Object):
  modules: List[Module]


@unitypy_define
class PluginBuildInfo(Object):
  m_EditorPlugins: List[str]
  m_RuntimePlugins: List[str]


@unitypy_define
class Prefab(Object):
  m_RootGameObject: PPtr[GameObject]
  m_ContainsMissingSerializeReferenceTypes: Optional[bool] = None
  m_HideFlagsBehaviour: Optional[int] = None
  m_IsExploded: Optional[bool] = None
  m_IsPrefabAsset: Optional[bool] = None
  m_IsPrefabParent: Optional[bool] = None
  m_Modification: Optional[PrefabModification] = None
  m_ParentPrefab: Optional[PPtr[Prefab]] = None
  m_SourcePrefab: Optional[PPtr[Prefab]] = None


@unitypy_define
class PrefabInstance(Object):
  m_Modification: PrefabModification
  m_RootGameObject: PPtr[GameObject]
  m_SourcePrefab: PPtr[Prefab]


@unitypy_define
class PresetManager(Object):
  m_DefaultList: Optional[List[DefaultPresetList]] = None
  m_DefaultPresets: Optional[List[Tuple[PresetType, List[DefaultPreset]]]] = None


@unitypy_define
class PropertyModificationsTargetTestObject(Object):
  m_Array: List[PropertyModificationsTargetTestNativeObject]
  m_Data: PropertyModificationsTargetTestNativeObject
  m_FloatTestValue: float
  byte_data: Optional[bytes] = None
  m_Bytes: Optional[List[int]] = None
  m_BytesSize: Optional[int] = None
  m_Floats: Optional[List[float]] = None


@unitypy_define
class RenderPassAttachment(Object):
  pass


@unitypy_define
class SceneRoots(Object):
  m_Roots: List[PPtr[Object]]


@unitypy_define
class SceneVisibilityState(Object):
  m_IsolationMode: Optional[bool] = None
  m_MainStageIsolated: Optional[bool] = None
  m_PrefabStageIsolated: Optional[bool] = None
  m_SceneData: Optional[List[Tuple[SceneIdentifier, SceneVisibilityData]]] = None
  m_ScenePickingData: Optional[SceneDataContainer] = None
  m_SceneVisibilityData: Optional[SceneDataContainer] = None
  m_SceneVisibilityDataIsolated: Optional[SceneDataContainer] = None


@unitypy_define
class ScenesUsingAssets(Object):
  m_ListOfScenesUsingEachAsset: List[Tuple[str, List[str]]]
  m_ScenesUsingAssets: List[BuildReportScenesUsingAsset]


@unitypy_define
class SerializableManagedHost(Object):
  m_Script: PPtr[MonoScript]


@unitypy_define
class SerializableManagedRefTestClass(Object):
  m_Script: PPtr[MonoScript]


@unitypy_define
class ShaderContainer(Object):
  pass


@unitypy_define
class SiblingDerived(Object):
  pass


@unitypy_define
class SpriteAtlasDatabase(Object):
  pass


@unitypy_define
class TestObjectVectorPairStringBool(Object):
  m_Map: List[Tuple[str, bool]]
  m_String: str


@unitypy_define
class TestObjectWithSerializedAnimationCurve(Object):
  m_Curve: AnimationCurve


@unitypy_define
class TestObjectWithSerializedArray(Object):
  m_ClampTestValue: float
  m_IntegerArray: List[int]


@unitypy_define
class TestObjectWithSerializedMapStringBool(Object):
  m_Map: List[Tuple[str, bool]]
  m_String: str


@unitypy_define
class TestObjectWithSerializedMapStringNonAlignedStruct(Object):
  m_Map: List[Tuple[str, NonAlignedStruct]]
  m_String: str


@unitypy_define
class TestObjectWithSpecialLayoutOne(Object):
  differentLayout: LayoutDataOne
  sameLayout: LayoutDataOne


@unitypy_define
class TestObjectWithSpecialLayoutTwo(Object):
  differentLayout: LayoutDataTwo
  sameLayout: LayoutDataThree


@unitypy_define
class TilemapEditorUserSettings(Object):
  m_FocusMode: int
  m_LastUsedPalette: PPtr[GameObject]


@unitypy_define
class VersionControlSettings(Object):
  m_Mode: str
  m_CollabEditorSettings: Optional[CollabEditorSettings] = None
  m_TrackPackagesOutsideProject: Optional[bool] = None


@unitypy_define
class VideoBuildInfo(Object):
  m_IsVideoModuleDisabled: bool
  m_VideoClipCount: int


@unitypy_define
class AABB:
  m_Center: Vector3f
  m_Extent: Vector3f


@unitypy_define
class AddedComponent:
  addedObject: PPtr[Component]
  insertIndex: int
  targetCorrespondingSourceObject: PPtr[GameObject]


@unitypy_define
class AddedGameObject:
  addedObject: PPtr[Transform]
  insertIndex: int
  targetCorrespondingSourceObject: PPtr[Transform]


@unitypy_define
class AndroidDeviceFilterData:
  androidOsVersionString: str
  brandName: str
  deviceName: str
  driverVersionString: str
  productName: str
  vendorName: str
  vulkanApiVersionString: str


@unitypy_define
class AnimationClipBindingConstant:
  genericBindings: List[GenericBinding]
  pptrCurveMapping: List[PPtr[Object]]


@unitypy_define
class AnimationClipOverride:
  m_OriginalClip: PPtr[AnimationClip]
  m_OverrideClip: PPtr[AnimationClip]


@unitypy_define
class AnimationCurve:
  m_Curve: List[Keyframe]
  m_PostInfinity: int
  m_PreInfinity: int
  m_RotationOrder: Optional[int] = None


@unitypy_define
class AnimationEvent:
  data: str
  floatParameter: float
  functionName: str
  intParameter: int
  messageOptions: int
  objectReferenceParameter: PPtr[Object]
  time: float


@unitypy_define
class AnimatorCondition:
  m_ConditionEvent: str
  m_ConditionMode: int
  m_EventTreshold: float


@unitypy_define
class Annotation:
  m_ClassID: int
  m_Flags: int
  m_GizmoEnabled: bool
  m_IconEnabled: bool
  m_ScriptClass: str


@unitypy_define
class ArticulationDrive:
  damping: float
  forceLimit: float
  lowerLimit: float
  stiffness: float
  target: float
  targetVelocity: float
  upperLimit: float
  driveType: Optional[int] = None


@unitypy_define
class AspectRatios:
  Others: bool
  x16_10: bool
  x16_9: bool
  x4_3: bool
  x5_4: bool


@unitypy_define
class AssemblyJsonAsset(TextAsset):
  m_Name: str
  m_Script: str
  m_PathName: Optional[str] = None


@unitypy_define
class AssemblyJsonImporter(AssetImporter):
  m_AssetBundleName: str
  m_AssetBundleVariant: str
  m_Name: str
  m_UserData: str
  m_ExternalObjects: Optional[List[Tuple[SourceAssetIdentifier, PPtr[Object]]]] = None


@unitypy_define
class Asset:
  children: List[GUID]
  labels: AssetLabels
  mainRepresentation: LibraryRepresentation
  parent: GUID
  representations: List[LibraryRepresentation]
  type: int
  assetBundleIndex: Optional[int] = None
  digest: Optional[MdFour] = None
  guidOfPathLocationDependencies: Optional[
    Union[List[Tuple[str, GUID]], List[Tuple[GUID, str]]]
  ] = None
  hash: Optional[Union[Hash128, MdFour]] = None
  hashOfImportedAssetDependencies: Optional[List[GUID]] = None
  hashOfSourceAssetDependencies: Optional[List[GUID]] = None
  importerClassId: Optional[int] = None
  importerVersionHash: Optional[int] = None
  metaModificationDate_0_: Optional[int] = None
  metaModificationDate_1_: Optional[int] = None
  modificationDate_0_: Optional[int] = None
  modificationDate_1_: Optional[int] = None
  scriptedImporterClassID: Optional[str] = None


@unitypy_define
class AssetBundleFullName:
  m_AssetBundleName: str
  m_AssetBundleVariant: str


@unitypy_define
class AssetBundleInfo:
  AssetBundleDependencies: List[int]
  AssetBundleHash: Hash128


@unitypy_define
class AssetBundleScriptInfo:
  assemblyName: str
  className: str
  hash: int
  nameSpace: str


@unitypy_define
class AssetDatabase(Object):
  m_Assets: List[Tuple[GUID, Asset]]
  m_AssetBundleNames: Optional[List[Tuple[int, AssetBundleFullName]]] = None
  m_AssetTimeStamps: Optional[List[Tuple[str, AssetTimeStamp]]] = None
  m_Metrics: Optional[AssetDatabaseMetrics] = None
  m_UnityShadersVersion: Optional[int] = None
  m_lastValidVersionHashes: Optional[List[Tuple[int, int]]] = None


@unitypy_define
class AssetDatabaseMetrics:
  totalAssetCount: int
  nonProAssetCount: Optional[int] = None
  nonProAssetsCreatedAfterProLicense: Optional[int] = None


@unitypy_define
class AssetImporterHashKey:
  ScriptClass: str
  type: int


@unitypy_define
class AssetImporterLog(NamedObject):
  m_Logs: List[AssetImporter_ImportError]
  m_Name: str


@unitypy_define
class AssetImporter_ImportError:
  error: str
  file: str
  line: int
  mode: int
  object: PPtr[Object]


@unitypy_define
class AssetInfo:
  asset: PPtr[Object]
  preloadIndex: int
  preloadSize: int


@unitypy_define
class AssetLabels:
  m_Labels: List[str]


@unitypy_define
class AssetTimeStamp:
  metaModificationDate_0_: int
  metaModificationDate_1_: int
  modificationDate_0_: int
  modificationDate_1_: int


@unitypy_define
class AttachmentIndexArray:
  activeAttachments: int
  attachments: List[int]


@unitypy_define
class AttachmentInfo:
  format: int
  needsResolve: bool


@unitypy_define
class AudioImporterOutput:
  editorOutputContainerFormat: int
  editorOutputSettings: SampleSettings
  outputContainerFormat: int
  outputSettings: SampleSettings
  playerResource: Optional[StreamedResource] = None


@unitypy_define
class AudioMixerConstant:
  effectGUIDs: List[GUID]
  effects: List[EffectConstant]
  exposedParameterIndices: List[int]
  exposedParameterNames: List[int]
  groupGUIDs: List[GUID]
  groupNameBuffer: List[str]
  groups: List[GroupConstant]
  numSideChainBuffers: int
  pluginEffectNameBuffer: List[str]
  snapshotGUIDs: List[GUID]
  snapshotNameBuffer: List[str]
  snapshots: List[SnapshotConstant]
  groupConnections: Optional[List[GroupConnection]] = None


@unitypy_define
class AudioMixerLiveUpdateBool(ABC):
  pass


@unitypy_define
class AudioMixerLiveUpdateFloat(ABC):
  pass


@unitypy_define
class AutoOffMeshLinkData:
  m_Area: int
  m_End: Vector3f
  m_LinkDirection: int
  m_LinkType: int
  m_Radius: float
  m_Start: Vector3f


@unitypy_define
class AvatarBodyMask(NamedObject):
  m_Mask: List[int]
  m_Name: str


@unitypy_define
class AvatarConstant:
  m_Human: OffsetPtr
  m_HumanSkeletonIndexArray: List[int]
  m_RootMotionBoneIndex: int
  m_RootMotionBoneX: xform
  m_AvatarSkeleton: Optional[OffsetPtr] = None
  m_AvatarSkeletonPose: Optional[OffsetPtr] = None
  m_DefaultPose: Optional[OffsetPtr] = None
  m_HumanSkeletonReverseIndexArray: Optional[List[int]] = None
  m_RootMotionSkeleton: Optional[OffsetPtr] = None
  m_RootMotionSkeletonIndexArray: Optional[List[int]] = None
  m_RootMotionSkeletonPose: Optional[OffsetPtr] = None
  m_Skeleton: Optional[OffsetPtr] = None
  m_SkeletonNameIDArray: Optional[List[int]] = None
  m_SkeletonPose: Optional[OffsetPtr] = None


@unitypy_define
class AvatarSkeletonMaskElement:
  path: str
  weight: float


@unitypy_define
class Axes:
  m_Length: float
  m_Limit: Limit
  m_PostQ: float4
  m_PreQ: float4
  m_Sgn: Union[float3, float4]
  m_Type: int


@unitypy_define
class BitField:
  m_Bits: int


@unitypy_define
class Blend1dDataConstant:
  m_ChildThresholdArray: List[float]


@unitypy_define
class Blend2dDataConstant:
  m_ChildMagnitudeArray: Optional[List[float]] = None
  m_ChildNeighborListArray: Optional[List[MotionNeighborList]] = None
  m_ChildPairAvgMagInvArray: Optional[List[float]] = None
  m_ChildPairVectorArray: Optional[List[Vector2f]] = None
  m_ChildPositionArray: Optional[List[Vector2f]] = None
  m_ChildThresholdArray: Optional[List[float]] = None


@unitypy_define
class BlendDirectDataConstant:
  m_ChildBlendEventIDArray: List[int]
  m_NormalizedBlendValues: bool


@unitypy_define
class BlendShapeData:
  channels: List[MeshBlendShapeChannel]
  fullWeights: List[float]
  shapes: List[MeshBlendShape]
  vertices: List[BlendShapeVertex]


@unitypy_define
class BlendShapeVertex:
  index: int
  normal: Vector3f
  tangent: Vector3f
  vertex: Vector3f


@unitypy_define
class BlendTreeConstant:
  m_NodeArray: List[OffsetPtr]
  m_BlendEventArrayConstant: Optional[OffsetPtr] = None


@unitypy_define
class BlendTreeNodeConstant:
  m_BlendEventID: int
  m_ChildIndices: List[int]
  m_ClipID: int
  m_Duration: float
  m_Blend1dData: Optional[OffsetPtr] = None
  m_Blend2dData: Optional[OffsetPtr] = None
  m_BlendDirectData: Optional[OffsetPtr] = None
  m_BlendEventYID: Optional[int] = None
  m_BlendType: Optional[int] = None
  m_ChildThresholdArray: Optional[List[float]] = None
  m_ClipIndex: Optional[int] = None
  m_CycleOffset: Optional[float] = None
  m_Mirror: Optional[bool] = None


@unitypy_define
class BoneInfluence:
  boneIndex_0_: int
  boneIndex_1_: int
  boneIndex_2_: int
  boneIndex_3_: int
  weight_0_: float
  weight_1_: float
  weight_2_: float
  weight_3_: float


@unitypy_define
class BoneWeights4:
  boneIndex_0_: int
  boneIndex_1_: int
  boneIndex_2_: int
  boneIndex_3_: int
  weight_0_: float
  weight_1_: float
  weight_2_: float
  weight_3_: float


@unitypy_define
class BranchWindLevel:
  m_afBend_0: float
  m_afBend_1: float
  m_afBend_10: float
  m_afBend_11: float
  m_afBend_12: float
  m_afBend_13: float
  m_afBend_14: float
  m_afBend_15: float
  m_afBend_16: float
  m_afBend_17: float
  m_afBend_18: float
  m_afBend_19: float
  m_afBend_2: float
  m_afBend_3: float
  m_afBend_4: float
  m_afBend_5: float
  m_afBend_6: float
  m_afBend_7: float
  m_afBend_8: float
  m_afBend_9: float
  m_afFlexibility_0: float
  m_afFlexibility_1: float
  m_afFlexibility_10: float
  m_afFlexibility_11: float
  m_afFlexibility_12: float
  m_afFlexibility_13: float
  m_afFlexibility_14: float
  m_afFlexibility_15: float
  m_afFlexibility_16: float
  m_afFlexibility_17: float
  m_afFlexibility_18: float
  m_afFlexibility_19: float
  m_afFlexibility_2: float
  m_afFlexibility_3: float
  m_afFlexibility_4: float
  m_afFlexibility_5: float
  m_afFlexibility_6: float
  m_afFlexibility_7: float
  m_afFlexibility_8: float
  m_afFlexibility_9: float
  m_afOscillation_0: float
  m_afOscillation_1: float
  m_afOscillation_10: float
  m_afOscillation_11: float
  m_afOscillation_12: float
  m_afOscillation_13: float
  m_afOscillation_14: float
  m_afOscillation_15: float
  m_afOscillation_16: float
  m_afOscillation_17: float
  m_afOscillation_18: float
  m_afOscillation_19: float
  m_afOscillation_2: float
  m_afOscillation_3: float
  m_afOscillation_4: float
  m_afOscillation_5: float
  m_afOscillation_6: float
  m_afOscillation_7: float
  m_afOscillation_8: float
  m_afOscillation_9: float
  m_afSpeed_0: float
  m_afSpeed_1: float
  m_afSpeed_10: float
  m_afSpeed_11: float
  m_afSpeed_12: float
  m_afSpeed_13: float
  m_afSpeed_14: float
  m_afSpeed_15: float
  m_afSpeed_16: float
  m_afSpeed_17: float
  m_afSpeed_18: float
  m_afSpeed_19: float
  m_afSpeed_2: float
  m_afSpeed_3: float
  m_afSpeed_4: float
  m_afSpeed_5: float
  m_afSpeed_6: float
  m_afSpeed_7: float
  m_afSpeed_8: float
  m_afSpeed_9: float
  m_afTurbulence_0: float
  m_afTurbulence_1: float
  m_afTurbulence_10: float
  m_afTurbulence_11: float
  m_afTurbulence_12: float
  m_afTurbulence_13: float
  m_afTurbulence_14: float
  m_afTurbulence_15: float
  m_afTurbulence_16: float
  m_afTurbulence_17: float
  m_afTurbulence_18: float
  m_afTurbulence_19: float
  m_afTurbulence_2: float
  m_afTurbulence_3: float
  m_afTurbulence_4: float
  m_afTurbulence_5: float
  m_afTurbulence_6: float
  m_afTurbulence_7: float
  m_afTurbulence_8: float
  m_afTurbulence_9: float
  m_fIndependence: float


@unitypy_define
class BufferBinding:
  m_Index: int
  m_NameIndex: int
  m_ArraySize: Optional[int] = None


@unitypy_define
class BuildReportFile:
  id: int
  path: str
  role: str
  totalSize: int


@unitypy_define
class BuildReportPackedAssetInfo:
  classID: int
  fileID: int
  packedSize: int
  sourceAssetGUID: GUID
  buildTimeAssetPath: Optional[str] = None
  offset: Optional[int] = None


@unitypy_define
class BuildReportScenesUsingAsset:
  assetPath: str
  scenePaths: List[str]


@unitypy_define
class BuildStepInfo:
  messages: List[BuildStepMessage]
  stepName: str
  depth: Optional[int] = None
  duration: Optional[int] = None
  durationTicks: Optional[int] = None


@unitypy_define
class BuildStepMessage:
  content: str
  type: int


@unitypy_define
class BuildSummary:
  assetBundleOptions: int
  crc: int
  options: int
  outputPath: str
  platformName: str
  totalErrors: int
  totalSize: int
  totalWarnings: int
  buildGUID: Optional[GUID] = None
  buildResult: Optional[int] = None
  buildStartTime: Optional[DateTime] = None
  buildType: Optional[int] = None
  multiProcessEnabled: Optional[bool] = None
  name: Optional[str] = None
  platformGroupName: Optional[str] = None
  subtarget: Optional[int] = None
  success: Optional[bool] = None
  totalTimeMS: Optional[int] = None
  totalTimeTicks: Optional[int] = None


@unitypy_define
class BuildTargetSettings:
  m_BuildTarget: str
  m_TextureFormat: int
  m_AllowsAlphaSplitting: Optional[bool] = None
  m_CompressionQuality: Optional[int] = None
  m_LoadingBehavior: Optional[int] = None
  m_MaxTextureSize: Optional[int] = None
  m_TextureHeight: Optional[int] = None
  m_TextureWidth: Optional[int] = None


@unitypy_define
class BuildTextureStackReference:
  groupName: str
  itemName: str


@unitypy_define
class BuiltAssetBundleInfo:
  bundleArchiveFile: int
  bundleName: str
  packagedFileIndices: List[int]


@unitypy_define
class BuiltinShaderSettings:
  m_Mode: int
  m_Shader: PPtr[Shader]


@unitypy_define
class CGProgram(TextAsset):
  m_Name: str
  m_Script: str
  m_PathName: Optional[str] = None


@unitypy_define
class CachedAssetMetaData:
  guid: GUID
  originalChangeset: int
  originalDigest: Union[Hash128, MdFour]
  originalName: str
  originalParent: GUID
  pathName: str


@unitypy_define
class Channel:
  attributeName: str
  byteOffset: int
  curve: AnimationCurve


@unitypy_define
class ChannelInfo:
  dimension: int
  format: int
  offset: int
  stream: int


@unitypy_define
class CharacterInfo:
  index: int
  uv: Rectf
  vert: Rectf
  advance: Optional[float] = None
  flipped: Optional[bool] = None
  width: Optional[float] = None


@unitypy_define
class Child:
  m_IsAnim: bool
  m_Motion: PPtr[Motion]
  m_Threshold: float
  m_TimeScale: float
  m_CycleOffset: Optional[float] = None
  m_Mirror: Optional[bool] = None
  m_Position: Optional[Vector2f] = None


@unitypy_define
class ChildAnimatorState:
  m_Position: Vector3f
  m_State: PPtr[AnimatorState]


@unitypy_define
class ChildAnimatorStateMachine:
  m_Position: Vector3f
  m_StateMachine: PPtr[AnimatorStateMachine]


@unitypy_define
class ChildMotion:
  m_CycleOffset: float
  m_DirectBlendParameter: str
  m_Mirror: bool
  m_Motion: PPtr[Motion]
  m_Position: Vector2f
  m_Threshold: float
  m_TimeScale: float


@unitypy_define
class ClampVelocityModule:
  dampen: float
  enabled: bool
  magnitude: MinMaxCurve
  separateAxis: bool
  x: MinMaxCurve
  y: MinMaxCurve
  z: MinMaxCurve
  drag: Optional[MinMaxCurve] = None
  inWorldSpace: Optional[bool] = None
  multiplyDragByParticleSize: Optional[bool] = None
  multiplyDragByParticleVelocity: Optional[bool] = None


@unitypy_define
class ClassInfo:
  m_AssemblyNameIndex: int
  m_ClassName: str
  m_IsUnityClass: bool
  m_MethodIndex: int
  m_NamespaceIndex: int
  m_NumOfMethods: int
  m_NamespaceName: Optional[str] = None


@unitypy_define
class ClassMethodInfo:
  m_ClassIndex: int
  m_MethodName: str
  m_OrderNumber: int


@unitypy_define
class Clip:
  m_DenseClip: DenseClip
  m_StreamedClip: StreamedClip
  m_Binding: Optional[OffsetPtr] = None
  m_ConstantClip: Optional[ConstantClip] = None


@unitypy_define
class ClipAnimationInfo:
  firstFrame: Union[int, float]
  lastFrame: Union[int, float]
  loop: bool
  name: str
  wrapMode: int
  additiveReferencePoseFrame: Optional[float] = None
  bodyMask: Optional[List[int]] = None
  curves: Optional[List[ClipAnimationInfoCurve]] = None
  cycleOffset: Optional[float] = None
  events: Optional[List[AnimationEvent]] = None
  hasAdditiveReferencePose: Optional[bool] = None
  heightFromFeet: Optional[bool] = None
  internalID: Optional[int] = None
  keepAdditionalBonesAnimation: Optional[bool] = None
  keepOriginalOrientation: Optional[bool] = None
  keepOriginalPositionXZ: Optional[bool] = None
  keepOriginalPositionY: Optional[bool] = None
  level: Optional[float] = None
  loopBlend: Optional[bool] = None
  loopBlendOrientation: Optional[bool] = None
  loopBlendPositionXZ: Optional[bool] = None
  loopBlendPositionY: Optional[bool] = None
  loopTime: Optional[bool] = None
  maskSource: Optional[PPtr[AvatarMask]] = None
  maskType: Optional[int] = None
  mirror: Optional[bool] = None
  orientationOffsetY: Optional[float] = None
  skeletonMaskElements: Optional[List[AvatarSkeletonMaskElement]] = None
  takeName: Optional[str] = None
  transformMask: Optional[List[TransformMaskElement]] = None


@unitypy_define
class ClipAnimationInfoCurve:
  curve: AnimationCurve
  name: str


@unitypy_define
class ClipMuscleConstant:
  m_AverageAngularSpeed: float
  m_AverageSpeed: Union[float3, float4]
  m_Clip: OffsetPtr
  m_CycleOffset: float
  m_DeltaPose: HumanPose
  m_HeightFromFeet: bool
  m_IndexArray: List[int]
  m_KeepOriginalOrientation: bool
  m_KeepOriginalPositionXZ: bool
  m_KeepOriginalPositionY: bool
  m_LeftFootStartX: xform
  m_Level: float
  m_LoopBlend: bool
  m_LoopBlendOrientation: bool
  m_LoopBlendPositionXZ: bool
  m_LoopBlendPositionY: bool
  m_Mirror: bool
  m_OrientationOffsetY: float
  m_RightFootStartX: xform
  m_StartTime: float
  m_StartX: xform
  m_StopTime: float
  m_ValueArrayDelta: List[ValueDelta]
  m_AdditionalCurveIndexArray: Optional[List[int]] = None
  m_LoopTime: Optional[bool] = None
  m_MotionStartX: Optional[xform] = None
  m_MotionStopX: Optional[xform] = None
  m_StartAtOrigin: Optional[bool] = None
  m_StopX: Optional[xform] = None
  m_ValueArrayReferencePose: Optional[List[float]] = None


@unitypy_define
class ClothAttachment:
  m_Collider: PPtr[Collider]
  m_Tearable: bool
  m_TwoWayInteraction: bool


@unitypy_define
class ClothConstrainCoefficients:
  collisionSphereDistance: float
  maxDistance: float
  collisionSphereRadius: Optional[float] = None
  maxDistanceBias: Optional[float] = None


@unitypy_define
class ClothSphereColliderPair:
  first: PPtr[SphereCollider]
  second: PPtr[SphereCollider]


@unitypy_define
class ClusterInput:
  m_DeviceName: str
  m_Index: int
  m_Name: str
  m_ServerUrl: str
  m_Type: int


@unitypy_define
class CollabEditorSettings:
  inProgressEnabled: bool


@unitypy_define
class Collision(ABC):
  pass


@unitypy_define
class Collision2D(ABC):
  pass


@unitypy_define
class CollisionModule:
  enabled: bool
  minKillSpeed: float
  type: int
  bounce: Optional[float] = None
  colliderForce: Optional[float] = None
  collidesWith: Optional[BitField] = None
  collidesWithDynamic: Optional[bool] = None
  collisionMessages: Optional[bool] = None
  collisionMode: Optional[int] = None
  dampen: Optional[float] = None
  energyLossOnCollision: Optional[float] = None
  interiorCollisions: Optional[bool] = None
  m_Bounce: Optional[MinMaxCurve] = None
  m_Dampen: Optional[MinMaxCurve] = None
  m_EnergyLossOnCollision: Optional[MinMaxCurve] = None
  m_Planes: Optional[List[PPtr[Transform]]] = None
  maxCollisionShapes: Optional[int] = None
  maxKillSpeed: Optional[float] = None
  multiplyColliderForceByCollisionAngle: Optional[bool] = None
  multiplyColliderForceByParticleSize: Optional[bool] = None
  multiplyColliderForceByParticleSpeed: Optional[bool] = None
  particleRadius: Optional[float] = None
  plane0: Optional[PPtr[Transform]] = None
  plane1: Optional[PPtr[Transform]] = None
  plane2: Optional[PPtr[Transform]] = None
  plane3: Optional[PPtr[Transform]] = None
  plane4: Optional[PPtr[Transform]] = None
  plane5: Optional[PPtr[Transform]] = None
  quality: Optional[int] = None
  radiusScale: Optional[float] = None
  voxelSize: Optional[float] = None


@unitypy_define
class ColorBySpeedModule:
  enabled: bool
  gradient: MinMaxGradient
  range: Vector2f


@unitypy_define
class ColorModule:
  enabled: bool
  gradient: MinMaxGradient


@unitypy_define
class ComponentPair:
  component: PPtr[Component]


@unitypy_define
class CompressedAnimationCurve:
  m_Path: str
  m_PostInfinity: int
  m_PreInfinity: int
  m_Slopes: PackedBitVector
  m_Times: PackedBitVector
  m_Values: PackedBitVector


@unitypy_define
class CompressedMesh:
  m_BoneIndices: PackedBitVector
  m_NormalSigns: PackedBitVector
  m_Normals: PackedBitVector
  m_TangentSigns: PackedBitVector
  m_Tangents: PackedBitVector
  m_Triangles: PackedBitVector
  m_UV: PackedBitVector
  m_Vertices: PackedBitVector
  m_Weights: PackedBitVector
  m_BindPoses: Optional[PackedBitVector] = None
  m_Colors: Optional[PackedBitVector] = None
  m_FloatColors: Optional[PackedBitVector] = None
  m_UVInfo: Optional[int] = None


@unitypy_define
class ComputeBufferCounter:
  bindpoint: int
  offset: int


@unitypy_define
class ComputeShaderBuiltinSampler:
  bindPoint: int
  sampler: int


@unitypy_define
class ComputeShaderCB:
  byteSize: int
  name: Union[FastPropertyName, str]
  params: List[ComputeShaderParam]


@unitypy_define
class ComputeShaderKernel:
  builtinSamplers: List[ComputeShaderBuiltinSampler]
  cbs: List[ComputeShaderResource]
  code: List[int]
  inBuffers: List[ComputeShaderResource]
  outBuffers: List[ComputeShaderResource]
  textures: List[ComputeShaderResource]
  cbVariantIndices: Optional[List[int]] = None
  name: Optional[Union[FastPropertyName, str]] = None
  requirements: Optional[int] = None
  threadGroupSize: Optional[List[int]] = None


@unitypy_define
class ComputeShaderKernelParent:
  name: str
  dynamicKeywords: Optional[List[str]] = None
  globalKeywords: Optional[List[str]] = None
  localKeywords: Optional[List[str]] = None
  uniqueVariants: Optional[List[ComputeShaderKernel]] = None
  validKeywords: Optional[List[str]] = None
  variantIndices: Optional[List[Tuple[str, int]]] = None
  variantMap: Optional[List[Tuple[str, ComputeShaderKernel]]] = None


@unitypy_define
class ComputeShaderParam:
  arraySize: int
  colCount: int
  name: Union[FastPropertyName, str]
  offset: int
  rowCount: int
  type: int


@unitypy_define
class ComputeShaderPlatformVariant:
  constantBuffers: List[ComputeShaderCB]
  kernels: List[ComputeShaderKernelParent]
  resourcesResolved: bool
  targetLevel: int
  targetRenderer: int


@unitypy_define
class ComputeShaderResource:
  bindPoint: int
  name: Union[FastPropertyName, str]
  counter: Optional[ComputeBufferCounter] = None
  generatedName: Optional[Union[FastPropertyName, str]] = None
  samplerBindPoint: Optional[int] = None
  secondaryBindPoint: Optional[int] = None
  texDimension: Optional[int] = None


@unitypy_define
class ComputeShaderVariant:
  constantBuffers: List[ComputeShaderCB]
  kernels: List[ComputeShaderKernel]
  targetLevel: int
  targetRenderer: int
  resourcesResolved: Optional[bool] = None


@unitypy_define
class Condition:
  m_ConditionEvent: str
  m_ConditionMode: int
  m_EventTreshold: float
  m_ExitTime: float


@unitypy_define
class ConditionConstant:
  m_ConditionMode: int
  m_EventID: int
  m_EventThreshold: float
  m_ExitTime: float


@unitypy_define
class ConfigSetting:
  flags: int
  value: str


@unitypy_define
class ConstantBuffer:
  m_MatrixParams: List[MatrixParameter]
  m_NameIndex: int
  m_Size: int
  m_VectorParams: List[VectorParameter]
  m_IsPartialCB: Optional[bool] = None
  m_StructParams: Optional[List[StructParameter]] = None


@unitypy_define
class ConstantClip:
  data: List[float]


@unitypy_define
class ConstraintSource:
  sourceTransform: PPtr[Transform]
  weight: float


@unitypy_define
class ControllerConstant:
  m_DefaultValues: OffsetPtr
  m_StateMachineArray: List[OffsetPtr]
  m_Values: OffsetPtr
  m_HumanLayerArray: Optional[List[OffsetPtr]] = None
  m_LayerArray: Optional[List[OffsetPtr]] = None


@unitypy_define
class CrashReportingSettings:
  m_Enabled: bool
  m_EventUrl: str
  m_LogBufferSize: Optional[int] = None
  m_NativeEventUrl: Optional[str] = None


@unitypy_define
class CustomDataModule:
  color0: MinMaxGradient
  color1: MinMaxGradient
  enabled: bool
  mode0: int
  mode1: int
  vector0_0: MinMaxCurve
  vector0_1: MinMaxCurve
  vector0_2: MinMaxCurve
  vector0_3: MinMaxCurve
  vector1_0: MinMaxCurve
  vector1_1: MinMaxCurve
  vector1_2: MinMaxCurve
  vector1_3: MinMaxCurve
  vectorComponentCount0: int
  vectorComponentCount1: int


@unitypy_define
class DataTemplate(NamedObject):
  m_Father: PPtr[DataTemplate]
  m_IsDataTemplate: bool
  m_LastMergeIdentifier: GUID
  m_Name: str
  m_Objects: List[PPtr[EditorExtension]]


@unitypy_define
class DateTime:
  ticks: int


@unitypy_define
class DefaultPreset:
  m_Preset: PPtr[Preset]
  m_Disabled: Optional[bool] = None
  m_Filter: Optional[str] = None


@unitypy_define
class DefaultPresetList:
  defaultPresets: List[DefaultPreset]
  type: PresetType


@unitypy_define
class DeletedItem:
  changeset: int
  digest: Union[Hash128, MdFour]
  fullPath: str
  guid: GUID
  parent: GUID
  type: int


@unitypy_define
class DenseClip:
  m_BeginTime: float
  m_CurveCount: int
  m_FrameCount: int
  m_SampleArray: List[float]
  m_SampleRate: float


@unitypy_define
class DetailDatabase:
  WavingGrassTint: ColorRGBA
  m_DetailPrototypes: List[DetailPrototype]
  m_PatchCount: int
  m_PatchSamples: int
  m_Patches: List[DetailPatch]
  m_PreloadTextureAtlasData: List[PPtr[Texture2D]]
  m_TreeInstances: List[TreeInstance]
  m_TreePrototypes: List[TreePrototype]
  m_WavingGrassAmount: float
  m_WavingGrassSpeed: float
  m_WavingGrassStrength: float
  m_DefaultShaders_0_: Optional[PPtr[Shader]] = None
  m_DefaultShaders_1_: Optional[PPtr[Shader]] = None
  m_DefaultShaders_2_: Optional[PPtr[Shader]] = None
  m_DetailBillboardShader: Optional[PPtr[Shader]] = None
  m_DetailMeshGrassShader: Optional[PPtr[Shader]] = None
  m_DetailMeshLitShader: Optional[PPtr[Shader]] = None
  m_DetailScatterMode: Optional[int] = None
  m_RandomRotations: Optional[List[Vector3f]] = None


@unitypy_define
class DetailPatch:
  layerIndices: List[int]
  bounds: Optional[AABB] = None
  coverage: Optional[List[int]] = None
  numberOfObjects: Optional[List[int]] = None


@unitypy_define
class DetailPrototype:
  dryColor: ColorRGBA
  healthyColor: ColorRGBA
  maxHeight: float
  maxWidth: float
  minHeight: float
  minWidth: float
  noiseSpread: float
  prototype: PPtr[GameObject]
  prototypeTexture: PPtr[Texture2D]
  renderMode: int
  usePrototypeMesh: int
  alignToGround: Optional[float] = None
  bendFactor: Optional[float] = None
  density: Optional[float] = None
  holeTestRadius: Optional[float] = None
  lightmapFactor: Optional[float] = None
  noiseSeed: Optional[int] = None
  positionJitter: Optional[float] = None
  positionOrderliness: Optional[float] = None
  targetCoverage: Optional[float] = None
  useDensityScaling: Optional[int] = None
  useInstancing: Optional[int] = None


@unitypy_define
class DeviceNone:
  pass


@unitypy_define
class DirectorGenericBinding:
  key: PPtr[Object]
  value: PPtr[Object]


@unitypy_define
class DirectorPlayer(Behaviour):
  m_GameObject: PPtr[GameObject]


@unitypy_define
class EffectConstant:
  bypass: bool
  groupConstantIndex: int
  parameterIndices: List[int]
  prevEffectIndex: int
  sendTargetEffectIndex: int
  type: int
  wetMixLevelIndex: int


@unitypy_define
class EmbeddedNativeType:
  m_FloatArray: List[float]
  m_String: str


@unitypy_define
class EmissionModule:
  enabled: bool
  m_BurstCount: int
  cnt0: Optional[int] = None
  cnt1: Optional[int] = None
  cnt2: Optional[int] = None
  cnt3: Optional[int] = None
  cntmax0: Optional[int] = None
  cntmax1: Optional[int] = None
  cntmax2: Optional[int] = None
  cntmax3: Optional[int] = None
  m_Bursts: Optional[List[ParticleSystemEmissionBurst]] = None
  m_Type: Optional[int] = None
  rate: Optional[MinMaxCurve] = None
  rateOverDistance: Optional[MinMaxCurve] = None
  rateOverTime: Optional[MinMaxCurve] = None
  time0: Optional[float] = None
  time1: Optional[float] = None
  time2: Optional[float] = None
  time3: Optional[float] = None


@unitypy_define
class EnlightenRendererInformation:
  dynamicLightmapSTInSystem: Vector4f
  instanceHash: Hash128
  renderer: PPtr[Object]
  systemId: int


@unitypy_define
class EnlightenSceneMapping:
  m_Renderers: List[EnlightenRendererInformation]
  m_SystemAtlases: List[EnlightenSystemAtlasInformation]
  m_Systems: List[EnlightenSystemInformation]
  m_TerrainChunks: List[EnlightenTerrainChunksInformation]
  m_Probesets: Optional[List[Hash128]] = None


@unitypy_define
class EnlightenSystemAtlasInformation:
  atlasHash: Hash128
  atlasSize: int
  firstSystemId: int


@unitypy_define
class EnlightenSystemInformation:
  atlasIndex: int
  atlasOffsetX: int
  atlasOffsetY: int
  inputSystemHash: Hash128
  radiositySystemHash: Hash128
  rendererIndex: int
  rendererSize: int


@unitypy_define
class EnlightenTerrainChunksInformation:
  firstSystemId: int
  numChunksInX: int
  numChunksInY: int


@unitypy_define
class ExpandedData:
  m_ClassID: int
  m_ExpandedProperties: List[str]
  m_InspectorExpanded: bool
  m_ScriptClass: str


@unitypy_define
class ExposedReferenceTable:
  m_References: List[Tuple[str, PPtr[Object]]]


@unitypy_define
class Expression:
  data_0_: int
  data_1_: int
  data_2_: int
  data_3_: int
  op: int
  valueIndex: int


@unitypy_define
class ExtensionPropertyValue:
  extensionName: str
  pluginName: str
  propertyName: str
  propertyValue: float


@unitypy_define
class ExternalForcesModule:
  enabled: bool
  influenceFilter: Optional[int] = None
  influenceList: Optional[List[PPtr[ParticleSystemForceField]]] = None
  influenceMask: Optional[BitField] = None
  multiplier: Optional[float] = None
  multiplierCurve: Optional[MinMaxCurve] = None


@unitypy_define
class FalloffTable:
  m_Table_0_: float
  m_Table_10_: float
  m_Table_11_: float
  m_Table_12_: float
  m_Table_1_: float
  m_Table_2_: float
  m_Table_3_: float
  m_Table_4_: float
  m_Table_5_: float
  m_Table_6_: float
  m_Table_7_: float
  m_Table_8_: float
  m_Table_9_: float


@unitypy_define
class FastPropertyName:
  name: str


@unitypy_define
class FlareElement:
  m_Color: ColorRGBA
  m_Fade: bool
  m_ImageIndex: int
  m_Position: float
  m_Rotate: bool
  m_Size: float
  m_UseLightColor: bool
  m_Zoom: bool


@unitypy_define
class FloatCurve:
  attribute: str
  classID: int
  curve: AnimationCurve
  path: str
  script: PPtr[MonoScript]
  flags: Optional[int] = None


@unitypy_define
class ForceModule:
  enabled: bool
  inWorldSpace: bool
  randomizePerFrame: bool
  x: MinMaxCurve
  y: MinMaxCurve
  z: MinMaxCurve


@unitypy_define
class GISettings:
  m_AlbedoBoost: float
  m_BounceScale: float
  m_EnableBakedLightmaps: bool
  m_EnableRealtimeLightmaps: bool
  m_EnvironmentLightingMode: int
  m_IndirectOutputScale: float
  m_TemporalCoherenceThreshold: Optional[float] = None


@unitypy_define
class GLTextureSettings:
  m_Aniso: int
  m_FilterMode: int
  m_MipBias: float
  m_WrapMode: Optional[int] = None
  m_WrapU: Optional[int] = None
  m_WrapV: Optional[int] = None
  m_WrapW: Optional[int] = None


@unitypy_define
class GUID:
  data_0_: int
  data_1_: int
  data_2_: int
  data_3_: int


@unitypy_define
class GenericBinding:
  attribute: int
  customType: int
  isPPtrCurve: int
  path: int
  script: PPtr[Object]
  classID: Optional[int] = None
  isIntCurve: Optional[int] = None
  isSerializeReferenceCurve: Optional[int] = None
  typeID: Optional[int] = None


@unitypy_define
class GfxBlendState:
  alphaToMask: int
  rt: List[GfxRenderTargetBlendState]
  separateMRTBlend: int


@unitypy_define
class GfxDepthState:
  depthFunc: int
  depthWrite: int


@unitypy_define
class GfxRasterState:
  conservative: int
  cullMode: int
  depthBias: int
  depthClip: int
  slopeScaledDepthBias: float


@unitypy_define
class GfxRenderTargetBlendState:
  blendOp: int
  blendOpAlpha: int
  dstBlend: int
  dstBlendAlpha: int
  srcBlend: int
  srcBlendAlpha: int
  writeMask: int


@unitypy_define
class GfxStencilState:
  padding: int
  readMask: int
  stencilEnable: int
  stencilFailOpBack: int
  stencilFailOpFront: int
  stencilFuncBack: int
  stencilFuncFront: int
  stencilPassOpBack: int
  stencilPassOpFront: int
  stencilZFailOpBack: int
  stencilZFailOpFront: int
  writeMask: int


@unitypy_define
class Google:
  depthFormat: int
  enableTransitionView: Optional[bool] = None
  enableVideoLayer: Optional[bool] = None
  maximumSupportedHeadTracking: Optional[int] = None
  minimumSupportedHeadTracking: Optional[int] = None
  useProtectedVideoMemory: Optional[bool] = None
  useSustainedPerformanceMode: Optional[bool] = None


@unitypy_define
class Gradient:
  atime0: Optional[int] = None
  atime1: Optional[int] = None
  atime2: Optional[int] = None
  atime3: Optional[int] = None
  atime4: Optional[int] = None
  atime5: Optional[int] = None
  atime6: Optional[int] = None
  atime7: Optional[int] = None
  ctime0: Optional[int] = None
  ctime1: Optional[int] = None
  ctime2: Optional[int] = None
  ctime3: Optional[int] = None
  ctime4: Optional[int] = None
  ctime5: Optional[int] = None
  ctime6: Optional[int] = None
  ctime7: Optional[int] = None
  key0: Optional[ColorRGBA] = None
  key1: Optional[ColorRGBA] = None
  key2: Optional[ColorRGBA] = None
  key3: Optional[ColorRGBA] = None
  key4: Optional[ColorRGBA] = None
  key5: Optional[ColorRGBA] = None
  key6: Optional[ColorRGBA] = None
  key7: Optional[ColorRGBA] = None
  m_ColorSpace: Optional[int] = None
  m_Color_0_: Optional[ColorRGBA] = None
  m_Color_1_: Optional[ColorRGBA] = None
  m_Color_2_: Optional[ColorRGBA] = None
  m_Color_3_: Optional[ColorRGBA] = None
  m_Color_4_: Optional[ColorRGBA] = None
  m_Mode: Optional[int] = None
  m_NumAlphaKeys: Optional[int] = None
  m_NumColorKeys: Optional[int] = None


@unitypy_define
class GradientNEW:
  atime0: int
  atime1: int
  atime2: int
  atime3: int
  atime4: int
  atime5: int
  atime6: int
  atime7: int
  ctime0: int
  ctime1: int
  ctime2: int
  ctime3: int
  ctime4: int
  ctime5: int
  ctime6: int
  ctime7: int
  key0: ColorRGBA
  key1: ColorRGBA
  key2: ColorRGBA
  key3: ColorRGBA
  key4: ColorRGBA
  key5: ColorRGBA
  key6: ColorRGBA
  key7: ColorRGBA
  m_NumAlphaKeys: int
  m_NumColorKeys: int


@unitypy_define
class GraphicsStateInfo:
  appBackface: bool
  depthBias: float
  forceCullMode: int
  invertProjectionMatrix: bool
  renderPass: int
  renderState: int
  slopeDepthBias: float
  subPassIndex: int
  topology: int
  userBackface: bool
  vertexLayout: int
  wireframe: bool


@unitypy_define
class GroupConnection:
  sendEffectIndex: int
  sourceGroupIndex: int
  targetGroupIndex: int


@unitypy_define
class GroupConstant:
  bypassEffects: bool
  mute: bool
  parentConstantIndex: int
  pitchIndex: int
  solo: bool
  volumeIndex: int
  sendIndex: Optional[int] = None


@unitypy_define
class Hand:
  m_HandBoneIndex: List[int]


@unitypy_define
class HandPose:
  m_CloseOpen: float
  m_DoFArray: List[float]
  m_Grab: float
  m_GrabX: xform
  m_InOut: float
  m_Override: float


@unitypy_define
class Handle:
  m_ID: int
  m_ParentHumanIndex: int
  m_X: xform


@unitypy_define
class Hash128:
  bytes_0_: int
  bytes_10_: int
  bytes_11_: int
  bytes_12_: int
  bytes_13_: int
  bytes_14_: int
  bytes_15_: int
  bytes_1_: int
  bytes_2_: int
  bytes_3_: int
  bytes_4_: int
  bytes_5_: int
  bytes_6_: int
  bytes_7_: int
  bytes_8_: int
  bytes_9_: int


@unitypy_define
class HeightMeshBVNode:
  i: int
  max: Vector3f
  min: Vector3f
  n: int


@unitypy_define
class HeightMeshData:
  m_Bounds: AABB
  m_Indices: List[int]
  m_Nodes: List[HeightMeshBVNode]
  m_Vertices: List[Vector3f]


@unitypy_define
class Heightmap:
  m_Heights: List[int]
  m_Levels: int
  m_MinMaxPatchHeights: List[float]
  m_PrecomputedError: List[float]
  m_Scale: Vector3f
  m_DefaultPhysicMaterial: Optional[PPtr[PhysicMaterial]] = None
  m_EnableHolesTextureCompression: Optional[bool] = None
  m_EnableSurfaceMaskTextureCompression: Optional[bool] = None
  m_Height: Optional[int] = None
  m_Holes: Optional[List[int]] = None
  m_HolesLOD: Optional[List[int]] = None
  m_Resolution: Optional[int] = None
  m_SurfaceMask: Optional[List[int]] = None
  m_SurfaceMaskLOD: Optional[List[int]] = None
  m_Thickness: Optional[float] = None
  m_Width: Optional[int] = None


@unitypy_define
class HeightmapData:
  terrainData: PPtr[Object]
  isRotated: Optional[bool] = None
  position: Optional[Vector3f] = None
  surfaceToTerrain: Optional[Matrix4x4f] = None


@unitypy_define
class HierarchicalSceneData:
  m_SceneGUID: GUID


@unitypy_define
class HoloLens:
  depthFormat: int
  depthBufferSharingEnabled: Optional[bool] = None


@unitypy_define
class Human:
  m_ArmStretch: float
  m_ArmTwist: float
  m_FeetSpacing: float
  m_ForeArmTwist: float
  m_HasLeftHand: bool
  m_HasRightHand: bool
  m_HumanBoneIndex: List[int]
  m_HumanBoneMass: List[float]
  m_LeftHand: OffsetPtr
  m_LegStretch: float
  m_LegTwist: float
  m_RightHand: OffsetPtr
  m_RootX: xform
  m_Scale: float
  m_Skeleton: OffsetPtr
  m_SkeletonPose: OffsetPtr
  m_UpperLegTwist: float
  m_ColliderArray: Optional[List[Collider]] = None
  m_ColliderIndex: Optional[List[int]] = None
  m_Handles: Optional[List[Handle]] = None
  m_HasTDoF: Optional[bool] = None


@unitypy_define
class HumanBone:
  m_BoneName: str
  m_HumanName: str
  m_Limit: SkeletonBoneLimit


@unitypy_define
class HumanDescription:
  m_ArmStretch: float
  m_ArmTwist: float
  m_FeetSpacing: float
  m_ForeArmTwist: float
  m_Human: List[HumanBone]
  m_LegStretch: float
  m_LegTwist: float
  m_RootMotionBoneName: str
  m_Skeleton: List[SkeletonBone]
  m_UpperLegTwist: float
  m_GlobalScale: Optional[float] = None
  m_Handles: Optional[List[HumanHandle]] = None
  m_HasExtraRoot: Optional[bool] = None
  m_HasTranslationDoF: Optional[bool] = None
  m_RootMotionBoneRotation: Optional[Quaternionf] = None
  m_SkeletonHasParents: Optional[bool] = None


@unitypy_define
class HumanGoal:
  m_WeightR: float
  m_WeightT: float
  m_X: xform
  m_HintT: Optional[Union[float3, float4]] = None
  m_HintWeightT: Optional[float] = None


@unitypy_define
class HumanHandle:
  m_BoneName: str
  m_LookAt: bool
  m_Name: str
  m_Position: Vector3f
  m_Rotation: Quaternionf
  m_Scale: Vector3f


@unitypy_define
class HumanLayerConstant:
  m_Binding: int
  m_BodyMask: HumanPoseMask
  m_IKPass: bool
  m_LayerBlendingMode: int
  m_SkeletonMask: OffsetPtr
  m_StateMachineIndex: int
  m_StateMachineMotionSetIndex: int
  m_DefaultWeight: Optional[float] = None
  m_SyncedLayerAffectsTiming: Optional[bool] = None


@unitypy_define
class HumanPose:
  m_DoFArray: List[float]
  m_GoalArray: List[HumanGoal]
  m_LeftHandPose: HandPose
  m_LookAtPosition: Union[float3, float4]
  m_LookAtWeight: float4
  m_RightHandPose: HandPose
  m_RootX: xform
  m_TDoFArray: Optional[Union[List[float4], List[float3]]] = None


@unitypy_define
class HumanPoseMask:
  word0: int
  word1: int
  word2: Optional[int] = None


@unitypy_define
class Image:
  image_data: bytes
  m_Format: int
  m_Height: int
  m_RowBytes: int
  m_Width: int


@unitypy_define
class ImportLog_ImportLogEntry:
  file: str
  line: int
  message: str
  mode: int
  object: PPtr[Object]


@unitypy_define
class InheritVelocityModule:
  enabled: bool
  m_Curve: MinMaxCurve
  m_Mode: int


@unitypy_define
class InitialModule:
  enabled: bool
  gravityModifier: Union[MinMaxCurve, float]
  maxNumParticles: int
  startColor: MinMaxGradient
  startLifetime: MinMaxCurve
  startRotation: MinMaxCurve
  startSize: MinMaxCurve
  startSpeed: MinMaxCurve
  customEmitterVelocity: Optional[Vector3f] = None
  gravitySource: Optional[int] = None
  inheritVelocity: Optional[float] = None
  randomizeRotationDirection: Optional[float] = None
  rotation3D: Optional[bool] = None
  size3D: Optional[bool] = None
  startRotationX: Optional[MinMaxCurve] = None
  startRotationY: Optional[MinMaxCurve] = None
  startSizeY: Optional[MinMaxCurve] = None
  startSizeZ: Optional[MinMaxCurve] = None


@unitypy_define
class InputAxis:
  altNegativeButton: str
  altPositiveButton: str
  axis: int
  dead: float
  descriptiveName: str
  descriptiveNegativeName: str
  gravity: float
  invert: bool
  joyNum: int
  m_Name: str
  negativeButton: str
  positiveButton: str
  sensitivity: float
  snap: bool
  type: int


@unitypy_define
class InputImportSettings:
  name: str
  alphaSource: Optional[int] = None
  aniso: Optional[int] = None
  filterMode: Optional[int] = None
  value: Optional[SubstanceValue] = None
  wrapMode: Optional[int] = None


@unitypy_define
class IntPoint:
  X: int
  Y: int


@unitypy_define
class Item:
  changeFlags: Optional[int] = None
  changeset: Optional[int] = None
  digest: Optional[Union[Hash128, MdFour]] = None
  downloadResolution: Optional[int] = None
  guid: Optional[GUID] = None
  markedForRemoval: Optional[bool] = None
  name: Optional[str] = None
  nameConflictResolution: Optional[int] = None
  oldVersion: Optional[int] = None
  origin: Optional[int] = None
  parent: Optional[GUID] = None
  parentFolderID: Optional[int] = None
  type: Optional[int] = None


@unitypy_define
class JointAngleLimit2D:
  m_LowerAngle: float
  m_UpperAngle: float


@unitypy_define
class JointAngleLimits2D:
  m_LowerAngle: float
  m_UpperAngle: float


@unitypy_define
class JointDrive:
  maximumForce: float
  positionDamper: float
  positionSpring: float
  mode: Optional[int] = None
  useAcceleration: Optional[int] = None


@unitypy_define
class JointLimits:
  max: float
  min: float
  bounceMinVelocity: Optional[float] = None
  bounciness: Optional[float] = None
  contactDistance: Optional[float] = None
  maxBounce: Optional[float] = None
  minBounce: Optional[float] = None


@unitypy_define
class JointMotor:
  force: float
  freeSpin: int
  targetVelocity: float


@unitypy_define
class JointMotor2D:
  m_MaximumMotorForce: float
  m_MotorSpeed: float


@unitypy_define
class JointSpring:
  damper: float
  spring: float
  targetPosition: float


@unitypy_define
class JointSuspension2D:
  m_Angle: float
  m_DampingRatio: float
  m_Frequency: float


@unitypy_define
class JointTranslationLimits2D:
  m_LowerTranslation: float
  m_UpperTranslation: float


@unitypy_define
class Keyframe:
  inSlope: Union[Quaternionf, float, Vector3f]
  outSlope: Union[Quaternionf, float, Vector3f]
  time: float
  value: Union[Quaternionf, float, Vector3f]
  inWeight: Optional[Union[Quaternionf, float, Vector3f]] = None
  outWeight: Optional[Union[Quaternionf, float, Vector3f]] = None
  weightedMode: Optional[int] = None


@unitypy_define
class LOD:
  renderers: List[LODRenderer]
  screenRelativeHeight: float
  fadeMode: Optional[int] = None
  fadeTransitionWidth: Optional[float] = None


@unitypy_define
class LODRenderer:
  renderer: PPtr[Renderer]


@unitypy_define
class LayerConstant:
  m_Binding: int
  m_BodyMask: HumanPoseMask
  m_DefaultWeight: float
  m_IKPass: bool
  m_LayerBlendingMode: int
  m_SkeletonMask: OffsetPtr
  m_StateMachineIndex: int
  m_SyncedLayerAffectsTiming: bool
  m_StateMachineMotionSetIndex: Optional[int] = None
  m_StateMachineSynchronizedLayerIndex: Optional[int] = None


@unitypy_define
class LayoutDataOne:
  m_FloatArray: List[float]


@unitypy_define
class LayoutDataThree:
  m_AnotherFloatArray: List[float]


@unitypy_define
class LayoutDataTwo:
  m_FloatValue: float
  m_IntegerValue: int


@unitypy_define
class LeafInfoConstant:
  m_IDArray: List[int]
  m_IndexOffset: int


@unitypy_define
class LibraryRepresentation:
  name: str
  scriptClassName: str
  thumbnail: Image
  thumbnailClassID: int
  flags: Optional[int] = None
  guid: Optional[GUID] = None
  localIdentifier: Optional[int] = None
  object: Optional[Union[PPtr[EditorExtension], PPtr[Object]]] = None
  path: Optional[str] = None


@unitypy_define
class LifetimeByEmitterSpeedModule:
  enabled: bool
  m_Curve: MinMaxCurve
  m_Range: Vector2f


@unitypy_define
class LightBakingOutput:
  probeOcclusionLightIndex: int
  isBaked: Optional[bool] = None
  lightmapBakeMode: Optional[LightmapBakeMode] = None
  lightmappingMask: Optional[int] = None
  occlusionMaskChannel: Optional[int] = None
  shadowMaskChannel: Optional[int] = None


@unitypy_define
class LightProbeData:
  m_NonTetrahedralizedProbeSetIndexMap: List[Tuple[Hash128, int]]
  m_Positions: List[Vector3f]
  m_ProbeSets: List[ProbeSetIndex]
  m_Tetrahedralization: ProbeSetTetrahedralization


@unitypy_define
class LightProbeOcclusion:
  m_Occlusion: List[float]
  m_BakedLightIndex: Optional[List[int]] = None
  m_OcclusionMaskChannel: Optional[List[int]] = None
  m_ProbeOcclusionLightIndex: Optional[List[int]] = None
  m_ShadowMaskChannel: Optional[List[int]] = None


@unitypy_define
class LightmapBakeMode:
  lightmapBakeType: int
  mixedLightingMode: int


@unitypy_define
class LightmapData:
  m_DirLightmap: Optional[PPtr[Texture2D]] = None
  m_IndirectLightmap: Optional[PPtr[Texture2D]] = None
  m_Lightmap: Optional[PPtr[Texture2D]] = None
  m_ShadowMask: Optional[PPtr[Texture2D]] = None
  sh_0_: Optional[float] = None
  sh_10_: Optional[float] = None
  sh_11_: Optional[float] = None
  sh_12_: Optional[float] = None
  sh_13_: Optional[float] = None
  sh_14_: Optional[float] = None
  sh_15_: Optional[float] = None
  sh_16_: Optional[float] = None
  sh_17_: Optional[float] = None
  sh_18_: Optional[float] = None
  sh_19_: Optional[float] = None
  sh_1_: Optional[float] = None
  sh_20_: Optional[float] = None
  sh_21_: Optional[float] = None
  sh_22_: Optional[float] = None
  sh_23_: Optional[float] = None
  sh_24_: Optional[float] = None
  sh_25_: Optional[float] = None
  sh_26_: Optional[float] = None
  sh_2_: Optional[float] = None
  sh_3_: Optional[float] = None
  sh_4_: Optional[float] = None
  sh_5_: Optional[float] = None
  sh_6_: Optional[float] = None
  sh_7_: Optional[float] = None
  sh_8_: Optional[float] = None
  sh_9_: Optional[float] = None


@unitypy_define
class LightmapSnapshot(NamedObject):
  m_BakedReflectionProbeCubemaps: List[PPtr[Texture]]
  m_BakedReflectionProbes: List[SceneObjectIdentifier]
  m_EnlightenData: List[int]
  m_EnlightenSceneMapping: EnlightenSceneMapping
  m_EnlightenSceneMappingRendererIDs: List[SceneObjectIdentifier]
  m_LightProbes: PPtr[LightProbes]
  m_LightmappedRendererData: List[RendererData]
  m_LightmappedRendererDataIDs: List[SceneObjectIdentifier]
  m_Lightmaps: List[LightmapData]
  m_Lights: List[SceneObjectIdentifier]
  m_Name: str
  m_BakedAmbientProbeInGamma: Optional[SphericalHarmonicsL2] = None
  m_BakedAmbientProbeInLinear: Optional[SphericalHarmonicsL2] = None
  m_BakedAmbientProbesInGamma: Optional[List[SphericalHarmonicsL2]] = None
  m_BakedAmbientProbesInLinear: Optional[List[SphericalHarmonicsL2]] = None
  m_BakedSkyboxProbeCubemaps: Optional[List[PPtr[Texture]]] = None
  m_SceneGUID: Optional[GUID] = None


@unitypy_define
class LightsModule:
  color: bool
  enabled: bool
  intensity: bool
  intensityCurve: MinMaxCurve
  light: PPtr[Light]
  maxLights: int
  randomDistribution: bool
  range: bool
  rangeCurve: MinMaxCurve
  ratio: float


@unitypy_define
class Limit:
  m_Max: Union[float3, float4]
  m_Min: Union[float3, float4]


@unitypy_define
class LineParameters:
  alignment: Optional[int] = None
  colorGradient: Optional[Gradient] = None
  endWidth: Optional[float] = None
  generateLightingData: Optional[bool] = None
  m_EndColor: Optional[ColorRGBA] = None
  m_StartColor: Optional[ColorRGBA] = None
  numCapVertices: Optional[int] = None
  numCornerVertices: Optional[int] = None
  shadowBias: Optional[float] = None
  startWidth: Optional[float] = None
  textureMode: Optional[int] = None
  textureScale: Optional[Vector2f] = None
  widthCurve: Optional[AnimationCurve] = None
  widthMultiplier: Optional[float] = None


@unitypy_define
class Lumin:
  depthFormat: int
  enableGLCache: bool
  frameTiming: int
  glCacheMaxBlobSize: int
  glCacheMaxFileSize: int


@unitypy_define
class MaterialImportOutput:
  baked: int
  currentSettings: BuildTargetSettings


@unitypy_define
class MaterialInstanceSettings:
  buildTargetSettings: List[BuildTargetSettings]
  inputs: List[InputImportSettings]
  materialInformation: ProceduralMaterialInformation
  materialProperties: UnityPropertySheet
  name: str
  prototypeName: str
  textureParameters: List[InputImportSettings]
  lightmapFlags: Optional[int] = None
  renderQueue: Optional[int] = None
  shader: Optional[PPtr[Shader]] = None
  shaderKeywords: Optional[str] = None
  shaderName: Optional[str] = None
  textureAssignments: Optional[List[ProceduralTextureAssignment]] = None


@unitypy_define
class MatrixParameter:
  m_ArraySize: int
  m_Index: int
  m_NameIndex: int
  m_RowCount: int
  m_Type: int


@unitypy_define
class MdFour:
  md4_hash: bytes


@unitypy_define
class MeshBlendShape:
  firstVertex: int
  hasNormals: bool
  hasTangents: bool
  vertexCount: int
  aabbMaxDelta: Optional[Vector3f] = None
  aabbMinDelta: Optional[Vector3f] = None
  name: Optional[str] = None


@unitypy_define
class MeshBlendShapeChannel:
  frameCount: int
  frameIndex: int
  name: str
  nameHash: int


@unitypy_define
class MeshBlendShapeVertex:
  index: int
  normal: Vector3f
  tangent: Vector3f
  vertex: Vector3f


@unitypy_define
class MinMaxAABB:
  m_Max: Vector3f
  m_Min: Vector3f


@unitypy_define
class MinMaxCurve:
  maxCurve: AnimationCurve
  minCurve: AnimationCurve
  minMaxState: int
  scalar: float
  minScalar: Optional[float] = None


@unitypy_define
class MinMaxGradient:
  maxColor: ColorRGBA
  maxGradient: Union[GradientNEW, Gradient]
  minColor: ColorRGBA
  minGradient: Union[GradientNEW, Gradient]
  minMaxState: int


@unitypy_define
class MipmapLimitSettings:
  limitBias: int
  limitBiasMode: int


@unitypy_define
class Module:
  dependencies: List[str]
  name: str
  strippable: bool
  controlledByBuiltinPackage: Optional[bool] = None


@unitypy_define
class MonoAssemblyImporter(AssetImporter):
  m_ExecutionOrder: List[Tuple[str, int]]
  m_IconMap: List[Tuple[str, PPtr[Texture2D]]]
  m_Name: str
  m_FileIDToRecycleName: Optional[List[Tuple[int, str]]] = None
  m_NewHashIdentity: Optional[MdFour] = None
  m_OldHashIdentity: Optional[MdFour] = None
  m_UserData: Optional[str] = None


@unitypy_define
class MonoObject(ABC):
  pass


@unitypy_define
class MotionNeighborList:
  m_NeighborArray: List[int]


@unitypy_define
class MultiModeParameter:
  mode: int
  speed: MinMaxCurve
  spread: float
  value: Optional[float] = None


@unitypy_define
class NameToObjectMap:
  m_ObjectToName: List[Tuple[PPtr[Shader], str]]


@unitypy_define
class NativeType:
  a: int
  b: float
  embedded: EmbeddedNativeType


@unitypy_define
class NavMesh(NamedObject):
  m_Heightmaps: List[HeightmapData]
  m_MeshData: List[int]
  m_Name: str


@unitypy_define
class NavMeshAreaData:
  cost: float
  name: str


@unitypy_define
class NavMeshAreas(GlobalGameManager):
  areas: List[NavMeshAreaData]


@unitypy_define
class NavMeshBuildDebugSettings:
  m_Flags: int


@unitypy_define
class NavMeshBuildSettings:
  agentClimb: float
  agentHeight: float
  agentRadius: float
  agentSlope: float
  agentTypeID: int
  cellSize: float
  ledgeDropHeight: float
  manualCellSize: Union[bool, int]
  manualTileSize: Union[bool, int]
  maxJumpAcrossDistance: float
  minRegionArea: float
  tileSize: int
  accuratePlacement: Optional[Union[bool, int]] = None
  buildHeightMesh: Optional[int] = None
  debug: Optional[NavMeshBuildDebugSettings] = None
  keepTiles: Optional[int] = None
  maxJobWorkers: Optional[int] = None
  preserveTilesOutsideBounds: Optional[int] = None


@unitypy_define
class NavMeshLayerData:
  cost: float
  editType: int
  name: str


@unitypy_define
class NavMeshLayers(GlobalGameManager):
  Built_in_Layer_0: NavMeshLayerData
  Built_in_Layer_1: NavMeshLayerData
  Built_in_Layer_2: NavMeshLayerData
  User_Layer_0: NavMeshLayerData
  User_Layer_1: NavMeshLayerData
  User_Layer_10: NavMeshLayerData
  User_Layer_11: NavMeshLayerData
  User_Layer_12: NavMeshLayerData
  User_Layer_13: NavMeshLayerData
  User_Layer_14: NavMeshLayerData
  User_Layer_15: NavMeshLayerData
  User_Layer_16: NavMeshLayerData
  User_Layer_17: NavMeshLayerData
  User_Layer_18: NavMeshLayerData
  User_Layer_19: NavMeshLayerData
  User_Layer_2: NavMeshLayerData
  User_Layer_20: NavMeshLayerData
  User_Layer_21: NavMeshLayerData
  User_Layer_22: NavMeshLayerData
  User_Layer_23: NavMeshLayerData
  User_Layer_24: NavMeshLayerData
  User_Layer_25: NavMeshLayerData
  User_Layer_26: NavMeshLayerData
  User_Layer_27: NavMeshLayerData
  User_Layer_28: NavMeshLayerData
  User_Layer_3: NavMeshLayerData
  User_Layer_4: NavMeshLayerData
  User_Layer_5: NavMeshLayerData
  User_Layer_6: NavMeshLayerData
  User_Layer_7: NavMeshLayerData
  User_Layer_8: NavMeshLayerData
  User_Layer_9: NavMeshLayerData


@unitypy_define
class NavMeshParams:
  cellSize: float
  tileSize: float
  walkableClimb: float
  walkableHeight: float
  walkableRadius: float


@unitypy_define
class NavMeshTileData:
  m_MeshData: List[int]
  m_Hash: Optional[Hash128] = None


@unitypy_define
class NetworkViewID:
  m_ID: int
  m_Type: int


@unitypy_define
class Node:
  m_AxesId: int
  m_ParentId: int


@unitypy_define
class NoiseModule:
  damping: bool
  enabled: bool
  frequency: float
  octaveMultiplier: float
  octaveScale: float
  octaves: int
  quality: int
  remap: MinMaxCurve
  remapEnabled: bool
  remapY: MinMaxCurve
  remapZ: MinMaxCurve
  scrollSpeed: MinMaxCurve
  separateAxes: bool
  strength: MinMaxCurve
  strengthY: MinMaxCurve
  strengthZ: MinMaxCurve
  positionAmount: Optional[MinMaxCurve] = None
  rotationAmount: Optional[MinMaxCurve] = None
  sizeAmount: Optional[MinMaxCurve] = None


@unitypy_define
class NonAlignedStruct:
  m_Bool: bool


@unitypy_define
class ObjectRolePair:
  m_Object: PPtr[Object]
  m_RolesMask: int


@unitypy_define
class OcclusionScene:
  indexPortals: int
  indexRenderers: int
  scene: GUID
  sizePortals: int
  sizeRenderers: int


@unitypy_define
class Oculus:
  dashSupport: bool
  sharedDepthBuffer: bool
  lowOverheadMode: Optional[bool] = None
  protectedContext: Optional[bool] = None
  v2Signing: Optional[bool] = None


@unitypy_define
class OffsetPtr:
  data: Union[
    SkeletonMask,
    SkeletonPose,
    Blend2dDataConstant,
    Blend1dDataConstant,
    BlendTreeConstant,
    Skeleton,
    Clip,
    SelectorTransitionConstant,
    LayerConstant,
    ValueArray,
    SelectorStateConstant,
    ConditionConstant,
    Human,
    HumanLayerConstant,
    Hand,
    StateConstant,
    StateMachineConstant,
    BlendTreeNodeConstant,
    BlendDirectDataConstant,
    ValueArrayConstant,
    TransitionConstant,
  ]


@unitypy_define
class Output:
  hasEmptyFontData: Optional[bool] = None
  importedType: Optional[int] = None
  previewData: Optional[List[float]] = None


@unitypy_define
class PPtrCurve:
  attribute: str
  classID: int
  curve: List[PPtrKeyframe]
  path: str
  script: PPtr[MonoScript]
  flags: Optional[int] = None


@unitypy_define
class PPtrKeyframe:
  time: float
  value: PPtr[Object]


@unitypy_define
class PackedBitVector:
  m_Data: List[int]
  m_NumItems: int
  m_BitSize: Optional[int] = None
  m_Range: Optional[float] = None
  m_Start: Optional[float] = None


@unitypy_define
class PackingSettings:
  allowAlphaSplitting: bool
  blockOffset: int
  enableRotation: bool
  enableTightPacking: bool
  padding: int
  enableAlphaDilation: Optional[bool] = None


@unitypy_define
class Parameter:
  m_GUID: GUID
  m_ParameterName: str


@unitypy_define
class ParserBindChannels:
  m_Channels: List[ShaderBindChannel]
  m_SourceMap: int


@unitypy_define
class ParticleSystemEmissionBurst:
  cycleCount: int
  repeatInterval: float
  time: float
  countCurve: Optional[MinMaxCurve] = None
  maxCount: Optional[int] = None
  minCount: Optional[int] = None
  probability: Optional[float] = None


@unitypy_define
class ParticleSystemForceFieldParameters:
  m_DirectionCurveX: MinMaxCurve
  m_DirectionCurveY: MinMaxCurve
  m_DirectionCurveZ: MinMaxCurve
  m_DragCurve: MinMaxCurve
  m_EndRange: float
  m_GravityCurve: MinMaxCurve
  m_GravityFocus: float
  m_Length: float
  m_MultiplyDragByParticleSize: bool
  m_MultiplyDragByParticleVelocity: bool
  m_RotationAttractionCurve: MinMaxCurve
  m_RotationRandomness: Vector2f
  m_RotationSpeedCurve: MinMaxCurve
  m_Shape: int
  m_StartRange: float
  m_VectorField: PPtr[Texture3D]
  m_VectorFieldAttractionCurve: MinMaxCurve
  m_VectorFieldSpeedCurve: MinMaxCurve


@unitypy_define
class PerLODSettings:
  castShadows: bool
  enableBump: bool
  enableHue: bool
  height: float
  receiveShadows: bool
  reflectionProbeUsage: int
  useLightProbes: bool
  windQuality: int
  enableSettingOverride: Optional[bool] = None
  enableSubsurface: Optional[bool] = None


@unitypy_define
class PerformanceReportingSettings:
  m_Enabled: bool


@unitypy_define
class PhysicMaterial(NamedObject):
  bounceCombine: int
  bounciness: float
  dynamicFriction: float
  frictionCombine: int
  m_Name: str
  staticFriction: float
  dynamicFriction2: Optional[float] = None
  frictionDirection2: Optional[Vector3f] = None
  staticFriction2: Optional[float] = None


@unitypy_define
class PhysicsJobOptions2D:
  m_ClearBodyForcesPerJob: int
  m_ClearFlagsPerJob: int
  m_CollideContactsPerJob: int
  m_FindNearestContactsPerJob: int
  m_InterpolationPosesPerJob: int
  m_IslandSolverBodiesPerJob: int
  m_IslandSolverBodyCostScale: int
  m_IslandSolverContactCostScale: int
  m_IslandSolverContactsPerJob: int
  m_IslandSolverCostThreshold: int
  m_IslandSolverJointCostScale: int
  m_NewContactsPerJob: int
  m_SyncContinuousFixturesPerJob: int
  m_SyncDiscreteFixturesPerJob: int
  m_UpdateTriggerContactsPerJob: int
  m_UseConsistencySorting: Optional[bool] = None
  m_UseMultithreading: Optional[bool] = None
  useConsistencySorting: Optional[bool] = None
  useMultithreading: Optional[bool] = None


@unitypy_define
class PhysicsShape:
  m_AdjacentEnd: Vector2f
  m_AdjacentStart: Vector2f
  m_Radius: float
  m_ShapeType: int
  m_UseAdjacentEnd: int
  m_UseAdjacentStart: int
  m_VertexCount: int
  m_VertexStartIndex: int


@unitypy_define
class PhysicsShapeGroup2D:
  m_Shapes: List[PhysicsShape]
  m_Vertices: List[Vector2f]


@unitypy_define
class PlatformSettings:
  m_AllowsAlphaSplitting: bool
  m_BuildTarget: str
  m_CompressionQuality: int
  m_CrunchedCompression: bool
  m_MaxTextureSize: int
  m_Overridden: bool
  m_TextureCompression: int
  m_TextureFormat: int
  m_ResizeAlgorithm: Optional[int] = None


@unitypy_define
class PlatformSettingsData:
  settings: List[Tuple[str, str]]
  enabled: Optional[bool] = None


@unitypy_define
class PlatformShaderDefines:
  defines_Tier1: List[int]
  defines_Tier2: List[int]
  defines_Tier3: List[int]
  shaderPlatform: int


@unitypy_define
class PlatformShaderSettings:
  useCascadedShadowMaps: Optional[bool] = None
  useScreenSpaceShadows: Optional[bool] = None


@unitypy_define
class PluginImportOutput:
  dllType: Optional[int] = None
  pluginType: Optional[int] = None
  scriptingRuntimeVersion: Optional[int] = None


@unitypy_define
class Polygon2D(ABC):
  m_Paths: Optional[List[List[Vector2f]]] = None


@unitypy_define
class PrefabModification:
  m_Modifications: List[PropertyModification]
  m_RemovedComponents: Union[List[PPtr[Object]], List[PPtr[Component]]]
  m_TransformParent: PPtr[Transform]
  m_AddedComponents: Optional[List[AddedComponent]] = None
  m_AddedGameObjects: Optional[List[AddedGameObject]] = None
  m_RemovedGameObjects: Optional[List[PPtr[GameObject]]] = None


@unitypy_define
class PresetType:
  m_ManagedTypeFallback: str
  m_ManagedTypePPtr: PPtr[MonoScript]
  m_NativeTypeID: int


@unitypy_define
class PreviewData:
  m_CompSize: int
  m_OrigSize: int
  m_PreviewData: List[float]


@unitypy_define
class ProbeSetIndex:
  m_Hash: Hash128
  m_Offset: int
  m_Size: int


@unitypy_define
class ProbeSetTetrahedralization:
  m_HullRays: List[Vector3f]
  m_Tetrahedra: List[Tetrahedron]


@unitypy_define
class ProceduralMaterialInformation:
  m_Offset: Vector2f
  m_Scale: Vector2f
  m_AnimationUpdateRate: Optional[int] = None
  m_GenerateAllOutputs: Optional[int] = None
  m_GenerateMipmaps: Optional[bool] = None
  m_GeneratedAtLoading: Optional[int] = None


@unitypy_define
class ProceduralTextureAssignment:
  baseUID: int
  material: PPtr[ProceduralMaterial]
  shaderProp: Union[FastPropertyName, str]


@unitypy_define
class PropertyModification:
  objectReference: PPtr[Object]
  propertyPath: str
  target: PPtr[Object]
  value: str


@unitypy_define
class PropertyModificationsTargetTestNativeObject:
  m_FloatValue: float
  m_IntegerValue: int


@unitypy_define
class QualitySetting:
  anisotropicTextures: int
  antiAliasing: int
  pixelLightCount: int
  shadowCascades: int
  shadowDistance: float
  shadowProjection: int
  shadowResolution: int
  shadows: int
  softParticles: bool
  softVegetation: bool
  vSyncCount: int
  adaptiveVsync: Optional[bool] = None
  adaptiveVsyncExtraA: Optional[int] = None
  adaptiveVsyncExtraB: Optional[int] = None
  asyncUploadBufferSize: Optional[int] = None
  asyncUploadPersistentBuffer: Optional[bool] = None
  asyncUploadTimeSlice: Optional[int] = None
  billboardsFaceCameraPosition: Optional[bool] = None
  blendWeights: Optional[int] = None
  customRenderPipeline: Optional[PPtr[MonoBehaviour]] = None
  enableLODCrossFade: Optional[bool] = None
  globalTextureMipmapLimit: Optional[int] = None
  lodBias: Optional[float] = None
  maximumLODLevel: Optional[int] = None
  name: Optional[str] = None
  particleRaycastBudget: Optional[int] = None
  realtimeGICPUUsage: Optional[int] = None
  realtimeReflectionProbes: Optional[bool] = None
  resolutionScalingFixedDPIFactor: Optional[float] = None
  shadowCascade2Split: Optional[float] = None
  shadowCascade4Split: Optional[Vector3f] = None
  shadowNearPlaneOffset: Optional[float] = None
  shadowmaskMode: Optional[int] = None
  skinWeights: Optional[int] = None
  streamingMipmapsActive: Optional[bool] = None
  streamingMipmapsAddAllCameras: Optional[bool] = None
  streamingMipmapsMaxFileIORequests: Optional[int] = None
  streamingMipmapsMaxLevelReduction: Optional[int] = None
  streamingMipmapsMemoryBudget: Optional[float] = None
  streamingMipmapsRenderersPerFrame: Optional[int] = None
  terrainBasemapDistance: Optional[float] = None
  terrainBillboardStart: Optional[float] = None
  terrainDetailDensityScale: Optional[float] = None
  terrainDetailDistance: Optional[float] = None
  terrainFadeLength: Optional[float] = None
  terrainMaxTrees: Optional[int] = None
  terrainPixelError: Optional[float] = None
  terrainQualityOverrides: Optional[int] = None
  terrainTreeDistance: Optional[float] = None
  textureMipmapLimitSettings: Optional[List[MipmapLimitSettings]] = None
  textureQuality: Optional[int] = None
  useLegacyDetailDistribution: Optional[bool] = None


@unitypy_define
class QuaternionCurve:
  curve: AnimationCurve
  path: str


@unitypy_define
class RationalTime:
  m_Count: int
  m_Rate: TicksPerSecond


@unitypy_define
class RayTracingShaderBuiltinSampler:
  bindPoint: int
  sampler: int


@unitypy_define
class RayTracingShaderConstantBuffer:
  byteSize: int
  name: str
  params: List[RayTracingShaderParam]
  hash: Optional[int] = None


@unitypy_define
class RayTracingShaderFunctionDesc:
  attributeSizeInBytes: int
  identifier: RayTracingShaderID
  payloadSizeInBytes: int


@unitypy_define
class RayTracingShaderID:
  name: str
  type: int


@unitypy_define
class RayTracingShaderParam:
  arraySize: int
  colCount: int
  name: str
  offset: int
  rowCount: int
  dataSize: Optional[int] = None
  dataType: Optional[int] = None
  propertySheetType: Optional[int] = None
  type: Optional[int] = None


@unitypy_define
class RayTracingShaderReflectionData:
  code: List[int]
  functions: List[RayTracingShaderFunctionDesc]
  globalResources: RayTracingShaderResources
  hasErrors: bool
  localResources: RayTracingShaderResources
  precompiled: Optional[List[int]] = None
  requirements: Optional[int] = None


@unitypy_define
class RayTracingShaderResource:
  bindPoint: int
  name: str
  rayGenMask: int
  samplerBindPoint: int
  texDimension: int
  arraySize: Optional[int] = None
  multisampled: Optional[bool] = None


@unitypy_define
class RayTracingShaderResources:
  builtinSamplers: List[RayTracingShaderBuiltinSampler]
  constantBuffers: List[RayTracingShaderResource]
  constantBuffersDesc: List[RayTracingShaderConstantBuffer]
  inputBuffers: List[RayTracingShaderResource]
  outputBuffers: List[RayTracingShaderResource]
  textures: List[RayTracingShaderResource]


@unitypy_define
class RayTracingShaderVariant:
  resourceReflectionData: RayTracingShaderReflectionData
  targetRenderer: int


@unitypy_define
class Rectf:
  height: float
  width: float
  x: float
  y: float


@unitypy_define
class RenderManager(GlobalGameManager):
  pass


@unitypy_define
class RenderPassInfo:
  attachmentCount: int
  attachments: List[AttachmentInfo]
  depthAttachmentIndex: int
  multiviewCount: int
  sampleCount: int
  shadingRateIndex: int
  subPassCount: int
  subPasses: List[SubPassDescriptor]


@unitypy_define
class RenderStateBlock:
  blendState: GfxBlendState
  depthState: GfxDepthState
  mask: int
  rasterState: GfxRasterState
  stencilRef: int
  stencilState: GfxStencilState


@unitypy_define
class RenderStateInfo:
  renderState: RenderStateBlock


@unitypy_define
class RendererData:
  lightmapIndex: int
  lightmapIndexDynamic: int
  lightmapST: Vector4f
  lightmapSTDynamic: Vector4f
  terrainChunkDynamicUVST: Vector4f
  terrainDynamicUVST: Vector4f
  uvMesh: PPtr[Mesh]
  explicitProbeSetHash: Optional[Hash128] = None


@unitypy_define
class ResourceManager_Dependency:
  m_Dependencies: List[PPtr[Object]]
  m_Object: PPtr[Object]


@unitypy_define
class RippleGroup:
  m_afDirectional_0: float
  m_afDirectional_1: float
  m_afDirectional_10: float
  m_afDirectional_11: float
  m_afDirectional_12: float
  m_afDirectional_13: float
  m_afDirectional_14: float
  m_afDirectional_15: float
  m_afDirectional_16: float
  m_afDirectional_17: float
  m_afDirectional_18: float
  m_afDirectional_19: float
  m_afDirectional_2: float
  m_afDirectional_3: float
  m_afDirectional_4: float
  m_afDirectional_5: float
  m_afDirectional_6: float
  m_afDirectional_7: float
  m_afDirectional_8: float
  m_afDirectional_9: float
  m_afFlexibility_0: float
  m_afFlexibility_1: float
  m_afFlexibility_10: float
  m_afFlexibility_11: float
  m_afFlexibility_12: float
  m_afFlexibility_13: float
  m_afFlexibility_14: float
  m_afFlexibility_15: float
  m_afFlexibility_16: float
  m_afFlexibility_17: float
  m_afFlexibility_18: float
  m_afFlexibility_19: float
  m_afFlexibility_2: float
  m_afFlexibility_3: float
  m_afFlexibility_4: float
  m_afFlexibility_5: float
  m_afFlexibility_6: float
  m_afFlexibility_7: float
  m_afFlexibility_8: float
  m_afFlexibility_9: float
  m_afPlanar_0: float
  m_afPlanar_1: float
  m_afPlanar_10: float
  m_afPlanar_11: float
  m_afPlanar_12: float
  m_afPlanar_13: float
  m_afPlanar_14: float
  m_afPlanar_15: float
  m_afPlanar_16: float
  m_afPlanar_17: float
  m_afPlanar_18: float
  m_afPlanar_19: float
  m_afPlanar_2: float
  m_afPlanar_3: float
  m_afPlanar_4: float
  m_afPlanar_5: float
  m_afPlanar_6: float
  m_afPlanar_7: float
  m_afPlanar_8: float
  m_afPlanar_9: float
  m_afSpeed_0: float
  m_afSpeed_1: float
  m_afSpeed_10: float
  m_afSpeed_11: float
  m_afSpeed_12: float
  m_afSpeed_13: float
  m_afSpeed_14: float
  m_afSpeed_15: float
  m_afSpeed_16: float
  m_afSpeed_17: float
  m_afSpeed_18: float
  m_afSpeed_19: float
  m_afSpeed_2: float
  m_afSpeed_3: float
  m_afSpeed_4: float
  m_afSpeed_5: float
  m_afSpeed_6: float
  m_afSpeed_7: float
  m_afSpeed_8: float
  m_afSpeed_9: float
  m_fIndependence: float
  m_fShimmer: float


@unitypy_define
class RootMotionData(ABC):
  pass


@unitypy_define
class RotationBySpeedModule:
  curve: MinMaxCurve
  enabled: bool
  range: Vector2f
  separateAxes: Optional[bool] = None
  x: Optional[MinMaxCurve] = None
  y: Optional[MinMaxCurve] = None


@unitypy_define
class RotationModule:
  curve: MinMaxCurve
  enabled: bool
  separateAxes: Optional[bool] = None
  x: Optional[MinMaxCurve] = None
  y: Optional[MinMaxCurve] = None


@unitypy_define
class SBranchWindLevel:
  m_afDirectionAdherence_0: float
  m_afDirectionAdherence_1: float
  m_afDirectionAdherence_2: float
  m_afDirectionAdherence_3: float
  m_afDirectionAdherence_4: float
  m_afDirectionAdherence_5: float
  m_afDirectionAdherence_6: float
  m_afDirectionAdherence_7: float
  m_afDirectionAdherence_8: float
  m_afDirectionAdherence_9: float
  m_afDistance_0: float
  m_afDistance_1: float
  m_afDistance_2: float
  m_afDistance_3: float
  m_afDistance_4: float
  m_afDistance_5: float
  m_afDistance_6: float
  m_afDistance_7: float
  m_afDistance_8: float
  m_afDistance_9: float
  m_afWhip_0: float
  m_afWhip_1: float
  m_afWhip_2: float
  m_afWhip_3: float
  m_afWhip_4: float
  m_afWhip_5: float
  m_afWhip_6: float
  m_afWhip_7: float
  m_afWhip_8: float
  m_afWhip_9: float
  m_fTurbulence: float
  m_fTwitch: float
  m_fTwitchFreqScale: float


@unitypy_define
class SParams:
  BranchLevel1: SBranchWindLevel
  BranchLevel2: SBranchWindLevel
  LeafGroup1: SWindGroup
  LeafGroup2: SWindGroup
  Oscillation0_0: float
  Oscillation0_1: float
  Oscillation0_2: float
  Oscillation0_3: float
  Oscillation0_4: float
  Oscillation0_5: float
  Oscillation0_6: float
  Oscillation0_7: float
  Oscillation0_8: float
  Oscillation0_9: float
  Oscillation1_0: float
  Oscillation1_1: float
  Oscillation1_2: float
  Oscillation1_3: float
  Oscillation1_4: float
  Oscillation1_5: float
  Oscillation1_6: float
  Oscillation1_7: float
  Oscillation1_8: float
  Oscillation1_9: float
  Oscillation2_0: float
  Oscillation2_1: float
  Oscillation2_2: float
  Oscillation2_3: float
  Oscillation2_4: float
  Oscillation2_5: float
  Oscillation2_6: float
  Oscillation2_7: float
  Oscillation2_8: float
  Oscillation2_9: float
  Oscillation3_0: float
  Oscillation3_1: float
  Oscillation3_2: float
  Oscillation3_3: float
  Oscillation3_4: float
  Oscillation3_5: float
  Oscillation3_6: float
  Oscillation3_7: float
  Oscillation3_8: float
  Oscillation3_9: float
  Oscillation4_0: float
  Oscillation4_1: float
  Oscillation4_2: float
  Oscillation4_3: float
  Oscillation4_4: float
  Oscillation4_5: float
  Oscillation4_6: float
  Oscillation4_7: float
  Oscillation4_8: float
  Oscillation4_9: float
  Oscillation5_0: float
  Oscillation5_1: float
  Oscillation5_2: float
  Oscillation5_3: float
  Oscillation5_4: float
  Oscillation5_5: float
  Oscillation5_6: float
  Oscillation5_7: float
  Oscillation5_8: float
  Oscillation5_9: float
  Oscillation6_0: float
  Oscillation6_1: float
  Oscillation6_2: float
  Oscillation6_3: float
  Oscillation6_4: float
  Oscillation6_5: float
  Oscillation6_6: float
  Oscillation6_7: float
  Oscillation6_8: float
  Oscillation6_9: float
  Oscillation7_0: float
  Oscillation7_1: float
  Oscillation7_2: float
  Oscillation7_3: float
  Oscillation7_4: float
  Oscillation7_5: float
  Oscillation7_6: float
  Oscillation7_7: float
  Oscillation7_8: float
  Oscillation7_9: float
  Oscillation8_0: float
  Oscillation8_1: float
  Oscillation8_2: float
  Oscillation8_3: float
  Oscillation8_4: float
  Oscillation8_5: float
  Oscillation8_6: float
  Oscillation8_7: float
  Oscillation8_8: float
  Oscillation8_9: float
  Oscillation9_0: float
  Oscillation9_1: float
  Oscillation9_2: float
  Oscillation9_3: float
  Oscillation9_4: float
  Oscillation9_5: float
  Oscillation9_6: float
  Oscillation9_7: float
  Oscillation9_8: float
  Oscillation9_9: float
  m_afFrondRippleDistance_0: float
  m_afFrondRippleDistance_1: float
  m_afFrondRippleDistance_2: float
  m_afFrondRippleDistance_3: float
  m_afFrondRippleDistance_4: float
  m_afFrondRippleDistance_5: float
  m_afFrondRippleDistance_6: float
  m_afFrondRippleDistance_7: float
  m_afFrondRippleDistance_8: float
  m_afFrondRippleDistance_9: float
  m_afGlobalDirectionAdherence_0: float
  m_afGlobalDirectionAdherence_1: float
  m_afGlobalDirectionAdherence_2: float
  m_afGlobalDirectionAdherence_3: float
  m_afGlobalDirectionAdherence_4: float
  m_afGlobalDirectionAdherence_5: float
  m_afGlobalDirectionAdherence_6: float
  m_afGlobalDirectionAdherence_7: float
  m_afGlobalDirectionAdherence_8: float
  m_afGlobalDirectionAdherence_9: float
  m_afGlobalDistance_0: float
  m_afGlobalDistance_1: float
  m_afGlobalDistance_2: float
  m_afGlobalDistance_3: float
  m_afGlobalDistance_4: float
  m_afGlobalDistance_5: float
  m_afGlobalDistance_6: float
  m_afGlobalDistance_7: float
  m_afGlobalDistance_8: float
  m_afGlobalDistance_9: float
  m_fAnchorDistanceScale: float
  m_fAnchorOffset: float
  m_fDirectionResponse: float
  m_fFrondRippleLightingScalar: float
  m_fFrondRippleTile: float
  m_fGlobalHeight: float
  m_fGlobalHeightExponent: float
  m_fGustDurationMax: float
  m_fGustDurationMin: float
  m_fGustFallScalar: float
  m_fGustFrequency: float
  m_fGustRiseScalar: float
  m_fGustStrengthMax: float
  m_fGustStrengthMin: float
  m_fRollingBranchFieldMin: float
  m_fRollingBranchLightingAdjust: float
  m_fRollingBranchVerticalOffset: float
  m_fRollingLeafRippleMin: float
  m_fRollingLeafTumbleMin: float
  m_fRollingNoisePeriod: float
  m_fRollingNoiseSize: float
  m_fRollingNoiseSpeed: float
  m_fRollingNoiseTurbulence: float
  m_fRollingNoiseTwist: float
  m_fStrengthResponse: float


@unitypy_define
class SWindGroup:
  m_afRippleDistance_0: float
  m_afRippleDistance_1: float
  m_afRippleDistance_2: float
  m_afRippleDistance_3: float
  m_afRippleDistance_4: float
  m_afRippleDistance_5: float
  m_afRippleDistance_6: float
  m_afRippleDistance_7: float
  m_afRippleDistance_8: float
  m_afRippleDistance_9: float
  m_afTumbleDirectionAdherence_0: float
  m_afTumbleDirectionAdherence_1: float
  m_afTumbleDirectionAdherence_2: float
  m_afTumbleDirectionAdherence_3: float
  m_afTumbleDirectionAdherence_4: float
  m_afTumbleDirectionAdherence_5: float
  m_afTumbleDirectionAdherence_6: float
  m_afTumbleDirectionAdherence_7: float
  m_afTumbleDirectionAdherence_8: float
  m_afTumbleDirectionAdherence_9: float
  m_afTumbleFlip_0: float
  m_afTumbleFlip_1: float
  m_afTumbleFlip_2: float
  m_afTumbleFlip_3: float
  m_afTumbleFlip_4: float
  m_afTumbleFlip_5: float
  m_afTumbleFlip_6: float
  m_afTumbleFlip_7: float
  m_afTumbleFlip_8: float
  m_afTumbleFlip_9: float
  m_afTumbleTwist_0: float
  m_afTumbleTwist_1: float
  m_afTumbleTwist_2: float
  m_afTumbleTwist_3: float
  m_afTumbleTwist_4: float
  m_afTumbleTwist_5: float
  m_afTumbleTwist_6: float
  m_afTumbleTwist_7: float
  m_afTumbleTwist_8: float
  m_afTumbleTwist_9: float
  m_afTwitchThrow_0: float
  m_afTwitchThrow_1: float
  m_afTwitchThrow_2: float
  m_afTwitchThrow_3: float
  m_afTwitchThrow_4: float
  m_afTwitchThrow_5: float
  m_afTwitchThrow_6: float
  m_afTwitchThrow_7: float
  m_afTwitchThrow_8: float
  m_afTwitchThrow_9: float
  m_fLeewardScalar: float
  m_fRollMaxScale: float
  m_fRollMinScale: float
  m_fRollSeparation: float
  m_fRollSpeed: float
  m_fTwitchSharpness: float


@unitypy_define
class SampleSettings:
  compressionFormat: int
  conversionMode: int
  loadType: int
  quality: float
  sampleRateOverride: int
  sampleRateSetting: int
  preloadAudioData: Optional[bool] = None


@unitypy_define
class SamplerParameter:
  bindPoint: int
  sampler: int


@unitypy_define
class Scene(LevelGameManager):
  enabled: Optional[bool] = None
  guid: Optional[GUID] = None
  m_PVSData: Optional[List[int]] = None
  m_PVSObjectsArray: Optional[List[PPtr[Renderer]]] = None
  m_PVSPortalsArray: Optional[List[PPtr[OcclusionPortal]]] = None
  m_QueryMode: Optional[int] = None
  path: Optional[str] = None


@unitypy_define
class SceneDataContainer:
  m_SceneData: List[Tuple[SceneIdentifier, HierarchicalSceneData]]


@unitypy_define
class SceneIdentifier:
  guid: GUID
  handle: int


@unitypy_define
class SceneObjectIdentifier:
  targetObject: int
  targetPrefab: int


@unitypy_define
class SceneSettings(LevelGameManager):
  m_PVSData: List[int]
  m_PVSObjectsArray: List[PPtr[Renderer]]
  m_PVSPortalsArray: List[PPtr[OcclusionPortal]]
  m_QueryMode: Optional[int] = None


@unitypy_define
class SceneVisibilityData:
  m_SceneGUID: GUID


@unitypy_define
class ScriptMapper(GlobalGameManager):
  m_Shaders: NameToObjectMap
  m_PreloadShaders: Optional[bool] = None


@unitypy_define
class SecondarySpriteTexture:
  name: str
  texture: PPtr[Texture2D]


@unitypy_define
class SecondaryTextureSettings:
  platformSettings: List[TextureImporterPlatformSettings]
  sRGB: Optional[bool] = None


@unitypy_define
class SelectorStateConstant:
  m_FullPathID: int
  m_IsEntry: bool
  m_TransitionConstantArray: List[OffsetPtr]


@unitypy_define
class SelectorTransitionConstant:
  m_ConditionConstantArray: List[OffsetPtr]
  m_Destination: int


@unitypy_define
class SerializedCustomEditorForRenderPipeline:
  customEditorName: str
  renderPipelineType: str


@unitypy_define
class SerializedPass:
  m_HasInstancingVariant: bool
  m_Name: str
  m_NameIndices: List[Tuple[str, int]]
  m_ProgramMask: int
  m_State: SerializedShaderState
  m_Tags: SerializedTagMap
  m_TextureName: str
  m_Type: int
  m_UseName: str
  progDomain: SerializedProgram
  progFragment: SerializedProgram
  progGeometry: SerializedProgram
  progHull: SerializedProgram
  progVertex: SerializedProgram
  m_EditorDataHash: Optional[List[Hash128]] = None
  m_GlobalKeywordMask: Optional[List[int]] = None
  m_HasProceduralInstancingVariant: Optional[bool] = None
  m_LocalKeywordMask: Optional[List[int]] = None
  m_Platforms: Optional[List[int]] = None
  m_SerializedKeywordStateMask: Optional[List[int]] = None
  progRayTracing: Optional[SerializedProgram] = None


@unitypy_define
class SerializedPlayerSubProgram:
  m_BlobIndex: int
  m_GpuProgramType: int
  m_KeywordIndices: List[int]
  m_ShaderRequirements: int


@unitypy_define
class SerializedProgram:
  m_SubPrograms: List[SerializedSubProgram]
  m_CommonParameters: Optional[SerializedProgramParameters] = None
  m_ParameterBlobIndices: Optional[List[List[int]]] = None
  m_PlayerSubPrograms: Optional[List[List[SerializedPlayerSubProgram]]] = None
  m_SerializedKeywordStateMask: Optional[List[int]] = None


@unitypy_define
class SerializedProgramParameters:
  m_BufferParams: List[BufferBinding]
  m_ConstantBufferBindings: List[BufferBinding]
  m_ConstantBuffers: List[ConstantBuffer]
  m_MatrixParams: List[MatrixParameter]
  m_Samplers: List[SamplerParameter]
  m_TextureParams: List[TextureParameter]
  m_UAVParams: List[UAVParameter]
  m_VectorParams: List[VectorParameter]


@unitypy_define
class SerializedProperties:
  m_Props: List[SerializedProperty]


@unitypy_define
class SerializedProperty:
  m_Attributes: List[str]
  m_DefTexture: SerializedTextureProperty
  m_DefValue_0_: float
  m_DefValue_1_: float
  m_DefValue_2_: float
  m_DefValue_3_: float
  m_Description: str
  m_Flags: int
  m_Name: str
  m_Type: int


@unitypy_define
class SerializedShader:
  m_CustomEditorName: str
  m_Dependencies: List[SerializedShaderDependency]
  m_DisableNoSubshadersMessage: bool
  m_FallbackName: str
  m_Name: str
  m_PropInfo: SerializedProperties
  m_SubShaders: List[SerializedSubShader]
  m_CustomEditorForRenderPipelines: Optional[
    List[SerializedCustomEditorForRenderPipeline]
  ] = None
  m_KeywordFlags: Optional[List[int]] = None
  m_KeywordNames: Optional[List[str]] = None


@unitypy_define
class SerializedShaderDependency:
  from_: str
  to: str


@unitypy_define
class SerializedShaderFloatValue:
  name: Union[FastPropertyName, str]
  val: float


@unitypy_define
class SerializedShaderRTBlendState:
  blendOp: SerializedShaderFloatValue
  blendOpAlpha: SerializedShaderFloatValue
  colMask: SerializedShaderFloatValue
  destBlend: SerializedShaderFloatValue
  destBlendAlpha: SerializedShaderFloatValue
  srcBlend: SerializedShaderFloatValue
  srcBlendAlpha: SerializedShaderFloatValue


@unitypy_define
class SerializedShaderState:
  alphaToMask: SerializedShaderFloatValue
  culling: SerializedShaderFloatValue
  fogColor: SerializedShaderVectorValue
  fogDensity: SerializedShaderFloatValue
  fogEnd: SerializedShaderFloatValue
  fogMode: int
  fogStart: SerializedShaderFloatValue
  gpuProgramID: int
  lighting: bool
  m_LOD: int
  m_Name: str
  m_Tags: SerializedTagMap
  offsetFactor: SerializedShaderFloatValue
  offsetUnits: SerializedShaderFloatValue
  rtBlend0: SerializedShaderRTBlendState
  rtBlend1: SerializedShaderRTBlendState
  rtBlend2: SerializedShaderRTBlendState
  rtBlend3: SerializedShaderRTBlendState
  rtBlend4: SerializedShaderRTBlendState
  rtBlend5: SerializedShaderRTBlendState
  rtBlend6: SerializedShaderRTBlendState
  rtBlend7: SerializedShaderRTBlendState
  rtSeparateBlend: bool
  stencilOp: SerializedStencilOp
  stencilOpBack: SerializedStencilOp
  stencilOpFront: SerializedStencilOp
  stencilReadMask: SerializedShaderFloatValue
  stencilRef: SerializedShaderFloatValue
  stencilWriteMask: SerializedShaderFloatValue
  zTest: SerializedShaderFloatValue
  zWrite: SerializedShaderFloatValue
  conservative: Optional[SerializedShaderFloatValue] = None
  zClip: Optional[SerializedShaderFloatValue] = None


@unitypy_define
class SerializedShaderVectorValue:
  name: Union[FastPropertyName, str]
  w: SerializedShaderFloatValue
  x: SerializedShaderFloatValue
  y: SerializedShaderFloatValue
  z: SerializedShaderFloatValue


@unitypy_define
class SerializedStencilOp:
  comp: SerializedShaderFloatValue
  fail: SerializedShaderFloatValue
  pass_: SerializedShaderFloatValue
  zFail: SerializedShaderFloatValue


@unitypy_define
class SerializedSubProgram:
  m_BlobIndex: int
  m_Channels: ParserBindChannels
  m_GpuProgramType: int
  m_ShaderHardwareTier: int
  m_BufferParams: Optional[List[BufferBinding]] = None
  m_ConstantBufferBindings: Optional[List[BufferBinding]] = None
  m_ConstantBuffers: Optional[List[ConstantBuffer]] = None
  m_GlobalKeywordIndices: Optional[List[int]] = None
  m_KeywordIndices: Optional[List[int]] = None
  m_LocalKeywordIndices: Optional[List[int]] = None
  m_MatrixParams: Optional[List[MatrixParameter]] = None
  m_Parameters: Optional[SerializedProgramParameters] = None
  m_Samplers: Optional[List[SamplerParameter]] = None
  m_ShaderRequirements: Optional[int] = None
  m_TextureParams: Optional[List[TextureParameter]] = None
  m_UAVParams: Optional[List[UAVParameter]] = None
  m_VectorParams: Optional[List[VectorParameter]] = None


@unitypy_define
class SerializedSubShader:
  m_LOD: int
  m_Passes: List[SerializedPass]
  m_Tags: SerializedTagMap


@unitypy_define
class SerializedTagMap:
  tags: List[Tuple[str, str]]


@unitypy_define
class SerializedTextureProperty:
  m_DefaultName: str
  m_TexDim: int


@unitypy_define
class ShaderBindChannel:
  source: int
  target: int


@unitypy_define
class ShaderInfo:
  variants: List[VariantInfo]


@unitypy_define
class ShadowSettings:
  m_Bias: float
  m_Resolution: int
  m_Strength: float
  m_Type: int
  m_CullingMatrixOverride: Optional[Matrix4x4f] = None
  m_CustomResolution: Optional[int] = None
  m_NearPlane: Optional[float] = None
  m_NormalBias: Optional[float] = None
  m_Softness: Optional[float] = None
  m_SoftnessFade: Optional[float] = None
  m_UseCullingMatrixOverride: Optional[bool] = None


@unitypy_define
class ShapeModule:
  angle: float
  enabled: bool
  m_Mesh: PPtr[Mesh]
  placementMode: int
  radius: Union[MultiModeParameter, float]
  type: int
  alignToDirection: Optional[bool] = None
  arc: Optional[Union[MultiModeParameter, float]] = None
  boxThickness: Optional[Vector3f] = None
  boxX: Optional[float] = None
  boxY: Optional[float] = None
  boxZ: Optional[float] = None
  donutRadius: Optional[float] = None
  length: Optional[float] = None
  m_MeshMaterialIndex: Optional[int] = None
  m_MeshNormalOffset: Optional[float] = None
  m_MeshRenderer: Optional[PPtr[MeshRenderer]] = None
  m_MeshScale: Optional[float] = None
  m_MeshSpawn: Optional[MultiModeParameter] = None
  m_Position: Optional[Vector3f] = None
  m_Rotation: Optional[Vector3f] = None
  m_Scale: Optional[Vector3f] = None
  m_SkinnedMeshRenderer: Optional[PPtr[SkinnedMeshRenderer]] = None
  m_Sprite: Optional[PPtr[Sprite]] = None
  m_SpriteRenderer: Optional[PPtr[SpriteRenderer]] = None
  m_Texture: Optional[PPtr[Texture2D]] = None
  m_TextureAlphaAffectsParticles: Optional[bool] = None
  m_TextureBilinearFiltering: Optional[bool] = None
  m_TextureClipChannel: Optional[int] = None
  m_TextureClipThreshold: Optional[float] = None
  m_TextureColorAffectsParticles: Optional[bool] = None
  m_TextureUVChannel: Optional[int] = None
  m_UseMeshColors: Optional[bool] = None
  m_UseMeshMaterialIndex: Optional[bool] = None
  radiusThickness: Optional[float] = None
  randomDirection: Optional[bool] = None
  randomDirectionAmount: Optional[float] = None
  randomPositionAmount: Optional[float] = None
  sphericalDirectionAmount: Optional[float] = None


@unitypy_define
class SizeBySpeedModule:
  curve: MinMaxCurve
  enabled: bool
  range: Vector2f
  separateAxes: Optional[bool] = None
  y: Optional[MinMaxCurve] = None
  z: Optional[MinMaxCurve] = None


@unitypy_define
class SizeModule:
  curve: MinMaxCurve
  enabled: bool
  separateAxes: Optional[bool] = None
  y: Optional[MinMaxCurve] = None
  z: Optional[MinMaxCurve] = None


@unitypy_define
class Skeleton:
  m_AxesArray: List[Axes]
  m_ID: List[int]
  m_Node: List[Node]


@unitypy_define
class SkeletonBone:
  m_Name: str
  m_Position: Vector3f
  m_Rotation: Quaternionf
  m_Scale: Vector3f
  m_ParentName: Optional[str] = None
  m_TransformModified: Optional[bool] = None


@unitypy_define
class SkeletonBoneLimit:
  m_Length: float
  m_Max: Vector3f
  m_Min: Vector3f
  m_Modified: bool
  m_Value: Vector3f
  m_PostQ: Optional[Quaternionf] = None
  m_PreQ: Optional[Quaternionf] = None


@unitypy_define
class SkeletonMask:
  m_Data: List[SkeletonMaskElement]


@unitypy_define
class SkeletonMaskElement:
  m_Weight: float
  m_Index: Optional[int] = None
  m_PathHash: Optional[int] = None


@unitypy_define
class SkeletonPose:
  m_X: List[xform]


@unitypy_define
class SketchUpImportCamera:
  aspectRatio: float
  fov: float
  isPerspective: int
  lookAt: Vector3f
  orthoSize: float
  position: Vector3f
  up: Vector3f
  farPlane: Optional[float] = None
  nearPlane: Optional[float] = None


@unitypy_define
class SketchUpImportData:
  defaultCamera: SketchUpImportCamera
  scenes: List[SketchUpImportScene]


@unitypy_define
class SketchUpImportScene:
  camera: SketchUpImportCamera
  name: str


@unitypy_define
class SnapshotConstant:
  nameHash: int
  transitionIndices: List[int]
  transitionTypes: List[int]
  values: List[float]


@unitypy_define
class SoftJointLimit:
  bounciness: float
  limit: float
  contactDistance: Optional[float] = None
  damper: Optional[float] = None
  spring: Optional[float] = None


@unitypy_define
class SoftJointLimitSpring:
  damper: float
  spring: float


@unitypy_define
class SortingLayerEntry:
  name: str
  uniqueID: int
  userID: Optional[int] = None


@unitypy_define
class SourceAssetIdentifier:
  assembly: str
  name: str
  type: str


@unitypy_define
class SourceTextureInformation:
  doesTextureContainAlpha: bool
  height: int
  width: int
  doesTextureContainColor: Optional[bool] = None
  sourceWasHDR: Optional[bool] = None


@unitypy_define
class SpeedTreeWind:
  BRANCH_DIRECTIONAL_1: bool
  BRANCH_DIRECTIONAL_2: bool
  BRANCH_DIRECTIONAL_FROND_1: bool
  BRANCH_DIRECTIONAL_FROND_2: bool
  BRANCH_OSC_COMPLEX_1: bool
  BRANCH_OSC_COMPLEX_2: bool
  BRANCH_SIMPLE_1: bool
  BRANCH_SIMPLE_2: bool
  BRANCH_TURBULENCE_1: bool
  BRANCH_TURBULENCE_2: bool
  BRANCH_WHIP_1: bool
  BRANCH_WHIP_2: bool
  BranchWindAnchor0: float
  BranchWindAnchor1: float
  BranchWindAnchor2: float
  FROND_RIPPLE_ADJUST_LIGHTING: bool
  FROND_RIPPLE_ONE_SIDED: bool
  FROND_RIPPLE_TWO_SIDED: bool
  GLOBAL_PRESERVE_SHAPE: bool
  GLOBAL_WIND: bool
  LEAF_OCCLUSION_1: bool
  LEAF_OCCLUSION_2: bool
  LEAF_RIPPLE_COMPUTED_1: bool
  LEAF_RIPPLE_COMPUTED_2: bool
  LEAF_RIPPLE_VERTEX_NORMAL_1: bool
  LEAF_RIPPLE_VERTEX_NORMAL_2: bool
  LEAF_TUMBLE_1: bool
  LEAF_TUMBLE_2: bool
  LEAF_TWITCH_1: bool
  LEAF_TWITCH_2: bool
  ROLLING: bool
  m_fMaxBranchLevel1Length: float
  m_sParams: SParams


@unitypy_define
class SpeedTreeWindConfig8:
  BRANCH_DIRECTIONAL_1: bool
  BRANCH_DIRECTIONAL_2: bool
  BRANCH_DIRECTIONAL_FROND_1: bool
  BRANCH_DIRECTIONAL_FROND_2: bool
  BRANCH_OSC_COMPLEX_1: bool
  BRANCH_OSC_COMPLEX_2: bool
  BRANCH_SIMPLE_1: bool
  BRANCH_SIMPLE_2: bool
  BRANCH_TURBULENCE_1: bool
  BRANCH_TURBULENCE_2: bool
  BRANCH_WHIP_1: bool
  BRANCH_WHIP_2: bool
  BranchLevel1: SBranchWindLevel
  BranchLevel2: SBranchWindLevel
  BranchWindAnchor0: float
  BranchWindAnchor1: float
  BranchWindAnchor2: float
  FROND_RIPPLE_ADJUST_LIGHTING: bool
  FROND_RIPPLE_ONE_SIDED: bool
  FROND_RIPPLE_TWO_SIDED: bool
  GLOBAL_PRESERVE_SHAPE: bool
  GLOBAL_WIND: bool
  LEAF_OCCLUSION_1: bool
  LEAF_OCCLUSION_2: bool
  LEAF_RIPPLE_COMPUTED_1: bool
  LEAF_RIPPLE_COMPUTED_2: bool
  LEAF_RIPPLE_VERTEX_NORMAL_1: bool
  LEAF_RIPPLE_VERTEX_NORMAL_2: bool
  LEAF_TUMBLE_1: bool
  LEAF_TUMBLE_2: bool
  LEAF_TWITCH_1: bool
  LEAF_TWITCH_2: bool
  LeafGroup1: SWindGroup
  LeafGroup2: SWindGroup
  Oscillation0_0: float
  Oscillation0_1: float
  Oscillation0_2: float
  Oscillation0_3: float
  Oscillation0_4: float
  Oscillation0_5: float
  Oscillation0_6: float
  Oscillation0_7: float
  Oscillation0_8: float
  Oscillation0_9: float
  Oscillation1_0: float
  Oscillation1_1: float
  Oscillation1_2: float
  Oscillation1_3: float
  Oscillation1_4: float
  Oscillation1_5: float
  Oscillation1_6: float
  Oscillation1_7: float
  Oscillation1_8: float
  Oscillation1_9: float
  Oscillation2_0: float
  Oscillation2_1: float
  Oscillation2_2: float
  Oscillation2_3: float
  Oscillation2_4: float
  Oscillation2_5: float
  Oscillation2_6: float
  Oscillation2_7: float
  Oscillation2_8: float
  Oscillation2_9: float
  Oscillation3_0: float
  Oscillation3_1: float
  Oscillation3_2: float
  Oscillation3_3: float
  Oscillation3_4: float
  Oscillation3_5: float
  Oscillation3_6: float
  Oscillation3_7: float
  Oscillation3_8: float
  Oscillation3_9: float
  Oscillation4_0: float
  Oscillation4_1: float
  Oscillation4_2: float
  Oscillation4_3: float
  Oscillation4_4: float
  Oscillation4_5: float
  Oscillation4_6: float
  Oscillation4_7: float
  Oscillation4_8: float
  Oscillation4_9: float
  Oscillation5_0: float
  Oscillation5_1: float
  Oscillation5_2: float
  Oscillation5_3: float
  Oscillation5_4: float
  Oscillation5_5: float
  Oscillation5_6: float
  Oscillation5_7: float
  Oscillation5_8: float
  Oscillation5_9: float
  Oscillation6_0: float
  Oscillation6_1: float
  Oscillation6_2: float
  Oscillation6_3: float
  Oscillation6_4: float
  Oscillation6_5: float
  Oscillation6_6: float
  Oscillation6_7: float
  Oscillation6_8: float
  Oscillation6_9: float
  Oscillation7_0: float
  Oscillation7_1: float
  Oscillation7_2: float
  Oscillation7_3: float
  Oscillation7_4: float
  Oscillation7_5: float
  Oscillation7_6: float
  Oscillation7_7: float
  Oscillation7_8: float
  Oscillation7_9: float
  Oscillation8_0: float
  Oscillation8_1: float
  Oscillation8_2: float
  Oscillation8_3: float
  Oscillation8_4: float
  Oscillation8_5: float
  Oscillation8_6: float
  Oscillation8_7: float
  Oscillation8_8: float
  Oscillation8_9: float
  Oscillation9_0: float
  Oscillation9_1: float
  Oscillation9_2: float
  Oscillation9_3: float
  Oscillation9_4: float
  Oscillation9_5: float
  Oscillation9_6: float
  Oscillation9_7: float
  Oscillation9_8: float
  Oscillation9_9: float
  ROLLING: bool
  m_afFrondRippleDistance_0: float
  m_afFrondRippleDistance_1: float
  m_afFrondRippleDistance_2: float
  m_afFrondRippleDistance_3: float
  m_afFrondRippleDistance_4: float
  m_afFrondRippleDistance_5: float
  m_afFrondRippleDistance_6: float
  m_afFrondRippleDistance_7: float
  m_afFrondRippleDistance_8: float
  m_afFrondRippleDistance_9: float
  m_afGlobalDirectionAdherence_0: float
  m_afGlobalDirectionAdherence_1: float
  m_afGlobalDirectionAdherence_2: float
  m_afGlobalDirectionAdherence_3: float
  m_afGlobalDirectionAdherence_4: float
  m_afGlobalDirectionAdherence_5: float
  m_afGlobalDirectionAdherence_6: float
  m_afGlobalDirectionAdherence_7: float
  m_afGlobalDirectionAdherence_8: float
  m_afGlobalDirectionAdherence_9: float
  m_afGlobalDistance_0: float
  m_afGlobalDistance_1: float
  m_afGlobalDistance_2: float
  m_afGlobalDistance_3: float
  m_afGlobalDistance_4: float
  m_afGlobalDistance_5: float
  m_afGlobalDistance_6: float
  m_afGlobalDistance_7: float
  m_afGlobalDistance_8: float
  m_afGlobalDistance_9: float
  m_fAnchorDistanceScale: float
  m_fAnchorOffset: float
  m_fDirectionResponse: float
  m_fFrondRippleLightingScalar: float
  m_fFrondRippleTile: float
  m_fGlobalHeight: float
  m_fGlobalHeightExponent: float
  m_fGustDurationMax: float
  m_fGustDurationMin: float
  m_fGustFallScalar: float
  m_fGustFrequency: float
  m_fGustRiseScalar: float
  m_fGustStrengthMax: float
  m_fGustStrengthMin: float
  m_fMaxBranchLevel1Length: float
  m_fRollingBranchFieldMin: float
  m_fRollingBranchLightingAdjust: float
  m_fRollingBranchVerticalOffset: float
  m_fRollingLeafRippleMin: float
  m_fRollingLeafTumbleMin: float
  m_fRollingNoisePeriod: float
  m_fRollingNoiseSize: float
  m_fRollingNoiseSpeed: float
  m_fRollingNoiseTurbulence: float
  m_fRollingNoiseTwist: float
  m_fStrengthResponse: float


@unitypy_define
class SpeedTreeWindConfig9:
  m_bDoBranch1: int
  m_bDoBranch2: int
  m_bDoRipple: int
  m_bDoShared: int
  m_bDoShimmer: int
  m_bLodFade: int
  m_fBranch1StretchLimit: float
  m_fBranch2StretchLimit: float
  m_fDirectionResponse: float
  m_fGustDurationMax: float
  m_fGustDurationMin: float
  m_fGustFallScalar: float
  m_fGustFrequency: float
  m_fGustRiseScalar: float
  m_fGustStrengthMax: float
  m_fGustStrengthMin: float
  m_fSharedHeightStart: float
  m_fStrengthResponse: float
  m_fWindIndependence: float
  m_sBranch1: BranchWindLevel
  m_sBranch2: BranchWindLevel
  m_sRipple: RippleGroup
  m_sShared: BranchWindLevel
  m_vTreeExtents: Vector3f
  m_fImportScaling: Optional[float] = None
  pad: Optional[int] = None


@unitypy_define
class SphericalHarmonicsL2:
  sh_10_: float
  sh_11_: float
  sh_12_: float
  sh_13_: float
  sh_14_: float
  sh_15_: float
  sh_16_: float
  sh_17_: float
  sh_18_: float
  sh_19_: float
  sh_20_: float
  sh_21_: float
  sh_22_: float
  sh_23_: float
  sh_24_: float
  sh_25_: float
  sh_26_: float
  sh__0_: float
  sh__1_: float
  sh__2_: float
  sh__3_: float
  sh__4_: float
  sh__5_: float
  sh__6_: float
  sh__7_: float
  sh__8_: float
  sh__9_: float


@unitypy_define
class SplashScreenLogo:
  duration: float
  logo: PPtr[Sprite]


@unitypy_define
class SplatDatabase:
  m_AlphaTextures: List[PPtr[Texture2D]]
  m_AlphamapResolution: int
  m_BaseMapResolution: int
  m_ColorSpace: Optional[int] = None
  m_MaterialRequiresMetallic: Optional[bool] = None
  m_MaterialRequiresSmoothness: Optional[bool] = None
  m_Splats: Optional[List[SplatPrototype]] = None
  m_TerrainLayers: Optional[List[PPtr[TerrainLayer]]] = None


@unitypy_define
class SplatPrototype:
  texture: PPtr[Texture2D]
  tileOffset: Vector2f
  tileSize: Vector2f
  normalMap: Optional[PPtr[Texture2D]] = None
  smoothness: Optional[float] = None
  specularMetallic: Optional[Vector4f] = None


@unitypy_define
class SpriteAtlasAssetData:
  packables: List[PPtr[Object]]


@unitypy_define
class SpriteAtlasData:
  alphaTexture: PPtr[Texture2D]
  downscaleMultiplier: float
  settingsRaw: int
  texture: PPtr[Texture2D]
  textureRect: Rectf
  textureRectOffset: Vector2f
  uvTransform: Vector4f
  atlasRectOffset: Optional[Vector2f] = None
  secondaryTextures: Optional[List[SecondarySpriteTexture]] = None


@unitypy_define
class SpriteAtlasEditorData:
  bindAsDefault: bool
  cachedData: PPtr[CachedSpriteAtlasRuntimeData]
  isAtlasV2: bool
  packables: List[PPtr[Object]]
  packingSettings: PackingSettings
  platformSettings: List[TextureImporterPlatformSettings]
  textureSettings: TextureSettings
  variantMultiplier: float
  secondaryTextureSettings: Optional[List[Tuple[str, SecondaryTextureSettings]]] = (
    None
  )
  storedHash: Optional[Hash128] = None
  totalSpriteSurfaceArea: Optional[int] = None


@unitypy_define
class SpriteBone:
  length: float
  name: str
  parentId: int
  position: Vector3f
  rotation: Quaternionf
  color: Optional[ColorRGBA] = None
  guid: Optional[str] = None


@unitypy_define
class SpriteCustomDataEntry:
  m_Key: str
  m_Value: str


@unitypy_define
class SpriteCustomMetadata:
  m_Entries: List[SpriteCustomDataEntry]


@unitypy_define
class SpriteData:
  sprite: PPtr[Object]


@unitypy_define
class SpriteMetaData:
  m_Alignment: int
  m_Name: str
  m_Pivot: Vector2f
  m_Rect: Rectf
  m_Bones: Optional[List[SpriteBone]] = None
  m_Border: Optional[Vector4f] = None
  m_CustomData: Optional[str] = None
  m_Edges: Optional[List[int2_storage]] = None
  m_Indices: Optional[List[int]] = None
  m_InternalID: Optional[int] = None
  m_Outline: Optional[List[List[Vector2f]]] = None
  m_PhysicsShape: Optional[List[List[Vector2f]]] = None
  m_SpriteID: Optional[str] = None
  m_TessellationDetail: Optional[float] = None
  m_Vertices: Optional[List[Vector2f]] = None
  m_Weights: Optional[List[BoneWeights4]] = None


@unitypy_define
class SpriteRenderData:
  settingsRaw: int
  texture: PPtr[Texture2D]
  textureRect: Rectf
  textureRectOffset: Vector2f
  alphaTexture: Optional[PPtr[Texture2D]] = None
  atlasRectOffset: Optional[Vector2f] = None
  downscaleMultiplier: Optional[float] = None
  indices: Optional[List[int]] = None
  m_Bindpose: Optional[List[Matrix4x4f]] = None
  m_IndexBuffer: Optional[List[int]] = None
  m_SourceSkin: Optional[List[BoneWeights4]] = None
  m_SubMeshes: Optional[List[SubMesh]] = None
  m_VertexData: Optional[VertexData] = None
  secondaryTextures: Optional[List[SecondarySpriteTexture]] = None
  uvTransform: Optional[Vector4f] = None
  vertices: Optional[List[SpriteVertex]] = None


@unitypy_define
class SpriteSheetMetaData:
  m_Sprites: List[SpriteMetaData]
  m_Bones: Optional[List[SpriteBone]] = None
  m_CustomData: Optional[str] = None
  m_Edges: Optional[List[int2_storage]] = None
  m_Indices: Optional[List[int]] = None
  m_InternalID: Optional[int] = None
  m_NameFileIdTable: Optional[List[Tuple[str, int]]] = None
  m_Outline: Optional[List[List[Vector2f]]] = None
  m_PhysicsShape: Optional[List[List[Vector2f]]] = None
  m_SecondaryTextures: Optional[List[SecondarySpriteTexture]] = None
  m_SpriteCustomMetadata: Optional[SpriteCustomMetadata] = None
  m_SpriteID: Optional[str] = None
  m_Vertices: Optional[List[Vector2f]] = None
  m_Weights: Optional[List[BoneWeights4]] = None


@unitypy_define
class SpriteTilingProperty:
  adaptiveTiling: bool
  adaptiveTilingThreshold: float
  border: Vector4f
  drawMode: int
  newSize: Vector2f
  oldSize: Vector2f
  pivot: Vector2f


@unitypy_define
class SpriteVertex:
  pos: Vector3f
  uv: Optional[Vector2f] = None


@unitypy_define
class State(NamedObject):
  m_IKOnFeet: bool
  m_Motions: List[PPtr[Motion]]
  m_Name: str
  m_ParentStateMachine: PPtr[StateMachine]
  m_Position: Vector3f
  m_Speed: float
  m_Tag: str
  m_CycleOffset: Optional[float] = None
  m_Mirror: Optional[bool] = None


@unitypy_define
class StateConstant:
  m_BlendTreeConstantArray: List[OffsetPtr]
  m_BlendTreeConstantIndexArray: List[int]
  m_IKOnFeet: bool
  m_Loop: bool
  m_Speed: float
  m_TagID: int
  m_TransitionConstantArray: List[OffsetPtr]
  m_CycleOffset: Optional[float] = None
  m_CycleOffsetParamID: Optional[int] = None
  m_FullPathID: Optional[int] = None
  m_ID: Optional[int] = None
  m_LeafInfoArray: Optional[List[LeafInfoConstant]] = None
  m_Mirror: Optional[bool] = None
  m_MirrorParamID: Optional[int] = None
  m_NameID: Optional[int] = None
  m_PathID: Optional[int] = None
  m_SpeedParamID: Optional[int] = None
  m_TimeParamID: Optional[int] = None
  m_WriteDefaultValues: Optional[bool] = None


@unitypy_define
class StateKey:
  m_LayerIndex: int
  m_StateID: int


@unitypy_define
class StateMachine(NamedObject):
  m_AnyStatePosition: Vector3f
  m_ChildStateMachine: List[PPtr[StateMachine]]
  m_ChildStateMachinePosition: List[Vector3f]
  m_DefaultState: PPtr[State]
  m_MotionSetCount: int
  m_Name: str
  m_OrderedTransitions: List[Tuple[PPtr[State], List[PPtr[Transition]]]]
  m_ParentStateMachinePosition: Vector3f
  m_States: List[PPtr[State]]
  m_LocalTransitions: Optional[List[Tuple[PPtr[State], List[PPtr[Transition]]]]] = (
    None
  )


@unitypy_define
class StateMachineBehaviourVectorDescription:
  m_StateMachineBehaviourIndices: List[int]
  m_StateMachineBehaviourRanges: List[Tuple[StateKey, StateRange]]


@unitypy_define
class StateMachineConstant:
  m_AnyStateTransitionConstantArray: List[OffsetPtr]
  m_DefaultState: int
  m_StateConstantArray: List[OffsetPtr]
  m_MotionSetCount: Optional[int] = None
  m_SelectorStateConstantArray: Optional[List[OffsetPtr]] = None
  m_SynchronizedLayerCount: Optional[int] = None


@unitypy_define
class StateRange:
  m_Count: int
  m_StartIndex: int


@unitypy_define
class StaticBatchInfo:
  firstSubMesh: int
  subMeshCount: int


@unitypy_define
class StreamInfo:
  channelMask: int
  offset: int
  stride: int
  align: Optional[int] = None
  dividerOp: Optional[int] = None
  frequency: Optional[int] = None


@unitypy_define
class StreamedClip:
  curveCount: int
  data: List[int]
  discreteCurveCount: Optional[int] = None


@unitypy_define
class StreamedResource:
  m_Offset: int
  m_Size: int
  m_Source: str


@unitypy_define
class StreamingInfo:
  offset: int
  path: str
  size: int


@unitypy_define
class StructParameter:
  m_ArraySize: int
  m_Index: int
  m_MatrixMembers: List[MatrixParameter]
  m_NameIndex: int
  m_StructSize: int
  m_VectorMembers: List[VectorParameter]


@unitypy_define
class SubCollider:
  m_Collider: PPtr[Collider2D]
  m_ColliderPaths: List[List[IntPoint]]


@unitypy_define
class SubEmitterData:
  emitter: PPtr[ParticleSystem]
  properties: int
  type: int
  emitProbability: Optional[float] = None


@unitypy_define
class SubMesh:
  firstByte: int
  firstVertex: int
  indexCount: int
  localAABB: AABB
  vertexCount: int
  baseVertex: Optional[int] = None
  isTriStrip: Optional[int] = None
  topology: Optional[int] = None
  triangleCount: Optional[int] = None


@unitypy_define
class SubModule:
  enabled: bool
  subEmitterBirth: Optional[PPtr[ParticleSystem]] = None
  subEmitterBirth1: Optional[PPtr[ParticleSystem]] = None
  subEmitterCollision: Optional[PPtr[ParticleSystem]] = None
  subEmitterCollision1: Optional[PPtr[ParticleSystem]] = None
  subEmitterDeath: Optional[PPtr[ParticleSystem]] = None
  subEmitterDeath1: Optional[PPtr[ParticleSystem]] = None
  subEmitters: Optional[List[SubEmitterData]] = None


@unitypy_define
class SubPassDescriptor:
  colorOutputs: AttachmentIndexArray
  flags: int
  inputs: AttachmentIndexArray


@unitypy_define
class SubstanceEnumItem:
  text: str
  value: int


@unitypy_define
class SubstanceInput:
  alteredTexturesUID: List[int]
  enumValues: List[SubstanceEnumItem]
  flags: int
  internalIndex: int
  internalType: int
  maximum: float
  minimum: float
  name: str
  step: float
  type: int
  value: SubstanceValue
  componentLabels: Optional[List[str]] = None
  group: Optional[str] = None
  internalIdentifier: Optional[int] = None
  label: Optional[str] = None
  visibleIf: Optional[str] = None


@unitypy_define
class SubstanceValue:
  scalar_0_: float
  scalar_1_: float
  scalar_2_: float
  scalar_3_: float
  texture: PPtr[Texture2D]
  stringvalue: Optional[str] = None


@unitypy_define
class TakeInfo:
  bakeStartTime: float
  bakeStopTime: float
  clip: PPtr[AnimationClip]
  defaultClipName: str
  name: str
  sampleRate: float
  startTime: float
  stopTime: float
  internalID: Optional[int] = None


@unitypy_define
class Tetrahedron:
  indices_0_: int
  indices_1_: int
  indices_2_: int
  indices_3_: int
  matrix: Matrix3x4f
  neighbors_0_: int
  neighbors_1_: int
  neighbors_2_: int
  neighbors_3_: int


@unitypy_define
class TextureImportInstructions:
  colorSpace: int
  compressedFormat: int
  compressionQuality: int
  height: int
  uncompressedFormat: int
  usageMode: int
  width: int
  androidETC2FallbackDownscale: Optional[bool] = None
  androidETC2FallbackFormat: Optional[int] = None
  cubeIntermediateSize: Optional[int] = None
  cubeLayout: Optional[int] = None
  cubeMode: Optional[int] = None
  depth: Optional[int] = None
  desiredFormat: Optional[int] = None
  recommendedFormat: Optional[int] = None
  vtOnly: Optional[bool] = None


@unitypy_define
class TextureImportOutput:
  sourceTextureInformation: SourceTextureInformation
  textureImportInstructions: TextureImportInstructions
  importInspectorWarnings: Optional[str] = None


@unitypy_define
class TextureImporterPlatformSettings:
  m_AllowsAlphaSplitting: bool
  m_AndroidETC2FallbackOverride: int
  m_BuildTarget: str
  m_CompressionQuality: int
  m_CrunchedCompression: bool
  m_MaxTextureSize: int
  m_Overridden: bool
  m_ResizeAlgorithm: int
  m_TextureCompression: int
  m_TextureFormat: int
  m_ForceMaximumCompressionQuality_BC6H_BC7: Optional[bool] = None
  m_IgnorePlatformSupport: Optional[bool] = None


@unitypy_define
class TextureParameter:
  m_Dim: int
  m_Index: int
  m_NameIndex: int
  m_SamplerIndex: int
  m_MultiSampled: Optional[bool] = None


@unitypy_define
class TextureParameters:
  height: int
  mipLevels: int
  textureFormat: int
  width: int


@unitypy_define
class TextureSettings:
  anisoLevel: int
  compressionQuality: int
  crunchedCompression: bool
  filterMode: int
  generateMipMaps: bool
  maxTextureSize: int
  readable: bool
  sRGB: bool
  textureCompression: int


@unitypy_define
class TicksPerSecond:
  m_Denominator: int
  m_Numerator: int


@unitypy_define
class TierGraphicsSettings:
  renderingPath: int
  useCascadedShadowMaps: bool
  enableLPPV: Optional[bool] = None
  hdrMode: Optional[int] = None
  prefer32BitShadowMaps: Optional[bool] = None
  realtimeGICPUUsage: Optional[int] = None
  useHDR: Optional[bool] = None


@unitypy_define
class Tile:
  m_TileColorIndex: int
  m_TileIndex: int
  m_TileMatrixIndex: int
  m_TileSpriteIndex: int
  dummyAlignment: Optional[int] = None
  m_AllTileFlags: Optional[int] = None
  m_ColliderType: Optional[int] = None
  m_ObjectToInstantiate: Optional[PPtr[GameObject]] = None
  m_TileFlags: Optional[int] = None
  m_TileObjectToInstantiateIndex: Optional[int] = None


@unitypy_define
class TileAnimationData:
  m_AnimatedSprites: List[PPtr[Sprite]]
  m_AnimationSpeed: float
  m_AnimationTimeOffset: float
  m_Flags: Optional[int] = None
  m_IsLooping: Optional[bool] = None


@unitypy_define
class TilemapRefCountedData:
  m_Data: Union[PPtr[GameObject], ColorRGBA, PPtr[Object], Matrix4x4f, PPtr[Sprite]]
  m_RefCount: int


@unitypy_define
class TrailModule:
  colorOverLifetime: MinMaxGradient
  colorOverTrail: MinMaxGradient
  dieWithParticles: bool
  enabled: bool
  inheritParticleColor: bool
  lifetime: MinMaxCurve
  minVertexDistance: float
  ratio: float
  sizeAffectsLifetime: bool
  sizeAffectsWidth: bool
  textureMode: int
  widthOverTrail: MinMaxCurve
  worldSpace: bool
  attachRibbonsToTransform: Optional[bool] = None
  generateLightingData: Optional[bool] = None
  mode: Optional[int] = None
  ribbonCount: Optional[int] = None
  shadowBias: Optional[float] = None
  splitSubEmitterRibbons: Optional[bool] = None
  textureScale: Optional[Vector2f] = None


@unitypy_define
class TransformMaskElement:
  m_Path: str
  m_Weight: float


@unitypy_define
class Transition(NamedObject):
  m_Atomic: bool
  m_Conditions: List[Condition]
  m_DstState: PPtr[State]
  m_Mute: bool
  m_Name: str
  m_Solo: bool
  m_SrcState: PPtr[State]
  m_TransitionDuration: float
  m_TransitionOffset: float
  m_CanTransitionToSelf: Optional[bool] = None


@unitypy_define
class TransitionConstant:
  m_ConditionConstantArray: List[OffsetPtr]
  m_DestinationState: int
  m_ID: int
  m_TransitionDuration: float
  m_TransitionOffset: float
  m_UserID: int
  m_Atomic: Optional[bool] = None
  m_CanTransitionToSelf: Optional[bool] = None
  m_ExitTime: Optional[float] = None
  m_FullPathID: Optional[int] = None
  m_HasExitTime: Optional[bool] = None
  m_HasFixedDuration: Optional[bool] = None
  m_InterruptionSource: Optional[int] = None
  m_OrderedInterruption: Optional[bool] = None


@unitypy_define
class TreeInstance:
  color: ColorRGBA
  heightScale: float
  index: int
  lightmapColor: ColorRGBA
  position: Vector3f
  widthScale: float
  rotation: Optional[float] = None


@unitypy_define
class TreePrototype:
  bendFactor: float
  prefab: PPtr[GameObject]
  navMeshLod: Optional[int] = None


@unitypy_define
class TriggerModule:
  enabled: bool
  enter: int
  exit: int
  inside: int
  outside: int
  radiusScale: float
  colliderQueryMode: Optional[int] = None
  collisionShape0: Optional[PPtr[Component]] = None
  collisionShape1: Optional[PPtr[Component]] = None
  collisionShape2: Optional[PPtr[Component]] = None
  collisionShape3: Optional[PPtr[Component]] = None
  collisionShape4: Optional[PPtr[Component]] = None
  collisionShape5: Optional[PPtr[Component]] = None
  primitives: Optional[List[PPtr[Component]]] = None


@unitypy_define
class UAVParameter:
  m_Index: int
  m_NameIndex: int
  m_OriginalIndex: int


@unitypy_define
class UVAnimation:
  cycles: float
  x_Tile: int
  y_Tile: int


@unitypy_define
class UVModule:
  animationType: int
  cycles: float
  enabled: bool
  frameOverTime: MinMaxCurve
  rowIndex: int
  tilesX: int
  tilesY: int
  flipU: Optional[float] = None
  flipV: Optional[float] = None
  fps: Optional[float] = None
  mode: Optional[int] = None
  randomRow: Optional[bool] = None
  rowMode: Optional[int] = None
  speedRange: Optional[Vector2f] = None
  sprites: Optional[List[SpriteData]] = None
  startFrame: Optional[MinMaxCurve] = None
  timeMode: Optional[int] = None
  uvChannelMask: Optional[int] = None


@unitypy_define
class UnityAdsSettings(GlobalGameManager):
  m_Enabled: bool
  m_InitializeOnStartup: bool
  m_TestMode: bool
  m_AndroidGameId: Optional[str] = None
  m_EnabledPlatforms: Optional[int] = None
  m_GameId: Optional[str] = None
  m_IosGameId: Optional[str] = None


@unitypy_define
class UnityAnalyticsSettings:
  m_Enabled: bool
  m_InitializeOnStartup: bool
  m_TestMode: bool
  m_PackageRequiringCoreStatsPresent: Optional[bool] = None
  m_TestConfigUrl: Optional[str] = None
  m_TestEventUrl: Optional[str] = None


@unitypy_define
class UnityPropertySheet:
  m_Colors: Union[
    List[Tuple[FastPropertyName, ColorRGBA]], List[Tuple[str, ColorRGBA]]
  ]
  m_Floats: Union[List[Tuple[FastPropertyName, float]], List[Tuple[str, float]]]
  m_TexEnvs: Union[
    List[Tuple[FastPropertyName, UnityTexEnv]], List[Tuple[str, UnityTexEnv]]
  ]
  m_Ints: Optional[List[Tuple[str, int]]] = None


@unitypy_define
class UnityPurchasingSettings:
  m_Enabled: bool
  m_TestMode: bool


@unitypy_define
class UnityTexEnv:
  m_Offset: Vector2f
  m_Scale: Vector2f
  m_Texture: PPtr[Texture]


@unitypy_define
class UpdateZoneInfo:
  needSwap: bool
  passIndex: int
  rotation: float
  updateZoneCenter: Vector3f
  updateZoneSize: Vector3f


@unitypy_define
class VFXCPUBufferData:
  data: List[int]


@unitypy_define
class VFXCPUBufferDesc:
  capacity: int
  initialData: VFXCPUBufferData
  layout: List[VFXLayoutElementDesc]
  stride: int


@unitypy_define
class VFXEditorSystemDesc:
  buffers: List[VFXMapping]
  capacity: int
  flags: int
  layer: int
  tasks: List[VFXEditorTaskDesc]
  type: int
  values: List[VFXMapping]
  name: Optional[str] = None


@unitypy_define
class VFXEditorTaskDesc:
  buffers: List[VFXMapping]
  params: List[VFXMapping]
  processor: PPtr[NamedObject]
  shaderSourceIndex: int
  type: int
  values: List[VFXMapping]
  temporaryBuffers: Optional[List[VFXMappingTemporary]] = None


@unitypy_define
class VFXEntryExposed:
  m_Name: str
  m_Overridden: bool
  m_Value: Union[
    Gradient,
    Vector3f,
    float,
    PPtr[NamedObject],
    Vector4f,
    AnimationCurve,
    PPtr[Object],
    int,
    Vector2f,
    bool,
    Matrix4x4f,
  ]


@unitypy_define
class VFXEntryExpressionValue:
  m_ExpressionIndex: int
  m_Value: Union[
    Gradient,
    Vector3f,
    float,
    PPtr[NamedObject],
    Vector4f,
    AnimationCurve,
    PPtr[Object],
    int,
    Vector2f,
    bool,
    Matrix4x4f,
  ]


@unitypy_define
class VFXEventDesc:
  name: str
  playSystems: List[int]
  stopSystems: List[int]
  initSystems: Optional[List[int]] = None


@unitypy_define
class VFXExposedMapping:
  mapping: VFXMapping
  space: int


@unitypy_define
class VFXExpressionContainer:
  m_Expressions: List[Expression]
  m_NeedsLocalToWorld: bool
  m_NeedsWorldToLocal: bool
  m_ConstantBakeCurveCount: Optional[int] = None
  m_ConstantBakeGradientCount: Optional[int] = None
  m_DynamicBakeCurveCount: Optional[int] = None
  m_DynamicBakeGradientCount: Optional[int] = None
  m_MaxCommonExpressionsIndex: Optional[int] = None
  m_NeededMainCameraBuffers: Optional[int] = None
  m_NeedsMainCamera: Optional[bool] = None


@unitypy_define
class VFXField:
  m_Array: Union[List[VFXEntryExpressionValue], List[VFXEntryExposed]]


@unitypy_define
class VFXGPUBufferDesc:
  capacity: int
  layout: List[VFXLayoutElementDesc]
  size: int
  stride: int
  mode: Optional[int] = None
  target: Optional[int] = None
  type: Optional[int] = None


@unitypy_define
class VFXInstanceSplitDesc:
  values: List[int]


@unitypy_define
class VFXLayoutElementDesc:
  name: str
  offset: VFXLayoutOffset
  type: int


@unitypy_define
class VFXLayoutOffset:
  bucket: int
  element: int
  structure: int


@unitypy_define
class VFXMapping:
  index: int
  nameId: str


@unitypy_define
class VFXMappingTemporary:
  mapping: VFXMapping
  pastFrameIndex: int
  perCameraBuffer: bool


@unitypy_define
class VFXPropertySheetSerializedBase:
  m_AnimationCurve: VFXField
  m_Bool: VFXField
  m_Float: VFXField
  m_Gradient: VFXField
  m_Int: VFXField
  m_Matrix4x4f: VFXField
  m_NamedObject: VFXField
  m_Uint: VFXField
  m_Vector2f: VFXField
  m_Vector3f: VFXField
  m_Vector4f: VFXField


@unitypy_define
class VFXRendererSettings:
  lightProbeUsage: int
  motionVectorGenerationMode: int
  receiveShadows: bool
  reflectionProbeUsage: int
  shadowCastingMode: int
  rayTracingMode: Optional[int] = None


@unitypy_define
class VFXShaderSourceDesc:
  compute: bool
  name: str
  source: str


@unitypy_define
class VFXSystemDesc:
  buffers: List[VFXMapping]
  capacity: int
  flags: int
  layer: int
  tasks: List[VFXTaskDesc]
  type: int
  values: List[VFXMapping]
  instanceSplitDescs: Optional[List[VFXInstanceSplitDesc]] = None
  name: Optional[str] = None


@unitypy_define
class VFXTaskDesc:
  buffers: List[VFXMapping]
  params: List[VFXMapping]
  processor: PPtr[NamedObject]
  type: int
  values: List[VFXMapping]
  instanceSplitIndex: Optional[int] = None
  temporaryBuffers: Optional[List[VFXMappingTemporary]] = None


@unitypy_define
class VFXTemplate:
  category: str
  description: str
  icon: PPtr[Texture2D]
  name: str
  thumbnail: PPtr[Texture2D]


@unitypy_define
class VFXTemporaryGPUBufferDesc:
  desc: VFXGPUBufferDesc
  frameCount: int


@unitypy_define
class VRSettings:
  cardboard: Optional[Google] = None
  daydream: Optional[Google] = None
  enable360StereoCapture: Optional[bool] = None
  hololens: Optional[HoloLens] = None
  lumin: Optional[Lumin] = None
  none: Optional[DeviceNone] = None
  oculus: Optional[Oculus] = None


@unitypy_define
class ValueArray:
  m_BoolValues: List[bool]
  m_FloatValues: List[float]
  m_IntValues: List[int]
  m_PositionValues: Optional[Union[List[float4], List[float3]]] = None
  m_QuaternionValues: Optional[List[float4]] = None
  m_ScaleValues: Optional[Union[List[float4], List[float3]]] = None
  m_VectorValues: Optional[List[float4]] = None


@unitypy_define
class ValueArrayConstant:
  m_ValueArray: List[ValueConstant]


@unitypy_define
class ValueConstant:
  m_ID: int
  m_Index: int
  m_Type: int
  m_TypeID: Optional[int] = None


@unitypy_define
class ValueDelta:
  m_Start: float
  m_Stop: float


@unitypy_define
class VariableBoneCountWeights:
  m_Data: List[int]


@unitypy_define
class VariantInfo:
  graphicsStateInfoSet: Optional[List[GraphicsStateInfo]] = None
  keywordNames: Optional[str] = None
  keywords: Optional[str] = None
  passIndex: Optional[int] = None
  passType: Optional[int] = None
  shader: Optional[PPtr[Shader]] = None
  shaderAssetGUID: Optional[str] = None
  shaderName: Optional[str] = None
  subShaderIndex: Optional[int] = None


@unitypy_define
class Vector3Curve:
  curve: AnimationCurve
  path: str


@unitypy_define
class VectorParameter:
  m_ArraySize: int
  m_Dim: int
  m_Index: int
  m_NameIndex: int
  m_Type: int


@unitypy_define
class VelocityModule:
  enabled: bool
  inWorldSpace: bool
  x: MinMaxCurve
  y: MinMaxCurve
  z: MinMaxCurve
  orbitalOffsetX: Optional[MinMaxCurve] = None
  orbitalOffsetY: Optional[MinMaxCurve] = None
  orbitalOffsetZ: Optional[MinMaxCurve] = None
  orbitalX: Optional[MinMaxCurve] = None
  orbitalY: Optional[MinMaxCurve] = None
  orbitalZ: Optional[MinMaxCurve] = None
  radial: Optional[MinMaxCurve] = None
  speedModifier: Optional[MinMaxCurve] = None


@unitypy_define
class VertexData:
  m_DataSize: bytes
  m_VertexCount: int
  m_Channels: Optional[List[ChannelInfo]] = None
  m_CurrentChannels: Optional[int] = None
  m_Streams: Optional[List[StreamInfo]] = None
  m_Streams_0_: Optional[StreamInfo] = None
  m_Streams_1_: Optional[StreamInfo] = None
  m_Streams_2_: Optional[StreamInfo] = None
  m_Streams_3_: Optional[StreamInfo] = None


@unitypy_define
class VertexLayoutInfo:
  vertexChannelsInfo: List[ChannelInfo]
  vertexStreamCount: int
  vertexStrides: List[int]


@unitypy_define
class VideoClipImporterOutput:
  encodedEndFrame: Optional[int] = None
  encodedHeight: Optional[int] = None
  encodedSettings: Optional[VideoClipImporterTargetSettings] = None
  encodedStartFrame: Optional[int] = None
  encodedWidth: Optional[int] = None
  format: Optional[int] = None
  originalFrameCount: Optional[int] = None
  originalHeight: Optional[int] = None
  originalWidth: Optional[int] = None
  settings: Optional[VideoClipImporterTargetSettings] = None
  sourceAudioChannelCount: Optional[List[int]] = None
  sourceAudioSampleRate: Optional[List[int]] = None
  sourceFileSize: Optional[int] = None
  sourceFrameRate: Optional[float] = None
  sourceHasAlpha: Optional[bool] = None
  sourcePixelAspectRatioDenominator: Optional[int] = None
  sourcePixelAspectRatioNumerator: Optional[int] = None
  streamedResource: Optional[StreamedResource] = None
  transcodeSkipped: Optional[bool] = None


@unitypy_define
class VideoClipImporterTargetSettings:
  aspectRatio: int
  bitrateMode: int
  codec: int
  customHeight: int
  customWidth: int
  enableTranscoding: bool
  resizeFormat: int
  spatialQuality: int


@unitypy_define
class VisualEffectInfo:
  m_Buffers: List[VFXGPUBufferDesc]
  m_CPUBuffers: List[VFXCPUBufferDesc]
  m_CullingFlags: int
  m_Events: List[VFXEventDesc]
  m_ExposedExpressions: Union[List[VFXMapping], List[VFXExposedMapping]]
  m_Expressions: VFXExpressionContainer
  m_PropertySheet: VFXPropertySheetSerializedBase
  m_RendererSettings: VFXRendererSettings
  m_UpdateMode: int
  m_CompilationVersion: Optional[int] = None
  m_InitialEventName: Optional[str] = None
  m_InstancingCapacity: Optional[int] = None
  m_InstancingDisabledReason: Optional[int] = None
  m_InstancingMode: Optional[int] = None
  m_PreWarmDeltaTime: Optional[float] = None
  m_PreWarmStepCount: Optional[int] = None
  m_RuntimeVersion: Optional[int] = None
  m_TemporaryBuffers: Optional[List[VFXTemporaryGPUBufferDesc]] = None


@unitypy_define
class VisualEffectSettings:
  m_CullingFlags: int
  m_InitialEventName: str
  m_PreWarmDeltaTime: float
  m_PreWarmStepCount: int
  m_RendererSettings: VFXRendererSettings
  m_UpdateMode: int
  m_InstancingCapacity: Optional[int] = None
  m_InstancingDisabledReason: Optional[int] = None
  m_InstancingMode: Optional[int] = None


@unitypy_define
class WheelFrictionCurve:
  asymptoteSlip: Optional[float] = None
  asymptoteValue: Optional[float] = None
  extremumSlip: Optional[float] = None
  extremumValue: Optional[float] = None
  m_AsymptoteSlip: Optional[float] = None
  m_AsymptoteValue: Optional[float] = None
  m_ExtremumSlip: Optional[float] = None
  m_ExtremumValue: Optional[float] = None
  m_Stiffness: Optional[float] = None
  stiffnessFactor: Optional[float] = None


@unitypy_define
class bitset:
  bitCount: int
  bitblocks: bytes


@unitypy_define
class int2_storage:
  x: int
  y: int


@unitypy_define
class int3_storage:
  x: int
  y: int
  z: int


@unitypy_define
class xform:
  q: float4
  s: Union[float3, float4]
  t: Union[float3, float4]
