class TypeTreeError(Exception):
    def __init__(self, message, nodes):
        super().__init__(message)
        self.nodes = nodes


class UnityVersionFallbackError(Exception):
    def __init__(self, message):
        super().__init__(message)


class UnityVersionFallbackWarning(UserWarning):
    def __init__(self, message):
        super().__init__(message)
