from enum import IntEnum

from .component import Behaviour, Component
from .object import Object, field


class Animation(Behaviour):
	animate_physics = field("m_AnimatePhysics", bool)
	culling_type = field("m_CullingType")
	play_automatically = field("m_PlayAutomatically", bool)
	wrap_mode = field("m_WrapMode")
	animation = field("m_Animation")
	animations = field("m_Animations")


class Motion(Object):
	pass


class AnimationClip(Motion):
	pass


class RuntimeAnimatorController(Object):
	animation_clips = field("m_AnimationClips")


class AnimatorController(RuntimeAnimatorController):
	controller = field("m_Controller")
	controller_size = field("m_ControllerSize")
	multithreaded_state_machine = field("m_MultiThreadedStateMachine")
	state_machine_behaviours = field("m_StateMachineBehaviours")
	state_machine_behaviour_vector_description = field("m_StateMachineBehaviourVectorDescription")
	TOS = field("m_TOS")


class AnimatorCullingMode(IntEnum):
	AlwaysAnimate = 0
	CullUpdateTransforms = 1
	CullCompletely = 2
	BasedOnRenderers = 1


class AnimatorUpdateMode(IntEnum):
	Normal = 0
	AnimatePhysics = 1
	unscaledTime = 2


class Animator(Behaviour):
	allow_constant_clip_sampling_optimization = field("m_AllowConstantClipSamplingOptimization", bool)
	apply_root_motion = field("m_ApplyRootMotion", bool)
	avatar = field("m_Avatar")
	controller = field("m_Controller")
	culling_mode = field("m_CullingMode", AnimatorCullingMode)
	has_transform_hierarchy = field("m_HasTransformHierarchy", bool)
	linear_velocity_binding = field("m_LinearVelocityBlending", bool)
	update_mode = field("m_UpdateMode", AnimatorUpdateMode)


class ParticleAnimator(Component):
	autodestruct = field("autodestruct", bool)
	damping = field("damping")
	does_animate_color = field("Does Animate Color?", bool)
	force = field("force")
	local_rotation_axis = field("localRotationAxis")
	rnd_force = field("rndForce")
	stop_simulation = field("stopSimulation")
	size_grow = field("sizeGrow")
	world_rotation_axis = field("worldRotationAxis")

	@property
	def color_animation(self):
		ret = []
		i = 0
		while True:
			k = "colorAnimation[%i]" % (i)
			if k in self._obj:
				ret.append(self._obj[k])
			else:
				break
			i += 1

		return ret
