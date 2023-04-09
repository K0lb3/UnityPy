__version__ = "1.9.27"

from .environment import Environment
from .helpers.ArchiveStorageManager import set_assetbundle_decrypt_key


def load(*args):
    return Environment(*args)


# backward compatibility
AssetsManager = Environment
