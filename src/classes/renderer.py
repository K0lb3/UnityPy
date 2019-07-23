from enum import IntEnum

from .component import Component
from .object import field


class ReflectionProbeUsage(IntEnum):
	Off = 0
	BlendProbes = 1
	BlendProbesAndSkybox = 2
	Simple = 3


class ShadowCastingMode(IntEnum):
	Off = 0
	On = 1
	TwoSided = 2
	ShadowsOnly = 3


class Renderer(Component):
	enabled = field("m_Enabled", bool)
	lightmap_index = field("m_LightmapIndex")
	materials = field("m_Materials")
	probe_anchor = field("m_ProbeAnchor")
	receive_shadows = field("m_ReceiveShadows", bool)
	reflection_probe_usage = field("m_ReflectionProbeUsage", ReflectionProbeUsage)
	shadow_casting_mode = field("m_CastShadows", ShadowCastingMode)
	sorting_layer_id = field("m_SortingLayerID")
	sorting_order = field("m_SortingOrder")
	use_light_probes = field("m_UseLightProbes", bool)
	lightmap_index_dynamic = field("m_LightmapIndexDynamic")
	lightmap_tiling_offset = field("m_LightmapTilingOffset")
	lightmap_tiling_offset_dynamic = field("m_LightmapTilingOffsetDynamic")
	static_batch_root = field("m_StaticBatchRoot")
	subset_indices = field("m_SubsetIndices")
	
	@property
	def material(self):
		return self.materials[0]


class ParticleSystemRenderMode(IntEnum):
	Billboard = 0
	Stretch = 1
	HorizontalBillboard = 2
	VerticalBillboard = 3
	Mesh = 4


class ParticleSystemSortMode(IntEnum):
	None_ = 0
	Distance = 1
	OldestInFront = 2
	YoungestInFront = 3


class MeshRenderer(Component):
	pass


class ParticleRenderer(Renderer):
	camera_velocity_scale = field("m_CameraVelocityScale")
	length_scale = field("m_LengthScale")
	max_particle_size = field("m_MaxParticleSize")
	velocity_scale = field("m_VelocityScale")
	stretch_particles = field("m_StretchParticles")
	uv_animation = field("UV Animation")


class ParticleSystemRenderer(Renderer):
	camera_velocity_scale = field("m_CameraVelocityScale")
	length_scale = field("m_LengthScale")
	max_particle_size = field("m_MaxParticleSize")
	mesh = field("m_Mesh")
	mesh1 = field("m_Mesh1")
	mesh2 = field("m_Mesh2")
	mesh3 = field("m_Mesh3")
	normal_direction = field("m_NormalDirection")
	render_mode = field("m_RenderMode", ParticleSystemRenderMode)
	sort_mode = field("m_SortMode", ParticleSystemSortMode)
	sorting_fudge = field("m_SortingFudge")
	velocity_scale = field("m_VelocityScale")
