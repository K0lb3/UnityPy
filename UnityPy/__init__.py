__version__ = "1.9.6"

from .environment import Environment


def load(*args):
    return Environment(*args)


# backward compatibility
AssetsManager = Environment
