__version__ = "1.20.15"

from .environment import Environment as Environment
from .helpers.ArchiveStorageManager import (
    set_assetbundle_decrypt_key as set_assetbundle_decrypt_key,
)


def load(*args, fs=None, **kwargs):
    return Environment(*args, fs=fs, **kwargs)


# backward compatibility
AssetsManager = Environment
