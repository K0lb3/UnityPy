class File(object):
    name: str
    files: dict
    signature: str
    compression: str
    # parent: File

    def keys(self):
        return self.files.keys()

    def items(self):
        return self.files.items()

    def values(self):
        return self.files.values()

    def __getitem__(self, item):
        return self.files[item]

    def __repr__(self):
        return f"<{self.__class__.__name__}>"
