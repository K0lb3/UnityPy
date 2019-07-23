from Object import Object


def field(f, cast = None, **kwargs):
	def _inner(self):
		if "default" in kwargs:
			ret = self.typeTree.get(f, kwargs["default"])
		else:
			ret = self.typeTree[f]
		if cast:
			ret = cast(ret)
		return ret
	
	return property(_inner)


class GameObject(Object):
	active = field("m_IsActive")
	component = field("m_Component")
	layer = field("m_Layer")
	tag = field("m_Tag")
