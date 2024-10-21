from typing import Optional

from ..helpers.TypeTreeNode import TypeTreeNode
from .Object import Object


class UnknownObject(Object):
    """An object of unknown type that showed up during typetree parsing."""

    __node__: Optional[TypeTreeNode]

    def __init__(self, __node__: TypeTreeNode = None, **kwargs):
        self.__node__ = __node__
        self.__dict__.update(**kwargs)

    def get_type(self):
        return self.__node__.m_Type if self.__node__ else None

    def __repr__(self) -> str:
        def format_value(v):
            vstr = repr(v)
            if len(vstr) > 100:
                return vstr[:97] + "..."
            return vstr

        inner_str = ", ".join(
            f"{k}={format_value(v)}"
            for k, v in self.__dict__.items()
            if k != "__node__"
        )

        return f"<UnknownObject<{self.get_type()}> {inner_str}>"
