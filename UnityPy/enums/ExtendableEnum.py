from enum import IntEnum

# based on https://stackoverflow.com/a/57179436


class ExtendableEnum(IntEnum):
    @classmethod
    def _missing_(cls, value):
        if isinstance(value, int):
            pseudo_member = cls._value2member_map_.get(value, None)
            if pseudo_member is None:
                new_member = int.__new__(cls, value)
                # I expect a name attribute to hold a string, hence str(value)
                # However, new_member._name_ = value works, too
                new_member._name_ = f"Unknown ({value})"
                new_member._value_ = value
                pseudo_member = cls._value2member_map_.setdefault(value, new_member)
            return pseudo_member
        return None  # will raise the ValueError in Enum.__new__
