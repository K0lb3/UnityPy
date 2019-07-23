from .component import Component
from .object import field


class ParticleEmitter(Component):
	angular_velocity = field("angularVelocity")
	emit = field("m_Emit", bool)
	emitter_velocity_scale = field("emitterVelocityScale")
	max_emission = field("maxEmission")
	max_energy = field("maxEnergy")
	max_size = field("maxSize")
	min_emission = field("minEmission")
	min_energy = field("minEnergy")
	min_size = field("minSize")
	rnd_angular_velocity = field("rndAngularVelocity")
	rnd_rotation = field("rndRotation")
	rnd_velocity = field("rndVelocity")
	use_worldspace = field("Simulate in Worldspace?", bool)
	world_velocity = field("worldVelocity")
	
	local_velocity = field("localVelocity")
	one_shot = field("m_OneShot", bool)
	tangent_velocity = field("tangentVelocity")


class EllipsoidParticleEmitter(ParticleEmitter):
	min_emitter_range = field("m_MinEmitterRange")


class MeshParticleEmitter(ParticleEmitter):
	mesh = field("m_Mesh")
	interpolate_triangles = field("m_InterpolateTriangles", bool)
	max_normal_velocity = field("m_MaxNormalVelocity")
	min_normal_velocity = field("m_MinNormalVelocity")
	systematic = field("m_Systematic", bool)


class ParticleSystem(Component):
	pass
