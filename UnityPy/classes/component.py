from .object import Object, field


class Component(Object):
	game_object = field("m_GameObject")


class Behaviour(Component):
	enabled = field("m_Enabled", bool)


class Transform(Component):
	position = field("m_LocalPosition")
	rotation = field("m_LocalRotation")
	scale = field("m_LocalScale")
	parent = field("m_Father")
	children = field("m_Children")
