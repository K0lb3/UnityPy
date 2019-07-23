from enum import IntEnum

from .component import Behaviour, Component
from .object import field


class Collider(Component):
	material = field("m_Material")
	is_trigger = field("m_IsTrigger", bool)


class BoxCollider(Collider):
	center = field("m_Center")
	size = field("m_Size")


class Collider2D(Behaviour):
	is_trigger = field("m_IsTrigger")
	material = field("m_Material")
	offset = field("m_Offset")
	used_by_effector = field("m_UsedByEffector", bool)


class BoxCollider2D(Collider2D):
	size = field("m_Size")


class RigidbodySleepMode2D(IntEnum):
	NeverSleep = 0
	StartAwake = 1
	StartAsleep = 2


class Rigidbody2D(Component):
	angular_drag = field("m_AngularDrag")
	collision_detection = field("m_CollisionDetection")
	constraints = field("m_Constraints")
	drag = field("m_LinearDrag")
	gravity_scale = field("m_GravityScale")
	interpolate = field("m_Interpolate")
	is_kinematic = field("m_IsKinematic", bool)
	mass = field("m_Mass")
	sleep_mode = field("m_SleepingMode", RigidbodySleepMode2D)
